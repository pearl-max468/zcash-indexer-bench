#!/usr/bin/env python3
"""Choose test transactions and transparent addresses deterministically from the chain.

    make_fixtures.py --zebra-rpc http://127.0.0.1:8232 --zebra-cookie /data/zebra-cookie/.cookie \
        --upper 3510000 --out fixtures/mainnet.json

Selection is seed-driven, never hand-picked: sample block heights with SplitMix64, take one
transaction per block, and keep the first match for each transaction kind. Transparent addresses
come from those transactions' outputs and are bucketed by history length. Ztreamer's own published
fixtures (benchmarks 2026-09-11) are included under `ztreamer-*` labels so its figures are comparable.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import lw  # noqa: E402
from zebra_rpc import JsonRpc, RpcError  # noqa: E402

ZTREAMER_PUBLISHED = {
    "addresses": {"ztreamer-busy": "t1Jg2S2sJwDd223cHphY9cwTbznjeeLWaan",
                  "ztreamer-quiet": "t1RwL3DvEjZHcNYJE6XXE76MH9wNonk6bpx"},
    "txids": ["4cc852b50a27de5b297732199d4f02b5c7f5aa0e6337554f2fd2ea4e7c90029f",
              "28f0dfa4310e52bbd1a129457e9714805ffc43f03d9a1c0183f63e6136e78f4b"],
}
KINDS = ("coinbase", "transparent-only", "sprout", "sapling-v4", "sapling-v5", "orchard", "orchard+sapling")
ADDRESS_BUCKETS = (("quiet", 1, 10), ("moderate", 11, 1_000), ("active", 1_001, 100_000))


def classify(tx: dict) -> str:
    if any("coinbase" in vin for vin in tx.get("vin", [])):
        return "coinbase"
    sapling = bool(tx.get("vShieldedSpend") or tx.get("vShieldedOutput"))
    orchard = bool((tx.get("orchard") or {}).get("actions"))
    if orchard and sapling:
        return "orchard+sapling"
    if orchard:
        return "orchard"
    if sapling:
        return "sapling-v5" if tx.get("version") == 5 else "sapling-v4"
    if tx.get("vjoinsplit"):
        return "sprout"
    return "transparent-only"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--zebra-rpc", required=True)
    parser.add_argument("--zebra-cookie")
    parser.add_argument("--upper", type=int, required=True)
    parser.add_argument("--network", choices=("Mainnet", "Testnet"), default="Mainnet")
    parser.add_argument("--lower", type=int, help="default: Sapling activation for --network")
    parser.add_argument("--seed", type=int, default=20261009)
    parser.add_argument("--max-blocks", type=int, default=600)
    parser.add_argument("--out", type=pathlib.Path, required=True)
    args = parser.parse_args()
    args.lower = args.lower or {"Mainnet": 419_200, "Testnet": 280_000}[args.network]
    published = ZTREAMER_PUBLISHED if args.network == "Mainnet" else {"addresses": {}, "txids": []}

    zebra = JsonRpc(args.zebra_rpc, cookie=args.zebra_cookie)
    rng = lw.SplitMix64(args.seed)
    by_kind: dict[str, dict] = {}
    candidates: list[str] = []
    visited = 0
    while visited < args.max_blocks and (len(by_kind) < len(KINDS) or len(candidates) < 60):
        visited += 1
        height = args.lower + rng.below(args.upper - args.lower + 1)
        block = zebra.call("getblock", str(height), 1)
        txid = block["tx"][rng.below(len(block["tx"]))]
        tx = zebra.call("getrawtransaction", txid, 1)
        kind = classify(tx)
        by_kind.setdefault(kind, {"txid": txid, "height": height, "kind": kind, "version": tx.get("version")})
        for vout in tx.get("vout", []):
            for address in (vout.get("scriptPubKey") or {}).get("addresses", []):
                if address.startswith("t") and address not in candidates:
                    candidates.append(address)

    addresses = dict(published["addresses"])
    histories = {}
    for address in candidates:
        if all(label in addresses for label, _, _ in ADDRESS_BUCKETS):
            break
        try:
            count = len(zebra.call("getaddresstxids", {"addresses": [address], "start": args.lower, "end": args.upper}))
        except RpcError:
            continue
        histories[address] = count
        for label, low, high in ADDRESS_BUCKETS:
            if label not in addresses and low <= count <= high:
                addresses[label] = address

    fixtures = {
        "addresses": addresses,
        "txids": published["txids"] + [by_kind[k]["txid"] for k in KINDS if k in by_kind],
        "transactions": [by_kind[k] for k in KINDS if k in by_kind],
        "address_history_lengths": {a: histories.get(a) for a in addresses.values()},
        "selection": {"seed": args.seed, "network": args.network, "lower": args.lower, "upper": args.upper,
                      "blocks_visited": visited, "missing_kinds": [k for k in KINDS if k not in by_kind],
                      "ztreamer_published": published},
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(fixtures, indent=2) + "\n")
    print(json.dumps({k: fixtures[k] for k in ("addresses", "address_history_lengths")}, indent=2))
    print(f"kinds found: {sorted(by_kind)}; missing: {fixtures['selection']['missing_kinds']}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
