#!/usr/bin/env bash
# Download, verify and unpack the pinned Zakura archive snapshots for Ztreamer's embedded node.
# usage: 11-zakura-snapshots.sh [v28|v29|all]   (default: all, v28 first)
#   v28 -> $DATA/zakura-v28  (Ztreamer v0.1.0)
#   v29 -> $DATA/zakura-v29  (Ztreamer master)
# Each unpacked directory is a Zakura cache_dir. Keep them apart: Zakura 1.5.1 (Ztreamer master)
# migrates a v28 state to v29 in place, after which Ztreamer v0.1.0 can no longer open it.
source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"
require_root

fetch() {
    local tag=$1 file=$2 sha=$3
    local dest="$DATA/zakura-$tag" downloads="$DATA/downloads"
    if [[ -f $dest/.zbench-complete ]]; then
        log "$dest already unpacked from $(cut -d' ' -f3 "$dest/.zbench-complete")"
        return
    fi
    mkdir -p "$downloads"
    local tarball="$downloads/$file"
    local need=$(( 600 * 1024 * 1024 * 1024 ))
    local free=$(( $(df --output=avail -B1 "$DATA" | tail -1) ))
    (( free > need )) || die "need ~600 GiB free in $DATA for $file (tarball + unpacked); have $((free >> 30)) GiB"

    if ! echo "$sha  $tarball" | sha256sum -c --status 2>/dev/null; then
        log "downloading $file"
        local url
        for url in "$SNAP_BASE_URL/$file" "$SNAP_BASE_URL/historical/$file"; do
            if aria2c -x16 -s16 -k64M --file-allocation=none --auto-file-renaming=false \
                --allow-overwrite=true --console-log-level=warn --summary-interval=60 \
                --checksum="sha-256=$sha" -d "$downloads" -o "$file" "$url"; then
                break
            fi
        done
    fi
    echo "$sha  $tarball" | sha256sum -c - || die "checksum mismatch for $file"

    log "unpacking $file into $dest"
    rm -rf "$dest"
    mkdir -p "$dest"
    pv -f -i 30 "$tarball" | zstd -dc --long=31 | tar -x -C "$dest"
    printf '%s  %s  %s\n' "$sha" "$(date -u +%FT%TZ)" "$file" > "$dest/.zbench-complete"
    du -sb "$dest" | awk '{print "unpacked_bytes=" $1}' >> "$dest/.zbench-complete"
    rm -f "$tarball"
    log "done: $dest ($(du -sh "$dest" | cut -f1))"
}

case ${1:-all} in
    v28) fetch v28 "$SNAP_V28_FILE" "$SNAP_V28_SHA256" ;;
    v29) fetch v29 "$SNAP_V29_FILE" "$SNAP_V29_SHA256" ;;
    all) fetch v28 "$SNAP_V28_FILE" "$SNAP_V28_SHA256"
         fetch v29 "$SNAP_V29_FILE" "$SNAP_V29_SHA256" ;;
    *) die "usage: $0 [v28|v29|all]" ;;
esac
