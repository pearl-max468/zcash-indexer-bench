#!/usr/bin/env bash
# Print a JSON record of the host: CPU, memory, storage under $DATA, OS, kernel and tuning knobs.
# Run before and after each benchmark session so settings during measurement are on record.
source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

python3 - "$DATA" <<'EOF'
import json, os, platform, subprocess, sys, datetime

data_dir = sys.argv[1]

def cmd(*args):
    try:
        return subprocess.run(args, capture_output=True, text=True, timeout=30).stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        return ""

def as_json(*args):
    out = cmd(*args)
    try:
        return json.loads(out) if out else None
    except json.JSONDecodeError:
        return out

def read(path):
    try:
        with open(path) as f:
            return f.read().strip()
    except OSError:
        return None

meminfo = {}
for line in (read("/proc/meminfo") or "").splitlines():
    key, _, value = line.partition(":")
    meminfo[key] = value.strip()

governors = sorted({read(f"/sys/devices/system/cpu/{c}/cpufreq/scaling_governor")
                    for c in os.listdir("/sys/devices/system/cpu") if c[3:].isdigit()} - {None})

json.dump({
    "collected_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "hostname": platform.node(),
    "cpu": as_json("lscpu", "-J"),
    "memory": {k: meminfo.get(k) for k in ("MemTotal", "SwapTotal", "HugePages_Total")},
    "storage": {
        "data_mount": as_json("findmnt", "-J", "-T", data_dir),
        "block_devices": as_json("lsblk", "-J", "-b", "-o", "NAME,MODEL,SIZE,ROTA,TYPE,FSTYPE,MOUNTPOINTS"),
        "raid": read("/proc/mdstat"),
        "nvme": as_json("nvme", "list", "-o", "json"),
        "free_bytes": os.statvfs(data_dir).f_bavail * os.statvfs(data_dir).f_frsize if os.path.isdir(data_dir) else None,
    },
    "os": read("/etc/os-release"),
    "kernel": platform.uname()._asdict(),
    "tuning": {
        "cpu_governors": governors,
        "transparent_hugepage": read("/sys/kernel/mm/transparent_hugepage/enabled"),
        "swappiness": read("/proc/sys/vm/swappiness"),
        "cpu_mitigations": read("/sys/devices/system/cpu/vulnerabilities/spectre_v2"),
        "smt": read("/sys/devices/system/cpu/smt/control"),
    },
}, sys.stdout, indent=2)
print()
EOF
