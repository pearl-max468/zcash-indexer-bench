#!/usr/bin/env python3
"""Aggregate raw runs into summary tables and figures.

    report.py --runs runs/ --out results/

Reads runs/<system>-r<k>/index/run.json and runs/<system>-r<k>/serving/results.json.
Writes CSV tables (one row per run, plus medians across repeats), markdown tables, and SVG/PNG
figures. Every figure has a table with the same numbers, and values are labelled on the marks.
"""

from __future__ import annotations

import argparse
import csv
import json
import pathlib
import re
import statistics
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import matplotlib.ticker  # noqa: E402,F401

# Validated categorical slots (dataviz reference palette, light mode); colour follows the system.
COLORS = {"zaino-0.10.1": "#2a78d6", "ztreamer-v0.1.0": "#eb6834", "zaino-0.9.0": "#1baf7a", "ztreamer-master": "#eda100"}
ORDER = list(COLORS)
SURFACE, INK, INK_2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "axes.edgecolor": GRID, "axes.labelcolor": INK_2, "xtick.color": INK_2, "ytick.color": INK_2,
    "text.color": INK, "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8,
    "axes.spines.top": False, "axes.spines.right": False, "font.size": 10, "axes.titlesize": 12,
    "axes.titleweight": "semibold", "axes.titlelocation": "left", "legend.frameon": False,
})


def run_dirs(runs: pathlib.Path):
    for d in sorted(p for p in runs.iterdir() if p.is_dir()):
        m = re.fullmatch(r"(.+)-r(\d+)", d.name)
        if m:
            yield m.group(1), int(m.group(2)), d


def cpu_model(path: pathlib.Path) -> str:
    try:
        hw = json.loads(path.read_text())
        for field in hw["cpu"]["lscpu"]:
            if field["field"].startswith("Model name"):
                return field["data"]
    except (OSError, KeyError, TypeError, json.JSONDecodeError):
        pass
    return ""


def med(values):
    values = [v for v in values if v is not None]
    return statistics.median(values) if values else None


def fmt(v, unit="", digits=1):
    if v is None:
        return "–"
    if abs(v) >= 1000 and not unit:
        return f"{v:,.0f}"
    return f"{v:,.{digits}f}{unit}"


def gib(b):
    return None if b is None else b / 2**30


# ---------------------------------------------------------------- index builds

def index_rows(runs):
    rows = []
    for system, repeat, d in run_dirs(runs):
        f = d / "index" / "run.json"
        if not f.exists():
            continue
        r = json.loads(f.read_text())
        res, z = r["resources"]["indexer_process"], r["resources"].get("zebrad_during_run") or {}
        stack_cpu = res["cpu_seconds"] + (z.get("cpu_seconds") or 0)
        rows.append({
            "system": system, "repeat": repeat, "status": r["status"], "cache": r["cache"],
            "target_height": (r.get("target") or {}).get("height"),
            "seconds_to_completion": r["headline"]["seconds_to_completion"],
            "seconds_to_first_grpc_answer": r["headline"]["seconds_to_first_grpc_answer"],
            "indexer_cpu_seconds": res["cpu_seconds"], "indexer_peak_memory_gib": gib(res["peak_memory_bytes"]),
            "indexer_written_gib": gib(res["write_bytes"]), "indexer_read_gib": gib(res["read_bytes"]),
            "zebrad_cpu_seconds": z.get("cpu_seconds"), "zebrad_peak_memory_gib": gib(z.get("peak_memory_bytes_sampled")),
            "stack_cpu_seconds": stack_cpu, "index_size_gib": gib(r["resources"]["index_bytes_on_disk"]),
            "runner_cpu": cpu_model(d / "index" / "hardware-before.json"),
        })
    return rows


# ---------------------------------------------------------------- serving

