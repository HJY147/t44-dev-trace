"""Single-use APP preparation worker; launch asynchronously, never starts S1/S2."""

import argparse
import hashlib
import ipaddress
import json
import os
import platform
import secrets
import subprocess
from datetime import datetime, timezone
from pathlib import Path

BASE = Path('/root/t44-r9')
PROFILE = BASE / 'r29-code-01/profile'
TOOLS = BASE / 'p790-r29-01'
CAMPAIGN = BASE / 'campaign-r29-01'
RECORDS = BASE / 'r29-app-prep-01'
BRIDGE = BASE / 'scope-bridge-v3-01'
SOURCE = 'f7cdb5fa3b19f84d8ab0d0b042bf51a5b8484e8f'
STOP = '2026-10-29T12:00:00Z'
ANCHOR = '2026-10-28T04:00:00Z'
RUN = 'r28p64gen04'
PROFILE_SHA = '5b0eef799680cbc30c5096d37b4fbffb32087add52410045e33842c972d4237a'
MANIFEST_SHA = 'a5510d962deee65ace91a3fa7cf93d0c720e1cb08e4b841220b75e9cc082e590'
BRIDGE_SHA = 'e5512dd264a2199bb599742ea72f671d184ab5e41a3d102bed498d49b244d5f7'
UPGRADE_SHA = 'df84e9b1dbcf8946209ae6ae0ea868d63dc96b60d01c2bae7f3d621e65b311b0'
SOURCE_MANIFEST = '3368534aececbb5441225e7859338aa3079b6e41798e38673bd8f337f8993577'
IMAGE_ID = 'sha256:a7d3dde54efda1405bbd7d9f5f5b7c5a6439f1afd1dc8c50b2ed8b37625fa5da'
ROLES = {'mysql', 'rabbitmq', 'api', 'consumer', 'web', 'tls-gateway'}


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stamp():
    return datetime.now(timezone.utc).isoformat()


def remaining():
    return (datetime.fromisoformat(STOP.replace('Z', '+00:00')) - datetime.now(timezone.utc)).total_seconds()


def exclusive(path, raw):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())


def save(path, value):
    exclusive(path, (json.dumps(value, sort_keys=True) + '\n').encode())


def json_rows(raw):
    # CLI stdout is JSONL; never pass a multi-record stream to json.loads.
    return [json.loads(line) for line in raw.splitlines() if line.strip()]


def choose(raw, predicate):
    rows = [row for row in json_rows(raw) if isinstance(row, dict) and predicate(row)]
    need(len(rows) == 1, 'ONE_EXACT_ACTUAL_STDOUT_RECORD_REQUIRED')
    return rows[0]


def pinned_tree(directory, manifest_name, wanted, key):
    path = directory / manifest_name
    need(path.resolve() == path and sha(path) == wanted, 'PINNED_MANIFEST_REQUIRED')
    value = json.loads(path.read_bytes())
    for name, row in value[key].items():
        candidate = directory / name
        need(not Path(name).is_absolute() and '..' not in Path(name).parts, 'RELATIVE_MANIFEST_FILE_REQUIRED')
        need(candidate.resolve() == candidate and sha(candidate) == row['sha256'], 'EVERY_PINNED_CODE_FILE_REQUIRED')


def preflight(app_ip):
    need(os.geteuid() == 0 and platform.system() == 'Linux' and platform.machine() in {'x86_64', 'amd64'}, 'ROOT_LINUX_AMD64_REQUIRED')
    need(BASE.is_dir() and BASE.resolve() == BASE, 'EXISTING_OWNED_BASE_REQUIRED')
    address = ipaddress.IPv4Address(app_ip)
    need(address.is_private and not address.is_loopback and not address.is_link_local, 'ACTUAL_PRIVATE_APP_IP_REQUIRED')
    need(remaining() > 600, 'UNCHANGED_FUTURE_HARD_STOP_REQUIRED')
    need(not CAMPAIGN.exists() and not CAMPAIGN.is_symlink() and not RECORDS.exists() and not RECORDS.is_symlink(), 'SINGLE_NEW_NAMESPACE_NO_RETRY_REQUIRED')
    pinned_tree(PROFILE, 'profile.json', PROFILE_SHA, 'derived_files')
    pinned_tree(TOOLS, 'manifest.json', MANIFEST_SHA, 'files')
    pinned_tree(BRIDGE, 'manifest.PUBLIC.json', BRIDGE_SHA, 'files')
    binding = BASE / 'backend-f7-build-01/upgrade-binding.json'
    need(binding.resolve() == binding and sha(binding) == UPGRADE_SHA, 'ACTUAL_ORIGINAL_UPGRADE_BINDING_REQUIRED')
    need(json.loads(binding.read_bytes())['actual_image_id'] == IMAGE_ID, 'ACTUAL_F7_IMAGE_BINDING_REQUIRED')


