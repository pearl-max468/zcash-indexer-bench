#!/usr/bin/env bash
# Give a Ztreamer build its own copy of the frozen Zebra snapshot as its embedded Zakura state.
# Zakura is a Zebra fork: the v0.1.0 fork reads format 28.x, and Zakura 1.5.1 (Ztreamer master)
# migrates a v28 state to v29 on open. Whether each one accepts Zebra's state is itself recorded.
# usage: ci/zakura-state.sh ztreamer-v0.1.0|ztreamer-master
source "$(dirname "${BASH_SOURCE[0]}")/../server/lib.sh"

case ${1:-} in
    "ztreamer-$ZTREAMER_RELEASE_REF") dest="$DATA/zakura-v28" ;;
    "ztreamer-$ZTREAMER_HEAD_REF")    dest="$DATA/zakura-v29" ;;
    *) die "usage: $0 ztreamer-$ZTREAMER_RELEASE_REF|ztreamer-$ZTREAMER_HEAD_REF" ;;
esac
started=$SECONDS
sudo rm -rf "$dest"
sudo mkdir -p "$dest" "$DATA/zakura-cookie"
sudo cp -a "$DATA/zebra/state" "$dest/state"
log "copied frozen state to $dest in $((SECONDS - started)) s"
sudo du -sh "$dest"
df -h "$DATA"
