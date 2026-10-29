"""Regress the actual delayed-provider-start rejection, without network or credentials."""

import importlib.util
from datetime import UTC, datetime
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location(
    "provider_v7", Path(__file__).with_name("821_provider_v7.py")
)
provider = importlib.util.module_from_spec(spec)
spec.loader.exec_module(provider)


def test_valid_scope_request_may_precede_provider_start(monkeypatch):
    monkeypatch.setattr(provider.time, "time", lambda: 140)
    supervisor = {"launch_clock": {"utc": datetime.fromtimestamp(100, UTC).isoformat()}}
    grant = {
        "tool_freeze_sha256": "frozen",
        "build": {"runtime_identity": "runtime", "source_sha": "source"},
        "isolated_resource_ids": ["new-db"],
        "expires_at": datetime.fromtimestamp(200, UTC).isoformat(),
    }
    request = {
        "kind": "SERVICE_SCOPE_REQUEST",
        "project_ids": [13],
        "scope": ["escalation:write"],
        "nonce": "a" * 48,
        "requested_utc": datetime.fromtimestamp(101, UTC).isoformat(),
        "context": {
            "tool_freeze_sha256": "frozen",
            "native_runtime_identity": "runtime",
            "source_sha": "source",
            "phase": "functional",
            "resource_ids": ["new-db"],
            "supervisor_nonce": "active",
        },
    }
    assert (
        provider.validate(
            request, grant, provider.phase_request_anchor(supervisor), "active"
        )
        == 13
    )
    with pytest.raises(ValueError):
        provider.validate(request, grant, 140, "active")


def test_fresh_scope_namespace_stays_under_approved_parent():
    parent = provider.ROOT_PRIVATE / "provisioned"
    target = parent / ("functional-v7-" + "a" * 48) / ("b" * 48)
    assert target.is_relative_to(parent)
    assert not (provider.ROOT_PRIVATE / "provisioned-v6-resume").is_relative_to(parent)
