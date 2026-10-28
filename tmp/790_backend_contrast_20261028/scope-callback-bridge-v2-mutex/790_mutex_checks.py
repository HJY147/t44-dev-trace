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
        mode,
        {"request": {}},
        {"bridge_id": "fake-owned-bridge"},
        tmp_path,
        backend.deadline,
        "c" * 64 if mode == "seal" else None,
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
        backend._data(
            "preflight", {"request": {}}, {"bridge_id": "owned"}, tmp_path, backend.deadline
        )
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
    result = backend.generation(
        "scheduler-token", {"request": {"project_ids": [7]}}, tmp_path, backend.deadline
    )
    assert result["success"] is True
    assert len(called) == 1 and called[0][-2:] == ["--project-id", "7"]


def install_fake_dependency(backend, body):
    path = backend.phase / "mysql-budget.py"
    path.write_text(body)
    backend.binding["file_hashes"]["mysql-budget.py"] = sha(path.read_bytes())
    return path


def test_binding_pinned_dependency_is_loaded_with_clamped_remaining_budget(backend):
    install_fake_dependency(
        backend,
        """from contextlib import contextmanager
@contextmanager
def operation_lock(phase_dir,binding_sha256,timeout_seconds=10):
    assert phase_dir.name=='f'
    assert binding_sha256=='b'*64
    assert timeout_seconds==7
    yield
""",
    )
    deadline = Deadline(backend.clock, backend.clock.now() + timedelta(seconds=7))
    with backend.phase_operation_lock(deadline):
        pass


def test_changed_dependency_refused_before_import_side_effect(backend):
    path = install_fake_dependency(backend, "raise AssertionError('IMPORT_MUST_NOT_HAPPEN')\n")
    backend.binding["file_hashes"]["mysql-budget.py"] = "0" * 64
    with (
        pytest.raises(Refused, match="EXACT_INPUT_SHA_REQUIRED"),
        backend.phase_operation_lock(backend.deadline),
    ):
        pass
    assert path.exists()


def test_manifest_rejects_wrong_phase_dependency_before_controller_or_SQL(backend):
    binding_raw = canonical({"file_hashes": {"mysql-budget.py": "1" * 64}})
    (backend.phase / "binding.json").write_bytes(binding_raw)
    manifest_raw = canonical(
        {"files": {}, "phase_dependencies": {"mysql-budget.py": {"sha256": "2" * 64}}}
    )
    (backend.bridge_dir / "manifest.PUBLIC.json").write_bytes(manifest_raw)
    backend.bundle_sha = sha(manifest_raw)
    authority = {
        "app_phase_dir": str(backend.phase),
        "documents": {"binding": {"sha256": sha(binding_raw)}},
    }
    with pytest.raises(Refused, match="APP_PHASE_MUTEX_DEPENDENCY_VERSION"):
        backend.check_binding({"binding": json.loads(binding_raw)}, authority)
    assert not (backend.phase / "controller.py").exists()


def test_lock_timeout_happens_before_SQL_dispatch_and_has_no_retry(backend, tmp_path):
    calls = []
    install_fake_dependency(
        backend,
        """from contextlib import contextmanager
@contextmanager
def operation_lock(phase_dir,binding_sha256,timeout_seconds=10):
    raise ValueError('PHASE_OPERATION_MUTEX_TIMEOUT')
    yield
""",
    )

    class Runner:
        def run(self, *_args):
            calls.append("SQL")

    backend.runner = Runner()
    with pytest.raises(ValueError, match="PHASE_OPERATION_MUTEX_TIMEOUT"):
        backend._data(
            "preflight", {"request": {}}, {"bridge_id": "owned"}, tmp_path, backend.deadline
        )
    assert calls == []


def actual_deployment_dependency(backend):
    raw = (Path(__file__).parent / "phase-dependency.PUBLIC.py").read_bytes()
    assert sha(raw) == "305f9eaeea96b0ef882ec17a457f51852bafc8c34b5fe2e47056bd12625dd82d"
    (backend.phase / "mysql-budget.py").write_bytes(raw)
    backend.binding["file_hashes"]["mysql-budget.py"] = sha(raw)
    # Only the mutex's documented public binding fields, own synthetic phase, no DB/config.
    binding = canonical({"generation_kind": "exact-pinned-production-entry-generation-v4"})
    (backend.phase / "binding.json").write_bytes(binding)
    (backend.phase / "binding.json").chmod(0o600)
    backend.phase.chmod(0o700)
    backend.authority["documents"]["binding"]["sha256"] = sha(binding)


def test_actual_deployment_helper_mutual_exclusion_and_release(backend):
    actual_deployment_dependency(backend)
    path = backend.phase / ".v4-operation.lock"
    with backend.phase_operation_lock(backend.deadline):
        assert blocked(path)
        assert path.stat().st_mode & 0o777 == 0o600
        assert path.stat().st_uid == os.geteuid()
    assert not blocked(path)


def test_actual_deployment_helper_foreign_lock_bounded_timeout(backend):
    actual_deployment_dependency(backend)
    path = backend.phase / ".v4-operation.lock"
    fd = os.open(path, os.O_CREAT | os.O_RDWR, 0o600)
    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    try:
        deadline = Deadline(backend.clock, backend.clock.now() + timedelta(seconds=0.02))
        with (
            pytest.raises(ValueError, match="PHASE_OPERATION_MUTEX_TIMEOUT"),
            backend.phase_operation_lock(deadline),
        ):
            raise AssertionError("foreign mutex must prevent body entry")
    finally:
        os.close(fd)
    assert not blocked(path)


def test_data_control_mount_remains_readable_with_actual_CLI_umask077(backend, tmp_path):
    @contextmanager
    def operation(_deadline):
        yield

    backend.phase_operation_lock = operation

    class Runner:
        def run(self, _argv, _deadline, prefix):
            inputs = prefix.parent / "preflight-inputs"
            assert inputs.stat().st_mode & 0o777 == 0o755, "UID10001 must traverse input mount"
            assert (inputs / "control.PUBLIC.json").stat().st_mode & 0o777 == 0o444
            (prefix.parent / "preflight-output/result.PUBLIC.json").write_bytes(b"{}")

    backend.runner = Runner()
    previous = os.umask(0o077)
    try:
        assert backend._data(
            "preflight", {"request": {}}, {"bridge_id": "owned"}, tmp_path, backend.deadline
        ) == b"{}"
    finally:
        os.umask(previous)
