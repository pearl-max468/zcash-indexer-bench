#!/usr/bin/env bash
# Prepare a fresh Ubuntu 24.04 host: packages, Rust, pinned load tools, data directories,
# CPU governor, and a hardware record. Safe to re-run.
source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"
require_root

export DEBIAN_FRONTEND=noninteractive
log "installing packages"
apt-get update -qq
apt-get install -y -qq --no-install-recommends \
    build-essential clang libclang-dev llvm-dev pkg-config libssl-dev cmake \
    protobuf-compiler libprotobuf-dev git curl ca-certificates jq zstd aria2 pv \
    sysstat python3-venv python3-pip tmux htop iotop-c nvme-cli lshw util-linux \
    cpufrequtils chrony >/dev/null
# perf is optional: Hetzner kernels do not always have a matching linux-tools package.
apt-get install -y -qq "linux-tools-$(uname -r)" linux-tools-common >/dev/null 2>&1 \
    || log "linux-tools for $(uname -r) unavailable; perf profiling disabled"

if ! command -v rustup >/dev/null; then
    log "installing rustup (projects pin their own toolchains via rust-toolchain.toml)"
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs \
        | sh -s -- -y --profile minimal --default-toolchain stable >/dev/null
    source "$HOME/.cargo/env"
fi

mkdir -p "$OPT/bin" "$OPT/src" "$OPT/provenance" "$DATA"
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

if [[ ! -x $OPT/bin/ghz ]]; then
    log "installing ghz $GHZ_VERSION"
    base="https://github.com/bojand/ghz/releases/download/$GHZ_VERSION"
    curl -fsSL -o "$tmp/ghz.tar.gz" "$base/ghz-linux-x86_64.tar.gz"
    curl -fsSL -o "$tmp/ghz.sha256" "$base/ghz-linux-x86_64.tar.gz.sha256"
    echo "$(awk '{print $1}' "$tmp/ghz.sha256")  $tmp/ghz.tar.gz" | sha256sum -c --quiet -
    tar -xzf "$tmp/ghz.tar.gz" -C "$tmp" ghz
    install -m755 "$tmp/ghz" "$OPT/bin/ghz"
fi

if [[ ! -x $OPT/bin/grpcurl ]]; then
    log "installing grpcurl $GRPCURL_VERSION"
    base="https://github.com/fullstorydev/grpcurl/releases/download/v$GRPCURL_VERSION"
    file="grpcurl_${GRPCURL_VERSION}_linux_x86_64.tar.gz"
    curl -fsSL -o "$tmp/$file" "$base/$file"
    if curl -fsSL -o "$tmp/sums.txt" "$base/grpcurl_${GRPCURL_VERSION}_checksums.txt"; then
        (cd "$tmp" && grep " $file\$" sums.txt | sha256sum -c --quiet -)
    else
        log "grpcurl checksum file not published; recording the tarball hash instead"
        sha256sum "$tmp/$file" > "$OPT/provenance/grpcurl-tarball.sha256"
    fi
    tar -xzf "$tmp/$file" -C "$tmp" grpcurl
    install -m755 "$tmp/grpcurl" "$OPT/bin/grpcurl"
fi

if [[ ! -d $OPT/venv ]]; then
    log "creating Python environment for the harness"
    python3 -m venv "$OPT/venv"
fi
"$OPT/venv/bin/pip" install -q --upgrade pip
"$OPT/venv/bin/pip" install -q -r "$repo_root/requirements.txt"

# Fixed CPU frequency policy for every run; the setting is recorded with the hardware.
if command -v cpufreq-set >/dev/null && [[ -d /sys/devices/system/cpu/cpu0/cpufreq ]]; then
    for cpu in /sys/devices/system/cpu/cpu[0-9]*; do
        cpufreq-set -c "${cpu##*cpu}" -g performance 2>/dev/null || true
    done
fi

"$repo_root/server/collect-hardware.sh" > "$OPT/provenance/hardware.json"
log "hardware record: $OPT/provenance/hardware.json"
log "bootstrap complete"
