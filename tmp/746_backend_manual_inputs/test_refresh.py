import base64
import contextlib
import copy
from datetime import datetime, timedelta, timezone
import importlib.util
import io
import json
from pathlib import Path
import stat
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / 'agents/backend/manual-inputs'


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


core = load('manual_core_test', HERE / 'refresh_core.py')
host = load('manual_host_test', HERE / 'host_runner.py')


def fixture():
    now = datetime(2026, 10, 30, 12, tzinfo=timezone.utc)
    sessions = {role: {'token': 'synthetic-not-real-' + role * 4, 'user_id': index,
                       'expires_at': core.stamp(now + timedelta(hours=1)),
                       'project_ids': list(range(1, 41)),
                       'scopes': ['escalation:write'] if role == 'service' else []}
                for index, role in enumerate(['manager', 'developer', 'reviewer', 'service'], 1)}
    attest = {role: {**{k: v for k, v in value.items() if k != 'token'},
                     'token_sha256': core.sha(value['token'].encode())}
              for role, value in sessions.items()}
    clients = []
    for i in range(400):
        pid = i % 40 + 1
        clients.append({'client_id': i, 'project_id': pid,
                        'transition_task': {'id': i + 1, 'project_id': pid, 'state': 2,
                                            'owner_id': 2, 'plan': {'planned_end': core.stamp(now + timedelta(days=2))}},
                        'escalation_task': {'id': i + 1001, 'project_id': pid, 'state': 2, 'schedule_version': 1},
                        'escalation_event': {'id': i + 2001, 'project_id': pid, 'task_id': i + 1001,
                                             'schedule_version': 1, 'rule_version': 1}})
    inventory = {'schema': '772-inventory-v1', 'captured_at': core.stamp(now),
                 'clients': clients, 'rule_version': 1}
    files = {name: ('synthetic ' + name).encode() for name in
             ['ca.pem', 'source-manifest.json', 'backend-bundle-manifest.json', 'backend-import-receipt.json']}
    counts = {'counts': {'projects': 40, 'tasks': 6400, 'dependencies': 9000,
                          'reviews': 11400, 'decisions': 3600}, 'actual_fixture_sha256': 'a' * 64}
    old = {'run_id': 'r30finalp09', 'schema': 'NEUTRAL_753_INPUTS_V1',
           'identity': {'git_commit': core.SOURCE, 'source_manifest_sha256': core.sha(files['source-manifest.json']),
                        'backend_bundle_manifest_sha256': core.sha(files['backend-bundle-manifest.json'])},
           'environment': {'ca_sha256': core.sha(files['ca.pem'])},
           'loaded_receipt_sha256': core.sha(files['backend-import-receipt.json']),
           'window': {'start_utc': '2026-10-29T00:00:00Z', 'end_utc': '2026-10-29T00:15:00Z'},
           'additional_neutral_snapshots': {'namespace': 't44-cloud-r30finalp09-p', 'database': 't44c_r30finalp09_p'},
           'inventory': copy.deepcopy(inventory), 'sessions': copy.deepcopy(sessions), 'counts': counts['counts']}
    old['binding_sha256'] = core.sha(core.canonical(old))
    auth = {'schema': 'manual-material-preparation-v1', 'root_approved': True,
            'benchmark_grant_allow': False, 'operations': core.OPERATIONS,
            'source_sha': core.SOURCE, 'old_packet_sha256': core.sha(core.canonical(old)),
            'new_packet_run_id': 'r30materialresume01', 'packet_nonce': 'b' * 64,
            **old['additional_neutral_snapshots']}
    return old, auth, sessions, inventory, counts, files, now, attest


