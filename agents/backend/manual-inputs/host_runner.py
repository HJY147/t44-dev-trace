"""Explicit APP-host invocation; private inputs stay in stdin and root-only files.

No SSH, VM lifecycle, seeding, task writes, scheduler restart, relay or benchmark.
"""
import argparse
import base64
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = '90b734f65ce6ee9f5c217e885bc7ea4857e32b48'


def read(path):
    path = Path(path)
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 32 * 1024 * 1024:
        raise ValueError('BOUNDED_ORIGINAL_FILE_REQUIRED')
    return path.read_bytes()


def put(path, raw):
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, 'wb') as stream:
        stream.write(raw)


def inspect_api(container, namespace, expected_image):
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,127}', container):
        raise ValueError('EXPLICIT_CONTAINER_ID_REQUIRED')
    fmt = '{"image":{{json .Image}},"running":{{json .State.Running}},"labels":{{json .Config.Labels}}}'
    row = json.loads(subprocess.run(['docker', '--context', 'default', 'inspect', '--format', fmt, container],
                                    capture_output=True, check=True, timeout=15).stdout)
    if not re.fullmatch('sha256:[0-9a-f]{64}', expected_image):
        raise ValueError('PINNED_ACTUAL_API_IMAGE_ID_REQUIRED')
    if not (row['running'] and row['image'] == expected_image
            and row['labels'].get('com.docker.compose.project') == namespace
            and row['labels'].get('com.docker.compose.service') == 'api'):
        raise ValueError('EXACT_RUNNING_EXISTING_API_OWNER_REQUIRED')
    image = json.loads(subprocess.run(['docker', '--context', 'default', 'image', 'inspect',
                                      '--format', '{{json .Config.Labels}}', row['image']],
                                     capture_output=True, check=True, timeout=15).stdout)
    if image.get('org.opencontainers.image.revision') != SOURCE:
        raise ValueError('EXACT90B_IMAGE_REVISION_REQUIRED')
    return row


