"""Owned v3 budget regressions. All MySQL rows are synthetic; no SUT/network."""

import copy
import fcntl
import json
import os
import sys
import types
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from bridge_backend import DockerBackend
from bridge_common import Deadline, Refused, canonical, document, sha
from bridge_protocol import budget_receipt_binding

UTC = timezone.utc  # noqa: UP017 -- host Python3.10.


class Clock:
    def now(self):
        return datetime(2031, 1, 1, 12, tzinfo=UTC)

    def mono(self):
        return 1000


@pytest.fixture
def backend(tmp_path, monkeypatch):
    phase = tmp_path / "f"
    phase.mkdir(mode=0o700)
    receipt = phase / "receipts/mysql-budget-00000000000000000000000000000001.PUBLIC.json"
    receipt.parent.mkdir(mode=0o700)
    receipt.write_bytes(b"{}")
    receipt.chmod(0o600)
    clock = Clock()
    value = DockerBackend(phase, tmp_path, "a" * 64, clock)
    value.deadline = Deadline(clock, clock.now() + timedelta(seconds=55))
    value.binding = {
        "database": "owned_synthetic_f",
        "project": "owned-synthetic-f",
        "source_sha": "b" * 40,
        "images": {"backend": {"alias": "owned-synthetic-image"}},
        "image_ids": {"backend": "sha256:" + "1" * 64},
        "config_ids": {"backend": "sha256:" + "1" * 64},
    }
    value.authority = {
        "documents": {"binding": {"sha256": "c" * 64}, "mysql_budget": document(b"{}")},
        "budget_receipt_path": str(receipt),
    }
    value.source_files = {}
    value.output = lambda _argv: ("sha256:" + "1" * 64 + "\n").encode()
    monkeypatch.setattr(os, "chown", lambda *_args: None)
    return value


@pytest.mark.parametrize("action", ["scheduler-token", "scheduler-rotate", "scheduler-start"])
def test_every_GEN_scheduler_call_passes_exact_budget_receipt(backend, tmp_path, action):
    class Runner:
        def run(self, argv, _deadline, _prefix):
            assert "--budget-receipt" in argv, "v4 GEN requires an actual budget receipt"
            assert (
                argv[argv.index("--budget-receipt") + 1] == backend.authority["budget_receipt_path"]
            )
            assert "--budget-receipt-sha256" in argv
            assert (
                argv[argv.index("--budget-receipt-sha256") + 1]
                == backend.authority["documents"]["mysql_budget"]["sha256"]
            )
            return canonical({"success": True, "action": action, "source_sha": "b" * 40})

    backend.runner = Runner()
    backend.generation(action, {"request": {"project_ids": [2, 1]}}, tmp_path, backend.deadline)


@pytest.mark.parametrize("mode", ["preflight", "seal"])
def test_direct_SQL_admits_budget_inside_lock_before_dispatch(backend, tmp_path, mode):
    events = []

    def admit(*_args):
        assert events == ["LOCK"]
        events.append("ADMIT")
        return {"budget_receipt_sha256": backend.authority["documents"]["mysql_budget"]["sha256"]}

    budget = SimpleNamespace(admit=admit)

    @contextmanager
    def operation(_deadline):
        events.append("LOCK")
        try:
            yield budget
        finally:
            events.append("UNLOCK")

    backend.phase_operation_lock = operation
    backend.live_mysql = lambda _role: {}

    class Runner:
        def run(self, _argv, _deadline, prefix):
            assert events == ["LOCK", "ADMIT"], "direct SQL must follow budget.admit in same lock"
            events.append("SQL")
            (prefix.parent / (mode + "-output/result.PUBLIC.json")).write_bytes(b"{}")

    backend.runner = Runner()
    backend._data(mode, {"request": {}}, {"bridge_id": "owned"}, tmp_path, backend.deadline)
    assert events == ["LOCK", "ADMIT", "SQL", "UNLOCK"]


def lock_is_held(path):
    fd = os.open(path, os.O_RDWR | os.O_CREAT, 0o600)
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return True
        return False
    finally:
        os.close(fd)


