"""No Docker/SSH: fake subprocess results; real temporary atomic filesystem writes."""
import importlib.util
from pathlib import Path
import stat
import subprocess
import tempfile
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('direct_start', HERE / 'start.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
BACKEND = HERE.parents[1] / 'backend/fast-bootstrap'


class Checks(unittest.TestCase):
    def setup_run(self, folder, failure=None):
        target = folder / 'scheduler-token.json'
        m.write(target, b'{"access_token":"OLD-SYNTHETIC"}\n')
        calls = []
        new = b'{ "access_token" : "NEW-SYNTHETIC", "expires_at":"2030-01-01Z" }\n'

        def runner(argv, **kwargs):
            calls.append(argv)
            label = 'bootstrap' if '--old-packet' in argv else ('workers' if m.IDS['consumer'] in argv else 'infra')
            if label == failure:
                return subprocess.CompletedProcess(argv, 3, b'PRIVATE-FAIL', b'PRIVATE-ERR')
            if label == 'bootstrap':
                out = Path(argv[argv.index('--output') + 1])
                out.mkdir(mode=0o700)
                m.public(out / 'bootstrap.PUBLIC.json', {'status': 'DIRECT_INITIALIZATION_COMPLETE',
                    'run_id': 'direct-test', 'source_expected': m.SOURCE})
                m.public(out / 'current-inputs.private.json', {'schema': 'DIRECT_INPUTS_V1',
                    'run_id': 'direct-test', 'sessions': {'service': {'token': 'NEW-SYNTHETIC'}}})
                m.write(out / 'service-cli.original.private.json', new)
            return subprocess.CompletedProcess(argv, 0, b'PRIVATE-OK', b'')
        return target, calls, new, runner

    def test_full_path_real_atomic_rotation(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp).resolve()
            target, calls, new, runner = self.setup_run(folder)
            before = target.stat()
            output = folder / 'run'
            result = m.execute(BACKEND, 'direct-test', output, runner, target)
            self.assertEqual(result['status'], 'INIT_DONE')
            self.assertEqual(len(calls), 3)
            self.assertEqual(calls[0][:4], ['docker', '--context', 'default', 'start'])
            self.assertEqual(calls[0][4:], [m.IDS[k] for k in ('mysql','rabbitmq','tls','api','web')])
            self.assertEqual(calls[2][4:], [m.IDS['consumer'], m.IDS['scheduler']])
            self.assertEqual(target.read_bytes(), new)
            self.assertNotEqual(target.stat().st_ino, before.st_ino)
            self.assertEqual((target.stat().st_uid, target.stat().st_gid), (before.st_uid, before.st_gid))
            self.assertEqual(stat.S_IMODE(target.stat().st_mode), 0o600)
            self.assertEqual((output/'rotation/scheduler-token.original.private.json').read_bytes(),
                             b'{"access_token":"OLD-SYNTHETIC"}\n')
            public_text = ''.join(p.read_text() for p in output.rglob('*.PUBLIC.json'))
            self.assertNotIn('SYNTHETIC', public_text)
            self.assertFalse(result['benchmark_started'])

    def test_subprocess_failure_stops_no_retry(self):
        for label, expected in [('infra',1),('bootstrap',2),('workers',3)]:
            with self.subTest(label=label), tempfile.TemporaryDirectory() as tmp:
                folder = Path(tmp).resolve()
                target, calls, _, runner = self.setup_run(folder, label)
                with self.assertRaises(ValueError):
                    m.execute(BACKEND, 'direct-test', folder/'run', runner, target)
                self.assertEqual(len(calls), expected)
                self.assertFalse((folder/'run/INIT_DONE.PUBLIC.json').exists())
                self.assertTrue((folder/'run/FAILED.PUBLIC.json').exists())
                if label != 'workers':
                    self.assertIn(b'OLD-SYNTHETIC', target.read_bytes())

    def test_rotation_failure_does_not_start_workers(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp).resolve()
            target, calls, _, runner = self.setup_run(folder)
            with patch.object(m.os, 'replace', side_effect=OSError('injected')), self.assertRaises(OSError):
                m.execute(BACKEND, 'direct-test', folder/'run', runner, target)
            self.assertEqual(len(calls), 2)
            self.assertIn(b'OLD-SYNTHETIC', target.read_bytes())
            self.assertFalse(list(folder.glob('.direct-token-*')))
            self.assertTrue((folder/'run/rotation/scheduler-token.original.private.json').exists())

    def test_mismatched_service_bytes_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp).resolve()
            target, calls, _, runner = self.setup_run(folder)
            def swapped(argv, **kwargs):
                result = runner(argv, **kwargs)
                if '--old-packet' in argv:
                    out = Path(argv[argv.index('--output')+1])
                    (out/'service-cli.original.private.json').write_bytes(b'{"access_token":"WRONG"}')
                return result
            with self.assertRaises(ValueError):
                m.execute(BACKEND, 'direct-test', folder/'run', swapped, target)
            self.assertEqual(len(calls), 2)

    def test_pin_and_existing_output_reject_before_docker(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp).resolve()
            target, calls, _, runner = self.setup_run(folder)
            (folder/'run').mkdir()
            with self.assertRaises(FileExistsError):
                m.execute(BACKEND, 'direct-test', folder/'run', runner, target)
            (folder/'bootstrap.py').write_bytes(b'incorrect source')
            with self.assertRaises(ValueError):
                m.execute(folder, 'direct-test', folder/'new', runner, target)
            self.assertEqual(calls, [])


if __name__ == '__main__':
    unittest.main()
