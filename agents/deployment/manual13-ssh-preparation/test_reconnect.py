"""Offline checks: no sockets, servers, real keys or cloud operations."""
import base64
import importlib.util
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
SPEC = importlib.util.spec_from_file_location('reconnect', ROOT / 'deployment/cloud-reuse/ssh-reconnect/update_ssh_addresses.py')
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)


class Reconnect(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name).resolve()
        self.pins = self.root / 'original-known-hosts'
        self.identity = self.root / 'test-only-key'
        self.identity.write_text('NOT A PRIVATE KEY; MUST NEVER BE READ')
        self.identity.chmod(0o600)
        prefix = struct.pack('>I', 11) + b'ssh-ed25519' + struct.pack('>I', 32)
        self.pins.write_text(''.join(instance + ' ssh-ed25519 ' + base64.b64encode(prefix + bytes([n]) * 32).decode() + '\n'
                                    for n, instance in enumerate(M.HOSTS, 1)))
        self.output = self.root / 'new-window-pins'

    def tearDown(self):
        self.tmp.cleanup()

    def prepare(self, **changes):
        args = dict(known_hosts=self.pins, identity=self.identity, app_ip='8.8.8.8', load_ip='1.1.1.1', output=self.output)
        args.update(changes)
        return M.prepare(**args)

    def test_preserves_original_pins_and_does_not_read_identity(self):
        original = self.pins.read_bytes()
        real_read = Path.read_bytes
        def read(path):
            self.assertNotEqual(path, self.identity)
            return real_read(path)
        with patch.object(Path, 'read_bytes', read), patch.object(Path, 'read_text', autospec=True, side_effect=lambda p, *a, **k: original.decode() if p == self.pins else self.fail('unexpected text read')):
            receipt = self.prepare()
        self.assertEqual(self.pins.read_bytes(), original)
        self.assertEqual((self.output / 'known_hosts').read_bytes(), original)
        self.assertFalse(receipt['temporary_authorization_verified'])
        self.assertFalse(receipt['connection_attempted'])
        self.assertEqual(self.output.stat().st_mode & 0o777, 0o700)
        self.assertTrue(all(p.stat().st_mode & 0o777 == 0o600 for p in self.output.iterdir()))

    @unittest.skipUnless(shutil.which('ssh'), 'local OpenSSH executable unavailable')
    def test_actual_openssh_parses_both_configs_without_network(self):
        receipt = self.prepare()
        for expected, row in zip(('8.8.8.8', '1.1.1.1'), receipt['configs']):
            result = subprocess.run(['ssh', '-G', '-F', row['config'], row['alias']], capture_output=True, text=True, timeout=10, check=True)
            parsed = dict(line.split(' ', 1) for line in result.stdout.splitlines())
            self.assertEqual(parsed['hostname'], expected)
            self.assertEqual(parsed['hostkeyalias'], row['instance_id'])
            self.assertEqual(parsed['stricthostkeychecking'], 'true')
            self.assertEqual(parsed['clearallforwardings'], 'yes')
            self.assertEqual(parsed['forwardagent'], 'no')
            self.assertEqual(parsed['controlmaster'], 'false')
            self.assertEqual(parsed['updatehostkeys'], 'false')

    def test_existing_output_is_never_overwritten(self):
        self.prepare()
        before = {p.name: p.read_bytes() for p in self.output.iterdir()}
        with self.assertRaisesRegex(ValueError, 'NEW_EXCLUSIVE'):
            self.prepare(app_ip='9.9.9.9')
        self.assertEqual(before, {p.name: p.read_bytes() for p in self.output.iterdir()})

    def test_nonpublic_duplicate_or_injected_ip_zero_output(self):
        for address in ('127.0.0.1', '172.21.182.245', '8.8.8.8\nProxyCommand malicious', '1.1.1.1', '2001:4860:4860::8888'):
            with self.subTest(address=address), self.assertRaises(ValueError):
                self.prepare(app_ip=address)
            self.assertFalse(self.output.exists())

    def test_missing_or_duplicate_instance_pin_zero_output(self):
        rows = self.pins.read_text().splitlines()
        for text in (rows[0] + '\n', rows[0] + '\n' + '\n'.join(rows) + '\n'):
            self.pins.write_text(text)
            with self.assertRaises(ValueError):
                self.prepare()
            self.assertFalse(self.output.exists())

    def test_invalid_host_key_wire_zero_output(self):
        self.pins.write_text(self.pins.read_text().replace('AAAAC3NzaC1lZDI1NTE5', 'AAAAA3NzaC1lZDI1NTE5'))
        with self.assertRaises(ValueError):
            self.prepare()
        self.assertFalse(self.output.exists())

    def test_unsafe_identity_or_symlink_inputs_zero_output(self):
        self.identity.chmod(0o644)
        with self.assertRaises(ValueError):
            self.prepare()
        self.identity.chmod(0o600)
        link = self.root / 'link'
        link.symlink_to(self.pins)
        with self.assertRaises(ValueError):
            self.prepare(known_hosts=link)
        self.assertFalse(self.output.exists())

    def test_recovery_script_stays_original_and_ssh89_compatible(self):
        script = (ROOT / 'deployment/cloud-reuse/ssh-reconnect/01_INSTALL_TEMP_SSH.USER_ONLY.sh').read_text()
        self.assertIn("expiry.astimezone().strftime('%Y%m%d%H%M%S')", script)
        self.assertNotIn("strftime('%Y%m%d%H%M%SZ')", script)
        self.assertIn("'restrict,expiry-time=", script)
        self.assertIn("datetime.timedelta(hours=2)", script)
        subprocess.run(['bash', '-n', str(ROOT / 'deployment/cloud-reuse/ssh-reconnect/01_INSTALL_TEMP_SSH.USER_ONLY.sh')], check=True, capture_output=True)


if __name__ == '__main__':
    unittest.main(verbosity=2)
