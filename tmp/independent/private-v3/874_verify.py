"""Offline-only freeze verification. This entry never creates a Harness or contacts a SUT."""
import ast
import base64
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def verify():
    manifest = json.loads((HERE / 'manifest.json').read_text())
    for name, expected in manifest['payload_files'].items():
        path = HERE / name
        assert path.is_file() and not path.is_symlink(), name + ': not a regular frozen file'
        assert digest(path) == expected, name + ': freeze hash mismatch'
    canonical = ''.join(name + '\0' + sha + '\n' for name, sha in sorted(manifest['payload_files'].items()))
    assert hashlib.sha256(canonical.encode()).hexdigest() == manifest['payload_set_sha256']
    packet = json.loads((HERE / 'neutral-inputs.json').read_text())
    inputs = {packet['freeze']['path']: packet['freeze']['sha256'], **packet['freeze']['files'],
              **packet['original_teacher_materials'], **packet['additional_neutral_policy'],
              **packet['approved_change_inputs']}
    for path, expected in inputs.items():
        assert digest(HERE / 'materials' / path) == expected, path + ': neutral source mismatch'
    r = packet['runtime_capability_document']
    assert digest(HERE / 'materials' / r['path']) == r['sha256']
    scripts = sorted(HERE.glob('*.py'))
    assert len(scripts) == 10
    assert {p.name.split('_')[0] for p in scripts} == {str(i) for i in range(874, 884)}
    for path in scripts:
        tree = ast.parse(path.read_text(), filename=str(path))
        compile(tree, str(path), 'exec')
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                assert all(not a.name.startswith(('t44', 'backend', 'frontend')) for a in node.names)
            if isinstance(node, ast.ImportFrom):
                assert not (node.module or '').startswith(('t44', 'backend', 'frontend'))
    contract = json.loads((HERE / 'materials/specs/contracts/openapi.json').read_text())
    assert contract['info']['version'] == '1.1.0'
    assert contract['components']['schemas']['Meta']['properties']['contract_version']['const'] == '1.1.0'
    assert len(contract['paths']) == 31 and len(contract['components']['schemas']) == 130
    assert sum(m in ('get', 'post', 'patch', 'put', 'delete') for pi in contract['paths'].values() for m in pi) == 38
    assert (HERE / 'materials/specs/contracts/openapi.json').read_bytes() == (HERE / 'materials/backend/t44/contracts/openapi.json').read_bytes()
    assert (HERE / 'materials/specs/database/schema.sql').read_bytes() == (HERE / 'materials/backend/t44/persistence/schema_v1.sql').read_bytes()
    cert = HERE / 'recipient.pem'
    subprocess.run(['openssl', 'x509', '-in', str(cert), '-noout', '-checkend', '3600'], check=True, capture_output=True)
    text = subprocess.check_output(['openssl', 'x509', '-in', str(cert), '-noout', '-text'], text=True)
    assert '3072 bit' in text or '3072-bit' in text
    assert [p.name for p in HERE.rglob('*.pem')] == ['recipient.pem']
    assert cert.read_text().startswith('-----BEGIN CERTIFICATE-----')
    return {'offline_verified': True, 'sut_accessed': False, 'payload_files': len(manifest['payload_files']),
            'payload_set_sha256': manifest['payload_set_sha256'], 'script_count': len(scripts)}

def decode_trace(path, output):
    """Lossless standalone metric/screenshot extraction for tester-only archived evidence."""
    source, target = Path(path), Path(output)
    target.mkdir(mode=0o700, parents=True, exist_ok=True)
    with (target / 'requests.csv').open('wb') as csv:
        header = False
        for number, line in enumerate(source.read_text().splitlines()):
            frame = json.loads(line)
            if frame.get('encoding') == 'gzip-base64-csv-v1':
                value = gzip.decompress(base64.b64decode(frame['payload']))
                assert hashlib.sha256(value).hexdigest() == frame['uncompressed_sha256']
                if not header:
                    csv.write((','.join(frame['columns']) + '\n').encode()); header = True
                csv.write(value)
            elif frame.get('kind') == 'real_browser_png':
                value = base64.b64decode(frame['payload']); assert len(value) == frame['bytes']
                (target / ('browser-' + str(number) + '.png')).write_bytes(value)

if __name__ == '__main__':
    if len(sys.argv) == 4 and sys.argv[1] == '--decode-private-trace':
        decode_trace(sys.argv[2], sys.argv[3])
    else:
        print(json.dumps(verify(), sort_keys=True))
