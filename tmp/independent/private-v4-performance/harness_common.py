"""Independent performance driver. No application imports; run only after separate source binding."""
import asyncio
import collections
import gzip
import hashlib
import json
import math
import os
from pathlib import Path
import re
import resource
import secrets
import struct
import subprocess
import sys
import time
import traceback
import uuid
from datetime import datetime, timedelta, timezone

import httpx
from jsonschema import Draft202012Validator, FormatChecker

HERE = Path(__file__).resolve().parent
SPEC = json.loads((HERE / 'inputs/openapi.json').read_text())
FMT = FormatChecker()
EVIDENCE = [{'kind': 2, 'locator': 'synthetic/performance-v4/fixture',
             'description': 'Generated performance fixture; no student or production action asserted'}]
ARTIFACT = hashlib.sha1(b'independent synthetic performance v4').hexdigest()
FRAME = struct.Struct('<QIHHIHHII')
# start microseconds, elapsed microseconds, VU, opcode, sequence, status, flags,
# fixture ordinal (0..5999; 0xffffffff if none), input expected_version (0 if none).
OPS = {'setup': 1, 'plan_prepare': 2, 'transition': 10, 'query_detail': 11,
       'query_list': 12, 'query_history': 13, 'contract_valid': 20,
       'contract_reject': 21, 'escalation_new': 30, 'escalation_duplicate': 31,
       'notification_query': 32, 'postcheck': 40}
PHASE = {'setup': 0, 'warmup': 1, 'steady': 2, 'postcheck': 3}


def utc():
    return datetime.now(timezone.utc).isoformat(timespec='microseconds').replace('+00:00', 'Z')


def at(value):
    return value.isoformat(timespec='microseconds').replace('+00:00', 'Z')


def sha(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                    ensure_ascii=False).encode()).hexdigest()


