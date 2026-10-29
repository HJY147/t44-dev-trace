"""Future synthetic scheduler races; real HTTP error parser, no service or credentials."""
import hashlib
import importlib
import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
CODE = ROOT / 'agents/backend/neutral-r30-cas'
sys.path.insert(0, str(CODE))
http = importlib.import_module('http_primitives')
prepare = importlib.import_module('prepare_http')
spec = importlib.util.spec_from_file_location('synthetic_regression', Path(__file__).with_name('756_regression.py'))
regression = importlib.util.module_from_spec(spec)
spec.loader.exec_module(regression)


def envelope(code='VERSION_CONFLICT'):
    return {'code': code, 'message': 'Version conflict', 'request_id': 'synthetic-request',
            'audit_id': 7, 'current_state': 1, 'current_version': 2,
            'original_error_code': None, 'violations': []}


class Response:
    def __init__(self, status, result):
        self.status, self.raw = status, json.dumps(result).encode()

    def read(self, cap):
        return self.raw[:cap]


class Connection:
    def __init__(self, response):
        self.response = response

    def request(self, *args, **kwargs):
        pass

    def getresponse(self):
        return self.response

    def close(self):
        pass


def reject_request(tmp_path, status=409, result=None, path='/internal/projects/16/tasks/2312/escalations'):
    client = http.Client('https://10.0.0.1', tmp_path / 'unused-ca', tmp_path, float('inf'))
    client.connection = Connection(Response(status, envelope() if result is None else result))
    return client.request(path, 'synthetic-only', {'expected_version': 1})


def test_actual_error_parser_preserves_status_top_level_envelope_and_evidence(tmp_path):
    with pytest.raises(ValueError) as caught:
        reject_request(tmp_path)
    assert getattr(caught.value, 'status', None) == 409
    assert caught.value.envelope == envelope()
    records = list(tmp_path.glob('*.private.json'))
    assert len(records) == 1
    record = json.loads(records[0].read_text())
    assert record['status'] == 409 and record['response']['code'] == 'VERSION_CONFLICT'
    assert record['response_sha256'] == hashlib.sha256(json.dumps(envelope()).encode()).hexdigest()
    assert records[0].stat().st_mode & 0o777 == 0o600


def test_full_400_flow_adopts_sixty_readback_events_without_post_retry(tmp_path, monkeypatch):
    original_prepare = prepare.prepare
    races = []

    def run(*args, client_type, **kwargs):
        class SchedulerClient(client_type):
            def request(self, path, token=None, body=None, method=None):
                if path.startswith('/internal/projects/') and int(path.split('/')[3]) in range(16, 22) and int(path.split('/')[5]) not in races:
                    # The synthetic scheduler wins the CAS before this request. Its original
                    # persisted event remains in the fake store and must be read back intact.
                    raced = dict(body, scan_run_id='44444444-4444-4444-8444-444444444444')
                    super().request(path, token, raced, method)
                    races.append(int(path.split('/')[5]))
                    reject_request(args[4] / 'requests', path=path)
                return super().request(path, token, body, method)
        return original_prepare(*args, client_type=SchedulerClient, **kwargs)

    monkeypatch.setattr(prepare, 'prepare', run)
    regression.test_complete_40_project_400_api_preparation_fake_only(tmp_path, monkeypatch)
    assert len(races) == 60
    snapshots = json.loads((tmp_path / 'out/factual-snapshots.json').read_text())
    recovered = [row for row in snapshots['inventory']['clients'] if row['escalation_task']['id'] in races]
    assert len(recovered) == len(races)
    assert all(row['escalation_event']['scan_run_id'] == '44444444-4444-4444-8444-444444444444' for row in recovered)
    assert len(list((tmp_path / 'out/session-prefix').glob('*.json'))) == 3
