"""Filesystem-only regression: main uses a zero-DB recipe, never the 19-query matrix."""

import builtins
import importlib.util
import json
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tmp/838_database_public_diagnostics/838_database_public_diagnostics.py"


@pytest.fixture
def subject(monkeypatch):
    spec = importlib.util.spec_from_file_location("output_guard_subject", TOOL)
    tool = importlib.util.module_from_spec(spec)
    seen = []
    original = builtins.__import__

    def track(name, *args, **kwargs):
        seen.append(name)
        return original(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", track)
    spec.loader.exec_module(tool)
    calls = []
    monkeypatch.setattr(tool, "recipes", lambda: calls.append("zero_db") or {"zero_db": True})
    yield tool, calls
    assert not any(
        name.startswith(("sqlalchemy", "t44", "pymysql", "sqlite3", "httpx", "fastapi"))
        for name in seen
    ), seen


def invoke(monkeypatch, tool, output):
    monkeypatch.setattr(sys, "argv", [str(TOOL), "--run", "--output", str(output)])
    return tool.main()


def test_result_appears_after_old_precheck(subject, tmp_path, monkeypatch, record_property):
    tool, calls = subject
    output = tmp_path / "race.json"
    marker = "prior-result-created-after-precheck"
    original = tool.provenance

    def inject(root):
        result = original(root)
        output.write_text(marker)
        return result

    monkeypatch.setattr(tool, "provenance", inject)
    code = 0
    try:
        invoke(monkeypatch, tool, output)
    except SystemExit as error:
        code = error.code
    record_property("main_exit", code)
    record_property("overwritten", output.read_text() != marker)
    assert output.read_text() == marker, "Output created after precheck must not be overwritten"
    assert code == 2 and calls == []


@pytest.mark.parametrize("kind", ["file", "directory", "valid_symlink", "dangling_symlink"])
def test_existing_objects_are_untouched(subject, tmp_path, monkeypatch, kind):
    tool, calls = subject
    output, target = tmp_path / "output.json", tmp_path / "target.json"
    if kind == "file":
        output.write_text("old")
    elif kind == "directory":
        output.mkdir()
    else:
        if kind == "valid_symlink":
            target.write_text("old-target")
        output.symlink_to(target)
    with pytest.raises(SystemExit) as error:
        invoke(monkeypatch, tool, output)
    assert error.value.code == 2 and calls == []
    if kind == "file":
        assert output.read_text() == "old"
    elif kind == "directory":
        assert output.is_dir() and list(output.iterdir()) == []
    elif kind == "valid_symlink":
        assert output.is_symlink() and target.read_text() == "old-target"
    else:
        assert output.is_symlink() and not target.exists()


def test_normal_new_result_is_private_and_descriptor_closed(subject, tmp_path, monkeypatch):
    tool, calls = subject
    output = tmp_path / "nested/result.json"
    opened = []
    original = tool.os.open

    def record(path, flags, mode):
        fd = original(path, flags, mode)
        opened.append((fd, flags, mode))
        return fd

    monkeypatch.setattr(tool.os, "open", record)
    invoke(monkeypatch, tool, output)
    data = json.loads(output.read_text())
    assert calls == ["zero_db"] and data["local_query_recipes"] == {"zero_db": True}
    assert data["status"].startswith("completed")
    assert output.stat().st_mode & 0o777 == 0o600
    assert len(opened) == 1
    fd, flags, mode = opened[0]
    assert flags & os.O_EXCL and flags & os.O_NOFOLLOW and flags & os.O_CREAT
    assert not flags & os.O_TRUNC and mode == 0o600
    with pytest.raises(OSError):
        os.fstat(fd)


def test_recipe_exception_is_recorded_then_propagated(subject, tmp_path, monkeypatch):
    tool, _ = subject
    output = tmp_path / "failure.json"

    def failure():
        raise ValueError("synthetic recipe failure")

    monkeypatch.setattr(tool, "recipes", failure)
    with pytest.raises(ValueError, match="synthetic recipe failure"):
        invoke(monkeypatch, tool, output)
    data = json.loads(output.read_text())
    assert data["status"].startswith("failed") and data["error_class"] == "ValueError"
    assert output.stat().st_mode & 0o777 == 0o600


def test_fixed_fd_does_not_reopen_replaced_leaf(subject, tmp_path, monkeypatch):
    tool, _ = subject
    output, reserved = tmp_path / "output.json", tmp_path / "reserved-inode.json"

    def replace_leaf():
        output.rename(reserved)
        output.write_text("replacement-marker")
        return {"zero_db": True}

    monkeypatch.setattr(tool, "recipes", replace_leaf)
    invoke(monkeypatch, tool, output)
    assert output.read_text() == "replacement-marker"
    assert json.loads(reserved.read_text())["status"].startswith("completed")


def test_fdopen_failure_closes_reserved_fd(subject, tmp_path, monkeypatch):
    tool, _ = subject
    output = tmp_path / "fdopen-error.json"
    opened = []
    original = tool.os.open

    def record(path, flags, mode):
        fd = original(path, flags, mode)
        opened.append(fd)
        return fd

    def fail(*args, **kwargs):
        raise RuntimeError("synthetic fdopen failure")

    monkeypatch.setattr(tool.os, "open", record)
    monkeypatch.setattr(tool.os, "fdopen", fail)
    with pytest.raises(RuntimeError, match="synthetic fdopen failure"):
        invoke(monkeypatch, tool, output)
    assert len(opened) == 1 and output.read_bytes() == b""
    with pytest.raises(OSError):
        os.fstat(opened[0])


def test_absent_nofollow_fails_closed(subject, tmp_path, monkeypatch):
    tool, calls = subject
    output = tmp_path / "no-follow.json"
    monkeypatch.delattr(tool.os, "O_NOFOLLOW")
    with pytest.raises(SystemExit) as error:
        invoke(monkeypatch, tool, output)
    assert error.value.code == 2 and not output.exists() and calls == []


def test_explicit_run_still_required(subject, tmp_path, monkeypatch):
    tool, calls = subject
    output = tmp_path / "implicit.json"
    monkeypatch.setattr(sys, "argv", [str(TOOL), "--output", str(output)])
    with pytest.raises(SystemExit) as error:
        tool.main()
    assert error.value.code == 2 and not output.exists() and calls == []
