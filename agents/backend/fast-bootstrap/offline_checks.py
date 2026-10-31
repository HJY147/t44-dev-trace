"""Synthetic-only full direct initialization graph and actual host CLI rehearsal."""
import copy
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import types
from unittest.mock import patch
import contextlib

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('bootstrap', HERE / 'bootstrap.py')
b = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)
SUPPORT = HERE / 'runtime_support.py'
spec = importlib.util.spec_from_file_location('support', SUPPORT)
tls = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tls)


def fixture():
    clients, tasks, events = [], {}, {}
    for pid in range(1, 41):
        tasks[pid], events[pid] = [], []
        for j in range(10):
            cid = (pid - 1) * 10 + j
            first, second = 2 * cid + 1, 2 * cid + 2
            task = lambda tid: {'id': tid, 'project_id': pid, 'version': 7,
                'schedule_version': 3, 'state': 2, 'plan': {'planned_end': '2000-01-01T00:00:00Z'}}
            x, y = task(first), task(second)
            tasks[pid] += [x, y]
            event = {'id': cid + 1, 'project_id': pid, 'task_id': second,
                     'schedule_version': 3, 'rule_version': 1}
            events[pid].append(event)
            clients.append({'client_id': cid, 'project_id': pid, 'transition_task': dict(x, version=1),
                'escalation_task': dict(y, version=1), 'escalation_event': dict(event, id=999999),
                'project_manager_ids': [1], 'other_static_payload': {'retained': True}})
        # Force two real task pages per project using the original pagination method.
        tasks[pid] += [{'id': 100000 + pid * 1000 + n, 'project_id': pid} for n in range(180)]
    old = {'inventory': {'schema': '772-inventory-v1', 'clients': clients, 'rule_version': 1,
                        'other_top_level': 'retain'}, 'identity': {'git_commit': 'historical'},
           'environment': {'origin': 'https://synthetic.invalid', 'connect_ip': '172.21.182.245',
                           'ca_sha256': b.sha(b'synthetic-ca')},
           'counts': {'tasks': 8000}, 'sessions': {r: {'user_id': i}
             for i, r in enumerate(('manager', 'developer', 'reviewer', 'service'), 1)}}
    old['additional_neutral_snapshots'] = {'database': 'synthetic', 'namespace': 'synthetic-ns'}
    accounts = {r: {'user_id': old['sessions'][r]['user_id'], 'username': r,
        'password': 'NEVER-PUBLIC-PASSWORD'} for r in ('manager', 'developer', 'reviewer')}
    old['binding_sha256'] = b.sha(b.canonical(old))
    return old, accounts, tasks, events


class API:
    pages = tls.PinnedAPI.pages

    def __init__(self, tasks, events, fail_at=None):
        self.tasks, self.events, self.requests = tasks, events, []
        self.fail_at = fail_at

    def request(self, path, token=None, body=None):
        self.requests.append({'path': path})
        if len(self.requests) == self.fail_at:
            raise OSError('SYNTHETIC_FAILURE')
        if path == '/auth/login':
            role = body['username']
            return {'access_token': 'NEVER-PUBLIC-TOKEN-' + role,
                'expires_at': '2000-01-01T00:00:01Z',
                'user': {'id': ('manager', 'developer', 'reviewer').index(role) + 1}}, {}
        route, query = path.split('?')
        pid = int(route.split('/')[2])
        rows = self.tasks[pid] if route.endswith('/tasks') else self.events[pid]
        page = int(query.split('page=')[1].split('&')[0])
        return {'items': rows[(page-1)*100:page*100], 'total': len(rows)}, {}


def collect(old, accounts, tasks, events, fail_at=None):
    api = API(tasks, events, fail_at)
    issued = []
    def service():
        issued.append(1)
        return {'token': 'NEVER-PUBLIC-TOKEN-service', 'user_id': 4,
                'expires_at': '2000-01-01T00:00:01Z'}, b'{"synthetic":true}'
    def readback(sessions):
        for session in sessions.values():
            session.update(project_ids=list(range(1, 41)), scopes=['synthetic'])
        return sessions
    return b.collect(old, accounts, api, service, readback, 'synthetic-direct-01'), api, issued


