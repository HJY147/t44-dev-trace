"""Offline transport trust guards; never Docker, cloud, live data or independent results."""

import gzip
import importlib.util
import io
import json
import subprocess
import tarfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def module():
    spec = importlib.util.spec_from_file_location(
        "cloud_bundle", ROOT / "deployment/cloud-reuse/image-bundle.py"
    )
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def fixture(tmp_path, m):
    source = "9" * 40
    images = {}
    for role, pin in m.PINS.items():
        images[role] = {
            "alias": "t44-official-" + role + ":" + pin.split("sha256:")[1],
            "official_upstream_pin": pin,
            "image_id": "sha256:" + "1" * 64,
            "os": "linux",
            "architecture": "amd64",
            "revision_label": None,
            "archive_label": None,
        }
    for role in ["backend", "web"]:
        images[role] = {
            "alias": "t44-" + role + ":src-" + source,
            "official_upstream_pin": None,
            "image_id": "sha256:" + "2" * 64,
            "os": "linux",
            "architecture": "amd64",
            "revision_label": source,
            "archive_label": m.digest(b"synthetic offline transport"),
        }
    files = {}
    for name in ["images.tar.gz", "source-runtime-context.tar.gz"]:
        p = tmp_path / name
        p.write_bytes(gzip.compress(b"synthetic offline transport"))
        files[name] = {"sha256": m.file_digest(p), "bytes": p.stat().st_size}
    manifest = {
        "schema": 1,
        "source_sha": source,
        "source_archive_sha256": m.digest(b"synthetic offline transport"),
        "uncompressed_image_archive_sha256": m.digest(b"synthetic offline transport"),
        "dependency_lock_sha256": m.EXPECTED_LOCK,
        "platform": "linux/amd64",
        "files": files,
        "images": images,
    }
    return manifest


def manifest_hash(tmp_path, m, v):
    p = tmp_path / "bundle-manifest.json"
    p.write_text(json.dumps(v))
    return m.file_digest(p)


def test_valid_transport_verified_without_docker(tmp_path, monkeypatch):
    m = module()
    v = fixture(tmp_path, m)
    monkeypatch.setattr(
        m, "command", lambda *a, **k: pytest.fail("pure verification called Docker")
    )
    assert m.verify(tmp_path, manifest_hash(tmp_path, m, v))["source_sha"] == "9" * 40


def test_corrupt_archive_rejected_before_docker(tmp_path, monkeypatch):
    m = module()
    v = fixture(tmp_path, m)
    expected = manifest_hash(tmp_path, m, v)
    (tmp_path / "images.tar.gz").write_bytes(b"damaged")
    monkeypatch.setattr(
        m, "command", lambda *a, **k: pytest.fail("corrupt artifact called Docker")
    )
    with pytest.raises(ValueError, match="ARCHIVE_BYTES_OR_HASH"):
        m.verify(tmp_path, expected)


@pytest.mark.parametrize(
    "field,value", [("revision_label", "8" * 40), ("alias", "untrusted/mirror:latest")]
)
def test_wrong_source_or_image_identity_rejected(tmp_path, field, value):
    m = module()
    v = fixture(tmp_path, m)
    v["images"]["backend"][field] = value
    with pytest.raises(ValueError):
        m.verify(tmp_path, manifest_hash(tmp_path, m, v))


@pytest.mark.parametrize(
    "name,kind",
    [
        ("../escape", "regular"),
        ("backend/t44/link", "symlink"),
        ("backend/.env", "regular"),
    ],
)
def test_unsafe_archive_rejected_before_any_write(tmp_path, name, kind):
    m = module()
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w") as archive:
        entry = tarfile.TarInfo(name)
        if kind == "symlink":
            entry.type = tarfile.SYMTYPE
            entry.linkname = "/etc/passwd"
            archive.addfile(entry)
        else:
            entry.size = 1
            archive.addfile(entry, io.BytesIO(b"x"))
    output = tmp_path / "context"
    with pytest.raises(ValueError, match="UNEXPECTED_OR_PRIVATE"):
        m.extract_context(buffer.getvalue(), output)
    assert not output.exists()


def test_exact_source_archive_extract_has_public_nonroot_read_modes(tmp_path):
    m = module()
    raw = subprocess.run(
        ["git", "archive", "935ab5b93bea788672c2b4a088c79cfeed848954", *m.SUBSET],
        cwd=ROOT,
        capture_output=True,
        check=True,
    ).stdout
    output = tmp_path / "context"
    m.extract_context(raw, output)
    assert (output / "backend/t44/__init__.py").stat().st_mode & 0o777 == 0o644
    assert (output / "backend/t44").stat().st_mode & 0o777 == 0o755
    assert not (output / "backend/tests").exists()
    assert not (output / ".env").exists()