def actual_budget_fixture(backend, monkeypatch):
    """Original305f admit/measure/SQL parser with owned synthetic metadata/query transport."""
    raw = (Path(__file__).parent / "phase-dependency.PUBLIC.py").read_bytes()
    assert sha(raw) == "305f9eaeea96b0ef882ec17a457f51852bafc8c34b5fe2e47056bd12625dd82d"
    vendor = types.ModuleType("own_budget_fixture")
    exec(compile(raw, "phase-dependency.PUBLIC.py", "exec"), vendor.__dict__)  # noqa: S102
    (backend.phase / "mysql-budget.py").write_bytes(raw)
    plan = vendor.pool_plan("f", 4, 5, 10)
    backend.binding.update(
        {
            "generation_kind": vendor.KIND,
            "phase": "f",
            "api_workers": 4,
            "stop_utc": "2031-01-01T12:30:00Z",
            "v4_pool_plan": plan,
            "file_hashes": {"mysql-budget.py": sha(raw)},
        }
    )
    for name in ("image_ids", "config_ids"):
        backend.binding[name]["mysql"] = "sha256:" + "2" * 64
    binding_raw = canonical(backend.binding)
    (backend.phase / "binding.json").write_bytes(binding_raw)
    (backend.phase / "binding.json").chmod(0o600)
    backend.authority["documents"]["binding"] = document(binding_raw)
    backend.authority["app_phase_dir"] = str(backend.phase)
    info = {
        "Id": "3" * 64,
        "Image": backend.binding["image_ids"]["mysql"],
        "RestartCount": 0,
        "Config": {
            "Labels": {
                "com.docker.compose.project": backend.binding["project"],
                "com.docker.compose.service": "mysql",
            }
        },
        "State": {"Running": True, "StartedAt": "2031-01-01T11:00:00Z", "Pid": 12345},
    }
    sample = {
        "max_connections": 128,
        "server_uuid": "00112233-4455-6677-8899-aabbccddeeff",
        "database": backend.binding["database"],
        "connection_id": 7,
        "Connections": 20,
        "Threads_connected": 6,
        "Max_used_connections": 12,
        "Uptime": 1000,
        "Threads_running": 1,
    }
    saved = {
        "kind": "actual-owned-mysql-budget-v4",
        "binding_sha256": sha(binding_raw),
        "source_sha": backend.binding["source_sha"],
        "stop_utc": backend.binding["stop_utc"],
        "mysql_identity": {
            "container_id": info["Id"],
            "image_id": info["Image"],
            "host_pid": 12345,
            "host_pid_start_ticks": "4567",
            "container_started_at": info["State"]["StartedAt"],
            "project": backend.binding["project"],
            "database": backend.binding["database"],
        },
        "actual_mysql_sample": copy.deepcopy(sample),
        "connection_budget": plan,
    }
    receipt = Path(backend.authority["budget_receipt_path"])
    receipt.write_bytes(canonical(saved))
    backend.authority["documents"]["mysql_budget"] = document(receipt.read_bytes())
    events, timeouts = [], []

    def output(argv):
        if "ps" in argv:
            return (info["Id"] + "\n").encode()
        if "image" in argv:
            return (backend.binding["image_ids"]["backend"] + "\n").encode()
        return canonical(info)

    def query(argv, **kwargs):
        assert lock_is_held(backend.phase / ".v4-operation.lock")
        assert kwargs["input"] == vendor.SQL.encode()
        assert argv[:4] == ["docker", "--context", "default", "exec"]
        assert argv[5] == info["Id"]
        assert "--skip-reconnect" in argv[-1]
        events.append("BUDGET_READ_ONLY_QUERY")
        timeouts.append(kwargs["timeout"])
        return SimpleNamespace(returncode=0, stdout=canonical(sample))

    backend.output = output
    monkeypatch.setattr("bridge_backend.subprocess.run", query)
    original = backend.phase_operation_lock

    @contextmanager
    def metadata_only(deadline):
        with original(deadline) as module:
            # /proc fixture only; original identity/admit/measure/numeric guard are unmodified.
            module.pid_start_ticks = lambda _pid: "4567"
            yield module

    backend.phase_operation_lock = metadata_only
    business = []

    class Runner:
        def run(self, _argv, _deadline, prefix):
            assert lock_is_held(backend.phase / ".v4-operation.lock")
            assert events == ["BUDGET_READ_ONLY_QUERY"]
            business.append("SQL")
            mode = prefix.name.removesuffix("-container")
            (prefix.parent / (mode + "-output/result.PUBLIC.json")).write_bytes(b"{}")

    backend.runner = Runner()
    return info, sample, receipt, events, business, timeouts


