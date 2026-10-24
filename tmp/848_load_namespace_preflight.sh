#!/usr/bin/env bash
# Neutral load-host preparation only; no application or private test execution.
set -euo pipefail
umask 077
test "$(id -u)" = 0
: "${T44_EXPECTED_INSTANCE_ID:?Explicit load instance identity is required}"
test "$(cat /var/lib/cloud/data/instance-id)" = "$T44_EXPECTED_INSTANCE_ID"
test "$(date -u +%s)" -lt "$(date -u -d 2026-10-24T08:40:00Z +%s)"
install -d -m 0700 /run/t44-relay852
python3.12 -I - <<'PY'
import json
import platform
import resource
import ssl

assert platform.system() == 'Linux' and platform.machine() == 'x86_64'
print(json.dumps({'python': platform.python_version(),
                  'cpu_architecture': platform.machine(),
                  'file_descriptor_limits': resource.getrlimit(resource.RLIMIT_NOFILE),
                  'ca_store_nonempty': ssl.create_default_context().cert_store_stats()['x509_ca'] > 0}))
PY
openssl version
unshare --net -- python3.12 -I - <<'PY'
import fcntl
import json
import os
import socket
import struct
from pathlib import Path

isolated = os.readlink('/proc/self/ns/net') != os.readlink('/proc/1/ns/net')
interfaces = sorted(path.name for path in Path('/sys/class/net').iterdir())
with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as probe:
    flags = struct.unpack('16sH14x', fcntl.ioctl(probe, 0x8913, struct.pack('16sH14x', b'lo', 0)))[1]
loopback_up = bool(flags & 1)
assert isolated and interfaces == ['lo'] and not loopback_up
print(json.dumps({'network_namespace_isolated': isolated,
                  'interfaces': interfaces, 'loopback_up': loopback_up,
                  'application_requests': 0}))
PY
printf 'T44_LOAD_NAMESPACE_PREFLIGHT_OK\n'
