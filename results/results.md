# Results

## Initial index build (from empty, backing node at the frozen tip)

| System | Runs | Time to complete | First gRPC answer | Indexer CPU-s | Indexer peak heap | Indexer peak RSS | Zebra CPU-s (during) | Zebra peak heap | Written by indexer | Index on disk |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| zaino-0.10.1 | 3 | 1,395 s | 6 s | 2,279 | 1.65 GiB | 9.18 GiB | 218 | 0.37 GiB | 39.05 GiB | 22.06 GiB |
| ztreamer-v0.1.0 | 3 | 216 s | 210 s | 256 | 0.75 GiB | 1.42 GiB | – | – | 10.56 GiB | 1.44 GiB |
| zaino-0.9.0 | 3 | 1,211 s | 6 s | 1,627 | 1.60 GiB | 8.95 GiB | 117 | 0.36 GiB | 39.05 GiB | 22.06 GiB |
| ztreamer-master | 3 | 159 s | 158 s | 208 | 0.77 GiB | 1.45 GiB | – | – | 8.18 GiB | 1.44 GiB |

Medians across repeats; whiskers in figures show min–max. Heap = peak anonymous memory of the process's cgroup; RSS = the main process's VmHWM, which also counts mmap'd index pages. Ztreamer's figures include its embedded Zakura node; Zaino's exclude Zebra, listed separately.

## Serving: latency (p50 / p99 ms)

| Scenario | zaino-0.10.1 | ztreamer-v0.1.0 | zaino-0.9.0 | ztreamer-master |
|---|---:|---:|---:|---:|
| GetLightdInfo | 2.474 / 41.147 | 0.095 / 0.399 | 2.385 / 41.274 | 0.080 / 0.346 |
| GetLatestBlock | 0.159 / 41.118 | 0.085 / 0.368 | 0.154 / 41.157 | 0.073 / 0.303 |
| GetBlock | 0.650 / 41.423 | 0.163 / 0.565 | 2.058 / 41.346 | 0.148 / 0.489 |
| GetBlockNullifiers | 0.257 / 41.251 | 0.160 / 0.522 | 0.267 / 41.311 | 0.148 / 0.443 |
| GetTreeState | 40.379 / 41.449 | 0.613 / 1.148 | 40.297 / 41.342 | 0.524 / 1.109 |
| GetLatestTreeState | 40.339 / 41.264 | 0.308 / 0.668 | 40.325 / 41.313 | 0.275 / 0.609 |
| GetSubtreeRoots/sapling-10 | 40.839 / 41.596 | 0.327 / 0.812 | 40.855 / 41.603 | 0.287 / 0.608 |
| GetSubtreeRoots/orchard-10 | 40.835 / 41.707 | 0.238 / 0.562 | 40.856 / 41.609 | 0.215 / 0.546 |
| GetMempoolTx | 40.838 / 41.547 | 0.196 / 0.506 | 40.851 / 41.518 | 0.181 / 0.467 |
| GetTransaction | 2.066 / 41.303 | 0.220 / 0.619 | 2.704 / 41.318 | 0.200 / 0.551 |
| GetTaddressBalance | 0.297 / 41.162 | 0.187 / 0.500 | 0.297 / 41.228 | 0.166 / 0.437 |
| GetAddressUtxos | 41.437 / 520.218 | 3.225 / 424.651 | 41.220 / 372.509 | 2.919 / 398.469 |

## Serving: ranges (blocks/s)

| Scenario | zaino-0.10.1 | ztreamer-v0.1.0 | zaino-0.9.0 | ztreamer-master |
|---|---:|---:|---:|---:|
| GetBlockRange/100 | 2,359 | 107,249 | 2,208 | 121,196 |
| GetBlockRange/1000 | 11,414 | 179,486 | 10,803 | 202,122 |
| GetBlockRange/10000 | 24,571 | 169,014 | 29,095 | 181,558 |
| GetBlockRange/100000 | 11,576 | 181,685 | 11,610 | 203,677 |

## Serving: scaling (blocks/s or req/s)

| Scenario | zaino-0.10.1 | ztreamer-v0.1.0 | zaino-0.9.0 | ztreamer-master |
|---|---:|---:|---:|---:|
| GetBlockRange/1000 x1 | 12,959 | 183,605 | 11,027 | 209,319 |
| GetBlock x1 | 132 req/s | 3,997 req/s | 58 req/s | 4,422 req/s |
| GetBlockRange/1000 x8 | 55,835 | 232,419 | 56,035 | 259,128 |
| GetBlock x8 | 1,006 req/s | 10,723 req/s | 461 req/s | 11,858 req/s |
| GetBlockRange/1000 x32 | 103,771 | 233,045 | 115,984 | 264,003 |
| GetBlock x32 | 3,236 req/s | 11,046 req/s | 1,780 req/s | 12,257 req/s |
| GetBlockRange/1000 x128 | 110,093 | 229,527 | 145,235 | 259,498 |
| GetBlock x128 | 6,843 req/s | 11,044 req/s | 5,528 req/s | 12,067 req/s |

## Serving: sync (blocks/s)

| Scenario | zaino-0.10.1 | ztreamer-v0.1.0 | zaino-0.9.0 | ztreamer-master |
|---|---:|---:|---:|---:|
| sync 280000-4382797 | 11,124 | 189,041 | 11,541 | 210,546 |

