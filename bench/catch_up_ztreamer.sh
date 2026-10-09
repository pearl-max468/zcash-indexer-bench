#!/usr/bin/env bash
# Bring a Ztreamer build's embedded Zakura state to the chain tip before a measured run, so the
# measurement covers indexing rather than node catch-up (Zaino's Zebra is likewise at the tip).
# Runs ztreamerd against a scratch index until it logs that Zakura is near the tip, then stops.
# usage: bench/catch_up_ztreamer.sh ztreamer-v0.1.0|ztreamer-master
source "$(dirname "${BASH_SOURCE[0]}")/../server/lib.sh"
require_root

case ${1:-} in
    "ztreamer-$ZTREAMER_RELEASE_REF") ref=$ZTREAMER_RELEASE_REF; snap=v28 ;;
    "ztreamer-$ZTREAMER_HEAD_REF")    ref=$ZTREAMER_HEAD_REF;    snap=v29 ;;
    *) die "usage: $0 ztreamer-$ZTREAMER_RELEASE_REF|ztreamer-$ZTREAMER_HEAD_REF" ;;
esac
state="$DATA/zakura-$snap"
[[ -f $state/.zbench-complete ]] || die "snapshot $snap not unpacked; run server/11-zakura-snapshots.sh $snap"

scratch="$DATA/index/catchup-$ref"
rm -rf "$scratch"
mkdir -p "$scratch" "$DATA/zakura-cookie"
config=$(mktemp --suffix=.toml)
sed -e "s|@ZAKURA_STATE@|$state|g" -e "s|@DATA@|$DATA|g" "$repo_root/configs/zakura-ztreamer.toml.in" > "$config"

unit="zbench-catchup-$ref"
since=$(date +%s)
systemd-run --unit="$unit" --collect --quiet --setenv=RUST_LOG=info -- \
    "$OPT/bin/ztreamerd-$ref" --zakura-config "$config" --index-dir "$scratch" \
    --grpc-listen 127.0.0.1:19067 --metrics-listen 127.0.0.1:19999
trap 'systemctl stop "$unit" 2>/dev/null || true; rm -rf "$scratch" "$config"' EXIT

log "waiting for embedded Zakura to reach the tip (follow: journalctl -fu $unit)"
until journalctl -u "$unit" --since "@$since" -o cat | grep -q "Zakura is near the chain tip"; do
    systemctl is-active --quiet "$unit" || die "ztreamerd exited; see journalctl -u $unit"
    sleep 15
done
journalctl -u "$unit" --since "@$since" -o cat | grep -m1 "Zakura is near the chain tip"
systemctl stop "$unit"
date -u +%FT%TZ > "$state/.zbench-caught-up"
log "caught up: $state (marker valid for 30 minutes; re-run before each measured run)"