def serving_rows(runs):
    rows = []
    for system, repeat, d in run_dirs(runs):
        f = d / "serving" / "results.json"
        if not f.exists():
            continue
        data = json.loads(f.read_text())
        for s in data["results"]:
            lat = s.get("latency_ns") or {}
            res = (s.get("resources") or {})
            rows.append({
                "system": system, "repeat": repeat, "suite": s["suite"], "scenario": s["name"],
                "concurrency": s["concurrency"], "count": s.get("count"), "ok": s.get("ok"),
                "p50_ms": lat.get("p50") and lat["p50"] / 1e6, "p95_ms": lat.get("p95") and lat["p95"] / 1e6,
                "p99_ms": lat.get("p99") and lat["p99"] / 1e6, "rps": s.get("rps"),
                "blocks_per_second": s.get("blocks_per_second"),
                "server_cpu_seconds": (res.get("server") or {}).get("cpu_seconds"),
                "zebrad_cpu_seconds": (res.get("zebrad") or {}).get("cpu_seconds"),
                "client_cpu_seconds": s.get("client_cpu_seconds"), "wall_seconds": s.get("wall_seconds"),
                "errors": json.dumps(s.get("errors") or {}),
            })
    return rows


def medians(rows, keys, values):
    groups = {}
    for r in rows:
        groups.setdefault(tuple(r[k] for k in keys), []).append(r)
    out = []
    for key, rs in groups.items():
        row = dict(zip(keys, key))
        row["runs"] = len(rs)
        for v in values:
            vals = [r[v] for r in rs if r[v] is not None]
            row[v] = med(vals)
            row[f"{v}_min"] = min(vals) if vals else None
            row[f"{v}_max"] = max(vals) if vals else None
        out.append(row)
    return out


def write_csv(path, rows):
    if not rows:
        return
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


# ---------------------------------------------------------------- figures

def systems_in(rows):
    present = {r["system"] for r in rows}
    return [s for s in ORDER if s in present] + sorted(present - set(ORDER))


def bar_chart(path, title, rows, value, unit, log=False):
    systems = systems_in(rows)
    by = {r["system"]: r for r in rows}
    fig, ax = plt.subplots(figsize=(7.5, 0.6 * len(systems) + 1.4))
    for i, s in enumerate(systems):
        v = by[s][value]
        if v is None:
            continue
        lo, hi = by[s].get(f"{value}_min"), by[s].get(f"{value}_max")
        ax.barh(i, v, height=0.55, color=COLORS.get(s, "#888"), zorder=2)
        if lo is not None and hi is not None and by[s]["runs"] > 1:
            ax.plot([lo, hi], [i, i], color=INK, linewidth=1.2, zorder=3)
        ax.text(v, i, f"  {fmt(v)}{unit}", va="center", ha="left", color=INK, fontsize=9, zorder=4)
    ax.set_yticks(range(len(systems)), systems)
    ax.invert_yaxis()
    ax.grid(axis="y", visible=False)
    if log:
        ax.set_xscale("log")
    ax.set_xlim(right=ax.get_xlim()[1] * (3 if log else 1.18))
    ax.set_title(title)
    ax.set_xlabel(unit.strip() + (" (log scale)" if log else ""))
    fig.tight_layout()
    for ext in ("svg", "png"):
        fig.savefig(path.with_suffix(f".{ext}"), dpi=160)
    plt.close(fig)


