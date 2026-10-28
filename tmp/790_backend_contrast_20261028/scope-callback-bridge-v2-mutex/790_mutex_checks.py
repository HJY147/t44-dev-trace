"""Offline shared phase mutex integration, using own real local flock descriptors."""

import fcntl
import json
import os
import sys
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from bridge_backend import DockerBackend
from bridge_common import Deadline, Refused, canonical, sha

UTC = timezone.utc  # noqa: UP017 -- host3.10-compatible data.


class Clock:
    def now(self):
        return datetime(2031, 1, 1, 12, tzinfo=UTC)

    def mono(self):
        return 1000


def blocked(path):
    fd = os.open(path, os.O_RDWR | os.O_CREAT, 0o600)
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return True
        fcntl.flock(fd, fcntl.LOCK_UN)
        return False
    finally:
        os.close(fd)


@pytest.fixture
def backend(tmp_path, monkeypatch):
    phase = tmp_path / "f"
    phase.mkdir()
    clock = Clock()
    value = DockerBackend(phase, tmp_path, "a" * 64, clock)
    value.deadline = Deadline(clock, clock.now() + timedelta(seconds=55))
    value.binding = {
        "database": "t44_owned_fake_f",
        "project": "t44-owned-f",
        "source_sha": "e" * 40,
        "images": {"backend": {"alias": "owned-synthetic-backend"}},
        "image_ids": {"backend": "sha256:" + "1" * 64},
        "config_ids": {"backend": "sha256:" + "1" * 64},
        "file_hashes": {},
    }
    value.authority = {"documents": {"binding": {"sha256": "b" * 64}}}
    value.source_files = {}
    value.output = lambda _argv: ("sha256:" + "1" * 64 + "\n").encode()
    monkeypatch.setattr(os, "chown", lambda *_args: None)
    return value


@pytest.mark.parametrize("mode", ["preflight", "seal"])
def test_each_SQL_container_holds_shared_phase_lock(backend, tmp_path, mode):
    events = []
    lock = backend.phase / ".v4-operation.lock"

    @contextmanager
    def operation(_deadline):
        fd = os.open(lock, os.O_RDWR | os.O_CREAT, 0o600)
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        events.append("enter")
        try:
            yield
        finally:
            os.close(fd)
            events.append("exit")

    backend.phase_operation_lock = operation

    class Runner:
        def run(self, _argv, _deadline, prefix):
            assert blocked(lock), "direct SQL started without shared phase mutex"
            events.append("SQL")
            (prefix.parent / (mode + "-output/result.PUBLIC.json")).write_bytes(b"{}")

    backend.runner = Runner()
    result = backend._data(
        mode, {"request": {}}, {"bridge_id": "fake-owned-bridge"}, tmp_path,
        backend.deadline, "c" * 64 if mode == "seal" else None,
    )
    assert result == b"{}"
    assert events == ["enter", "SQL", "exit"]
    assert not blocked(lock)


def test_SQL_failure_releases_shared_lock(backend, tmp_path):
    lock = backend.phase / ".v4-operation.lock"

    @contextmanager
    def operation(_deadline):
        fd = os.open(lock, os.O_RDWR | os.O_CREAT, 0o600)
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            yield
        finally:
            os.close(fd)

    backend.phase_operation_lock = operation

    class Runner:
        def run(self, *_args):
            assert blocked(lock)
            raise Refused("OWNED_SYNTHETIC_SQL_FAILURE")

    backend.runner = Runner()
    with pytest.raises(Refused, match="OWNED_SYNTHETIC_SQL_FAILURE"):
        backend._data("preflight", {"request": {}}, {"bridge_id": "owned"}, tmp_path, backend.deadline)
    assert not blocked(lock)


def test_GEN_can_acquire_shared_phase_lock_and_is_not_wrapped_by_parent(backend, tmp_path):
    lock = backend.phase / ".v4-operation.lock"
    called = []

    class Runner:
        def run(self, argv, _deadline, _prefix):
            assert not blocked(lock), "GEN must take its own mutex without parent nesting"
            called.append(argv)
            return canonical({"success": True, "action": "scheduler-token", "source_sha": "e" * 40})

    backend.runner = Runner()
    result = backend.generation("scheduler-token", {"request": {"project_ids": [7]}}, tmp_path, backend.deadline)
    assert result["success"] is True
    assert len(called) == 1 and called[0][-2:] == ["--project-id", "7"]


def install_fake_dependency(backend, body):
    path = backend.phase / "mysql-budget.py"
    path.write_text(body)
    backend.binding["file_hashes"]["mysql-budget.py"] = sha(path.read_bytes())
    return path


def test_binding_pinned_dependency_is_loaded_with_clamped_remaining_budget(backend):
    install_fake_dependency(backend, '''from contextlib import contextmanager
@contextmanager
def operation_lock(phase_dir,binding_sha256,timeout_seconds=10):
    assert phase_dir.name=='f'
    assert binding_sha256=='b'*64
    assert timeout_seconds==7
    yield
''')
    deadline = Deadline(backend.clock, backend.clock.now() + timedelta(seconds=7))
    with backend.phase_operation_lock(deadline):
        pass


def test_changed_dependency_refused_before_import_side_effect(backend):
    path = install_fake_dependency(backend, "raise AssertionError('IMPORT_MUST_NOT_HAPPEN')\n")
    backend.binding["file_hashes"]["mysql-budget.py"] = "0" * 64
    with pytest.raises(Refused, match="SHA256_MISMATCH"):
        with backend.phase_operation_lock(backend.deadline):
            pass
    assert path.exists()


def test_lock_timeout_happens_before_SQL_dispatch_and_has_no_retry(backend, tmp_path):
    calls = []
    install_fake_dependency(backend, '''from contextlib import contextmanager
@contextmanager
def operation_lock(phase_dir,binding_sha256,timeout_seconds=10):
    raise ValueError('PHASE_OPERATION_MUTEX_TIMEOUT')
    yield
''')

    class Runner:
        def run(self, *_args):
            calls.append("SQL")

    backend.runner = Runner()
    with pytest.raises(ValueError, match="PHASE_OPERATION_MUTEX_TIMEOUT"):
        backend._data("preflight", {"request": {}}, {"bridge_id": "owned"}, tmp_path, backend.deadline)
    assert calls == []
