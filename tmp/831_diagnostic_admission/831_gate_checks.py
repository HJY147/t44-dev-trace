"""Admission boundaries only; fake repository, no application imports or database."""

import hashlib
import importlib.util
import json
import subprocess
from pathlib import Path
from unittest.mock import Mock

import pytest


@pytest.fixture
def admission(tmp_path, monkeypatch):
    source = Path(__file__).with_name("831_admission.py")
    spec = importlib.util.spec_from_file_location("admission_boundary_test", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    root = tmp_path / "repository"
    root.mkdir()
    module.__file__ = str(root / "tmp/831_diagnostic_admission/831_admission.py")
    tools = {
        "tmp/834_backend_performance/834_request_profile.py": b"# synthetic API tool\n",
        "tmp/833_database_performance/833_database_trace.py": b"# synthetic database tool\n",
    }
    for name, data in tools.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    request = {
        "request_id": "unit-boundary-only",
        "authorized": True,
        "mode": "mysql",
        "samples": 12,
        "database": "t44_diagnostics",
        "application_ref": "b" * 40,
        "tools": {name: hashlib.sha256(data).hexdigest() for name, data in tools.items()},
    }
    path = root / "records/diagnostics/20261025/request-before.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(request))
    monkeypatch.setenv("CI", "true")
    monkeypatch.setenv("GITHUB_SHA", "a" * 40)
    monkeypatch.setenv("T44_DATABASE", "t44_diagnostics")
    monkeypatch.setenv("DATABASE_URL", "mysql+pymysql://unused@127.0.0.1/t44_diagnostics")

    def git_output(command, **kwargs):
        if command == ["git", "rev-parse", "HEAD"]:
            return "a" * 40
        assert command[:2] == ["git", "show"]
        return tools[command[2].removeprefix("HEAD:")]

    git = Mock(side_effect=git_output)
    diff = Mock()
    monkeypatch.setattr(module.subprocess, "check_output", git)
    monkeypatch.setattr(module.subprocess, "run", diff)
    return module, root, request, path, git, diff


def test_explicit_local_plan_and_exclusive_receipt(admission):
    module, root, _, _, _, _ = admission
    module.main()
    receipt = root / "reports/diagnostics/admission-before.json"
    assert json.loads(receipt.read_text())["formal_acceptance"] is False
    assert receipt.stat().st_mode & 0o777 == 0o600
    with pytest.raises(FileExistsError):
        module.main()


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("CI", "false"),
        ("DATABASE_URL", "mysql+pymysql://unused@external.invalid/t44_diagnostics"),
        ("DATABASE_URL", "mysql+pymysql://unused@127.0.0.1/unrelated_database"),
        ("T44_DATABASE", "unrelated_database"),
    ],
)
def test_wrong_environment_rejected_before_git_or_application(admission, monkeypatch, name, value):
    module, root, _, _, git, diff = admission
    monkeypatch.setenv(name, value)
    with pytest.raises(ValueError):
        module.main()
    git.assert_not_called()
    diff.assert_not_called()
    assert not (root / "reports").exists()


def test_unapproved_request_rejected(admission):
    module, root, request, path, git, _ = admission
    request["authorized"] = False
    path.write_text(json.dumps(request))
    with pytest.raises(ValueError):
        module.main()
    git.assert_not_called()
    assert not (root / "reports").exists()


def test_tool_hash_change_rejected(admission):
    module, root, _, _, _, _ = admission
    (root / "tmp/833_database_performance/833_database_trace.py").write_text("# changed\n")
    with pytest.raises(ValueError):
        module.main()
    assert not (root / "reports").exists()


def test_application_drift_rejected(admission):
    module, root, _, _, _, diff = admission
    diff.side_effect = subprocess.CalledProcessError(1, ["git", "diff"])
    with pytest.raises(subprocess.CalledProcessError):
        module.main()
    assert not (root / "reports").exists()


def test_checkout_source_mismatch_rejected(admission, monkeypatch):
    module, root, _, _, _, diff = admission
    monkeypatch.setenv("GITHUB_SHA", "c" * 40)
    with pytest.raises(ValueError):
        module.main()
    diff.assert_not_called()
    assert not (root / "reports").exists()
