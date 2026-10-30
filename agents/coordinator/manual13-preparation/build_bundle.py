"""Assemble only public offline tools into a new directory and archive."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import tarfile
from verify_bundle import MEASUREMENT, verify, verify_archive


def copy_verified(source, expected, target):
    raw = source.read_bytes()
    if source.is_symlink() or hashlib.sha256(raw).hexdigest() != expected:
        raise ValueError('SOURCE_CHANGED:' + str(source))
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open('xb') as stream:
        stream.write(raw)


def build(args):
    output = args.output.resolve()
    archive = output.with_suffix('.tar.gz')
    if output.exists() or archive.exists():
        raise ValueError('NEW_OUTPUT_REQUIRED')
    continuation = json.loads((args.continuation / 'MANIFEST.PUBLIC.json').read_text())
    legacy = json.loads((args.legacy / 'launch-manifest.PUBLIC.json').read_text())
    ssh = json.loads((args.ssh / 'MANIFEST.PUBLIC.json').read_text())
    output.mkdir(mode=0o700)
    for name, item in continuation['files'].items():
        relative = Path(name)
        if relative.is_absolute() or '..' in relative.parts:
            raise ValueError('UNSAFE_SOURCE_PATH')
        target = 'CONTINUATION_RUNBOOK.md' if name == 'RUNBOOK.md' else name
        copy_verified(args.continuation / relative, item['sha256'], output / target)
    # These public QA tools and original entry wrappers remain byte-identical.
    names = [name for name in legacy['files'] if name.startswith('qa/')]
    names += ['coordinator/dispatch_once.py', 'coordinator/observe_ready.py']
    for name in names:
        copy_verified(args.legacy / name, legacy['files'][name], output / name)
    for name, item in ssh['files'].items():
        relative = Path(name)
        if relative.is_absolute() or '..' in relative.parts:
            raise ValueError('UNSAFE_SSH_SOURCE_PATH')
        expected = item['sha256'] if isinstance(item, dict) else item
        copy_verified(args.ssh / name, expected, output / 'ssh' / name)
    here = Path(__file__).resolve().parent
    for name in ['READY_AFTER_BOOT.md', 'verify_bundle.py', 'REVIEW.md', 'VALIDATION.PUBLIC.json']:
        shutil.copyfile(here / name, output / name)
    files = {p.relative_to(output).as_posix():
             dict(bytes=p.stat().st_size, sha256=hashlib.sha256(p.read_bytes()).hexdigest())
             for p in sorted(output.rglob('*')) if p.is_file()}
    manifest = dict(schema='t44-offline-ready-bundle-v1', source=legacy['source'],
                    qa_run='r30manualp12', material_run='r30materialresume05',
                    maintenance_run='r30restoretransition05', measurement=MEASUREMENT,
                    actual_execute_grant=False, cloud_actions_performed=False,
                    status='OFFLINE_PREPARATION_ONLY_LIVE_GATES_PENDING', files=files,
                    provenance=dict(continuation_manifest_sha256=hashlib.sha256(
                        (args.continuation / 'MANIFEST.PUBLIC.json').read_bytes()).hexdigest(),
                        ssh_manifest_sha256=hashlib.sha256(
                        (args.ssh / 'MANIFEST.PUBLIC.json').read_bytes()).hexdigest()))
    (output / 'READY_MANIFEST.PUBLIC.json').write_text(json.dumps(manifest, indent=2) + '\n')
    result = verify(output)
    with tarfile.open(archive, 'x:gz') as stream:
        for p in sorted(output.rglob('*')):
            if p.is_file():
                stream.add(p, arcname=p.relative_to(output).as_posix(), recursive=False)
    verify_archive(archive, output)
    return dict(**result, archive=str(archive),
                archive_sha256=hashlib.sha256(archive.read_bytes()).hexdigest())


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ['continuation', 'legacy', 'ssh', 'output']:
        parser.add_argument('--' + name, required=True, type=Path)
    print(json.dumps(build(parser.parse_args()), sort_keys=True))
