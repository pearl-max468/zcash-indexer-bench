#!/usr/bin/env bash
# Build every indexer under test at its pinned commit, with each project's lockfile and toolchain.
# Binaries land in $OPT/bin/<name>; provenance (commit, rustc, SHA-256) in $OPT/provenance/.
source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"
require_root

build_zaino() {
    local ref=$1 commit=$2 name="zainod-$1"
    local src
    src=$(checkout_pinned "zaino-$ref" https://github.com/zingolabs/zaino "$commit")
    local build=(cargo build --locked --release -p zainod --bin zainod --features "$ZAINO_FEATURES")
    log "building $name: ${build[*]}"
    (cd "$src" && "${build[@]}")
    install -m755 "$src/target/release/zainod" "$OPT/bin/$name"
    record_build "$name" "$src" "$OPT/bin/$name" "${build[@]}"
}

build_ztreamer() {
    local ref=$1 commit=$2 name="ztreamerd-$1"
    local src
    src=$(checkout_pinned "ztreamer-$ref" https://github.com/distractedm1nd/ztreamer "$commit")
    local build=(cargo build --locked --release -p ztreamerd --bin ztreamerd)
    log "building $name: ${build[*]}"
    (cd "$src" && "${build[@]}")
    install -m755 "$src/target/release/ztreamerd" "$OPT/bin/$name"
    record_build "$name" "$src" "$OPT/bin/$name" "${build[@]}"
}

# Ztreamer's own serving client, used only as a cross-check of the independent ghz results.
build_ztreamer_client() {
    local src="$OPT/src/ztreamer-$ZTREAMER_HEAD_REF"
    local build=(cargo build --locked --release -p ztreamer-service --example serving-suite)
    log "building Ztreamer serving-suite client: ${build[*]}"
    (cd "$src" && "${build[@]}")
    install -m755 "$src/target/release/examples/serving-suite" "$OPT/bin/ztreamer-serving-suite"
    record_build ztreamer-serving-suite "$src" "$OPT/bin/ztreamer-serving-suite" "${build[@]}"
}

targets=${*:-zaino-stable zaino-repro ztreamer-release ztreamer-head ztreamer-client}
for target in $targets; do
    case $target in
        zaino-stable)     build_zaino "$ZAINO_STABLE_REF" "$ZAINO_STABLE_COMMIT" ;;
        zaino-repro)      build_zaino "$ZAINO_REPRO_REF" "$ZAINO_REPRO_COMMIT" ;;
        ztreamer-release) build_ztreamer "$ZTREAMER_RELEASE_REF" "$ZTREAMER_RELEASE_COMMIT" ;;
        ztreamer-head)    build_ztreamer "$ZTREAMER_HEAD_REF" "$ZTREAMER_HEAD_COMMIT" ;;
        ztreamer-client)  build_ztreamer_client ;;
        *) die "unknown target $target" ;;
    esac
done
log "built: $(ls "$OPT/bin" | tr '\n' ' ')"
