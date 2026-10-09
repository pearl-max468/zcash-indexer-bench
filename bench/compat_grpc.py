#!/usr/bin/env python3
"""Lightwallet gRPC compatibility suite.

Sends identical requests for every CompactTxStreamer method (lightwallet-protocol v0.5.0) to each
server, compares the responses between servers, and checks them against Zebra's JSON-RPC as an
independent reference. Inputs are derived from a seed, so reruns issue the same requests.

    compat_grpc.py --server zaino=http://127.0.0.1:8137 --server ztreamer=http://127.0.0.1:9067 \
        --zebra-rpc http://127.0.0.1:8232 --zebra-cookie /data/zebra-cookie/.cookie \
        --fixtures fixtures/mainnet.json --out runs/compat/<run>

Outputs in --out: metadata.json, results.jsonl (one row per server x case), matrix.csv (one row
per case), summary.md. Exit status is 0 even when servers disagree; disagreement is a result.
"""

from __future__ import annotations

import argparse
import csv
import dataclasses
import datetime
import json
import pathlib
import platform
import sys
import time
from typing import Callable

import grpc

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import lw  # noqa: E402
from lw import cf, pb  # noqa: E402
from zebra_rpc import JsonRpc, RpcError  # noqa: E402

REORG_MARGIN = 100  # only finalized heights are compared


@dataclasses.dataclass
class Case:
    method: str
    case: str
    kind: str  # unary | server_stream | client_stream
    request: Callable[[], object]  # factory; client-stream factories return an iterator
    mode: str = "equal"  # equal: servers must match | report: tip/mempool-dependent, recorded only
    oracle: Callable[[list], tuple[bool | None, str]] | None = None
    timeout: float = 120.0


@dataclasses.dataclass
class Outcome:
    status: str
    details: str
    seconds: float
    messages: list
    digest: str | None


def call(stub, case: Case) -> Outcome:
    rpc = getattr(stub, case.method)
    started = time.perf_counter()
    messages: list = []
    try:
        if case.kind == "unary":
            messages = [rpc(case.request(), timeout=case.timeout)]
        elif case.kind == "server_stream":
            for message in rpc(case.request(), timeout=case.timeout):
                messages.append(message)
        elif case.kind == "client_stream":
            messages = [rpc(case.request(), timeout=case.timeout)]
        else:
            raise ValueError(case.kind)
        status, details = "OK", ""
    except grpc.RpcError as e:
        status, details = e.code().name, (e.details() or "")[:300]
    elapsed = time.perf_counter() - started
    return Outcome(status, details, elapsed, messages, lw.digest(messages) if messages else None)


# ---------------------------------------------------------------- reference checks against Zebra

def block_oracle(zebra: JsonRpc, height: int):
    expected = zebra.call("getblock", str(height), 1)
    txids = expected["tx"]
    trees = expected.get("trees", {})

    def check_block(block) -> list[str]:
        problems = []
        if block.height != height:
            problems.append(f"height {block.height} != {height}")
        if lw.display_hex(block.hash) != expected["hash"]:
            problems.append("hash differs from zebra")
        if expected.get("previousblockhash") and lw.display_hex(block.prevHash) != expected["previousblockhash"]:
            problems.append("prevHash differs from zebra")
        if block.time and block.time != expected["time"]:
            problems.append(f"time {block.time} != {expected['time']}")
        for tx in block.vtx:
            if tx.index >= len(txids) or lw.display_hex(tx.txid) != txids[tx.index]:
                problems.append(f"vtx index {tx.index} txid not at that position in zebra's block")
                break
        meta = block.chainMetadata
        for pool, field in (("sapling", "saplingCommitmentTreeSize"), ("orchard", "orchardCommitmentTreeSize")):
            size = trees.get(pool, {}).get("size")
            if size is not None and block.HasField("chainMetadata") and getattr(meta, field) != size:
                problems.append(f"{field} {getattr(meta, field)} != zebra {size}")
        return problems

    def oracle(messages):
        if len(messages) != 1:
            return False, f"expected 1 block, got {len(messages)}"
        problems = check_block(messages[0])
        return (not problems), "; ".join(problems) or f"{len(messages[0].vtx)} of {len(txids)} txs compact"

    return oracle


