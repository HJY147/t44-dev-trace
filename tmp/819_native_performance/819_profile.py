"""Pure explicit-profile checks; never execute generated main or connect services."""

import ast
import importlib.util
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("native_profile_guard", ROOT / "deployment/native/profile-prepare.py")
PROFILE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PROFILE)


@pytest.fixture(scope="module")
def originals():
    return {
        name: subprocess.run(
            ["git", "show", PROFILE.BASE + ":deployment/native/" + name], cwd=ROOT, check=True, capture_output=True
        ).stdout
        for name in PROFILE.PINS
    }


@pytest.mark.parametrize("profile", ["functional", "performance"])
def test_only_exact_profile_changes_preserve_source_and_deadline(originals, profile):
    files, manifest = PROFILE.render(profile, originals)
    assert {n: PROFILE.digest(v) for n, v in originals.items()} == PROFILE.PINS
    expected = PROFILE.PROFILES[profile]
    for name, data in files.items():
        ast.parse(data)
        restored = data.decode()
        for change in reversed(manifest["files"][name]["allowed_changes"]):
            restored = restored.replace(change["new"], change["old"])
        assert restored.encode() == originals[name]
        assert PROFILE.digest(originals[name]) == manifest["files"][name]["old_sha256"]
    constants = {}
    for node in ast.parse(files["isolated-application.py"]).body:
        if (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id == "DATABASE"
        ):
            constants["database"] = ast.literal_eval(node.value)
    assert constants["database"] == expected["database"]
    assert PROFILE.SOURCE.encode() in files["isolated.py"]
    assert b"8, 47, tzinfo=UTC" in files["isolated.py"]
    assert b"module.STOP - 30" in files["isolated-application.py"]
    assert manifest["old_files_changed"] is False and manifest["generated_files_executed"] is False
    if profile == "performance":
        assert b"!= 8" in files["isolated-application.py"]
        assert b"18097" in files["isolated.py"] and b"45716" in files["isolated.py"]


def test_unknown_profile_refused(originals):
    with pytest.raises(ValueError):
        PROFILE.render("arbitrary", originals)


def test_changed_template_refused(originals):
    changed = dict(originals)
    changed["isolated.py"] += b"\n# changed"
    with pytest.raises(ValueError, match="HASH"):
        PROFILE.render("performance", changed)
