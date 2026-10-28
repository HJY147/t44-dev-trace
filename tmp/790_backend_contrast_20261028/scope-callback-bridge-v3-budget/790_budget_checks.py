"""Owned v3 budget regressions. All MySQL rows are synthetic; no SUT/network."""

import os
import sys
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from bridge_backend import DockerBackend
from bridge_common import Deadline, canonical, document

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
        "database": "owned_synthetic_f", "project": "owned-synthetic-f", "source_sha": "b" * 40,
        "images": {"backend": {"alias": "owned-synthetic-image"}},
        "image_ids": {"backend": "sha256:" + "1" * 64},
        "config_ids": {"backend": "sha256:" + "1" * 64},
    }
    value.authority = {"documents": {"binding": {"sha256": "c" * 64},
                                       "mysql_budget": document(b"{}")},
                       "budget_receipt_path": str(receipt)}
    value.source_files = {}
    value.output = lambda _argv: ("sha256:" + "1" * 64 + "\n").encode()
    monkeypatch.setattr(os, "chown", lambda *_args: None)
    return value


@pytest.mark.parametrize("action", ["scheduler-token", "scheduler-rotate", "scheduler-start"])
def test_every_GEN_scheduler_call_passes_exact_budget_receipt(backend, tmp_path, action):
    class Runner:
        def run(self, argv, _deadline, _prefix):
            assert "--budget-receipt" in argv, "v4 GEN requires an actual budget receipt"
            assert argv[argv.index("--budget-receipt") + 1] == backend.authority["budget_receipt_path"]
            assert "--budget-receipt-sha256" in argv
            assert argv[argv.index("--budget-receipt-sha256") + 1] == backend.authority["documents"]["mysql_budget"]["sha256"]
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
