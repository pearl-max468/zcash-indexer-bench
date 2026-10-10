# zcash-indexer-bench

An independent, reproducible compatibility and performance comparison of two Zcash indexers:
**Zaino** (Zingo Labs, part of the Z3 stack) and **Ztreamer** (Rust indexer with an embedded Zakura node).
Funded by a ZecHub bounty. Not affiliated with either project.

> **Status:** measurement campaign in progress on GitHub Actions. Results, raw data and the
> written comparison will be added under `results/` and `report/`.

## Where it runs, and on what data

The published measurements run on **free GitHub-hosted runners** (4 vCPU, 16 GB RAM), so anyone
can reproduce them by forking this repository and running the `bench` workflow; no hardware or
accounts beyond GitHub are needed.

Runner disks cannot hold mainnet (about 255 GiB of node state per node), so the campaign uses
**Zcash testnet frozen at height 4,382,897**: every node starts from the same
[Zcash Foundation snapshot](https://snapshots.zfnd.org/) (pinned by SHA-256 in
[`versions.env`](versions.env)) and stays at that height. Zebra has no outbound peers; Ztreamer's
embedded Zakura node peers only with that Zebra, so it sees itself at the tip. Testnet is a complete
chain with every pool (Sprout, Sapling, Orchard), and the snapshot predates testnet's NU7 activation,
so all builds follow the same consensus rules. Neither project produced the data.

What this does and does not show:
- Compatibility results (protocol coverage, byte-level agreement, correctness against Zebra) carry
  over to mainnet: the code paths are the same.
- Performance results are **relative** comparisons on identical inputs. Testnet blocks are smaller
  than mainnet's (no sandblasting-era blocks), so absolute times, index sizes and memory are not
  mainnet figures.
- Shared CI machines are noisier than dedicated hardware: each system runs on several runners and
  the spread is reported, along with each runner's CPU model.

The same scripts run the full mainnet campaign on dedicated hardware (see "Reproduce on mainnet").

## Systems under test

| Build | Commit | Backing node | Why it is included |
|---|---|---|---|
| Zaino `0.10.1` | `3244a74` | Zebra `v6.4.2`, `direct` backend (same host) | Latest stable release |
| Zaino `0.9.0` | `d27ec93` | Zebra `v6.4.2`, `direct` backend | The build Ztreamer's published comparison measured |
| Ztreamer `v0.1.0` | `c40f3c3` | Embedded Zakura fork `f4d44dd` (state format 28.1.5) | Latest tag |
| Ztreamer `master` | `6232ae0` | Embedded Zakura `v1.5.1` (state format 29.1.0) | What the README's install command builds |

All pins live in [`versions.env`](versions.env). Every run records the binary SHA-256, commit,
toolchain and build command (`/opt/zbench/provenance/*.json`). Z3's compose file pins
`zainod:0.6.0`; that is noted in the report, but the current stable release is what operators
would deploy today.

## What is measured

**Compatibility**
- All 20 lightwallet-protocol v0.5.0 gRPC methods: the same seed-derived requests go to every server.
  Responses are compared byte-for-byte across servers and checked against Zebra's JSON-RPC as an
  independent reference (block hashes, transaction bytes, tree states, subtree roots, address data).
  Tool: [`bench/compat_grpc.py`](bench/compat_grpc.py).
- All 28 JSON-RPC methods Zaino serves, on Zaino, on Ztreamer's embedded Zakura RPC, and on Zebra.
  Tool: [`bench/compat_jsonrpc.py`](bench/compat_jsonrpc.py).

**Initial index build** (from an empty index, with the backing node already at the chain tip)
- Time to first gRPC answer and to a complete index, broken into the phases each indexer reports.
- CPU seconds, peak memory and block I/O from each process's own cgroup (exact kernel accounting).
  Zebra's resources are reported separately and summed with Zaino's for a "whole stack" figure;
  Ztreamer embeds its node, so only the combined figure exists for it.
- Index size on disk. Tool: [`bench/run_index_build.py`](bench/run_index_build.py).

**Serving** (index built, loopback, plaintext gRPC on both)
- Per-RPC latency distribution (1,000 sequential requests each), `GetBlockRange` at 100 to 100,000
  blocks, scaling at 1 / 8 / 32 / 128 concurrent clients, and a full compact-block download from
  Sapling activation to a fixed upper height.
