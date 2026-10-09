#!/usr/bin/env bash
# Build binaries under test at their pinned commits, with each project's lockfile and toolchain.
# Binaries land in $OPT/bin/<name>; provenance (commit, rustc, SHA-256) in $OPT/provenance/.
# usage: 12-build.sh [zebrad zaino-stable zaino-repro ztreamer-release ztreamer-head ztreamer-client]
# Needs no root: set OPT to any writable directory (CI does).
source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"
mkdir -p "$OPT/bin" "$OPT/src" "$OPT/provenance"

build() {
    local name=$1 url=$2 commit=$3 artifact=$4; shift 4
    local src
    src=$(checkout_pinned "$name" "$url" "$commit")
    # Install the toolchain a project pins (newer rustup no longer installs it implicitly).
    if [[ -f $src/rust-toolchain.toml ]]; then
        local channel
        channel=$(sed -n 's/^channel *= *"\(.*\)"/\1/p' "$src/rust-toolchain.toml")
        [[ -n $channel ]] && rustup toolchain install "$channel" --profile minimal >&2
    fi
    local cmd=(cargo build --locked --release "$@")
    log "building $artifact: ${cmd[*]}"
    (cd "$src" && "${cmd[@]}") >&2
    printf '%s\n' "$src"
}

build_zebrad() {
    local src
    src=$(build "zebra-$ZEBRA_REF" https://github.com/ZcashFoundation/zebra "$ZEBRA_COMMIT" zebrad \
        -p zebrad --bin zebrad --features "$ZEBRA_FEATURES")
    install -m755 "$src/target/release/zebrad" "$OPT/bin/zebrad-$ZEBRA_REF"
    record_build "zebrad-$ZEBRA_REF" "$src" "$OPT/bin/zebrad-$ZEBRA_REF" \
        cargo build --locked --release -p zebrad --bin zebrad --features "$ZEBRA_FEATURES"
}

build_zaino() {
    local ref=$1 commit=$2 src
    src=$(build "zaino-$ref" https://github.com/zingolabs/zaino "$commit" "zainod-$ref" \
        -p zainod --bin zainod --features "$ZAINO_FEATURES")
    install -m755 "$src/target/release/zainod" "$OPT/bin/zainod-$ref"
    record_build "zainod-$ref" "$src" "$OPT/bin/zainod-$ref" \
        cargo build --locked --release -p zainod --bin zainod --features "$ZAINO_FEATURES"
}

build_ztreamer() {
    local ref=$1 commit=$2 src
    src=$(build "ztreamer-$ref" https://github.com/distractedm1nd/ztreamer "$commit" "ztreamerd-$ref" \
        -p ztreamerd --bin ztreamerd)
    install -m755 "$src/target/release/ztreamerd" "$OPT/bin/ztreamerd-$ref"
    record_build "ztreamerd-$ref" "$src" "$OPT/bin/ztreamerd-$ref" \
        cargo build --locked --release -p ztreamerd --bin ztreamerd
}

# Ztreamer's own serving client, used only as a cross-check of the independent ghz results.
build_ztreamer_client() {
    local src
    src=$(build "ztreamer-$ZTREAMER_HEAD_REF" https://github.com/distractedm1nd/ztreamer "$ZTREAMER_HEAD_COMMIT" \
        ztreamer-serving-suite -p ztreamer-service --example serving-suite)
    install -m755 "$src/target/release/examples/serving-suite" "$OPT/bin/ztreamer-serving-suite"
    record_build ztreamer-serving-suite "$src" "$OPT/bin/ztreamer-serving-suite" \
        cargo build --locked --release -p ztreamer-service --example serving-suite
}

targets=${*:-zebrad zaino-stable zaino-repro ztreamer-release ztreamer-head ztreamer-client}
for target in $targets; do
    case $target in
        zebrad)           build_zebrad ;;
        zaino-stable)     build_zaino "$ZAINO_STABLE_REF" "$ZAINO_STABLE_COMMIT" ;;
        zaino-repro)      build_zaino "$ZAINO_REPRO_REF" "$ZAINO_REPRO_COMMIT" ;;
        ztreamer-release) build_ztreamer "$ZTREAMER_RELEASE_REF" "$ZTREAMER_RELEASE_COMMIT" ;;
        ztreamer-head)    build_ztreamer "$ZTREAMER_HEAD_REF" "$ZTREAMER_HEAD_COMMIT" ;;
        ztreamer-client)  build_ztreamer_client ;;
        *) die "unknown target $target" ;;
    esac
done
log "built: $(ls "$OPT/bin" | tr '\n' ' ')"
