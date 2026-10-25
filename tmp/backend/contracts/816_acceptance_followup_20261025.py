"""Public F08 role-priority regression, using independent development fixtures only."""

from importlib import import_module
from uuid import uuid4

import pytest

priority = import_module("tmp.backend.contracts.856_release_error_priority")
http = import_module("tmp.backend.contracts.986_http")
pytestmark = pytest.mark.contract


@pytest.mark.parametrize("stale_baseline", [False, True])
def test_unapproved_deliver_requires_manager_before_assessment_gate(application, stale_baseline):
    client, factory = application
    tokens, pid, iid = http.setup_project(client)
    result = priority._assess(client, tokens, pid, priority._ready(client, tokens, pid, iid))
    if stale_baseline:
        result = priority._approve(client, tokens, pid, result)
        task = priority._replan(client, tokens, pid, result["task"])
    else:
        task = result["task"]
    assessment = result["assessment"]
    assert task["state"] == 5 and task["approved_assessment_id"] is None
    assert (task["schedule_version"] != assessment["schedule_version"]) is stale_baseline
    with factory() as uow:
        member = uow.gateway.rows("project_members", {"project_id": pid, "user_id": 2, "active": 1})
        assert len(member) == 1 and member[0]["roles_mask"] == 2
    before, audit_before = priority._business(factory, pid), priority._audits(factory, pid)
    body, key = priority._release_body(task, assessment), str(uuid4())
    first = priority._release(
        client, tokens, pid, task, body, key=key, expect=None, actor="developer"
    )
    payload = first.json()
    # Check all rejection postconditions even on the old wrong-code response.
    assert priority._business(factory, pid) == before
    audits = priority._audits(factory, pid)
    assert len(audits) == len(audit_before) + 1
    saved = next(row for row in audits if row["id"] == payload["audit_id"])
    assert saved["outcome"] == 2 and saved["operation_id"] == "transitionTask"
    assert saved["request_id"] == payload["request_id"] == first.headers["X-Request-ID"]
    replay = priority._release(
        client, tokens, pid, task, body, key=key, expect=first.status_code, actor="developer"
    )
    assert {k: v for k, v in replay.json().items() if k != "request_id"} == {
        k: v for k, v in payload.items() if k != "request_id"
    }
    assert replay.json()["request_id"] != payload["request_id"]
    assert priority._audits(factory, pid) == audits
    assert priority._business(factory, pid) == before
    assert (first.status_code, payload["code"], saved["reason_code"]) == (
        403,
        "ACTION_FORBIDDEN",
        6,
    )


@pytest.mark.parametrize("actor", ["manager", "developer"])
def test_failed_approval_slot_keeps_state_before_manager_guard(application, actor):
    client, factory = application
    tokens, pid, iid = http.setup_project(client)
    result = priority._approve(
        client,
        tokens,
        pid,
        priority._assess(client, tokens, pid, priority._ready(client, tokens, pid, iid)),
    )
    task = priority._replan(client, tokens, pid, result["task"])
    task = http.transition(
        client,
        tokens["manager"],
        pid,
        task,
        2,
        reason="Synthetic release-stage block",
        responsibility_stage=4,
        evidence=http.EVIDENCE,
    )
    assert task["state"] == 3 and task["blocked_from_state"] == 5
    assert task["approved_assessment_id"] is None
    priority._reject(
        client, factory, tokens, pid, task, result["assessment"], "STATE_CONFLICT", actor=actor
    )
