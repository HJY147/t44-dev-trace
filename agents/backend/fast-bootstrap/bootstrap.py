"""Direct-run initialization; deliberately not the historical full-admission packet."""
import argparse
import base64
import copy
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile

SOURCE = 'bcec3326b40814fdb1922bbfea7c29473b47ba47'
CONFIG = 'sha256:479c406502b2e4834a0e8ab9ed3fd35e60df60601a041348b1e4a97825056f0e'
SOURCE_MANIFEST = '52d74144437ad77140ccb8cab44bf82c4826e4ba00b9d2dc04895f35100bcfd7'
BUNDLE_MANIFEST = '3e09cc1bfe5074832fbb61bc2e500f5b27bc23a987c3d68f9744dd650c126d29'
SUPPORT_SHA = 'bec01e4038ef4ca5d6ba6d048e96fb8c7cb32933f705fd65a6995d24d9753170'


def need(value, code):
    if not value:
        raise ValueError(code)


def canonical(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False) + '\n').encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def stamp():
    return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')


def assemble(old, sessions, tasks, events, run_id, captured_at):
    """Resource binding only; never assert state, date, rule-window or scan eligibility."""
    rows = copy.deepcopy(old['inventory']['clients'])
    need(len(rows) == 400 and {r['client_id'] for r in rows} == set(range(400)), '400_CLIENT_MAPPING_REQUIRED')
    ids = [r[k]['id'] for r in rows for k in ('transition_task', 'escalation_task')]
    need(len(set(ids)) == 800, '800_DISJOINT_ORIGINAL_IDS_REQUIRED')
    missing_events = 0
    for row in rows:
        pid = row['project_id']
        for kind in ('transition_task', 'escalation_task'):
            task = tasks[pid][row[kind]['id']]
            need(task['project_id'] == pid, 'CURRENT_TASK_PROJECT_MISMATCH')
            row[kind] = task
        task = row['escalation_task']
        candidates = [e for e in events[pid] if e['task_id'] == task['id']
                      and e['project_id'] == pid and e['schedule_version'] == task['schedule_version']]
        row['escalation_event'] = max(candidates, key=lambda e: e['id']) if candidates else None
        missing_events += not candidates
    identity = dict(old['identity'])
    identity.update(git_commit=SOURCE, sut_image_config_digest=CONFIG,
                    source_manifest_sha256=SOURCE_MANIFEST,
                    backend_bundle_manifest_sha256=BUNDLE_MANIFEST)
    inventory = copy.deepcopy(old['inventory'])
    inventory.update(clients=rows, captured_at=captured_at)
    levels = {r['escalation_event']['rule_version'] for r in rows if r['escalation_event'] is not None}
    inventory['rule_version'] = next(iter(levels)) if len(levels) == 1 else None
    return {'schema': 'DIRECT_INPUTS_V1', 'producer_schema': 'T44_FAST_BOOTSTRAP_V1',
            'run_id': run_id, 'created_at': captured_at, 'captured_at': captured_at,
            'mode': 'DIRECT_INITIALIZATION_NOT_ORIGINAL_FULL_GATE_ACCEPTANCE',
            'identity': identity, 'identity_observation': 'EXISTING_API_EXECUTION_AND_ORIGINAL_IMPORT_PROVENANCE',
            'environment': copy.deepcopy(old['environment']), 'sessions': sessions,
            'inventory': inventory,
            'cohort_snapshot_sha256': sha(canonical(rows)),
            'missing_current_escalation_events': missing_events,
            'historical_counts_not_current': copy.deepcopy(old['counts']),
            'historical_inventory_fields_not_refreshed': ['project_manager_ids', 'static_contract_payloads'],
            'omitted_preparation_gates': ['maintenance', 'replan', 'transition_horizon',
                'escalation_window_horizon', 'complete_scan_wait', 'per_task_dependency_and_role_preflight'],
            'production_business_rules_changed': False, 'benchmark_started': False}


def collect(old, accounts, api, issue_service, read_sessions, run_id, clock=stamp):
    """Dependency-injected full request graph for an offline synthetic rehearsal."""
    sessions = {}
    for role in ('manager', 'developer', 'reviewer'):
        account = accounts[role]
        value, _ = api.request('/auth/login', body={k: account[k] for k in ('username', 'password')})
        need(value['user']['id'] == account['user_id'] == old['sessions'][role]['user_id'],
             'REAL_LOGIN_SUBJECT_MISMATCH')
        sessions[role] = {'token': value['access_token'], 'user_id': value['user']['id'],
                          'expires_at': value['expires_at']}
    service, original_service = issue_service()
    sessions['service'] = service
    # Four exact new sessions, one bounded database readback; no historical token reuse.
    sessions = read_sessions(sessions)
    pids = sorted({r['project_id'] for r in old['inventory']['clients']})
    tasks, events = {}, {}
    for pid in pids:
        values = api.pages(f'/projects/{pid}/tasks', sessions['manager']['token'])
        need(len({t['id'] for t in values}) == len(values), 'DUPLICATE_TASK_PAGE_RESULT')
        tasks[pid] = {t['id']: t for t in values}
        events[pid] = api.pages(f'/projects/{pid}/escalations', sessions['manager']['token'])
    result = assemble(old, sessions, tasks, events, run_id, clock())
    result['initialization_http_requests'] = len(api.requests)
    return result, original_service


