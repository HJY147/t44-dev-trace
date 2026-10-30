"""Offline exact-file and digest verification; never connects to a host."""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import subprocess
import tarfile


MEASUREMENT = dict(clients=400, warmup_seconds=60, steady_seconds=600,
                   p95_max_ms=270, throughput_min_per_minute=1000, business_errors=0)


def verify(root):
    root = Path(root)
    manifest = json.loads((root / 'READY_MANIFEST.PUBLIC.json').read_text())
    if manifest['measurement'] != MEASUREMENT or manifest['actual_execute_grant'] is not False:
        raise ValueError('MEASUREMENT_OR_AUTHORIZATION_CHANGED')
    if (manifest.get('qa_run'), manifest.get('material_run'), manifest.get('maintenance_run')) != ('r30manualp13', 'r30materialresume06', 'r30restoretransition06'):
        raise ValueError('EXACT_P13_RUN_BINDING_REQUIRED')
    actual = set()
    for p in root.rglob('*'):
        if p.is_symlink():
            raise ValueError('SYMLINK_NOT_ALLOWED')
        if p.is_file():
            actual.add(p.relative_to(root).as_posix())
    if actual != set(manifest['files']) | {'READY_MANIFEST.PUBLIC.json'}:
        raise ValueError('EXACT_FILE_SET_REQUIRED')
    for name, expected in manifest['files'].items():
        relative = Path(name)
        if relative.is_absolute() or '..' in relative.parts:
            raise ValueError('UNSAFE_MANIFEST_PATH')
        p = root / relative
        raw = p.read_bytes()
        if len(raw) != expected['bytes'] or hashlib.sha256(raw).hexdigest() != expected['sha256']:
            raise ValueError('FILE_DIGEST_MISMATCH:' + name)
        if p.suffix == '.py':
            ast.parse(raw, filename=name, feature_version=(3, 10))
        elif p.suffix == '.sh':
            subprocess.run(['bash', '-n', str(p)], check=True, capture_output=True)
    return dict(status='OFFLINE_BUNDLE_VERIFIED_LIVE_PREPARATION_PENDING',
                files=len(manifest['files']), cloud_requests=0, benchmark_started=False)


def verify_archive(archive, root):
    """Compare archive payload directly without extracting or running tools."""
    expected = {p.relative_to(root).as_posix(): p.read_bytes()
                for p in root.rglob('*') if p.is_file()}
    with tarfile.open(archive, 'r:gz') as stream:
        members = stream.getmembers()
        if len(members) != len(expected) or {m.name for m in members} != set(expected):
            raise ValueError('ARCHIVE_FILE_SET_MISMATCH')
        for member in members:
            if not member.isfile() or stream.extractfile(member).read() != expected[member.name]:
                raise ValueError('ARCHIVE_BYTES_MISMATCH')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    parser.add_argument('--archive', type=Path)
    args = parser.parse_args()
    result = verify(args.directory)
    if args.archive:
        verify_archive(args.archive, args.directory)
        result['archive_bytes_verified'] = True
    print(json.dumps(result, sort_keys=True))
