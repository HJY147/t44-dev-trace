"""Five-file transport guards with synthetic source payload; no product import or Docker."""

import argparse
import gzip
import hashlib
import importlib.util
import io
import json
import stat
import tarfile
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def module(name):
    spec = importlib.util.spec_from_file_location(
        name.replace("-", "_"), ROOT / "deployment/cloud-reuse" / name
    )
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def h(raw):
    return hashlib.sha256(raw).hexdigest()


def fixture_files():
    m = module("backend-upgrade-v2.py")
    contents = {
        "backend/t44/__init__.py": b"# synthetic source fixture only\n",
        "backend/requirements.lock": (ROOT / "backend/requirements.lock").read_bytes(),
        "backend/pyproject.toml": (ROOT / "backend/pyproject.toml").read_bytes(),
    }
    out = io.BytesIO()
    with tarfile.open(fileobj=out, mode="w") as t:
        for name, raw in contents.items():
            info = tarfile.TarInfo(name)
            info.size = len(raw)
            info.mode = 0o644
            t.addfile(info, io.BytesIO(raw))
    raw = out.getvalue()
    gz = gzip.compress(raw, mtime=0)
    frozen = (
        ROOT / "agents/deployment/cloud-reuse-20261025/upgrade-frozen-equality.json"
    ).read_bytes()
    f = json.loads(frozen)
    manifest = {
        "kind": "exact-source935-to-f4-offline-backend-upgrade",
        "base_source_sha": m.BASE,
        "source_sha": m.TARGET,
        "source_paths": list(m.SOURCE_PATHS),
        "source_archive_sha256": h(raw),
        "compressed_source_archive_sha256": h(gz),
        "source_archive_bytes": len(raw),
        "files": m.archive_files(raw)[0],
        "dependency_lock_sha256": m.LOCK_SHA,
        "frozen_equality_sha256": h(frozen),
        "frozen_file_set_sha256": f["file_set_sha256"],
        "dockerfile_sha256": h(m.dockerfile()),
        "preparer_sha256": h(
            (ROOT / "deployment/cloud-reuse/backend-upgrade-v2.py").read_bytes()
        ),
    }
    return {
        "source-backend.tar.gz": gz,
        "source-manifest.json": json.dumps(manifest).encode(),
        "frozen-equality.json": frozen,
        "Dockerfile": m.dockerfile(),
        "backend-upgrade.py": (
            ROOT / "deployment/cloud-reuse/backend-upgrade-v2.py"
        ).read_bytes(),
    }


def zip_file(tmp_path, files, extra=None):
    p = tmp_path / "source.zip"
    with zipfile.ZipFile(p, "w") as z:
        for name, raw in files.items():
            z.writestr(name, raw)
        if extra is not None:
            z.writestr(*extra)
    p.chmod(0o600)
    return p


def args(tmp_path, p, files):
    tmp_path.chmod(0o700)
    return argparse.Namespace(
        zip=p,
        zip_sha256=h(p.read_bytes()),
        manifest_sha256=h(files["source-manifest.json"]),
        output=tmp_path / "received",
    )


def test_valid_five_file_artifact_full_crc_safe_tar_and_no_pycache(tmp_path):
    files = fixture_files()
    p = zip_file(tmp_path, files)
    a = args(tmp_path, p, files)
    result = module("source-artifact-receive.py").receive(a)
    assert result["success"] and not result["Docker_or_business_started"]
    assert {p.name for p in a.output.iterdir()} == set(files)
    assert all(stat.S_IMODE(p.stat().st_mode) == 0o600 for p in a.output.iterdir())
    assert (a.output / "backend-upgrade.py").read_bytes() == files["backend-upgrade.py"]


@pytest.mark.parametrize(
    "change", ["extra", "traversal", "symlink", "builder", "duplicate"]
)
def test_unapproved_archive_objects_rejected_before_creating_output(tmp_path, change):
    files = fixture_files()
    extra = None
    if change == "extra":
        files["private.json"] = b"no"
    elif change == "traversal":
        files["../Dockerfile"] = files.pop("Dockerfile")
    elif change == "builder":
        files["backend-upgrade.py"] = b'raise RuntimeError("must never execute")'
    elif change == "duplicate":
        extra = ("Dockerfile", files["Dockerfile"])
    p = zip_file(tmp_path, files, extra)
    if change == "symlink":
        with zipfile.ZipFile(p) as z:
            rows = [(i, z.read(i)) for i in z.infolist()]
        with zipfile.ZipFile(p, "w") as z:
            for info, raw in rows:
                if info.filename == "Dockerfile":
                    info.external_attr = (stat.S_IFLNK | 0o777) << 16
                z.writestr(info, raw)
    a = args(tmp_path, p, files)
    with pytest.raises(ValueError):
        module("source-artifact-receive.py").receive(a)
    assert not a.output.exists()


def test_wrong_official_whole_sha_refused_before_zip_parsing(tmp_path):
    p = tmp_path / "bad.zip"
    p.write_bytes(b"notzip")
    p.chmod(0o600)
    with pytest.raises(ValueError, match="WHOLE_ZIP_SHA"):
        module("source-artifact-receive.py").inspect_zip(p, "0" * 64, "1" * 64)


def test_zip_crc_mismatch_rejected_even_if_whole_hash_is_supplied(tmp_path):
    files = fixture_files()
    p = zip_file(tmp_path, files)
    raw = p.read_bytes()
    assert b"exact-source935" in raw
    p.write_bytes(raw.replace(b"exact-source935", b"Exact-source935", 1))
    a = args(tmp_path, p, files)
    with pytest.raises((ValueError, zipfile.BadZipFile)):
        module("source-artifact-receive.py").receive(a)
    assert not a.output.exists()


def test_existing_output_is_never_reused_or_overwritten(tmp_path):
    files = fixture_files()
    p = zip_file(tmp_path, files)
    a = args(tmp_path, p, files)
    a.output.mkdir()
    sentinel = a.output / "original"
    sentinel.write_bytes(b"preserve")
    with pytest.raises(FileExistsError):
        module("source-artifact-receive.py").receive(a)
    assert sentinel.read_bytes() == b"preserve"


def test_nested_tar_traversal_never_extracted_and_failed_input_preserved(tmp_path):
    files = fixture_files()
    b = io.BytesIO()
    with tarfile.open(fileobj=b, mode="w") as t:
        i = tarfile.TarInfo("backend/t44/../../../escape")
        i.size = 1
        t.addfile(i, io.BytesIO(b"x"))
    raw = b.getvalue()
    files["source-backend.tar.gz"] = gzip.compress(raw, mtime=0)
    m = json.loads(files["source-manifest.json"])
    m.update(
        source_archive_sha256=h(raw),
        compressed_source_archive_sha256=h(files["source-backend.tar.gz"]),
        source_archive_bytes=len(raw),
    )
    files["source-manifest.json"] = json.dumps(m).encode()
    p = zip_file(tmp_path, files)
    a = args(tmp_path, p, files)
    with pytest.raises(ValueError, match="SAFE_CANONICAL"):
        module("source-artifact-receive.py").receive(a)
    assert a.output.exists() and not (tmp_path / "escape").exists()
