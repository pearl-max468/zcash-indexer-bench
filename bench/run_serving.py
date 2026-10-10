#!/usr/bin/env python3
"""Serving benchmark for one system with an already-built index, driven by ghz.

    sudo /opt/zbench/venv/bin/python bench/run_serving.py --system zaino-0.10.1 --upper 3510000 \
        --fixtures fixtures/mainnet.json --repeat 1 --out runs/serving/zaino-0.10.1-r1

The server runs in its own systemd unit on CPUs disjoint from the load generator (AllowedCPUs),
for every system alike. Workloads are deterministic: unary requests cycle through seed-derived
arrays, and streaming ranges derive their start height from ghz's request number, so every server
receives the same request sequence for the same request count.

Suites:
  latency   one client, one connection, sequential; 1,000 measured requests per RPC (50 warmup)
  ranges    one client; GetBlockRange of 100 / 1,000 / 10,000 / 100,000 blocks
  scaling   1 / 8 / 32 / 128 clients, one connection each, 30 s: GetBlockRange(1,000) and GetBlock
  sync      one client downloads [Sapling activation, upper] in sequential 10,000-block chunks

Per scenario: the raw ghz JSON report (every request's latency and status), server CPU seconds and
peak memory from its cgroup (plus Zebra's for Zaino), and the load generator's CPU time.
"""

from __future__ import annotations

import argparse
import base64
import datetime
import json
import os
import pathlib
import subprocess
import sys
import threading
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import common  # noqa: E402
from common import V  # noqa: E402

SERVICE = "cash.z.wallet.sdk.rpc.CompactTxStreamer"
PROTO_DIR = common.ROOT / "proto" / "lightwallet-protocol"
STRIDE = 2_654_435_761  # odd multiplier for the request-number -> height sequence (Knuth)


def range_template(lo: int, hi: int, size: int, offset: int) -> str:
    """ghz call-data template: a deterministic sequence of `size`-block ranges within [lo, hi].

    ghz parses call data as JSON before templating, so each expression sits in a string; proto3 JSON
    accepts uint64 fields as strings."""
    span = hi - size + 1 - lo + 1
    start = f"(add {lo} (mod (add (mul .RequestNumber {STRIDE}) {offset}) {span}))"
    return ('{"start":{"height":"{{ ' + start + ' }}"},"end":{"height":"{{ add ' + start + f' {size - 1}' + ' }}"}}')


def sync_template(lo: int, hi: int, chunk: int) -> str:
    start = f"(add {lo} (mul .RequestNumber {chunk}))"
    return ('{"start":{"height":"{{ ' + start + ' }}"},"end":{"height":"{{ min (add ' + start + f' {chunk - 1}) {hi}' + ' }}"}}')


def build_data(out: pathlib.Path, lo: int, hi: int, seed: int, fixtures: dict) -> dict[str, pathlib.Path]:
    import lw
    rng = lw.SplitMix64(seed)
    heights = [lo + rng.below(hi - lo + 1) for _ in range(2_000)]
    files = {
        "heights": [{"height": h} for h in heights],
        "txids": [{"hash": base64.b64encode(lw.internal_bytes(t)).decode()} for t in fixtures.get("txids", [])],
        "balances": [{"addresses": [a]} for a in fixtures.get("addresses", {}).values()],
        "utxos": [{"addresses": [a], "startHeight": lo, "maxEntries": 0} for a in fixtures.get("addresses", {}).values()],
    }
    paths = {}
    for name, rows in files.items():
        if rows:
            paths[name] = out / f"data-{name}.json"
            paths[name].write_text(json.dumps(rows))
    return paths


