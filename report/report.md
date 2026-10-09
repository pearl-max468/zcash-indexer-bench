# Zaino vs Ztreamer: an independent compatibility and performance comparison

*Draft. Results sections are filled from the published CI runs; every number links back to raw data.*

## Summary

<!-- results summary goes here once the campaign completes -->

## What was compared

| Build | Commit | Backing node | Why |
|---|---|---|---|
| Zaino 0.10.1 | `3244a74` | Zebra 6.4.2, `direct` backend | Latest stable Zaino release (2026-09-29) |
| Zaino 0.9.0 | `d27ec93` | Zebra 6.4.2, `direct` backend | The build Ztreamer's published comparison (2026-09-11) measured |
| Ztreamer v0.1.0 | `c40f3c3` | Embedded Zakura (fork `f4d44dd`, state format 28.1.5) | Latest Ztreamer tag (2026-09-12) |
| Ztreamer master | `6232ae0` | Embedded Zakura 1.5.1 (state format 29.1.0) | What Ztreamer's README install command builds |

Both indexers serve the same lightwallet gRPC protocol: each vendors `zcash/lightwallet-protocol`
v0.5.0 unchanged. They differ in architecture:

- **Zaino** is a separate process beside a Zebra full node. In `direct` mode it reads Zebra's state
  database on the same host and uses Zebra's JSON-RPC for what the database cannot answer (mempool,
  passthrough RPCs). It keeps its own LMDB index.
- **Ztreamer** embeds a Zakura node (a Zebra fork) in the same process and keeps an LMDB compact-block
  index. Its JSON-RPC surface is the embedded Zakura node's RPC.

Z3's compose file still pins `zainod:0.6.0`, and the public Zaino endpoint `zaino.unsafe.zec.rocks`
reports 0.6.0. This comparison uses the current releases.

## Method

**Data.** Every node starts from the same Zcash Foundation testnet snapshot
(`zebrad-state-testnet-v28-20260923.tar.zst`, SHA-256 `e1702bb2…8636`) and stays frozen at its tip,
height 4,382,897. Zebra runs with no outbound peers and no peer cache; Ztreamer's embedded Zakura
node peers only with that Zebra, so it sees itself at the tip and receives nothing newer. The
snapshot predates testnet's NU7 activation, so every build follows the same consensus rules.
Neither project produced the data.

**Hardware.** Free GitHub-hosted runners (`ubuntu-24.04`, 4 vCPU, 16 GB RAM, runner swap as provided).
Each job records the runner's CPU model, memory, kernel and disk.

**Fairness rules.**
1. Each project runs as its documentation recommends; default settings unless required to run.
2. One system per job: nothing else under test runs on the machine.
3. The backing node is at the frozen tip before the clock starts.
4. Every system receives the same requests: seed-derived heights, the same fixtures, the same fixed
   upper height (tip − 100).
5. The load generator ([ghz](https://github.com/bojand/ghz) v0.121.0, third-party) runs on CPUs
   separate from the server's (`AllowedCPUs`); its CPU time is recorded to rule out a client bottleneck.
6. Resource figures come from each process's cgroup (kernel accounting). Zaino's exclude Zebra, which is
   reported separately; Ztreamer's include its embedded node, because they cannot be separated.

**Measurements.**

| Area | What | How |
|---|---|---|
| gRPC compatibility | All 20 lightwallet-protocol methods; identical requests to each system | Responses compared byte-for-byte across systems and checked against Zebra's JSON-RPC (block hashes, transaction bytes, tree states, subtree roots, address data) |
| JSON-RPC coverage | The 28 methods Zaino 0.10.1 serves | Status and result per system, compared with Zebra where deterministic |
| Index build | From an empty index, cold page cache | Time to first gRPC answer and to a complete index; CPU seconds, peak memory, bytes written; index size |
| Latency | 12 RPCs, 1,000 sequential requests each after 50 warmups | p50 / p95 / p99 |
| Range throughput | `GetBlockRange` of 100 to 100,000 blocks | blocks per second |
| Concurrency | 1, 8, 32, 128 clients, one connection each, 30 s | blocks/s for `GetBlockRange(1,000)`, requests/s for `GetBlock` |
| Wallet download | Sapling activation to the upper height in 10,000-block chunks | blocks per second (download only; no trial decryption) |

## Results

<!-- filled from results/results.md and results/compat/compat.md -->

## Limitations

- **Testnet, not mainnet.** Testnet blocks are smaller than mainnet's and include no
  sandblasting-era blocks. Absolute times, sizes and memory are therefore not mainnet figures;
  the comparison is relative, on identical inputs. Compatibility findings carry over, because the
  code paths are the same.
- **Shared CI machines** are noisier than dedicated hardware. Each system runs on several runners;
  the spread is reported with each runner's CPU model.
- **Different node implementations.** Zaino's node is Zebra; Ztreamer's is Zakura. Each is what its
  indexer is built for, but node-level differences are part of every end-to-end figure.
- **Not measured:** behaviour under reorgs, live tip-following, mempool load, TLS overhead, and
  wallet-side scanning.

## Reproduce

Fork <https://github.com/pearl-max468/zcash-indexer-bench>, run the `bench` workflow, download the
`run-*` artifacts and run `bench/report.py`. The same scripts run on mainnet given dedicated hardware.
