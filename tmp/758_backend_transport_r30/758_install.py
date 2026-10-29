"""Public code installation only; fixed /root prefix replaced by local synthetic tmp."""
import hashlib
import importlib.util
import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / 'agents/backend/neutral-transport-r30'
spec = importlib.util.spec_from_file_location('public_install', TOOLS / 'build-install.PUBLIC.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


def test_install_exact_bytes_and_refuse_existing(tmp_path):
    command, proof = builder.build()
    assert command == (TOOLS / 'install.PUBLIC.sh').read_bytes()
    assert proof == json.loads((TOOLS / 'install-proof.PUBLIC.json').read_bytes())
    prefix = str(tmp_path / 'synthetic-root/t44-r30')
    local = command.decode().replace('/root/t44-r30', prefix)
    result = subprocess.run(['sh', '-c', local], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    destination = Path(prefix) / 'neutral-transport-01'
    assert sorted(p.name for p in destination.iterdir()) == sorted(builder.ORDER)
    for name in builder.ORDER:
        path = destination / name
        assert path.read_bytes() == (TOOLS / name).read_bytes()
        assert path.stat().st_mode & 0o777 == 0o444
    snapshot = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in destination.iterdir()}
    second = subprocess.run(['sh', '-c', local], capture_output=True, text=True)
    assert second.returncode != 0
    assert 'File exists' in second.stderr
    assert snapshot == {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in destination.iterdir()}


def test_no_secret_archive_and_whole_command_cap():
    command, proof = builder.build()
    assert proof['complete_command_base64_plus_256'] < 18000
    assert set(proof['files']) == set(json.loads((TOOLS / 'code-manifest.PUBLIC.json').read_bytes())['files']) | {'code-manifest.PUBLIC.json'}
    assert hashlib.sha256(command).hexdigest() == proof['installer_sha256']