def step(label, argv, cap=360):
    save(RECORDS / (label + '.command.private.json'), {'utc': stamp(), 'argv': list(map(str, argv)), 'automatic_retry': False})
    out = RECORDS / (label + '.stdout.private')
    err = RECORDS / (label + '.stderr.private')
    timeout = min(cap, remaining())
    need(timeout > 0, 'ABSOLUTE_HARD_STOP_EXPIRED')
    code = None
    timed_out = False
    with out.open('xb') as stdout, err.open('xb') as stderr:
        try:
            result = subprocess.run(list(map(str, argv)), stdout=stdout, stderr=stderr, check=False, timeout=timeout)
            code = result.returncode
        except subprocess.TimeoutExpired:
            timed_out = True
    save(RECORDS / (label + '.exit.PUBLIC.json'), {'utc': stamp(), 'returncode': code, 'timed_out': timed_out, 'stdout_sha256': sha(out), 'stderr_sha256': sha(err), 'partial_state_preserved': True})
    need(code == 0 and not timed_out, 'STEP_FAILED_PRESERVE_NO_RETRY_' + label)
    return out.read_bytes()


def actual_roles(value, required):
    rows = value['resources']
    need(len({r['role'] for r in rows}) == len(rows), 'UNIQUE_ACTUAL_ROLES_REQUIRED')
    mapping = {r['role']: r for r in rows}
    result = {}
    for name in required:
        row = mapping[name]
        need(not row.get('absent') and row['state']['Running'] is True and row['restart_count'] == 0, 'ACTUAL_RUNNING_ZERO_RESTART_ROLE_REQUIRED')
        result[name] = {'container_id': row['container_id'], 'image_id': row['image_id'], 'running': row['state']['Running'], 'restart_count': row['restart_count']}
    return result


