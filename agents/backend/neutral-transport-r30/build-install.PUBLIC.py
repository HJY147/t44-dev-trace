"""Build a pinned public-code-only installer; never connects or handles session data."""

import base64
import gzip
import hashlib
import io
import json
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ORDER = (
    '790_transfer.original.py', 'five_files.py', 'policy_790.py', 'opaque_tls.py',
    'provenance.PUBLIC.json', 'relay.template.PUBLIC.json', 'code-manifest.PUBLIC.json',
)
DESTINATION = '/root/t44-r30/neutral-transport-01'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def build():
    manifest_raw = (ROOT / 'code-manifest.PUBLIC.json').read_bytes()
    manifest = json.loads(manifest_raw)
    assert set(ORDER) == set(manifest['files']) | {'code-manifest.PUBLIC.json'}
    archive = io.BytesIO()
    with tarfile.open(fileobj=archive, mode='w', format=tarfile.USTAR_FORMAT) as tar:
        for name in ORDER:
            path = ROOT / name
            assert not path.is_symlink()
            data = path.read_bytes()
            if name != 'code-manifest.PUBLIC.json':
                assert sha(data) == manifest['files'][name]
                assert len(data) == manifest['file_sizes'][name]
            info = tarfile.TarInfo(name)
            info.size, info.mode, info.mtime = len(data), 0o444, 0
            tar.addfile(info, io.BytesIO(data))
    compressed = gzip.compress(archive.getvalue(), compresslevel=9, mtime=0)
    payload = base64.b64encode(compressed).decode('ascii')
    script = (
        'set -eu\numask 022\nd=' + DESTINATION
        + '\nmkdir -p /root/t44-r30\nmkdir "$d"\nprintf %s \' '
    )
    script = script[:-1] + payload + '\'|base64 -d|gzip -dc|tar -xf - -C "$d"\n'
    raw = script.encode('ascii')
    outer_bytes = len(base64.b64encode(raw))
    assert outer_bytes + 256 < 18000
    return raw, {
        'kind': 'PUBLIC-code-only-r30-embedded-install-v1',
        'destination': DESTINATION,
        'installer_sha256': sha(raw),
        'command_bytes': len(raw),
        'complete_command_base64_bytes': outer_bytes,
        'complete_command_base64_plus_256': outer_bytes + 256,
        'limit_exclusive': 18000,
        'gzip_bytes': len(compressed),
        'gzip_sha256': sha(compressed),
        'tar_sha256': sha(archive.getvalue()),
        'manifest_sha256': sha(manifest_raw),
        'files': list(ORDER),
        'credentials_or_sessions_in_installer': False,
        'existing_destination_policy': 'mkdir fails; no extraction or retry',
        'archive_is_generated_from_only_pinned_regular_PUBLIC_files': True,
    }


if __name__ == '__main__':
    command, proof = build()
    (ROOT / 'install.PUBLIC.sh').write_bytes(command)
    (ROOT / 'install-proof.PUBLIC.json').write_text(json.dumps(proof, indent=2) + '\n')
    print(json.dumps(proof, sort_keys=True))
