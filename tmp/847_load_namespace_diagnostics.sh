#!/usr/bin/env bash
# Inspect this temporary network namespace, never contact an application endpoint.
set -euo pipefail
umask 077
test "$(id -u)" = 0
: "${T44_EXPECTED_INSTANCE_ID:?Explicit load instance identity is required}"
test "$(cat /var/lib/cloud/data/instance-id)" = "$T44_EXPECTED_INSTANCE_ID"
unshare --net -- python3.12 -I - <<'PY'
import fcntl
import json
import os
import socket
import struct
from pathlib import Path

isolated = os.readlink('/proc/self/ns/net') != os.readlink('/proc/1/ns/net')
sysfs_names = sorted(path.name for path in Path('/sys/class/net').iterdir())
proc_names = sorted(line.split(':', 1)[0].strip()
                    for line in Path('/proc/net/dev').read_text().splitlines() if ':' in line)
with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as probe:
    flags = struct.unpack('16sH14x', fcntl.ioctl(probe, 0x8913, struct.pack('16sH14x', b'lo', 0)))[1]
loopback_up = bool(flags & 1)
print(json.dumps({'network_namespace_isolated': isolated,
                  'sysfs_interface_names': sysfs_names,
                  'current_namespace_proc_interface_names': proc_names,
                  'loopback_up': loopback_up, 'application_requests': 0}), flush=True)
assert isolated and proc_names == ['lo'] and not loopback_up
PY
printf 'T44_LOAD_NAMESPACE_DIAGNOSTIC_OK\n'