def prepare_once(app_ip):
    preflight(app_ip)
    RECORDS.mkdir(mode=0o700)
    gen = ['python3', '-I', str(PROFILE / 'generation.py')]
    prepared = choose(step('01-prepare', gen + ['prepare', '--factory', BASE / 'campaign-935/p/controller.py', '--upgrade-binding', BASE / 'backend-f7-build-01/upgrade-binding.json', '--upgrade-binding-sha256', UPGRADE_SHA, '--source-package', BASE / 'source-f7-checked-01', '--source-manifest-sha256', SOURCE_MANIFEST, '--original-proof', BASE / 'proof-v2-01/proof.jsonl', '--image-proof', BASE / 'image-proof.py', '--output', CAMPAIGN, '--run-id', RUN, '--app-ip', app_ip, '--f-tls-port', '22443', '--f-http-port', '18480', '--p-tls-port', '22445', '--p-http-port', '18481', '--p-workers', '64', '--p-pool-size', '5', '--p-max-overflow', '0', '--stop-utc', STOP]), lambda r: r.get('success') is True and 'phases' in r)
    p = prepared['phases']['p']
    phase = Path(p['phase_dir'])
    need(phase == CAMPAIGN / 'p', 'EXACT_NEW_P_PHASE_REQUIRED')
    wanted = p['binding_sha256']
    need(sha(phase / 'binding.json') == wanted, 'ACTUAL_PREPARE_BINDING_SHA_REQUIRED')
    binding = json.loads((phase / 'binding.json').read_bytes())
    common = ['--phase-dir', phase, '--binding-sha256', wanted]

    def operation(label, action, more=()):
        return choose(step(label, gen + [action] + common + list(more)), lambda r: r.get('success') is True)

    operation('02-arm', 'arm')
    operation('03-config', 'config')
    operation('04-infra', 'infra')
    budget = operation('05-actual-budget', 'probe-budget')
    receipt = Path(budget['budget_receipt'])
    need(receipt.parent == phase / 'receipts' and sha(receipt) == budget['budget_receipt_sha256'], 'ACTUAL_BUDGET_RECEIPT_SHA_REQUIRED')
    budget_args = ['--budget-receipt', receipt, '--budget-receipt-sha256', budget['budget_receipt_sha256']]
    operation('06-migrate', 'migrate', ['--database', binding['database']] + budget_args)
    state = operation('07-prep-actual-status', 'status')
    roles = actual_roles(state, {'mysql', 'rabbitmq'})
    image_rows = json_rows(step('08-actual-backend-image', ['docker', '--context', 'default', 'image', 'inspect', '--format', '{{json .Id}}', binding['images']['backend']['alias']]))
    need(image_rows == [IMAGE_ID] and image_rows[0] == binding['image_ids']['backend'], 'ACTUAL_CURRENT_F7_BACKEND_IMAGE_REQUIRED')
    proof = CAMPAIGN / 'actual-source-files.json'
    need(sha(proof) == binding['source_actual_proof_sha256'] and len(json.loads(proof.read_bytes())['files']) == 53, 'ACTUAL_FULL_SOURCE53_PROOF_REQUIRED')
    grant = {'kind': 'ROOT_P_PREP_GRANT_V4', 'admitted': True, 'HTTP_authorized': False, 'formal_performance_authorized': False, 'no_automatic_retry': True, 'issued_at': stamp(), 'expires_at': STOP, 'session_nonce': secrets.token_hex(32), 'source_sha': SOURCE, 'run_id': RUN, 'binding_sha256': wanted, 'namespace': binding['project'], 'database': binding['database'], 'api_workers': binding['api_workers'], 'backend_image_id': image_rows[0], 'source_proof_sha256': sha(proof), 'source_file_count': 53, 'seed': 44, 'anchor_at': ANCHOR, 'stop_utc': STOP, 'session_ttl_seconds': 600, 'cohorts': [['baseline1', 1, 20, 0], ['warmup40', 40, 5, 1], ['measure400', 400, 5, 41]], 'roles': roles}
    grant_path = RECORDS / 'prep-grant.private.json'
    save(grant_path, grant)
    result = choose(step('09-bootstrap-once', ['python3', TOOLS / '790_bootstrap.py'] + common + ['--output-name', 'fixture790-r29-01', '--anchor-at', ANCHOR, '--manifest-sha256', MANIFEST_SHA] + budget_args + ['--root-grant', grant_path, '--root-grant-sha256', sha(grant_path), '--scope-bridge-dir', BRIDGE], cap=900), lambda r: r.get('kind') == 'contrast790-bootstrap-complete-not-acceptance')
    idle = operation('10-idle-after-bootstrap', 'idle', budget_args)
    all_roles = actual_roles(idle, ROLES)
    scheduler = [r for r in idle['resources'] if r['role'] == 'scheduler']
    need(scheduler == [{'role': 'scheduler', 'absent': True}], 'ACTUAL_SCHEDULER_ABSENCE_REQUIRED')
    need(idle['host_https']['status'] == 401 and idle['host_https']['strict_CA_and_IP_verified'] is True, 'ACTUAL_STRICT_TLS401_REQUIRED')
    summary = {'kind': 'R29_APP_PREP_COMPLETE_NOT_PRESSURE', 'source_sha': SOURCE, 'phase_dir': str(phase), 'binding_sha256': wanted, 'budget_receipt': str(receipt), 'budget_receipt_sha256': budget['budget_receipt_sha256'], 'actual_max_connections': budget['actual_max_connections'], 'source_proof_sha256': sha(proof), 'bootstrap_output_dir': result['output_dir'], 'roles': all_roles, 'scheduler': {'absent': True}, 'stop_utc': STOP, 'S1_or_S2_started': False, 'pressure_grant': None, 'relay_ready': None, 'resource_ready': None, 'formal_acceptance': False, 'raw_records_dir': str(RECORDS)}
    save(RECORDS / 'complete.PUBLIC.json', summary)
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--app-ip', required=True)
    parser.add_argument('--root-admit-prep', action='store_true', required=True)
    args = parser.parse_args()
    os.umask(0o077)
    try:
        print(json.dumps(prepare_once(args.app_ip), sort_keys=True))
    except Exception as error:
        result = {'kind': 'R29_APP_PREP_FAILED_NO_RETRY', 'error_class': type(error).__name__, 'reason': str(error), 'partial_state_preserved': True, 'automatic_retry': False, 'S1_or_S2_started': False}
        if RECORDS.is_dir() and not (RECORDS / 'failure.PUBLIC.json').exists():
            save(RECORDS / 'failure.PUBLIC.json', result)
        print(json.dumps(result, sort_keys=True))
        raise SystemExit(1) from None


if __name__ == '__main__':
    main()
