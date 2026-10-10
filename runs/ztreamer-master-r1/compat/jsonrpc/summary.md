# JSON-RPC coverage

| Method | Case | ztreamer-master | zebra |
|---|---|---|---|
| getinfo |  | ok | ok |
| getblockchaininfo |  | ok | ok |
| getblockcount |  | ok | ok |
| getbestblockhash |  | ok | ok |
| getdifficulty |  | ok | ok |
| getmininginfo |  | ok | ok |
| getnetworksolps |  | ok | ok |
| getpeerinfo |  | ok | ok |
| getmempoolinfo |  | ok | ok |
| getrawmempool |  | ok | ok |
| getchaintips |  | ok | error -32601 |
| gettxoutsetinfo |  | error -32601 | error -32601 |
| getblock | height verbosity 0 | ok (= zebra) | ok |
| getblock | height verbosity 1 | ok (= zebra) | ok |
| getblock | height verbosity 2 | ok (≠ zebra) | ok |
| getblock | hash verbosity 1 | ok (= zebra) | ok |
| getblockheader | verbose | ok (= zebra) | ok |
| getblockheader | hex | ok (= zebra) | ok |
| getblockdeltas |  | error -32601 | error -32601 |
| getblocksubsidy |  | ok (≠ zebra) | ok |
| getrawtransaction | hex | ok (= zebra) | ok |
| getrawtransaction | verbose | ok (= zebra) | ok |
| getspentinfo | output 0 | error -32601 | error -32601 |
| sendrawtransaction | already mined | error -25 | error -25 |
| validateaddress |  | ok (= zebra) | ok |
| z_validateaddress |  | ok (= zebra) | ok |
| z_gettreestate |  | ok (= zebra) | ok |
| z_getsubtreesbyindex | sapling 0..3 | ok (= zebra) | ok |
| z_getsubtreesbyindex | orchard 0..3 | ok (= zebra) | ok |
| getaddressbalance |  | ok | ok |
| getaddresstxids | quiet, full range | ok (= zebra) | ok |
| getaddressutxos |  | ok | ok |
| getaddressdeltas | quiet, full range | error -32601 | error -32601 |
| gettxout | unspent output | ok (= zebra) | ok |
