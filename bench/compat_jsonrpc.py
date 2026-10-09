#!/usr/bin/env python3
"""JSON-RPC coverage and agreement: the 28 methods Zaino 0.10.1 serves, called on every server.

    compat_jsonrpc.py --server zaino=http://127.0.0.1:8237 \
        --server ztreamer=http://127.0.0.1:8242,cookie=/data/zakura-cookie/.cookie \
        --reference zebra=http://127.0.0.1:8232,cookie=/data/zebra-cookie/.cookie \
        --fixtures fixtures/mainnet.json --height 3500000 --out runs/compat-jsonrpc/<run>

Ztreamer has no JSON-RPC server of its own; its embedded Zakura node's RPC is what it offers
(the README's "24 of the 27 JSON-RPC requests provided by Zaino direct mode").
Each call's status and result are recorded; deterministic results are compared with the reference.
"""

from __future__ import annotations

import argparse
import csv
import datetime
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from zebra_rpc import JsonRpc, RpcError  # noqa: E402

# Results that depend on the moment of the call (tip, mempool, peers, uptime) are recorded, not compared.
VOLATILE = {"getinfo", "getblockchaininfo", "getblockcount", "getbestblockhash", "getdifficulty", "getmininginfo",
            "getnetworksolps", "getpeerinfo", "getmempoolinfo", "getrawmempool", "getchaintips", "gettxoutsetinfo",
            "getaddressbalance", "getaddressutxos", "sendrawtransaction"}


def parse_endpoint(spec: str) -> tuple[str, JsonRpc, str]:
    name, _, rest = spec.partition("=")
    url, *opts = rest.split(",")
    kwargs = dict(o.split("=", 1) for o in opts)
    return name, JsonRpc(url, cookie=kwargs.get("cookie"), userpass=kwargs.get("userpass"), timeout=120), url


def build_calls(ref: JsonRpc, fixtures: dict, height: int) -> list[tuple[str, str, list]]:
    block_hash = ref.call("getblockhash", height)
    txid = fixtures["txids"][0]
    raw = ref.call("getrawtransaction", txid, 0)
    addresses = list(fixtures.get("addresses", {}).values())
    quiet = fixtures["addresses"].get("quiet") or addresses[-1]
    utxos = ref.call("getaddressutxos", {"addresses": [quiet]})
    calls = [
        ("getinfo", "", []), ("getblockchaininfo", "", []), ("getblockcount", "", []),
        ("getbestblockhash", "", []), ("getdifficulty", "", []), ("getmininginfo", "", []),
        ("getnetworksolps", "", []), ("getpeerinfo", "", []), ("getmempoolinfo", "", []),
        ("getrawmempool", "", []), ("getchaintips", "", []), ("gettxoutsetinfo", "", []),
        ("getblock", "height verbosity 0", [str(height), 0]),
        ("getblock", "height verbosity 1", [str(height), 1]),
        ("getblock", "height verbosity 2", [str(height), 2]),
        ("getblock", "hash verbosity 1", [block_hash, 1]),
        ("getblockheader", "verbose", [block_hash, True]),
        ("getblockheader", "hex", [block_hash, False]),
        ("getblockdeltas", "", [block_hash]),
        ("getblocksubsidy", "", [height]),
        ("getrawtransaction", "hex", [txid, 0]),
        ("getrawtransaction", "verbose", [txid, 1]),
        ("getspentinfo", "output 0", [{"txid": txid, "index": 0}]),
        ("sendrawtransaction", "already mined", [raw]),
        ("validateaddress", "", [quiet]),
        ("z_validateaddress", "", [quiet]),
        ("z_gettreestate", "", [str(height)]),
        ("z_getsubtreesbyindex", "sapling 0..3", ["sapling", 0, 3]),
        ("z_getsubtreesbyindex", "orchard 0..3", ["orchard", 0, 3]),
        ("getaddressbalance", "", [{"addresses": addresses}]),
        ("getaddresstxids", "quiet, full range", [{"addresses": [quiet], "start": 419_200, "end": height}]),
        ("getaddressutxos", "", [{"addresses": [quiet]}]),
        ("getaddressdeltas", "quiet, full range", [{"addresses": [quiet], "start": 419_200, "end": height}]),
    ]
    if utxos:
        calls.append(("gettxout", "unspent output", [utxos[0]["txid"], utxos[0]["outputIndex"]]))
    else:
        calls.append(("gettxout", "spent/unknown output", [txid, 0]))
    return calls


def invoke(rpc: JsonRpc, method: str, params: list) -> tuple[str, object]:
    try:
        return "ok", rpc.call(method, *params)
    except RpcError as e:
        return f"error {e.code}", e.message
    except OSError as e:
        return "transport error", str(e)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--server", action="append", required=True)
    parser.add_argument("--reference", required=True)
    parser.add_argument("--fixtures", type=pathlib.Path, required=True)
    parser.add_argument("--height", type=int, required=True, help="finalized height for block-specific calls")
    parser.add_argument("--out", type=pathlib.Path, required=True)
    args = parser.parse_args()

    ref_name, ref, ref_url = parse_endpoint(args.reference)
    servers = [parse_endpoint(s) for s in args.server]
    fixtures = json.loads(args.fixtures.read_text())
    calls = build_calls(ref, fixtures, args.height)
    args.out.mkdir(parents=True, exist_ok=True)

    rows, raw = [], []
    for method, case, params in calls:
        expected_status, expected = invoke(ref, method, params)
        row = {"method": method, "case": case, "volatile": method in VOLATILE, f"{ref_name}_status": expected_status}
        for name, rpc, _ in servers:
            status, result = invoke(rpc, method, params)
            row[f"{name}_status"] = status
            if method in VOLATILE or status != "ok" or expected_status != "ok":
                row[f"{name}_matches_{ref_name}"] = ""
            else:
                row[f"{name}_matches_{ref_name}"] = "yes" if result == expected else "NO"
            raw.append({"method": method, "case": case, "server": name, "status": status, "result": result})
        raw.append({"method": method, "case": case, "server": ref_name, "status": expected_status, "result": expected})
        rows.append(row)
        print(f"{method} {case}: " + ", ".join(f"{k}={v}" for k, v in row.items() if k.endswith("_status")), file=sys.stderr)

    with open(args.out / "matrix.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    with open(args.out / "responses.jsonl", "w") as f:
        for r in raw:
            f.write(json.dumps(r, default=str) + "\n")
    (args.out / "metadata.json").write_text(json.dumps({
        "run_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "reference": {ref_name: ref_url}, "servers": {n: u for n, _, u in servers},
        "height": args.height, "fixtures": fixtures, "volatile_methods": sorted(VOLATILE), "argv": sys.argv,
    }, indent=2))

    names = [n for n, _, _ in servers]
    lines = ["# JSON-RPC coverage", "", "| Method | Case | " + " | ".join(names + [ref_name]) + " |",
             "|---|---|" + "---|" * (len(names) + 1)]
    for r in rows:
        cells = []
        for n in names:
            match = r[f"{n}_matches_{ref_name}"]
            cells.append(r[f"{n}_status"] + (f" ({'= ' + ref_name if match == 'yes' else '≠ ' + ref_name})" if match else ""))
        lines.append(f"| {r['method']} | {r['case']} | " + " | ".join(cells + [r[f'{ref_name}_status']]) + " |")
    (args.out / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {args.out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
