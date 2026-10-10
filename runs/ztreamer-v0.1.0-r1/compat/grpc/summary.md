# gRPC compatibility summary

| Method | Cases | ztreamer-v0.1.0 OK / oracle pass | Identical across servers |
|---|---:|---:|---:|
| GetLightdInfo | 1 | 1/1 · – | 0/0 |
| GetLatestBlock | 1 | 1/1 · – | 1/1 |
| GetLatestTreeState | 1 | 1/1 · – | 1/1 |
| Ping | 1 | 0/1 · – | 0/0 |
| GetBlock | 75 | 74/75 · 73/73 | 75/75 |
| GetBlockNullifiers | 68 | 68/68 · – | 68/68 |
| GetTreeState | 73 | 73/73 · 73/73 | 73/73 |
| GetBlockRange | 12 | 12/12 · 12/12 | 12/12 |
| GetBlockRangeNullifiers | 6 | 6/6 · 6/6 | 6/6 |
| GetTransaction | 6 | 5/6 · 5/5 | 6/6 |
| SendTransaction | 2 | 0/2 · – | 2/2 |
| GetTaddressTxids | 3 | 3/3 · 3/3 | 3/3 |
| GetTaddressTransactions | 3 | 3/3 · 3/3 | 3/3 |
| GetTaddressBalance | 5 | 4/5 · 4/4 | 5/5 |
| GetTaddressBalanceStream | 4 | 4/4 · 3/4 | 4/4 |
| GetAddressUtxos | 3 | 3/3 · 3/3 | 3/3 |
| GetAddressUtxosStream | 3 | 3/3 · 3/3 | 3/3 |
| GetMempoolTx | 1 | 1/1 · – | 1/1 |
| GetMempoolStream | 1 | 0/1 · – | 0/0 |
| GetSubtreeRoots | 5 | 5/5 · 4/4 | 5/5 |

## Disagreements


## Server identity (GetLightdInfo)

```json
{
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
```