def container_main(payload):
    from t44.persistence import SqlAlchemyUnitOfWorkFactory, create_mysql_engine
    from t44.services.common import wire
    from t44.settings import Settings
    need(Path(__import__('t44').__file__).as_posix() == '/app/backend/t44/__init__.py', 'API_PACKAGE_ORIGIN')
    old = payload['old']
    settings = Settings.from_env()
    need(settings.mysql_settings().database == old['additional_neutral_snapshots']['database'], 'EXISTING_DATABASE_SCOPE')
    factory = SqlAlchemyUnitOfWorkFactory(create_mysql_engine(settings.mysql_settings()))
    with factory() as uow:
        account = uow.gateway.get('service_accounts', old['sessions']['service']['user_id'])
    need(account and account['active'] and account['name'].startswith(
        old['additional_neutral_snapshots']['namespace']), 'EXISTING_SERVICE_ACCOUNT_REQUIRED')
    pids = sorted({r['project_id'] for r in old['inventory']['clients']})
    with tempfile.TemporaryDirectory(prefix='t44-direct-init-') as tmp:
        folder = Path(tmp)
        ca = folder / 'ca.pem'
        ca.write_bytes(base64.b64decode(payload['ca_b64'], validate=True))
        os.chmod(ca, 0o600)
        need(sha(ca.read_bytes()) == old['environment']['ca_sha256'], 'ORIGINAL_CA_BYTES_REQUIRED')
        support = folder / 'runtime_support.py'
        raw = base64.b64decode(payload['support_b64'], validate=True)
        need(sha(raw) == SUPPORT_SHA, 'PINNED_TLS_SUPPORT_REQUIRED')
        support.write_bytes(raw)
        spec = importlib.util.spec_from_file_location('tls_support', support)
        tls = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(tls)
        api = tls.PinnedAPI(old['environment']['origin'],
            payload.get('connect_ip') or socket.gethostbyname(payload['gateway_dns']), ca,
            connect_port=payload.get('connect_port'))

        def issue_service():
            token_file = folder / 'service.private.json'
            argv = [sys.executable, '-m', 't44.cli', 'service-token', '--name', account['name'],
                    '--token-file', str(token_file)]
            for pid in pids:
                argv += ['--project-id', str(pid)]
            result = subprocess.run(argv, capture_output=True, timeout=45, check=False)
            need(result.returncode == 0, 'SERVICE_CLI_FAILED_NO_RETRY')
            original = token_file.read_bytes()
            value = json.loads(original)
            return {'token': value['access_token'], 'user_id': account['id'],
                    'expires_at': value['expires_at']}, original

        def read_sessions(sessions):
            hashes = [hashlib.sha256(s['token'].encode()).digest() for s in sessions.values()]
            with factory() as uow:
                rows = uow.gateway.rows('auth_sessions', {'token_hash': hashes}, limit=5)
                memberships = uow.gateway.rows('project_members', {
                    'user_id': [sessions[r]['user_id'] for r in ('manager', 'developer', 'reviewer')],
                    'active': 1})
            need(len(rows) == 4, 'FOUR_REAL_NEW_SESSIONS_REQUIRED')
            by_hash = {r['token_hash']: r for r in rows}
            for role, session in sessions.items():
                row = by_hash[hashlib.sha256(session['token'].encode()).digest()]
                subject = row['service_account_id'] if role == 'service' else row['user_id']
                need(subject == session['user_id'] and row['revoked_at'] is None
                     and wire(row['expires_at']) == session['expires_at'], 'PERSISTED_SESSION_MISMATCH')
                project_ids = row['project_ids'] if role == 'service' else sorted({
                    m['project_id'] for m in memberships if m['user_id'] == subject})
                session.update(project_ids=project_ids, scopes=row['scopes'])
            return sessions

        try:
            value, original = collect(old, payload['accounts'], api, issue_service,
                                      read_sessions, payload['run_id'])
            with factory() as uow:
                g = uow.gateway
                counts = {n: g.count(n, {}) for n in
                    ('projects', 'tasks', 'task_dependencies', 'reviews', 'decisions')}
                snapshot = wire(g.rows('tasks', {}, order_by=('id',)))
            value['counts'] = {'projects': counts['projects'], 'tasks': counts['tasks'],
                'dependencies': counts['task_dependencies'], 'reviews': counts['reviews'],
                'decisions': counts['decisions']}
            value['fixture_sha256'] = sha(json.dumps(snapshot, sort_keys=True,
                separators=(',', ':')).encode())
            value['counts_captured_at'] = stamp()
            value['fixture_hash_scope'] = 'CURRENT_DATABASE_ALL_TASKS_ORDERED_ID'
            value['service_cli_original_b64'] = base64.b64encode(original).decode()
            return value
        finally:
            api.close()


