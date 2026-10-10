"""Shared plumbing for benchmark runners: settings, systems under test, cgroup accounting, sampling."""

from __future__ import annotations

import dataclasses
import json
import os
import pathlib
import re
import shlex
import subprocess
import time
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent


def load_versions() -> dict[str, str]:
    """Parse versions.env; `${NAME:-default}` values resolve from the environment like the shell does."""
    values = {}
    for line in (ROOT / "versions.env").read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            default = re.fullmatch(r"\$\{(\w+):-(.*)\}", value)
            values[key] = os.environ.get(default.group(1), default.group(2)) if default else value
    return values


V = load_versions()

# Frozen mode: every node stays at a fixed snapshot height (CI on testnet). Set by ZBENCH_FROZEN=1.
FROZEN = os.environ.get("ZBENCH_FROZEN") == "1"
SAPLING_ACTIVATION = {"Mainnet": 419_200, "Testnet": 280_000}[V["NETWORK"]]


def render(template: str, out: pathlib.Path, **extra: str) -> pathlib.Path:
    """Fill @NAME@ placeholders in configs/<template> from versions.env plus `extra`."""
    peers_key = "initial_mainnet_peers" if V["NETWORK"] == "Mainnet" else "initial_testnet_peers"
    values = dict(V, ZAKURA_PEERS=f'{peers_key} = ["127.0.0.1:8233"]\ncache_dir = false' if FROZEN else "", **extra)
    text = re.sub(r"@([A-Z0-9_]+)@", lambda m: values[m.group(1)], (ROOT / "configs" / template).read_text())
    out.write_text(text)
    return out


@dataclasses.dataclass
class System:
    """One indexer build under test and how to run it."""

    name: str  # e.g. zaino-0.10.1
    family: str  # zaino | ztreamer
    binary: str
    index_dir: str
    grpc: str  # host:port
    metrics: str  # host:port
    zakura_state: str | None = None  # Ztreamer only: cache_dir of the embedded node
    zakura_p2p_stack: bool = False  # embedded Zakura has `network.p2p_stack` (1.5.1+; the v0.1.0 fork rejects it)

    def command(self, config_path: str) -> list[str]:
        # Absolute: systemd starts units in /, not in the caller's directory.
        config_path = str(pathlib.Path(config_path).resolve())
        if self.family == "zaino":
            return [self.binary, "start", "--config", config_path]
        return [
            self.binary,
            "--zakura-config", config_path,
            "--index-dir", self.index_dir,
            "--grpc-listen", self.grpc,
            "--metrics-listen", self.metrics,
        ]

    def render_config(self, out: pathlib.Path) -> pathlib.Path:
        if self.family == "zaino":
            return render("zainod.toml.in", out / "zainod.toml", INDEX_DIR=self.index_dir)
        stack = 'p2p_stack = "legacy"' if FROZEN and self.zakura_p2p_stack else ""
        return render("zakura-ztreamer.toml.in", out / "zakura.toml", ZAKURA_STATE=self.zakura_state or "",
                      ZAKURA_P2P_STACK=stack)


def systems() -> dict[str, System]:
    opt, data = V["OPT"], V["DATA"]
    zaino = lambda ref: System(
        name=f"zaino-{ref}", family="zaino", binary=f"{opt}/bin/zainod-{ref}",
        index_dir=f"{data}/index/zaino-{ref}", grpc=V["ZAINO_GRPC"], metrics=V["ZAINO_METRICS"])
    ztreamer = lambda ref, snap, p2p_stack: System(
        name=f"ztreamer-{ref}", family="ztreamer", binary=f"{opt}/bin/ztreamerd-{ref}",
        index_dir=f"{data}/index/ztreamer-{ref}", grpc=V["ZTREAMER_GRPC"], metrics=V["ZTREAMER_METRICS"],
        zakura_state=f"{data}/zakura-{snap}", zakura_p2p_stack=p2p_stack)
    return {s.name: s for s in (
        zaino(V["ZAINO_STABLE_REF"]),
        zaino(V["ZAINO_REPRO_REF"]),
        ztreamer(V["ZTREAMER_RELEASE_REF"], "v28", False),
        ztreamer(V["ZTREAMER_HEAD_REF"], "v29", True),
    )}


def provenance(name: str) -> dict | None:
    """Build provenance written by server/12-build.sh (binary hash, commit, toolchain)."""
    binary_name = name.replace("zaino-", "zainod-").replace("ztreamer-", "ztreamerd-")
    path = pathlib.Path(V["OPT"]) / "provenance" / f"{binary_name}.json"
    return json.loads(path.read_text()) if path.exists() else None


def sh(*args: str, check: bool = True) -> str:
    return subprocess.run(args, check=check, capture_output=True, text=True).stdout


# ---------------------------------------------------------------- cgroup v2 accounting via systemd

