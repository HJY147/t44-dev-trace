"""Build a pinned local SSH config from a user-executed Cloud Assistant report.

No connection, private-key read, instance startup or credential installation.
"""
import argparse
import base64
import datetime
import hashlib
import ipaddress
import json
from pathlib import Path
import struct

HOSTS = {
    'i-bp13uag4r4u9r2hge0mt': ('172.21.182.245', 't44-manual-app'),
    'i-bp13uag4r4u9r2hge0mu': ('172.21.182.244', 't44-manual-load'),
}


def checked_report(report, instance_id, now):
    expected_ip, alias = HOSTS[instance_id]
    if (report.get('kind') != 'T44_TEMPORARY_SSH_RECOVERY'
            or report.get('private_ip') != expected_ip
            or report.get('expected_instance_id_from_known_private_ip') != instance_id
            or report.get('ssh_service_state') != 'active' or report.get('port') != 22):
        raise ValueError('EXPECTED_INSTANCE_REPORT_REQUIRED')
    expiry = datetime.datetime.fromisoformat(report['authorization_expires_utc'].replace('Z', '+00:00'))
    if expiry.utcoffset() != datetime.timedelta(0) or expiry <= now:
        raise ValueError('EXPIRED_OR_NON_UTC_AUTHORIZATION')
    fields = report['host_public_key'].split()
    if len(fields) != 2 or fields[0] != 'ssh-ed25519':
        raise ValueError('ED25519_HOST_KEY_REQUIRED')
    wire = base64.b64decode(fields[1], validate=True)
    expected_prefix = struct.pack('>I', 11) + b'ssh-ed25519' + struct.pack('>I', 32)
    if len(wire) != len(expected_prefix) + 32 or not wire.startswith(expected_prefix):
        raise ValueError('INVALID_HOST_KEY_WIRE_FORMAT')
    fingerprint = 'SHA256:' + base64.b64encode(hashlib.sha256(wire).digest()).decode().rstrip('=')
    if report.get('host_fingerprint') != fingerprint:
        raise ValueError('HOST_FINGERPRINT_MISMATCH')
    return alias, ' '.join(fields), fingerprint


def write_config(report, instance_id, public_ip, identity, output, route='direct', now=None):
    now = now or datetime.datetime.now(datetime.timezone.utc)
    alias, host_key, fingerprint = checked_report(report, instance_id, now)
    address = ipaddress.IPv4Address(public_ip)
    if not address.is_global:
        raise ValueError('ACTUAL_PUBLIC_IPV4_REQUIRED')
    identity = Path(identity).absolute()
    if not identity.is_file() or identity.is_symlink() or identity.stat().st_mode & 0o077:
        raise ValueError('LOCAL_REGULAR_PRIVATE_KEY_WITH_0600_REQUIRED')
    if route not in {'proxy', 'direct'}:
        raise ValueError('KNOWN_ROUTE_REQUIRED')
    if any(c in str(identity) for c in '\r\n"'):
        raise ValueError('UNSAFE_CONFIG_PATH')
    output = Path(output).absolute()
    if output.is_symlink() or any(c in str(output) for c in '\r\n"'):
        raise ValueError('UNSAFE_OUTPUT_PATH')
    output.mkdir(mode=0o700, parents=True, exist_ok=True)
    hosts = output / 'known_hosts'
    config = output / (instance_id + '.sshconfig')
    if hosts.is_symlink() or config.is_symlink():
        raise ValueError('PIN_OUTPUT_SYMLINK_REFUSED')
    existing = hosts.read_text().splitlines() if hosts.exists() else []
    entry = instance_id + ' ' + host_key
    old = [line for line in existing if line.split() and line.split()[0] == instance_id]
    if old and any(line != entry for line in old):
        raise ValueError('HOST_KEY_CHANGED_EXPLICIT_REVIEW_REQUIRED')
    if not old:
        existing.append(entry)
    hosts.write_text('\n'.join(existing) + '\n')
    hosts.chmod(0o600)
    proxy = '  ProxyCommand /usr/bin/nc -X 5 -x 127.0.0.1:7890 %h %p\n' if route == 'proxy' else ''
    config.write_text(
        f'Host {alias}\n  HostName {address}\n  HostKeyAlias {instance_id}\n'
        f'  User root\n  Port 22\n  IdentityFile "{identity}"\n'
        f'  UserKnownHostsFile "{hosts}"\n'
        '  StrictHostKeyChecking yes\n  IdentitiesOnly yes\n  BatchMode yes\n'
        '  ClearAllForwardings yes\n  ConnectTimeout 8\n  ConnectionAttempts 1\n'
        '  ServerAliveInterval 15\n  ServerAliveCountMax 2\n' + proxy)
    config.chmod(0o600)
    return {'status': 'LOCAL_PINNED_CONFIG_ONLY_NOT_CONNECTED', 'alias': alias,
            'config': str(config), 'host_fingerprint': fingerprint, 'route': route}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--instance-id', choices=HOSTS, required=True)
    parser.add_argument('--public-ip', required=True)
    parser.add_argument('--identity', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--route', choices=['proxy', 'direct'], default='direct')
    args = parser.parse_args()
    if args.report.is_symlink() or args.report.stat().st_size > 16384:
        raise ValueError('BOUNDED_TRUSTED_PUBLIC_REPORT_REQUIRED')
    print(json.dumps(write_config(json.loads(args.report.read_text()), args.instance_id,
                                 args.public_ip, args.identity, args.output_dir, args.route)))


if __name__ == '__main__':
    main()
