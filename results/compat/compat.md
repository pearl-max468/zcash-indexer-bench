# gRPC compatibility across systems

Inputs: upper height 4382797; one run per system; Zebra as reference.

| Method | Cases | zaino-0.10.1: OK · ref pass | zaino-0.9.0: OK · ref pass | ztreamer-master: OK · ref pass | ztreamer-v0.1.0: OK · ref pass | Byte-identical across all |
|---|---:|---:|---:|---:|---:|---:|
| GetLightdInfo | 1 | 1/1 · – | 1/1 · – | 1/1 · – | 1/1 · – | 0/1 |
| GetLatestBlock | 1 | 1/1 · – | 1/1 · – | 1/1 · – | 1/1 · – | 1/1 |
| GetLatestTreeState | 1 | 1/1 · – | 1/1 · – | 1/1 · – | 1/1 · – | 1/1 |
| Ping | 1 | 0/1 · – | 0/1 · – | 0/1 · – | 0/1 · – | 1/1 |
| GetBlock | 75 | 74/75 · 73/73 | 74/75 · 73/73 | 74/75 · 73/73 | 74/75 · 73/73 | 1/75 |
| GetBlockNullifiers | 68 | 68/68 · – | 68/68 · – | 68/68 · – | 68/68 · – | 6/68 |
| GetTreeState | 73 | 73/73 · 73/73 | 73/73 · 73/73 | 73/73 · 73/73 | 73/73 · 73/73 | 73/73 |
| GetBlockRange | 12 | 12/12 · 12/12 | 12/12 · 12/12 | 12/12 · 12/12 | 12/12 · 12/12 | 12/12 |
| GetBlockRangeNullifiers | 6 | 6/6 · 6/6 | 6/6 · 6/6 | 6/6 · 6/6 | 6/6 · 6/6 | 6/6 |
| GetTransaction | 6 | 5/6 · 5/5 | 5/6 · 5/5 | 5/6 · 5/5 | 5/6 · 5/5 | 5/6 |
| SendTransaction | 2 | 0/2 · – | 0/2 · – | 0/2 · – | 0/2 · – | 0/2 |
| GetTaddressTxids | 3 | 3/3 · 3/3 | 3/3 · 3/3 | 3/3 · 3/3 | 3/3 · 3/3 | 3/3 |
| GetTaddressTransactions | 3 | 3/3 · 3/3 | 3/3 · 3/3 | 3/3 · 3/3 | 3/3 · 3/3 | 3/3 |
| GetTaddressBalance | 5 | 4/5 · 4/4 | 4/5 · 4/4 | 4/5 · 4/4 | 4/5 · 4/4 | 4/5 |
| GetTaddressBalanceStream | 4 | 4/4 · 3/4 | 4/4 · 3/4 | 4/4 · 4/4 | 4/4 · 3/4 | 3/4 |
| GetAddressUtxos | 3 | 3/3 · 3/3 | 3/3 · 3/3 | 3/3 · 3/3 | 3/3 · 3/3 | 3/3 |
| GetAddressUtxosStream | 3 | 3/3 · 3/3 | 3/3 · 3/3 | 3/3 · 3/3 | 3/3 · 3/3 | 3/3 |
| GetMempoolTx | 1 | 1/1 · – | 1/1 · – | 1/1 · – | 1/1 · – | 1/1 |
| GetMempoolStream | 1 | 0/1 · – | 0/1 · – | 0/1 · – | 0/1 · – | 1/1 |
| GetSubtreeRoots | 5 | 5/5 · 4/4 | 5/5 · 4/4 | 5/5 · 4/4 | 5/5 · 4/4 | 0/5 |

## Cases where systems differ

