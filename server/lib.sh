# Shared helpers, sourced by every server/ script.
set -Eeuo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
# shellcheck source=../versions.env
source "$repo_root/versions.env"
[[ -f $HOME/.cargo/env ]] && source "$HOME/.cargo/env"
export PATH="$OPT/bin:$PATH"

log() { printf '[%s] %s\n' "$(date -u +%H:%M:%S)" "$*" >&2; }
die() { log "error: $*"; exit 1; }

require_root() { [[ $EUID -eq 0 ]] || die "run as root"; }

# checkout_pinned NAME URL COMMIT -> prints the source directory, checked out at exactly COMMIT.
checkout_pinned() {
    local name=$1 url=$2 commit=$3 src="$OPT/src/$1"
    if [[ ! -d $src/.git ]]; then
        git clone --quiet --filter=blob:none "$url" "$src" >&2
    fi
    git -C "$src" cat-file -e "$commit^{commit}" 2>/dev/null || git -C "$src" fetch --quiet --tags origin >&2
    git -C "$src" checkout --quiet --detach "$commit" >&2
    [[ $(git -C "$src" rev-parse HEAD) == "$commit" ]] || die "$name is not at $commit"
    [[ -z $(git -C "$src" status --porcelain) ]] || die "$name checkout has local changes"
    printf '%s\n' "$src"
}

# record_build NAME SRC BINARY BUILD_COMMAND...: write provenance JSON for a built binary.
record_build() {
    local name=$1 src=$2 bin=$3; shift 3
    mkdir -p "$OPT/provenance"
    python3 - "$name" "$src" "$bin" "$*" > "$OPT/provenance/$name.json" <<'EOF'
import hashlib, json, subprocess, sys, datetime
name, src, binary, command = sys.argv[1:]
def run(*args):
    return subprocess.run(args, cwd=src, capture_output=True, text=True).stdout.strip()
with open(binary, "rb") as f:
    digest = hashlib.sha256(f.read()).hexdigest()
json.dump({
    "name": name,
    "remote": run("git", "remote", "get-url", "origin"),
    "commit": run("git", "rev-parse", "HEAD"),
    "describe": run("git", "describe", "--tags", "--always"),
    "dirty_files": len([l for l in run("git", "status", "--porcelain").splitlines() if l]),
    "rustc": run("rustc", "-vV"),
    "cargo": run("cargo", "-V"),
    "build_command": command,
    "binary": binary,
    "binary_sha256": digest,
    "recorded_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
}, sys.stdout, indent=2)
print()
EOF
    log "provenance: $OPT/provenance/$name.json"
}

# zebra_rpc METHOD [PARAMS_JSON]: call Zebra's cookie-authenticated JSON-RPC.
zebra_rpc() {
    local method=$1 params=${2:-[]}
    curl -fsS --max-time 10 --user "$(<"$DATA/zebra-cookie/.cookie")" \
        -H 'content-type: application/json' \
        --data-binary "{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"$method\",\"params\":$params}" \
        "http://$ZEBRA_RPC"
}