def scenarios(lo: int, hi: int, data: dict[str, pathlib.Path], quick: bool) -> list[dict]:
    n = 200 if quick else 1_000
    plan = []

    def unary(name, method, **kw):
        plan.append({"suite": "latency", "name": name, "method": method, "concurrency": 1, "total": n + 50,
                     "skip_first": 50, **kw})

    unary("GetLightdInfo", "GetLightdInfo", data_json="{}")
    unary("GetLatestBlock", "GetLatestBlock", data_json="{}")
    unary("GetBlock", "GetBlock", data_file=data["heights"])
    unary("GetBlockNullifiers", "GetBlockNullifiers", data_file=data["heights"])
    unary("GetTreeState", "GetTreeState", data_file=data["heights"])
    unary("GetLatestTreeState", "GetLatestTreeState", data_json="{}")
    unary("GetSubtreeRoots/sapling-10", "GetSubtreeRoots", data_json='{"startIndex":0,"shieldedProtocol":"sapling","maxEntries":10}')
    unary("GetSubtreeRoots/orchard-10", "GetSubtreeRoots", data_json='{"startIndex":0,"shieldedProtocol":"orchard","maxEntries":10}')
    unary("GetMempoolTx", "GetMempoolTx", data_json="{}")
    if "txids" in data:
        unary("GetTransaction", "GetTransaction", data_file=data["txids"])
    if "balances" in data:
        unary("GetTaddressBalance", "GetTaddressBalance", data_file=data["balances"])
        unary("GetAddressUtxos", "GetAddressUtxos", data_file=data["utxos"])

    for size, total in ((100, 1_000), (1_000, 300), (10_000, 100), (100_000, 10)):
        total = max(3, total // 5) if quick else total
        plan.append({"suite": "ranges", "name": f"GetBlockRange/{size}", "method": "GetBlockRange",
                     "concurrency": 1, "total": total + 2, "skip_first": 2, "blocks_per_call": size,
                     "data_template": range_template(lo, hi, size, offset=size)})

    for clients in (1, 8, 32, 128):
        seconds = 10 if quick else 30
        plan.append({"suite": "scaling", "name": f"GetBlockRange/1000 x{clients}", "method": "GetBlockRange",
                     "concurrency": clients, "duration": f"{seconds}s", "blocks_per_call": 1_000,
                     "data_template": range_template(lo, hi, 1_000, offset=clients)})
        plan.append({"suite": "scaling", "name": f"GetBlock x{clients}", "method": "GetBlock",
                     "concurrency": clients, "duration": f"{seconds}s", "data_file": data["heights"]})

    chunk = 10_000
    chunks = (hi - lo) // chunk + 1
    plan.append({"suite": "sync", "name": f"sync {lo}-{hi}", "method": "GetBlockRange", "concurrency": 1,
                 "total": chunks, "blocks_total": hi - lo + 1, "data_template": sync_template(lo, hi, chunk),
                 "timeout": "600s"})
    return plan


class CgroupWatch:
    """Samples cgroups every 0.5 s on a thread while a scenario runs."""

    def __init__(self, paths: dict[str, pathlib.Path]):
        self.paths = paths
        self.peak = {k: 0 for k in paths}
        self.peak_anon = {k: 0 for k in paths}
        self.start = {k: common.read_cgroup(p) for k, p in paths.items()}
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self):
        while not self._stop.wait(0.5):
            for k, p in self.paths.items():
                stats = common.read_cgroup(p)
                self.peak[k] = max(self.peak[k], stats["mem_bytes"])
                self.peak_anon[k] = max(self.peak_anon[k], stats["anon_bytes"])

    def finish(self) -> dict:
        self._stop.set()
        self._thread.join()
        result = {}
        for k, p in self.paths.items():
            end = common.read_cgroup(p)
            result[k] = {"cpu_seconds": (end["cpu_usec"] - self.start[k]["cpu_usec"]) / 1e6,
                         "peak_anon_memory_bytes_sampled": max(self.peak_anon[k], end["anon_bytes"]),
                         "peak_cgroup_memory_bytes_sampled": max(self.peak[k], end["mem_bytes"]),
                         "read_bytes": end["rbytes"] - self.start[k]["rbytes"],
                         "write_bytes": end["wbytes"] - self.start[k]["wbytes"]}
        return result


