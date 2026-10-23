"""Independent v3 support. Imports only own frozen material and standard/client libraries."""
import copy
import datetime as dt
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import secrets
import subprocess
import threading
import time
import urllib.error
import urllib.parse
import urllib.request

HERE = Path(__file__).resolve().parent
CONTRACT = json.loads((HERE / 'materials/specs/contracts/openapi.json').read_text())
OPS = {o['operationId']: (m.upper(), p, o) for p, pi in CONTRACT['paths'].items()
       for m, o in pi.items() if m in ('get', 'post', 'patch', 'put', 'delete')}
EVIDENCE = [{'kind': 2, 'locator': 'independent-v3/synthetic-fixture',
             'description': 'Synthetic test reference, not a verified human review'}]
REVISION = '1a' * 20
SECTIONS = ['scope_baseline', 'requirements_mapping', 'change_scope', 'compatibility',
            'correctness', 'evidence', 'findings', 'conclusion']
REASONS = dict(enumerate(['AUTH_REQUIRED', 'INVALID_CREDENTIALS', 'TOKEN_EXPIRED',
    'TOKEN_REVOKED', 'PROJECT_ACCESS_DENIED', 'ACTION_FORBIDDEN', 'SERVICE_SCOPE_REQUIRED',
    'RESOURCE_NOT_FOUND', 'PARAMETER_INVALID', 'INVALID_JSON', 'SECURITY_INPUT_REJECTED',
    'STATE_CONFLICT', 'VERSION_CONFLICT', 'IDEMPOTENCY_CONTENT_CONFLICT',
    'IDEMPOTENCY_IN_PROGRESS', 'DEPENDENCIES_UNSATISFIED', 'DEPENDENCY_SELF_REFERENCE',
    'DEPENDENCY_CYCLE', 'DEPENDENCY_EDIT_LOCKED', 'EVIDENCE_REQUIRED', 'REVIEW_NOT_PASSED',
    'REVIEW_BASELINE_MISMATCH', 'RELEASE_APPROVAL_REQUIRED', 'ASSESSMENT_BASELINE_MISMATCH',
    'OWNER_NOT_PROJECT_DEVELOPER', 'LAST_MANAGER', 'MEMBER_IN_USE', 'ACCOUNT_NOT_INITIALIZED',
    'TIME_RANGE_INVALID', 'CAPACITY_REFERENCE_INVALID', 'NOT_ELIGIBLE_FOR_ESCALATION',
    'SCHEDULE_VERSION_CONFLICT', 'RULE_VERSION_CONFLICT', 'CONTRACT_INVALID',
    'AUDIT_UNAVAILABLE', 'DEPENDENCY_UNAVAILABLE', 'TRANSACTION_UNCERTAIN', 'RATE_LIMITED',
    'PAYLOAD_TOO_LARGE', 'INTERNAL_ERROR', 'ASSIGNMENT_EDIT_LOCKED'], 1))
_OBSERVER = None

class Blocked(Exception):
    pass