- **GetLightdInfo** `info` — differs: zaino-0.10.1 | zaino-0.9.0 | ztreamer-master | ztreamer-v0.1.0. zaino-0.10.1: OK; zaino-0.9.0: OK; ztreamer-master: OK; ztreamer-v0.1.0: OK
- **GetBlock** `height=279999` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK pass 0 of 1 txs compact; zaino-0.9.0: OK pass 1 of 1 txs compact; ztreamer-master: OK pass 0 of 1 txs compact; ztreamer-v0.1.0: OK pass 0 of 1 txs compact
- **GetBlockNullifiers** `height=279999` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK; zaino-0.9.0: OK; ztreamer-master: OK; ztreamer-v0.1.0: OK
- **GetBlock** `height=280000` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK pass 0 of 1 txs compact; zaino-0.9.0: OK pass 1 of 1 txs compact; ztreamer-master: OK pass 0 of 1 txs compact; ztreamer-v0.1.0: OK pass 0 of 1 txs compact
- **GetBlockNullifiers** `height=280000` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK; zaino-0.9.0: OK; ztreamer-master: OK; ztreamer-v0.1.0: OK
- **GetBlock** `height=280001` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK pass 0 of 1 txs compact; zaino-0.9.0: OK pass 1 of 1 txs compact; ztreamer-master: OK pass 0 of 1 txs compact; ztreamer-v0.1.0: OK pass 0 of 1 txs compact
- **GetBlockNullifiers** `height=280001` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK; zaino-0.9.0: OK; ztreamer-master: OK; ztreamer-v0.1.0: OK
- **GetBlock** `height=350494` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK pass 0 of 1 txs compact; zaino-0.9.0: OK pass 1 of 1 txs compact; ztreamer-master: OK pass 0 of 1 txs compact; ztreamer-v0.1.0: OK pass 0 of 1 txs compact
- **GetBlockNullifiers** `height=350494` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK; zaino-0.9.0: OK; ztreamer-master: OK; ztreamer-v0.1.0: OK
- **GetBlock** `height=583999` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK pass 0 of 1 txs compact; zaino-0.9.0: OK pass 1 of 1 txs compact; ztreamer-master: OK pass 0 of 1 txs compact; ztreamer-v0.1.0: OK pass 0 of 1 txs compact
- **GetBlockNullifiers** `height=583999` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK; zaino-0.9.0: OK; ztreamer-master: OK; ztreamer-v0.1.0: OK
- **GetBlock** `height=584000` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK pass 0 of 1 txs compact; zaino-0.9.0: OK pass 1 of 1 txs compact; ztreamer-master: OK pass 0 of 1 txs compact; ztreamer-v0.1.0: OK pass 0 of 1 txs compact
- **GetBlockNullifiers** `height=584000` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK; zaino-0.9.0: OK; ztreamer-master: OK; ztreamer-v0.1.0: OK
- **GetBlock** `height=584001` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK pass 0 of 1 txs compact; zaino-0.9.0: OK pass 1 of 1 txs compact; ztreamer-master: OK pass 0 of 1 txs compact; ztreamer-v0.1.0: OK pass 0 of 1 txs compact
- **GetBlockNullifiers** `height=584001` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK; zaino-0.9.0: OK; ztreamer-master: OK; ztreamer-v0.1.0: OK
- **GetBlock** `height=723451` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK pass 0 of 1 txs compact; zaino-0.9.0: OK pass 1 of 1 txs compact; ztreamer-master: OK pass 0 of 1 txs compact; ztreamer-v0.1.0: OK pass 0 of 1 txs compact
- **GetBlockNullifiers** `height=723451` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK; zaino-0.9.0: OK; ztreamer-master: OK; ztreamer-v0.1.0: OK
- **GetBlock** `height=843371` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK pass 0 of 1 txs compact; zaino-0.9.0: OK pass 1 of 1 txs compact; ztreamer-master: OK pass 0 of 1 txs compact; ztreamer-v0.1.0: OK pass 0 of 1 txs compact
- **GetBlockNullifiers** `height=843371` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK; zaino-0.9.0: OK; ztreamer-master: OK; ztreamer-v0.1.0: OK
- **GetBlock** `height=874772` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK pass 0 of 1 txs compact; zaino-0.9.0: OK pass 1 of 1 txs compact; ztreamer-master: OK pass 0 of 1 txs compact; ztreamer-v0.1.0: OK pass 0 of 1 txs compact
- **GetBlockNullifiers** `height=874772` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK; zaino-0.9.0: OK; ztreamer-master: OK; ztreamer-v0.1.0: OK
- **GetBlock** `height=896900` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK pass 0 of 1 txs compact; zaino-0.9.0: OK pass 1 of 1 txs compact; ztreamer-master: OK pass 0 of 1 txs compact; ztreamer-v0.1.0: OK pass 0 of 1 txs compact
- **GetBlockNullifiers** `height=896900` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK; zaino-0.9.0: OK; ztreamer-master: OK; ztreamer-v0.1.0: OK
- **GetBlock** `height=903799` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK pass 0 of 1 txs compact; zaino-0.9.0: OK pass 1 of 1 txs compact; ztreamer-master: OK pass 0 of 1 txs compact; ztreamer-v0.1.0: OK pass 0 of 1 txs compact
- **GetBlockNullifiers** `height=903799` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK; zaino-0.9.0: OK; ztreamer-master: OK; ztreamer-v0.1.0: OK
- **GetBlock** `height=903800` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK pass 0 of 1 txs compact; zaino-0.9.0: OK pass 1 of 1 txs compact; ztreamer-master: OK pass 0 of 1 txs compact; ztreamer-v0.1.0: OK pass 0 of 1 txs compact
- **GetBlockNullifiers** `height=903800` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK; zaino-0.9.0: OK; ztreamer-master: OK; ztreamer-v0.1.0: OK
- **GetBlock** `height=903801` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK pass 0 of 1 txs compact; zaino-0.9.0: OK pass 1 of 1 txs compact; ztreamer-master: OK pass 0 of 1 txs compact; ztreamer-v0.1.0: OK pass 0 of 1 txs compact
- **GetBlockNullifiers** `height=903801` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK; zaino-0.9.0: OK; ztreamer-master: OK; ztreamer-v0.1.0: OK
- **GetBlock** `height=984098` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK pass 0 of 1 txs compact; zaino-0.9.0: OK pass 1 of 1 txs compact; ztreamer-master: OK pass 0 of 1 txs compact; ztreamer-v0.1.0: OK pass 0 of 1 txs compact
- **GetBlockNullifiers** `height=984098` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK; zaino-0.9.0: OK; ztreamer-master: OK; ztreamer-v0.1.0: OK
- **GetBlock** `height=1001845` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK pass 0 of 1 txs compact; zaino-0.9.0: OK pass 1 of 1 txs compact; ztreamer-master: OK pass 0 of 1 txs compact; ztreamer-v0.1.0: OK pass 0 of 1 txs compact
- **GetBlockNullifiers** `height=1001845` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK; zaino-0.9.0: OK; ztreamer-master: OK; ztreamer-v0.1.0: OK
- **GetBlock** `height=1028499` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK pass 0 of 1 txs compact; zaino-0.9.0: OK pass 1 of 1 txs compact; ztreamer-master: OK pass 0 of 1 txs compact; ztreamer-v0.1.0: OK pass 0 of 1 txs compact
- **GetBlockNullifiers** `height=1028499` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK; zaino-0.9.0: OK; ztreamer-master: OK; ztreamer-v0.1.0: OK
- **GetBlock** `height=1028500` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK pass 0 of 1 txs compact; zaino-0.9.0: OK pass 1 of 1 txs compact; ztreamer-master: OK pass 0 of 1 txs compact; ztreamer-v0.1.0: OK pass 0 of 1 txs compact
- **GetBlockNullifiers** `height=1028500` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK; zaino-0.9.0: OK; ztreamer-master: OK; ztreamer-v0.1.0: OK
- **GetBlock** `height=1028501` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK pass 0 of 1 txs compact; zaino-0.9.0: OK pass 1 of 1 txs compact; ztreamer-master: OK pass 0 of 1 txs compact; ztreamer-v0.1.0: OK pass 0 of 1 txs compact
- **GetBlockNullifiers** `height=1028501` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK; zaino-0.9.0: OK; ztreamer-master: OK; ztreamer-v0.1.0: OK
- **GetBlock** `height=1092515` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK pass 1 of 1 txs compact; zaino-0.9.0: OK pass 1 of 1 txs compact; ztreamer-master: OK pass 1 of 1 txs compact; ztreamer-v0.1.0: OK pass 1 of 1 txs compact
- **GetBlock** `height=1430953` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK pass 0 of 1 txs compact; zaino-0.9.0: OK pass 1 of 1 txs compact; ztreamer-master: OK pass 0 of 1 txs compact; ztreamer-v0.1.0: OK pass 0 of 1 txs compact
- **GetBlockNullifiers** `height=1430953` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK; zaino-0.9.0: OK; ztreamer-master: OK; ztreamer-v0.1.0: OK
- **GetBlock** `height=1509923` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK pass 0 of 1 txs compact; zaino-0.9.0: OK pass 1 of 1 txs compact; ztreamer-master: OK pass 0 of 1 txs compact; ztreamer-v0.1.0: OK pass 0 of 1 txs compact
- **GetBlockNullifiers** `height=1509923` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK; zaino-0.9.0: OK; ztreamer-master: OK; ztreamer-v0.1.0: OK
- **GetBlock** `height=1570287` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK pass 0 of 1 txs compact; zaino-0.9.0: OK pass 1 of 1 txs compact; ztreamer-master: OK pass 0 of 1 txs compact; ztreamer-v0.1.0: OK pass 0 of 1 txs compact
- **GetBlockNullifiers** `height=1570287` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK; zaino-0.9.0: OK; ztreamer-master: OK; ztreamer-v0.1.0: OK
- **GetBlock** `height=1589366` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK pass 0 of 1 txs compact; zaino-0.9.0: OK pass 1 of 1 txs compact; ztreamer-master: OK pass 0 of 1 txs compact; ztreamer-v0.1.0: OK pass 0 of 1 txs compact
- **GetBlockNullifiers** `height=1589366` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK; zaino-0.9.0: OK; ztreamer-master: OK; ztreamer-v0.1.0: OK
- **GetBlock** `height=1617199` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK pass 0 of 1 txs compact; zaino-0.9.0: OK pass 1 of 1 txs compact; ztreamer-master: OK pass 0 of 1 txs compact; ztreamer-v0.1.0: OK pass 0 of 1 txs compact
- **GetBlockNullifiers** `height=1617199` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK; zaino-0.9.0: OK; ztreamer-master: OK; ztreamer-v0.1.0: OK
- **GetBlock** `height=1650676` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK pass 0 of 1 txs compact; zaino-0.9.0: OK pass 1 of 1 txs compact; ztreamer-master: OK pass 0 of 1 txs compact; ztreamer-v0.1.0: OK pass 0 of 1 txs compact
- **GetBlockNullifiers** `height=1650676` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK; zaino-0.9.0: OK; ztreamer-master: OK; ztreamer-v0.1.0: OK
- **GetBlock** `height=1668200` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK pass 0 of 1 txs compact; zaino-0.9.0: OK pass 1 of 1 txs compact; ztreamer-master: OK pass 0 of 1 txs compact; ztreamer-v0.1.0: OK pass 0 of 1 txs compact
- **GetBlockNullifiers** `height=1668200` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK; zaino-0.9.0: OK; ztreamer-master: OK; ztreamer-v0.1.0: OK
- **GetBlock** `height=1686066` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK pass 0 of 1 txs compact; zaino-0.9.0: OK pass 1 of 1 txs compact; ztreamer-master: OK pass 0 of 1 txs compact; ztreamer-v0.1.0: OK pass 0 of 1 txs compact
- **GetBlockNullifiers** `height=1686066` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK; zaino-0.9.0: OK; ztreamer-master: OK; ztreamer-v0.1.0: OK
- **GetBlock** `height=1769442` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK pass 0 of 1 txs compact; zaino-0.9.0: OK pass 1 of 1 txs compact; ztreamer-master: OK pass 0 of 1 txs compact; ztreamer-v0.1.0: OK pass 0 of 1 txs compact
- **GetBlockNullifiers** `height=1769442` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK; zaino-0.9.0: OK; ztreamer-master: OK; ztreamer-v0.1.0: OK
- **GetBlock** `height=1842419` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK pass 0 of 1 txs compact; zaino-0.9.0: OK pass 1 of 1 txs compact; ztreamer-master: OK pass 0 of 1 txs compact; ztreamer-v0.1.0: OK pass 0 of 1 txs compact
- **GetBlockNullifiers** `height=1842419` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK; zaino-0.9.0: OK; ztreamer-master: OK; ztreamer-v0.1.0: OK
- **GetBlock** `height=1842420` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK pass 0 of 1 txs compact; zaino-0.9.0: OK pass 1 of 1 txs compact; ztreamer-master: OK pass 0 of 1 txs compact; ztreamer-v0.1.0: OK pass 0 of 1 txs compact
- **GetBlockNullifiers** `height=1842420` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK; zaino-0.9.0: OK; ztreamer-master: OK; ztreamer-v0.1.0: OK
- **GetBlock** `height=1842421` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK pass 1 of 2 txs compact; zaino-0.9.0: OK pass 2 of 2 txs compact; ztreamer-master: OK pass 1 of 2 txs compact; ztreamer-v0.1.0: OK pass 1 of 2 txs compact
- **GetBlockNullifiers** `height=1842421` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK; zaino-0.9.0: OK; ztreamer-master: OK; ztreamer-v0.1.0: OK
- **GetBlock** `height=2108826` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK pass 0 of 1 txs compact; zaino-0.9.0: OK pass 1 of 1 txs compact; ztreamer-master: OK pass 0 of 1 txs compact; ztreamer-v0.1.0: OK pass 0 of 1 txs compact
- **GetBlockNullifiers** `height=2108826` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK; zaino-0.9.0: OK; ztreamer-master: OK; ztreamer-v0.1.0: OK
- **GetBlock** `height=2200289` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK pass 0 of 1 txs compact; zaino-0.9.0: OK pass 1 of 1 txs compact; ztreamer-master: OK pass 0 of 1 txs compact; ztreamer-v0.1.0: OK pass 0 of 1 txs compact
- **GetBlockNullifiers** `height=2200289` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK; zaino-0.9.0: OK; ztreamer-master: OK; ztreamer-v0.1.0: OK
- **GetBlock** `height=2208164` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK pass 0 of 1 txs compact; zaino-0.9.0: OK pass 1 of 1 txs compact; ztreamer-master: OK pass 0 of 1 txs compact; ztreamer-v0.1.0: OK pass 0 of 1 txs compact
- **GetBlockNullifiers** `height=2208164` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK; zaino-0.9.0: OK; ztreamer-master: OK; ztreamer-v0.1.0: OK
- **GetBlock** `height=2223078` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK pass 0 of 1 txs compact; zaino-0.9.0: OK pass 1 of 1 txs compact; ztreamer-master: OK pass 0 of 1 txs compact; ztreamer-v0.1.0: OK pass 0 of 1 txs compact
- **GetBlockNullifiers** `height=2223078` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK; zaino-0.9.0: OK; ztreamer-master: OK; ztreamer-v0.1.0: OK
- **GetBlock** `height=2389415` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK pass 0 of 1 txs compact; zaino-0.9.0: OK pass 1 of 1 txs compact; ztreamer-master: OK pass 0 of 1 txs compact; ztreamer-v0.1.0: OK pass 0 of 1 txs compact
- **GetBlockNullifiers** `height=2389415` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK; zaino-0.9.0: OK; ztreamer-master: OK; ztreamer-v0.1.0: OK
- **GetBlock** `height=2901405` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK pass 0 of 1 txs compact; zaino-0.9.0: OK pass 1 of 1 txs compact; ztreamer-master: OK pass 0 of 1 txs compact; ztreamer-v0.1.0: OK pass 0 of 1 txs compact
- **GetBlockNullifiers** `height=2901405` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK; zaino-0.9.0: OK; ztreamer-master: OK; ztreamer-v0.1.0: OK
- **GetBlock** `height=2906382` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK pass 0 of 1 txs compact; zaino-0.9.0: OK pass 1 of 1 txs compact; ztreamer-master: OK pass 0 of 1 txs compact; ztreamer-v0.1.0: OK pass 0 of 1 txs compact
- **GetBlockNullifiers** `height=2906382` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK; zaino-0.9.0: OK; ztreamer-master: OK; ztreamer-v0.1.0: OK
- **GetBlock** `height=2975999` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK pass 0 of 1 txs compact; zaino-0.9.0: OK pass 1 of 1 txs compact; ztreamer-master: OK pass 0 of 1 txs compact; ztreamer-v0.1.0: OK pass 0 of 1 txs compact
- **GetBlockNullifiers** `height=2975999` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK; zaino-0.9.0: OK; ztreamer-master: OK; ztreamer-v0.1.0: OK
- **GetBlock** `height=2976000` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK pass 0 of 1 txs compact; zaino-0.9.0: OK pass 1 of 1 txs compact; ztreamer-master: OK pass 0 of 1 txs compact; ztreamer-v0.1.0: OK pass 0 of 1 txs compact
- **GetBlockNullifiers** `height=2976000` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK; zaino-0.9.0: OK; ztreamer-master: OK; ztreamer-v0.1.0: OK
- **GetBlock** `height=2976001` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK pass 0 of 1 txs compact; zaino-0.9.0: OK pass 1 of 1 txs compact; ztreamer-master: OK pass 0 of 1 txs compact; ztreamer-v0.1.0: OK pass 0 of 1 txs compact
- **GetBlockNullifiers** `height=2976001` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK; zaino-0.9.0: OK; ztreamer-master: OK; ztreamer-v0.1.0: OK
- **GetBlock** `height=2990864` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK pass 0 of 1 txs compact; zaino-0.9.0: OK pass 1 of 1 txs compact; ztreamer-master: OK pass 0 of 1 txs compact; ztreamer-v0.1.0: OK pass 0 of 1 txs compact
- **GetBlockNullifiers** `height=2990864` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK; zaino-0.9.0: OK; ztreamer-master: OK; ztreamer-v0.1.0: OK
- **GetBlock** `height=3001713` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK pass 0 of 1 txs compact; zaino-0.9.0: OK pass 1 of 1 txs compact; ztreamer-master: OK pass 0 of 1 txs compact; ztreamer-v0.1.0: OK pass 0 of 1 txs compact
- **GetBlockNullifiers** `height=3001713` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK; zaino-0.9.0: OK; ztreamer-master: OK; ztreamer-v0.1.0: OK
- **GetBlock** `height=3135279` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK pass 0 of 1 txs compact; zaino-0.9.0: OK pass 1 of 1 txs compact; ztreamer-master: OK pass 0 of 1 txs compact; ztreamer-v0.1.0: OK pass 0 of 1 txs compact
- **GetBlockNullifiers** `height=3135279` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK; zaino-0.9.0: OK; ztreamer-master: OK; ztreamer-v0.1.0: OK
- **GetBlock** `height=3256693` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK pass 0 of 1 txs compact; zaino-0.9.0: OK pass 1 of 1 txs compact; ztreamer-master: OK pass 0 of 1 txs compact; ztreamer-v0.1.0: OK pass 0 of 1 txs compact
- **GetBlockNullifiers** `height=3256693` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK; zaino-0.9.0: OK; ztreamer-master: OK; ztreamer-v0.1.0: OK
- **GetBlock** `height=3317406` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK pass 1 of 1 txs compact; zaino-0.9.0: OK pass 1 of 1 txs compact; ztreamer-master: OK pass 1 of 1 txs compact; ztreamer-v0.1.0: OK pass 1 of 1 txs compact
- **GetBlock** `height=3472373` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK pass 0 of 1 txs compact; zaino-0.9.0: OK pass 1 of 1 txs compact; ztreamer-master: OK pass 0 of 1 txs compact; ztreamer-v0.1.0: OK pass 0 of 1 txs compact
- **GetBlockNullifiers** `height=3472373` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK; zaino-0.9.0: OK; ztreamer-master: OK; ztreamer-v0.1.0: OK
- **GetBlock** `height=3536499` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK pass 0 of 1 txs compact; zaino-0.9.0: OK pass 1 of 1 txs compact; ztreamer-master: OK pass 0 of 1 txs compact; ztreamer-v0.1.0: OK pass 0 of 1 txs compact
- **GetBlockNullifiers** `height=3536499` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK; zaino-0.9.0: OK; ztreamer-master: OK; ztreamer-v0.1.0: OK
- **GetBlock** `height=3536500` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK pass 0 of 1 txs compact; zaino-0.9.0: OK pass 1 of 1 txs compact; ztreamer-master: OK pass 0 of 1 txs compact; ztreamer-v0.1.0: OK pass 0 of 1 txs compact
- **GetBlockNullifiers** `height=3536500` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK; zaino-0.9.0: OK; ztreamer-master: OK; ztreamer-v0.1.0: OK
- **GetBlock** `height=3536501` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK pass 0 of 1 txs compact; zaino-0.9.0: OK pass 1 of 1 txs compact; ztreamer-master: OK pass 0 of 1 txs compact; ztreamer-v0.1.0: OK pass 0 of 1 txs compact
- **GetBlockNullifiers** `height=3536501` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK; zaino-0.9.0: OK; ztreamer-master: OK; ztreamer-v0.1.0: OK
- **GetBlock** `height=3582373` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK pass 1 of 1 txs compact; zaino-0.9.0: OK pass 1 of 1 txs compact; ztreamer-master: OK pass 1 of 1 txs compact; ztreamer-v0.1.0: OK pass 1 of 1 txs compact
- **GetBlock** `height=3738392` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK pass 0 of 1 txs compact; zaino-0.9.0: OK pass 1 of 1 txs compact; ztreamer-master: OK pass 0 of 1 txs compact; ztreamer-v0.1.0: OK pass 0 of 1 txs compact
- **GetBlockNullifiers** `height=3738392` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK; zaino-0.9.0: OK; ztreamer-master: OK; ztreamer-v0.1.0: OK
- **GetBlock** `height=3803062` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK pass 0 of 1 txs compact; zaino-0.9.0: OK pass 1 of 1 txs compact; ztreamer-master: OK pass 0 of 1 txs compact; ztreamer-v0.1.0: OK pass 0 of 1 txs compact
- **GetBlockNullifiers** `height=3803062` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK; zaino-0.9.0: OK; ztreamer-master: OK; ztreamer-v0.1.0: OK
- **GetBlock** `height=3845282` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK pass 0 of 1 txs compact; zaino-0.9.0: OK pass 1 of 1 txs compact; ztreamer-master: OK pass 0 of 1 txs compact; ztreamer-v0.1.0: OK pass 0 of 1 txs compact
- **GetBlockNullifiers** `height=3845282` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK; zaino-0.9.0: OK; ztreamer-master: OK; ztreamer-v0.1.0: OK
- **GetBlock** `height=3885879` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK pass 0 of 1 txs compact; zaino-0.9.0: OK pass 1 of 1 txs compact; ztreamer-master: OK pass 0 of 1 txs compact; ztreamer-v0.1.0: OK pass 0 of 1 txs compact
- **GetBlockNullifiers** `height=3885879` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK; zaino-0.9.0: OK; ztreamer-master: OK; ztreamer-v0.1.0: OK
- **GetBlock** `height=4051999` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK pass 0 of 1 txs compact; zaino-0.9.0: OK pass 1 of 1 txs compact; ztreamer-master: OK pass 0 of 1 txs compact; ztreamer-v0.1.0: OK pass 0 of 1 txs compact
- **GetBlockNullifiers** `height=4051999` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK; zaino-0.9.0: OK; ztreamer-master: OK; ztreamer-v0.1.0: OK
- **GetBlock** `height=4052000` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK pass 2 of 3 txs compact; zaino-0.9.0: OK pass 3 of 3 txs compact; ztreamer-master: OK pass 2 of 3 txs compact; ztreamer-v0.1.0: OK pass 2 of 3 txs compact
- **GetBlockNullifiers** `height=4052000` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK; zaino-0.9.0: OK; ztreamer-master: OK; ztreamer-v0.1.0: OK
- **GetBlock** `height=4052001` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK pass 0 of 1 txs compact; zaino-0.9.0: OK pass 1 of 1 txs compact; ztreamer-master: OK pass 0 of 1 txs compact; ztreamer-v0.1.0: OK pass 0 of 1 txs compact
- **GetBlockNullifiers** `height=4052001` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK; zaino-0.9.0: OK; ztreamer-master: OK; ztreamer-v0.1.0: OK
- **GetBlock** `height=4069643` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK pass 1 of 1 txs compact; zaino-0.9.0: OK pass 1 of 1 txs compact; ztreamer-master: OK pass 1 of 1 txs compact; ztreamer-v0.1.0: OK pass 1 of 1 txs compact
- **GetBlock** `height=4114325` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK pass 1 of 1 txs compact; zaino-0.9.0: OK pass 1 of 1 txs compact; ztreamer-master: OK pass 1 of 1 txs compact; ztreamer-v0.1.0: OK pass 1 of 1 txs compact
- **GetBlock** `height=4133999` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK pass 0 of 1 txs compact; zaino-0.9.0: OK pass 1 of 1 txs compact; ztreamer-master: OK pass 0 of 1 txs compact; ztreamer-v0.1.0: OK pass 0 of 1 txs compact
- **GetBlockNullifiers** `height=4133999` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK; zaino-0.9.0: OK; ztreamer-master: OK; ztreamer-v0.1.0: OK
- **GetBlock** `height=4134000` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK pass 0 of 1 txs compact; zaino-0.9.0: OK pass 1 of 1 txs compact; ztreamer-master: OK pass 0 of 1 txs compact; ztreamer-v0.1.0: OK pass 0 of 1 txs compact
- **GetBlockNullifiers** `height=4134000` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK; zaino-0.9.0: OK; ztreamer-master: OK; ztreamer-v0.1.0: OK
- **GetBlock** `height=4134001` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK pass 0 of 1 txs compact; zaino-0.9.0: OK pass 1 of 1 txs compact; ztreamer-master: OK pass 0 of 1 txs compact; ztreamer-v0.1.0: OK pass 0 of 1 txs compact
- **GetBlockNullifiers** `height=4134001` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK; zaino-0.9.0: OK; ztreamer-master: OK; ztreamer-v0.1.0: OK
- **GetBlock** `height=4205892` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK pass 0 of 1 txs compact; zaino-0.9.0: OK pass 1 of 1 txs compact; ztreamer-master: OK pass 0 of 1 txs compact; ztreamer-v0.1.0: OK pass 0 of 1 txs compact
- **GetBlockNullifiers** `height=4205892` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK; zaino-0.9.0: OK; ztreamer-master: OK; ztreamer-v0.1.0: OK
- **GetBlock** `height=4225517` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK pass 0 of 1 txs compact; zaino-0.9.0: OK pass 1 of 1 txs compact; ztreamer-master: OK pass 0 of 1 txs compact; ztreamer-v0.1.0: OK pass 0 of 1 txs compact
- **GetBlockNullifiers** `height=4225517` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK; zaino-0.9.0: OK; ztreamer-master: OK; ztreamer-v0.1.0: OK
- **GetBlock** `height=4329097` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK pass 0 of 1 txs compact; zaino-0.9.0: OK pass 1 of 1 txs compact; ztreamer-master: OK pass 0 of 1 txs compact; ztreamer-v0.1.0: OK pass 0 of 1 txs compact
- **GetBlockNullifiers** `height=4329097` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK; zaino-0.9.0: OK; ztreamer-master: OK; ztreamer-v0.1.0: OK
- **GetBlock** `height=4382797` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK pass 1 of 1 txs compact; zaino-0.9.0: OK pass 1 of 1 txs compact; ztreamer-master: OK pass 1 of 1 txs compact; ztreamer-v0.1.0: OK pass 1 of 1 txs compact
- **GetBlock** `hash@350494` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK pass 0 of 1 txs compact; zaino-0.9.0: OK pass 1 of 1 txs compact; ztreamer-master: OK pass 0 of 1 txs compact; ztreamer-v0.1.0: OK pass 0 of 1 txs compact
- **GetBlock** `hash@723451` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK pass 0 of 1 txs compact; zaino-0.9.0: OK pass 1 of 1 txs compact; ztreamer-master: OK pass 0 of 1 txs compact; ztreamer-v0.1.0: OK pass 0 of 1 txs compact
- **GetBlock** `hash@843371` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK pass 0 of 1 txs compact; zaino-0.9.0: OK pass 1 of 1 txs compact; ztreamer-master: OK pass 0 of 1 txs compact; ztreamer-v0.1.0: OK pass 0 of 1 txs compact
- **GetBlock** `hash@874772` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK pass 0 of 1 txs compact; zaino-0.9.0: OK pass 1 of 1 txs compact; ztreamer-master: OK pass 0 of 1 txs compact; ztreamer-v0.1.0: OK pass 0 of 1 txs compact
- **GetBlock** `hash@896900` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK pass 0 of 1 txs compact; zaino-0.9.0: OK pass 1 of 1 txs compact; ztreamer-master: OK pass 0 of 1 txs compact; ztreamer-v0.1.0: OK pass 0 of 1 txs compact
- **GetBlock** `pre-sapling height=1` — differs: zaino-0.10.1,ztreamer-master,ztreamer-v0.1.0 | zaino-0.9.0. zaino-0.10.1: OK; zaino-0.9.0: OK; ztreamer-master: OK; ztreamer-v0.1.0: OK
- **SendTransaction** `already-mined tx` — status differs. zaino-0.10.1: INTERNAL  InternalServerError: error receiving data from backing node: critical error in backing blo; zaino-0.9.0: INTERNAL  InternalServerError: error receiving data from backing node; ztreamer-master: INVALID_ARGUMENT  Zakura rejected transaction: transaction verification failed: failed to validate tx: trans; ztreamer-v0.1.0: INVALID_ARGUMENT  Zakura rejected transaction: transaction verification failed: failed to validate tx: trans
- **SendTransaction** `malformed bytes` — status differs. zaino-0.10.1: INTERNAL  InternalServerError: error receiving data from backing node: critical error in backing blo; zaino-0.9.0: INTERNAL  InternalServerError: error receiving data from backing node; ztreamer-master: INVALID_ARGUMENT  invalid transaction: parse error: bad tx header; ztreamer-v0.1.0: INVALID_ARGUMENT  invalid transaction: parse error: bad tx header
- **GetTransaction** `unknown txid` — status differs. zaino-0.10.1: INTERNAL  RPC error: LegacyRpcError { code: -5, message: "No such mempool or main chain transaction"; zaino-0.9.0: INTERNAL  RPC error: LegacyRpcError { code: -5, message: "No such mempool or main chain transaction"; ztreamer-master: NOT_FOUND  transaction not found; ztreamer-v0.1.0: NOT_FOUND  transaction not found
- **GetTaddressBalanceStream** `all fixtures + duplicate` — differs: zaino-0.10.1,zaino-0.9.0,ztreamer-v0.1.0 | ztreamer-master. zaino-0.10.1: OK FAIL valueZat 870875041300 vs zebra 819125020650; zaino-0.9.0: OK FAIL valueZat 870875041300 vs zebra 819125020650; ztreamer-master: OK pass valueZat 819125020650 vs zebra 819125020650; ztreamer-v0.1.0: OK FAIL valueZat 870875041300 vs zebra 819125020650
- **GetTaddressBalance** `invalid address` — status differs. zaino-0.10.1: INTERNAL  InternalServerError: error receiving data from backing node: critical error in backing blo; zaino-0.9.0: INTERNAL  InternalServerError: error receiving data from backing node; ztreamer-master: INVALID_ARGUMENT  invalid address: parse error: invalid Bech32 encoding; ztreamer-v0.1.0: INVALID_ARGUMENT  invalid address: parse error: invalid Bech32 encoding
- **GetSubtreeRoots** `sapling all` — differs: zaino-0.10.1,zaino-0.9.0 | ztreamer-master,ztreamer-v0.1.0. zaino-0.10.1: OK pass 6 roots match z_getsubtreesbyindex; zaino-0.9.0: OK pass 6 roots match z_getsubtreesbyindex; ztreamer-master: OK pass 6 roots match z_getsubtreesbyindex; ztreamer-v0.1.0: OK pass 6 roots match z_getsubtreesbyindex
- **GetSubtreeRoots** `sapling from 2, max 3` — differs: zaino-0.10.1,zaino-0.9.0 | ztreamer-master,ztreamer-v0.1.0. zaino-0.10.1: OK pass 3 roots match z_getsubtreesbyindex; zaino-0.9.0: OK pass 3 roots match z_getsubtreesbyindex; ztreamer-master: OK pass 3 roots match z_getsubtreesbyindex; ztreamer-v0.1.0: OK pass 3 roots match z_getsubtreesbyindex
- **GetSubtreeRoots** `orchard all` — differs: zaino-0.10.1,zaino-0.9.0 | ztreamer-master,ztreamer-v0.1.0. zaino-0.10.1: OK pass 3 roots match z_getsubtreesbyindex; zaino-0.9.0: OK pass 3 roots match z_getsubtreesbyindex; ztreamer-master: OK pass 3 roots match z_getsubtreesbyindex; ztreamer-v0.1.0: OK pass 3 roots match z_getsubtreesbyindex
- **GetSubtreeRoots** `orchard from 2, max 3` — differs: zaino-0.10.1,zaino-0.9.0 | ztreamer-master,ztreamer-v0.1.0. zaino-0.10.1: OK pass 1 roots match z_getsubtreesbyindex; zaino-0.9.0: OK pass 1 roots match z_getsubtreesbyindex; ztreamer-master: OK pass 1 roots match z_getsubtreesbyindex; ztreamer-v0.1.0: OK pass 1 roots match z_getsubtreesbyindex
- **GetSubtreeRoots** `ironwood (not active on mainnet)` — differs: zaino-0.10.1,zaino-0.9.0 | ztreamer-master,ztreamer-v0.1.0. zaino-0.10.1: OK; zaino-0.9.0: OK; ztreamer-master: OK; ztreamer-v0.1.0: OK

# JSON-RPC coverage

| Method | Case | zaino-0.10.1 | zaino-0.9.0 | ztreamer-master | ztreamer-v0.1.0 | Zebra |
|---|---|---|---|---|---|---|
| getinfo |  | ok | ok | ok | ok | ok |
| getblockchaininfo |  | ok | ok | ok | ok | ok |
| getblockcount |  | ok | ok | ok | ok | ok |
| getbestblockhash |  | ok | ok | ok | ok | ok |
| getdifficulty |  | ok | ok | ok | ok | ok |
| getmininginfo |  | ok | ok | ok | ok | ok |
| getnetworksolps |  | ok | ok | ok | ok | ok |
| getpeerinfo |  | ok | ok | ok | ok | ok |
| getmempoolinfo |  | ok | ok | ok | ok | ok |
| getrawmempool |  | ok | ok | ok | ok | ok |
| getchaintips |  | ok | ok | ok | ok | error -32601 |
| gettxoutsetinfo |  | ok | ok | error -32601 | error -32601 | error -32601 |
| getblock | height verbosity 0 | ok (= zebra) | ok (= zebra) | ok (= zebra) | ok (= zebra) | ok |
| getblock | height verbosity 1 | ok (≠ zebra) | ok (≠ zebra) | ok (= zebra) | ok (= zebra) | ok |
| getblock | height verbosity 2 | ok (≠ zebra) | ok (≠ zebra) | ok (≠ zebra) | ok (≠ zebra) | ok |
| getblock | hash verbosity 1 | ok (≠ zebra) | ok (≠ zebra) | ok (= zebra) | ok (= zebra) | ok |
| getblockheader | verbose | ok (= zebra) | ok (= zebra) | ok (= zebra) | ok (= zebra) | ok |
| getblockheader | hex | ok (= zebra) | ok (= zebra) | ok (= zebra) | ok (= zebra) | ok |
| getblockdeltas |  | ok | ok | error -32601 | error -32601 | error -32601 |
| getblocksubsidy |  | ok (= zebra) | ok (= zebra) | ok (≠ zebra) | ok (≠ zebra) | ok |
| getrawtransaction | hex | ok (≠ zebra) | ok (≠ zebra) | ok (= zebra) | ok (= zebra) | ok |
| getrawtransaction | verbose | ok (= zebra) | ok (≠ zebra) | ok (= zebra) | ok (= zebra) | ok |
| getspentinfo | output 0 | error -1 | error -1 | error -32601 | error -32601 | error -32601 |
| sendrawtransaction | already mined | error -8 | error -8 | error -25 | error -25 | error -25 |
| validateaddress |  | ok (= zebra) | ok (= zebra) | ok (= zebra) | ok (= zebra) | ok |
| z_validateaddress |  | ok (≠ zebra) | ok (≠ zebra) | ok (= zebra) | ok (= zebra) | ok |
| z_gettreestate |  | ok (= zebra) | ok (≠ zebra) | ok (= zebra) | ok (= zebra) | ok |
| z_getsubtreesbyindex | sapling 0..3 | ok (= zebra) | ok (= zebra) | ok (= zebra) | ok (= zebra) | ok |
| z_getsubtreesbyindex | orchard 0..3 | ok (= zebra) | ok (= zebra) | ok (= zebra) | ok (= zebra) | ok |
| getaddressbalance |  | ok | ok | ok | ok | ok |
| getaddresstxids | quiet, full range | ok (= zebra) | ok (= zebra) | ok (= zebra) | ok (= zebra) | ok |
| getaddressutxos |  | ok | ok | ok | ok | ok |
| getaddressdeltas | quiet, full range | ok | error -32601 | error -32601 | error -32601 | error -32601 |
| gettxout | unspent output | ok (≠ zebra) | ok (≠ zebra) | ok (= zebra) | ok (= zebra) | ok |

## Server identity

```json
{
  "zaino-0.10.1-r1": {
    "upper_height": 4382797,
    "upper_hash": "005fcbb2921b64191535e49eb788b8d83848043ab2f46ef1c220621f85822227",
    "seed": 20261009,
    "case_count": 274,
    "lightd_info": {
      "zaino-0.10.1": {
        "version": "0.10.1",
        "vendor": "ZingoLabs ZainoD",
        "taddrSupport": true,
        "chainName": "test",
        "saplingActivationHeight": "280000",
        "consensusBranchId": "37a5165b",
        "blockHeight": "4382897",
        "gitCommit": "3244a74bb09fa6a09a4b2deeb6be53bab0890747",
        "branch": "HEAD",
        "buildDate": "unknown",
        "buildUser": "runner",
        "estimatedHeight": "4403250",
        "zcashdBuild": "v6.4.2",
        "zcashdSubversion": "/Zebra:6.4.2/",
        "upgradeName": "NU6.3",
        "upgradeHeight": "4134000",
        "lightwalletProtocolVersion": "v0.5.0",
        "donationAddress": ""
      }
    }
  },
  "zaino-0.9.0-r1": {
    "upper_height": 4382797,
    "upper_hash": "005fcbb2921b64191535e49eb788b8d83848043ab2f46ef1c220621f85822227",
    "seed": 20261009,
    "case_count": 274,
    "lightd_info": {
      "zaino-0.9.0": {
        "version": "0.9.0",
        "vendor": "ZingoLabs ZainoD",
        "taddrSupport": true,
        "chainName": "test",
        "saplingActivationHeight": "280000",
        "consensusBranchId": "37a5165b",
        "blockHeight": "4382897",
        "gitCommit": "d27ec9303858d0216367f5469e37364a4f34ee2c",
        "branch": "HEAD",
        "buildDate": "unknown",
        "buildUser": "runner",
        "estimatedHeight": "4403247",
        "zcashdBuild": "v6.4.2",
        "zcashdSubversion": "/Zebra:6.4.2/",
        "upgradeName": "NU6.3",
        "upgradeHeight": "4134000",
        "lightwalletProtocolVersion": "v0.5.0",
        "donationAddress": ""
      }
    }
  },
  "ztreamer-master-r1": {
    "upper_height": 4382797,
    "upper_hash": "005fcbb2921b64191535e49eb788b8d83848043ab2f46ef1c220621f85822227",
    "seed": 20261009,
    "case_count": 274,
    "lightd_info": {
      "ztreamer-master": {
        "version": "0.1.0",
        "vendor": "Ztreamer",
        "taddrSupport": true,
        "chainName": "test",
        "saplingActivationHeight": "280000",
        "consensusBranchId": "37a5165b",
        "blockHeight": "4382897",
        "estimatedHeight": "4382897",
        "zcashdBuild": "v1.5.1+gaf944f5194ef",
        "zcashdSubversion": "/Zakura:1.5.1/",
        "lightwalletProtocolVersion": "v0.5.0",
        "gitCommit": "",
        "branch": "",
        "buildDate": "",
        "buildUser": "",
        "donationAddress": "",
        "upgradeName": "",
        "upgradeHeight": "0"
      }
    }
  },
  "ztreamer-v0.1.0-r1": {
    "upper_height": 4382797,
    "upper_hash": "005fcbb2921b64191535e49eb788b8d83848043ab2f46ef1c220621f85822227",
    "seed": 20261009,
    "case_count": 274,
    "lightd_info": {
      "ztreamer-v0.1.0": {
        "version": "0.1.0",
        "vendor": "Ztreamer",
        "taddrSupport": true,
        "chainName": "test",
        "saplingActivationHeight": "280000",
        "consensusBranchId": "37a5165b",
        "blockHeight": "4382897",
        "estimatedHeight": "4382897",
        "zcashdBuild": "v1.3.1+gf4d44dd5cce2",
        "zcashdSubversion": "/Zakura:1.3.1/",
        "lightwalletProtocolVersion": "v0.5.0",
        "gitCommit": "",
        "branch": "",
        "buildDate": "",
        "buildUser": "",
        "donationAddress": "",
        "upgradeName": "",
        "upgradeHeight": "0"
      }
    }
  }
}
```
