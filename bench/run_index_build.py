#!/usr/bin/env python3
"""Measure one from-empty index build: process start -> index at the chain tip -> serving.

    sudo /opt/zbench/venv/bin/python bench/run_index_build.py --system zaino-0.10.1 --out runs/index/zaino-0.10.1-r1 --cold

Preconditions (checked): the backing node is at the chain tip before the clock starts.
  zaino-*     zebrad.service running and its best block less than --max-tip-age old.
  ztreamer-*  the embedded node's state was caught up by `bench/catch_up_ztreamer.sh`, and Zebra is
              stopped (--exclusive, default) so only the system under test runs.

The indexer runs in its own transient systemd unit. Its cgroup gives exact CPU time, peak memory and
block I/O; Zebra's cgroup is sampled alongside so Zaino can be reported alone and with its node.
Ztreamer embeds its node, so only the combined figure exists for it.

Outputs in --out:
  run.json      definitions, inputs, provenance, phase timestamps and resource totals
  samples.csv   1 s timeline: cgroup CPU/memory/IO for the indexer (and zebrad), host memory
  metrics.csv   2 s Prometheus samples from the indexer
  probes.csv    5 s gRPC probes (GetLightdInfo, GetBlock near tip, GetBlock historical)
  index-size.csv, journal.log, rendered config, hardware-before/after.json
"""

from __future__ import annotations

import argparse
import csv
import datetime
import json
import pathlib
import re
import shutil
import subprocess
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import common  # noqa: E402
from common import V  # noqa: E402

HISTORICAL_PROBE_HEIGHT = 1_000_000


def zebra_rpc():
    from zebra_rpc import JsonRpc
    return JsonRpc(f"http://{V['ZEBRA_RPC']}", cookie=f"{V['DATA']}/zebra-cookie/.cookie")


def zebra_tip(rpc) -> tuple[int, str, int]:
    height = rpc.call("getblockcount")
    block_hash = rpc.call("getblockhash", height)
    block_time = rpc.call("getblock", block_hash, 1)["time"]
    return height, block_hash, block_time


