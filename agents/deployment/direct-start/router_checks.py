"""Actual frozen FastAPI application and actual Starlette route-order regression."""
import hashlib
import importlib.util
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / 'backend'))
spec = importlib.util.spec_from_file_location('readiness', HERE / 'readiness.py')
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)
from fastapi import FastAPI
from fastapi.testclient import TestClient
from t44.api import create_app


class RouterChecks(unittest.TestCase):
    def test_exact_bcec_application_options_does_not_enter_runtime(self):
        # Pin to bcec's actual API bytes; test our adapter against the real route order.
        self.assertEqual(hashlib.sha256((ROOT/'backend/t44/api.py').read_bytes()).hexdigest(),
                         '974ede3d838b1cd865dd1af863a2a7a44ba12c2c26973d5397d16ddf86ba73b4')
        app = create_app()
        methods = [next(iter(route.methods)) for route in app.routes
                   if route.path == '/api/v1/projects']
        self.assertEqual(methods, ['POST', 'GET'])
        with patch.object(app.state.runtime, 'execute', side_effect=AssertionError('NO_RUNTIME_CALL')):
            result = TestClient(app).options('/api/v1/projects')
        self.assertEqual((result.status_code, result.headers['allow']), (405, 'POST'))
        r.validate_router_response(result.status_code, result.headers.get('allow'), result.content)

    def test_actual_fastapi_both_registration_orders(self):
        for order in [('POST', 'GET'), ('GET', 'POST')]:
            with self.subTest(order=order):
                app = FastAPI()
                async def endpoint():
                    raise AssertionError('OPTIONS_MUST_NOT_EXECUTE_ENDPOINT')
                for method in order:
                    app.add_api_route('/api/v1/projects', endpoint, methods=[method])
                result = TestClient(app).options('/api/v1/projects')
                self.assertEqual(result.status_code, 405)
                self.assertEqual(result.headers['allow'], order[0])
                r.validate_router_response(result.status_code, result.headers.get('allow'), result.content)

    def test_reject_false_router_signals(self):
        body = b'{"detail":"Method Not Allowed"}'
        for status, allow, raw in [(404,'GET',body),(503,'POST',body),(405,None,body),
                                  (405,'DELETE',body),(405,'POST',b'fake'),
                                  (405,'GET',b'{}'),(405,'POST',b'{"detail":"Method Not Allowed","fake":true}')]:
            with self.subTest(status=status, allow=allow, raw=raw), self.assertRaises(RuntimeError):
                r.validate_router_response(status, allow, raw)


if __name__ == '__main__':
    unittest.main()
