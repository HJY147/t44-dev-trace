"""Purely local release/contract check. Never imports Docker, SSH or cloud tools."""
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent

def check():
    contract = json.loads((HERE/'RUN.PUBLIC.json').read_bytes())
    assert contract['run_id'] == 'r30posttools17'
    assert contract['remote_root'] == '/root/t44-direct-p17'
    assert contract['qa_workspace'] == '/root/t44-final-20261101/QA753_POSTTOOLS_V12_P17'
    assert contract['exclusive_output'] == contract['remote_root']+'/app-init'
    assert contract['private_inputs'] == contract['exclusive_output']+'/bootstrap/current-inputs.private.json'
    for name, expected in contract['release_files'].items():
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest() == expected, name
    spec = importlib.util.spec_from_file_location('p17_start', ROOT/'agents/deployment/direct-start/start.py')
    start = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(start)
    assert start.SOURCE == contract['source']
    assert start.IDS == contract['existing_container_ids']
    for name, expected in start.PINS.items():
        assert hashlib.sha256((ROOT/'agents/backend/fast-bootstrap'/name).read_bytes()).hexdigest() == expected
    return {'status':'LOCAL_P17_RELEASE_CHECK_PASS','remote_calls':0,
            'remote_output_absence_verified':False,'run_consumed':False}

if __name__ == '__main__':
    print(json.dumps(check(), sort_keys=True))
