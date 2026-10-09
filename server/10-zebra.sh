#!/usr/bin/env bash
# Build zebrad at the pinned commit and run it as a systemd service syncing mainnet from genesis.
# This is the longest step (1-3 days), so it starts first.
source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"
require_root

bin="$OPT/bin/zebrad-$ZEBRA_REF"
[[ -x $bin ]] || "$repo_root/server/12-build.sh" zebrad

mkdir -p "$DATA/zebra" "$DATA/zebra-cookie" /etc/zbench
install -m644 "$repo_root/configs/zebrad.toml" /etc/zbench/zebrad.toml

cat > /etc/systemd/system/zebrad.service <<EOF
[Unit]
Description=Zebra $ZEBRA_REF mainnet node (zcash-indexer-bench)
After=network-online.target
Wants=network-online.target

[Service]
ExecStart=$bin -c /etc/zbench/zebrad.toml start
Restart=on-failure
RestartSec=10
KillSignal=SIGINT
TimeoutStopSec=180
LimitNOFILE=1048576

[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload
systemctl enable --now zebrad
sleep 5
systemctl --no-pager --lines=20 status zebrad || die "zebrad failed to start; see journalctl -u zebrad"
log "zebrad is syncing; follow with: journalctl -fu zebrad  or  server/status.sh"
