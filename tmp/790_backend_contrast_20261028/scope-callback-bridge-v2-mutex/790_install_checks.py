"""Offline installer checks; no Docker, service, network, or private inputs."""

import ast
import hashlib
import json
import subprocess
from pathlib import Path

import pytest

FOLDER = Path(__file__).resolve().parent
DESTINATION = "/root/t44-r9/scope-bridge-v2-01"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def constants():
    tree = ast.parse((FOLDER / "bridge_protocol.py").read_text())
    return {
        statement.targets[0].id: ast.literal_eval(statement.value)
        for statement in tree.body
        if isinstance(statement, ast.Assign)
        and isinstance(statement.targets[0], ast.Name)
        and statement.targets[0].id in {"FREEZE", "EXECUTION"}
    }


def delivery():
    return json.loads((FOLDER / "delivery.PUBLIC.json").read_text())


def install(index, target, restrictive_umask=False):
    item = delivery()["parts"][index]
    raw = (FOLDER / item["file"]).read_bytes()
    assert sha(raw) == item["sha256"]
    assert raw.decode().count(repr(DESTINATION)) == 1
    # Only the destination is redirected to this test's fresh directory; payload stays byte exact.
    command = raw.decode().replace(repr(DESTINATION), repr(str(target)))
    return subprocess.run(
        ["sh"],
        input=("umask 077\n" if restrictive_umask else "") + command,
        text=True,
        capture_output=True,
        check=False,
    )


def test_manifest_identifiers_come_from_exact_protocol_constants():
    manifest = json.loads((FOLDER / "manifest.PUBLIC.json").read_text())
    assert manifest["tool_freeze_sha256"] == constants()["FREEZE"]
    assert manifest["tool_execution_build_sha256"] == constants()["EXECUTION"]


def test_all_installer_commands_with_description_fit_UI_ceiling():
    for item in delivery()["parts"]:
        assert item["bytes"] == len((FOLDER / item["file"]).read_bytes())
        assert item["bytes"] + item["description_allowance"] < 18000


def test_complete_install_preserves_all_nine_source_bytes_and_modes(tmp_path):
    target = tmp_path / "new-bundle"
    for index in range(len(delivery()["parts"])):
        result = install(index, target)
        assert result.returncode == 0, result.stderr
        assert json.loads(result.stdout)["all_nine_verified"] is (index == 3)
    assert sha((target / "manifest.PUBLIC.json").read_bytes()) == delivery()["manifest_sha256"]
    manifest = json.loads((target / "manifest.PUBLIC.json").read_text())
    assert len(manifest["files"]) == 9
    for name in manifest["files"]:
        assert (target / name).read_bytes() == (FOLDER / name).read_bytes()
        assert (target / name).stat().st_mode & 0o777 == 0o444


@pytest.mark.parametrize("index", [0, 1, 2, 3])
def test_duplicate_install_part_never_overwrites(tmp_path, index):
    target = tmp_path / "once"
    for current in range(index + 1):
        assert install(current, target).returncode == 0
    before = {path.name: sha(path.read_bytes()) for path in target.iterdir()}
    assert install(index, target).returncode != 0
    assert {path.name: sha(path.read_bytes()) for path in target.iterdir()} == before


def test_mixed_bundle_marker_refused_before_second_part(tmp_path):
    target = tmp_path / "mixed"
    assert install(0, target).returncode == 0
    marker = target / "install-bundle.PUBLIC.json"
    marker.chmod(0o600)
    marker.write_text(json.dumps({"bundle_sha256": "0" * 64}))
    assert install(1, target).returncode != 0
    assert not (target / "bridge_load.py").exists()


def test_new_directory_must_not_be_symlink(tmp_path):
    actual = tmp_path / "actual"
    actual.mkdir()
    target = tmp_path / "linked"
    target.symlink_to(actual, target_is_directory=True)
    assert install(0, target).returncode != 0
    assert list(actual.iterdir()) == []


def test_installer_handles_private_umask_without_hiding_UID10001_code(tmp_path):
    target = tmp_path / "private-umask"
    for index in range(len(delivery()["parts"])):
        result = install(index, target, restrictive_umask=True)
        assert result.returncode == 0, result.stderr
    assert target.stat().st_mode & 0o777 == 0o755
    for name in json.loads((target / "manifest.PUBLIC.json").read_text())["files"]:
        assert (target / name).stat().st_mode & 0o777 == 0o444