class Checks(unittest.TestCase):
    def test_full_123_request_graph_no_horizon_or_scan_gate(self):
        old, accounts, tasks, events = fixture()
        (value, _), api, issued = collect(old, accounts, tasks, events)
        self.assertEqual(len(api.requests), 123)
        self.assertEqual(len(issued), 1)
        self.assertEqual(value['schema'], 'DIRECT_INPUTS_V1')
        self.assertEqual(value['inventory']['schema'], '772-inventory-v1')
        self.assertEqual(value['inventory']['other_top_level'], 'retain')
        self.assertTrue(all(x['transition_task']['version'] == 7 for x in value['inventory']['clients']))
        self.assertEqual(value['inventory']['clients'][0]['transition_task']['plan']['planned_end'], '2000-01-01T00:00:00Z')
        self.assertEqual(value['missing_current_escalation_events'], 0)
        self.assertEqual(old['inventory']['clients'][0]['transition_task']['version'], 1)

    def test_missing_or_new_schedule_event_null_without_wait(self):
        old, accounts, tasks, events = fixture()
        events[1] = []
        (value, _), api, _ = collect(old, accounts, tasks, events)
        self.assertEqual(value['missing_current_escalation_events'], 10)
        self.assertIsNone(value['inventory']['clients'][0]['escalation_event'])
        self.assertEqual(len(api.requests), 123)

    def test_first_http_failure_has_no_retry(self):
        old, accounts, tasks, events = fixture()
        api = API(tasks, events, fail_at=2)
        called = []
        with self.assertRaises(OSError):
            b.collect(old, accounts, api, lambda: called.append('service'), lambda x: x, 'run')
        self.assertEqual(len(api.requests), 2)
        self.assertFalse(called)

    def test_missing_id_and_cross_project_refused(self):
        old, accounts, tasks, events = fixture()
        tasks[1][0]['project_id'] = 2
        with self.assertRaises(ValueError):
            collect(old, accounts, tasks, events)
        tasks[1] = tasks[1][1:]
        with self.assertRaises(KeyError):
            collect(old, accounts, tasks, events)

    def host(self, folder, fail=False):
        old, accounts, tasks, events = fixture()
        (value, raw), _, _ = collect(old, accounts, tasks, events)
        value.update(service_cli_original_b64=b.base64.b64encode(raw).decode(),
                     fixture_sha256='f'*64, counts={'tasks': 8000})
        files = {'old.json': old, 'accounts.json': accounts,
            'import.json': {'source_sha': b.SOURCE, 'source_manifest_sha256': b.SOURCE_MANIFEST,
                'bundle_manifest_sha256': b.BUNDLE_MANIFEST,
                'identity': {'config_id': b.CONFIG, 'success': True}}}
        for name, data in files.items():
            (folder/name).write_bytes(b.canonical(data))
        (folder/'ca.pem').write_bytes(b'synthetic-ca')
        argv = ['bootstrap.py', '--old-packet', str(folder/'old.json'), '--accounts', str(folder/'accounts.json'),
            '--ca', str(folder/'ca.pem'), '--import-receipt', str(folder/'import.json'),
            '--runtime-support', str(SUPPORT), '--output', str(folder/'out'),
            '--api-container', 'synthetic-api', '--run-id', 'synthetic-direct-01']
        result = subprocess.CompletedProcess([], 2 if fail else 0,
            stdout=b'partial-private-issuance' if fail else b.canonical(value), stderr=b'')
        output = io.StringIO()
        with patch.object(sys, 'argv', argv), patch.object(b.os, 'geteuid', return_value=0), \
             patch.object(b.subprocess, 'run', return_value=result) as run, contextlib.redirect_stdout(output):
            if fail:
                with self.assertRaises(ValueError): b.main()
            else:
                b.main()
            self.assertEqual(run.call_count, 1)
            payload = json.loads(run.call_args.kwargs['input'])
            self.assertEqual(payload['connect_port'], 8443)
            self.assertEqual(payload['old']['environment']['origin'], 'https://synthetic.invalid')
            self.assertEqual(payload['gateway_dns'], 'tls-gateway')
            cmd = run.call_args.args[0]
            self.assertEqual(cmd[:5], ['docker', '--context', 'default', 'exec', '-i'])
            self.assertIn('120s', cmd)
            code = cmd[cmd.index('-c')+1]
            compile(code, '<container-entry>', 'exec')
        return output.getvalue()

    def test_actual_host_cli_private_modes_public_redaction_exclusive(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            public = self.host(folder)
            self.assertNotIn('NEVER-PUBLIC', public)
            for name in ['current-inputs.private.json', 'service-cli.original.private.json',
                         'runtime.stdout.private', 'runtime.stderr.private', 'bootstrap.PUBLIC.json']:
                self.assertEqual((folder/'out'/name).stat().st_mode & 0o777, 0o600)
            current = json.loads((folder/'out/current-inputs.private.json').read_bytes())
            self.assertEqual(current['schema'], 'DIRECT_INPUTS_V1')
            original = (folder/'out/current-inputs.private.json').read_bytes()
            with self.assertRaises(FileExistsError): self.host(folder)
            self.assertEqual((folder/'out/current-inputs.private.json').read_bytes(), original)

    def test_host_failure_keeps_prefix_and_never_retries(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            public = self.host(folder, True)
            self.assertEqual(public, '')
            self.assertTrue((folder/'out/FAILED.PUBLIC.json').is_file())
            self.assertFalse((folder/'out/current-inputs.private.json').exists())
            self.assertEqual((folder/'out/runtime.stdout.private').read_bytes(), b'partial-private-issuance')

    def test_full_container_entry_cli_real_readbacks_counts_and_graph_synthetic(self):
        old, accounts, tasks, events = fixture()
        api = API(tasks, events)
        api.close = lambda: None
        expires = '2000-01-01T00:00:01Z'
        session_rows = []
        for i, role in enumerate(('manager', 'developer', 'reviewer', 'service'), 1):
            session_rows.append({'token_hash': b.hashlib.sha256(('NEVER-PUBLIC-TOKEN-' + role).encode()).digest(),
                'user_id': i if role != 'service' else None,
                'service_account_id': i if role == 'service' else None,
                'expires_at': expires, 'revoked_at': None, 'project_ids': list(range(1, 41)), 'scopes': []})
        calls = []
        class Gateway:
            def get(self, table, identifier):
                calls.append(('get', table))
                return {'id': 4, 'active': True, 'name': 'synthetic-ns-service'}
            def rows(self, table, where, **kwargs):
                calls.append(('rows', table))
                if table == 'auth_sessions': return session_rows
                if table == 'project_members':
                    return [{'user_id': i, 'project_id': pid, 'active': 1}
                            for i in (1, 2, 3) for pid in range(1, 41)]
                return [t for rows in tasks.values() for t in rows]
            def count(self, table, where):
                calls.append(('count', table))
                return 8000 if table == 'tasks' else 40
        class Uow:
            def __enter__(self): self.gateway = Gateway(); return self
            def __exit__(self, *args): return False
        class Settings:
            @staticmethod
            def from_env(): return Settings()
            def mysql_settings(self): return types.SimpleNamespace(database='synthetic')
        modules = {n: types.ModuleType(n) for n in ('t44', 't44.persistence', 't44.services.common', 't44.settings')}
        modules['t44'].__file__ = '/app/backend/t44/__init__.py'
        modules['t44.persistence'].SqlAlchemyUnitOfWorkFactory = lambda engine: Uow
        modules['t44.persistence'].create_mysql_engine = lambda settings: object()
        modules['t44.services.common'].wire = lambda value: value
        modules['t44.settings'].Settings = Settings
        def cli(argv, **kwargs):
            self.assertEqual(argv[1:4], ['-m', 't44.cli', 'service-token'])
            self.assertEqual(argv.count('--project-id'), 40)
            Path(argv[argv.index('--token-file')+1]).write_bytes(b.canonical({
                'access_token': 'NEVER-PUBLIC-TOKEN-service', 'expires_at': expires, 'session_id': 4}))
            return subprocess.CompletedProcess(argv, 0, b'private-cli-output', b'')
        class Loader:
            def exec_module(self, module): module.PinnedAPI = lambda *args, **kwargs: api
        payload = {'old': old, 'accounts': accounts, 'ca_b64': b.base64.b64encode(b'synthetic-ca').decode(),
            'support_b64': b.base64.b64encode(SUPPORT.read_bytes()).decode(),
            'run_id': 'synthetic', 'gateway_dns': 'tls-gateway', 'connect_ip': '172.21.182.245'}
        with patch.dict(sys.modules, modules), patch.object(b.subprocess, 'run', side_effect=cli) as run, \
             patch.object(b.importlib.util, 'spec_from_file_location', return_value=types.SimpleNamespace(loader=Loader())), \
             patch.object(b.importlib.util, 'module_from_spec', return_value=types.ModuleType('fake_tls')):
            value = b.container_main(payload)
        self.assertEqual(run.call_count, 1)
        self.assertEqual(value['counts']['tasks'], 8000)
        self.assertEqual(len(value['fixture_sha256']), 64)
        self.assertEqual(value['initialization_http_requests'], 123)
        self.assertEqual(calls.count(('rows', 'auth_sessions')), 1)
        self.assertEqual(calls.count(('rows', 'tasks')), 1)
        self.assertEqual(calls.count(('rows', 'project_members')), 1)
        self.assertEqual(value['sessions']['developer']['project_ids'], list(range(1, 41)))
        self.assertEqual(sum(k == 'count' for k, _ in calls), 5)


if __name__ == '__main__':
    unittest.main(verbosity=2)
