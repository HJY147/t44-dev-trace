"""Actual HTTP parser with synthetic connection; no service, session, cloud or runtime files."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
CODE = Path('/Users/yang/Desktop/nothing/软件开发大作业/.agent-worktrees/backend-neutral-r30/agents/backend/neutral-r30-cas')
spec = importlib.util.spec_from_file_location('review_cas_http', CODE / 'http_primitives.py')
http = importlib.util.module_from_spec(spec)
spec.loader.exec_module(http)


class Response:
    def __init__(self, status, value):
        self.status = status
        self.raw = json.dumps(value).encode()

    def read(self, cap):
        return self.raw[:cap]


class Connection:
    def __init__(self, response):
        self.response, self.requests = response, []

    def request(self, *args, **kwargs):
        self.requests.append((args, kwargs))

    def getresponse(self):
        return self.response


class Boundary(unittest.TestCase):
    def test_rejections_keep_actual_wire_outcome_and_only_one_attempt(self):
        envelope = {'code': 'VERSION_CONFLICT', 'message': 'synthetic conflict', 'request_id': 'synthetic-response', 'audit_id': 7, 'current_version': 99, 'current_state': 1, 'original_error_code': None, 'violations': []}
        for status, value in [(409, envelope), (403, envelope), (503, envelope), (409, {'error': {'code': 'VERSION_CONFLICT'}}), (200, envelope)]:
            with self.subTest(status=status, value=value), tempfile.TemporaryDirectory(prefix='755-http-') as directory:
                output = Path(directory)
                response = Response(status, value)
                connection = Connection(response)
                client = http.Client('https://10.0.0.1', output / 'no-ca-not-used', output, float('inf'))
                client.connection = connection
                with self.assertRaises(http.HttpRejected) as caught:
                    client.request('/internal/projects/1/tasks/2/escalations', 'SYNTHETIC_NOT_REAL', {'expected_version': 1})
                self.assertEqual(caught.exception.status, status)
                self.assertEqual(caught.exception.envelope, value)
                self.assertEqual(len(connection.requests), 1)
                paths = list(output.glob('*.private.json'))
                self.assertEqual(len(paths), 1)
                record = json.loads(paths[0].read_bytes())
                self.assertEqual(record['response'], value)
                self.assertEqual(record['response_sha256'], hashlib.sha256(response.raw).hexdigest())
                self.assertEqual(record['status'], status)
                self.assertEqual(record['failure_type'], 'HttpRejected')
                self.assertEqual(record['request_id'], caught.exception.request_id)
                self.assertEqual(paths[0].stat().st_mode & 0o777, 0o600)

    def test_original_source_free_executor_import_is_still_an_open_P1(self):
        # Isolated stdlib + producer path models absent t44, not a Docker/platform validation.
        command = [sys.executable, '-I', '-B', '-c', 'import sys;sys.path.insert(0,sys.argv[1]);import prepare_http', str(CODE)]
        result = subprocess.run(command, capture_output=True, check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(b"No module named 't44'", result.stderr)
        self.assertIn(b'escalation_readback.py', result.stderr)


if __name__ == '__main__':
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Boundary))
    receipt = {'source_files_sha256': {name: hashlib.sha256((CODE / name).read_bytes()).hexdigest() for name in ['http_primitives.py', 'prepare_http.py', 'escalation_readback.py']}, 'tests': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors), 'actual_HTTP_cloud_Docker_sessions': False, 'source_free_original_executor_P1_reproduced': True, 'real_validator_scenarios_rerun': False}
    Path(__file__).with_name('755_http_boundary.json').write_text(json.dumps(receipt, indent=2) + '\n')
    raise SystemExit(not result.wasSuccessful())