def load_own(name):
    p = HERE / name
    spec = importlib.util.spec_from_file_location('private_' + p.stem, p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def check(test, message):
    if _OBSERVER is not None:
        _OBSERVER.observe_assertion(bool(test), message)
    if not test:
        raise AssertionError(message)

def utc(delta=0):
    return (dt.datetime.now(dt.timezone.utc) + dt.timedelta(seconds=delta)).isoformat(
        timespec='microseconds').replace('+00:00', 'Z')

def plan(end=86400 * 5, start=-86400, **kw):
    value = {'planned_start': utc(start), 'planned_end': utc(end), 'estimated_hours': 8,
             'buffer_hours': 1, 'delay_contingency': 'Synthetic manager reviews and replans'}
    value.update(kw)
    return value

def key():
    return 'iv3-' + secrets.token_hex(16)

class Recorder:
    def __init__(self, directory, group):
        self.directory = Path(directory)
        self.directory.mkdir(mode=0o700, parents=True, exist_ok=True)
        self.group = group
        self.results = []
        self.events = self.directory / 'events.jsonl'
        self.lock = threading.Lock()
        self.secrets = []
        self.active_case = 'preconditions'
        self.assertions = {}

    def observe_assertion(self, passed, criterion):
        with self.lock:
            group = self.assertions.setdefault(self.active_case, {'pass': 0, 'fail': 0, 'criteria': {}})
            group['pass' if passed else 'fail'] += 1
            detail = group['criteria'].setdefault(criterion, {'pass': 0, 'fail': 0})
            detail['pass' if passed else 'fail'] += 1

    def scrub(self, value):
        value = json.dumps(value, ensure_ascii=False, default=str)
        for secret in self.secrets:
            if secret:
                value = value.replace(secret, '[redacted]')
        return json.loads(value)

    def event(self, value):
        with self.lock:
            with self.events.open('a') as f:
                f.write(json.dumps(self.scrub({'at': utc(), **value}), ensure_ascii=False) + '\n')

    def run(self, case_id, fn):
        self.active_case = case_id
        if getattr(self, 'case_filter', None) and case_id not in self.case_filter:
            item = {'id': case_id, 'status': 'not_executed', 'reason': 'Bounded continuation excludes previously completed scope'}
            self.results.append(item)
            return item
        start = time.monotonic()
        try:
            fn()
            item = {'id': case_id, 'status': 'pass'}
        except Blocked as exc:
            item = {'id': case_id, 'status': 'capability_blocked', 'reason': str(exc)}
        except AssertionError as exc:
            item = {'id': case_id, 'status': 'fail_observed', 'reason': str(exc)}
        except Exception as exc:
            # An infrastructure/driver error is not a product defect.
            item = {'id': case_id, 'status': 'execution_error', 'type': type(exc).__name__}
        item['elapsed_seconds'] = round(time.monotonic() - start, 6)
        self.results.append(item)
        self.event({'kind': 'case_result', **item})
        return item

    def finish(self, extra=None):
        counts = {s: sum(r['status'] == s for r in self.results) for s in
                  ('pass', 'fail_observed', 'execution_error', 'capability_blocked', 'not_executed')}
        result = {'round': 'v3', 'group': self.group, 'finished_at': utc(), 'counts': counts,
                  'results': self.results, 'human_participation': 'none; synthetic automated actors',
                  'subassertions': self.assertions,
                  'unreached_assertions': 'After any failed/blocked whole case, remaining statements are unexecuted, never inferred passing',
                  'scope_limit': 'Only named executed subcases; no whitebox or deliverable verdict',
                  **(extra or {})}
        (self.directory / 'results.json').write_text(json.dumps(self.scrub(result), indent=2,
                                                               ensure_ascii=False))
        rows = ['# Independent v3 private execution record', '',
                'Automated synthetic users. Not a human approval or coursework completion claim.', '',
                f'Group: {self.group}', '', json.dumps(counts), '']
        rows += [f"- {r['id']}: {r['status']}" for r in self.results]
        (self.directory / 'report.md').write_text('\n'.join(rows) + '\n')
        return 1 if counts['fail_observed'] or counts['execution_error'] else 2 if counts['capability_blocked'] else 0

class Harness:
    def __init__(self, group='functional'):
        load_own('874_verify.py').verify()
        context_path = os.environ.get('T44_ACCEPTANCE_CONTEXT')
        if not context_path:
            raise Blocked('No coordinator-bound neutral execution context; no SUT selected')
        self.c = json.loads(Path(context_path).read_text())
        sha = self.c.get('product_source_sha', '')
        check(re.fullmatch(r'[0-9a-f]{40}', sha), 'Context requires exact product SHA')
        # Never infer or select the local HEAD as product version.
        self.rec = Recorder(self.c['harness_output_directory'], group)
        self.rec.case_filter = self.c.get('selected_case_ids')
        global _OBSERVER
        _OBSERVER = self.rec
        self.rec.event({'kind': 'binding', 'product_source_sha': sha,
                        'harness_group': group, 'spec_version': '1.1.0'})
        self.base = self.c['api_base_url'].rstrip('/')
        if urllib.parse.urlsplit(self.base).path in ('', '/'):
            self.base += '/api/v1'
        self.tokens = {}
        self.users = {}
        self.credentials = {}
        self.covered = set()
        self.local = threading.local()
        try:
            from jsonschema import Draft202012Validator, FormatChecker
        except ImportError:
            raise Blocked('Neutral execution Python requires the locked jsonschema client; no application import or unlocked install substituted')
        self.validator_cls = Draft202012Validator
        self.formats = FormatChecker()

    def control(self, *args, stdin=''):
        argv = [self.c['python'], self.c['control_cli'], *map(str, args)]
        env = os.environ.copy()
        if 'control_state' in self.c:
            env['T44_ACCEPTANCE_STATE'] = self.c['control_state']
        p = subprocess.run(argv, input=stdin, text=True, capture_output=True,
                           env=env, timeout=180)
        self.rec.event({'kind': 'control_io_boundary', 'command': args[0], 'exit_code': p.returncode,
                        'stdout_bytes': len(p.stdout.encode()), 'stderr_bytes': len(p.stderr.encode())})
        if p.returncode:
            raise Blocked('Neutral control failed with actual nonzero exit: ' + str(args[0]) + ':' + str(p.returncode))
        try:
            value = json.loads(p.stdout)
        except Exception:
            if not p.stdout.strip() and args[0] in ('init-user', 'scheduler-scope', 'fault'):
                # README does not promise JSON for these commands. This is an exact exit receipt,
                # not a fabricated operation/business result. Account identity is separately
                # established by real login; recovery/SQL/service-token keep strict JSON boundaries.
                return {'command': args[0], 'exit_code': 0, 'json_receipt_available': False}
            raise Blocked('Control did not return the documented JSON receipt: ' + str(args[0]))
        return value

    def sql(self, query):
        check(query.lstrip().upper().startswith(('SELECT ', 'SHOW ', 'EXPLAIN ')),
              'Independent observer permits read-only SQL only')
        if self.c.get('local_readonly_credentials_file'):
            import pymysql
            credentials = json.loads(Path(self.c['local_readonly_credentials_file']).read_text())
            check(credentials['database'] == 't44_ui_v3', 'Local observer is restricted to this exact independent database')
            conn = pymysql.connect(**credentials, cursorclass=pymysql.cursors.DictCursor,
                                   autocommit=True, read_timeout=5, write_timeout=5)
            try:
                with conn.cursor() as cursor:
                    cursor.execute('SET SESSION TRANSACTION READ ONLY')
                    cursor.execute(query)
                    return list(cursor.fetchall())
            finally:
                conn.close()
        value = self.control('audit-sql', stdin=query)
        # Operational receipt envelope is unspecified. Accept common JSON row envelopes;
        # no value normalization or expected-result substitution occurs here.
        def rows_from(rows, envelope):
            if rows and isinstance(rows[0], (list, tuple)):
                cols = envelope.get('columns') if isinstance(envelope, dict) else None
                if not isinstance(cols, list):
                    raise Blocked('SQL positional row receipt needs neutral columns binding')
                names = [x if isinstance(x, str) else x.get('name') for x in cols]
                if not all(isinstance(x, str) for x in names):
                    raise Blocked('SQL column metadata names unavailable')
                return [dict(zip(names, row)) for row in rows]
            return rows
        if isinstance(value, list):
            return rows_from(value, {})
        if isinstance(value, dict):
            for k in ('rows', 'result', 'data'):
                if isinstance(value.get(k), list):
                    return rows_from(value[k], value)
                if isinstance(value.get(k), dict) and isinstance(value[k].get('rows'), list):
                    return rows_from(value[k]['rows'], value[k])
        raise Blocked('SQL receipt row envelope needs neutral schema binding')

    def valid(self, schema, value):
        root = {'$schema': 'https://json-schema.org/draft/2020-12/schema',
                'components': CONTRACT['components'], **schema}
        errors = list(self.validator_cls(root, format_checker=self.formats).iter_errors(value))
        check(not errors, 'HTTP content violates frozen response schema at ' +
              (str(list(errors[0].path)) + ': ' + errors[0].validator if errors else ''))

    def request(self, op_id, actor='m', body=None, ids=None, query=None, idem=None,
                raw=None, expected=None, code=None, auth=True, record=True):
        method, path, op = OPS[op_id]
        ids = ids or {}
        for field in re.findall(r'{([^}]+)}', path):
            check(field in ids, 'Missing independently supplied path ID ' + field)
            path = path.replace('{' + field + '}', urllib.parse.quote(str(ids[field]), safe=''))
        url = self.base + path + ('?' + urllib.parse.urlencode(query) if query else '')
        headers = {'Accept': 'application/json', 'X-Request-ID': key()}
        if auth and actor in self.tokens:
            headers['Authorization'] = 'Bearer ' + self.tokens[actor]
        write = any((p.get('name') == 'Idempotency-Key' or
                     p.get('$ref', '').endswith('/IdempotencyKey')) for p in op.get('parameters', []))
        # Resolve parameter aliases instead of guessing which writes are idempotent.
        for p in op.get('parameters', []):
            if '$ref' in p:
                p = CONTRACT['components']['parameters'][p['$ref'].split('/')[-1]]
            write = write or p.get('name') == 'Idempotency-Key'
        if write and idem is not False:
            headers['Idempotency-Key'] = idem or key()
        data = raw if raw is not None else json.dumps(body, separators=(',', ':')).encode() if body is not None else None
        if data is not None:
            headers['Content-Type'] = 'application/json'
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        start = time.perf_counter()
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                status, rh, content = resp.status, dict(resp.headers), resp.read()
        except urllib.error.HTTPError as resp:
            status, rh, content = resp.code, dict(resp.headers), resp.read()
        elapsed = (time.perf_counter() - start) * 1000
        try:
            value = json.loads(content)
        except Exception:
            raise AssertionError(f'{op_id} HTTP {status} is not the JSON contract')
        check(str(status) in op['responses'], f'{op_id} undeclared HTTP {status}')
        rs = op['responses'][str(status)]['content']['application/json']['schema']
        self.valid(rs, value)
        if expected is not None:
            statuses = expected if isinstance(expected, (list, tuple, set)) else [expected]
            check(status in statuses, f'{op_id}: expected HTTP {statuses}; actual {status}/{value.get("code")}')
        if code:
            codes = code if isinstance(code, (list, tuple, set)) else [code]
            check(value.get('code') in codes, f'{op_id}: expected {codes}; actual {value.get("code")}')
        for secret in self.rec.secrets:
            if op_id != 'login':
                check(secret not in content.decode(errors='replace'), 'Secret disclosed in ordinary HTTP content')
        item = {'operation': op_id, 'status': status, 'ms': round(elapsed, 3),
                'request_id': value.get('meta', {}).get('request_id', value.get('request_id')),
                'ids': ids, 'body_sha256': hashlib.sha256(data or b'').hexdigest(),
                'response_sha256': hashlib.sha256(content).hexdigest(), 'code': value.get('code')}
        if record:
            self.rec.event({'kind': 'http', **item})
        self.local.last = (status, value, rh, item)
        self.covered.add(op_id)
        return value

    def data(self, *a, **kw):
        return self.request(*a, **kw)['data']

    def setup_users(self):
        c = json.loads(Path(self.c['manager_credentials_file']).read_text())
        if isinstance(c.get('manager'), dict): c = c['manager']
        if isinstance(c.get('credentials'), dict) and all(k in c['credentials'] for k in ('username', 'password')):
            c = c['credentials']
        if not all(k in c for k in ('username', 'password')):
            raise Blocked('Manager private file requires neutral username/password field binding')
        self.credentials['m'] = {k: c[k] for k in ('username', 'password')}
        self.rec.secrets.append(c['password'])
        pool = None
        if self.c.get('additional_accounts_file'):
            pool = iter(json.loads(Path(self.c['additional_accounts_file']).read_text())['accounts'].values())
        for label in ('a', 'b', 'r', 'o', 'n'):
            if pool is not None:
                account = next(pool)
                self.credentials[label] = {k: account[k] for k in ('username', 'password')}
                self.rec.secrets.append(account['password'])
                continue
            username = 'iv3_' + label + '_' + secrets.token_hex(5)
            password = secrets.token_urlsafe(32)
            self.rec.secrets.append(password)
            self.control('init-user', '--username', username, '--display-name', 'Synthetic ' + label,
                         stdin=password + '\n')
            self.credentials[label] = {'username': username, 'password': password}
        self.display_names = {}
        for label, credentials in self.credentials.items():
            d = self.data('login', auth=False, body=credentials, expected=200)
            self.tokens[label] = d['access_token']
            self.rec.secrets.append(d['access_token'])
            self.users[label] = d['user']['id']
            self.display_names[label] = d['user']['display_name']

    def fixture(self, capacities=('a', 'b'), title=None):
        p = self.data('createProject', body={'name': title or 'Independent v3 ' + key()}, expected=201)
        pid = p['id']
        ids = {'project_id': pid}
        for who, roles in [('a', [2, 3]), ('b', [2]), ('r', [3]), ('n', [1])]:
            self.data('addProjectMember', body={'username': self.credentials[who]['username'],
                      'roles': roles, 'reason': 'Synthetic test role'}, ids=ids, expected=201)
        ip = {'name': 'Synthetic iteration', 'planned_start': utc(-86400 * 5),
              'planned_end': utc(86400 * 10), 'capacity': [
                  {'user_id': self.users[w], 'available_hours': 80} for w in capacities],
              'buffer_hours': 2, 'delay_contingency': 'Manager revises schedule with evidence'}
        iteration = self.data('createIteration', ids=ids, body=ip, expected=201)
        return {'p': pid, 'i': iteration['id'], 'iteration': iteration}

    def ids(self, fixture, task=None, **extra):
        value = {'project_id': fixture['p']}
        if task is not None:
            value['task_id'] = task['id'] if isinstance(task, dict) else task
        return {**value, **extra}

    def task(self, f, who='a', deps=None, timing=None, title=None):
        return self.data('createTask', ids=self.ids(f), expected=201, body={
            'title': title or 'Synthetic ' + key(), 'iteration_id': f['i'],
            'owner_id': self.users[who], 'plan': timing or plan(), 'dependency_task_ids': deps or []})

    def get(self, f, t, actor='m'):
        return self.data('getTask', actor=actor, ids=self.ids(f, t), expected=200)

    def trans(self, f, t, action, actor='m', **extra):
        return self.data('transitionTask', actor=actor, ids=self.ids(f, t), expected=200,
                         body={'expected_version': t['version'], 'action': action, **extra})['task']

    def iteration_change(self, f, people, expected=200):
        old = f['iteration']
        body = {'expected_version': old['version'], 'plan': copy.deepcopy(old['plan']),
                'reason': 'Synthetic capacity change', 'evidence': EVIDENCE}
        body['plan']['capacity'] = [{'user_id': self.users[w], 'available_hours': 80} for w in people]
        value = self.request('changeIteration', ids=self.ids(f, iteration_id=f['i']),
                             body=body, expected=expected)
        if expected == 200:
            f['iteration'] = value['data']
        return value, body

    def review_body(self, t, verdict=1):
        return {'expected_version': t['version'], 'template_version': 1,
                'artifact_revision': REVISION, 'sections': [
                    {'section_id': s, 'content': 'Synthetic evidence section ' + s, 'evidence': EVIDENCE}
                    for s in SECTIONS], 'checklist': [
                    {'item_id': 'R%02d' % i, 'judgment': 1 if verdict == 1 else 2,
                     'rationale': 'Synthetic test judgment', 'evidence': EVIDENCE} for i in range(1, 11)],
                'verdict': verdict}

    def to_review(self, f, t):
        t = self.trans(f, t, 1, actor='a')
        return self.trans(f, t, 4, actor='a', artifact_revision=REVISION, evidence=EVIDENCE)

    def to_ready(self, f, t):
        if t['state'] == 1:
            t = self.to_review(f, t)
        d = self.data('createTaskReview', actor='r', ids=self.ids(f, t),
                      body=self.review_body(t), expected=201)
        return self.trans(f, d['task'], 5, actor='r', review_id=d['review']['id'],
                          review_version=d['review']['version'])

    def assessment_body(self, t):
        return {'expected_version': t['version'], 'risks': [
            {'perspective': p, 'severity': 1, 'risk': 'Synthetic perspective ' + str(p),
             'mitigation': 'Synthetic mitigation', 'evidence': EVIDENCE} for p in range(1, 5)],
            'rollback_plan': {'target_version': 'synthetic-before', 'trigger': 'Synthetic trigger',
                'steps': ['Synthetic bounded rollback record'], 'impact': 'Synthetic impact',
                'verification': 'Synthetic verification reference',
                'responsible_user_id': self.users['a'], 'evidence': EVIDENCE}}

    def assessed(self, f, t):
        d = self.data('createReleaseAssessment', ids=self.ids(f, t),
                      body=self.assessment_body(t), expected=201)
        t, a = d['task'], d['assessment']
        d = self.data('reviewReleaseAssessment', actor='r', ids=self.ids(f, t, assessment_id=a['id']),
                      body={'expected_version': t['version'], 'expected_assessment_version': a['version'],
                            'verdict': 1, 'reason': 'Synthetic separated assessment reviewer',
                            'evidence': EVIDENCE}, expected=200)
        return d['task'], d['assessment']

    def delivered(self, f, t):
        t = self.to_ready(f, t)
        t, a = self.assessed(f, t)
        t = self.trans(f, t, 7, assessment_id=a['id'], assessment_version=a['version'],
                       release_version='synthetic-release', reason='Automated synthetic manager decision',
                       evidence=EVIDENCE)
        return t, a

    def rolled(self, f, t):
        t, a = self.delivered(f, t)
        return self.trans(f, t, 8, assessment_id=a['id'], rollback_plan_version=a['rollback_plan_version'],
                          target_version=a['rollback_plan']['target_version'], impact='Synthetic impact',
                          reason='Automated synthetic rollback decision', evidence=EVIDENCE), a

    def unchanged(self, f, before):
        check(self.get(f, before) == before, 'Rejected request changed authoritative task snapshot')

    def audit(self, response, expected_outcome, expected_reason=None):
        aid = response.get('audit_id', response.get('data', {}).get('audit_id'))
        check(isinstance(aid, int), 'Completed action/rejection must carry durable audit ID')
        rows = self.sql('SELECT id,outcome,reason_code,request_id,before_values,after_values '
                        'FROM audit_events WHERE id=' + str(aid))
        check(len(rows) == 1, 'Audit ID not durably observable through independent read connection')
        row = rows[0]
        check(row['outcome'] == expected_outcome, 'Audit outcome mismatch')
        if expected_reason:
            check(REASONS.get(row['reason_code']) == expected_reason, 'Durable rejection reason mismatch')
        return row

    def service(self, pid, label='s', ttl=900):
        value = self.control('service-credential', '--project-id', pid, '--ttl-seconds', ttl)
        candidates = [value] + [x for x in value.values() if isinstance(x, dict)] if isinstance(value, dict) else []
        tok = next((x[k] for x in candidates for k in ('access_token', 'token', 'bearer')
                    if isinstance(x.get(k), str)), None)
        if not tok:
            raise Blocked('Service credential receipt requires neutral token field binding')
        self.tokens[label] = tok
        self.rec.secrets.append(tok)
        return label

    def wait(self, predicate, seconds=45, interval=.5):
        end = time.monotonic() + seconds
        while time.monotonic() < end:
            result = predicate()
            if result:
                return result
            time.sleep(interval)
        raise AssertionError('Documented eventual observation absent within diagnostic budget; no formal SLA inferred')
