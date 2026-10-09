#!/usr/bin/env bash
# Runtime tools for benchmark jobs: zstd, ghz (checksum-verified), the Python harness environment.
# Expects downloaded binaries already in $OPT/bin.
source "$(dirname "${BASH_SOURCE[0]}")/../server/lib.sh"

sudo apt-get update -qq
sudo apt-get install -y -qq --no-install-recommends zstd jq sysstat util-linux python3-venv >/dev/null
sudo mkdir -p "$OPT/bin" "$OPT/provenance"
sudo chown -R "$(id -u):$(id -g)" "$OPT"
chmod +x "$OPT"/bin/* 2>/dev/null || true

if [[ ! -x $OPT/bin/ghz ]]; then
    tmp=$(mktemp -d)
    base="https://github.com/bojand/ghz/releases/download/$GHZ_VERSION"
    curl -fsSL -o "$tmp/ghz.tar.gz" "$base/ghz-linux-x86_64.tar.gz"
    curl -fsSL -o "$tmp/ghz.sha256" "$base/ghz-linux-x86_64.tar.gz.sha256"
    echo "$(awk '{print $1}' "$tmp/ghz.sha256")  $tmp/ghz.tar.gz" | sha256sum -c --quiet -
    tar -xzf "$tmp/ghz.tar.gz" -C "$tmp" ghz
    install -m755 "$tmp/ghz" "$OPT/bin/ghz"
fi

python3 -m venv "$OPT/venv"
"$OPT/venv/bin/pip" install -q --upgrade pip
"$OPT/venv/bin/pip" install -q -r "$repo_root/requirements.txt"
"$OPT/venv/bin/python" -c "import sys; sys.path.insert(0, '$repo_root/bench'); import lw"  # generate stubs once
ls -la "$OPT/bin"
