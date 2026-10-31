"""Prepare fresh SSH configs using new user-observed IPs and previously trusted pins.

Pure local preparation: no server contact or credential installation. Does not
establish whether the persistent authorization has been installed on the server.
"""
import argparse
import base64
import hashlib
import ipaddress
import json
import os
from pathlib import Path
import stat
import struct

HOSTS = {
    'i-bp13uag4r4u9r2hge0mt': 't44-manual-app',
    'i-bp13uag4r4u9r2hge0mu': 't44-manual-load',
}


def require(value, code):
    if not value:
        raise ValueError(code)


def safe_path(value):
    path = Path(value).absolute()
    require(not any(c in str(path) for c in '\r\n"'), 'UNSAFE_CONFIG_PATH')
    require(path.resolve() == path, 'CANONICAL_PATH_REQUIRED')
    return path


def trusted_pins(path):
    path = safe_path(path)
    require(path.is_file() and not path.is_symlink() and path.stat().st_size <= 16384,
            'BOUNDED_ORIGINAL_KNOWN_HOSTS_REQUIRED')
    result = {}
    for line in path.read_text().splitlines():
        if not line.strip() or line.lstrip().startswith('#'):
            continue
        fields = line.split()
        require(len(fields) == 3 and fields[0] in HOSTS and fields[1] == 'ssh-ed25519',
                'EXACT_ORIGINAL_INSTANCE_PINS_REQUIRED')
        instance, algorithm, encoded = fields
        require(instance not in result, 'DUPLICATE_PIN_REFUSED')
        wire = base64.b64decode(encoded, validate=True)
        prefix = struct.pack('>I', 11) + b'ssh-ed25519' + struct.pack('>I', 32)
        require(len(wire) == len(prefix) + 32 and wire.startswith(prefix), 'INVALID_ED25519_WIRE')
        result[instance] = algorithm + ' ' + encoded
    require(set(result) == set(HOSTS), 'BOTH_ORIGINAL_INSTANCE_PINS_REQUIRED')
    return path, result


def prepare(known_hosts, identity, app_ip, load_ip, output):
    original, pins = trusted_pins(known_hosts)
    identity = safe_path(identity)
    require(identity.is_file() and not identity.is_symlink() and
            stat.S_ISREG(identity.stat().st_mode) and identity.stat().st_mode & 0o077 == 0,
            'LOCAL_REGULAR_PRIVATE_KEY_WITH_0600_REQUIRED')
    ips = [ipaddress.IPv4Address(ip) for ip in (app_ip, load_ip)]
    require(all(ip.is_global for ip in ips) and ips[0] != ips[1], 'TWO_DISTINCT_ACTUAL_PUBLIC_IPV4_REQUIRED')
    output = safe_path(output)
    require(output.parent.is_dir() and not output.exists(), 'NEW_EXCLUSIVE_OUTPUT_DIRECTORY_REQUIRED')
    # Directory and files are exclusive. Nothing in the original pin directory is modified.
    output.mkdir(mode=0o700)
    hosts = output / 'known_hosts'
    with hosts.open('x') as stream:
        stream.write(''.join(instance + ' ' + pins[instance] + '\n' for instance in HOSTS))
    hosts.chmod(0o600)
    records = []
    for (instance, alias), address in zip(HOSTS.items(), ips):
        config = output / (instance + '.sshconfig')
        with config.open('x') as stream:
            stream.write(
                f'Host {alias}\n  HostName {address}\n  HostKeyAlias {instance}\n'
                f'  User root\n  Port 22\n  IdentityFile "{identity}"\n'
                f'  UserKnownHostsFile "{hosts}"\n  GlobalKnownHostsFile /dev/null\n'
                '  StrictHostKeyChecking yes\n  UpdateHostKeys no\n'
                '  IdentitiesOnly yes\n  BatchMode yes\n'
                '  ClearAllForwardings yes\n  ForwardAgent no\n  ForwardX11 no\n'
                '  ProxyCommand none\n  ProxyJump none\n  CanonicalizeHostname no\n'
                '  ControlMaster no\n  ControlPath none\n  ControlPersist no\n'
                '  ConnectTimeout 8\n  ConnectionAttempts 1\n'
                '  ServerAliveInterval 15\n  ServerAliveCountMax 2\n')
        config.chmod(0o600)
        records.append({'instance_id': instance, 'alias': alias, 'config': str(config),
                        'public_ip': str(address), 'config_sha256': hashlib.sha256(config.read_bytes()).hexdigest()})
    receipt = {'status': 'LOCAL_CONFIGS_PREPARED_NOT_CONNECTED', 'connection_attempted': False,
               'persistent_authorization_verified_live': False, 'host_identity_verified_live': False,
               'old_configs_overwritten': False, 'route': 'direct',
               'source_known_hosts_sha256': hashlib.sha256(original.read_bytes()).hexdigest(),
               'configs': records}
    with (output / 'reconnect.PUBLIC.json').open('x') as stream:
        json.dump(receipt, stream, sort_keys=True, indent=2)
        stream.write('\n')
    (output / 'reconnect.PUBLIC.json').chmod(0o600)
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ('known-hosts', 'identity', 'app-ip', 'load-ip', 'output-dir'):
        parser.add_argument('--' + key, required=True)
    args = parser.parse_args()
    # Files are local runtime state and may include private paths; create owner-only.
    os.umask(0o077)
    print(json.dumps(prepare(args.known_hosts, args.identity, args.app_ip, args.load_ip, args.output_dir), sort_keys=True))


if __name__ == '__main__':
    main()