def grouped_latency(path, rows):
    """Dot plot on a log axis: dot = median, whisker = median to p99. Dots, not bars, because a log
    axis has no zero for a bar to start from."""
    rows = [r for r in rows if r["suite"] == "latency" and r["p50_ms"] is not None]
    if not rows:
        return
    systems = systems_in(rows)
    scenarios = list(dict.fromkeys(r["scenario"] for r in rows))
    by = {(r["system"], r["scenario"]): r for r in rows}
    h = 0.8 / len(systems)
    fig, ax = plt.subplots(figsize=(8.5, 0.28 * len(scenarios) * len(systems) + 1.9))
    for j, s in enumerate(systems):
        for i, sc in enumerate(scenarios):
            r = by.get((s, sc))
            if not r:
                continue
            y = i + (j - (len(systems) - 1) / 2) * h
            color = COLORS.get(s, "#888")
            if r["p99_ms"]:
                ax.plot([r["p50_ms"], r["p99_ms"]], [y, y], color=color, linewidth=2, solid_capstyle="round", zorder=2)
            ax.plot([r["p50_ms"]], [y], marker="o", markersize=7, color=color, markeredgecolor=SURFACE,
                    markeredgewidth=1.5, zorder=3, linestyle="none", label=s if i == 0 else None)
            ax.annotate(f"{r['p50_ms']:.3g}", (r["p50_ms"], y), textcoords="offset points", xytext=(-6, 0),
                        ha="right", va="center", fontsize=7, color=INK_2)
    ax.set_yticks(range(len(scenarios)), scenarios)
    ax.invert_yaxis()
    ax.set_xscale("log")
    ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:g}"))
    ax.grid(axis="y", visible=False)
    ax.set_xlabel("milliseconds, log scale — dot: median (p50), line: to p99")
    ax.set_title("Per-request latency, one client, sequential requests", pad=28)
    ax.legend(loc="lower left", bbox_to_anchor=(0, 1.0), ncol=len(systems), fontsize=8, handletextpad=0.3)
    fig.tight_layout()
    for ext in ("svg", "png"):
        fig.savefig(path.with_suffix(f".{ext}"), dpi=160)
    plt.close(fig)


def line_chart(path, title, rows, x_key, x_label, y_key, y_label):
    if not rows:
        return
    systems = systems_in(rows)
    fig, ax = plt.subplots(figsize=(7.5, 4.2))
    for s in systems:
        pts = sorted((r[x_key], r[y_key]) for r in rows if r["system"] == s and r[y_key] is not None)
        if not pts:
            continue
        xs, ys = zip(*pts)
        ax.plot(xs, ys, color=COLORS.get(s, "#888"), linewidth=2, marker="o", markersize=5, label=s, zorder=3)
        ax.annotate(f"{ys[-1]:,.0f}", (xs[-1], ys[-1]), textcoords="offset points", xytext=(6, 0),
                    va="center", fontsize=8, color=INK)
    ax.set_xscale("log")
    xs_all = sorted({r[x_key] for r in rows})
    ax.set_xticks(xs_all, [f"{x:,}" for x in xs_all])
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    ax.set_ylim(bottom=0)
    ax.set_title(title)
    ax.legend(fontsize=8)
    fig.tight_layout()
    for ext in ("svg", "png"):
        fig.savefig(path.with_suffix(f".{ext}"), dpi=160)
    plt.close(fig)


# ---------------------------------------------------------------- markdown