def range_oracle(zebra: JsonRpc, start: int, end: int):
    def oracle(messages):
        heights = [m.height for m in messages]
        step = 1 if end >= start else -1
        want = list(range(start, end + step, step))
        if heights != want:
            return False, f"heights {heights[:3]}..{heights[-3:]} (n={len(heights)}) != {start}..{end}"
        # Spot-check first, middle and last block against zebra (a full check would re-fetch every block).
        problems = []
        for m in (messages[0], messages[len(messages) // 2], messages[-1]):
            expected = zebra.call("getblock", str(m.height), 1)
            if lw.display_hex(m.hash) != expected["hash"]:
                problems.append(f"hash mismatch at {m.height}")
        return (not problems), "; ".join(problems) or f"{len(messages)} blocks in order"

    return oracle


def treestate_oracle(zebra: JsonRpc, height: int):
    expected = zebra.call("z_gettreestate", str(height))

    def final_state(pool):
        return ((expected.get(pool) or {}).get("commitments") or {}).get("finalState", "")

    def oracle(messages):
        t = messages[0]
        problems = []
        if t.height != height:
            problems.append(f"height {t.height}")
        if t.hash != expected["hash"]:
            problems.append("hash differs")
        if t.saplingTree != final_state("sapling"):
            problems.append("saplingTree differs")
        if t.orchardTree != final_state("orchard"):
            problems.append("orchardTree differs")
        return (not problems), "; ".join(problems) or "matches z_gettreestate"

    return oracle


def subtree_oracle(zebra: JsonRpc, pool: str, start: int, limit: int):
    expected = zebra.call("z_getsubtreesbyindex", pool, start, *([limit] if limit else []))["subtrees"]

    def oracle(messages):
        if len(messages) != len(expected):
            return False, f"{len(messages)} roots != zebra {len(expected)}"
        for i, (m, e) in enumerate(zip(messages, expected)):
            if m.rootHash.hex() != e["root"] and lw.display_hex(m.rootHash) != e["root"]:
                return False, f"root {start + i} differs"
            if m.completingBlockHeight != e["end_height"]:
                return False, f"root {start + i} height {m.completingBlockHeight} != {e['end_height']}"
        return True, f"{len(messages)} roots match z_getsubtreesbyindex"

    return oracle


def transaction_oracle(zebra: JsonRpc, txid: str):
    expected = zebra.call("getrawtransaction", txid, 1)

    def oracle(messages):
        t = messages[0]
        problems = []
        if t.data != bytes.fromhex(expected["hex"]):
            problems.append("raw bytes differ")
        if expected.get("height") is not None and t.height != expected["height"]:
            problems.append(f"height {t.height} != {expected['height']}")
        return (not problems), "; ".join(problems) or "matches getrawtransaction"

    return oracle


def address_txids_oracle(zebra: JsonRpc, address: str, start: int, end: int):
    txids = zebra.call("getaddresstxids", {"addresses": [address], "start": start, "end": end})

    def oracle(messages):
        if len(messages) != len(txids):
            return False, f"{len(messages)} txs != zebra {len(txids)}"
        # Raw bytes for a deterministic sample; the full set is compared server-to-server.
        sample = sorted(set(txids[:: max(1, len(txids) // 25)]))
        want = {bytes.fromhex(zebra.call("getrawtransaction", t, 0)) for t in sample}
        have = {m.data for m in messages}
        missing = len(want - have)
        return missing == 0, f"{len(messages)} txs; {len(sample) - missing}/{len(sample)} sampled raw txs present"

    return oracle


def balance_oracle(zebra: JsonRpc, addresses: list[str]):
    def oracle(messages):
        expected = zebra.call("getaddressbalance", {"addresses": addresses})["balance"]
        got = messages[0].valueZat
        # Balance is tip-dependent: a block arriving between the two calls can change it.
        return got == expected, f"valueZat {got} vs zebra {expected} (tip-dependent)"

    return oracle


def utxos_oracle(zebra: JsonRpc, addresses: list[str], start: int, stream: bool):
    def oracle(messages):
        expected = [u for u in zebra.call("getaddressutxos", {"addresses": addresses}) if u["height"] >= start]
        replies = list(messages) if stream else list(messages[0].addressUtxos)
        want = {(u["txid"], u["outputIndex"], u["satoshis"]) for u in expected}
        have = {(lw.display_hex(r.txid), r.index, r.valueZat) for r in replies}
        if want == have:
            return True, f"{len(have)} utxos match getaddressutxos (tip-dependent)"
        return False, f"{len(have)} utxos vs zebra {len(want)}; {len(want - have)} missing, {len(have - want)} extra"

    return oracle


# ---------------------------------------------------------------- case construction

def build_cases(zebra: JsonRpc, upper: int, sapling: int, upgrades: dict[str, int], fixtures: dict,
                samples: int, seed: int) -> tuple[list[Case], dict]:
    rng = lw.SplitMix64(seed)
    sampled = sorted({sapling + rng.below(upper - sapling + 1) for _ in range(samples)})
    landmarks = sorted({h + d for h in upgrades.values() if sapling <= h <= upper for d in (-1, 0, 1)})
    heights = sorted(set(sampled) | set(landmarks) | {sapling, upper})
    plan = {"sampled_heights": sampled, "upgrade_landmarks": landmarks, "heights": heights}
    cases: list[Case] = []

    cases.append(Case("GetLightdInfo", "info", "unary", lambda: pb.Empty(), mode="report"))
    cases.append(Case("GetLatestBlock", "tip", "unary", lambda: pb.ChainSpec(), mode="report"))
    cases.append(Case("GetLatestTreeState", "tip", "unary", lambda: pb.Empty(), mode="report"))
    cases.append(Case("Ping", "zero", "unary", lambda: pb.Duration(intervalUs=0), mode="report"))

    for h in heights:
        cases.append(Case("GetBlock", f"height={h}", "unary", lambda h=h: pb.BlockID(height=h),
                          oracle=block_oracle(zebra, h)))
        cases.append(Case("GetBlockNullifiers", f"height={h}", "unary", lambda h=h: pb.BlockID(height=h)))
        cases.append(Case("GetTreeState", f"height={h}", "unary", lambda h=h: pb.BlockID(height=h),
                          oracle=treestate_oracle(zebra, h)))
    for h in sampled[:5]:
        block_hash = lw.internal_bytes(zebra.call("getblockhash", h))
        cases.append(Case("GetBlock", f"hash@{h}", "unary", lambda b=block_hash: pb.BlockID(hash=b),
                          oracle=block_oracle(zebra, h)))
        cases.append(Case("GetTreeState", f"hash@{h}", "unary", lambda b=block_hash: pb.BlockID(hash=b),
                          oracle=treestate_oracle(zebra, h)))
    cases.append(Case("GetBlock", "pre-sapling height=1", "unary", lambda: pb.BlockID(height=1)))
    cases.append(Case("GetBlock", "beyond tip", "unary", lambda: pb.BlockID(height=upper + 10_000_000)))

    for i, start in enumerate(sampled[:: max(1, len(sampled) // 6)][:6]):
        end = min(start + 99, upper)
        rng_req = lambda s=start, e=end, pools=(): pb.BlockRange(
            start=pb.BlockID(height=s), end=pb.BlockID(height=e), poolTypes=list(pools))
        cases.append(Case("GetBlockRange", f"{start}-{end}", "server_stream", rng_req,
                          oracle=range_oracle(zebra, start, end)))
        cases.append(Case("GetBlockRangeNullifiers", f"{start}-{end}", "server_stream", rng_req,
                          oracle=range_oracle(zebra, start, end)))
        if i == 0:
            cases.append(Case("GetBlockRange", f"{end}-{start} descending", "server_stream",
                              lambda s=start, e=end: pb.BlockRange(start=pb.BlockID(height=e), end=pb.BlockID(height=s)),
                              oracle=range_oracle(zebra, end, start)))
            for label, pools in (("transparent", [pb.TRANSPARENT]), ("sapling", [pb.SAPLING]),
                                 ("orchard", [pb.ORCHARD]), ("all", [pb.TRANSPARENT, pb.SAPLING, pb.ORCHARD])):
                cases.append(Case("GetBlockRange", f"{start}-{end} pools={label}", "server_stream",
                                  lambda s=start, e=end, p=tuple(pools): rng_req(s, e, p),
                                  oracle=range_oracle(zebra, start, end)))
    cases.append(Case("GetBlockRange", f"{upper - 100_000}-{upper} 100k", "server_stream",
                      lambda: pb.BlockRange(start=pb.BlockID(height=upper - 100_000), end=pb.BlockID(height=upper)),
                      oracle=range_oracle(zebra, upper - 100_000, upper), timeout=600))

    for txid in fixtures.get("txids", []):
        cases.append(Case("GetTransaction", f"txid={txid[:12]}", "unary",
                          lambda t=txid: pb.TxFilter(hash=lw.internal_bytes(t)),
                          oracle=transaction_oracle(zebra, txid)))
    if fixtures.get("txids"):
        txid = fixtures["txids"][0]
        mined = bytes.fromhex(zebra.call("getrawtransaction", txid, 0))
        cases.append(Case("SendTransaction", "already-mined tx", "unary",
                          lambda raw=mined: pb.RawTransaction(data=raw, height=0)))
    cases.append(Case("SendTransaction", "malformed bytes", "unary",
                      lambda: pb.RawTransaction(data=b"\x00" * 16, height=0)))
    cases.append(Case("GetTransaction", "unknown txid", "unary", lambda: pb.TxFilter(hash=b"\x11" * 32)))

    addresses = fixtures.get("addresses", {})
    for label, address in addresses.items():
        start = sapling
        cases.append(Case("GetTaddressTxids", f"{label}", "server_stream",
                          lambda a=address, s=start: pb.TransparentAddressBlockFilter(
                              address=a, range=pb.BlockRange(start=pb.BlockID(height=s), end=pb.BlockID(height=upper))),
                          oracle=address_txids_oracle(zebra, address, start, upper), timeout=600))
        cases.append(Case("GetTaddressTransactions", f"{label}", "server_stream",
                          lambda a=address, s=start: pb.TransparentAddressBlockFilter(
                              address=a, range=pb.BlockRange(start=pb.BlockID(height=s), end=pb.BlockID(height=upper))),
                          oracle=address_txids_oracle(zebra, address, start, upper), timeout=600))
        cases.append(Case("GetTaddressBalance", f"{label}", "unary",
                          lambda a=address: pb.AddressList(addresses=[a]), oracle=balance_oracle(zebra, [address])))
        cases.append(Case("GetTaddressBalanceStream", f"{label}", "client_stream",
                          lambda a=address: iter([pb.Address(address=a)]), oracle=balance_oracle(zebra, [address])))
        cases.append(Case("GetAddressUtxos", f"{label}", "unary",
                          lambda a=address: pb.GetAddressUtxosArg(addresses=[a], startHeight=sapling, maxEntries=0),
                          oracle=utxos_oracle(zebra, [address], sapling, stream=False)))
        cases.append(Case("GetAddressUtxosStream", f"{label}", "server_stream",
                          lambda a=address: pb.GetAddressUtxosArg(addresses=[a], startHeight=sapling, maxEntries=0),
                          oracle=utxos_oracle(zebra, [address], sapling, stream=True)))
    if len(addresses) > 1:
        both = list(addresses.values())
        cases.append(Case("GetTaddressBalance", "all fixtures", "unary",
                          lambda: pb.AddressList(addresses=both), oracle=balance_oracle(zebra, both)))
        cases.append(Case("GetTaddressBalanceStream", "all fixtures + duplicate", "client_stream",
                          lambda: iter([pb.Address(address=a) for a in both + both[:1]]),
                          oracle=balance_oracle(zebra, both)))
    cases.append(Case("GetTaddressBalance", "invalid address", "unary",
                      lambda: pb.AddressList(addresses=["t1notavalidaddress"])))

    cases.append(Case("GetMempoolTx", "no exclusions", "server_stream", lambda: pb.GetMempoolTxRequest(), mode="report"))
    cases.append(Case("GetMempoolStream", "5s window", "server_stream", lambda: pb.Empty(), mode="report", timeout=5))

    for pool, proto_pool in (("sapling", pb.sapling), ("orchard", pb.orchard)):
        cases.append(Case("GetSubtreeRoots", f"{pool} all", "server_stream",
                          lambda p=proto_pool: pb.GetSubtreeRootsArg(startIndex=0, shieldedProtocol=p, maxEntries=0),
                          oracle=subtree_oracle(zebra, pool, 0, 0)))
        cases.append(Case("GetSubtreeRoots", f"{pool} from 2, max 3", "server_stream",
                          lambda p=proto_pool: pb.GetSubtreeRootsArg(startIndex=2, shieldedProtocol=p, maxEntries=3),
                          oracle=subtree_oracle(zebra, pool, 2, 3)))
    cases.append(Case("GetSubtreeRoots", "ironwood (not active on mainnet)", "server_stream",
                      lambda: pb.GetSubtreeRootsArg(startIndex=0, shieldedProtocol=pb.ironwood, maxEntries=0)))
    return cases, plan


# ---------------------------------------------------------------- run and report

def parse_server(spec: str) -> tuple[str, str]:
    name, sep, url = spec.partition("=")
    if not sep:
        raise argparse.ArgumentTypeError("--server takes NAME=URL")
    return name, url


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--server", action="append", type=parse_server, required=True)
    parser.add_argument("--zebra-rpc", required=True)
    parser.add_argument("--zebra-cookie")
    parser.add_argument("--zebra-userpass")
    parser.add_argument("--fixtures", type=pathlib.Path)
    parser.add_argument("--out", type=pathlib.Path, required=True)
    parser.add_argument("--upper", type=int, help="highest height compared (default: min tip - 100)")
    parser.add_argument("--samples", type=int, default=40)
    parser.add_argument("--seed", type=int, default=20261009)
    args = parser.parse_args()

    zebra = JsonRpc(args.zebra_rpc, cookie=args.zebra_cookie, userpass=args.zebra_userpass)
    fixtures = json.loads(args.fixtures.read_text()) if args.fixtures else {}
    stubs = {name: lw.connect(url) for name, url in args.server}

    info = {name: lw.canonical(stub.GetLightdInfo(pb.Empty(), timeout=30)) for name, stub in stubs.items()}
    tips = {name: int(i.get("blockHeight", 0)) for name, i in info.items()}
    chain = zebra.call("getblockchaininfo")
    tips["zebra"] = chain["blocks"]
    upper = args.upper or min(tips.values()) - REORG_MARGIN
    upgrades = {u["name"]: u["activationheight"] for u in chain.get("upgrades", {}).values()}
    sapling = upgrades.get("Sapling", 419_200)

    cases, plan = build_cases(zebra, upper, sapling, upgrades, fixtures, args.samples, args.seed)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "metadata.json").write_text(json.dumps({
        "started_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "servers": dict(args.server),
        "lightd_info": info,
        "tips_at_start": tips,
        "upper_height": upper,
        "upper_hash": zebra.call("getblockhash", upper),
        "reorg_margin": REORG_MARGIN,
        "seed": args.seed,
        "network_upgrades": upgrades,
        "plan": plan,
        "fixtures": fixtures,
        "case_count": len(cases),
        "protocol": "zcash/lightwallet-protocol v0.5.0 (ac7cee052a1bf5d430985a478d39e8b513fc4bd4)",
        "client": {"python": platform.python_version(), "grpcio": grpc.__version__},
        "argv": sys.argv,
    }, indent=2))

    names = [name for name, _ in args.server]
    matrix_rows = []
    with open(args.out / "results.jsonl", "w") as results:
        for n, case in enumerate(cases, 1):
            outcomes = {name: call(stubs[name], case) for name in names}
            row = {"method": case.method, "case": case.case, "mode": case.mode}
            for name, o in outcomes.items():
                verdict, note = (None, "")
                if case.oracle and o.status == "OK":
                    try:
                        verdict, note = case.oracle(o.messages)
                    except (RpcError, KeyError, IndexError) as e:
                        verdict, note = None, f"oracle error: {e}"
                results.write(json.dumps({
                    "method": case.method, "case": case.case, "server": name, "status": o.status,
                    "details": o.details, "seconds": round(o.seconds, 6), "messages": len(o.messages),
                    "digest": o.digest, "oracle_ok": verdict, "oracle_note": note,
                    "first_message": lw.canonical(o.messages[0]) if o.messages and len(o.messages) == 1 else None,
                }) + "\n")
                row[f"{name}_status"] = o.status
                row[f"{name}_messages"] = len(o.messages)
                row[f"{name}_oracle"] = {True: "pass", False: "FAIL", None: ""}[verdict]
                row[f"{name}_note"] = note or o.details
            statuses = {o.status for o in outcomes.values()}
            digests = {o.digest for o in outcomes.values()}
            if case.mode == "report":
                agreement = "n/a (tip-dependent)"
            elif len(statuses) > 1:
                agreement = "status differs"
            elif statuses == {"OK"}:
                agreement = "identical" if len(digests) == 1 else "content differs"
            else:
                agreement = f"both {statuses.pop()}"
            row["agreement"] = agreement
            if agreement == "content differs" and len(names) >= 2:
                a, b = (outcomes[names[0]].messages, outcomes[names[1]].messages)
                if len(a) != len(b):
                    row["diff"] = f"message count {len(a)} != {len(b)}"
                else:
                    first = next((i for i, (x, y) in enumerate(zip(a, b))
                                  if x.SerializeToString(deterministic=True) != y.SerializeToString(deterministic=True)), 0)
                    row["diff"] = f"message {first}: " + "; ".join(lw.diff(lw.canonical(a[first]), lw.canonical(b[first]), limit=6))
            matrix_rows.append(row)
            print(f"[{n}/{len(cases)}] {case.method} {case.case}: {agreement}", file=sys.stderr)

    columns = ["method", "case", "mode", "agreement", "diff"]
    for name in names:
        columns += [f"{name}_status", f"{name}_messages", f"{name}_oracle", f"{name}_note"]
    with open(args.out / "matrix.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(matrix_rows)
    write_summary(args.out, names, matrix_rows, info)
    print(f"wrote {args.out}", file=sys.stderr)
    return 0


def write_summary(out: pathlib.Path, names: list[str], rows: list[dict], info: dict) -> None:
    lines = ["# gRPC compatibility summary", ""]
    lines.append("| Method | Cases | " + " | ".join(f"{n} OK / oracle pass" for n in names) + " | Identical across servers |")
    lines.append("|---|---:|" + "---:|" * len(names) + "---:|")
    methods: dict[str, list[dict]] = {}
    for r in rows:
        methods.setdefault(r["method"], []).append(r)
    for method, rs in methods.items():
        cells = []
        for n in names:
            ok = sum(r[f"{n}_status"] == "OK" for r in rs)
            checked = [r for r in rs if r[f"{n}_oracle"]]
            passed = sum(r[f"{n}_oracle"] == "pass" for r in checked)
            cells.append(f"{ok}/{len(rs)} · {passed}/{len(checked)}" if checked else f"{ok}/{len(rs)} · –")
        comparable = [r for r in rs if r["mode"] == "equal"]
        same = sum(r["agreement"] in ("identical",) or r["agreement"].startswith("both ") for r in comparable)
        lines.append(f"| {method} | {len(rs)} | " + " | ".join(cells) + f" | {same}/{len(comparable)} |")
    lines += ["", "## Disagreements", ""]
    for r in rows:
        if r["agreement"] in ("status differs", "content differs"):
            statuses = ", ".join(f"{n}: {r[f'{n}_status']}" for n in names)
            lines.append(f"- **{r['method']}** `{r['case']}` — {r['agreement']} ({statuses}) {r.get('diff', '')}")
    lines += ["", "## Server identity (GetLightdInfo)", "", "```json", json.dumps(info, indent=2), "```", ""]
    (out / "summary.md").write_text("\n".join(lines))


if __name__ == "__main__":
    sys.exit(main())
