#!/usr/bin/env bash
# Read-only inventory. Cloud Assistant captures stdout privately; do not publish raw network identity.
set -euo pipefail
readonly NODE_ROLE="${1:-${T44_NODE_ROLE:-}}"
case "$NODE_ROLE" in app|load) ;; *) printf '%s\n' 'Set T44_NODE_ROLE=app or load, or pass that one argument.' >&2; exit 2 ;; esac
command -v python3 >/dev/null || { printf '%s\n' 'python3 is required for this read-only probe.' >&2; exit 2; }
python3 - "$NODE_ROLE" <<'T44_READ_ONLY_PROBE'
import datetime
import json
import os
import platform
import re
import resource
import shutil
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import urlsplit


def command(argv, limit=5):
    if not shutil.which(argv[0]):
        return {"available": False}
    try:
        result = subprocess.run(argv, capture_output=True, text=True, timeout=limit, check=False)
        return {"available": True, "exit_code": result.returncode,
                "stdout": result.stdout[:4096].strip(), "stderr": result.stderr[:512].strip(),
                "stdout_truncated": len(result.stdout) > 4096, "stderr_truncated": len(result.stderr) > 512}
    except subprocess.TimeoutExpired:
        return {"available": True, "timed_out": True}


def text(path):
    try:
        return Path(path).read_text()
    except (OSError, UnicodeError):
        return None


def emit(kind, **fields):
    print(json.dumps({"kind": kind, "role": sys.argv[1],
                      "utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                      "monotonic_ns": time.monotonic_ns(), **fields}), flush=True)


os_release = {}
for line in (text("/etc/os-release") or "").splitlines():
    if "=" in line:
        key, value = line.split("=", 1)
        os_release[key] = value.strip('"')
memory = {}
for line in (text("/proc/meminfo") or "").splitlines():
    key, value = line.split(":", 1)
    if key in {"MemTotal", "MemAvailable", "SwapTotal", "SwapFree"}:
        memory[key + "_bytes"] = int(value.split()[0]) * 1024
emit("host", uname=list(platform.uname()), os_release=os_release, uid=os.getuid(),
     logical_cpu=os.cpu_count(), affinity_cpu=len(os.sched_getaffinity(0)),
     memory=memory, fd_limit=list(resource.getrlimit(resource.RLIMIT_NOFILE)),
     cgroup_cpu_max=text("/sys/fs/cgroup/cpu.max"),
     cgroup_memory_max=text("/sys/fs/cgroup/memory.max"))
emit("disk_clock", disk=command(["df", "-B1", "-P", "/", "/var/lib"]),
     clock=command(["timedatectl", "show", "-p", "NTPSynchronized", "-p", "Timezone", "-p", "TimeUSec"]),
     file_nr=text("/proc/sys/fs/file-nr"))
versions = {name: command(argv) for name, argv in {
    "python3": ["python3", "--version"], "git": ["git", "--version"],
    "docker": ["docker", "--version"], "compose": ["docker", "compose", "version", "--short"],
    "openssl": ["openssl", "version"], "curl": ["curl", "--version"],
}.items()}
emit("software", versions=versions,
     ubuntu_packages=command(["dpkg-query", "-W", "-f=${Package}\t${Version}\t${db:Status-Status}\n",
                              "docker.io", "docker.io-app", "docker-compose-v2", "docker-buildx",
                              "containerd", "runc", "ca-certificates", "ufw", "unattended-upgrades"]),
     docker_daemon=command(["systemctl", "is-active", "docker.service"]))
emit("cloud_assistant", units={unit: command(["systemctl", "is-active", unit]) for unit in
                               ["aliyun.service", "aliyun-assist.service", "AliYunDun.service"]},
     installed_paths={p: Path(p).is_dir() for p in ["/usr/local/share/aliyun-assist", "/usr/local/aegis"]},
     security_services={unit: command(["systemctl", "is-active", unit]) for unit in
                        ["ssh.service", "ufw.service", "unattended-upgrades.service"]})
sources = [Path("/etc/apt/sources.list"), *Path("/etc/apt/sources.list.d").glob("*.list"),
           *Path("/etc/apt/sources.list.d").glob("*.sources")]
source_hosts = set()
for path in sources:
    for match in re.findall(r"https?://[^\s]+", text(path) or ""):
        source_hosts.add(urlsplit(match).hostname)
emit("network", apt_source_hosts=sorted(h for h in source_hosts if h),
     routes=command(["ip", "-j", "route", "show"]),
     addresses=command(["ip", "-j", "address", "show"]),
     listening_tcp=command(["ss", "-H", "-lnt"]),
     default_route_dns_hosts={host: command(["getent", "ahostsv4", host]) for host in
                              ["archive.ubuntu.com", "security.ubuntu.com", "registry-1.docker.io", "github.com"]})
emit("probe_complete", success=True, mutation_performed=False,
     uploads_or_software_installs_performed=False, credentials_or_process_environment_dumped=False,
     raw_receipt_is_private=True)
T44_READ_ONLY_PROBE
