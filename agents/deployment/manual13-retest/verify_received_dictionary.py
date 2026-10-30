"""Parse owner-published native dictionary CLI bytes; no database or network calls."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
def verify(receipt):
    source = ROOT / 'deployment/cloud-reuse/manual13-observe.py'
    spec = importlib.util.spec_from_file_location('received_observer', source)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    raw = receipt.read_bytes(); v = json.loads(raw)
    assert v['observer_sha256'] == '52c3e7850e01d6c117c65c6efd00fe79f47825644fd0e1ed9f18116b4d392535'
    assert v['status'] == 'ALL_STATIC_DICTIONARY_QUERIES_EXECUTED'
    q = v['queries']; results = {}
    for name, parser in [('status', m.mysql), ('config', m.mysql_config), ('waits', m.mysql_waits)]:
        assert q[name]['returncode'] == 0
        stdout = q[name]['stdout']; assert len(stdout.encode()) == q[name]['stdout_bytes']
        with patch.object(m, 'command', return_value=stdout) as spy:
            results[name] = parser('a' * 64)
            assert spy.call_count == 1
    assert results['status']['checkpoint_age']['bytes'] == 53239
    assert results['config']['available'] is True
    assert results['waits'].get('coverage') is not None
    return {'status':'NATIVE_PUBLIC_CLI_BYTES_PARSED', 'receipt_sha256':hashlib.sha256(raw).hexdigest(),
            'original_observer_sha256':v['observer_sha256'], 'observer_sha256':hashlib.sha256(source.read_bytes()).hexdigest(), 'results':results,
            'cloud_or_database_calls':0,'linux_counter_validation':False,
            'scope':'native MySQL dictionary CLI parse only, not live permissions or IO validation'}
if __name__ == '__main__':
    p=argparse.ArgumentParser();p.add_argument('receipt', type=Path);a=p.parse_args()
    print(json.dumps(verify(a.receipt), sort_keys=True, indent=2))
