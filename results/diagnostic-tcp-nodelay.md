# Serving with TCP_NODELAY forced on (diagnostic)

Each diagnostic run is the unmodified build with `ci/nodelay.c` preloaded, compared with the
default runs of the same build on a runner with the same CPU model. Latency in ms; throughput
in blocks/s for ranges and sync, requests/s otherwise.

## zaino-0.10.1

Runner CPU AMD EPYC 7763 64-Core Processor. Diagnostic `zaino-0.10.1-r1-nodelay` vs `zaino-0.10.1-r1`, `zaino-0.10.1-r2` (median if more than one).

| Scenario | p50 default | p50 nodelay | mean default | mean nodelay | throughput default | throughput nodelay |
|---|---:|---:|---:|---:|---:|---:|
| GetLightdInfo | 2.99 | 2.45 | 6.97 | 2.49 | 137 | 360 |
| GetLatestBlock | 0.19 | 0.15 | 4.41 | 0.18 | 216 | 3,074 |
| GetBlock | 0.64 | 0.87 | 7.21 | 0.71 | 128 | 1,110 |
| GetBlockNullifiers | 0.31 | 0.24 | 6.73 | 0.26 | 143 | 2,372 |
| GetTreeState | 40.33 | 0.75 | 21.86 | 0.79 | 43 | 1,027 |
| GetLatestTreeState | 40.37 | 0.48 | 21.54 | 0.50 | 44 | 1,502 |
| GetSubtreeRoots/sapling-10 | 40.84 | 30.05 | 41.93 | 30.16 | 23 | 31 |
| GetSubtreeRoots/orchard-10 | 41.28 | 6.22 | 41.20 | 6.25 | 23 | 149 |
| GetMempoolTx | 40.81 | 0.20 | 40.82 | 0.22 | 23 | 2,771 |
| GetTransaction | 2.72 | 0.90 | 19.40 | 1.25 | 49 | 684 |
| GetTaddressBalance | 0.34 | 0.29 | 4.32 | 0.31 | 204 | 2,162 |
| GetAddressUtxos | 41.56 | 3.82 | 207.02 | 171.61 | 5 | 6 |
| GetBlockRange/100 | 41.80 | 2.61 | 41.86 | 9.40 | 2,366 | 10,375 |
| GetBlockRange/1000 | 37.42 | 146.06 | 83.52 | 99.00 | 11,737 | 9,965 |
| GetBlockRange/10000 | 104.75 | 402.72 | 343.22 | 420.49 | 27,804 | 22,341 |
| GetBlockRange/100000 | 1073.04 | 8013.00 | 4887.09 | 7968.20 | 12,652 | 9,643 |
| GetBlockRange/1000 x1 | 16.08 | 131.57 | 73.17 | 90.47 | 13,653 | 11,026 |
| GetBlock x1 | 0.30 | 0.23 | 7.24 | 0.25 | 135 | 2,817 |
| GetBlockRange/1000 x8 | 52.96 | 49.31 | 140.20 | 192.84 | 56,628 | 41,248 |
| GetBlock x8 | 0.30 | 0.55 | 7.88 | 0.66 | 999 | 8,729 |
| GetBlockRange/1000 x32 | 192.88 | 194.99 | 287.75 | 454.00 | 108,417 | 68,743 |
| GetBlock x32 | 0.36 | 2.09 | 10.06 | 2.51 | 3,130 | 9,469 |
| GetBlockRange/1000 x128 | 994.07 | 857.60 | 1004.28 | 1166.19 | 115,197 | 106,275 |
| GetBlock x128 | 4.56 | 8.27 | 18.96 | 9.99 | 6,478 | 9,414 |
| sync 280000-4382797 | 755.70 | 773.92 | 839.46 | 808.41 | 11,943 | 12,343 |

## ztreamer-v0.1.0

Runner CPU AMD EPYC 7763 64-Core Processor. Diagnostic `ztreamer-v0.1.0-r1-nodelay` vs `ztreamer-v0.1.0-r3` (median if more than one).

| Scenario | p50 default | p50 nodelay | mean default | mean nodelay | throughput default | throughput nodelay |
|---|---:|---:|---:|---:|---:|---:|
| GetLightdInfo | 0.16 | 0.17 | 0.19 | 0.19 | 2,976 | 2,935 |
| GetLatestBlock | 0.15 | 0.15 | 0.18 | 0.18 | 3,114 | 3,092 |
| GetBlock | 0.24 | 0.24 | 0.29 | 0.27 | 2,272 | 2,317 |
| GetBlockNullifiers | 0.24 | 0.24 | 0.27 | 0.27 | 2,366 | 2,351 |
| GetTreeState | 0.63 | 0.62 | 0.67 | 0.67 | 1,160 | 1,169 |
| GetLatestTreeState | 0.44 | 0.44 | 0.47 | 0.47 | 1,600 | 1,584 |
| GetSubtreeRoots/sapling-10 | 0.49 | 0.50 | 0.51 | 0.51 | 1,502 | 1,511 |
| GetSubtreeRoots/orchard-10 | 0.37 | 0.37 | 0.38 | 0.38 | 1,887 | 1,870 |
| GetMempoolTx | 0.29 | 0.29 | 0.31 | 0.31 | 2,285 | 2,290 |
| GetTransaction | 0.32 | 0.32 | 0.36 | 0.37 | 1,930 | 1,905 |
| GetTaddressBalance | 0.29 | 0.29 | 0.31 | 0.31 | 2,199 | 2,209 |
| GetAddressUtxos | 3.71 | 3.70 | 166.17 | 164.39 | 6 | 6 |
| GetBlockRange/100 | 0.79 | 0.78 | 0.96 | 0.93 | 86,357 | 88,150 |
| GetBlockRange/1000 | 5.86 | 5.74 | 6.37 | 6.21 | 151,032 | 155,030 |
| GetBlockRange/10000 | 51.61 | 50.50 | 66.41 | 65.74 | 147,124 | 148,773 |
| GetBlockRange/100000 | 513.43 | 501.57 | 560.63 | 546.61 | 150,105 | 152,034 |
| GetBlockRange/1000 x1 | 5.06 | 4.92 | 6.12 | 6.08 | 158,848 | 159,885 |
| GetBlock x1 | 0.24 | 0.23 | 0.25 | 0.25 | 2,826 | 2,844 |
| GetBlockRange/1000 x8 | 32.72 | 33.30 | 35.31 | 35.74 | 200,416 | 199,260 |
| GetBlock x8 | 0.53 | 0.53 | 0.63 | 0.63 | 8,805 | 8,831 |
| GetBlockRange/1000 x32 | 121.73 | 120.90 | 133.29 | 133.61 | 200,254 | 201,615 |
| GetBlock x32 | 2.09 | 2.08 | 2.45 | 2.44 | 9,538 | 9,591 |
| GetBlockRange/1000 x128 | 529.70 | 536.46 | 557.76 | 567.13 | 200,552 | 200,145 |
| GetBlock x128 | 8.02 | 8.19 | 9.58 | 9.75 | 9,579 | 9,473 |
| sync 280000-4382797 | 49.76 | 49.95 | 60.01 | 60.21 | 165,602 | 165,096 |