def run_ghz(scenario: dict, endpoint: str, out: pathlib.Path, client_cpus: str) -> dict:
    import resource  # POSIX only; the benchmark host is Linux

    report = out / f"{scenario['suite']}--{scenario['name'].replace('/', '_').replace(' ', '_')}.json"
    args = ["taskset", "-c", client_cpus, f"{V['OPT']}/bin/ghz", "--insecure",
            "--proto", str(PROTO_DIR / "service.proto"), "--import-paths", str(PROTO_DIR),
            "--call", f"{SERVICE}.{scenario['method']}",
            "--concurrency", str(scenario["concurrency"]), "--connections", str(scenario["concurrency"]),
            "--timeout", scenario.get("timeout", "120s"), "--max-recv-message-size", "256MB",
            "--format", "json", "--output", str(report)]
    if "duration" in scenario:
        args += ["--duration", scenario["duration"], "--duration-stop", "wait"]
    else:
        args += ["--total", str(scenario["total"])]
    if scenario.get("skip_first"):
        args += ["--skipFirst", str(scenario["skip_first"])]
    if "data_file" in scenario:
        args += ["--data-file", str(scenario["data_file"])]
    elif "data_template" in scenario:
        args += ["--data", scenario["data_template"]]
    else:
        args += ["--data", scenario.get("data_json", "{}")]
    args.append(endpoint)

    before = resource.getrusage(resource.RUSAGE_CHILDREN)
    started = time.time()
    proc = subprocess.run(args, capture_output=True, text=True)
    elapsed = time.time() - started
    after = resource.getrusage(resource.RUSAGE_CHILDREN)
    result = {"command": common.quote(args), "exit_code": proc.returncode, "stderr": proc.stderr[-2000:],
              "wall_seconds": elapsed, "report_file": report.name,
              "client_cpu_seconds": (after.ru_utime - before.ru_utime) + (after.ru_stime - before.ru_stime)}
    if report.exists():
        r = json.loads(report.read_text())
        dist = {d["percentage"]: d["latency"] for d in r.get("latencyDistribution") or []}
        ok = r.get("statusCodeDistribution", {}).get("OK", 0)
        result.update({
            "count": r.get("count"), "ok": ok, "status_codes": r.get("statusCodeDistribution"),
            "errors": r.get("errorDistribution"), "rps": r.get("rps"), "total_ns": r.get("total"),
            "latency_ns": {"average": r.get("average"), "fastest": r.get("fastest"), "slowest": r.get("slowest"),
                           "p50": dist.get(50), "p90": dist.get(90), "p95": dist.get(95), "p99": dist.get(99)},
        })
        seconds = (r.get("total") or 0) / 1e9
        if scenario.get("blocks_per_call") and seconds:
            result["blocks_per_second"] = ok * scenario["blocks_per_call"] / seconds
        if scenario.get("blocks_total") and seconds and ok == scenario["total"]:
            result["blocks_per_second"] = scenario["blocks_total"] / seconds
    return result


