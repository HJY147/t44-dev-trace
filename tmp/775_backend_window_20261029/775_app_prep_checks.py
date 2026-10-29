"""Narrow local worker orchestration tests; no Docker, cloud, SQL or SUT."""

import base64
import gzip
import hashlib
import importlib.util
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
PATH = ROOT / 'agents/backend/window-20261029/app-prep-once.py'
SPEC = importlib.util.spec_from_file_location('r29_app_prep', PATH)
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)


class AppPrepChecks(unittest.TestCase):
    def test_JSONL_unique_selection_and_duplicate_rejection(self):
        raw = b'{"event":"start"}\n{"kind":"done","success":true}\n'
        self.assertEqual(M.choose(raw, lambda r: r.get('kind') == 'done')['success'], True)
        with self.assertRaisesRegex(ValueError, 'ONE_EXACT'):
            M.choose(raw + raw, lambda r: r.get('kind') == 'done')
        launcher = PATH.with_name('app-prep-launch.PUBLIC.sh').read_bytes()
        proof = json.loads(PATH.with_name('app-prep-proof.PUBLIC.json').read_bytes())
        encoded = re.search(rb"base64.b64decode\('([A-Za-z0-9+/=]+)',validate=True\)", launcher).group(1)
        self.assertEqual(gzip.decompress(base64.b64decode(encoded, validate=True)), PATH.read_bytes())
        self.assertEqual(hashlib.sha256(launcher).hexdigest(), proof['launcher_sha256'])
        self.assertIn(b"R29_APP_IP=''\nR29_ROOT_ADMIT_PREP=0", launcher)
        self.assertLess(len(launcher) + 300, 18000)
        self.assertLess(len(base64.b64encode(launcher)) + 300, 18000)
        self.assertEqual(subprocess.run(['sh', '-n'], input=launcher, capture_output=True, check=False).returncode, 0)

    def fixture(self, directory, fail_at=None):
        base = Path(directory).resolve()
        campaign = base / 'campaign-r29-01'
        phase = campaign / 'p'
        phase.mkdir(parents=True)
        receipts = phase / 'receipts'
        receipts.mkdir()
        proof = campaign / 'actual-source-files.json'
        proof.write_text(json.dumps({'files': [{}] * 53}))
        binding = {'source_actual_proof_sha256': M.sha(proof), 'database': 't44c_r28p64gen04_p', 'project': 't44-cloud-r28p64gen04-p', 'api_workers': 64, 'images': {'backend': {'alias': 'actual-alias-from-binding'}}, 'image_ids': {'backend': M.IMAGE_ID}}
        (phase / 'binding.json').write_text(json.dumps(binding))
        receipt = receipts / 'actual-budget.json'
        receipt.write_text('{"actual_max_connections":386}')
        resources = [{'role': name, 'container_id': ('abc' + name.encode().hex()).ljust(64, '0')[:64], 'image_id': 'sha256:' + 'b' * 64, 'state': {'Running': True}, 'restart_count': 0} for name in sorted(M.ROLES)] + [{'role': 'scheduler', 'absent': True}]
        calls = []

        def fake_step(label, argv, cap=360):
            calls.append((label, list(map(str, argv))))
            if label == fail_at:
                raise ValueError('ACTUAL_SIMULATED_MIGRATION_FAILURE')
            if label == '01-prepare':
                row = {'success': True, 'phases': {'p': {'phase_dir': str(phase), 'binding_sha256': M.sha(phase / 'binding.json')}}}
            elif label == '05-actual-budget':
                row = {'success': True, 'budget_receipt': str(receipt), 'budget_receipt_sha256': M.sha(receipt), 'actual_max_connections': 386}
            elif label == '07-prep-actual-status':
                row = {'success': True, 'resources': resources}
            elif label == '08-actual-backend-image':
                return (json.dumps(M.IMAGE_ID) + '\n').encode()
            elif label == '09-bootstrap-once':
                row = {'kind': 'contrast790-bootstrap-complete-not-acceptance', 'output_dir': str(phase / 'fixture790-r29-01')}
            elif label == '10-idle-after-bootstrap':
                row = {'success': True, 'resources': resources, 'host_https': {'status': 401, 'strict_CA_and_IP_verified': True}}
            else:
                row = {'success': True}
            return b'{"event":"preserved-leading-JSONL-row"}\n' + json.dumps(row).encode() + b'\n'

        return base, campaign, calls, fake_step

    def test_pipeline_actual_data_grant_only_prep_and_no_S1_S2(self):
        with tempfile.TemporaryDirectory() as directory:
            base, campaign, calls, fake_step = self.fixture(directory)
            records = base / 'r29-app-prep-01'
            # Preflight is deliberately stubbed: this test proves orchestration,
            # not root/Linux, live manifest/image or actual server correctness.
            with patch.object(M, 'preflight'), patch.object(M, 'step', side_effect=fake_step), patch.object(M, 'BASE', base), patch.object(M, 'CAMPAIGN', campaign), patch.object(M, 'RECORDS', records):
                result = M.prepare_once('10.0.0.99')
            self.assertEqual([r[0] for r in calls], ['01-prepare', '02-arm', '03-config', '04-infra', '05-actual-budget', '06-migrate', '07-prep-actual-status', '08-actual-backend-image', '09-bootstrap-once', '10-idle-after-bootstrap'])
            grant = json.loads((records / 'prep-grant.private.json').read_bytes())
            self.assertEqual(set(grant['roles']), {'mysql', 'rabbitmq'})
            self.assertTrue(grant['admitted'])
            self.assertFalse(grant['HTTP_authorized'])
            self.assertEqual(grant['source_proof_sha256'], M.sha(campaign / 'actual-source-files.json'))
            self.assertEqual(result['actual_max_connections'], 386)
            self.assertFalse(result['S1_or_S2_started'])
            self.assertIsNone(result['pressure_grant'])
            self.assertIsNone(result['relay_ready'])
            self.assertIsNone(result['resource_ready'])
            self.assertEqual(sum(label == '09-bootstrap-once' for label, _ in calls), 1)

    def test_failed_migration_prevents_grant_seed_idle_and_retry(self):
        with tempfile.TemporaryDirectory() as directory:
            base, campaign, calls, fake_step = self.fixture(directory, '06-migrate')
            records = base / 'r29-app-prep-01'
            with patch.object(M, 'preflight'), patch.object(M, 'step', side_effect=fake_step), patch.object(M, 'BASE', base), patch.object(M, 'CAMPAIGN', campaign), patch.object(M, 'RECORDS', records):
                with self.assertRaisesRegex(ValueError, 'SIMULATED'):
                    M.prepare_once('10.0.0.99')
            self.assertEqual(len(calls), 6)
            self.assertFalse((records / 'prep-grant.private.json').exists())
            self.assertFalse((records / 'complete.PUBLIC.json').exists())

    def test_real_failed_subprocess_preserves_both_raw_streams_and_exit(self):
        with tempfile.TemporaryDirectory() as directory:
            records = Path(directory).resolve()
            with patch.object(M, 'RECORDS', records), patch.object(M, 'remaining', return_value=10):
                with self.assertRaisesRegex(ValueError, 'STEP_FAILED'):
                    M.step('local-real-failure', [sys.executable, '-c', 'import sys; print("raw-stdout"); print("raw-stderr", file=sys.stderr); sys.exit(3)'])
            self.assertEqual((records / 'local-real-failure.stdout.private').read_bytes(), b'raw-stdout\n')
            self.assertEqual((records / 'local-real-failure.stderr.private').read_bytes(), b'raw-stderr\n')
            self.assertEqual(json.loads((records / 'local-real-failure.exit.PUBLIC.json').read_bytes())['returncode'], 3)


if __name__ == '__main__':
    unittest.main(verbosity=2)
