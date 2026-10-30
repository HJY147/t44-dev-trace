import base64
import datetime
import hashlib
import importlib.util
from pathlib import Path
import struct
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    'pin_host', ROOT / 'agents/coordinator/manual-recovery/pin_ssh_host.py')
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)
NOW = datetime.datetime(2026, 10, 30, 4, 0, tzinfo=datetime.timezone.utc)
ID = 'i-bp13uag4r4u9r2hge0mu'


def report(marker=0):
    # Synthetic public host-key wire bytes, not a generated private credential.
    wire = struct.pack('>I', 11) + b'ssh-ed25519' + struct.pack('>I', 32) + bytes([marker]) * 32
    return {'kind': 'T44_TEMPORARY_SSH_RECOVERY', 'private_ip': '172.21.182.244',
            'expected_instance_id_from_known_private_ip': ID, 'ssh_service_state': 'active',
            'port': 22, 'authorization_expires_utc': '2026-10-30T06:00:00Z',
            'host_public_key': 'ssh-ed25519 ' + base64.b64encode(wire).decode(),
            'host_fingerprint': 'SHA256:' + base64.b64encode(hashlib.sha256(wire).digest()).decode().rstrip('=')}


class HostPinning(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.key = self.root / 'unused-identity'
        self.key.write_text('not opened or used by these tests')
        self.key.chmod(0o600)
        self.output = self.root / 'pins'

    def write(self, value=None, **kw):
        return M.write_config(value or report(), ID, kw.get('ip', '116.62.22.109'),
                              self.key, self.output, route=kw.get('route', 'direct'), now=NOW)

    def test_valid_report_pins_and_config_has_no_security_bypass(self):
        result = self.write()
        config = Path(result['config']).read_text()
        self.assertIn('StrictHostKeyChecking yes', config)
        self.assertIn('HostKeyAlias ' + ID, config)
        self.assertIn('ClearAllForwardings yes', config)
        self.assertNotIn('ProxyCommand', config)
        self.assertEqual(self.write(), result)

    def test_proxy_is_explicit_optional_route(self):
        result = self.write(route='proxy')
        self.assertIn('ProxyCommand /usr/bin/nc -X 5', Path(result['config']).read_text())

    def test_wrong_machine_refused(self):
        value = report();value['private_ip'] = '172.21.182.245'
        with self.assertRaisesRegex(ValueError, 'EXPECTED_INSTANCE'):
            self.write(value)
        self.assertFalse(self.output.exists())

    def test_expired_report_refused(self):
        value = report();value['authorization_expires_utc'] = NOW.isoformat()
        with self.assertRaisesRegex(ValueError, 'EXPIRED'):
            self.write(value)

    def test_fingerprint_mismatch_refused(self):
        value = report();value['host_fingerprint'] = 'SHA256:wrong'
        with self.assertRaisesRegex(ValueError, 'FINGERPRINT_MISMATCH'):
            self.write(value)

    def test_different_host_key_cannot_replace_existing_pin(self):
        self.write();original = (self.output / 'known_hosts').read_bytes()
        with self.assertRaisesRegex(ValueError, 'HOST_KEY_CHANGED'):
            self.write(report(1))
        self.assertEqual((self.output / 'known_hosts').read_bytes(), original)

    def test_world_readable_identity_refused(self):
        self.key.chmod(0o644)
        with self.assertRaisesRegex(ValueError, '0600_REQUIRED'):
            self.write()

    def test_ssh_argument_injection_and_private_ip_refused(self):
        for ip in ['116.62.22.109 -oProxyCommand=bad', '127.0.0.1', '172.21.182.244']:
            with self.subTest(ip=ip), self.assertRaises(ValueError):
                self.write(ip=ip)

    def test_pin_symlink_refused(self):
        self.output.mkdir();target = self.root / 'unrelated';target.write_text('keep')
        (self.output / 'known_hosts').symlink_to(target)
        with self.assertRaisesRegex(ValueError, 'SYMLINK_REFUSED'):
            self.write()
        self.assertEqual(target.read_text(), 'keep')


if __name__ == '__main__':
    unittest.main()