class ManualRefreshTests(unittest.TestCase):
    def test_old_window_not_retimed_new_packet_has_current_facts(self):
        values = fixture()
        old = copy.deepcopy(values[0])
        core.authorization(values[1], core.canonical(old))
        value = core.build_packet(*values)
        self.assertEqual(values[0], old)
        self.assertEqual(value['additional_neutral_snapshots']['original_packet_window'], old['window'])
        self.assertNotEqual(value['binding_sha256'], old['binding_sha256'])
        self.assertFalse(value['additional_neutral_snapshots']['benchmark_grant_allow'])
        self.assertFalse(value['additional_neutral_snapshots']['external_writer_absence_proven'])

    def test_expired_or_insufficient_session_refused(self):
        for delta in [-1, 900]:
            values = list(fixture())
            values[2]['developer']['expires_at'] = core.stamp(values[6] + timedelta(seconds=delta))
            values[7]['developer']['expires_at'] = values[2]['developer']['expires_at']
            with self.assertRaisesRegex(ValueError, 'ACTUAL_SESSION_LIFETIME'):
                core.build_packet(*values)

    def test_task_state_and_owner_not_fabricated(self):
        for field, value in [('state', 3), ('owner_id', 999)]:
            values = list(fixture()); values[3]['clients'][0]['transition_task'][field] = value
            with self.assertRaisesRegex(ValueError, 'NOT_ELIGIBLE'):
                core.build_packet(*values)

    def test_wrong_ids_count_or_manifest_refused(self):
        values = list(fixture()); values[3]['clients'][0]['transition_task']['id'] = 99999
        with self.assertRaisesRegex(ValueError, 'SAME_EXISTING_800'):
            core.build_packet(*values)
        values = list(fixture()); values[4]['counts'] = {**values[4]['counts'], 'tasks': 6800}
        with self.assertRaisesRegex(ValueError, 'COUNTS_CHANGED'):
            core.build_packet(*values)
        values = list(fixture()); values[5]['source-manifest.json'] = b'tampered'
        with self.assertRaisesRegex(ValueError, 'EXACT_SOURCE_FILE'):
            core.build_packet(*values)

    def test_old_budget_not_authorization(self):
        old, auth, *_ = fixture()
        for key, bad in [('root_approved', False), ('benchmark_grant_allow', True),
                         ('old_packet_sha256', '0' * 64), ('database', 'unrelated')]:
            changed = {**auth, key: bad}
            with self.assertRaises(ValueError):
                core.authorization(changed, core.canonical(old))

    def test_host_capture_keeps_realistic_secret_payload_out_of_console_and_argv(self):
        values = fixture(); old, auth, sessions, _, _, files, _, _ = values
        packet = core.build_packet(*values)
        service_raw = b'{"access_token":"synthetic-private-service-token"}'
        private = {'packet': packet, 'public': {'service_cli_original_sha256': core.sha(service_raw)},
                   'service_cli_original_b64': base64.b64encode(service_raw).decode()}
        seen = []
        def command(argv, **kwargs):
            seen.append((argv, kwargs))
            if 'exec' in argv:
                if '--version' in argv:
                    return types.SimpleNamespace(returncode=0, stdout=b'timeout (GNU coreutils) 9.1\n')
                if '-c' in argv and 'def audit(' in argv[argv.index('-c') + 1]:
                    return types.SimpleNamespace(returncode=0, stdout=b'{"process_exit_proven":true}')
                prefix = json.dumps({'private_event': 'issued', 'value': 'synthetic-private-service-token'}) + '\n'
                return types.SimpleNamespace(returncode=0, stdout=prefix.encode() + json.dumps(private).encode(), stderr=b'')
            if 'image' in argv:
                return types.SimpleNamespace(stdout=json.dumps({'org.opencontainers.image.revision': core.SOURCE}).encode())
            return types.SimpleNamespace(stdout=json.dumps({'running': True, 'image': 'sha256:' + 'c' * 64,
                'labels': {'com.docker.compose.project': auth['namespace'], 'com.docker.compose.service': 'api'}}).encode())
        with tempfile.TemporaryDirectory() as folder:
            r = Path(folder); arguments = ['host_runner.py', '--api-container', 'synthetic-api',
                                          '--expected-api-image-id', 'sha256:' + 'c' * 64]
            supplied = {'old-packet': core.canonical(old), 'authorization': json.dumps(auth).encode(),
                         'accounts': b'{"manager":{"password":"synthetic-private-password"}}',
                         'ca': files['ca.pem'], 'source-manifest': files['source-manifest.json'],
                         'bundle-manifest': files['backend-bundle-manifest.json'],
                         'import-receipt': files['backend-import-receipt.json']}
            for name, raw in supplied.items():
                p = r / name; p.write_bytes(raw); arguments += ['--' + name, str(p)]
            output = r / 'new'; arguments += ['--output', str(output)]
            stdout = io.StringIO()
            with patch.object(sys, 'argv', arguments), patch.object(host.os, 'geteuid', return_value=0), \
                 patch.object(host.subprocess, 'run', side_effect=command), contextlib.redirect_stdout(stdout):
                self.assertEqual(host.main(), 0)
            visible = stdout.getvalue()
            self.assertNotIn('synthetic-private-password', visible)
            self.assertNotIn('synthetic-private-service-token', visible)
            self.assertNotIn(sessions['developer']['token'], visible)
            self.assertNotIn('synthetic-private-password', str([x[0] for x in seen]))
            self.assertIn(b'synthetic-private-password', next(k['input'] for a, k in seen if 'input' in k))
            invoked = next(a for a, k in seen if 'input' in k)
            self.assertIn('--kill-after=5s', invoked)
            self.assertEqual(invoked[-2], auth['packet_nonce'])
            self.assertEqual((output / 'service-cli.original.private.json').read_bytes(), service_raw)
            self.assertEqual(stat.S_IMODE((output / 'inputs/session.private.json').stat().st_mode), 0o600)

    def test_host_timeout_never_claims_container_process_stopped(self):
        old, auth, _, _, _, files, _, _ = fixture()
        def command(argv, **kwargs):
            if '--version' in argv:
                return types.SimpleNamespace(returncode=0, stdout=b'timeout (GNU coreutils) 9.1\n')
            if 'exec' in argv:
                if 'input' in kwargs:
                    raise host.subprocess.TimeoutExpired(argv, 330, output=b'private-issued-prefix', stderr=b'')
                return types.SimpleNamespace(returncode=0,
                    stdout=b'{"process_exit_proven":false,"status":"MATERIAL_GROUP_STILL_ACTIVE"}')
            if 'image' in argv:
                return types.SimpleNamespace(stdout=json.dumps({'org.opencontainers.image.revision': core.SOURCE}).encode())
            return types.SimpleNamespace(stdout=json.dumps({'running': True, 'image': 'sha256:' + 'c' * 64,
                'labels': {'com.docker.compose.project': auth['namespace'], 'com.docker.compose.service': 'api'}}).encode())
        with tempfile.TemporaryDirectory() as folder:
            r = Path(folder); arguments = ['host_runner.py', '--api-container', 'synthetic-api',
                                          '--expected-api-image-id', 'sha256:' + 'c' * 64]
            supplied = {'old-packet': core.canonical(old), 'authorization': json.dumps(auth).encode(),
                         'accounts': b'{}', 'ca': files['ca.pem'], 'source-manifest': files['source-manifest.json'],
                         'bundle-manifest': files['backend-bundle-manifest.json'], 'import-receipt': files['backend-import-receipt.json']}
            for name, raw in supplied.items():
                p = r / name; p.write_bytes(raw); arguments += ['--' + name, str(p)]
            output = r / 'new'; arguments += ['--output', str(output)]; stdout = io.StringIO()
            with patch.object(sys, 'argv', arguments), patch.object(host.os, 'geteuid', return_value=0), \
                 patch.object(host.subprocess, 'run', side_effect=command), contextlib.redirect_stdout(stdout):
                self.assertEqual(host.main(), 2)
            self.assertFalse(json.loads(stdout.getvalue())['process_exit_proven'])
            self.assertNotIn('private-issued-prefix', stdout.getvalue())
            self.assertEqual((output / 'runtime.stdout.private.jsonl').read_bytes(), b'private-issued-prefix')
            self.assertFalse((output / 'inputs/session.private.json').exists())


if __name__ == '__main__':
    unittest.main()