@pytest.mark.parametrize("mode", ["preflight", "seal"])
def test_original_admit_accepts_actual128_not_a384_default_before_each_SQL(
    backend, tmp_path, monkeypatch, mode
):
    _, _, _, events, business, _ = actual_budget_fixture(backend, monkeypatch)
    backend._data(mode, {"request": {}}, {"bridge_id": "owned"}, tmp_path, backend.deadline)
    proof = json.loads((tmp_path / (mode + "-budget-admission.PUBLIC.json")).read_text())
    assert proof["actual_max_connections"] == 128
    assert proof["connection_budget"]["required_max_connections"] == 124
    assert events == ["BUDGET_READ_ONLY_QUERY"] and business == ["SQL"]
    assert not lock_is_held(backend.phase / ".v4-operation.lock")


@pytest.mark.parametrize(
    "fault", ["receipt_sha", "capacity", "server_uuid", "restart", "container_id", "database"]
)
def test_original_admit_refuses_current_faults_before_any_business_SQL(
    backend, tmp_path, monkeypatch, fault
):
    info, sample, receipt, _, business, _ = actual_budget_fixture(backend, monkeypatch)
    if fault == "receipt_sha":
        receipt.write_bytes(receipt.read_bytes() + b" ")
    elif fault == "capacity":
        sample["max_connections"] = 123
    elif fault == "server_uuid":
        sample["server_uuid"] = "11112233-4455-6677-8899-aabbccddeeff"
    elif fault == "restart":
        info["RestartCount"] = 1
    elif fault == "container_id":
        info["Id"] = "4" * 64
    else:
        sample["database"] = "different_owned_database"
    with pytest.raises(ValueError):
        backend._data(
            "preflight", {"request": {}}, {"bridge_id": "owned"}, tmp_path, backend.deadline
        )
    assert business == []
    assert not lock_is_held(backend.phase / ".v4-operation.lock")


def test_original_budget_query_wait_is_clamped_to_remaining_callback_lease(
    backend, tmp_path, monkeypatch
):
    *_, business, timeouts = actual_budget_fixture(backend, monkeypatch)
    deadline = Deadline(backend.clock, backend.clock.now() + timedelta(seconds=3))
    backend._data("preflight", {"request": {}}, {"bridge_id": "owned"}, tmp_path, deadline)
    assert timeouts == [3]
    assert business == ["SQL"]


@pytest.mark.parametrize("fault", ["path", "binding", "source", "database"])
def test_public_authority_budget_context_rejects_cross_phase_or_changed_receipt(
    backend, monkeypatch, fault
):
    actual_budget_fixture(backend, monkeypatch)
    authority = copy.deepcopy(backend.authority)
    if fault == "path":
        authority["budget_receipt_path"] = str(
            backend.phase.parent
            / "other/receipts/mysql-budget-00000000000000000000000000000001.PUBLIC.json"
        )
    else:
        saved = json.loads(Path(authority["budget_receipt_path"]).read_bytes())
        if fault == "binding":
            saved["binding_sha256"] = "0" * 64
        elif fault == "source":
            saved["source_sha"] = "0" * 40
        else:
            saved["mysql_identity"]["database"] = "different_owned_database"
        authority["documents"]["mysql_budget"] = document(canonical(saved))
    with pytest.raises(Refused):
        budget_receipt_binding(authority, backend.binding)
