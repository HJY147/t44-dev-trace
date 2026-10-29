"""Actual local public-code install and opaque import checks; no service operations."""

import ast
import base64
import hashlib
import importlib
import json
import subprocess
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
TARGET = "/root/t44-r9/p790-f7-1600-01"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def install(index, target):
    delivery = json.loads((HERE / "delivery.PUBLIC.json").read_text())
    row = delivery["parts"][index]
    raw = (HERE / row["file"]).read_bytes()
    assert sha(raw) == row["sha256"]
    assert raw.decode().count(repr(TARGET)) == 1
    command = raw.decode().replace(repr(TARGET), repr(str(target)))
    return subprocess.run(
        ["sh"], input="umask 077\n" + command, text=True, capture_output=True, check=False
    )


def test_complete_real_install_preserves_thirteen_modules_and_private_umask(tmp_path):
    target = tmp_path / "new"
    for i in range(4):
        result = install(i, target)
        assert result.returncode == 0, result.stderr
        assert json.loads(result.stdout)["all_thirteen_verified"] is (i == 3)
    manifest = json.loads((target / "manifest.json").read_text())
    assert len(manifest["files"]) == 13
    for name, row in manifest["files"].items():
        assert (target / name).read_bytes() == (HERE / name).read_bytes()
        assert sha((target / name).read_bytes()) == row["sha256"]
        assert (target / name).stat().st_mode & 0o777 == 0o444
        assert (target / name).parent.stat().st_mode & 0o777 == 0o755


@pytest.mark.parametrize("index", [0, 1, 2, 3])
def test_no_install_part_overwrites_existing_source(tmp_path, index):
    target = tmp_path / "once"
    for i in range(index + 1):
        assert install(i, target).returncode == 0
    before = {
        str(p.relative_to(target)): sha(p.read_bytes()) for p in target.rglob("*") if p.is_file()
    }
    assert install(index, target).returncode != 0
    assert {
        str(p.relative_to(target)): sha(p.read_bytes()) for p in target.rglob("*") if p.is_file()
    } == before


def test_mixed_manifest_marker_prevents_second_part(tmp_path):
    target = tmp_path / "mixed"
    assert install(0, target).returncode == 0
    marker = target / "install-bundle.PUBLIC.json"
    marker.chmod(0o600)
    marker.write_text(json.dumps({"bundle_sha256": "0" * 64}))
    assert install(1, target).returncode != 0
    assert not (target / "790_producer.py").exists()


def test_opaque_receive_roundtrip_and_duplicate_preservation(tmp_path):
    receiver = importlib.import_module("790_receive")
    config = {
        "work_dir": str(tmp_path / "work"),
        "source_sha": "f7cdb5fa3b19f84d8ab0d0b042bf51a5b8484e8f",
        "binding_sha256": "a" * 64,
        "root_grant_sha256": "b" * 64,
    }
    metadata = {
        "source_sha": config["source_sha"],
        "phase_binding_sha256": "a" * 64,
        "root_grant_sha256": "b" * 64,
        "part_count": 1,
    }
    receiver.receive(config, {"metadata": metadata}, "metadata")
    raw = b"OWNED_SYNTHETIC_OPAQUE_ONLY"
    part = {
        "index": 0,
        "parts": 1,
        "bytes": len(raw),
        "sha256": sha(raw),
        "data": base64.b64encode(raw).decode(),
    }
    receiver.receive(config, part, "part")
    assert (tmp_path / "work/part-0.OPAQUE").read_bytes() == raw
    with pytest.raises(FileExistsError):
        receiver.receive(config, part, "part")
    assert (tmp_path / "work/part-0.OPAQUE").read_bytes() == raw


def test_opaque_receive_wrong_grant_has_no_output(tmp_path):
    receiver = importlib.import_module("790_receive")
    config = {
        "work_dir": str(tmp_path / "work"),
        "source_sha": "f7cdb5fa3b19f84d8ab0d0b042bf51a5b8484e8f",
        "binding_sha256": "a" * 64,
        "root_grant_sha256": "b" * 64,
    }
    metadata = {
        "source_sha": config["source_sha"],
        "phase_binding_sha256": "a" * 64,
        "root_grant_sha256": "c" * 64,
        "part_count": 1,
    }
    with pytest.raises(ValueError):
        receiver.receive(config, {"metadata": metadata}, "metadata")
    assert not (tmp_path / "work").exists()


def test_command_lengths_and_host310_syntax():
    for item in json.loads((HERE / "delivery.PUBLIC.json").read_text())["parts"]:
        assert len((HERE / item["file"]).read_bytes()) + 300 < 18000
    for name in (
        "790_bootstrap.py",
        "790_host.py",
        "790_load.py",
        "790_budget.py",
        "790_producer.py",
        "790_consumer.py",
        "790_receive.py",
        "transport/790_transfer.py",
        "edge/790_authority.py",
    ):
        tree = ast.parse((HERE / name).read_text(), feature_version=(3, 10))
        assert not any(
            isinstance(n, ast.ImportFrom)
            and n.module == "datetime"
            and any(x.name == "UTC" for x in n.names)
            for n in ast.walk(tree)
        )
