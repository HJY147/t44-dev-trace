"""Real deployment-to-host-bootstrap flow with full Chinese historical packet fixture.
Only container execution is mocked; host binding, raw-hash outputs and rotation run.
"""
import base64
import contextlib
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
BACKEND = HERE.parents[1] / 'backend/fast-bootstrap'

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

m = load('unicode_start', HERE/'start.py')
b = load('unicode_bootstrap', BACKEND/'bootstrap.py')
fixtures = load('backend_public_fixture', BACKEND/'offline_checks.py')


class UnicodeChecks(unittest.TestCase):
    def exercise(self, tampered=False):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp).resolve()
            p09 = folder/'P09'
            packet = p09/'P-packet/output/packet/inputs'
            packet.mkdir(parents=True)
            old, accounts, _, _ = fixtures.fixture()
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
            calls, container_calls = [], []

            def docker(argv, **kwargs):
                container_calls.append(argv)
                payload = json.loads(kwargs['input'])
                self.assertEqual(payload['old'], old)
                self.assertEqual(b.canonical({k:v for k,v in payload['old'].items()
                                             if k != 'binding_sha256'}), original_canonical)
                value = {'schema':'DIRECT_INPUTS_V1', 'run_id':'unicode-direct',
                    'sessions': {'service': {'token':'NEW-SYNTHETIC'}},
                    'captured_at':'2026-10-31T00:00:00Z', 'initialization_http_requests':123,
                    'missing_current_escalation_events':[],
                    'service_cli_original_b64':base64.b64encode(original_cli).decode()}
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
                if tampered:
                    with self.assertRaisesRegex(ValueError, 'ORIGINAL_PACKET_BINDING_REQUIRED'):
                        m.execute(BACKEND,'unicode-direct',out,runner,target)
                    self.assertEqual(container_calls, [])
                    self.assertEqual(len(calls), 4)  # stop/start/readiness/host, no worker start
                    self.assertEqual(target.read_bytes(), b'{"access_token":"OLD-SYNTHETIC"}\n')
                    self.assertTrue((out/'bootstrap/FAILED.PUBLIC.json').exists())
                else:
                    result = m.execute(BACKEND,'unicode-direct',out,runner,target)
                    self.assertEqual(result['status'],'INIT_DONE')
                    self.assertEqual(len(container_calls),1)
                    self.assertEqual(target.read_bytes(), original_cli)
                    value = json.loads((out/'bootstrap/current-inputs.private.json').read_bytes())
                    self.assertEqual(value['original_packet_sha256'], hashlib.sha256(packet_raw).hexdigest())
                    self.assertTrue((out/'rotation/scheduler-token.original.private.json').exists())

    def test_full_chinese_packet_host_bootstrap_and_atomic_rotation(self):
        self.exercise()

    def test_chinese_binding_tamper_fails_before_container_session(self):
        self.exercise(tampered=True)


if __name__ == '__main__':
    unittest.main()
