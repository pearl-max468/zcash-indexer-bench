#!/usr/bin/env bash
# Start one system on its already-built index, run both compatibility suites against it with Zebra
# as the reference, then stop it. Results from separate jobs are merged by bench/compare_compat.py.
# usage: ci/compat.sh SYSTEM UPPER FIXTURES OUT
source "$(dirname "${BASH_SOURCE[0]}")/../server/lib.sh"
system=$1 upper=$2 fixtures=$3 out=$4
py="$OPT/venv/bin/python"

"$py" - "$system" "$out" <<'EOF'
import sys, pathlib, time
sys.path.insert(0, "bench")
import common, lw
from lw import pb
system = common.systems()[sys.argv[1]]
out = pathlib.Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
config = system.render_config(out)
unit = common.Unit(f"zbench-compat-{system.name}", system.command(str(config)), env={"RUST_LOG": "warn"})
unit.start()
deadline = time.time() + 3600
while time.time() < deadline:
    try:
        lw.connect(f"http://{system.grpc}", ready_timeout=2).GetLightdInfo(pb.Empty(), timeout=5)
        break
    except Exception:
        time.sleep(5)
else:
    sys.exit(f"{system.name} did not start serving")
EOF

if [[ $system == zaino-* ]]; then
    jsonrpc="http://$ZAINO_JSONRPC"
else
    jsonrpc="http://127.0.0.1:8242,cookie=$DATA/zakura-cookie/.cookie"
fi
grpc=$([[ $system == zaino-* ]] && echo "$ZAINO_GRPC" || echo "$ZTREAMER_GRPC")

status=0
"$py" bench/compat_grpc.py --server "$system=http://$grpc" \
    --zebra-rpc "http://$ZEBRA_RPC" --zebra-cookie "$DATA/zebra-cookie/.cookie" \
    --fixtures "$fixtures" --upper "$upper" --out "$out/grpc" || status=1
"$py" bench/compat_jsonrpc.py --server "$system=$jsonrpc" \
    --reference "zebra=http://$ZEBRA_RPC,cookie=$DATA/zebra-cookie/.cookie" \
    --fixtures "$fixtures" --height "$upper" --out "$out/jsonrpc" || status=1
journalctl -u "zbench-compat-$system" --no-pager > "$out/journal.log" || true
systemctl stop "zbench-compat-$system" || true
exit $status