class Unit:
    """A process tree in its own transient systemd unit, so the kernel accounts its resources exactly."""

    def __init__(self, name: str, command: list[str], env: dict[str, str] | None = None,
                 properties: list[str] | None = None):
        self.name = name if name.endswith(".service") else f"{name}.service"
        self.command = command
        self.env = env or {}
        self.properties = properties or []

    def start(self) -> None:
        props = ["CPUAccounting=yes", "MemoryAccounting=yes", "IOAccounting=yes", "TasksAccounting=yes",
                 "LimitNOFILE=1048576", "KillSignal=SIGINT", "TimeoutStopSec=300", *self.properties]
        args = ["systemd-run", f"--unit={self.name}", "--collect", "--quiet"]
        args += [f"--property={p}" for p in props]
        args += [f"--setenv={k}={v}" for k, v in self.env.items()]
        subprocess.run(args + ["--"] + self.command, check=True)

    def active(self) -> bool:
        return sh("systemctl", "is-active", self.name, check=False).strip() in ("active", "activating")

    def stop(self) -> None:
        subprocess.run(["systemctl", "stop", self.name], check=False)

    def main_pid(self) -> int | None:
        pid = sh("systemctl", "show", "-p", "MainPID", "--value", self.name, check=False).strip()
        return int(pid) if pid.isdigit() and pid != "0" else None

    @property
    def cgroup(self) -> pathlib.Path:
        return cgroup_path(self.name)

    def journal(self, since: float) -> str:
        return sh("journalctl", "-u", self.name, "--since", f"@{since:.0f}", "-o", "short-unix", "--no-pager",
                  check=False)


def cgroup_path(unit: str) -> pathlib.Path:
    rel = sh("systemctl", "show", "-p", "ControlGroup", "--value", unit, check=False).strip()
    return pathlib.Path("/sys/fs/cgroup") / rel.lstrip("/")


def read_cgroup(path: pathlib.Path) -> dict[str, int]:
    """CPU microseconds, memory and block I/O bytes for a cgroup (0 when unavailable).

    Memory is split, because the cgroup total also counts page cache for files the process reads
    (node state, mmap'd LMDB index), which the kernel can evict:
      anon_bytes   heap and other anonymous memory: what the process itself holds
      file_bytes   page cache charged to the cgroup
      mem_bytes / mem_peak_bytes   cgroup totals (anon + file + kernel), as memory.current / memory.peak
    """
    out = {"cpu_usec": 0, "user_usec": 0, "system_usec": 0, "mem_bytes": 0, "mem_peak_bytes": 0,
           "anon_bytes": 0, "file_bytes": 0, "rbytes": 0, "wbytes": 0, "pids": 0}
    try:
        for line in (path / "cpu.stat").read_text().splitlines():
            key, value = line.split()
            if key in ("usage_usec", "user_usec", "system_usec"):
                out["cpu_usec" if key == "usage_usec" else key] = int(value)
        out["mem_bytes"] = int((path / "memory.current").read_text())
        peak = path / "memory.peak"
        out["mem_peak_bytes"] = int(peak.read_text()) if peak.exists() else 0
        for line in (path / "memory.stat").read_text().splitlines():
            key, value = line.split()
            if key in ("anon", "file"):
                out[f"{key}_bytes"] = int(value)
        for line in (path / "io.stat").read_text().splitlines():
            for field in line.split()[1:]:
                key, _, value = field.partition("=")
                if key in ("rbytes", "wbytes"):
                    out[key] += int(value)
        out["pids"] = int((path / "pids.current").read_text())
    except (OSError, ValueError):
        pass
    return out


def process_memory(pid: int | None) -> dict[str, int]:
    """VmHWM (peak RSS), VmRSS and its anon/file split from /proc/<pid>/status, in bytes."""
    out = {}
    if not pid:
        return out
    try:
        for line in pathlib.Path(f"/proc/{pid}/status").read_text().splitlines():
            key, _, value = line.partition(":")
            if key in ("VmHWM", "VmRSS", "RssAnon", "RssFile"):
                out[key] = int(value.split()[0]) * 1024
    except OSError:
        pass
    return out


def scrape(addr: str, prefixes: tuple[str, ...]) -> dict[str, float]:
    """Prometheus text-format scrape, keeping unlabelled-or-labelled samples whose name has a prefix."""
    try:
        with urllib.request.urlopen(f"http://{addr}/metrics", timeout=2) as response:
            text = response.read().decode()
    except OSError:
        return {}
    samples = {}
    for line in text.splitlines():
        if not line or line.startswith("#"):
            continue
        name, _, value = line.rpartition(" ")
        if name.startswith(prefixes):
            try:
                samples[name] = float(value)
            except ValueError:
                pass
    return samples


def tree_bytes(path: str) -> int:
    total = 0
    for root, _, files in os.walk(path):
        for f in files:
            try:
                total += os.stat(os.path.join(root, f)).st_blocks * 512
            except OSError:
                pass
    return total


def drop_page_cache() -> None:
    os.sync()
    pathlib.Path("/proc/sys/vm/drop_caches").write_text("3\n")


def now() -> float:
    return time.time()


def quote(cmd: list[str]) -> str:
    return " ".join(shlex.quote(c) for c in cmd)
