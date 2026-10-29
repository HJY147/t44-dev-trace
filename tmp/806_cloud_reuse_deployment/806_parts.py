"""Offline split/join trust, corruption and non-overwrite guards; no cloud or secrets."""

import hashlib
import importlib.util
import io
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def module():
    spec = importlib.util.spec_from_file_location(
        "file_parts", ROOT / "deployment/cloud-reuse/file-parts.py"
    )
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    m.PART_SIZE = 64
    return m


def test_split_join_exact_bytes_and_no_overwrite(tmp_path):
    m = module()
    source = tmp_path / "archive.zip"
    source.write_bytes(bytes(range(200)))
    sha = m.digest(source)
    result = m.split(source, sha, tmp_path / "parts")
    assert result["parts"] == 4
    joined = tmp_path / "joined.zip"
    assert (
        m.join(tmp_path / "parts", result["manifest_sha256"], joined)["sha256"] == sha
    )
    assert joined.read_bytes() == source.read_bytes()
    with pytest.raises(FileExistsError):
        m.join(tmp_path / "parts", result["manifest_sha256"], joined)
    assert joined.read_bytes() == source.read_bytes()


def test_corrupt_part_rejected_before_output_creation(tmp_path):
    m = module()
    source = tmp_path / "data"
    source.write_bytes(b"a" * 200)
    result = m.split(source, m.digest(source), tmp_path / "parts")
    (tmp_path / "parts/payload.part0001").write_bytes(b"x" * 64)
    with pytest.raises(ValueError, match="PART_BYTES_OR_HASH"):
        m.join(tmp_path / "parts", result["manifest_sha256"], tmp_path / "output")
    assert not (tmp_path / "output").exists()


def test_unknown_zip_path_rejected_before_extraction(tmp_path):
    m = module()
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("../escape", "x")
    source = tmp_path / "bad.zip"
    source.write_bytes(buffer.getvalue())
    with pytest.raises(ValueError, match="EXACT_THREE"):
        m.unpack(source, m.digest(source), tmp_path / "unpacked")
    assert not (tmp_path / "unpacked").exists()


def test_exact_three_verified_artifact_objects_unpacked(tmp_path):
    m = module()
    source = tmp_path / "good.zip"
    with zipfile.ZipFile(source, "w") as archive:
        for name in m.OBJECTS:
            archive.writestr(name, b"synthetic")
    result = m.unpack(source, m.digest(source), tmp_path / "unpacked")
    assert result["bundle_manifest_sha256"] == hashlib.sha256(b"synthetic").hexdigest()
    assert {x.name for x in (tmp_path / "unpacked").iterdir()} == m.OBJECTS