def wait_ready(system, upper: int, timeout: float) -> float:
    import lw
    from lw import pb
    started = time.time()
    while time.time() - started < timeout:
        try:
            stub = lw.connect(f"http://{system.grpc}", ready_timeout=2)
            tip = stub.GetLatestBlock(pb.ChainSpec(), timeout=5).height
            stub.GetBlock(pb.BlockID(height=upper), timeout=30)
            # The index was built by the index-build step; serving the tip and the upper block is enough.
            # (A restarted Zaino with a complete index does not re-publish its sync-target metric.)
            if tip >= upper + 100:
                return time.time() - started
        except Exception:
            pass
        time.sleep(5)
    raise TimeoutError(f"{system.name} not ready (tip >= upper+100, index at target) within {timeout}s")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--system", required=True, choices=sorted(common.systems()))
    parser.add_argument("--upper", type=int, required=True, help="fixed highest height for every workload")
    parser.add_argument("--lower", type=int, default=common.SAPLING_ACTIVATION, help="default: Sapling activation")
    parser.add_argument("--fixtures", type=pathlib.Path, required=True)
    parser.add_argument("--out", type=pathlib.Path, required=True)
    parser.add_argument("--repeat", type=int, default=1)
    parser.add_argument("--seed", type=int, default=20261009)
    parser.add_argument("--suites", default="latency,ranges,scaling,sync")
    parser.add_argument("--client-cpus", type=int, default=0, help="CPUs reserved for ghz (default: 1/4 of host)")
    parser.add_argument("--quick", action="store_true", help="smaller sample counts, for smoke tests")
    parser.add_argument("--ready-timeout", type=float, default=3600)
    parser.add_argument("--tcp-nodelay", type=pathlib.Path, metavar="SHIM",
                        help="diagnostic: LD_PRELOAD this build of ci/nodelay.c into the server")
    args = parser.parse_args()

    system = common.systems()[args.system]
    if args.out.exists() and any(args.out.iterdir()):
        sys.exit(f"{args.out} is not empty")
    args.out.mkdir(parents=True)
    fixtures = json.loads(args.fixtures.read_text())

    ncpu = os.cpu_count()
    reserve = args.client_cpus or max(2, ncpu // 4)
    server_cpus, client_cpus = f"0-{ncpu - reserve - 1}", f"{ncpu - reserve}-{ncpu - 1}"
    if system.family == "zaino" and common.sh("systemctl", "is-active", "zebrad", check=False).strip() != "active":
        sys.exit("zebrad.service is not running")
    if system.family == "ztreamer" and not common.FROZEN:
        subprocess.run(["systemctl", "stop", "zebrad"], check=False)

    config = system.render_config(args.out)
    env = {"RUST_LOG": "warn"}
    if args.tcp_nodelay:
        env["LD_PRELOAD"] = str(args.tcp_nodelay.resolve())
    unit = common.Unit(f"zbench-serve-{system.name}", system.command(str(config)), env=env,
                       properties=[f"AllowedCPUs={server_cpus}"])
    if system.family == "zaino":
        subprocess.run(["systemctl", "set-property", "--runtime", "zebrad", f"AllowedCPUs={server_cpus}"], check=False)

    data = build_data(args.out, args.lower, args.upper, args.seed, fixtures)
    plan = [s for s in scenarios(args.lower, args.upper, data, args.quick) if s["suite"] in args.suites.split(",")]
    meta = {"system": system.name, "repeat": args.repeat, "upper": args.upper, "lower": args.lower, "seed": args.seed,
            "server_cpus": server_cpus, "client_cpus": client_cpus, "fixtures": fixtures,
            "provenance": common.provenance(system.name), "command": common.quote(unit.command),
            "ghz": common.sh(f"{V['OPT']}/bin/ghz", "--version", check=False).strip(),
            "started_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "cache": "warm: index built earlier, no cache drop; warmups excluded via --skipFirst",
            "tcp_nodelay_shim": bool(args.tcp_nodelay)}
    (args.out / "hardware.json").write_text(common.sh(str(common.ROOT / "server" / "collect-hardware.sh"), check=False))

    unit_started = time.time()
    unit.start()
    results = []
    try:
        meta["seconds_to_ready"] = wait_ready(system, args.upper, args.ready_timeout)
        import lw
        from lw import pb
        info = lw.connect(f"http://{system.grpc}").GetLightdInfo(pb.Empty(), timeout=10)
        meta["lightd_info"] = lw.canonical(info)
        watch_paths = {"server": unit.cgroup}
        if system.family == "zaino":
            watch_paths["zebrad"] = common.cgroup_path("zebrad.service")
        for i, scenario in enumerate(plan, 1):
            watch = CgroupWatch(watch_paths)
            outcome = run_ghz(scenario, system.grpc, args.out, client_cpus)
            outcome["resources"] = watch.finish()
            row = {k: v for k, v in scenario.items() if k not in ("data_file",)} | outcome
            row["data_file"] = scenario["data_file"].name if "data_file" in scenario else None
            results.append(row)
            p50 = (outcome.get("latency_ns") or {}).get("p50")
            print(f"[{i}/{len(plan)}] {system.name} {scenario['name']}: ok={outcome.get('ok')} "
                  f"p50={p50 / 1e6 if p50 else float('nan'):.3f}ms bps={outcome.get('blocks_per_second', 0):,.0f}",
                  file=sys.stderr)
            (args.out / "results.json").write_text(json.dumps({"meta": meta, "results": results}, indent=2))
    finally:
        unit.stop()
        if system.family == "zaino":
            subprocess.run(["systemctl", "set-property", "--runtime", "zebrad", "AllowedCPUs="], check=False)
        elif not common.FROZEN:
            subprocess.run(["systemctl", "start", "zebrad"], check=False)
        (args.out / "journal.log").write_text(unit.journal(unit_started))
        meta["finished_utc"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        (args.out / "results.json").write_text(json.dumps({"meta": meta, "results": results}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
