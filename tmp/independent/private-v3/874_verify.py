"""Offline-only freeze verification. This entry never creates a Harness or contacts a SUT."""
import ast
import base64
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import sys

def offline_wire_selftest(output):
    """Synthetic harness I/O checks only. All transport is replaced before any call."""
    import copy
    import importlib.util
    import threading
    from jsonschema import Draft202012Validator, FormatChecker
    target = Path(output); target.mkdir(mode=0o700, parents=True, exist_ok=True)
    spec = importlib.util.spec_from_file_location('own_offline_wire_support', HERE / '881_support.py')
    S = importlib.util.module_from_spec(spec); spec.loader.exec_module(S)
    h = object.__new__(S.Harness)
    h.c = {'python': 'offline-python', 'control_cli': 'offline-control'}
    h.rec = S.Recorder(target, 'offline-harness-wire-only')
    h.validator_cls = Draft202012Validator; h.formats = FormatChecker()
    h.base = 'http://offline.invalid/api/v1'; h.tokens = {'m': 'offline-synthetic-session'}
    h.users = {'m': 1, 'a': 2, 'b': 3, 'r': 4, 'o': 5, 'n': 6}
    h.credentials = {k: {'username': 'offline_' + k, 'password': 'offline-not-real'} for k in h.users}
    h.local = threading.local(); h.covered = set()
    now = '2026-10-24T00:00:00Z'
    meta = {'request_id': 'offline-result-001', 'server_time': now, 'contract_version': '1.1.0',
            'replayed': False, 'original_request_id': None}
    project = {'id': 1, 'name': 'offline-project', 'description': '', 'version': 1,
               'my_roles': [1], 'created_by': 1, 'created_at': now}
    iteration = {'id': 2, 'project_id': 1, 'version': 1, 'plan_version': 1, 'plan': {
        'name': 'offline-iteration', 'planned_start': now, 'planned_end': '2026-10-25T00:00:00Z',
        'capacity': [{'user_id': 2, 'available_hours': 8}], 'buffer_hours': 1,
        'delay_contingency': 'offline-contingency'}, 'created_at': now, 'updated_at': now}
    task = {'id': 3, 'project_id': 1, 'iteration_id': 2, 'title': 'offline-task', 'description': '',
        'owner_id': 2, 'state': 1, 'version': 1, 'schedule_version': 1, 'delivery_cycle': 1,
        'review_cycle': 1, 'plan': S.plan(), 'blocked_from_state': None, 'block_reason': None,
        'responsibility_stage': None, 'latest_review_id': None, 'approved_review_id': None,
        'approved_assessment_id': None, 'approved_assessment_version': None, 'escalation_count': 0,
        'created_at': now, 'updated_at': now, 'artifact_revision': None}
    queue, results = [], []
    def envelope(data): return {'data': data, 'meta': meta}
    def enqueue(op, status, data): queue.append((op, status, envelope(data)))
    class Response:
        def __init__(self, status, value): self.status, self.value, self.headers = status, value, {'Content-Type': 'application/json'}
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def read(self): return self.value if isinstance(self.value, bytes) else json.dumps(self.value).encode()
    def fake_open(request, timeout):
        assert queue, 'Unexpected offline transport call'
        op, status, value = queue.pop(0)
        assert request.method == S.OPS[op][0]
        return Response(status, value)
    def passed(name): results.append({'id': name, 'status': 'pass'})
    original_open, original_run = S.urllib.request.urlopen, S.subprocess.run
    S.urllib.request.urlopen = fake_open
    class Completed:
        def __init__(self, code, stdout): self.returncode, self.stdout, self.stderr = code, stdout, ''
    current = None
    calls = []
    def fake_run(argv, **kwargs):
        calls.append({'argv': argv, 'stdin': kwargs.get('input'), 'timeout': kwargs.get('timeout'),
                      'capture_output': kwargs.get('capture_output')})
        if isinstance(current, Exception): raise current
        return current
    S.subprocess.run = fake_run
    try:
        enqueue('createProject', 201, project)
        for label, roles in [('a', [2, 3]), ('b', [2]), ('r', [3]), ('n', [1])]:
            enqueue('addProjectMember', 201, {'project_id': 1, 'user': {'id': h.users[label],
                'username': h.credentials[label]['username'], 'display_name': 'offline ' + label},
                'roles': roles, 'version': 1, 'active': True})
        enqueue('createIteration', 201, iteration)
        fixture = h.fixture(); assert fixture['p'] == 1 and fixture['i'] == 2
        enqueue('createTask', 201, {'task': task, 'audit_id': 1})
        assert h.task(fixture) == task
        enqueue('getTask', 200, task); assert h.get(fixture, task) == task
        advanced = copy.deepcopy(task); advanced.update(state=2, version=2)
        enqueue('transitionTask', 200, {'task': advanced, 'audit_id': 2, 'decision': None})
        assert h.trans(fixture, task, 1) == advanced
        passed('factory-project-member-iteration-task-get-transition-envelope-projection')
        for name, value in [('incorrect-task-envelope', envelope(task)), ('non-json-response', b'<html>invalid</html>')]:
            queue.append(('createTask', 201, value))
            try: h.task(fixture)
            except AssertionError: passed(name + '-rejected')
            else: raise AssertionError(name + ' was accepted')
        error = {'code': 'ACTION_FORBIDDEN', 'message': 'offline denied', 'request_id': 'offline-denied',
                 'audit_id': 1, 'current_version': None, 'current_state': None,
                 'original_error_code': None, 'violations': []}
        queue.append(('createTask', 403, error))
        assert h.request('createTask', ids={'project_id': 1}, body={}, expected=403, code='ACTION_FORBIDDEN') == error
        passed('declared-error-response-remains-error')
        samples = {
            'init-user': '{"user_id":2}',
            'scheduler-scope': '{"session_id":3,"expires_at":"2026-10-24T01:00:00Z","credential_written":true,"rotated":true,"previous_session_revoked":true,"previous_session_already_inactive":false}',
            'service-credential': '{"credential":{"access_token":"offline-wire-synthetic-bearer"}}',
            'recover': '{"schema_version":1,"recovery_completed":true,"steps":[]}',
            'audit-sql': 'id\tversion\n3\t1\n',
            'broker': 'Listing queues for vhost / ...\nname\tmessages\nt44.notifications\t0\n',
            'fault': ''}
        inputs = {
            'init-user': (['--username', 'offline_a', '--display-name', 'Offline a'], 'offline-not-real\n'),
            'scheduler-scope': (['--project-id', 1], ''),
            'service-credential': (['--project-id', 1, '--ttl-seconds', 900], ''),
            'recover': ([], ''), 'audit-sql': ([], 'SELECT id,version FROM tasks'),
            'broker': (['queues'], ''),
            'fault': (['--service', 'api', '--action', 'stop', '--lease-seconds', 60], '')}
        for command, output in samples.items():
            argv, stdin = inputs[command]
            current = Completed(0, output); value = h.control(command, *argv, stdin=stdin)
            assert calls[-1] == {'argv': ['offline-python', 'offline-control', command, *map(str, argv)],
                'stdin': stdin, 'timeout': 180, 'capture_output': True}
            if command in ('audit-sql', 'broker'): assert value['native_text'] == output
            if command == 'fault': assert value['exit_code'] == 0 and value['json_receipt_available'] is False
            passed('documented-input-output-' + command)
            for name, failure in [('nonzero', Completed(7, output)),
                                  ('timeout', S.subprocess.TimeoutExpired(['offline-control'], 180))]:
                current = failure
                try: h.control(command, *argv, stdin=stdin)
                except (S.Blocked, S.subprocess.TimeoutExpired): passed(name + '-' + command + '-blocked')
                else: raise AssertionError(name + ' control was accepted')
        for command in ('init-user', 'scheduler-scope', 'recover', 'service-credential'):
            for name, output in [('empty', ''), ('mixed-text-json', 'progress\n' + samples[command]),
                    ('two-json-objects', samples[command] + samples[command]),
                    ('duplicate-key', '{"user_id":1,"user_id":2}'), ('array', '[]')]:
                current = Completed(0, output)
                try: h.control(command)
                except S.Blocked: passed(name + '-' + command + '-blocked')
                else:
                    # A duplicate key is always rejected; documented object requirements differ.
                    raise AssertionError(name + ' control was accepted')
        for output in ['{}', '{"user_id":true}', '{"user_id":1.0}', '{"user_id":0}',
                       '{"user_id":4294967296}', '{"user_id":1,"extra":2}']:
            current = Completed(0, output)
            try: h.control('init-user')
            except S.Blocked: passed('init-user-invalid-id-or-fields-blocked')
            else: raise AssertionError('Invalid user_id accepted')
        current = Completed(0, '{}')
        try: h.control('scheduler-scope')
        except S.Blocked: passed('scheduler-missing-fields-blocked')
        else: raise AssertionError('Missing scheduler fields accepted')
        for output in ['{}', '{"recovery_completed":1}', '{"recovery_completed":"true"}']:
            current = Completed(0, output)
            try: h.control('recover')
            except S.Blocked: passed('recovery-non-boolean-or-missing-blocked')
            else: raise AssertionError('Invalid recovery completion accepted')
        current = Completed(0, '{"recovery_completed":false,"error":"RECOVERY_FAILED"}')
        assert h.control('recover')['recovery_completed'] is False
        passed('false-recovery-remains-false')
        current = Completed(0, '{}')
        try: h.control('fault')
        except S.Blocked: passed('fault-nonempty-stdout-blocked')
        else: raise AssertionError('Nonempty fault receipt accepted')
        for command in ('audit-sql', 'broker'):
            current = Completed(0, '')
            try: h.control(command)
            except S.Blocked: passed('empty-native-text-' + command + '-blocked')
            else: raise AssertionError('Absent native receipt accepted')
        current = Completed(0, samples['audit-sql'])
        assert h.sql('SELECT id,version FROM tasks') == [{'id': 3, 'version': 1}]
        passed('mysql-batch-integer-typed-from-frozen-storage')
        current = Completed(0, 'id\tversion\n')
        assert h.sql('SELECT id,version FROM tasks') == []
        passed('mysql-batch-header-only-empty-result')
        current = Completed(0, 'id\tread_at\thandling_note\tdigest\n3\tNULL\tline1\\nline2\\tend\\\\path\t1234\n')
        assert h.sql('SELECT id,read_at,handling_note FROM notifications') == [
            {'id': 3, 'read_at': None, 'handling_note': 'line1\nline2\tend\\path', 'digest': '1234'}]
        passed('mysql-batch-null-escape-and-text-digit-preservation')
        for name, output in [('missing-header', ''), ('duplicate-columns', 'id\tid\n1\t2\n'),
                ('wrong-field-count', 'id\tversion\n1\n'), ('progress-prefix', 'warning text\nid\n1\n'),
                ('invalid-integer', 'id\nnot-an-id\n'), ('unknown-escape', 'handling_note\nabc\\q\n')]:
            current = Completed(0, output)
            try: h.sql('SELECT id FROM tasks')
            except S.Blocked: passed('mysql-batch-' + name + '-blocked')
            else: raise AssertionError('Ambiguous SQL batch output accepted: ' + name)
        current = Completed(0, samples['service-credential'])
        h.service(1); assert h.tokens['s'] == 'offline-wire-synthetic-bearer'
        passed('service-token-required-field-projection')
        current = Completed(0, '{"session_id":1}')
        try: h.service(1)
        except S.Blocked: passed('absent-service-token-blocked')
        else: raise AssertionError('Absent token was accepted')

    finally:
        S.urllib.request.urlopen, S.subprocess.run = original_open, original_run
        (target / 'offline-wire-selftest.json').write_text(json.dumps({'scope': 'Independent harness synthetic wire only',
            'network_used': False, 'application_imports': False, 'actual_SUT_cases': 0, 'results': results}, indent=2) + '\n')
        (target / 'synthetic-wire-samples.json').write_text(json.dumps({'project': envelope(project),
            'iteration': envelope(iteration), 'task_mutation': envelope({'task': task, 'audit_id': 1}),
            'task_read': envelope(task)}, indent=2) + '\n')
    return {'offline_wire_checks_passed': len(results), 'actual_SUT_cases': 0, 'network_used': False}

