"""No Docker/SSH: fake subprocess results; real temporary atomic filesystem writes."""
import importlib.util
import json
import hashlib
import http.server
import ssl
import threading
import time
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
BACKEND = HERE.parents[1] / 'backend/direct-p18-bootstrap'


class Checks(unittest.TestCase):
    def setup_run(self, folder, failure=None):
        m.P09 = folder / 'P09'
        inputs = m.P09 / 'P-packet/output/packet/inputs'
        inputs.mkdir(parents=True)
        (inputs / 'ca.pem').write_bytes(b'SYNTHETIC-CA')
        (inputs / 'session.private.json').write_text(json.dumps({'environment': {
            'origin': 'https://original.test', 'ca_sha256': hashlib.sha256(b'SYNTHETIC-CA').hexdigest()}}))
        target = folder / 'scheduler-token.json'
        m.write(target, b'{"access_token":"OLD-SYNTHETIC"}\n')
        calls = []
        new = b'{ "access_token" : "NEW-SYNTHETIC", "expires_at":"2030-01-01Z" }\n'

        def runner(argv, **kwargs):
            calls.append(argv)
            label = ('bootstrap' if '--old-packet' in argv else
                     'stop' if 'stop' in argv else
                     'readiness' if 'exec' in argv else
                     'workers' if m.IDS['consumer'] in argv else 'infra')
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
            self.assertEqual(len(calls), 5)
            self.assertEqual(calls[0], ['docker', '--context', 'default', 'stop', m.IDS['consumer'], m.IDS['scheduler']])
            self.assertEqual(calls[1][:4], ['docker', '--context', 'default', 'start'])
            self.assertEqual(calls[1][4:], [m.IDS[k] for k in ('mysql','rabbitmq','tls','api','web')])
            self.assertEqual(calls[4][4:], [m.IDS['consumer'], m.IDS['scheduler']])
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
        for label, expected in [('stop',1),('infra',2),('readiness',3),('bootstrap',4),('workers',5)]:
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
            self.assertEqual(len(calls), 4)
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
            self.assertEqual(len(calls), 4)

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


class ConnectivityChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location('direct_readiness', HERE / 'readiness.py')
        cls.r = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.r)

    def test_real_tls_delayed_ready_and_db_failure_then_success(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            key, cert = folder/'key.pem', folder/'cert.pem'
            subprocess.run(['openssl', 'req', '-x509', '-newkey', 'rsa:2048', '-nodes',
                '-keyout', str(key), '-out', str(cert), '-days', '1', '-subj', '/CN=localhost',
                '-addext', 'subjectAltName=DNS:localhost'], capture_output=True, check=True)
            ready = threading.Event()
            paths = []
            behavior = {'status': 405, 'allow': 'GET'}
            class Handler(http.server.BaseHTTPRequestHandler):
                def do_OPTIONS(self):
                    paths.append((self.command, self.path, self.headers.get('Host'), self.headers.get('Authorization')))
                    self.send_response(behavior['status'] if ready.is_set() else 503)
                    self.send_header('Allow', behavior['allow'])
                    self.send_header('X-Request-ID', 'local-read-only-probe')
                    body = b'{"detail":"Method Not Allowed"}'
                    self.send_header('Content-Length', str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)
                def log_message(self, *unused):
                    pass
            server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Handler)
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            context.load_cert_chain(cert, key)
            server.socket = context.wrap_socket(server.socket, server_side=True)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            tries = []
            def db():
                tries.append('SELECT 1')
                if len(tries) == 1:
                    raise ConnectionRefusedError('synthetic DB unready')
            timer = threading.Timer(0.25, ready.set)
            timer.start()
            try:
                result = self.r.wait_ready(db, lambda: self.r.tls_probe('https://localhost',
                    cert.read_text(), '127.0.0.1', server.server_port), budget=2)
                self.assertEqual(result['status'], 'CONNECTIONS_READY')
                self.assertGreaterEqual(len(tries), 3)
                self.assertTrue(paths)
                self.assertTrue(all(p == ('OPTIONS', '/api/v1/projects', 'localhost', None) for p in paths))
                behavior.update(status=405, allow='POST')
                self.r.tls_probe('https://localhost', cert.read_text(),
                                 '127.0.0.1', server.server_port)
                for status, allow in [(404, 'GET'), (405, ''), (503, 'POST'), (405, 'DELETE')]:
                    behavior.update(status=status, allow=allow)
                    with self.assertRaises(RuntimeError):
                        self.r.tls_probe('https://localhost', cert.read_text(),
                                         '127.0.0.1', server.server_port)
                with self.assertRaises(ssl.SSLCertVerificationError):
                    self.r.tls_probe('https://wrong-host.invalid', cert.read_text(),
                                     '127.0.0.1', server.server_port)
            finally:
                timer.cancel()
                server.shutdown()
                server.server_close()
                thread.join()

    def test_failure_deadline_and_late_success_rejected_without_sessions(self):
        now = [0.0]
        calls = []
        def sleep(seconds):
            now[0] += seconds
        def fail():
            calls.append('SELECT 1')
            raise ConnectionRefusedError('not logged')
        with self.assertRaises(RuntimeError):
            self.r.wait_ready(fail, lambda: calls.append('HTTPS'), budget=0.5,
                              clock=lambda: now[0], sleep=sleep)
        self.assertEqual(now[0], 0.5)
        self.assertNotIn('HTTPS', calls)
        now[0] = 0.0
        def late():
            now[0] = 1.1
        with self.assertRaises(RuntimeError):
            self.r.wait_ready(lambda: None, late, budget=1,
                              clock=lambda: now[0], sleep=sleep)


if __name__ == '__main__':
    unittest.main()
