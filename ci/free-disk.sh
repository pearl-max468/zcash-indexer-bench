#!/usr/bin/env bash
# Reclaim disk on a GitHub-hosted Ubuntu runner and choose the data volume.
# Writes DATA=<dir> to $GITHUB_ENV: the volume with the most free space after cleanup. Swap is
# left as the runner provides it, so memory conditions match what any fork of this workflow gets.
set -Eeuo pipefail

echo "::group::disk before cleanup"
df -h / /mnt 2>/dev/null || df -h /
echo "::endgroup::"
sudo rm -rf /usr/share/dotnet /usr/local/lib/android /opt/ghc /usr/local/.ghcup /opt/hostedtoolcache/CodeQL \
    /usr/local/share/boost /usr/share/swift /usr/local/share/powershell /usr/local/julia* /opt/microsoft \
    /opt/google /usr/lib/jvm /usr/local/share/chromium /opt/az 2>/dev/null || true
sudo docker image prune --all --force >/dev/null 2>&1 || true
echo "::group::disk after cleanup"
df -h / /mnt 2>/dev/null || df -h /
echo "::endgroup::"

root_free=$(df --output=avail -B1 / | tail -1)
mnt_free=$(df --output=avail -B1 /mnt 2>/dev/null | tail -1 || echo 0)
if (( mnt_free > root_free )); then data=/mnt/zbench; else data=/zbench; fi
sudo mkdir -p "$data"
echo "data volume: $data (root free $((root_free >> 30)) GiB, /mnt free $((mnt_free >> 30)) GiB)"
[[ -n ${GITHUB_ENV:-} ]] && echo "DATA=$data" >> "$GITHUB_ENV"
