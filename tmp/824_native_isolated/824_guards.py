"""Deployment-only synthetic boundaries; no database, services or tester materials."""

import ast
import importlib.util
import os
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("native_isolated_guard", ROOT / "deployment/native/isolated.py")
NATIVE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(NATIVE)


def test_exact_broker_derivation_has_new_ports_and_unchanged_safety():
    raw = subprocess.run(
        ["git", "show", NATIVE.SOURCE + ":deployment/native/runtime.py"], cwd=ROOT, check=True, capture_output=True
    ).stdout
    data, changes = NATIVE.derive_broker(raw)
    ast.parse(data)
    assert len(changes) == 3
    assert NATIVE.sha(raw) == NATIVE.BROKER_SHA
    assert b'PORTS = {"amqp": 25696, "epmd": 24396, "distribution": 35696}' in data
    assert b"CLI_PORTS = (45696, 45705)" in data
    for marker in (b"def same_owner", b"-nocookie", b"COOKIE", b"--no-wait"):
        assert raw.count(marker) == data.count(marker)
    restored = data.decode()
    for change in reversed(changes):
        restored = restored.replace(change["new"], change["old"])
    assert restored.encode() == raw


def test_changed_template_refused():
    with pytest.raises(ValueError, match="TEMPLATE"):
        NATIVE.derive_broker(b"unrecognized")


@pytest.mark.parametrize("offset,allowed", [(-121, True), (-120, False), (0, False), (1, False)])
def test_deadline_admission(offset, allowed):
    if allowed:
        NATIVE.admitted(NATIVE.STOP + offset)
    else:
        with pytest.raises(ValueError, match="WINDOW"):
            NATIVE.admitted(NATIVE.STOP + offset)


def test_private_file_and_no_overwrite(tmp_path):
    path = tmp_path / "file"
    NATIVE.write(path, b"first")
    assert path.stat().st_mode & 0o777 == 0o600
    NATIVE.private(path)
    with pytest.raises(FileExistsError):
        NATIVE.write(path, b"second")
    assert path.read_bytes() == b"first"
    path.chmod(0o644)
    with pytest.raises(ValueError, match="PRIVATE"):
        NATIVE.private(path)


def test_stop_does_not_signal_unconfirmed_identity(monkeypatch):
    signals = []

    def reject(*_):
        raise ValueError("PROCESS_IDENTITY_CHANGED")

    monkeypatch.setattr(NATIVE, "owned", reject)
    monkeypatch.setattr(NATIVE.os, "killpg", lambda *args: signals.append(args))
    with pytest.raises(ValueError, match="IDENTITY"):
        NATIVE.stop_app(Path("/synthetic"), "api")
    assert signals == []


def test_absent_process_does_not_signal(monkeypatch):
    monkeypatch.setattr(NATIVE, "owned", lambda *_: (None, None))
    monkeypatch.setattr(NATIVE.os, "killpg", lambda *_: pytest.fail("unexpected signal"))
    assert NATIVE.stop_app(Path("/synthetic"), "consumer")["success"]


def test_does_not_override_global_home():
    value = NATIVE.environment()
    if "HOME" in os.environ:
        assert value["HOME"] == os.environ["HOME"]
    assert "AMQP_URL" not in value
    assert "DATABASE_URL" not in value
