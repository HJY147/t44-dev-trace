"""No database/network access: reject scope and runtime confusion at the provider boundary."""

import importlib.util
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location(
    "provider", Path(__file__).with_name("821_provider.py")
)
provider = importlib.util.module_from_spec(spec)
spec.loader.exec_module(provider)


def inputs():
    grant = {
        "tool_freeze_sha256": "frozen",
        "build": {"runtime_identity": "new-native", "source_sha": "source"},
        "isolated_resource_ids": ["new-schema", "new-broker"],
        "expires_at": (datetime.now(UTC) + timedelta(minutes=1)).isoformat(),
    }
    request = {
        "kind": "SERVICE_SCOPE_REQUEST",
        "scope": ["escalation:write"],
        "project_ids": [7],
        "nonce": "a" * 48,
        "requested_utc": datetime.now(UTC).isoformat(),
        "context": {
            "tool_freeze_sha256": "frozen",
            "native_runtime_identity": "new-native",
            "source_sha": "source",
            "phase": "functional",
            "resource_ids": ["new-schema", "new-broker"],
            "supervisor_nonce": "active-supervisor",
        },
    }
    return grant, request


@pytest.mark.parametrize(
    "change",
    ["union", "boolean_id", "other_runtime", "old_resource", "wrong_scope", "expired"],
)
def test_refuse_scope_or_environment_confusion(change):
    grant, request = inputs()
    if change == "union":
        request["project_ids"] = [7, 8]
    elif change == "boolean_id":
        request["project_ids"] = [True]
    elif change == "other_runtime":
        request["context"]["native_runtime_identity"] = "old-native"
    elif change == "old_resource":
        request["context"]["resource_ids"] = ["old-schema", "old-broker"]
    elif change == "wrong_scope":
        request["scope"] = ["*"]
    else:
        grant["expires_at"] = (datetime.now(UTC) - timedelta(seconds=1)).isoformat()
    with pytest.raises(ValueError):
        provider.validate(request, grant, time.time() - 1)


def test_accept_only_exact_current_single_project_scope():
    grant, request = inputs()
    assert provider.validate(request, grant, time.time() - 1) == 7
