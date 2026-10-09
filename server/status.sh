#!/usr/bin/env bash
# One-screen status: Zebra sync progress, services, snapshot state and disk usage.
source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

echo "== zebrad"
if systemctl is-active --quiet zebrad 2>/dev/null; then
    if info=$(zebra_rpc getblockchaininfo 2>/dev/null); then
        jq -r '.result | "height \(.blocks) / estimated \(.estimatedheight // "?")  (\(if .estimatedheight then (100 * .blocks / .estimatedheight | floor) else "?" end)%)  verificationprogress \(.verificationprogress // "?")"' <<< "$info"
    else
        echo "running; RPC not answering yet (cookie appears once RPC starts)"
    fi
    zebra_peers=$(zebra_rpc getpeerinfo 2>/dev/null | jq '.result | length' 2>/dev/null || echo "?")
    echo "peers: $zebra_peers"
else
    echo "not running"
fi

echo "== services"
for unit in zebrad zainod ztreamerd; do
    printf '%-10s %s\n' "$unit" "$(systemctl is-active "$unit" 2>/dev/null || true)"
done

echo "== snapshots"
for tag in v28 v29; do
    marker="$DATA/zakura-$tag/.zbench-complete"
    if [[ -f $marker ]]; then echo "$tag: unpacked ($(head -1 "$marker" | cut -d' ' -f3-))"
    elif compgen -G "$DATA/downloads/*.aria2" >/dev/null; then echo "$tag: download in progress"
    else echo "$tag: not present"; fi
done

echo "== disk ($DATA)"
df -h "$DATA" | tail -1
du -sh "$DATA"/* 2>/dev/null | sort -h