def process_audit(container, marker, expected_code):
    code = read(HERE / 'process_guard.py').decode()
    try:
        result = subprocess.run(['docker', '--context', 'default', 'exec', container,
                                 'python', '-B', '-c', code, marker, expected_code], capture_output=True,
                                timeout=15, check=False)
        if result.returncode == 0:
            return json.loads(result.stdout)
    except (subprocess.TimeoutExpired, ValueError):
        pass
    return {'status': 'PROCESS_EXIT_AUDIT_UNAVAILABLE', 'process_exit_proven': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ['old-packet', 'accounts', 'authorization', 'ca', 'source-manifest',
                 'bundle-manifest', 'import-receipt', 'output']:
        parser.add_argument('--' + name, required=True, type=Path)
    parser.add_argument('--api-container', required=True)
    parser.add_argument('--expected-api-image-id', required=True)
    args = parser.parse_args()
    if os.geteuid() != 0:
        raise ValueError('APP_HOST_ROOT_ONLY_PRIVATE_STAGING')
    os.umask(0o077)
    auth = json.loads(read(args.authorization))
    old = read(args.old_packet)
    # Run the shared admission before any Docker execution or credential issuance.
    import importlib.util
    spec = importlib.util.spec_from_file_location('manual_refresh_core', HERE / 'refresh_core.py')
    core = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(core)
    core.authorization(auth, old)
    if args.output.exists() or args.output.is_symlink():
        raise ValueError('EXCLUSIVE_NEW_OUTPUT_DIRECTORY_REQUIRED')
    observed = inspect_api(args.api_container, auth['namespace'], args.expected_api_image_id)
    timeout_probe = subprocess.run(['docker', '--context', 'default', 'exec', args.api_container,
                                    'timeout', '--version'], capture_output=True, timeout=15, check=False)
    if timeout_probe.returncode or not timeout_probe.stdout.startswith(b'timeout (GNU coreutils)'):
        raise ValueError('CONTAINER_GNU_TIMEOUT_REQUIRED_NO_UNBOUNDED_FALLBACK')
    files = {'ca.pem': read(args.ca), 'source-manifest.json': read(args.source_manifest),
             'backend-bundle-manifest.json': read(args.bundle_manifest),
             'backend-import-receipt.json': read(args.import_receipt)}
    payload = {'old_packet_b64': base64.b64encode(old).decode(),
               'accounts': json.loads(read(args.accounts)), 'authorization': auth,
               'public_files_b64': {n: base64.b64encode(b).decode() for n, b in files.items()}}
    code = (read(HERE / 'refresh_core.py').decode() + '\n' + read(HERE / 'runtime_support.py').decode()
            + '\n' + read(HERE / 'refresh_runtime.py').decode())
    code_sha = hashlib.sha256(code.encode()).hexdigest()
    args.output.mkdir(mode=0o700)
    # The container-side GNU timeout supervises the actual process group. The
    # outer timeout is not itself evidence that a container process has stopped.
    try:
        result = subprocess.run(['docker', '--context', 'default', 'exec', '-i', args.api_container,
                                 'timeout', '--signal=TERM', '--kill-after=5s', '300s',
                                 'python', '-B', '-c', code, auth['packet_nonce'], code_sha],
                                input=json.dumps(payload).encode(), capture_output=True,
                                timeout=330, check=False)
    except subprocess.TimeoutExpired as error:
        put(args.output / 'runtime.stdout.private.jsonl', error.stdout or b'')
        put(args.output / 'runtime.stderr.private.log', error.stderr or b'')
        proof = process_audit(args.api_container, auth['packet_nonce'], code_sha)
        put(args.output / 'process-state.PUBLIC.json', core.canonical(proof))
        print(json.dumps({'status': 'MATERIAL_HOST_TIMEOUT_PREFIX_PRESERVED',
                          'process_exit_proven': proof.get('process_exit_proven') is True,
                          'benchmark_started': False, 'output': str(args.output)}))
        return 2
    put(args.output / 'runtime.stdout.private.jsonl', result.stdout)
    put(args.output / 'runtime.stderr.private.log', result.stderr)
    proof = process_audit(args.api_container, auth['packet_nonce'], code_sha)
    put(args.output / 'process-state.PUBLIC.json', core.canonical(proof))
    if result.returncode:
        print(json.dumps({'status': 'FAILED_PRIVATE_PREFIX_PRESERVED', 'output': str(args.output),
                          'process_exit_proven': proof.get('process_exit_proven') is True,
                          'benchmark_started': False}))
        return result.returncode
    if proof.get('process_exit_proven') is not True:
        print(json.dumps({'status': 'MATERIAL_EXIT_NOT_PROVEN_NO_PACKET_RELEASE',
                          'output': str(args.output), 'benchmark_started': False}))
        return 2
    lines = result.stdout.splitlines()
    if not lines:
        raise ValueError('NO_COMPLETE_PRIVATE_RUNTIME_RESULT')
    value = json.loads(lines[-1])
    packet = value['packet']
    core.require(packet['binding_sha256'] == core.sha(core.canonical(
        {k: v for k, v in packet.items() if k != 'binding_sha256'})), 'RETURNED_PACKET_BINDING')
    inputs = args.output / 'inputs'
    inputs.mkdir(mode=0o700)
    for name, raw in files.items():
        put(inputs / name, raw)
    put(inputs / 'session.private.json', core.canonical(packet))
    service_raw = base64.b64decode(value['service_cli_original_b64'], validate=True)
    core.require(core.sha(service_raw) == value['public']['service_cli_original_sha256'],
                 'ORIGINAL_SERVICE_CREDENTIAL_RAW_SHA')
    put(args.output / 'service-cli.original.private.json', service_raw)
    summary = {**value['public'], 'api_owner_observation': observed,
               'material_process_exit_proof': proof,
               'files': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs.iterdir()},
               'private_packet_dir': str(inputs), 'benchmark_started': False,
               'service_credential_private_file': str(args.output / 'service-cli.original.private.json'),
               'transport_started': False, 'old_packet_modified': False}
    put(args.output / 'material.PUBLIC.json', core.canonical(summary))
    print(json.dumps(summary, separators=(',', ':')))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
