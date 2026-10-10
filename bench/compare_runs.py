#!/usr/bin/env python3
"""Compare one serving run against baseline runs of the same build on the same runner CPU.

    compare_runs.py --run runs-diagnostic/zaino-0.10.1-r1-nodelay --baseline runs \
        --out results/diagnostic-tcp-nodelay.md

Used for the TCP_NODELAY diagnostic: the build under test is unchanged, so only baseline runs whose
runner reported the same CPU model are compared. Mean latency is listed beside p50 because some
streaming distributions are bimodal and their median moves between runs.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import statistics
import sys

from report import cpu_model, run_dirs


def scenarios(run: pathlib.Path):
    data = json.loads((run / "serving" / "results.json").read_text())
    return data["meta"], {(s["suite"], s["name"]): s for s in data["results"]}


def value(s, unit):
    if unit == "blocks/s" and s.get("blocks_per_second"):
        return s["blocks_per_second"]
    return s.get("rps")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--run", type=pathlib.Path, action="append", required=True)
    parser.add_argument("--baseline", type=pathlib.Path, required=True, help="directory of <system>-r<k> runs")
    parser.add_argument("--out", type=pathlib.Path, required=True)
    args = parser.parse_args()

    md = ["# Serving with TCP_NODELAY forced on (diagnostic)", "",
          "Each diagnostic run is the unmodified build with `ci/nodelay.c` preloaded, compared with the",
          "default runs of the same build on a runner with the same CPU model. Latency in ms; throughput",
          "in blocks/s for ranges and sync, requests/s otherwise.", ""]
    for run in args.run:
        meta, diag = scenarios(run)
        cpu = cpu_model(run / "serving" / "hardware.json")
        base = [d for system, _, d in run_dirs(args.baseline)
                if system == meta["system"] and cpu_model(d / "serving" / "hardware.json") == cpu]
        if not base:
            print(f"no baseline for {meta['system']} on {cpu}", file=sys.stderr)
            return 1
        bases = [scenarios(d)[1] for d in base]
        md += [f"## {meta['system']}", "",
               f"Runner CPU {cpu}. Diagnostic `{run.name}` vs {', '.join(f'`{d.name}`' for d in base)}"
               f" (median if more than one).", "",
               "| Scenario | p50 default | p50 nodelay | mean default | mean nodelay | throughput default | throughput nodelay |",
               "|---|---:|---:|---:|---:|---:|---:|"]
        for key, s in diag.items():
            b = [x[key] for x in bases if key in x]
            unit = "blocks/s" if key[0] in ("ranges", "sync") or "Range" in key[1] else "req/s"
            p50 = lambda r: r["latency_ns"]["p50"] / 1e6  # noqa: E731
            avg = lambda r: r["latency_ns"]["average"] / 1e6  # noqa: E731
            md.append(f"| {key[1]} | {statistics.median(map(p50, b)):.2f} | {p50(s):.2f} "
                      f"| {statistics.median(map(avg, b)):.2f} | {avg(s):.2f} "
                      f"| {statistics.median(value(x, unit) for x in b):,.0f} | {value(s, unit):,.0f} |")
        md.append("")
    args.out.write_text("\n".join(md), encoding="utf-8")
    print(f"wrote {args.out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
