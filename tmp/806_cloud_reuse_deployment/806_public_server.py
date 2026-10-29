"""Offline public-file scope checks only; no Linux PID or network execution."""

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def module():
    spec = importlib.util.spec_from_file_location(
        "public_server", ROOT / "deployment/cloud-reuse/public-bundle-server.py"
    )
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def manifest(tmp_path):
    data = b"public immutable image bytes"
    (tmp_path / "payload.part0000").write_bytes(data)
    v = {
        "schema": 1,
        "parts": [
            {
                "name": "payload.part0000",
                "bytes": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
            }
        ],
    }
    p = tmp_path / "parts-manifest.json"
    p.write_text(json.dumps(v))
    return hashlib.sha256(p.read_bytes()).hexdigest()


def test_only_declared_public_objects_allowed(tmp_path):
    m = module()
    sha = manifest(tmp_path)
    assert set(m.public_files(tmp_path, "parts", sha)) == {
        "parts-manifest.json",
        "payload.part0000",
    }


def test_extra_private_file_rejects_entire_directory(tmp_path):
    m = module()
    sha = manifest(tmp_path)
    (tmp_path / "application.env").write_text("synthetic private marker")
    with pytest.raises(ValueError, match="NO_EXTRA_FILES"):
        m.public_files(tmp_path, "parts", sha)


def test_symlink_object_rejected(tmp_path):
    m = module()
    sha = manifest(tmp_path)
    (tmp_path / "payload.part0000").unlink()
    (tmp_path / "payload.part0000").symlink_to(tmp_path / "parts-manifest.json")
    with pytest.raises(ValueError, match="SINGLE_LINK"):
        m.public_files(tmp_path, "parts", sha)


@pytest.mark.parametrize("address", ["0.0.0.0", "127.0.0.1", "8.8.8.8"])
def test_nonprivate_or_loopback_bind_rejected(address):
    with pytest.raises(ValueError, match="RFC1918"):
        module().private_ip(address)
