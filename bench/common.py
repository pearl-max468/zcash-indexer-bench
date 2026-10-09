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
    values = {}
    for line in (ROOT / "versions.env").read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            values[key] = value
    return values


V = load_versions()


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

    def command(self, config_path: str) -> list[str]:
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
        template = "zainod.toml.in" if self.family == "zaino" else "zakura-ztreamer.toml.in"
        text = (ROOT / "configs" / template).read_text()
        values = dict(V, INDEX_DIR=self.index_dir, ZAKURA_STATE=self.zakura_state or "")
        text = re.sub(r"@([A-Z0-9_]+)@", lambda m: values[m.group(1)], text)
        path = out / ("zainod.toml" if self.family == "zaino" else "zakura.toml")
        path.write_text(text)
        return path


def systems() -> dict[str, System]:
    opt, data = V["OPT"], V["DATA"]
    zaino = lambda ref: System(
        name=f"zaino-{ref}", family="zaino", binary=f"{opt}/bin/zainod-{ref}",
        index_dir=f"{data}/index/zaino-{ref}", grpc=V["ZAINO_GRPC"], metrics=V["ZAINO_METRICS"])
    ztreamer = lambda ref, snap: System(
        name=f"ztreamer-{ref}", family="ztreamer", binary=f"{opt}/bin/ztreamerd-{ref}",
        index_dir=f"{data}/index/ztreamer-{ref}", grpc=V["ZTREAMER_GRPC"], metrics=V["ZTREAMER_METRICS"],
        zakura_state=f"{data}/zakura-{snap}")
    return {s.name: s for s in (
        zaino(V["ZAINO_STABLE_REF"]),
        zaino(V["ZAINO_REPRO_REF"]),
        ztreamer(V["ZTREAMER_RELEASE_REF"], "v28"),
        ztreamer(V["ZTREAMER_HEAD_REF"], "v29"),
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
    """CPU microseconds, current/peak memory and block I/O bytes for a cgroup (0 when unavailable)."""
    out = {"cpu_usec": 0, "user_usec": 0, "system_usec": 0, "mem_bytes": 0, "mem_peak_bytes": 0,
           "rbytes": 0, "wbytes": 0, "pids": 0}
    try:
        for line in (path / "cpu.stat").read_text().splitlines():
            key, value = line.split()
            if key in ("usage_usec", "user_usec", "system_usec"):
                out["cpu_usec" if key == "usage_usec" else key] = int(value)
        out["mem_bytes"] = int((path / "memory.current").read_text())
        peak = path / "memory.peak"
        out["mem_peak_bytes"] = int(peak.read_text()) if peak.exists() else 0
        for line in (path / "io.stat").read_text().splitlines():
            for field in line.split()[1:]:
                key, _, value = field.partition("=")
                if key in ("rbytes", "wbytes"):
                    out[key] += int(value)
        out["pids"] = int((path / "pids.current").read_text())
    except (OSError, ValueError):
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