class Evidence:
    def __init__(self, output, mode):
        self.output = Path(output)
        self.output.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.raw = gzip.open(self.output / 'trace.log', 'wb', compresslevel=6)
        self.raw.write(b'T44PV4\x00\x01' + struct.pack('<I', FRAME.size))
        self.events = gzip.open(self.output / 'events.jsonl', 'wt', compresslevel=6)
        self.origin = time.perf_counter_ns()
        self.mode = mode
        self.stats = {}
        self.report = {'schema_version': 1, 'test_number': mode, 'status': 'NOT_RUN',
                       'source_bound': False, 'started_at': utc(), 'failure': None,
                       'observations': {}, 'phases': {}, 'limits': [], 'fixture': {},
                       'events_encoding': 'gzip JSONL despite fixed archive filename events.jsonl',
                       'raw_format': {'path': 'trace.log', 'encoding': 'gzip binary',
                                      'magic_hex': '5434345056340001', 'struct': '<QIHHIHHII',
                                      'fields': ['start_us', 'latency_us', 'vu', 'opcode', 'sequence',
                                                 'http_status', 'flags', 'fixture_ordinal',
                                                 'input_expected_version'],
                                      'flags': {'0': 'pass', 'bit0': 'failure', 'bits1-2': 'phase',
                                                'bit3': 'expected rejection'}, 'opcodes': OPS}}
        self.count = 0

    def event(self, kind, **data):
        self.events.write(json.dumps({'at': utc(), 'kind': kind, **data}, ensure_ascii=False,
                                     separators=(',', ':')) + '\n')
        if kind != 'accepted_event':
            self.events.flush()

    def record(self, phase, op, vu, seq, ordinal, version, started, elapsed, status,
               failure, expected_reject):
        flags = PHASE[phase] * 2 + bool(failure) + (8 if expected_reject else 0)
        micros = max(0, math.ceil(elapsed / 1000))
        self.raw.write(FRAME.pack((started - self.origin) // 1000, micros, vu, OPS[op], seq,
                                 status or 0, flags, ordinal if ordinal is not None else 0xffffffff,
                                 version or 0))
        self.count += 1
        key = (phase, op)
        if key not in self.stats:
            self.stats[key] = {'latency_us': [], 'failed': 0, 'status': collections.Counter(),
                               'completions': collections.Counter(), 'issued': 0,
                               'successful_completed_in_window': 0}
        row = self.stats[key]
        row['latency_us'].append(micros)
        row['issued'] += 1
        row['failed'] += bool(failure)
        row['status'][str(status or 0)] += 1
        steady = self.report['phases'].get('steady')
        if phase == 'steady' and steady:
            completed = (started + elapsed - steady['start_ns']) / 1e9
            if 0 <= completed < 600:
                row['completions'][int(completed // 60)] += not bool(failure)
                row['successful_completed_in_window'] += not bool(failure)

    def finish(self):
        groups = {}
        for (phase, op), row in self.stats.items():
            values = sorted(row.pop('latency_us'))
            count = len(values)
            row.update(n=count, p50_ms=values[math.ceil(count * .50)-1]/1000,
                       p95_ms=values[math.ceil(count * .95)-1]/1000,
                       p99_ms=values[math.ceil(count * .99)-1]/1000,
                       max_ms=values[-1]/1000, mean_ms=sum(values)/count/1000)
            completed_by_minute = row.pop('completions')
            row['minute_completed_success'] = [completed_by_minute[i] for i in range(10)]
            groups[f'{phase}/{op}'] = row
        self.report['statistics'] = groups
        self.report['finished_at'] = utc()
        self.raw.close()
        self.events.close()
        raw_path = self.output / 'trace.log'
        self.report['raw_records'] = self.count
        self.report['raw_sha256'] = hashlib.sha256(raw_path.read_bytes()).hexdigest()
        self.report['raw_size_bytes'] = raw_path.stat().st_size
        if any((self.output / name).stat().st_size > 20 * 1024 * 1024
               for name in ['trace.log', 'events.jsonl']):
            self.report['status'] = 'INCOMPLETE_EVIDENCE'
            self.report['limits'].append('Archive per-file capacity exceeded; no passing conclusion permitted.')
        (self.output / 'results.json').write_text(json.dumps(self.report, ensure_ascii=False, indent=2) + '\n')
        (self.output / 'report.md').write_text(
            '# Independent performance v4\n\n'
            f"Test: {self.mode}. Status: {self.report['status']}.\n\n"
            'Only this performance class is commissioned. Raw requests and timings are in trace.log '
            '(gzip binary; decoder frozen with harness); events.jsonl (gzip JSONL) contains exact fixture mapping, '
            'control and sampling records; results.json contains binding, criteria and observations. '
            'No full functional acceptance, source coverage, student activity, or production decision is claimed.\n')


class Driver:
    def __init__(self, mode):
        context_path = os.environ.get('T44_ACCEPTANCE_CONTEXT')
        if not context_path:
            raise RuntimeError('No separately bound hosted acceptance context; execution prohibited.')
        self.context = json.loads(Path(context_path).read_text())
        source = self.context.get('product_source_sha', '')
        if not re.fullmatch('[0-9a-f]{40}', source):
            raise RuntimeError('Exact separately bound product SHA required.')
        if self.context.get('api_base_url') != 'http://127.0.0.1:18082/api/v1':
            raise RuntimeError('Only the declared isolated loopback reverse-proxy origin is permitted.')
        self.mode = mode
        self.e = Evidence(self.context['harness_output_directory'], mode)
        self.e.report.update(source_bound=True, product_source_sha=source,
                             harness_commit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
                             input_hash_manifest_sha256=hashlib.sha256((HERE/'inputs/source-hashes.json').read_bytes()).hexdigest())
        self.client = httpx.AsyncClient(base_url=self.context['api_base_url'], trust_env=False, http2=False,
                                       timeout=httpx.Timeout(5.0),
                                       limits=httpx.Limits(max_connections=800, max_keepalive_connections=800))
        self.validators = {}
        self.projects = []
        self.tasks = []
        self.dev = []
        self.manager = None
        self.reviewer = None
        self.service = None
        self.run_id = str(uuid.uuid4())
        self.phase = 'setup'
        self.inflight = collections.Counter()
        self.active_users = 0
        self.steady_end = None
        self.new_events = {}
        self.histories = {}
        self.e.report['limits'] = [
            '400 closed-loop virtual users; maximum one outstanding HTTP request per user; this is not 400 simultaneous server executions.',
            'Same hosted runner origin is observed via loopback; physical hardware placement beyond reported daemon metadata is unknown.',
            'Background consumer, 60-second bootstrap-scoped scanner and health probes remain; other traffic attribution is unknown.',
            'Per-service RSS is unavailable. Optional neutral runtime-usage snapshots, when explicitly declared, retain Docker CLI units/limitations and never establish whole-window peaks.',
            'Synthetic evidence references and manager decisions are fixture data, not student actions or real releases.'
        ]

    def key(self, phase, vu, seq, suffix=''):
        return f'pv4-{self.mode}-{self.run_id}-{phase}-{vu}-{seq}-{suffix}'[:128]

    async def control(self, *args, stdin=None, timeout=60, secret=False, allow_nonzero=False):
        started = time.perf_counter_ns()
        env = dict(os.environ)
        env['T44_ACCEPTANCE_STATE'] = self.context['control_state']
        proc = await asyncio.create_subprocess_exec(self.context['python'], self.context['control_cli'], *args,
                                                    stdin=asyncio.subprocess.PIPE,
                                                    stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
                                                    env=env)
        try:
            out, err = await asyncio.wait_for(proc.communicate(stdin.encode() if stdin else None), timeout)
        except BaseException:
            proc.kill()
            await proc.wait()
            self.e.event('control_failure', command=args[0], error='TIMEOUT_OR_CANCEL')
            raise
        self.e.event('control', command=args[0], argv=list(args), stdin_recorded=False, returncode=proc.returncode,
                     elapsed_ms=(time.perf_counter_ns()-started)/1e6,
                     stdout_sha256=None if secret else hashlib.sha256(out).hexdigest(),
                     stderr_bytes=len(err))
        if allow_nonzero:
            return proc.returncode, out.decode()
        if proc.returncode:
            raise RuntimeError('Neutral control failed: ' + args[0])
        return out.decode()

    def validate_response(self, method, route, status, body):
        key = (method.lower(), route, str(status))
        if key not in self.validators:
            schema = SPEC['paths'][route][method.lower()]['responses'][str(status)]['content']['application/json']['schema']
            self.validators[key] = Draft202012Validator({'$ref': '#/$defs/result', '$defs': {'result': schema},
                                                         'components': SPEC['components']}, format_checker=FMT)
        self.validators[key].validate(body)

    async def request(self, method, path, token, payload=None, status=200, op='setup', vu=65535,
                      seq=0, ordinal=None, version=None, route=None, expect_code=None, semantic=None):
        phase = self.phase
        if phase in ('warmup','steady') and time.perf_counter_ns() >= self.phase_deadline:
            return None
        headers = {'Authorization': 'Bearer ' + token} if token else {}
        if method in ('POST', 'PATCH') and path not in ('/auth/login', '/auth/logout') and '/contract-validations' not in path:
            headers['Idempotency-Key'] = self.key(phase, vu, seq, str(ordinal) + '-' + op)
            if op == 'setup':
                headers['Idempotency-Key'] += '-' + secrets.token_hex(6)
        started = time.perf_counter_ns()
        self.inflight[op] += 1
        actual, body, failure, elapsed = 0, None, None, 0
        try:
            response = await asyncio.wait_for(self.client.request(method, path, json=payload, headers=headers), 5.0)
            elapsed = time.perf_counter_ns() - started
            actual = response.status_code
            body = response.json()
            if actual != status:
                raise AssertionError(f'HTTP status {actual}; expected {status}')
            if expect_code and body.get('code') != expect_code:
                raise AssertionError('Unexpected contract rejection code')
            if actual < 300:
                meta = body['meta']
                if meta['contract_version'] != '1.1.0' or meta['replayed'] is not False:
                    raise AssertionError('Contract metadata or unexpected idempotency replay')
                if response.headers.get('cache-control') != 'no-store':
                    raise AssertionError('Missing authenticated no-store response header')
            if route and (self.mode == 867 or seq == 1 or seq % 1000 == 0 or phase in ('setup', 'postcheck')):
                self.validate_response(method, route, actual, body)
            if semantic:
                semantic(body)
        except asyncio.CancelledError:
            failure = 'CancelledError'
            elapsed = time.perf_counter_ns() - started
            self.e.event('request_cancelled', phase=phase, op=op, vu=vu, seq=seq, ordinal=ordinal)
            raise
        except Exception as error:
            if not elapsed:
                elapsed = time.perf_counter_ns() - started
            failure = type(error).__name__ + ': ' + str(error)[:200]
            # No headers, credentials, arbitrary response strings or request bodies enter evidence.
            self.e.event('request_failure', phase=phase, op=op, vu=vu, seq=seq, ordinal=ordinal,
                         expected_version=version, status=actual, failure_type=type(error).__name__,
                         expected_status=status, error_code=body.get('code') if isinstance(body, dict) else None,
                         response_sha256=sha(body) if body is not None and path!='/auth/login' else None,
                         input_sha256=sha(payload) if payload is not None and path!='/auth/login' else None)
        finally:
            self.inflight[op] -= 1
            self.e.record(phase, op, vu, seq, ordinal, version, started, elapsed, actual,
                          failure, expect_code is not None)
        if failure:
            if phase in ('setup', 'postcheck'):
                raise RuntimeError('Prerequisite/postcheck HTTP failure (' + op + ')')
            return None
        return body

    async def login(self, username, password):
        r = await self.request('POST', '/auth/login', None, {'username': username, 'password': password})
        return {'id': r['data']['user']['id'], 'token': r['data']['access_token'], 'username': username}

    def plan(self, end=None, width=0):
        if end is None:
            end = self.anchor + timedelta(days=3, seconds=width)
        return {'planned_start': at(end-timedelta(days=1)), 'planned_end': at(end),
                'estimated_hours': 8.25, 'buffer_hours': 2.0,
                'delay_contingency': 'Synthetic manager reschedules with retained evidence'}

    def assessment(self, version, owner):
        return {'expected_version': version,
                'risks': [{'perspective': k, 'severity': 1, 'risk': 'Synthetic fixture risk',
                           'mitigation': 'Synthetic mitigation', 'evidence': EVIDENCE} for k in range(1,5)],
                'rollback_plan': {'target_version': 'synthetic-baseline-v1', 'trigger': 'Synthetic rollback trigger',
                                  'steps': ['Synthetic offline plan only'], 'impact': 'Synthetic scope',
                                  'verification': 'Synthetic fixture confirmation',
                                  'responsible_user_id': owner, 'evidence': EVIDENCE}}

    async def transition(self, task, actor, action, fields=None, op='setup', vu=65535, seq=0):
        version = task['version']
        destination = {1:2,2:3,3:task.get('blocked_from_state'),4:4,5:5,6:2,7:6,8:7,9:2}[action]
        def semantic(value):
            changed = value['data']['task']
            if changed['version'] != version+1 or changed['state'] != destination:
                raise AssertionError('Transition acknowledgement version/state mismatch')
            if value['data']['audit_id'] < 1:
                raise AssertionError('Transition acknowledgement lacks durable audit identity')
        r = await self.request('POST', f"/projects/{task['project_id']}/tasks/{task['id']}/transitions",
                               actor['token'], {'expected_version': version, 'action': action, **(fields or {})},
                               op=op, vu=vu, seq=seq, ordinal=task['ordinal'], version=version,
                               route='/projects/{project_id}/tasks/{task_id}/transitions', semantic=semantic)
        if r:
            new = r['data']['task']
            task.update(new)
        return r

    async def fixture(self):
        self.anchor = datetime.now(timezone.utc)
        manager = json.loads(Path(self.context['manager_credentials_file']).read_text())
        self.manager = {'id': manager['user_id'], 'token': manager['access_token'], 'username': manager['username']}
        # One isolated bootstrap project remains empty and scanner-scoped. Create exactly 40 workload projects.
        async def init(index):
            username = f'pv4-{self.mode}-{index:02d}'
            password = secrets.token_urlsafe(36)
            raw = await self.control('init-user', '--username', username, '--display-name', 'Synthetic performance user',
                                     stdin=password+'\n', secret=True)
            uid = json.loads(raw)['user_id']
            user = await self.login(username, password)
            if uid != user['id']:
                raise RuntimeError('Account receipt and authenticated identity mismatch')
            return user
        # CLI container startups are bounded to four simultaneous neutral commands.
        accounts = []
        for index in range(0,19,4):
            accounts.extend(await asyncio.gather(*(init(i) for i in range(index,min(index+4,19)))))
        self.dev, self.reviewer = accounts[:18], accounts[18]
        self.by_id = {u['id']: u for u in self.dev}
        template = None

        async def build_project(p):
            nonlocal template
            r = await self.request('POST', '/projects', self.manager['token'],
                                   {'name': f'Synthetic perf v4 {self.mode} project {p:02d}',
                                    'description': 'Independent generated performance fixture only'}, status=201)
            pid = r['data']['id']
            for user in accounts:
                await self.request('POST', f'/projects/{pid}/members', self.manager['token'],
                                   {'username': user['username'], 'roles': [2] if user in self.dev else [3],
                                    'reason': 'Synthetic performance fixture'}, status=201)
            r = await self.request('POST', f'/projects/{pid}/iterations', self.manager['token'],
                                   {'name': 'Synthetic iteration', 'planned_start': at(self.anchor-timedelta(days=120)),
                                    'planned_end': at(self.anchor+timedelta(days=120)),
                                    'capacity': [{'user_id': u['id'], 'available_hours': 1000} for u in self.dev],
                                    'buffer_hours': 8, 'delay_contingency': 'Synthetic contingency'}, status=201)
            iteration = r['data']['id']
            tr = await self.request('GET', f'/projects/{pid}/review-template', self.manager['token'])
            t = tr['data']
            if template is None:
                template = t
            local = []
            for q in range(150):
                ordinal = p*150+q
                owner = self.dev[(p+q)%18]
                deps = [local[k]['id'] for k in (20,21,22)] if q >= 75 else []
                payload = {'title': f'Synthetic task {ordinal:04d}',
                           'description': ('Synthetic fixture description ' * (8+(q%4)*8))[:1024],
                           'iteration_id': iteration, 'owner_id': owner['id'],
                           'plan': self.plan(width=q), 'dependency_task_ids': deps}
                r = await self.request('POST', f'/projects/{pid}/tasks', self.manager['token'], payload, status=201)
                task = dict(r['data']['task'], ordinal=ordinal)
                local.append(task)
                if q >= 75:
                    continue
                await self.transition(task, owner, 1)
                await self.transition(task, owner, 4, {'artifact_revision': ARTIFACT, 'evidence': EVIDENCE})
                rolled = q < 12 or (p < 20 and q == 12)
                for review_index in range(3 if rolled else 4):
                    rp = {'expected_version': task['version'], 'template_version': t['version'],
                          'artifact_revision': ARTIFACT,
                          'sections': [{'section_id': x['section_id'], 'content': 'Synthetic fixture evidence',
                                        'evidence': EVIDENCE} for x in t['sections']],
                          'checklist': [{'item_id': x['item_id'], 'judgment': 1, 'rationale': 'Synthetic fixture pass',
                                         'evidence': EVIDENCE} for x in t['items']], 'verdict': 1}
                    rr = await self.request('POST', f"/projects/{pid}/tasks/{task['id']}/reviews",
                                            self.manager['token'], rp, status=201)
                    task.update(rr['data']['task'])
                    review = rr['data']['review']
                await self.transition(task, self.manager, 5, {'review_id': review['id'], 'review_version': review['version']})
                ar = await self.request('POST', f"/projects/{pid}/tasks/{task['id']}/release-assessments",
                                        self.manager['token'], self.assessment(task['version'], owner['id']), status=201)
                task.update(ar['data']['task'])
                assessment = ar['data']['assessment']
                approved = await self.request('POST', f"/projects/{pid}/tasks/{task['id']}/release-assessments/{assessment['id']}/reviews",
                                             self.reviewer['token'],
                                             {'expected_version': task['version'], 'expected_assessment_version': assessment['version'],
                                              'verdict': 1, 'reason': 'Synthetic fixture approval', 'evidence': EVIDENCE})
                task.update(approved['data']['task'])
                assessment = approved['data']['assessment']
                await self.transition(task, self.manager, 7, {'assessment_id': assessment['id'],
                                      'assessment_version': assessment['version'], 'release_version': 'synthetic-v1',
                                      'reason': 'Synthetic fixture decision, no external release', 'evidence': EVIDENCE})
                if rolled:
                    await self.transition(task, self.manager, 8,
                                          {'reason': 'Synthetic fixture rollback, no external deployment',
                                           'impact': 'Synthetic scope', 'target_version': 'synthetic-baseline-v1',
                                           'assessment_id': assessment['id'], 'rollback_plan_version': assessment['rollback_plan_version'],
                                           'evidence': EVIDENCE})
            return {'id': pid, 'iteration_id': iteration, 'tasks': local, 'template_version': t['version']}
        self.projects = await asyncio.gather(*(build_project(p) for p in range(40)))
        self.tasks = [t for p in self.projects for t in p['tasks']]
        self.template = template
        self.e.event('fixture_mapping', run_id=self.run_id, anchor=at(self.anchor),
                     projects=[{'id': p['id'], 'iteration_id': p['iteration_id']} for p in self.projects],
                     task_ids=[t['id'] for t in self.tasks], owners=[t['owner_id'] for t in self.tasks],
                     synthetic_users=[{'id': u['id'], 'username': u['username']} for u in accounts],
                     manager_user_id=self.manager['id'], bootstrap_project_id=self.context['bootstrap_project_id'])
        await self.audit_fixture()
        if self.mode == 868:
            for p in self.projects:
                for task in p['tasks'][75:80]:
                    await self.transition(task, self.by_id[task['owner_id']], 1)
        if self.mode == 868:
            ids = ','.join(str(p['id']) for p in self.projects)
            rows = await self.audit(f"SELECT COUNT(*) AS n FROM audit_events WHERE project_id IN ({ids}) AND operation_id='transitionTask' AND outcome=1;")
            self.transition_audit_baseline = int(rows[0]['n'])
        if self.mode == 866:
            rules = await self.request('GET', f"/projects/{self.projects[0]['id']}/escalation-rules", self.manager['token'])
            self.e.event('escalation_rule_observation', rules=rules['data'])
            if rules['data']['version'] != 1:
                raise RuntimeError('Frozen default escalation rule version not observed')
            args = ['service-credential']
            for p in self.projects:
                args += ['--project-id', str(p['id'])]
            args += ['--ttl-seconds', '900', '--output-name', f'pv4-{self.mode}-{uuid.uuid4().hex[:12]}.json']
            meta = json.loads(await self.control(*args, secret=True))
            cred = json.loads(Path(meta['credential_file']).read_text())
            if sorted(cred['project_ids']) != sorted(p['id'] for p in self.projects) or cred['scopes'] != ['escalation:write']:
                raise RuntimeError('Issued limited service identity does not match explicit fixture scopes')
            self.service = cred['access_token']
            self.e.event('service_identity', session_id=meta['session_id'], expires_at=meta['expires_at'],
                         ttl_seconds=meta['ttl_seconds'], project_count=len(cred['project_ids']))

    async def audit(self, query):
        raw = await self.control('audit-sql', stdin=query, timeout=15)
        self.e.event('readonly_sql', query=query, raw=raw)
        if not raw:
            return []
        lines = raw.splitlines()
        if not lines or '\t' not in lines[0]:
            # Single-column batch output is permitted; caller validates its exact column name/value.
            return [dict(zip([lines[0]], [line])) for line in lines[1:]]
        names = lines[0].split('\t')
        rows = [line.split('\t') for line in lines[1:]]
        if any(len(r) != len(names) for r in rows):
            raise RuntimeError('Unparseable nonempty SELECT observation')
        return [dict(zip(names, r)) for r in rows]

    async def audit_fixture(self):
        ids = ','.join(str(p['id']) for p in self.projects)
        query = ('SELECT '
                 f'(SELECT COUNT(*) FROM projects WHERE id IN ({ids})) AS projects_count, '
                 f'(SELECT COUNT(*) FROM tasks WHERE project_id IN ({ids})) AS tasks_count, '
                 f'(SELECT COUNT(*) FROM task_dependencies WHERE project_id IN ({ids})) AS dependencies_count, '
                 f'((SELECT COUNT(*) FROM reviews WHERE project_id IN ({ids})) + '
                 f'(SELECT COUNT(*) FROM decisions WHERE project_id IN ({ids}))) AS review_decision_count;')
        rows = await self.audit(query)
        expected = {'projects_count': '40', 'tasks_count': '6000', 'dependencies_count': '9000',
                    'review_decision_count': '15000'}
        if rows != [expected]:
            raise RuntimeError('Representative fixture cardinality not established')
        self.e.report['fixture'] = {'counts': expected, 'api_only_writes': True,
                                    'bootstrap_excluded': True, 'sha256_id_order': sha([t['id'] for t in self.tasks])}

    async def usage_snapshot(self, label):
        capability = self.context.get('runtime_usage')
        if not capability:
            self.e.event('runtime_usage_unavailable', label=label, observed=False,
                         reason='not_declared_in_exact_runtime_context')
            return
        if capability.get('control_command') != 'runtime-usage':
            self.e.event('runtime_usage_unavailable', label=label, observed=False,
                         reason='declaration_does_not_match_frozen_neutral_contract')
            return
        try:
            returncode, raw = await self.control('runtime-usage', timeout=20, allow_nonzero=True)
            value = json.loads(raw)
            required = {'mysql','rabbitmq','api','consumer','scheduler','web'}
            complete = returncode==0 and value.get('schema_version')==1 and value.get('observation_complete') is True
            complete = complete and set(value.get('services',{}))==required
            self.e.event('runtime_usage', label=label, interpretation='bounded Docker CLI snapshot, not RSS or whole-window peak',
                         complete=complete, snapshot=value)
            if not complete:
                self.e.report.setdefault('observation_warnings', []).append('runtime-usage incomplete at '+label)
        except Exception as error:
            self.e.event('runtime_usage_failure', label=label, observed=False, exception_type=type(error).__name__)
            self.e.report.setdefault('observation_warnings', []).append('runtime-usage unavailable at '+label)

    async def usage_observer(self, stop):
        while not stop.is_set():
            await self.usage_snapshot(self.phase)
            try:
                await asyncio.wait_for(stop.wait(), 60)
            except asyncio.TimeoutError:
                pass

    async def resource_snapshot(self, name):
        returncode, raw = await self.control('runtime-metadata', timeout=60, allow_nonzero=True)
        value = json.loads(raw)
        self.e.report['observations'][name] = value
        if returncode != 0 or value.get('observation_complete') is not True:
            raise RuntimeError('Required read-only runtime metadata incomplete')

    async def sampler(self, stop):
        last = time.perf_counter()
        usage0 = resource.getrusage(resource.RUSAGE_SELF)
        while not stop.is_set():
            now = time.perf_counter()
            usage = resource.getrusage(resource.RUSAGE_SELF)
            meminfo = {}
            try:
                for line in Path('/proc/meminfo').read_text().splitlines():
                    if line.startswith(('MemTotal:', 'MemAvailable:', 'SwapTotal:', 'SwapFree:')):
                        key, value = line.split(':',1)
                        meminfo[key] = value.strip()
            except OSError:
                meminfo = {'unavailable': True}
            self.e.event('load_generator_sample', phase=self.phase, active_users=self.active_users,
                         outstanding_http=dict(self.inflight), loop_interval_s=now-last,
                         loop_lag_over_one_second_s=max(0,now-last-1),
                         cpu_user_s=usage.ru_utime, cpu_system_s=usage.ru_stime,
                         max_rss_linux_kib=usage.ru_maxrss,
                         voluntary_context_switches=usage.ru_nvcsw, involuntary_context_switches=usage.ru_nivcsw,
                         memory=meminfo)
            last = now
            try:
                await asyncio.wait_for(stop.wait(), 1)
            except asyncio.TimeoutError:
                pass
        self.e.report['observations']['load_generator_cpu_delta_s'] = (
            resource.getrusage(resource.RUSAGE_SELF).ru_utime + resource.getrusage(resource.RUSAGE_SELF).ru_stime
            - usage0.ru_utime - usage0.ru_stime)

    async def task_operation(self, vu, seq):
        p = self.projects[vu%40]
        if vu < 200:
            task = p['tasks'][75+vu//40]
            fields = {'reason': 'Synthetic dependency coordination', 'responsibility_stage': 2,
                      'evidence': EVIDENCE} if task['state'] == 2 else {'basis': 'Synthetic blocker cleared', 'evidence': EVIDENCE}
            await self.transition(task, self.by_id[task['owner_id']], 2 if task['state']==2 else 3,
                                  fields, op='transition', vu=vu, seq=seq)
        else:
            task = p['tasks'][(seq*17+vu)%150]
            if vu < 300:
                def detail_semantic(value):
                    item = value['data']
                    if any(item[key] != task[key] for key in ('id','project_id','iteration_id','owner_id')):
                        raise AssertionError('Detail query identity/scope mismatch')
                await self.request('GET', f"/projects/{p['id']}/tasks/{task['id']}", self.manager['token'],
                                   op='query_detail', vu=vu, seq=seq, ordinal=task['ordinal'],
                                   route='/projects/{project_id}/tasks/{task_id}', semantic=detail_semantic)
            elif vu < 350:
                query = f"?page={1+seq%3}&page_size=50&sort={['id','planned_end','updated_at'][seq%3]}"
                def list_semantic(value):
                    page = value['data']
                    if page['total'] != 150 or page['page'] != 1+seq%3 or page['page_size'] != 50:
                        raise AssertionError('Task pagination metadata mismatch')
                    if len(page['items']) != 50 or len({t['id'] for t in page['items']}) != 50:
                        raise AssertionError('Task pagination count/uniqueness mismatch')
                    if any(t['project_id'] != p['id'] for t in page['items']):
                        raise AssertionError('Task pagination project scope mismatch')
                await self.request('GET', f"/projects/{p['id']}/tasks"+query, self.manager['token'],
                                   op='query_list', vu=vu, seq=seq, route='/projects/{project_id}/tasks',
                                   semantic=list_semantic)
            else:
                history = p['tasks'][(seq+vu)%75]
                endpoint = 'reviews' if seq%2 == 0 else 'decisions'
                def history_semantic(value):
                    page = value['data']
                    q = history['ordinal']%150
                    project_ordinal = history['ordinal']//150
                    rolled = q < 12 or (project_ordinal < 20 and q==12)
                    expected = (3 if rolled else 4) if endpoint=='reviews' else (2 if rolled else 1)
                    if page['total'] != expected or len(page['items']) != expected:
                        raise AssertionError('History query omitted representative real fixture rows')
                    if any(t['project_id'] != p['id'] or t['task_id'] != history['id'] for t in page['items']):
                        raise AssertionError('History query scope mismatch')
                await self.request('GET', f"/projects/{p['id']}/tasks/{history['id']}/{endpoint}?page=1&page_size=20",
                                   self.manager['token'], op='query_history', vu=vu, seq=seq,
                                   ordinal=history['ordinal'], route='/projects/{project_id}/tasks/{task_id}/'+endpoint, semantic=history_semantic)

    async def contract_operation(self, vu, seq):
        p = self.projects[vu%40]
        task = p['tasks'][75+(seq+vu)%75]
        category = [1,1,2,2,3][vu%5]
        if category == 1:
            payload = {'title': f'Synthetic validation {vu}-{seq}', 'description': 'Synthetic contract request',
                       'iteration_id': p['iteration_id'], 'owner_id': task['owner_id'],
                       'plan': self.plan(width=seq%600), 'dependency_task_ids': [p['tasks'][20]['id']]}
        elif category == 2:
            payload = {'expected_version': task['version'], 'action': 2,
                       'reason': 'Synthetic contract blocker', 'responsibility_stage': 2, 'evidence': EVIDENCE}
        else:
            payload = self.assessment(task['version'], task['owner_id'])
        reject = (seq+vu)%4 == 3
        if reject:
            if category == 1:
                payload['plan']['planned_end'] = payload['plan']['planned_start']
            elif category == 2:
                # Structurally valid TransitionRequest with cross-field invalid evidence is not possible here;
                # candidate-only illegal action is expressly CONTRACT_INVALID per frozen operation description.
                payload['action'] = 99
            else:
                payload['risks'][3]['perspective'] = 1  # duplicate perspective, valid outer structural shape
        body = {'category': category, 'payload': payload}
        if category != 1:
            body['task_id'] = task['id']
        def semantic(value):
            if not reject and (value['data']['valid'] is not True or value['data']['category'] != category
                               or value['data']['business_guards_executed'] is not False):
                raise AssertionError('Contract result failed semantic oracle')
        await self.request('POST', f"/projects/{p['id']}/contract-validations", self.manager['token'], body,
                           status=422 if reject else 200, op='contract_reject' if reject else 'contract_valid',
                           expect_code='CONTRACT_INVALID' if reject else None, semantic=semantic,
                           vu=vu, seq=seq, ordinal=task['ordinal'], version=task['version'],
                           route='/projects/{project_id}/contract-validations')

    async def escalation_operation(self, vu, seq):
        p = self.projects[vu%40]
        task = p['tasks'][75+vu//40]
        # This preparation is explicitly excluded from escalation latency/throughput, but remains part
        # of the same 400-user cycle and competes for the same server. Actual per-op outstanding HTTP is sampled.
        version = task['version']
        due = self.anchor-timedelta(hours=48, microseconds=seq*400+vu)
        plan_payload = {'expected_version': version, 'plan': self.plan(end=due),
                        'reason': 'Synthetic fresh schedule for independently counted upgrade', 'evidence': EVIDENCE}
        old_schedule = task['schedule_version']
        def prepare_semantic(value):
            changed = value['data']['task']
            if changed['version'] != version+1 or changed['schedule_version'] != old_schedule+1:
                raise AssertionError('Plan preparation failed to advance exact versions')
        prepared = await self.request('PATCH', f"/projects/{p['id']}/tasks/{task['id']}/plan", self.manager['token'],
                                      plan_payload, op='plan_prepare', vu=vu, seq=seq, ordinal=task['ordinal'], version=version,
                                      route='/projects/{project_id}/tasks/{task_id}/plan', semantic=prepare_semantic)
        if not prepared:
            return
        task.update(prepared['data']['task'])
        body = {'expected_version': task['version'], 'schedule_version': task['schedule_version'],
                'rule_version': 1, 'scan_run_id': str(uuid.uuid5(uuid.UUID(self.run_id), f'{self.phase}-{vu}-{seq}'))}
        version = task['version']
        def semantic(value):
            data = value['data']
            if data['created'] is not True or data['task_version'] != version+1:
                raise AssertionError('New escalation did not reliably create exactly one event/version')
            event = data['event']
            if event['level'] != 3 or event['schedule_version'] != task['schedule_version'] or event['task_id'] != task['id'] or event['project_id'] != p['id']:
                raise AssertionError('Escalation highest-level/schedule oracle failed')
            if sorted(event['recipient_ids']) != sorted({task['owner_id'], self.manager['id']}):
                raise AssertionError('Escalation recipient snapshot incomplete')
        r = await self.request('POST', f"/internal/projects/{p['id']}/tasks/{task['id']}/escalations", self.service,
                               body, status=202, op='escalation_new', vu=vu, seq=seq, ordinal=task['ordinal'],
                               version=version, route='/internal/projects/{project_id}/tasks/{task_id}/escalations',
                               semantic=semantic)
        if r:
            data = r['data']
            task['version'] = data['task_version']
            task['escalation_count'] += 1
            event = data['event']
            self.new_events[event['id']] = (event['task_id'], event['schedule_version'], event['recipient_ids'])
            # Original server timestamps and event identity permit post-load delivery-lag calculation.
            self.e.event('accepted_event', phase=self.phase, vu=vu, seq=seq, event=event)

    async def worker(self, vu, phase, ramp, gate):
        await gate.wait()
        end = self.phase_deadline
        if ramp:
            await asyncio.sleep(vu*30/400)
        self.active_users += 1
        seq = 0
        try:
            while time.perf_counter_ns() < end:
                seq += 1
                try:
                    if self.mode == 868:
                        await self.task_operation(vu, seq)
                    elif self.mode == 867:
                        await self.contract_operation(vu, seq)
                    else:
                        await self.escalation_operation(vu, seq)
                except Exception as error:
                    self.e.event('worker_failure', phase=phase, vu=vu, seq=seq, error_type=type(error).__name__)
                    self.e.report.setdefault('worker_failures', []).append({'phase': phase, 'vu': vu, 'seq': seq,
                                                                            'error_type': type(error).__name__})
                    return
        finally:
            self.active_users -= 1

    async def phase_run(self, phase, seconds, ramp=False):
        self.phase = phase
        gate = asyncio.Event()
        workers = [asyncio.create_task(self.worker(vu, phase, ramp, gate)) for vu in range(400)]
        await asyncio.sleep(0)
        start = time.perf_counter_ns()
        end = start + int(seconds*1e9)
        self.phase_deadline = end
        self.e.report['phases'][phase] = {'start_ns': start, 'end_ns': end, 'configured_users': 400,
                                          'duration_s': seconds, 'ramp_s': 30 if ramp else 0,
                                          'started_at': utc(), 'prewarm_excluded': phase!='steady'}
        gate.set()
        await asyncio.gather(*workers)
        self.e.report['phases'][phase]['drained_at'] = utc()
        self.e.report['phases'][phase]['last_completion_ns'] = time.perf_counter_ns()
        self.e.event('phase_complete', phase=phase, duration_s=seconds)

    async def postcheck(self):
        self.phase = 'postcheck'
        await self.audit_fixture()
        if self.mode in (867,868):
            ids = ','.join(str(p['id']) for p in self.projects)
            rows = await self.audit(f'SELECT state, COUNT(*) AS n FROM tasks WHERE project_id IN ({ids}) GROUP BY state ORDER BY state;')
            self.e.report['observations']['final_task_states'] = rows
        if self.mode == 867:
            # Contract validation cannot alter task versions or create business records.
            ids = ','.join(str(p['id']) for p in self.projects)
            rows = await self.audit(f'SELECT id, version FROM tasks WHERE project_id IN ({ids}) ORDER BY id;')
            versions = {int(r['id']): int(r['version']) for r in rows}
            if versions != {t['id']: t['version'] for t in self.tasks}:
                raise RuntimeError('Read-only validation mutated task version')
        if self.mode == 868:
            ids = ','.join(str(p['id']) for p in self.projects)
            rows = await self.audit(f"SELECT COUNT(*) AS n FROM audit_events WHERE project_id IN ({ids}) AND operation_id='transitionTask' AND outcome=1;")
            acknowledged = sum(row['issued']-row['failed'] for (phase,op),row in self.e.stats.items()
                               if phase in ('warmup','steady') and op=='transition')
            if int(rows[0]['n'])-self.transition_audit_baseline != acknowledged:
                raise RuntimeError('Successful transition audit count differs from acknowledged mutations')
            for p in self.projects:
                for task in p['tasks'][75:80]:
                    r = await self.request('GET', f"/projects/{p['id']}/tasks/{task['id']}", self.manager['token'],
                                           op='postcheck', ordinal=task['ordinal'])
                    if r['data']['version'] != task['version'] or r['data']['state'] != task['state']:
                        raise RuntimeError('Persisted transition result differs from acknowledged result')
        if self.mode == 866:
            await asyncio.sleep(5)
            ids = ','.join(str(p['id']) for p in self.projects)
            counts = await self.audit(f'SELECT COUNT(*) AS n, COUNT(DISTINCT task_id,schedule_version,level) AS unique_n FROM escalation_events WHERE project_id IN ({ids});')
            if counts != [{'n': str(len(self.new_events)), 'unique_n': str(len(self.new_events))}]:
                raise RuntimeError('Escalation event count/uniqueness differs from acknowledged new events')
            rows = await self.audit(
                'SELECT e.id AS escalation_id,e.event_id,e.task_id,e.schedule_version,e.level,'
                'TIMESTAMPDIFF(MICROSECOND,o.created_at,n.created_at) AS delivery_lag_us,'
                'n.recipient_id,n.fallback '
                'FROM escalation_events e JOIN outbox_events o ON o.id=e.event_id '
                'LEFT JOIN notifications n ON n.event_id=o.id '
                f'WHERE e.project_id IN ({ids}) ORDER BY e.id,n.recipient_id;')
            by_event = collections.defaultdict(list)
            lags = []
            for row in rows:
                by_event[int(row['escalation_id'])].append(row)
                if row['delivery_lag_us'] != 'NULL':
                    lags.append(int(row['delivery_lag_us']))
            missing = 0
            fallback = 0
            for event_id, (_, _, recipients) in self.new_events.items():
                actual = by_event[event_id]
                got = [int(r['recipient_id']) for r in actual if r['recipient_id']!='NULL']
                if sorted(got) != sorted(recipients):
                    missing += 1
                fallback += sum(r['fallback']=='1' for r in actual)
            self.e.report['observations']['delivery'] = {'accepted_events': len(self.new_events),
                'missing_or_duplicate_recipient_events_after_5s_drain': missing, 'fallback_notifications': fallback,
                'delivery_lag_us_all': lags, 'delivery_lag_p95_ms': sorted(lags)[math.ceil(len(lags)*.95)-1]/1000 if lags else None,
                'latency_threshold': 'No taskbook end-to-end delivery bound; reported separately from HTTP 202.'}
            self.e.report['observations']['delivery']['scope'] = 'Diagnostic only; missing at bounded observation is pending, not an invented taskbook latency failure. HTTP interface acceptance is separate.'

    def judge(self):
        self.e.report['status'] = 'PASS'
        steady = self.e.report['phases'].get('steady', {})
        if steady.get('duration_s') != 600 or self.e.report.get('worker_failures'):
            self.e.report['status'] = 'INVALID_OR_FAILED'
        primary = {868: ['transition','query_detail','query_list','query_history'],
                   867: ['contract_valid'], 866: ['escalation_new']}[self.mode]
        totals = [0]*10
        evidence = {}
        for op in primary:
            row = self.e.stats.get(('steady',op))
            if not row or row['failed'] or not row['latency_us']:
                self.e.report['status'] = 'FAIL'
                continue
            values = sorted(row['latency_us'])
            p95 = values[math.ceil(len(values)*.95)-1]/1000
            if p95 > 270:
                self.e.report['status'] = 'FAIL'
            evidence[op] = {'p95_ms': p95, 'n': len(values), 'failures': row['failed']}
            for i in range(10):
                totals[i] += row['completions'][i]
        # All steady operations, including preparation and planned rejections, must meet their oracle.
        if any(row['failed'] for (phase,op),row in self.e.stats.items() if phase=='steady'):
            self.e.report['status'] = 'FAIL'
        if any(n < 1000 for n in totals):
            self.e.report['status'] = 'FAIL'
        # Planned negative validation is never credited to valid throughput; retain its independent latency bound.
        reject = self.e.stats.get(('steady','contract_reject'))
        if reject:
            values = sorted(reject['latency_us'])
            if reject['failed'] or values[math.ceil(len(values)*.95)-1] > 270000:
                self.e.report['status'] = 'FAIL'
        self.e.report['criteria'] = {'p95_limit_ms': 270, 'nearest_rank_percentile': True,
                                     'minute_success_minimum': 1000, 'steady_seconds': 600,
                                     'configured_closed_loop_users': 400, 'primary_operations': primary,
                                     'primary_evidence': evidence, 'minute_success_totals': totals,
                                     'target_success_per_minute_full_window': sum(totals)/10,
                                     'no_unexpected_failures': True,
                                     'setup_control_replay_planned_rejection_excluded_from_success_numerator': True}

    async def run(self):
        stop = asyncio.Event()
        sampling = None
        usage_sampling = None
        try:
            await asyncio.wait_for(self.fixture(), timeout=330)
            await self.resource_snapshot('before_load')
            stop = asyncio.Event()
            sampling = asyncio.create_task(self.sampler(stop))
            usage_sampling = asyncio.create_task(self.usage_observer(stop))
            await self.phase_run('warmup', 90, ramp=True)
            await self.phase_run('steady', 600)
            stop.set()
            await sampling
            sampling = None
            await usage_sampling
            usage_sampling = None
            await self.resource_snapshot('after_load')
            await self.usage_snapshot('after_load')
            await self.postcheck()
            self.judge()
        except BaseException as error:
            self.e.report['status'] = 'INCOMPLETE_OR_FAILED'
            self.e.report['failure'] = {'type': type(error).__name__, 'phase': self.phase}
            self.e.event('harness_failure', phase=self.phase, exception_type=type(error).__name__)
        finally:
            stop.set()
            if sampling:
                await sampling
            if usage_sampling:
                await usage_sampling
            await self.client.aclose()
            self.e.finish()
        return 0 if self.e.report['status']=='PASS' else 1


def main(mode):
    os.umask(0o077)
    driver = Driver(mode)
    return asyncio.run(driver.run())
