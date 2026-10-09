#!/usr/bin/env python3
"""Merge per-system compatibility runs into one cross-system matrix.

Each CI job runs compat_grpc.py / compat_jsonrpc.py against a single system. Inputs are identical
across jobs (same frozen snapshot, seed, fixtures and upper height), so cases line up by
(method, case) and response digests are directly comparable.

    compare_compat.py --runs runs/ --out results/compat
"""

from __future__ import annotations

import argparse
import collections
import csv
import json
import pathlib
import sys


def load_grpc(runs: pathlib.Path) -> tuple[dict, dict]:
    cases: dict[tuple[str, str], dict[str, dict]] = collections.OrderedDict()
    meta = {}
    for results in sorted(runs.glob("*/compat/grpc/results.jsonl")):
        m = json.loads((results.parent / "metadata.json").read_text())
        meta[results.parts[-4]] = {k: m.get(k) for k in ("upper_height", "upper_hash", "seed", "case_count", "lightd_info")}
        for line in results.read_text().splitlines():
            row = json.loads(line)
            cases.setdefault((row["method"], row["case"]), {})[row["server"]] = row
    return cases, meta


def load_jsonrpc(runs: pathlib.Path) -> dict:
    rows: dict[tuple[str, str], dict[str, str]] = collections.OrderedDict()
    for matrix in sorted(runs.glob("*/compat/jsonrpc/matrix.csv")):
        with open(matrix) as f:
            for r in csv.DictReader(f):
                entry = rows.setdefault((r["method"], r["case"]), {"zebra": r.get("zebra_status", ""),
                                                                    "volatile": r["volatile"]})
                for key, value in r.items():
                    if key.endswith("_status") and not key.startswith("zebra"):
                        system = key[: -len("_status")]
                        entry[system] = value
                        entry[f"{system}_matches"] = r.get(f"{system}_matches_zebra", "")
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--runs", type=pathlib.Path, required=True)
    parser.add_argument("--out", type=pathlib.Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    cases, meta = load_grpc(args.runs)
    systems = sorted({s for per in cases.values() for s in per})
    uppers = {m["upper_height"] for m in meta.values()}
    if len(uppers) > 1:
        print(f"warning: runs used different upper heights {uppers}; digests are not comparable", file=sys.stderr)

    rows = []
    for (method, case), per in cases.items():
        row = {"method": method, "case": case}
        for s in systems:
            r = per.get(s)
            row[f"{s}_status"] = r["status"] if r else "not run"
            row[f"{s}_oracle"] = {True: "pass", False: "FAIL", None: ""}[r["oracle_ok"]] if r else ""
            row[f"{s}_note"] = (r["oracle_note"] or r["details"]) if r else ""
        ok = [per[s] for s in systems if s in per and per[s]["status"] == "OK"]
        statuses = {per[s]["status"] for s in systems if s in per}
        if len(statuses) > 1:
            row["agreement"] = "status differs"
        elif len(ok) == len(systems) and len({r["digest"] for r in ok}) == 1:
            row["agreement"] = "identical"
        elif len(ok) == len(systems):
            groups = collections.defaultdict(list)
            for s in systems:
                groups[per[s]["digest"]].append(s)
            row["agreement"] = "differs: " + " | ".join(",".join(g) for g in groups.values())
        else:
            row["agreement"] = f"all {statuses.pop()}" if statuses else "no data"
        rows.append(row)

    columns = ["method", "case", "agreement"] + [f"{s}_{k}" for s in systems for k in ("status", "oracle", "note")]
    with open(args.out / "grpc-matrix.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)

    lines = ["# gRPC compatibility across systems", "",
             f"Inputs: upper height {', '.join(map(str, sorted(uppers)))}; one run per system; Zebra as reference.", "",
             "| Method | Cases | " + " | ".join(f"{s}: OK · ref pass" for s in systems) + " | Byte-identical across all |",
             "|---|---:|" + "---:|" * len(systems) + "---:|"]
    by_method = collections.OrderedDict()
    for r in rows:
        by_method.setdefault(r["method"], []).append(r)
    for method, rs in by_method.items():
        cells = []
        for s in systems:
            ok = sum(r[f"{s}_status"] == "OK" for r in rs)
            checked = [r for r in rs if r[f"{s}_oracle"]]
            passed = sum(r[f"{s}_oracle"] == "pass" for r in checked)
            cells.append(f"{ok}/{len(rs)} · {passed}/{len(checked)}" if checked else f"{ok}/{len(rs)} · –")
        same = sum(r["agreement"] == "identical" or r["agreement"].startswith("all ") for r in rs)
        lines.append(f"| {method} | {len(rs)} | " + " | ".join(cells) + f" | {same}/{len(rs)} |")
    lines += ["", "## Cases where systems differ", ""]
    for r in rows:
        if r["agreement"] not in ("identical",) and not r["agreement"].startswith("all "):
            detail = "; ".join(f"{s}: {r[f'{s}_status']} {r[f'{s}_oracle']} {r[f'{s}_note'][:90]}".strip() for s in systems)
            lines.append(f"- **{r['method']}** `{r['case']}` — {r['agreement']}. {detail}")

    jrows = load_jsonrpc(args.runs)
    if jrows:
        jsystems = sorted({k for e in jrows.values() for k in e if k not in ("zebra", "volatile") and not k.endswith("_matches")})
        lines += ["", "# JSON-RPC coverage", "", "| Method | Case | " + " | ".join(jsystems) + " | Zebra |",
                  "|---|---|" + "---|" * (len(jsystems) + 1)]
        for (method, case), e in jrows.items():
            cells = []
            for s in jsystems:
                match = e.get(f"{s}_matches", "")
                cells.append(e.get(s, "not run") + (" (= zebra)" if match == "yes" else " (≠ zebra)" if match == "NO" else ""))
            lines.append(f"| {method} | {case} | " + " | ".join(cells) + f" | {e['zebra']} |")
    lines += ["", "## Server identity", "", "```json", json.dumps(meta, indent=2), "```", ""]
    (args.out / "compat.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {args.out / 'compat.md'} and grpc-matrix.csv ({len(rows)} cases, systems: {systems})", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
