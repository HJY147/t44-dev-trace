"""Real deployment-to-host-bootstrap flow with full Chinese historical packet fixture.
Only container execution is mocked; host binding, raw-hash outputs and rotation run.
"""
import base64
import contextlib
import copy
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
BACKEND = HERE.parents[1] / 'backend/direct-p18-bootstrap'

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

m = load('unicode_start', HERE/'start.py')
b = load('unicode_bootstrap', BACKEND/'bootstrap.py')
fixtures = load('backend_public_fixture', BACKEND.parent/'fast-bootstrap/offline_checks.py')


class UnicodeChecks(unittest.TestCase):
    def exercise(self, tampered=False, run_id='r30posttools18', invalid_state=False):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp).resolve()
            p09 = folder/'P09'
            packet = p09/'P-packet/output/packet/inputs'
            packet.mkdir(parents=True)
            old, accounts, tasks, events = fixtures.fixture()
            transition_ids = {row['transition_task']['id'] for row in old['inventory']['clients']}
            for rows in tasks.values():
                for task in rows:
                    if task['id'] in transition_ids:
                        task.update(owner_id=2, state=3 if task['id'] % 4 == 3 else 2,
                                    blocked_from_state=2 if task['id'] % 4 == 3 else None)
            if invalid_state:
                tasks[40][18]['state'] = 4
            old.pop('binding_sha256')
            old['chinese_note'] = {'项目': '软件开发大作业', '说明': '中文绑定必须保持原始规范'}
            original_canonical = (json.dumps(old, sort_keys=True, separators=(',', ':'),
                                            ensure_ascii=False, allow_nan=False)+'\n').encode()
            old['binding_sha256'] = hashlib.sha256(original_canonical).hexdigest()
            packet_raw = (json.dumps(old, sort_keys=True, separators=(',', ':'),
                                     ensure_ascii=False, allow_nan=False)+'\n').encode()
            self.assertIn('中文绑定'.encode(), packet_raw)
            self.assertEqual(len(old['inventory']['clients']), 400)
            if tampered:
                packet_raw = packet_raw.replace('中文绑定'.encode(), '篡改绑定'.encode())
            (packet/'session.private.json').write_bytes(packet_raw)
            (packet/'ca.pem').write_bytes(b'synthetic-ca')
            account = p09/'P-accounts/output'
            account.mkdir(parents=True)
            (account/'accounts.initialized.private.json').write_bytes(b.canonical(accounts))
            receipt = folder/'receipt.json'
            receipt.write_bytes(b.canonical({'source_sha': b.SOURCE,
                'source_manifest_sha256': b.SOURCE_MANIFEST, 'bundle_manifest_sha256': b.BUNDLE_MANIFEST,
                'identity': {'config_id': b.CONFIG, 'success': True}}))
            target = folder/'scheduler-token.json'
            m.write(target, b'{"access_token":"OLD-SYNTHETIC"}\n')
            original_cli = b'{ "access_token" : "NEW-SYNTHETIC" }\n'
            calls, container_calls, task_writes = [], [], []

            def docker(argv, **kwargs):
                container_calls.append(argv)
                payload = json.loads(kwargs['input'])
                self.assertEqual(payload['old'], old)
                self.assertEqual(b.canonical({k:v for k,v in payload['old'].items()
                                             if k != 'binding_sha256'}), original_canonical)
                class API(fixtures.API):
                    def request(self, path, token=None, body=None, **options):
                        if path == '/auth/login' or '?' in path:
                            return copy.deepcopy(super().request(path, token, body))
                        self.requests.append({'path':path})
                        parts = path.split('/')
                        pid, tid = int(parts[2]), int(parts[4])
                        task = next(t for t in self.tasks[pid] if t['id'] == tid)
                        if body:
                            task_writes.append(path)
                            selftest.assertEqual(body['action'],3)
                            selftest.assertEqual(body['expected_version'],task['version'])
                            selftest.assertEqual(token,'NEVER-PUBLIC-TOKEN-developer')
                            selftest.assertTrue(options['idempotency_key'].startswith('p18-unblock-'))
                            task.update(state=2, blocked_from_state=None, version=task['version']+1)
                        return copy.deepcopy(task), {}
                selftest = self
                api = API(copy.deepcopy(tasks),copy.deepcopy(events))
                value, rawcli = b.collect(payload['old'], accounts, api,
                    lambda: ({'token':'NEW-SYNTHETIC','user_id':4,'expires_at':'2030-01-01T00:00:00Z'},original_cli),
                    lambda sessions:sessions,run_id)
                self.assertEqual(value['transition_initialization']['unblocked'],200)
                self.assertTrue(all(row['transition_task']['state']==2 for row in value['inventory']['clients']))
                for row in value['inventory']['clients']:
                    self.assertEqual(row['transition_task']['version'],8 if row['transition_task']['id']%4==3 else 7)
                value['service_cli_original_b64']=base64.b64encode(rawcli).decode()
                return subprocess.CompletedProcess(argv, 0, b.canonical(value), b'')

            def runner(argv, **kwargs):
                calls.append(argv)
                if '--old-packet' in argv:
                    args = list(argv[2:])
                    args[args.index('--import-receipt')+1] = str(receipt)
                    with patch.object(sys, 'argv', args), patch.object(b.os, 'geteuid', return_value=0), \
                         patch.object(b.subprocess, 'run', side_effect=docker), \
                         contextlib.redirect_stdout(io.StringIO()):
                        b.main()
                return subprocess.CompletedProcess(argv,0,b'PRIVATE',b'')

            out = folder/'run'
            with patch.object(m, 'P09', p09):
                if invalid_state:
                    with self.assertRaisesRegex(ValueError, 'INITIAL_STATE_NOT_DEVELOPING_OR_RETURNABLE'):
                        m.execute(BACKEND,run_id,out,runner,target)
                    self.assertEqual(len(container_calls),1)
                    self.assertEqual(task_writes,[])
                    self.assertEqual(len(calls),4)
                    self.assertEqual(target.read_bytes(), b'{"access_token":"OLD-SYNTHETIC"}\n')
                elif tampered:
                    with self.assertRaisesRegex(ValueError, 'ORIGINAL_PACKET_BINDING_REQUIRED'):
                        m.execute(BACKEND,run_id,out,runner,target)
                    self.assertEqual(container_calls, [])
                    self.assertEqual(len(calls), 4)  # stop/start/readiness/host, no worker start
                    self.assertEqual(target.read_bytes(), b'{"access_token":"OLD-SYNTHETIC"}\n')
                    self.assertTrue((out/'bootstrap/FAILED.PUBLIC.json').exists())
                else:
                    result = m.execute(BACKEND,run_id,out,runner,target)
                    self.assertEqual(result['status'],'INIT_DONE')
                    self.assertEqual(len(container_calls),1)
                    self.assertEqual(target.read_bytes(), original_cli)
                    value = json.loads((out/'bootstrap/current-inputs.private.json').read_bytes())
                    self.assertEqual(value['original_packet_sha256'], hashlib.sha256(packet_raw).hexdigest())
                    self.assertTrue((out/'rotation/scheduler-token.original.private.json').exists())

    def test_full_chinese_packet_host_bootstrap_and_atomic_rotation(self):
        self.exercise()

    def test_p18_complete_chinese_packet_initialization(self):
        self.exercise(run_id='r30posttools18')

    def test_invalid_mixed_state_no_rotation_or_worker_start(self):
        self.exercise(invalid_state=True)

    def test_chinese_binding_tamper_fails_before_container_session(self):
        self.exercise(tampered=True)


if __name__ == '__main__':
    unittest.main()