def exclusive_write(path, raw):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('old-packet', 'accounts', 'ca', 'runtime-support', 'import-receipt', 'output'):
        p.add_argument('--' + name, type=Path, required=True)
    p.add_argument('--api-container', required=True)
    p.add_argument('--run-id', required=True)
    p.add_argument('--gateway-dns', default='tls-gateway')
    p.add_argument('--connect-ip')
    p.add_argument('--connect-port', type=int, default=8443)
    a = p.parse_args()
    os.umask(0o077)
    need(os.geteuid() == 0, 'ROOT_PRIVATE_HOST_REQUIRED')
    a.output.mkdir(mode=0o700, exist_ok=False)
    try:
        old_raw = a.old_packet.read_bytes()
        old = json.loads(old_raw)
        need(sha(canonical({k: v for k, v in old.items() if k != 'binding_sha256'}))
             == old['binding_sha256'], 'ORIGINAL_PACKET_BINDING_REQUIRED')
        receipt = json.loads(a.import_receipt.read_bytes())
        need(receipt['source_sha'] == SOURCE and receipt['source_manifest_sha256'] == SOURCE_MANIFEST
             and receipt['bundle_manifest_sha256'] == BUNDLE_MANIFEST
             and receipt['identity']['success'] is True
             and receipt['identity']['config_id'] == CONFIG, 'RECORDED_IMPORT_PROVENANCE_REQUIRED')
        payload = {'old': old, 'accounts': json.loads(a.accounts.read_bytes()),
            'ca_b64': base64.b64encode(a.ca.read_bytes()).decode(),
            'support_b64': base64.b64encode(a.runtime_support.read_bytes()).decode(),
            'run_id': a.run_id, 'gateway_dns': a.gateway_dns,
            'connect_ip': a.connect_ip, 'connect_port': a.connect_port}
        code = Path(__file__).read_text().replace("if __name__ == '__main__':\n    main()", '')
        code += '\nprint(json.dumps(container_main(json.load(sys.stdin)), separators=(",", ":")))\n'
        result = subprocess.run(['docker', '--context', 'default', 'exec', '-i', a.api_container,
            'timeout', '--signal=TERM', '--kill-after=5s', '120s', 'python', '-B', '-c', code],
            input=canonical(payload), capture_output=True, timeout=135, check=False)
        exclusive_write(a.output / 'runtime.stdout.private', result.stdout)
        exclusive_write(a.output / 'runtime.stderr.private', result.stderr)
        need(result.returncode == 0, 'INITIALIZATION_FAILED_PREFIX_PRESERVED_NO_RETRY')
        value = json.loads(result.stdout)
        original = base64.b64decode(value.pop('service_cli_original_b64'), validate=True)
        exclusive_write(a.output / 'service-cli.original.private.json', original)
        value['original_import_receipt_sha256'] = sha(a.import_receipt.read_bytes())
        value['original_packet_sha256'] = sha(old_raw)
        exclusive_write(a.output / 'current-inputs.private.json', canonical(value))
        public = {'schema': 'T44_FAST_BOOTSTRAP_RECEIPT_V1', 'status': 'DIRECT_INITIALIZATION_COMPLETE',
            'run_id': a.run_id, 'captured_at': value['captured_at'], 'source_expected': SOURCE,
            'http_requests': value['initialization_http_requests'], 'original_task_ids': 800,
            'missing_current_escalation_events': value['missing_current_escalation_events'],
            'private_inputs': str(a.output / 'current-inputs.private.json'),
            'original_full_preparation_gates_executed': False, 'benchmark_started': False,
            'no_automatic_retry': True}
        exclusive_write(a.output / 'bootstrap.PUBLIC.json', canonical(public))
        print(json.dumps(public))
    except BaseException:
        exclusive_write(a.output / 'FAILED.PUBLIC.json', canonical({
            'status': 'FAILED_PREFIX_PRESERVED', 'automatic_retry': False,
            'credentials_may_have_been_issued': True, 'benchmark_started': False}))
        raise


if __name__ == '__main__':
    main()
