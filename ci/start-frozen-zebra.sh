#!/usr/bin/env bash
# Frozen Zebra from the pinned Zcash Foundation snapshot.
#   ci/start-frozen-zebra.sh unpack   download, verify while streaming, unpack into $DATA/zebra
#   ci/start-frozen-zebra.sh start    start zebrad as the systemd unit `zebrad`, frozen at the snapshot tip
# Unpack and start are separate so other state copies (ci/zakura-state.sh) are taken from the
# pristine snapshot before Zebra opens it; a running RocksDB compacts and deletes files.
source "$(dirname "${BASH_SOURCE[0]}")/../server/lib.sh"

unpack() {
    local url=$ZF_TESTNET_URL sha=$ZF_TESTNET_SHA256
    sudo mkdir -p "$DATA/zebra" "$DATA/zebra-cookie"
    if [[ -d $DATA/zebra/state ]]; then
        log "snapshot already unpacked"
        return
    fi
    log "downloading and unpacking $(basename "$url")"
    local started=$SECONDS sumfile
    sumfile=$(mktemp)
    curl -fsSL --retry 5 --retry-delay 10 "$url" \
        | tee >(sha256sum | awk '{print $1}' > "$sumfile") \
        | zstd -dc --long=31 | sudo tar -x -C "$DATA/zebra"
    sleep 2
    local got
    got=$(cat "$sumfile")
    [[ $got == "$sha" ]] || die "snapshot checksum mismatch: got $got, expected $sha"
    log "snapshot verified ($sha) and unpacked in $((SECONDS - started)) s"
    sudo du -sh "$DATA/zebra/state"/*/* | sed 's/^/state: /'
}

start() {
    local config
    config=$(mktemp --suffix=.toml)
    "$OPT/venv/bin/python" - "$config" <<EOF
import sys, pathlib
sys.path.insert(0, "$repo_root/bench")
import common
common.render("zebrad-frozen.toml.in", pathlib.Path(sys.argv[1]))
EOF
    sudo install -D -m644 "$config" /etc/zbench/zebrad.toml
    cat /etc/zbench/zebrad.toml

    sudo systemd-run --unit=zebrad --collect --quiet \
        --property=CPUAccounting=yes --property=MemoryAccounting=yes --property=IOAccounting=yes \
        --property=LimitNOFILE=1048576 --property=KillSignal=SIGINT --property=TimeoutStopSec=180 \
        -- "$OPT/bin/zebrad-$ZEBRA_REF" -c /etc/zbench/zebrad.toml start

    local info
    for _ in $(seq 1 180); do
        if sudo test -s "$DATA/zebra-cookie/.cookie" && info=$(sudo -E bash -c "source $repo_root/server/lib.sh; zebra_rpc getblockchaininfo" 2>/dev/null); then
            jq -c '.result | {chain, blocks, bestblockhash}' <<< "$info"
            return
        fi
        systemctl is-active --quiet zebrad || { sudo journalctl -u zebrad --no-pager | tail -50; die "zebrad exited"; }
        sleep 5
    done
    sudo journalctl -u zebrad --no-pager | tail -50
    die "zebrad RPC did not come up"
}

case ${1:-} in
    unpack) unpack ;;
    start)  start ;;
    *) die "usage: $0 unpack|start" ;;
esac
