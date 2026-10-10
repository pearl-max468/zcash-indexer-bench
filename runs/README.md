# Runs

One directory per run (`<system>-r<repeat>`), as uploaded by the `bench` workflow, plus `prepare/`
(the fixtures, upper height and runner record that every run in the campaign used). Every table in
[`results/`](../results) and [`report/report.md`](../report/report.md) is built from these files.

| Directories | Workflow run | Harness commit | Notes |
|---|---|---|---|
| `ztreamer-v0.1.0-r1..3` | [37871834309](https://github.com/pearl-max468/zcash-indexer-bench/actions/runs/37871834309) | `125b464` | That run's Zaino jobs failed on the old completion rule and were rerun below; its Ztreamer v0.1.0 jobs completed and all ended serving the frozen tip. |
| `zaino-0.10.1-r1..3`, `zaino-0.9.0-r1..3` | [38079103942](https://github.com/pearl-max468/zcash-indexer-bench/actions/runs/38079103942) | `d5b2598` | Zaino completion on the "switched back to the persistent database" log line. |
| `ztreamer-master-r1..3`, `prepare/` | [38079353139](https://github.com/pearl-max468/zcash-indexer-bench/actions/runs/38079353139) | `2eb5340` | Master's embedded node pinned to the legacy P2P stack; `tip_mismatch` check. |
| `../runs-diagnostic/*-nodelay` | [38080047816](https://github.com/pearl-max468/zcash-indexer-bench/actions/runs/38080047816) | `529b932` | `tcp_nodelay: true` (the `ci/nodelay.c` shim); diagnostic only, not in the main tables. |

All runs use the same snapshot, frozen tip (4,382,897) and upper height (4,382,797). The runner CPU
of each run is in `serving/hardware.json` and in the `runner_cpu` column of
[`results/index-runs.csv`](../results/index-runs.csv).

Per run:

```
index/      run.json (phases, resources, headline), samples.csv (1 s cgroup samples), probes.csv,
            metrics.csv, index-size.csv, journal.log, the indexer config, hardware before/after
serving/    results.json (every scenario's summary), hardware.json, journal.log, data-*.json, config
compat/     grpc/ and jsonrpc/: matrix.csv, responses.jsonl (every response), summary.md
```

## Not in the repository

The per-scenario ghz reports (`serving/<suite>--<scenario>.json`, every request's latency) are left
out to keep the repository small. They are in the raw-data release, with the complete run
directories:

- Release: [results-2026-10-10](https://github.com/pearl-max468/zcash-indexer-bench/releases/tag/results-2026-10-10)
- File: `zcash-indexer-bench-raw-20261010.tar.xz` (95 MiB)
- SHA-256: `b31cec0ba5b26f5537441d33278b18dc9c3565cce471e2eebe21f633e8693ea8`

## Commit hashes

On 2026-10-10 the commit messages were rewritten to remove a co-author line; the code at every
commit is unchanged. The workflow runs above were made from the earlier hashes:

| Earlier hash | Current hash |
|---|---|
| `0064fc5` | `125b464` |
| `f6c2ad1` | `d5b2598` |
| `2f1306e` | `2eb5340` |
| `9fee499` | `529b932` |