HERE = Path(__file__).resolve().parent

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def verify():
    manifest = json.loads((HERE / 'manifest.json').read_text())
    for name, expected in manifest['payload_files'].items():
        path = HERE / name
        assert path.is_file() and not path.is_symlink(), name + ': not a regular frozen file'
        assert digest(path) == expected, name + ': freeze hash mismatch'
    canonical = ''.join(name + '\0' + sha + '\n' for name, sha in sorted(manifest['payload_files'].items()))
    assert hashlib.sha256(canonical.encode()).hexdigest() == manifest['payload_set_sha256']
    packet = json.loads((HERE / 'neutral-inputs.json').read_text())
    inputs = {packet['freeze']['path']: packet['freeze']['sha256'], **packet['freeze']['files'],
              **packet['original_teacher_materials'], **packet['additional_neutral_policy'],
              **packet['approved_change_inputs']}
    for path, expected in inputs.items():
        assert digest(HERE / 'materials' / path) == expected, path + ': neutral source mismatch'
    r = packet['runtime_capability_document']
    assert digest(HERE / 'materials' / r['path']) == r['sha256']
    scripts = sorted(HERE.glob('*.py'))
    assert len(scripts) == 10
    assert {p.name.split('_')[0] for p in scripts} == {str(i) for i in range(874, 884)}
    for path in scripts:
        tree = ast.parse(path.read_text(), filename=str(path))
        compile(tree, str(path), 'exec')
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                assert all(not a.name.startswith(('t44', 'backend', 'frontend')) for a in node.names)
            if isinstance(node, ast.ImportFrom):
                assert not (node.module or '').startswith(('t44', 'backend', 'frontend'))
    contract = json.loads((HERE / 'materials/specs/contracts/openapi.json').read_text())
    assert contract['info']['version'] == '1.1.0'
    assert contract['components']['schemas']['Meta']['properties']['contract_version']['const'] == '1.1.0'
    assert len(contract['paths']) == 31 and len(contract['components']['schemas']) == 130
    assert sum(m in ('get', 'post', 'patch', 'put', 'delete') for pi in contract['paths'].values() for m in pi) == 38
    assert (HERE / 'materials/specs/contracts/openapi.json').read_bytes() == (HERE / 'materials/backend/t44/contracts/openapi.json').read_bytes()
    assert (HERE / 'materials/specs/database/schema.sql').read_bytes() == (HERE / 'materials/backend/t44/persistence/schema_v1.sql').read_bytes()
    cert = HERE / 'recipient.pem'
    subprocess.run(['openssl', 'x509', '-in', str(cert), '-noout', '-checkend', '3600'], check=True, capture_output=True)
    text = subprocess.check_output(['openssl', 'x509', '-in', str(cert), '-noout', '-text'], text=True)
    assert '3072 bit' in text or '3072-bit' in text
    assert [p.name for p in HERE.rglob('*.pem')] == ['recipient.pem']
    assert cert.read_text().startswith('-----BEGIN CERTIFICATE-----')
    return {'offline_verified': True, 'sut_accessed': False, 'payload_files': len(manifest['payload_files']),
            'payload_set_sha256': manifest['payload_set_sha256'], 'script_count': len(scripts)}

