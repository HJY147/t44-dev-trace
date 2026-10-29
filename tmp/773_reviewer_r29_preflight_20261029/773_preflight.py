"""Narrow offline review probes; no cloud, Docker, SUT, or real session data."""
import ast
import base64
import gzip
import hashlib
import importlib.util
import json
import subprocess
import tempfile
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

PROJECT = Path('/Users/yang/Desktop/nothing/软件开发大作业')
BROOT = PROJECT / '.agent-worktrees/backend-window-20261029'
DROOT = PROJECT / '.agent-worktrees/deployment-transfer-20261029'
B = BROOT / 'agents/backend/window-20261029'
D = DROOT / 'agents/deployment/opaque-relay-20261029'
BSHA = '650ba6a85c964d0df7cfbea6ba2ef917343f40bc'
DSHA = '40631378ab9e34c408130d4d87c74a259dc0c284'
SOURCE = 'f7cdb5fa3b19f84d8ab0d0b042bf51a5b8484e8f'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


relay = module(D / 'relay.py', 'review_relay')
prep = module(B / 'app-prep-once.py', 'review_prep')
installer = module(B / 'install.py', 'review_installer')


class Review(unittest.TestCase):
    def test_reviewed_bytes_match_exact_git_objects(self):
        for root, directory, commit, names in [
            (BROOT, B, BSHA, ['app-prep-once.py', 'app-prep-launch.PUBLIC.sh',
                             'install.py', 'install-via-github-api.PUBLIC.sh']),
            (DROOT, D, DSHA, ['relay.py', 'install.PUBLIC.sh',
                             'APP-configuration.template.PUBLIC.json',
                             'LOAD-configuration.template.PUBLIC.json'])]:
            for name in names:
                raw = subprocess.check_output(['git', 'show', commit + ':' +
                    (directory / name).relative_to(root).as_posix()], cwd=root)
                self.assertEqual(raw, (directory / name).read_bytes())

    def test_thirteen_runtime_files_only_declared_time_delta(self):
        derivation = json.loads((B / 'derivation.PUBLIC.json').read_bytes())
        old = BROOT / 'tmp/790_backend_contrast_20261028/p64-f7-window2000'
        self.assertEqual(len(derivation['p64']), 13)
        for row in derivation['p64']:
            raw = (old / row['file']).read_bytes()
            self.assertEqual(sha(raw), row['parent_sha256'])
            text = raw.decode()
            for before, after in row['literal_allowlist']:
                self.assertEqual(text.count(before), 1)
                text = text.replace(before, after)
            current = (B / 'p64' / row['file']).read_bytes()
            self.assertEqual(current, text.encode())
            self.assertEqual(sha(current), row['new_sha256'])
            # The original assertions are structurally unchanged in all 13.
            def assertions(data):
                return [ast.dump(n) for n in ast.walk(ast.parse(data))
                        if isinstance(n, ast.Assert)]
            self.assertEqual(assertions(raw), assertions(current))
        self.assertEqual(derivation['source_sha'], SOURCE)
        self.assertEqual(derivation['inherited_anchor_unchanged'], '2026-10-28T04:00:00Z')
        self.assertEqual(derivation['stop_utc'], '2026-10-29T12:00:00Z')

    def test_cross_role_manifest_cli_and_budget_pins(self):
        manifest_raw = (B / 'p64/manifest.json').read_bytes()
        manifest = json.loads(manifest_raw)
        for name, row in manifest['files'].items():
            raw = (B / 'p64' / name).read_bytes()
            self.assertEqual((sha(raw), len(raw)), (row['sha256'], row['bytes']))
        self.assertEqual(prep.MANIFEST_SHA, sha(manifest_raw))
        self.assertEqual(prep.PROFILE_SHA, sha((B / 'profile/profile.json').read_bytes()))
        for side in ('APP', 'LOAD'):
            c = json.loads((B / 'templates' / (side + '-configuration.template.PUBLIC.json')).read_bytes())
            self.assertEqual(c['manifest_sha256'], sha(manifest_raw))
            self.assertEqual(c['transfer_sha256'], manifest['files']['transport/790_transfer.py']['sha256'])
            self.assertEqual(c['source_sha'], SOURCE)
            self.assertEqual(c['tools_dir'], '/root/t44-r9/p790-r29-01')
        consumer = (B / 'p64/790_consumer.py').read_text()
        self.assertIn('timeout=60', consumer)
        self.assertIn('timeout=15', consumer)
        self.assertIn('timeout=300', consumer)
        self.assertLessEqual(60 + 15 + 300, 420)
        self.assertEqual(420 + 3 * (5 + 25) + 30, 540)
        self.assertIn('< 330', (B / 'p64/790_load.py').read_text())
        packet = (B / 'p64/edge/790_http.py').read_text()
        self.assertIn('timedelta(seconds=600)', packet)
        self.assertIn('any(value <= datetime.now(UTC) for value in expires)', packet)

    def test_whole_scripts_and_embedded_bytes(self):
        for path in [B / 'install-via-github-api.PUBLIC.sh',
                     B / 'app-prep-launch.PUBLIC.sh', D / 'install.PUBLIC.sh']:
            raw = path.read_bytes()
            self.assertLessEqual(len(raw) + 300, 18000)
            self.assertLessEqual(len(base64.b64encode(raw)) + 300, 18000)
            subprocess.run(['/bin/sh', '-n', str(path)], check=True)
        launch = (B / 'app-prep-launch.PUBLIC.sh').read_text()
        payload = launch.split("base64.b64decode('", 1)[1].split("'", 1)[0]
        self.assertEqual(gzip.decompress(base64.b64decode(payload)), (B / 'app-prep-once.py').read_bytes())
        self.assertIn('R29_ROOT_ADMIT_PREP=0', launch)
        self.assertIn('KillMode=control-group', launch)
        self.assertIn('RuntimeMaxSec=1800', launch)
        self.assertIn(sha((D / 'relay.py').read_bytes()), (D / 'install.PUBLIC.sh').read_text())
        files, _ = installer.verified((B / 'runtime-bundle.PUBLIC.tar.gz').read_bytes())
        self.assertEqual(len(files), 20)

    def test_jsonl_selection_is_exact_and_rejects_ambiguity(self):
        raw = b'{"unrelated":true}\n{"success":true,"resources":[]}\n'
        self.assertEqual(prep.choose(raw, lambda r: r.get('success') is True),
                         {'success': True, 'resources': []})
        with self.assertRaisesRegex(ValueError, 'ONE_EXACT'):
            prep.choose(raw + b'{"success":true}\n', lambda r: r.get('success') is True)
        with self.assertRaisesRegex(ValueError, 'ONE_EXACT'):
            prep.choose(b'{"success":false}\n', lambda r: r.get('success') is True)

    def test_cost_threshold_reserves_no_consumer_and_preserves_download_prefix(self):
        raw = b'public synthetic opaque bytes only'
        compressed = gzip.compress(raw, mtime=0)
        metadata = {'source_sha': SOURCE, 'phase_binding_sha256': '1'*64,
                    'root_grant_sha256': '2'*64, 'original_public_meta': {'key_sha256': '3'*64},
                    'part_count': 1, 'compressed_bytes': len(compressed),
                    'compressed_sha256': sha(compressed), 'raw_bytes': len(raw), 'raw_sha256': sha(raw)}
        part = {'index': 0, 'parts': 1, 'bytes': len(compressed), 'sha256': sha(compressed),
                'data': base64.b64encode(compressed).decode()}
        calls = []
        with tempfile.TemporaryDirectory() as directory:
            # macOS /var is a symlink; use the real canonical scratch parent.
            output = Path(directory).resolve() / 'new'
            c = {'output_dir': str(output), 'deadline': time.monotonic()+600,
                 'max_wait_seconds': 1, 'source_sha': SOURCE, 'binding_sha256': '1'*64,
                 'root_grant_sha256': '2'*64, 'key_sha256': '3'*64, 'nonce': 'r29-review-scope-01',
                 'load_configuration': '/synthetic/load.json', 'load_configuration_sha256': '4'*64,
                 'original_load': {'tools_dir': '/synthetic/tools'}}
            def fetch(_c, name, _cap):
                return json.dumps(metadata if name == 'metadata' else part).encode()
            def invoke(*args):
                calls.append(args)
            with patch.object(relay, 'fetch', fetch), patch.object(relay, 'cost_remaining', return_value=539.9):
                with self.assertRaisesRegex(ValueError, 'NEEDS_540S'):
                    relay.load(c, invoke)
            self.assertEqual(len(calls), 2)  # Existing metadata/part receiver only.
            self.assertFalse(any('790_consumer.py' in str(call) for call in calls))
            self.assertTrue((output / 'metadata-import.PUBLIC.json').is_file())
            self.assertTrue((output / 'part-0.OPAQUE.json').is_file())
            self.assertFalse((output / 'CONSUMER_RESERVED.PUBLIC.json').exists())
            self.assertFalse((output / 'result.PUBLIC.json').exists())

    def test_cleanup_wrong_identity_never_signals(self):
        original = {'namespace': 't44-cloud-r28p64gen04-p', 'python_image_id': 'sha256:'+'a'*64}
        item = {'Name': '/t44-cloud-r28p64gen04-p-790-baseline1', 'Image': 'sha256:'+'b'*64,
                'Config': {'Labels': {'io.t44.contrast.owner': original['namespace']}},
                'State': {'Running': True}, 'Id': 'synthetic'}
        calls = []
        def invoke(argv, **kwargs):
            calls.append((argv, kwargs))
            return SimpleNamespace(returncode=0, stdout=json.dumps(item).encode())
        with patch.object(relay.subprocess, 'run', invoke):
            with self.assertRaisesRegex(ValueError, 'NO_SIGNAL'):
                relay.cleanup_owned_load({'original_load': original})
        self.assertEqual(len(calls), 1)
        self.assertNotIn('stop', calls[0][0])
        self.assertEqual(calls[0][1]['timeout'], 5)


if __name__ == '__main__':
    unittest.main(verbosity=2)
