"""Notification Call migration boundaries; no external service or acceptance claim."""

from datetime import UTC, datetime
from unittest.mock import Mock

import pytest
from t44.messaging.facade import NotificationFacade
from t44.services.common import Call
from t44.services.errors import Rejected
from t44.services.runtime import Runtime
from t44.settings import Settings


@pytest.fixture
def case():
    clock = datetime(2026, 10, 28, 12, tzinfo=UTC)
    row = dict(
        id=3, project_id=2, task_id=5, event_id=7, recipient_id=1, version=1,
        level=1, title="synthetic", message="synthetic", fallback=False,
        read_at=None, handled_at=None, handling_note=None, created_at=clock,
    )
    gateway = Mock()
    gateway.get.side_effect = lambda table, *_args, **_kw: {"id": 2} if table == "projects" else row
    gateway.rows.return_value = [{"project_id": 2}]
    gateway.update.return_value = 1
    call = Call(
        "handleNotification", "synthetic-notification-call", None,
        actor={"actor_id": 1, "actor_kind": 1, "id": 11},
        project={"id": 2}, path={"project_id": 2, "notification_id": 3},
        body={"expected_version": 1, "note": "checked", "evidence": [{"kind": 1}]},
        clock=clock,
    )
    return NotificationFacade(), gateway, call, row


@pytest.mark.parametrize("observed,expected", [(2, 1), (2147483647, 2147483647)])
def test_version_refuses_before_lazy_values_or_write(case, observed, expected):
    facade, gateway, call, row = case
    row["version"], call.body["expected_version"] = observed, expected
    values = Mock(side_effect=AssertionError("values must stay lazy"))
    with pytest.raises(Rejected, match="VERSION_CONFLICT") as error:
        facade._update(gateway, call, values)
    assert error.value.current_version == observed and error.value.current_state is None
    values.assert_not_called()
    gateway.update.assert_not_called()
    assert call.before == call.after == []


def test_recipient_rejection_precedes_stale_version_and_values(case):
    facade, gateway, call, row = case
    row.update(recipient_id=9, version=4)
    values = Mock(side_effect=AssertionError("values must stay lazy"))
    with pytest.raises(Rejected, match="ACTION_FORBIDDEN"):
        facade._update(gateway, call, values)
    values.assert_not_called()
    gateway.update.assert_not_called()
    assert gateway.get.call_args_list[-1].kwargs == {"lock": "update"}


def test_empty_evidence_refuses_before_any_scope_query(case):
    facade, gateway, call, _row = case
    call.body["evidence"] = []
    with pytest.raises(Rejected, match="EVIDENCE_REQUIRED"):
        facade.handle(gateway, call)
    gateway.get.assert_not_called()
    gateway.rows.assert_not_called()
    gateway.update.assert_not_called()


def test_mark_read_preserves_existing_timestamp_and_call_diffs(case):
    facade, gateway, call, row = case
    read_at = datetime(2026, 10, 27, 12, tzinfo=UTC)
    row["read_at"] = read_at
    before, after = call.before, call.after
    result = facade.mark_read(gateway, call)
    assert result["version"] == 2 and result["handled_at"] is None
    assert gateway.update.call_args.args == (
        "notifications", {"id": 3, "version": 1}, {"read_at": read_at, "version": 2}
    )
    assert call.before is before and call.after is after and before == after == []
    assert row["version"] == 1


def test_handle_keeps_read_independent_and_runtime_still_audits_empty_diffs(case):
    facade, gateway, call, row = case
    before, after = call.before, call.after
    result = facade.handle(gateway, call)
    assert result["version"] == 2 and result["read_at"] is None and result["handled_at"]
    assert gateway.update.call_args.args == (
        "notifications", {"id": 3, "version": 1},
        {"handled_at": call.clock, "handling_note": "checked", "handling_evidence": [{"kind": 1}], "version": 2},
    )
    assert call.before is before and call.after is after and before == after == []
    Runtime(None, Settings(), None).audit(gateway, call)
    table, values = gateway.insert.call_args.args
    assert table == "audit_events" and values["outcome"] == 1
    assert values["before_values"] == values["after_values"] == []
    assert row["read_at"] is None and row["version"] == 1


def test_failed_compare_and_swap_keeps_error_version_and_empty_diffs(case):
    facade, gateway, call, row = case
    gateway.update.return_value = 0
    with pytest.raises(Rejected, match="VERSION_CONFLICT") as error:
        facade.mark_read(gateway, call)
    assert error.value.current_version == 1 and error.value.current_state is None
    assert gateway.update.call_args.args[1] == {"id": 3, "version": 1}
    assert row["version"] == 1 and call.before == call.after == []
