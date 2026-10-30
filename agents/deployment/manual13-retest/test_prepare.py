"""Local seam checks; never Docker, SSH, cloud, TLS network or real product calls."""
import importlib.util
import json
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location('resume_chain', ROOT / 'deployment/cloud-reuse/manual13-resume-prepare.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class Chain(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        inputs = self.root / 'old-five'
        inputs.mkdir()
        clients = [{'client_id': i, 'project_id': i // 10 + 1,
                    'transition_task': {'id': i + 1, 'project_id': i // 10 + 1, 'owner_id': 2},
                    'escalation_task': {'id': i + 401, 'project_id': i // 10 + 1, 'owner_id': 2}} for i in range(400)]
        accounts = {role: {'user_id': i + 1, 'username': role, 'password': 'SYNTHETIC'}
                    for i, role in enumerate(('manager', 'developer', 'reviewer'))}
        packet = {'counts': {'projects': 40, 'tasks': 6400, 'dependencies': 9000, 'reviews': 11400, 'decisions': 3600}, 'run_id': 'old', 'inventory': {'clients': clients}, 'environment': {'ca_sha256': m.digest(b'ca')},
            'identity': {'git_commit': m.SOURCE, 'source_manifest_sha256': m.digest(b'{}'),
                         'backend_bundle_manifest_sha256': m.digest(b'{}')},
            'loaded_receipt_sha256': m.digest(b'{}'),
            'sessions': {role: {'user_id': a['user_id']} for role, a in accounts.items()},
            'additional_neutral_snapshots': {'namespace': m.PROJECT, 'database': m.DATABASE}}
        packet['sessions']['service'] = {'user_id': 9}
        raw = (json.dumps(packet,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False)+'\n').encode()
        packet['binding_sha256'] = m.digest(raw)
        for name in ('source-manifest.json','backend-bundle-manifest.json','backend-import-receipt.json'):
            (inputs/name).write_bytes(b'{}')
        (inputs / 'session.private.json').write_text(json.dumps(packet))
        (inputs / 'ca.pem').write_bytes(b'ca')
        (self.root / 'accounts.private.json').write_text(json.dumps(accounts))
        (self.root / 'recipient.pem').write_bytes(b'cert')
        self.a = SimpleNamespace(backend_tools=self.root, deployment_tools=self.root, helper_dir=self.root,
            packet=inputs / 'session.private.json', accounts=self.root / 'accounts.private.json', ca=inputs / 'ca.pem',
            load_cert=self.root / 'recipient.pem', load_cert_sha256=m.digest(b'cert'), openssl='openssl',
            maintenance_id='r30restoretransition06', material_id='r30materialresume06', output=self.root / 'new-output',
            authorize_existing_task_restoration=True, ack_exclusive_no_benchmark_or_other_writer=True, authorize_owned_worker_stop=True)
        self.ids, self.ids_sha = m.inventory(packet)
        self.roles = ('api', 'mysql', 'rabbitmq', 'consumer', 'scheduler', 'web', 'tls-gateway')
        self.expected = {r: {'id': str(i + 1) * 64, 'image_id': 'sha256:' + 'a' * 64, 'running': False} for i, r in enumerate(self.roles)}
        self.trace = []
        self.stage_failure = None
        self.unknown = False
        self.unknown_stop = False
        self.bad_helper = False
        self.bad_counts = False
        self.before_count_drift = None
        self.service_active = True
        self.service_scope_match = True
        self.expired = False
        self.bad_seven = False
        self.tls_fail = False
        self.interrupt = False
        self.cms = SimpleNamespace(modern=lambda unused: None, command=self.cert)
        self.prep = SimpleNamespace(retire_old_timer=lambda *args: self.trace.append('retire'))
        self.resume = SimpleNamespace(PROJECT=m.PROJECT, expected=lambda: self.expected, inspect=self.inspect,
            start=lambda *args: self.trace.append('start:' + ','.join(args[1])), wait=lambda *args: None)

    def cert(self, *args):
        if self.tls_fail:
            raise ValueError('EXPIRED_TLS_CERT')

    def inspect(self, unused):
        if self.bad_seven:
            raise ValueError('EXACT_EXISTING_P09_SEVEN_IDS_REQUIRED')
        return self.expected

    def probe(self, api, ids, name):
        self.trace.append(name)
        is_before = name == 'before-maintenance'
        counts = {'projects': 40, 'tasks': 6400, 'task_dependencies': 9000, 'reviews': 11400, 'decisions': 3600}
        if self.before_count_drift and is_before:
            counts[self.before_count_drift] += 1
        if self.bad_counts and not is_before:
            counts['tasks'] += 1
        return {'service_account': {'id': 9, 'active': self.service_active, 'scope_match': self.service_scope_match}, 'index_layout_sha256': m.LAYOUT,
                'target_index': [['outbox_events', 'ix_outbox_confirmed_recovery', i + 1, col, 1, 'A', None, 'BTREE', 'YES']
                                 for i, col in enumerate(('status', 'event_type', 'id', 'confirmed_at'))],
                'counts': counts, 'original800_count': 800, 'original800_sha256': self.ids_sha,
                'transition400_count': 400, 'transition_state2': 262 if is_before else 400,
                'transition_state3_from2': 138 if is_before else 0}

    def child(self, label, argv, timeout, stdin=None):
        self.trace.append(label)
        if label == 'stop-owned-workers':
            self.assertEqual(argv[3:6], ['stop', '--time', '20'])
            self.assertEqual(set(argv[6:]), {self.expected[r]['id'] for r in ('consumer', 'scheduler') if self.expected[r]['running']})
            if self.unknown_stop:
                raise ValueError('STOP_OUTCOME_UNKNOWN')
            for r in ('consumer', 'scheduler'):
                self.expected[r]['running'] = False
        elif label == 'restore-existing-transition-cohort':
            if self.interrupt:
                raise KeyboardInterrupt()
            if self.unknown:
                raise ValueError('CHILD_FAILED_OR_UNKNOWN_NO_RETRY')
            output = self.a.output / 'maintenance'
            output.mkdir()
            receipt = {'status': 'COMPLETE_EXISTING400_STATE2_ORIGINAL800_PRESERVED', 'preflight400': 400,
                'final400_state2': 399 if self.bad_helper else 400, 'original800_before': 800, 'original800_after': 800,
                'project_task_totals_unchanged': True, 'new_tasks': 0, 'seed_calls': 0, 'exit_code': 0}
            (output / 'receipt.PUBLIC.json').write_text(json.dumps(receipt))
        elif label == 'original-prepare-material06-full-chain':
            output = self.a.output / 'material06'
            (output / 'material').mkdir(parents=True)
            expires = datetime.now(timezone.utc) + timedelta(seconds=100 if self.expired else 3600)
            receipt = {'status': 'FRESH_MATERIAL_NOT_BENCHMARK_AUTHORIZATION', 'new_tasks': 0, 'seed_calls': 0,
                'original_task_ids_preserved': True, 'material_process_exit_proof': {'process_exit_proven': True},
                'counts': {'projects': 40, 'tasks': 6400, 'dependencies': 9000, 'reviews': 11400, 'decisions': 3600},
                'session_attestations': {r: {'expires_at': expires.isoformat()} for r in ('manager', 'developer', 'reviewer', 'service')}}
            (output / 'material/material.PUBLIC.json').write_text(json.dumps(receipt))
            (output / 'APP-ready.PUBLIC.json').write_text(json.dumps({'status': 'APP_MATERIAL_SEALED_NOT_BENCHMARK_AUTHORIZATION'}))
            for row in self.expected.values():
                row['running'] = True
                row['health'] = 'healthy'
        else:
            raise AssertionError(label)
        return b'{}'

    def run_chain(self):
        actual_load = m.load
        def load(path, unused):
            if path.name == 'cohort_maintenance.py':
                file = Path('/Users/yang/Desktop/nothing/软件开发大作业/.agent-worktrees/manual13-backend-preparation/agents/backend/manual11-maintenance/v2/cohort_maintenance.py')
                return actual_load(file, 'actual_backend_preflight')
            return {'cms_five_transport.py': self.cms, 'prepare_next_manual.py': self.prep,
                    'resume_existing_p09.py': self.resume}[path.name]
        with patch.object(m, 'pinned'), patch.object(m, 'load', side_effect=load), patch.object(m.os, 'geteuid', return_value=0):
            pipeline = m.Pipeline(self.a)
            pipeline.child = self.child
            pipeline.probe = self.probe
            return pipeline.run()

    def test_state3_restoration_then_one_original_full_chain(self):
        result = self.run_chain()
        self.assertEqual(result['status'], 'PREPARATION_COMPLETE_NOT_FORMAL_ADMISSION')
        self.assertEqual(self.trace.count('restore-existing-transition-cohort'), 1)
        self.assertEqual(self.trace.count('original-prepare-material06-full-chain'), 1)
        self.assertLess(self.trace.index('after-maintenance'), self.trace.index('original-prepare-material06-full-chain'))
        self.assertEqual(len([x for x in self.trace if x.startswith('start:')]), 3)
        with self.assertRaises(ValueError):
            self.run_chain()  # No rerun into existing output.

    def test_realistic_boot_seven_running_stops_only_owned_two(self):
        for row in self.expected.values():
            row['running'] = True
        result = self.run_chain()
        self.assertEqual(result['status'], 'PREPARATION_COMPLETE_NOT_FORMAL_ADMISSION')
        self.assertEqual(self.trace.count('stop-owned-workers'), 1)
        self.assertLess(self.trace.index('stop-owned-workers'), self.trace.index('restore-existing-transition-cohort'))
        self.assertEqual(result['owned_worker_state'], 'ALL_SEVEN_RUNNING_CONFIGURED_HEALTHCHECKS_PASSED')

    def test_unknown_worker_stop_blocks_helper_and_material(self):
        self.expected['consumer']['running'] = True
        self.expected['scheduler']['running'] = True
        self.unknown_stop = True
        with self.assertRaises(ValueError):
            self.run_chain()
        self.assertNotIn('restore-existing-transition-cohort', self.trace)
        self.assertNotIn('original-prepare-material06-full-chain', self.trace)
        result = json.loads((self.a.output / 'continuation.PUBLIC.json').read_text())
        self.assertEqual(result['stage'], 'stop-owned-consumer-scheduler')
        self.assertEqual(result['owned_worker_state'], 'STOP_REQUESTED_OUTCOME_UNKNOWN')

    def test_real_frozen_backend_authorization_accepts_wrapper_contract(self):
        helper = Path('/Users/yang/Desktop/nothing/软件开发大作业/.agent-worktrees/manual13-backend-preparation/agents/backend/manual11-maintenance/v2/cohort_maintenance.py')
        backend = m.load(helper, 'frozen_backend_authorization')
        accounts = {role: {'user_id': i + 1, 'username': role, 'password': 'SYNTHETIC'}
                    for i, role in enumerate(('manager', 'developer', 'reviewer'))}
        clients = []
        for i in range(400):
            pid = i // 10 + 1
            clients.append({'client_id': i, 'project_id': pid,
                'transition_task': {'id': i + 1, 'project_id': pid, 'owner_id': 2},
                'escalation_task': {'id': i + 401, 'project_id': pid, 'owner_id': 2}})
        packet = {'identity': {'git_commit': m.SOURCE}, 'run_id': 'r30old', 'inventory': {'clients': clients},
            'sessions': {role: {'user_id': a['user_id']} for role, a in accounts.items()},
            'additional_neutral_snapshots': {'namespace': m.PROJECT, 'database': m.DATABASE}}
        packet['binding_sha256'] = backend.sha(backend.canonical(packet))
        raw = json.dumps(packet).encode()
        ids, ids_sha = m.inventory(packet)
        auth = m.maintenance_authorization(raw, ids_sha, 'separate-maintenance05')
        items, accepted_ids = backend.authorization(packet, raw, auth, accounts)
        self.assertEqual(len(items), 400)
        self.assertEqual(accepted_ids, ids['ids'])

    def test_missing_original_manifest_blocks_before_live_mutation(self):
        (self.a.packet.parent / 'source-manifest.json').unlink()
        with self.assertRaises(ValueError):
            self.run_chain()
        self.assertEqual(self.trace, [])
        self.assertFalse(self.a.output.exists())

    def test_changed_original_import_blocks_before_live_mutation(self):
        (self.a.packet.parent / 'backend-import-receipt.json').write_text('{"wrong": true}')
        with self.assertRaises(ValueError):
            self.run_chain()
        self.assertEqual(self.trace, [])
        self.assertFalse(self.a.output.exists())

    def test_actual_old_timer_not_found_and_boot_seven_running(self):
        original = Path('/Users/yang/Desktop/nothing/软件开发大作业/.agent-worktrees/.runtime/manual12-repair-kit/deployment/prepare_next_manual.py')
        self.prep = m.load(original, 'actual_original_timer_preflight')
        for row in self.expected.values():
            row['running'] = True
        calls = []
        def raw_systemctl(argv, **kwargs):
            calls.append(argv)
            self.assertEqual(argv[:2], ['systemctl', 'show'])
            raw = ('Id=' + argv[2] + '\nLoadState=not-found\nActiveState=inactive\nUnitFileState=\n').encode()
            return SimpleNamespace(returncode=1, stdout=raw, stderr=b'')
        with patch.object(self.prep.subprocess, 'run', side_effect=raw_systemctl):
            result = self.run_chain()
        self.assertEqual(result['status'], 'PREPARATION_COMPLETE_NOT_FORMAL_ADMISSION')
        self.assertEqual(len(calls), 6)
        self.assertEqual(self.trace.count('stop-owned-workers'), 1)
        self.assertEqual(self.trace.count('restore-existing-transition-cohort'), 1)
        timer = json.loads((self.a.output / 'bootstrap/old-timer.PUBLIC.json').read_text())
        self.assertEqual(timer['before']['t44-final-p09-continuous.service']['LoadState'], 'not-found')

    def test_unknown_partial_post_blocks_material(self):
        self.unknown = True
        with self.assertRaises(ValueError):
            self.run_chain()
        self.assertNotIn('original-prepare-material06-full-chain', self.trace)
        self.assertEqual(json.loads((self.a.output / 'continuation.PUBLIC.json').read_text())['status'],
                         'BLOCKED_PRESERVE_PREFIX_NO_AUTOMATIC_RETRY')

    def test_interruption_never_continues_to_material(self):
        self.interrupt = True
        with self.assertRaises(KeyboardInterrupt):
            self.run_chain()
        self.assertNotIn('original-prepare-material06-full-chain', self.trace)

    def test_state3_remaining_blocks(self):
        self.bad_helper = True
        with self.assertRaises(ValueError):
            self.run_chain()
        self.assertNotIn('original-prepare-material06-full-chain', self.trace)

    def test_expired_tls_blocks_before_infra(self):
        self.tls_fail = True
        with self.assertRaises(ValueError):
            self.run_chain()
        self.assertEqual(self.trace, [])

    def test_expired_new_session_never_ready(self):
        self.expired = True
        with self.assertRaises(ValueError):
            self.run_chain()
        self.assertNotIn('after-material06', self.trace)

    def test_original_seven_mismatch_blocks_before_start(self):
        self.bad_seven = True
        with self.assertRaises(ValueError):
            self.run_chain()
        self.assertEqual(self.trace, [])

    def test_changed_counts_block_material(self):
        self.bad_counts = True
        with self.assertRaises(ValueError):
            self.run_chain()
        self.assertNotIn('original-prepare-material06-full-chain', self.trace)

    def test_each_original_count_drift_blocks_before_http_maintenance(self):
        for table in ('projects', 'tasks', 'task_dependencies', 'reviews', 'decisions'):
            with self.subTest(table=table):
                self.a.output = self.root / ('drift-' + table)
                self.trace.clear()
                self.before_count_drift = table
                with self.assertRaisesRegex(ValueError, 'ORIGINAL_PACKET_BUSINESS_COUNTS_CHANGED_BEFORE_MAINTENANCE'):
                    self.run_chain()
                self.assertNotIn('restore-existing-transition-cohort', self.trace)
                self.assertNotIn('original-prepare-material06-full-chain', self.trace)
                self.assertFalse((self.a.output / 'maintenance-authorization.PUBLIC.json').exists())
                summary = json.loads((self.a.output / 'continuation.PUBLIC.json').read_text())
                self.assertEqual(summary['status'], 'BLOCKED_PRESERVE_PREFIX_NO_AUTOMATIC_RETRY')

    def test_original_service_inactive_or_wrong_namespace_blocks_before_http(self):
        for scenario in ('inactive', 'wrong-namespace'):
            with self.subTest(scenario=scenario):
                self.a.output = self.root / scenario
                self.trace.clear()
                self.service_active = scenario != 'inactive'
                self.service_scope_match = scenario != 'wrong-namespace'
                with self.assertRaisesRegex(ValueError, 'EXISTING_SERVICE_ACCOUNT_SCOPE_BEFORE_MAINTENANCE'):
                    self.run_chain()
                self.assertNotIn('restore-existing-transition-cohort', self.trace)
                self.assertNotIn('original-prepare-material06-full-chain', self.trace)
                self.assertFalse((self.a.output / 'maintenance-authorization.PUBLIC.json').exists())

    def test_missing_index_blocks_without_ddl(self):
        row = self.probe(None, self.ids, 'before-maintenance')
        row['target_index'] = []
        with self.assertRaises(ValueError):
            m.check_probe(row, self.ids_sha)
        self.assertNotIn('ALTER', m.PROBE)
        self.assertNotIn('CREATE', m.PROBE)

    def test_real_child_timeout_preserves_prefix_and_exits(self):
        self.a.output.mkdir()
        with self.assertRaises(Exception):
            m.Pipeline(self.a).child('local-timeout', [sys.executable, '-c', 'import time;time.sleep(60)'], .02)
        row = json.loads((self.a.output / '01-local-timeout.PUBLIC.json').read_text())
        self.assertEqual(row['status'], 'BLOCKED_PARTIAL_OR_UNKNOWN_NO_RETRY')
        self.assertIsNotNone(row['exit_code'])

    def test_exact06_ids_reject_old_or_qa_before_child(self):
        for material, maintenance in [('r30materialresume05', 'r30restoretransition06'),
                                      ('r30materialresume06','r30manualp13'),
                                      ('r30materialresume06','r30restoretransition05')]:
            self.a.material_id, self.a.maintenance_id = material, maintenance
            with self.assertRaisesRegex(ValueError, 'EXACT_MAINTENANCE06_AND_MATERIAL06_REQUIRED'):
                self.run_chain()
            self.assertEqual(self.trace, [])


if __name__ == '__main__':
    unittest.main()
