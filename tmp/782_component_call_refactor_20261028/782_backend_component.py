"""Backend component/Call boundary checks; no DB or end-to-end notification claim."""

from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from t44.services.application import Business
from t44.services.common import Call
from t44.services.errors import Rejected


@pytest.mark.parametrize(
    "operation,component,method",
    [
        ("listMyNotifications", "notifications", "list"),
        ("markNotificationRead", "notifications", "mark_read"),
        ("handleNotification", "notifications", "handle"),
        ("getEscalationRules", "escalations", "rules"),
        ("listEscalations", "escalations", "list"),
        ("createEscalation", "escalations", "create"),
    ],
)
def test_component_receives_exact_trusted_gateway_and_call(operation, component, method):
    gateway, result, seen = object(), object(), []
    call = Call(operation, "synthetic-component-boundary", None)

    def receive(actual_gateway, actual_call):
        seen.append((actual_gateway, actual_call))
        return result

    owner = SimpleNamespace(**{method: receive})
    business = Business(**{component: owner})
    assert business.dispatch(gateway, call) is result
    assert len(seen) == 1
    assert seen[0][0] is gateway and seen[0][1] is call


@pytest.mark.parametrize("operation", ["handleNotification", "createEscalation"])
def test_missing_owner_precedes_missing_context_fields(operation):
    call = Call(operation, "synthetic-missing-owner", None)
    with pytest.raises(Rejected) as error:
        Business().dispatch(object(), call)
    assert (error.value.code, error.value.status) == ("DEPENDENCY_UNAVAILABLE", 503)


class Gateway:
    def __init__(self, changed=1):
        self.changed, self.updates = changed, []

    def update(self, table, where, values):
        self.updates.append((table, where, values))
        return self.changed


def context(expected=7):
    call = Call(
        "markNotificationRead",
        "synthetic-cas-boundary",
        None,
        body={"expected_version": expected},
        clock=datetime(2026, 10, 28, tzinfo=UTC),
    )
    call.before = [{"field": "prior", "value": "before"}]
    call.after = [{"field": "prior", "value": "after"}]
    return call


@pytest.mark.parametrize("record_diff", [None, False])
def test_cas_default_records_versions_false_preserves_existing_diff(record_diff):
    call, gateway = context(), Gateway()
    before, after = call.before, call.after
    row = {"id": 17, "version": 7, "read_at": None}
    values = {"read_at": call.clock}
    options = {} if record_diff is None else {"record_diff": record_diff}
    changed = call.cas(gateway, "notifications", row, values, **options)
    assert changed == {"id": 17, "version": 8, "read_at": call.clock}
    assert gateway.updates == [
        ("notifications", {"id": 17, "version": 7}, {"read_at": call.clock, "version": 8})
    ]
    assert row == {"id": 17, "version": 7, "read_at": None}
    assert values == {"read_at": call.clock}
    if record_diff is None:
        assert call.before == [{"field": "version", "value": "7"}]
        assert call.after == [{"field": "version", "value": "8"}]
    else:
        assert call.before is before and call.after is after
        assert call.before == [{"field": "prior", "value": "before"}]
        assert call.after == [{"field": "prior", "value": "after"}]


@pytest.mark.parametrize("case", ["stale", "maximum", "race"])
def test_false_diff_keeps_version_guards_and_failed_cas_side_effects(case):
    version = 2147483647 if case == "maximum" else 7
    call = context(expected=version - 1 if case == "stale" else version)
    before, after = call.before, call.after
    gateway = Gateway(changed=0 if case == "race" else 1)
    row = {"id": 17, "version": version, "state": 2}
    with pytest.raises(Rejected) as error:
        call.cas(gateway, "tasks", row, {"state": 3}, record_diff=False)
    assert (error.value.code, error.value.current_version, error.value.current_state) == (
        "VERSION_CONFLICT",
        version,
        2,
    )
    assert len(gateway.updates) == int(case == "race")
    assert row == {"id": 17, "version": version, "state": 2}
    assert call.before is before and call.after is after


def test_false_diff_keeps_explicit_expected_override_and_updated_at():
    call, gateway = context(expected=1), Gateway()
    before, after = call.before, call.after
    old_time = datetime(2026, 10, 27, tzinfo=UTC)
    row = {"id": 17, "version": 7, "updated_at": old_time}
    changed = call.cas(gateway, "tasks", row, {}, expected=7, record_diff=False)
    assert changed == {"id": 17, "version": 8, "updated_at": call.clock}
    assert gateway.updates == [
        ("tasks", {"id": 17, "version": 7}, {"version": 8, "updated_at": call.clock})
    ]
    assert row == {"id": 17, "version": 7, "updated_at": old_time}
    assert call.before is before and call.after is after
