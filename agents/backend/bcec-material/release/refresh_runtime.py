"""App-container half, concatenated after refresh_core.py by host_runner.py.

Only stdout is a PRIVATE transport to the host runner. Never invoke this file
directly through a public cloud-console output pane.
"""
import base64
import http.client
import os
import ssl
import subprocess
import sys
import tempfile
import time
import urllib.parse
import uuid
from pathlib import Path


def private_event(kind, value):
    # Captured only by host_runner's root-private stdout file, including failure prefixes.
    print(json.dumps({'private_event': kind, 'value': value}, separators=(',', ':'), default=str), flush=True)


def runtime(payload):
    from t44.persistence import SqlAlchemyUnitOfWorkFactory, create_mysql_engine
    from t44.services.common import wire
    from t44.settings import Settings
    from t44.scheduling.rules import load_rules, select_window

    old_raw = base64.b64decode(payload['old_packet_b64'], validate=True)
    auth = payload['authorization']
    old = authorization(auth, old_raw)
    job = setup_material_job(auth)
    settings = Settings.from_env()
    require(settings.mysql_settings().database == auth['database'], 'ACTUAL_DATABASE_MISMATCH')
    require(Path(__import__('t44').__file__).as_posix() == '/app/backend/t44/__init__.py',
            'OFFICIAL_PACKAGE_ORIGIN_REQUIRED')
    factory = SqlAlchemyUnitOfWorkFactory(create_mysql_engine(settings.mysql_settings()))
    original_ids = sorted({c['project_id'] for c in old['inventory']['clients']})
    require(len(original_ids) == 40, 'EXACT_EXISTING_FORTY_PROJECTS_REQUIRED')
    manifests = {n: base64.b64decode(b, validate=True) for n, b in payload['public_files_b64'].items()}
    require(sha(manifests['ca.pem']) == old['environment']['ca_sha256'], 'ACTUAL_CA_PIN')
    candidate_source = validate_new_source(auth, old, manifests)
    for row in candidate_source['backend_runtime_files']:
        path = Path('/app') / row['path']
        require(not path.is_symlink() and path.is_file() and sha(path.read_bytes()) == row['sha256'],
                'CURRENT_CONTAINER_FULL_SOURCE_BYTES_REQUIRED')
    sessions, attestations, requests = {}, {}, []
    with tempfile.TemporaryDirectory(prefix='manual-material-') as folder:
        folder = Path(folder)
        ca = folder / 'ca.pem'
        ca.write_bytes(manifests['ca.pem'])
        os.chmod(ca, 0o600)
        maintenance = payload.get('maintenance_endpoint')
        api = PinnedAPI(old['environment']['origin'],
                        maintenance['connect_ip'] if maintenance else old['environment']['connect_ip'], ca,
                        connect_port=maintenance['connect_port'] if maintenance else None)
        requests = api.requests
        with factory() as uow:
            service = uow.gateway.get('service_accounts', old['sessions']['service']['user_id'])
        require(service is not None and service['active']
                and service['name'].startswith(auth['namespace']), 'EXISTING_SERVICE_ACCOUNT_SCOPE')
        token_path = folder / 'actual-service.json'
        argv = [sys.executable, '-m', 't44.cli', 'service-token', '--name', service['name'],
                '--token-file', str(token_path)]
        for pid in original_ids:
            argv += ['--project-id', str(pid)]
        issued = subprocess.run(argv, capture_output=True, timeout=45)
        require(issued.returncode == 0, 'REAL_ORIGINAL_SERVICE_CLI_FAILED')
        original_service_raw = token_path.read_bytes()
        original_service = json.loads(original_service_raw)
        private_event('service_cli_original_before_readback', {
            'raw_b64': base64.b64encode(original_service_raw).decode()})
        with factory() as uow:
            row = uow.gateway.get('auth_sessions', original_service['session_id'])
        require(row['token_hash'] == hashlib.sha256(original_service['access_token'].encode()).digest()
                and row['revoked_at'] is None and row['service_account_id'] == service['id'],
                'REAL_SERVICE_SESSION_READBACK')
        sessions['service'] = {'token': original_service['access_token'], 'user_id': row['service_account_id'],
                               'expires_at': wire(row['expires_at']), 'project_ids': row['project_ids'],
                               'scopes': row['scopes']}
        attestations['service'] = {k: v for k, v in sessions['service'].items() if k != 'token'}
        attestations['service'].update(issued_at=wire(row['created_at']),
                                       token_sha256=sha(original_service['access_token'].encode()),
                                       method='ORIGINAL_SERVICE_CLI_AND_PERSISTED_READBACK')

        try:
            for role in ['manager', 'developer', 'reviewer']:
                account = payload['accounts'][role]
                login, meta = api.request('/auth/login', body={'username': account['username'],
                                                          'password': account['password']})
                private_event('actual_login_before_readback', {'role': role, 'response': login, 'meta': meta})
                require(login['user']['id'] == account['user_id'] == old['sessions'][role]['user_id'],
                        'ORIGINAL_ROLE_SUBJECT_' + role)
                token = login['access_token']
                with factory() as uow:
                    matches = uow.gateway.rows('auth_sessions', {'token_hash': hashlib.sha256(token.encode()).digest()}, limit=2)
                require(len(matches) == 1 and matches[0]['revoked_at'] is None
                        and matches[0]['user_id'] == account['user_id'], 'HUMAN_SESSION_PERSISTED_' + role)
                row = matches[0]
                require(wire(row['expires_at']) == login['expires_at'], 'SERVER_SESSION_EXPIRY_' + role)
                scope, roles_by_project = role_scope(api, role, token, original_ids)
                sessions[role] = {'token': token, 'user_id': account['user_id'], 'expires_at': login['expires_at'],
                                  'project_ids': scope, 'scopes': row['scopes']}
                attestations[role] = {k: v for k, v in sessions[role].items() if k != 'token'}
                attestations[role].update(issued_at=wire(row['created_at']), token_sha256=sha(token.encode()),
                                          response_meta=meta, roles_by_project=roles_by_project,
                                          method='REAL_HTTPS_LOGIN_AND_PERSISTED_READBACK')
            inventory = current_inventory(api, old['inventory'], sessions, load_rules(), select_window)
        finally:
            api.close()
    with factory() as uow:
        g = uow.gateway
        rows = {n: g.count(n, {}) for n in ['projects', 'tasks', 'task_dependencies', 'reviews', 'decisions']}
        snapshot = wire(g.rows('tasks', {}, order_by=('id',)))
    counts = {'counts': {'projects': rows['projects'], 'tasks': rows['tasks'],
                         'dependencies': rows['task_dependencies'], 'reviews': rows['reviews'],
                         'decisions': rows['decisions']},
              'actual_fixture_sha256': sha(json.dumps(snapshot, sort_keys=True, separators=(',', ':')).encode()),
              'captured_at': stamp(datetime.now(timezone.utc))}
    packet_at = datetime.now(timezone.utc)
    validate_stable_inventory(inventory, load_rules(), select_window, packet_at)
    packet = build_packet(old, auth, sessions, inventory, counts, manifests,
                          packet_at, attestations)
    return {'packet': packet, 'requests': requests,
            'service_cli_original_b64': base64.b64encode(original_service_raw).decode(), 'public': {
        'status': 'FRESH_MATERIAL_NOT_BENCHMARK_AUTHORIZATION', 'new_tasks': 0, 'seed_calls': 0,
        'packet_run_id': packet['run_id'], 'packet_binding_sha256': packet['binding_sha256'],
        'actual_fixture_sha256': packet['fixture_sha256'], 'counts': packet['counts'],
        'session_attestations': attestations, 'original_task_ids_preserved': True,
        'service_cli_original_sha256': sha(original_service_raw),
        'external_writer_absence_proven': False, 'scheduler_token_refreshed': False,
        'http_request_count': len(requests)}}


if __name__ == '__main__':
    try:
        print(json.dumps(runtime(json.load(sys.stdin)), separators=(',', ':'), default=str))
    except Exception as error:
        # Fixed exception class only. Neither password, token nor remote error body is public.
        print(json.dumps({'status': 'BLOCKED', 'exception_type': type(error).__name__,
                          'error_code': str(error) if type(error) is ValueError else 'RUNTIME_DEPENDENCY_OR_IO_FAILURE'}))
        raise SystemExit(2)