def md_table(headers, rows):
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join("---:" if i else "---" for i in range(len(headers))) + "|"]
    lines += ["| " + " | ".join(str(c) for c in row) + " |" for row in rows]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--runs", type=pathlib.Path, required=True)
    parser.add_argument("--out", type=pathlib.Path, required=True)
    args = parser.parse_args()
    figures = args.out / "figures"
    figures.mkdir(parents=True, exist_ok=True)
    md = ["# Results", ""]

    idx = index_rows(args.runs)
    write_csv(args.out / "index-runs.csv", idx)
    if idx:
        values = ["seconds_to_completion", "seconds_to_first_grpc_answer", "indexer_cpu_seconds", "indexer_peak_memory_gib",
                  "indexer_written_gib", "zebrad_cpu_seconds", "zebrad_peak_memory_gib", "stack_cpu_seconds", "index_size_gib"]
        agg = medians(idx, ["system"], values)
        write_csv(args.out / "index-summary.csv", agg)
        agg.sort(key=lambda r: ORDER.index(r["system"]) if r["system"] in ORDER else 99)
        md += ["## Initial index build (from empty, backing node at the frozen tip)", "",
               md_table(["System", "Runs", "Time to complete", "First gRPC answer", "Indexer CPU-s", "Indexer peak RAM",
                         "Zebra CPU-s (during)", "Zebra peak RAM", "Written by indexer", "Index on disk"],
                        [[r["system"], r["runs"], fmt(r["seconds_to_completion"], " s", 0),
                          fmt(r["seconds_to_first_grpc_answer"], " s", 0), fmt(r["indexer_cpu_seconds"], "", 0),
                          fmt(r["indexer_peak_memory_gib"], " GiB", 2), fmt(r["zebrad_cpu_seconds"], "", 0),
                          fmt(r["zebrad_peak_memory_gib"], " GiB", 2), fmt(r["indexer_written_gib"], " GiB", 2),
                          fmt(r["index_size_gib"], " GiB", 2)] for r in agg]),
               "", "Medians across repeats; whiskers in figures show min–max. Ztreamer's indexer figures include its "
                   "embedded Zakura node; Zaino's exclude Zebra, which is listed separately.", ""]
        bar_chart(figures / "index-time", "Time to a complete index (from empty)", agg, "seconds_to_completion", " s")
        bar_chart(figures / "index-peak-memory", "Peak memory of the indexer process", agg, "indexer_peak_memory_gib", " GiB")
        bar_chart(figures / "index-cpu", "CPU time spent building the index", agg, "indexer_cpu_seconds", " s")
        bar_chart(figures / "index-size", "Index size on disk", agg, "index_size_gib", " GiB")

    srv = serving_rows(args.runs)
    write_csv(args.out / "serving-runs.csv", srv)
    if srv:
        agg = medians(srv, ["system", "suite", "scenario", "concurrency"],
                      ["p50_ms", "p95_ms", "p99_ms", "rps", "blocks_per_second", "server_cpu_seconds", "client_cpu_seconds"])
        write_csv(args.out / "serving-summary.csv", agg)
        systems = systems_in(agg)
        by = {(r["system"], r["scenario"]): r for r in agg}
        for suite, metric, label in (("latency", "p50_ms", "p50 / p99 ms"), ("ranges", "blocks_per_second", "blocks/s"),
                                     ("scaling", "blocks_per_second", "blocks/s or req/s"), ("sync", "blocks_per_second", "blocks/s")):
            scen = list(dict.fromkeys(r["scenario"] for r in agg if r["suite"] == suite))
            if not scen:
                continue
            table = []
            for sc in scen:
                cells = [sc]
                for s in systems:
                    r = by.get((s, sc))
                    if not r:
                        cells.append("–")
                    elif suite == "latency":
                        cells.append(f"{fmt(r['p50_ms'], '', 3)} / {fmt(r['p99_ms'], '', 3)}")
                    elif "GetBlock x" in sc:
                        cells.append(fmt(r["rps"], " req/s", 0))
                    else:
                        cells.append(fmt(r["blocks_per_second"], "", 0))
                table.append(cells)
            md += [f"## Serving: {suite} ({label})", "", md_table(["Scenario"] + systems, table), ""]
        grouped_latency(figures / "latency", agg)
        ranges = [dict(r, size=int(r["scenario"].split("/")[1])) for r in agg if r["suite"] == "ranges"]
        line_chart(figures / "range-throughput", "GetBlockRange throughput by range size (one client)", ranges,
                   "size", "blocks per request", "blocks_per_second", "blocks / second")
        scaling = [r for r in agg if r["suite"] == "scaling" and r["scenario"].startswith("GetBlockRange")]
        line_chart(figures / "scaling-ranges", "GetBlockRange(1,000) throughput by concurrent clients", scaling,
                   "concurrency", "concurrent clients", "blocks_per_second", "blocks / second")
        unary = [r for r in agg if r["suite"] == "scaling" and r["scenario"].startswith("GetBlock x")]
        line_chart(figures / "scaling-getblock", "GetBlock requests per second by concurrent clients", unary,
                   "concurrency", "concurrent clients", "rps", "requests / second")
        sync = [r for r in agg if r["suite"] == "sync"]
        bar_chart(figures / "wallet-sync", "Full compact-block download (Sapling activation to upper height)", sync,
                  "blocks_per_second", " blocks/s")

    (args.out / "results.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"wrote {args.out}/results.md, CSV tables and figures/", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
