"""Necessary P64 identity/grant/SQL-adapter guards; no cloud or SUT."""

import base64
import hashlib
import importlib
import importlib.util
import json
import sys
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "edge"))
authority = importlib.import_module("790_authority")
guard = importlib.import_module("790_budget")
from grant_fixture import pressure  # noqa: E402 -- owned source-free fixture after explicit module path.

UTC = timezone.utc  # noqa: UP017 -- host3.10.


def control():
    return pressure(
        {
            "kind": "t44-contrast-development-v1",
            "source_sha": authority.SOURCE,
            "run_id": "r28p64gen01",
            "binding_sha256": "a" * 64,
            "namespace": "t44-cloud-r28p64gen01-p",
            "database": "t44c_r28p64gen01_p",
            "api_workers": 64,
            "seed": 44,
            "anchor_at": authority.ANCHOR,
            "stop_utc": authority.STOP,
            "url": "https://192.168.1.9:19445",
            "ca_sha256": "b" * 64,
        }
    )


def changed(value, field, item):
    grant = json.loads(base64.b64decode(value["root_grant_b64"]))
    grant[field] = item
    raw = json.dumps(grant).encode()
    return {
        **value,
        "root_grant_b64": base64.b64encode(raw).decode(),
        "root_grant_sha256": hashlib.sha256(raw).hexdigest(),
    }


def test_prep_does_not_authorize_HTTP():
    value = pressure(control(), "prep")
    assert (
        authority.check_control(value, "prep", datetime(2026, 10, 28, 6, tzinfo=UTC))[
            "HTTP_authorized"
        ]
        is False
    )
    with pytest.raises(ValueError, match="WRONG_ROOT_GRANT_STAGE"):
        authority.check_control(value, "pressure", datetime(2026, 10, 28, 6, tzinfo=UTC))


@pytest.mark.parametrize(
    "field,item",
    [
        ("source_sha", "0" * 40),
        ("api_workers", 16),
        ("seed", 45),
        ("session_ttl_seconds", 601),
        ("cohorts", [["measure400", 400, 1, 0]]),
        ("formal_performance_authorized", True),
        ("no_automatic_retry", False),
    ],
)
def test_changed_pressure_grant_is_rejected(field, item):
    with pytest.raises(ValueError):
        authority.check_control(
            changed(control(), field, item), "pressure", datetime(2026, 10, 28, 6, tzinfo=UTC)
        )


def test_default_no_grant_refuses_before_any_network(tmp_path, monkeypatch):
    http = importlib.import_module("790_http")
    value = control()
    del value["root_grant_b64"]
    raw = json.dumps(value).encode()
    path = tmp_path / "control.private.json"
    path.write_bytes(raw)
    path.chmod(0o600)
    attempts = []
    monkeypatch.setattr("socket.socket.connect", lambda *_args: attempts.append("NETWORK"))
    monkeypatch.setattr(http, "CONTROL", None)
    with pytest.raises((KeyError, ValueError)):
        http.configure(path, hashlib.sha256(raw).hexdigest())
    assert attempts == []


def test_pressure_requires_six_actual_roles_and_scheduler_absent():
    value = control()
    grant = json.loads(base64.b64decode(value["root_grant_b64"]))
    grant["roles"]["api"] = {"absent": True}
    with pytest.raises(ValueError):
        authority.check_control(
            changed(value, "roles", grant["roles"]),
            "pressure",
            datetime(2026, 10, 28, 6, tzinfo=UTC),
        )
    grant = json.loads(base64.b64decode(value["root_grant_b64"]))
    grant["roles"]["scheduler"] = {
        "container_id": "3" * 64,
        "image_id": "sha256:" + "4" * 64,
        "running": True,
        "restart_count": 0,
    }
    with pytest.raises(ValueError):
        authority.check_control(
            changed(value, "roles", grant["roles"]),
            "pressure",
            datetime(2026, 10, 28, 6, tzinfo=UTC),
        )


def test_e551_dependency_wrong_pin_refuses_before_import(tmp_path):
    (tmp_path / "manifest.PUBLIC.json").write_bytes(b"{}")
    with pytest.raises(ValueError, match="APPROVED_E551_BRIDGE_ONLY"):
        guard.modules(tmp_path)


@pytest.mark.parametrize("refuse", [False, True])
def test_thin_SQL_adapter_admits_inside_lock_before_caller_body(tmp_path, monkeypatch, refuse):
    common_path = HERE.parent / "scope-callback-bridge-v3-budget/bridge_common.py"
    spec = importlib.util.spec_from_file_location("own_p64_bridge_common", common_path)
    common = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(common)
    phase = tmp_path / "p"
    phase.mkdir()
    receipt = phase / "receipts/mysql-budget-00000000000000000000000000000001.PUBLIC.json"
    receipt.parent.mkdir()
    raw = b"{}"
    receipt.write_bytes(raw)
    receipt.chmod(0o600)
    args = SimpleNamespace(
        phase_dir=phase,
        scope_bridge_dir=tmp_path,
        binding_sha256="c" * 64,
        budget_receipt=receipt,
        budget_receipt_sha256=common.sha(raw),
    )
    events = []

    class Backend:
        def __init__(self, *_args):
            pass

        @contextmanager
        def phase_operation_lock(self, _deadline):
            events.append("LOCK")
            try:
                yield object()
            finally:
                events.append("UNLOCK")

        def admit_budget(self, _budget, _deadline):
            events.append("ADMIT")
            if refuse:
                raise ValueError("ACTUAL_CAPACITY_REFUSED")
            return {"actual_max_connections": 384}

    adapter = SimpleNamespace(DockerBackend=Backend, budget_receipt_binding=lambda *_args: None)
    monkeypatch.setattr(guard, "modules", lambda _path: (common, adapter))
    if refuse:
        with pytest.raises(ValueError, match="ACTUAL_CAPACITY_REFUSED"), guard.admitted(
            args, {"file_hashes": {"mysql-budget.py": guard.HELPER}}, "2031-01-01T16:00:00Z"
        ):
            events.append("SQL")
        assert events == ["LOCK", "ADMIT", "UNLOCK"]
    else:
        with guard.admitted(
            args, {"file_hashes": {"mysql-budget.py": guard.HELPER}}, "2031-01-01T16:00:00Z"
        ):
            events.append("SQL")
        assert events == ["LOCK", "ADMIT", "SQL", "UNLOCK"]