- Load generator: [ghz](https://github.com/bojand/ghz) `v0.121.0`, a third-party gRPC tool, pinned to
  CPUs separate from the server's. Ztreamer's own Rust client is run once per build as a cross-check.
  Tool: [`bench/run_serving.py`](bench/run_serving.py).

## Fairness rules

1. Each project runs as its own documentation recommends: Zaino beside Zebra in `direct` mode,
   Ztreamer with its embedded node. Default settings everywhere unless a setting is required to run.
2. Only the system under test runs during a measurement; runs are sequential and their order alternates.
3. Both backing nodes are at the chain tip before the clock starts. Node sync time is not indexer time.
4. Workloads use the same fixed height bounds, seed and fixtures for every system.
5. Ztreamer's published fixtures are included so its own figures can be compared directly.
6. Every asymmetry that remains (different node implementations, embedded vs separate process,
   page-cache state, chain growth between runs) is stated next to the numbers it affects.
7. Raw samples are published, not only summaries, so every figure can be recomputed.

## Reproduce on GitHub Actions (testnet)

1. Fork this repository (public forks get the free 4-vCPU runners).
2. Actions → **bench** → *Run workflow*. Inputs choose the systems, the number of repeats
   (e.g. `[1,2,3]`, one runner per system per repeat) and the serving suites.
3. Each job uploads its raw outputs as an artifact `run-<system>-r<n>`. Download them into `runs/`
   and build the tables and figures:

```sh
python bench/compare_compat.py --runs runs --out results/compat
python bench/report.py --runs runs --out results
```

The workflow: `build` compiles every pinned binary; `prepare` starts the frozen Zebra, then derives
fixtures and a fixed upper height (tip - 100); `bench` runs one system per job: index build from
empty (cold page cache), serving suites, and both compatibility suites with Zebra as the reference.

## Reproduce on mainnet

Requirements: Linux (tested on Ubuntu 24.04), at least 16 threads, 64 GB RAM, ~2 TB NVMe as one
volume, unmetered network. Run as root on a dedicated host. The Zcash Foundation's mainnet snapshot
(254 GiB, format 28.0.0) can replace the from-genesis sync in `10-zebra.sh`.

```sh
git clone <this repo> /opt/zbench/repo && cd /opt/zbench/repo
server/00-bootstrap.sh              # packages, Rust, ghz, grpcurl, Python env, hardware record
server/10-zebra.sh                  # build Zebra v6.4.2, start mainnet sync from genesis (1-3 days)
server/11-zakura-snapshots.sh       # download + verify Zakura archive snapshots (SHA-256 pinned)
server/12-build.sh                  # build all four indexers at their pinned commits
server/status.sh                    # sync progress, services, disk
```

Then, once Zebra is at the tip (`PY=/opt/zbench/venv/bin/python`):

```sh
$PY bench/make_fixtures.py --zebra-rpc http://127.0.0.1:8232 --zebra-cookie /data/zebra-cookie/.cookie \
    --upper <H> --out fixtures/mainnet.json
bench/catch_up_ztreamer.sh ztreamer-v0.1.0      # embedded node to tip (before each Ztreamer run)
$PY bench/run_index_build.py --system ztreamer-v0.1.0 --cold --out runs/index/ztreamer-v0.1.0-r1
$PY bench/run_index_build.py --system zaino-0.10.1   --cold --out runs/index/zaino-0.10.1-r1
$PY bench/run_serving.py --system zaino-0.10.1 --upper <H> --fixtures fixtures/mainnet.json \
    --repeat 1 --out runs/serving/zaino-0.10.1-r1
$PY bench/compat_grpc.py --server zaino=http://127.0.0.1:8137 --server ztreamer=http://127.0.0.1:9067 \
    --zebra-rpc http://127.0.0.1:8232 --zebra-cookie /data/zebra-cookie/.cookie \
    --fixtures fixtures/mainnet.json --upper <H> --out runs/compat/grpc
```

## Layout

```
versions.env        every pinned version, commit, snapshot hash and port
.github/workflows/  the bench workflow (build, prepare, bench)
ci/                 runner setup: disk cleanup, snapshot download and verification, frozen Zebra
server/             host setup for mainnet: bootstrap, Zebra, snapshots, builds, status
configs/            Zebra config and the Zaino / Zakura config templates
proto/              lightwallet-protocol v0.5.0 (MIT, Electric Coin Company), as both projects vendor it
bench/              compatibility suites, index-build and serving runners, fixtures
runs/               raw outputs, one directory per run
```

## License

Code: MIT. Measurement data and report: CC BY 4.0.
