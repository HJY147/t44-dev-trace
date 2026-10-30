"""Pure projection/negative checks; no Docker, network, cloud or credentials."""
import importlib.util
import json
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location('manual13_observer', ROOT / 'deployment/cloud-reuse/manual13-observe.py')
observe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(observe)


def raw_mysql(status=None, resize='OK'):
    status = status or {}
    rows = ['CAPACITY\t384', 'LOCKS\t0', 'DIGEST_TOTAL\t0\t0\t0\t0\t0',
            'FILE_IO_TOTAL\t0\t0\t0\t0\t0\t0']
    rows += [key + '\t' + str(value) for key, value in status.items()]
    if resize is not None:
        rows += ['Innodb_redo_log_resize_status\t' + resize]
    return '\n'.join(rows) + '\n'


WAITS = ('WAIT_COVERAGE\t4\t3\t2\t40\t1000\n'
         'wait/io/file/innodb/innodb_log_file\tYES\tYES\t20\t700\t2\t70\n'
         'wait/synch/mutex/innodb/log_writer_mutex\tYES\tYES\t20\t300\t1\t30\n')


class Observer(unittest.TestCase):
    def test_redo_status_checkpoint_age_and_exact_fields(self):
        with patch.object(observe, 'command', return_value=raw_mysql({
            'Innodb_redo_log_current_lsn': 9000, 'Innodb_redo_log_checkpoint_lsn': 1000,
            'Innodb_redo_log_capacity_resized': 104857600, 'Innodb_buffer_pool_bytes_dirty': 256})):
            result = observe.mysql('a' * 64)
        self.assertEqual(result['checkpoint_age']['bytes'], 8000)
        self.assertEqual(result['redo_resize_status']['Innodb_redo_log_resize_status'], 'OK')
        self.assertEqual(result['status']['Innodb_redo_log_capacity_resized'], 104857600)
        self.assertIn('Innodb_redo_log_flushed_to_disk_lsn', result['unavailable_status_fields'])

    def test_absent_lsn_or_resize_never_zero(self):
        with patch.object(observe, 'command', return_value=raw_mysql({}, resize=None)):
            result = observe.mysql('a' * 64)
        self.assertFalse(result['checkpoint_age']['available'])
        self.assertIsNone(result['checkpoint_age']['bytes'])
        self.assertIn('Innodb_redo_log_resize_status', result['unavailable_text_status_fields'])
        self.assertNotIn('Innodb_redo_log_capacity_resized', result['status'])

    def test_old_lsn_names_and_reset_are_explicit(self):
        old = {'Innodb_lsn_current': 70, 'Innodb_lsn_last_checkpoint': 50}
        self.assertEqual(observe.checkpoint_age(old)['bytes'], 20)
        old['Innodb_lsn_last_checkpoint'] = 100
        value = observe.checkpoint_age(old)
        self.assertFalse(value['available'])
        self.assertIsNone(value['bytes'])
        self.assertEqual(value['missing_reason'], 'LSN_SAMPLE_INCONSISTENT_OR_RESET')

    def test_resize_enum_and_numeric_projection_are_strict(self):
        for raw in (raw_mysql({}, 'secret text'), raw_mysql({'Innodb_redo_log_current_lsn': 'NULL'}),
                    raw_mysql({'PASSWORD': 'secret'})):
            with patch.object(observe, 'command', return_value=raw), self.assertRaises(ValueError):
                observe.mysql('a' * 64)

    def test_effective_autoincrement_durability_and_redo(self):
        with patch.object(observe, 'command', return_value=(
            'innodb_autoinc_lock_mode\t2\ninnodb_redo_log_capacity\t104857600\n'
            'innodb_flush_log_at_trx_commit\t1\nsync_binlog\t1\n')):
            value = observe.mysql_config('a' * 64)
        self.assertTrue(value['available'])
        self.assertEqual(value['values']['innodb_autoinc_lock_mode'], 2)
        self.assertEqual(value['values']['sync_binlog'], 1)
        self.assertIn('innodb_io_capacity', value['unavailable_fields'])

    def test_config_null_or_error_unavailable_not_zero(self):
        for raw in ('innodb_autoinc_lock_mode\tNULL', 'PASSWORD\tsecret'):
            with patch.object(observe, 'command', return_value=raw):
                value = observe.mysql_config('a' * 64)
            self.assertFalse(value['available'])
            self.assertIsNone(value['values'])
            self.assertNotIn('secret', json.dumps(value))

    def test_wait_aggregate_and_event_names_only(self):
        with patch.object(observe, 'command', return_value=WAITS):
            value = observe.mysql_waits('a' * 64)
        self.assertTrue(value['available'])
        self.assertEqual(value['coverage']['sum_timer_wait_ps'], 1000)
        self.assertEqual(value['coverage']['timed_instruments'], 2)
        self.assertEqual(len(value['top20_by_cumulative_timer']), 2)
        self.assertFalse(value['sql_text_or_parameters_collected'])
        self.assertNotIn('DIGEST_TEXT', observe.WAITS_SQL)
        self.assertNotIn('SQL_TEXT', observe.WAITS_SQL)

    def test_waits_absence_permission_null_and_injection_unavailable(self):
        for raw in ('', 'WAIT_COVERAGE\t0\tNULL\tNULL\tNULL\tNULL',
                    WAITS.replace('700', 'NULL'), WAITS.replace('wait/io/file/innodb/innodb_log_file', 'SELECT password'),
                    WAITS + WAITS.splitlines()[1] + '\n'):
            with patch.object(observe, 'command', return_value=raw):
                value = observe.mysql_waits('a' * 64)
            self.assertFalse(value['available'])
            self.assertIsNone(value['top20_by_cumulative_timer'])
        with patch.object(observe, 'command', side_effect=ValueError('private message')):
            value = observe.mysql_waits('a' * 64)
        self.assertFalse(value['available'])
        self.assertNotIn('private message', json.dumps(value))

    def test_disabled_or_untimed_instruments_not_zero_waiting(self):
        for enabled, timed in ((0, 0), (2, 0)):
            raw = WAITS.replace('4\t3\t2\t40\t1000', f'4\t{enabled}\t{timed}\t40\t1000')
            with patch.object(observe, 'command', return_value=raw):
                value = observe.mysql_waits('a' * 64)
            self.assertFalse(value['available'])
            self.assertIsNone(value['top20_by_cumulative_timer'])
            self.assertEqual(value['missing_reason'], 'WAIT_INSTRUMENTATION_DISABLED_OR_UNTIMED')

    def test_new_optional_query_cannot_exceed_original_deadline(self):
        with patch.object(observe, 'DEADLINE', 0), patch.object(observe.subprocess, 'run') as spy:
            value = observe.mysql_waits('a' * 64)
            self.assertFalse(value['available'])
            spy.assert_not_called()
        with patch.object(observe, 'command', side_effect=subprocess.TimeoutExpired('readonly', 1)):
            self.assertFalse(observe.mysql_waits('a' * 64)['available'])

    def test_command_spy_preserves_roles_and_adds_one_bounded_query(self):
        calls = []
        containers = {role: str(index + 1) * 64 for index, role in enumerate(observe.ROLES)}
        def fake(argv):
            calls.append(argv)
            if argv[3] == 'inspect':
                return '\n'.join(json.dumps(v) for v in (argv[-1], 'sha256:' + 'f' * 64, True, {'Memory': 123}))
            if argv[-1] == observe.CGROUP:
                return 'FILE:cpu.stat\nusage_usec 42\n'
            if argv[-1] == observe.PROCESS:
                return '{"processes":[],"pool":{}}'
            if argv[-1] == observe.SQL:
                return raw_mysql({})
            if argv[-1] == observe.CONFIG_SQL:
                return 'innodb_autoinc_lock_mode\t2\n'
            if argv[-1] in (observe.DIGEST_CANDIDATE_SQL, observe.DIGEST_TOP_SQL):
                return ''
            if argv[-1] == observe.WAITS_SQL:
                return WAITS
            raise AssertionError(argv)
        with patch.object(observe, 'command', fake):
            value = observe.observe(containers)
        self.assertEqual(set(value['services']), set(observe.ROLES))
        self.assertEqual(len(calls), 20)
        self.assertTrue(all(call[3] in ('exec', 'inspect') for call in calls))
        self.assertTrue(value['services']['mysql']['mysql']['global_waits']['available'])
        self.assertNotIn('MYSQL_ROOT_PASSWORD', json.dumps(value))


if __name__ == '__main__':
    unittest.main()
