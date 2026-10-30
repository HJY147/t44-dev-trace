import base64
from datetime import datetime, timedelta, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import tempfile
import unittest

SOURCE = Path(__file__).resolve().parents[3] / 'deployment/cloud-reuse/manual13-retest/check_ssh_window.py'
spec = importlib.util.spec_from_file_location('check_ssh_window', SOURCE)
window = importlib.util.module_from_spec(spec)
spec.loader.exec_module(window)


class WindowChecks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()
        self.now = datetime(2026, 10, 30, 14, 0, tzinfo=timezone.utc)
        self.ids = ['i-bp13uag4r4u9r2hge0mt', 'i-bp13uag4r4u9r2hge0mu']
        self.reports, entries = {}, []
        for index, instance in enumerate(self.ids):
            wire = struct.pack('>I', 11) + b'ssh-ed25519' + struct.pack('>I', 32) + bytes([index + 1]) * 32
            encoded = base64.b64encode(wire).decode()
            host = 'ssh-ed25519 ' + encoded
            fingerprint = 'SHA256:' + base64.b64encode(hashlib.sha256(wire).digest()).decode().rstrip('=')
            row = dict(kind='T44_TEMPORARY_SSH_RECOVERY',
                       private_ip=['172.21.182.245', '172.21.182.244'][index],
                       expected_instance_id_from_known_private_ip=instance,
                       ssh_service_state='active', port=22, host_public_key=host,
                       host_fingerprint=fingerprint,
                       installed_utc=(self.now - timedelta(minutes=10)).isoformat(),
                       authorization_expires_utc=(self.now + timedelta(minutes=110)).isoformat(),
                       authorized_key_options='restrict,expiry-time; no forwarding')
            path = self.root / (instance + '.PUBLIC.json')
            path.write_text(json.dumps(row))
            self.reports[instance] = path
            entries.append(instance + ' ' + host)
        self.hosts = self.root / 'known_hosts'
        self.hosts.write_text('\n'.join(entries) + '\n')

    def tearDown(self):
        self.temp.cleanup()

    def modify(self, instance=None, **values):
        path = self.reports[instance or self.ids[0]]
        row = json.loads(path.read_text())
        row.update(values)
        path.write_text(json.dumps(row))

    def test_fresh_both_original_pins_only_local(self):
        result = window.check(self.hosts, self.reports, self.now)
        self.assertEqual(result['required_seconds'], 3600)
        self.assertFalse(result['connection_attempted'])
        self.assertFalse(result['benchmark_authorized'])
        self.assertFalse(result['actual_authorization_validity_proven'])

    def test_exact_one_hour_boundary_accepted(self):
        self.modify(installed_utc=(self.now - timedelta(hours=1)).isoformat(),
                    authorization_expires_utc=(self.now + timedelta(hours=1)).isoformat())
        self.assertEqual(window.check(self.hosts, self.reports, self.now)['receipts'][0]['remaining_seconds'], 3600)

    def test_prior_window_has_insufficient_recovery_margin(self):
        self.modify(installed_utc=(self.now - timedelta(minutes=61)).isoformat(),
                    authorization_expires_utc=(self.now + timedelta(minutes=59)).isoformat())
        with self.assertRaisesRegex(ValueError, 'SSH_WINDOW_BELOW'):
            window.check(self.hosts, self.reports, self.now)

    def test_cannot_silently_extend_original_two_hour_permission(self):
        self.modify(authorization_expires_utc=(self.now + timedelta(hours=4)).isoformat())
        with self.assertRaisesRegex(ValueError, 'ORIGINAL_TWO_HOUR'):
            window.check(self.hosts, self.reports, self.now)

    def test_missing_report_or_replaced_original_pin_refused(self):
        with self.assertRaisesRegex(ValueError, 'BOTH_ORIGINAL'):
            window.check(self.hosts, {self.ids[0]: self.reports[self.ids[0]]}, self.now)
        self.hosts.write_text(self.hosts.read_text().replace(self.ids[0], 'unknown-host'))
        with self.assertRaisesRegex(ValueError, 'EXACT_ORIGINAL'):
            window.check(self.hosts, self.reports, self.now)

    def test_changed_options_or_instance_refused(self):
        self.modify(authorized_key_options='unrestricted')
        with self.assertRaisesRegex(ValueError, 'ORIGINAL_RESTRICTED'):
            window.check(self.hosts, self.reports, self.now)
        self.modify(authorized_key_options='restrict,expiry-time; no forwarding',
                    expected_instance_id_from_known_private_ip=self.ids[1])
        with self.assertRaisesRegex(ValueError, 'EXPECTED_INSTANCE'):
            window.check(self.hosts, self.reports, self.now)

    def test_expired_report_and_symlink_refused(self):
        self.modify(authorization_expires_utc=(self.now - timedelta(seconds=1)).isoformat())
        with self.assertRaisesRegex(ValueError, 'EXPIRED'):
            window.check(self.hosts, self.reports, self.now)
        target = self.reports[self.ids[1]]
        link = self.root / 'symlink.PUBLIC.json'
        link.symlink_to(target)
        self.reports[self.ids[1]] = link
        with self.assertRaises(ValueError):
            window.bounded_json(link)


if __name__ == '__main__':
    unittest.main()