class Prober:
    """gRPC probes that tolerate the server not listening yet. Once connected, gRPC reconnects itself."""

    def __init__(self, addr: str):
        self.addr = addr
        self.stub = None

    def probe(self, name: str, fn) -> tuple[str, float, str]:
        import lw
        started = time.perf_counter()
        try:
            if self.stub is None:
                self.stub = lw.connect(f"http://{self.addr}", ready_timeout=0.5)
            value = fn(self.stub)
            return "OK", time.perf_counter() - started, str(value)
        except Exception as e:  # not listening yet, deadline, gRPC status: all are observations
            code = getattr(e, "code", None)
            status = code().name if callable(code) else type(e).__name__
            return status, time.perf_counter() - started, ""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--system", required=True, choices=sorted(common.systems()))
    parser.add_argument("--out", type=pathlib.Path, required=True)
    parser.add_argument("--cold", action="store_true", help="drop the OS page cache before starting")
    parser.add_argument("--no-exclusive", action="store_true", help="leave zebrad running during Ztreamer runs")
    parser.add_argument("--timeout-hours", type=float, default=16)
    parser.add_argument("--settle-seconds", type=int, default=120, help="keep sampling after completion")
    parser.add_argument("--max-tip-age", type=int, default=1800, help="seconds; Zebra freshness precondition")
    args = parser.parse_args()

    import lw
    from lw import pb

    system = common.systems()[args.system]
    if args.out.exists() and any(args.out.iterdir()):
        sys.exit(f"{args.out} is not empty; every run gets a fresh directory")
    args.out.mkdir(parents=True, exist_ok=True)
    if not pathlib.Path(system.binary).exists():
        sys.exit(f"missing {system.binary}; run server/12-build.sh")
    busy = common.sh("systemctl", "list-units", "--plain", "--no-legend", "zbench-*", check=False).strip()
    if busy:
        sys.exit(f"another benchmark unit is active:\n{busy}")

    rpc = None
    target = None
    stopped_zebra = False
    if system.family == "zaino":
        if common.sh("systemctl", "is-active", "zebrad", check=False).strip() != "active":
            sys.exit("zebrad.service is not running")
        rpc = zebra_rpc()
        height, block_hash, block_time = zebra_tip(rpc)
        age = int(time.time()) - block_time
        if age > args.max_tip_age:
            sys.exit(f"Zebra tip {height} is {age}s old; wait for it to catch up")
        target = {"height": height, "hash": block_hash, "block_time": block_time, "source": "zebra getblockcount"}
    else:
        marker = pathlib.Path(system.zakura_state) / ".zbench-caught-up"
        if not marker.exists() or time.time() - marker.stat().st_mtime > args.max_tip_age:
            sys.exit(f"{system.zakura_state} is not freshly caught up; run bench/catch_up_ztreamer.sh {system.name}")
        if not args.no_exclusive:
            stopped_zebra = common.sh("systemctl", "is-active", "zebrad", check=False).strip() == "active"
            subprocess.run(["systemctl", "stop", "zebrad"], check=False)
        target = {"source": "embedded Zakura tip, read from GetLatestBlock at completion",
                  "caught_up": marker.read_text().strip()}

    shutil.rmtree(system.index_dir, ignore_errors=True)
    pathlib.Path(system.index_dir).parent.mkdir(parents=True, exist_ok=True)
    if system.family == "ztreamer":
        pathlib.Path(V["DATA"], "zakura-cookie").mkdir(parents=True, exist_ok=True)
    config = system.render_config(args.out)
    (args.out / "hardware-before.json").write_text(
        common.sh(str(common.ROOT / "server" / "collect-hardware.sh"), check=False))
    if args.cold:
        common.drop_page_cache()

    unit = common.Unit(f"zbench-{system.name}", system.command(str(config)), env={"RUST_LOG": "info"})
    zebra_cg = common.cgroup_path("zebrad.service") if system.family == "zaino" else None
    prober = Prober(system.grpc)
    probe_recent = (target or {}).get("height")

    events: dict[str, float] = {}
    started = common.now()
    unit.start()
    events["process_started"] = started
    cg = unit.cgroup
    zebra_base = common.read_cgroup(zebra_cg) if zebra_cg else None

    samples_f = open(args.out / "samples.csv", "w", newline="")
    metrics_f = open(args.out / "metrics.csv", "w", newline="")
    probes_f = open(args.out / "probes.csv", "w", newline="")
    size_f = open(args.out / "index-size.csv", "w", newline="")
    samples = csv.writer(samples_f)
    samples.writerow(["t", "elapsed_s", "who", "cpu_usec", "user_usec", "system_usec", "mem_bytes",
                      "mem_peak_bytes", "rbytes", "wbytes", "pids", "host_mem_available_bytes"])
    metrics = csv.writer(metrics_f)
    metrics.writerow(["t", "elapsed_s", "metric", "value"])
    probes = csv.writer(probes_f)
    probes.writerow(["t", "elapsed_s", "probe", "status", "seconds", "value"])
    sizes = csv.writer(size_f)
    sizes.writerow(["t", "elapsed_s", "index_bytes"])

    prefixes = ("zaino_", "ztreamer_", "state_finalized_block_height", "sync_", "process_")
    last = {"metrics": 0.0, "probe": 0.0, "size": 0.0, "journal": 0.0}
    last_metrics: dict[str, float] = {}
    accumulator_seen_change = started
    accumulator_value = None
    completed_at = None
    deadline = started + args.timeout_hours * 3600
    status = "timeout"

    def host_available() -> int:
        for line in pathlib.Path("/proc/meminfo").read_text().splitlines():
            if line.startswith("MemAvailable:"):
                return int(line.split()[1]) * 1024
        return 0

    try:
        while True:
            t = common.now()
            elapsed = t - started
            if not unit.active():
                status = "exited" if completed_at is None else status
                events.setdefault("process_exited", t)
                break
            stats = common.read_cgroup(cg)
            avail = host_available()
            samples.writerow([f"{t:.3f}", f"{elapsed:.3f}", "indexer", *[stats[k] for k in (
                "cpu_usec", "user_usec", "system_usec", "mem_bytes", "mem_peak_bytes", "rbytes", "wbytes", "pids")], avail])
            if zebra_cg:
                z = common.read_cgroup(zebra_cg)
                samples.writerow([f"{t:.3f}", f"{elapsed:.3f}", "zebrad", *[z[k] for k in (
                    "cpu_usec", "user_usec", "system_usec", "mem_bytes", "mem_peak_bytes", "rbytes", "wbytes", "pids")], avail])

            if t - last["metrics"] >= 2:
                last["metrics"] = t
                scraped = common.scrape(system.metrics, prefixes)
                for name, value in scraped.items():
                    if last_metrics.get(name) != value:
                        metrics.writerow([f"{t:.3f}", f"{elapsed:.3f}", name, value])
                last_metrics.update(scraped)
                metrics_f.flush()

            if t - last["probe"] >= 5:
                last["probe"] = t
                checks = [("GetLightdInfo", lambda s: s.GetLightdInfo(pb.Empty(), timeout=2).blockHeight),
                          ("GetBlock-historical", lambda s: len(s.GetBlock(pb.BlockID(height=HISTORICAL_PROBE_HEIGHT), timeout=5).vtx))]
                if probe_recent:
                    checks.append(("GetBlock-target", lambda s: lw.display_hex(s.GetBlock(pb.BlockID(height=probe_recent), timeout=5).hash)))
                for name, fn in checks:
                    result, secs, value = prober.probe(name, fn)
                    probes.writerow([f"{t:.3f}", f"{elapsed:.3f}", name, result, f"{secs:.6f}", value])
                    if result == "OK":
                        events.setdefault(f"first_ok_{name}", t)
                probes_f.flush()

            if t - last["size"] >= 60:
                last["size"] = t
                sizes.writerow([f"{t:.3f}", f"{elapsed:.3f}", common.tree_bytes(system.index_dir)])
                size_f.flush()

            # Completion: the indexer's own index has reached the tip and the tip block is served.
            if completed_at is None:
                if system.family == "zaino":
                    finalized = last_metrics.get("zaino_sync_finalized_height") or last_metrics.get("zaino_db_tip_height") or 0
                    sync_target = last_metrics.get("zaino_sync_target_height") or 0
                    if finalized and sync_target and finalized >= sync_target and "index_reached_sync_target" not in events:
                        events["index_reached_sync_target"] = t
                        accumulator_seen_change = t
                    acc = last_metrics.get("zaino_sync_accumulator_height")
                    if acc != accumulator_value:
                        accumulator_value, accumulator_seen_change = acc, t
                    # The txout-set accumulator rebuild runs after the block sync; wait for it unless it
                    # does not exist in this version or stops moving for 10 minutes after the sync.
                    accumulator_done = acc is None or acc >= finalized or t - accumulator_seen_change > 600
                    if "index_reached_sync_target" in events and accumulator_done and "first_ok_GetBlock-target" in events:
                        if acc is not None and acc >= finalized:
                            events.setdefault("accumulator_caught_up", t)
                        completed_at = t
                elif t - last["journal"] >= 10:
                    last["journal"] = t
                    log = unit.journal(started)
                    for marker, event in (("Zakura is near the chain tip", "node_near_tip"),
                                          ("historical compact index complete", "historical_index_complete")):
                        if marker in log and event not in events:
                            match = re.search(rf"^(\d+\.\d+) .*{re.escape(marker)}", log, re.M)
                            events[event] = float(match.group(1)) if match else t
                    if "historical_index_complete" in events and "first_ok_GetLightdInfo" in events:
                        completed_at = t
                if completed_at:
                    events["completed"] = completed_at
                    status = "complete"
                    print(f"{system.name}: complete after {completed_at - started:.0f}s; settling", file=sys.stderr)
            elif t - completed_at >= args.settle_seconds:
                break
            if t > deadline:
                status = "timeout"
                break
            time.sleep(max(0.0, 1.0 - (common.now() - t)))
    finally:
        final = common.read_cgroup(cg)
        zebra_final = common.read_cgroup(zebra_cg) if zebra_cg else None
        tip_served = None
        try:
            stub = lw.connect(f"http://{system.grpc}")
            tip_served = int(stub.GetLatestBlock(pb.ChainSpec(), timeout=10).height)
        except Exception:
            pass
        stop_started = common.now()
        unit.stop()
        events["stopped"] = common.now()
        (args.out / "journal.log").write_text(unit.journal(started))
        for f in (samples_f, metrics_f, probes_f, size_f):
            f.close()
        if stopped_zebra:
            subprocess.run(["systemctl", "start", "zebrad"], check=False)

    index_bytes = common.tree_bytes(system.index_dir)
    (args.out / "hardware-after.json").write_text(
        common.sh(str(common.ROOT / "server" / "collect-hardware.sh"), check=False))

    def rel(name):
        return round(events[name] - started, 3) if name in events else None

    summary = {
        "system": system.name,
        "family": system.family,
        "status": status,
        "started_utc": datetime.datetime.fromtimestamp(started, datetime.timezone.utc).isoformat(),
        "cache": "cold (page cache dropped)" if args.cold else "warm",
        "exclusive": system.family == "ztreamer" and not args.no_exclusive,
        "target": target,
        "tip_served_at_end": tip_served,
        "phases_seconds_from_start": {k: rel(k) for k in sorted(events)},
        "headline": {
            "seconds_to_completion": rel("completed"),
            "seconds_to_first_grpc_answer": rel("first_ok_GetLightdInfo"),
            "seconds_to_serve_historical_block": rel("first_ok_GetBlock-historical"),
            "shutdown_seconds": round(events["stopped"] - stop_started, 3),
        },
        "resources": {
            "indexer_process": {
                "cpu_seconds": final["cpu_usec"] / 1e6,
                "peak_memory_bytes": final["mem_peak_bytes"],
                "read_bytes": final["rbytes"],
                "write_bytes": final["wbytes"],
                "note": "Ztreamer's figure includes its embedded Zakura node" if system.family == "ztreamer" else
                        "Zaino process only; Zebra reported separately",
            },
            "zebrad_during_run": None if not zebra_final else {
                "cpu_seconds": (zebra_final["cpu_usec"] - zebra_base["cpu_usec"]) / 1e6,
                "read_bytes": zebra_final["rbytes"] - zebra_base["rbytes"],
                "write_bytes": zebra_final["wbytes"] - zebra_base["wbytes"],
                "peak_memory_bytes_sampled": max_sampled(args.out / "samples.csv", "zebrad"),
            },
            "index_bytes_on_disk": index_bytes,
        },
        "command": common.quote(unit.command),
        "config_file": config.name,
        "provenance": common.provenance(system.name),
        "definitions": {
            "completed": ("zaino: finalized height >= Zaino's sync target, txout accumulator caught up (or idle 10 min), "
                          "and GetBlock at Zebra's start-of-run tip answered"
                          if system.family == "zaino" else
                          "ztreamer: 'historical compact index complete' logged and gRPC answering"),
            "clock": "starts at systemd unit start; includes node startup (embedded for Ztreamer, already running for Zaino)",
        },
    }
    (args.out / "run.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary["headline"] | {"status": status}, indent=2))
    return 0 if status == "complete" else 1


def max_sampled(path: pathlib.Path, who: str) -> int:
    peak = 0
    with open(path) as f:
        for row in csv.DictReader(f):
            if row["who"] == who:
                peak = max(peak, int(row["mem_bytes"]))
    return peak


if __name__ == "__main__":
    sys.exit(main())
