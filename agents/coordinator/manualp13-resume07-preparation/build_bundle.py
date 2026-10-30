"""Assemble hash-bound public p13 inputs; never launch a host or benchmark."""
import argparse
import hashlib
import json
from pathlib import Path
import tarfile
from verify_bundle import MEASUREMENT, verify, verify_archive


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def collect(root, manifest, prefix, payload):
    root = root.resolve()
    for name, item in manifest['files'].items():
        rel = Path(name)
        if rel.is_absolute() or '..' in rel.parts:
            raise ValueError('UNSAFE_SOURCE_PATH')
        path = root / rel
        if path.is_symlink() or path.resolve().parent != (root / rel.parent).resolve():
            raise ValueError('SOURCE_SYMLINK')
        if root not in path.resolve().parents:
            raise ValueError('SOURCE_OUTSIDE_ROOT')
        raw = path.read_bytes()
        expected = item['sha256'] if isinstance(item, dict) else item
        if digest(raw) != expected:
            raise ValueError('SOURCE_CHANGED:' + name)
        target = (Path(prefix) / rel).as_posix()
        if target in payload:
            raise ValueError('DUPLICATE_TARGET:' + target)
        payload[target] = raw


def build(args):
    here = Path(__file__).resolve().parent
    payload, provenance = {}, {}
    for label, root, name, prefix in [
            ('continuation', args.continuation, 'MANIFEST.PUBLIC.json', ''),
            ('qa', args.qa, 'HASH_MANIFEST.PUBLIC.json', 'qa')]:
        raw = (root / name).read_bytes()
        value = json.loads(raw)
        if label == 'qa' and (
                (value.get('qa_run'), value.get('material_id'), value.get('maintenance_id')) !=
                ('r30manualp13', 'r30materialresume07', 'r30restoretransition07')
                or any(value.get(k) is not False for k in
                       ['current_identity_issued', 'prepare_executed', 'grant_issued', 'execute_executed'])):
            raise ValueError('UNAPPROVED_P13_QA07_REQUIRED')
        if label == 'continuation' and (
                value.get('product_source') != '90b734f65ce6ee9f5c217e885bc7ea4857e32b48'
                or value.get('executed') is not False
                or value.get('contains_accounts_tokens_or_keys') is not False):
            raise ValueError('PUBLIC_UNEXECUTED_SOURCE90B_REQUIRED')
        if label == 'continuation' and (
                value.get('qa_run'), value.get('material_run'), value.get('maintenance_run')) != (
                    'r30manualp13', 'r30materialresume07', 'r30restoretransition07'):
            raise ValueError('P13_CONTINUATION_REQUIRED')
        collect(root, value, prefix, payload)
        provenance[label + '_manifest_sha256'] = digest(raw)
        payload[(Path(prefix) / name).as_posix()] = raw
        if label == 'qa':
            payload['qa/SHA256SUMS.PUBLIC.txt'] = (root / 'SHA256SUMS.PUBLIC.txt').read_bytes()
    ssh_raw = (args.ssh_source / 'READY_MANIFEST.PUBLIC.json').read_bytes()
    ssh_manifest = json.loads(ssh_raw)
    collect(args.ssh_source,
            {'files': {n: v for n, v in ssh_manifest['files'].items()
                       if n.startswith('ssh/') and n.endswith(('.py', '.sh'))}},
            '', payload)
    provenance['ssh_source_manifest_sha256'] = digest(ssh_raw)
    for path in sorted((here / 'coordinator').glob('*.py')):
        payload['coordinator/' + path.name] = path.read_bytes()
    for name in ['verify_bundle.py', 'READY_AFTER_BOOT.md']:
        payload[name] = (here / name).read_bytes()
    payload['ssh/README.md'] = (here / 'SSH_README.md').read_bytes()
    manifest = dict(schema='t44-offline-ready-bundle-v1',
                    source='90b734f65ce6ee9f5c217e885bc7ea4857e32b48',
                    qa_run='r30manualp13', material_run='r30materialresume07',
                    maintenance_run='r30restoretransition07', measurement=MEASUREMENT,
                    actual_execute_grant=False, cloud_actions_performed=False,
                    status='OFFLINE_PREPARATION_ONLY_LIVE_GATES_PENDING',
                    distribution='RESTRICTED_RUNTIME_CONTAINS_INTERNAL_TOPOLOGY_NO_SECRETS',
                    automatic_vm_shutdown=False,
                    provenance=provenance,
                    files={n: dict(bytes=len(b), sha256=digest(b))
                           for n, b in sorted(payload.items())})
    output = args.output.absolute()
    archive = Path(str(output) + '.tar.gz')
    if output.exists() or archive.exists():
        raise ValueError('NEW_OUTPUT_REQUIRED')
    output.mkdir(mode=0o700)
    for name, raw in payload.items():
        path = output / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('xb') as stream:
            stream.write(raw)
        path.chmod(0o600)
    (output / 'READY_MANIFEST.PUBLIC.json').write_text(json.dumps(manifest, indent=2) + '\n')
    result = verify(output)
    with tarfile.open(archive, 'x:gz') as stream:
        for path in sorted(output.rglob('*')):
            if path.is_file():
                stream.add(path, arcname=path.relative_to(output).as_posix(), recursive=False)
    verify_archive(archive, output)
    archive.chmod(0o600)
    return dict(**result, archive=str(archive), archive_sha256=digest(archive.read_bytes()))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ['continuation', 'qa', 'ssh-source', 'output']:
        parser.add_argument('--' + name, type=Path, required=True)
    print(json.dumps(build(parser.parse_args()), sort_keys=True))