def decode_trace(path, output):
    """Lossless standalone metric/screenshot extraction for tester-only archived evidence."""
    source, target = Path(path), Path(output)
    target.mkdir(mode=0o700, parents=True, exist_ok=True)
    with (target / 'requests.csv').open('wb') as csv:
        header = False
        for number, line in enumerate(source.read_text().splitlines()):
            frame = json.loads(line)
            if frame.get('encoding') == 'gzip-base64-csv-v1':
                value = gzip.decompress(base64.b64decode(frame['payload']))
                assert hashlib.sha256(value).hexdigest() == frame['uncompressed_sha256']
                if not header:
                    csv.write((','.join(frame['columns']) + '\n').encode()); header = True
                csv.write(value)
            elif frame.get('kind') == 'real_browser_png':
                value = base64.b64decode(frame['payload']); assert len(value) == frame['bytes']
                (target / ('browser-' + str(number) + '.png')).write_bytes(value)

if __name__ == '__main__':
    if len(sys.argv) == 3 and sys.argv[1] == '--offline-wire-selftest':
        print(json.dumps(offline_wire_selftest(sys.argv[2]), sort_keys=True))
    elif len(sys.argv) == 4 and sys.argv[1] == '--decode-private-trace':
        decode_trace(sys.argv[2], sys.argv[3])
    else:
        print(json.dumps(verify(), sort_keys=True))
