"""D008 frozen1.2 HTTP regression; controlled legacy rows are explicitly labelled."""

from datetime import UTC, datetime
from importlib import import_module
from uuid import uuid4

import pytest

http = import_module("tmp.backend.contracts.986_http")
pytestmark = pytest.mark.contract


def _ready(client, tokens, pid, iid):
    task = http.create_task(client, tokens, pid, iid)
    task = http.transition(client, tokens["developer"], pid, task, 1)
    task = http.transition(
        client,
        tokens["developer"],
        pid,
        task,
        4,
        artifact_revision="a" * 40,
        evidence=http.EVIDENCE,
    )
    result = http.request(
        client,
        "createTaskReview",
        token=tokens["reviewer"],
        project_id=pid,
        task_id=task["id"],
        body=http.review_payload(task),
        expect=201,
    ).json()["data"]
    return http.transition(
        client,
        tokens["reviewer"],
        pid,
        result["task"],
        5,
        review_id=result["review"]["id"],
        review_version=result["review"]["version"],
    )


def _assess(client, tokens, pid, task):
    return http.request(
        client,
        "createReleaseAssessment",
        token=tokens["manager"],
        project_id=pid,
        task_id=task["id"],
        body=http.assessment_payload(task),
        expect=201,
    ).json()["data"]


def _approve(client, tokens, pid, result):
    return http.request(
        client,
        "reviewReleaseAssessment",
        token=tokens["reviewer"],
        project_id=pid,
        task_id=result["task"]["id"],
        assessment_id=result["assessment"]["id"],
        body={
            "expected_version": result["task"]["version"],
            "expected_assessment_version": result["assessment"]["version"],
            "verdict": 1,
            "reason": "Independent synthetic reviewer approves",
            "evidence": http.EVIDENCE,
        },
        expect=200,
    ).json()["data"]


def _replan(client, tokens, pid, task):
    return http.request(
        client,
        "changeTaskPlan",
        token=tokens["manager"],
        project_id=pid,
        task_id=task["id"],
        body={
            "expected_version": task["version"],
            "plan": {**http.PLAN, "planned_end": "2026-10-26T00:00:00Z"},
            "reason": "Synthetic schedule changed after approval",
            "evidence": http.EVIDENCE,
        },
        expect=200,
    ).json()["data"]["task"]


def _release_body(task, assessment):
    return {
        "action": 7,
        "expected_version": task["version"],
        "assessment_id": assessment["id"],
        "assessment_version": assessment["version"],
        "release_version": "synthetic-d008-v1",
        "reason": "Manager release decision",
        "evidence": http.EVIDENCE,
    }


def _release(client, tokens, pid, task, body, *, key=None, expect=409, actor="manager"):
    return http.request(
        client,
        "transitionTask",
        token=tokens[actor],
        project_id=pid,
        task_id=task["id"],
        body=body,
        key=key,
        expect=expect,
    )


def _business(factory, pid):
    with factory() as uow:
        return {
            table: uow.gateway.rows(table, {"project_id": pid})
            for table in (
                "tasks",
                "reviews",
                "release_assessments",
                "decisions",
                "schedule_changes",
                "outbox_events",
            )
        }


def _audits(factory, pid):
    with factory() as uow:
        return uow.gateway.rows("audit_events", {"project_id": pid})


def _reject(client, factory, tokens, pid, task, assessment, code, *, body=None, actor="manager"):
    before, audit_before = _business(factory, pid), _audits(factory, pid)
    response = _release(
        client,
        tokens,
        pid,
        task,
        body or _release_body(task, assessment),
        actor=actor,
        expect=403 if code == "ACTION_FORBIDDEN" else 404 if code == "RESOURCE_NOT_FOUND" else 409,
    )
    payload = response.json()
    assert _business(factory, pid) == before
    audit_after = _audits(factory, pid)
    assert len(audit_after) == len(audit_before) + 1
    saved = next(row for row in audit_after if row["id"] == payload["audit_id"])
    assert saved["outcome"] == 2 and saved["operation_id"] == "transitionTask"
    assert saved["request_id"] == payload["request_id"] == response.headers["X-Request-ID"]
    if payload["code"] in {"RELEASE_APPROVAL_REQUIRED", "ASSESSMENT_BASELINE_MISMATCH"}:
        # Stable persisted IDs23/24 are specified in the frozen field dictionary.
        assert saved["reason_code"] == (
            23 if payload["code"] == "RELEASE_APPROVAL_REQUIRED" else 24
        )
    assert payload["code"] == code, {
        "actual_code": payload["code"],
        "audit_id": payload["audit_id"],
        "business_unchanged": True,
        "one_independent_rejection_audit_verified": True,
    }
    return response


def test_replan_dual_failure_requires_new_assessment_then_independent_approval(application):
    client, factory = application
    tokens, pid, iid = http.setup_project(client)
    approved = _approve(
        client, tokens, pid, _assess(client, tokens, pid, _ready(client, tokens, pid, iid))
    )
    old = approved["assessment"]
    task = _replan(client, tokens, pid, approved["task"])
    assert task["approved_assessment_id"] is None
    assert task["schedule_version"] != old["schedule_version"]
    _reject(client, factory, tokens, pid, task, old, "ASSESSMENT_BASELINE_MISMATCH")

    current = _assess(client, tokens, pid, task)
    task, assessment = current["task"], current["assessment"]
    assert task["schedule_version"] == assessment["schedule_version"]
    _reject(client, factory, tokens, pid, task, assessment, "RELEASE_APPROVAL_REQUIRED")
    current = _approve(client, tokens, pid, current)
    task, assessment = current["task"], current["assessment"]
    assert assessment["created_by"] != assessment["reviewed_by"]
    body, key = _release_body(task, assessment), str(uuid4())
    released = _release(client, tokens, pid, task, body, key=key, expect=200)
    first = released.json()
    assert first["data"]["task"]["state"] == 6
    assert first["meta"]["contract_version"] == "1.2.0"
    business, audits = _business(factory, pid), _audits(factory, pid)
    started = datetime.now(UTC)
    replay = _release(client, tokens, pid, task, body, key=key, expect=200).json()
    assert replay["data"] == first["data"]
    assert replay["meta"]["replayed"] is True
    assert replay["meta"]["original_request_id"] == first["meta"]["request_id"]
    assert replay["meta"]["request_id"] != first["meta"]["request_id"]
    assert replay["meta"]["contract_version"] == "1.2.0"
    assert datetime.fromisoformat(replay["meta"]["server_time"]) >= started
    assert (_business(factory, pid), _audits(factory, pid)) == (business, audits)


def test_completed_approval_error_replays_original_values_after_schedule_changes(application):
    client, factory = application
    tokens, pid, iid = http.setup_project(client)
    result = _assess(client, tokens, pid, _ready(client, tokens, pid, iid))
    task, assessment = result["task"], result["assessment"]
    body, key = _release_body(task, assessment), str(uuid4())
    first = _release(client, tokens, pid, task, body, key=key)
    assert first.json()["code"] == "RELEASE_APPROVAL_REQUIRED"
    with factory() as uow:
        saved = uow.gateway.rows("idempotency_requests", {"idempotency_key": key})
        assert len(saved) == 1 and saved[0]["status"] == 2
        assert saved[0]["response_request_id"] == first.json()["request_id"]
        assert "request_id" not in saved[0]["response_body"]["error"]
    task = _replan(client, tokens, pid, task)
    business, audits = _business(factory, pid), _audits(factory, pid)
    replay = _release(client, tokens, pid, task, body, key=key)
    assert replay.headers["Idempotency-Replayed"] == "true"
    assert replay.status_code == first.status_code
    assert {k: v for k, v in replay.json().items() if k != "request_id"} == {
        k: v for k, v in first.json().items() if k != "request_id"
    }
    assert replay.json()["request_id"] != first.json()["request_id"]
    assert replay.json()["request_id"] == replay.headers["X-Request-ID"]
    assert "meta" not in replay.json() and "original_request_id" not in replay.json()
    assert (_business(factory, pid), _audits(factory, pid)) == (business, audits)
    _reject(client, factory, tokens, pid, task, assessment, "ASSESSMENT_BASELINE_MISMATCH")


def test_controlled_cycle_mismatch_uses_failed_approval_slot_without_real_rework(application):
    client, factory = application
    tokens, pid, iid = http.setup_project(client)
    result = _assess(client, tokens, pid, _ready(client, tokens, pid, iid))
    task, assessment = result["task"], result["assessment"]
    # Deliberately controlled legacy-row boundary, not a real rework/delivery history.
    with factory() as uow:
        uow.gateway.update("release_assessments", {"id": assessment["id"]}, {"delivery_cycle": 2})
    _reject(client, factory, tokens, pid, task, assessment, "ASSESSMENT_BASELINE_MISMATCH")


@pytest.mark.parametrize("case", ["task_version", "request_version", "foreign", "missing"])
def test_release_reference_preconditions_keep_original_priority(application, case):
    client, factory = application
    tokens, pid, iid = http.setup_project(client)
    approved = _approve(
        client, tokens, pid, _assess(client, tokens, pid, _ready(client, tokens, pid, iid))
    )
    task, assessment = _replan(client, tokens, pid, approved["task"]), approved["assessment"]
    body = _release_body(task, assessment)
    code = "ASSESSMENT_BASELINE_MISMATCH"
    if case == "task_version":
        body["expected_version"] -= 1
        code = "VERSION_CONFLICT"
    elif case == "request_version":
        body["assessment_version"] += 1
    elif case == "foreign":
        other = _assess(client, tokens, pid, _ready(client, tokens, pid, iid))["assessment"]
        body.update(assessment_id=other["id"], assessment_version=other["version"])
        code = "RESOURCE_NOT_FOUND"
    else:
        body["assessment_id"] = 4294967295
        code = "RELEASE_APPROVAL_REQUIRED"
    _reject(client, factory, tokens, pid, task, assessment, code, body=body)


@pytest.mark.parametrize(
    ("case", "code"),
    [
        ("state", "STATE_CONFLICT"),
        ("role", "ACTION_FORBIDDEN"),
        ("review", "REVIEW_NOT_PASSED"),
        ("baseline", "ASSESSMENT_BASELINE_MISMATCH"),
    ],
)
def test_controlled_matching_reference_keeps_original_domain_order(application, case, code):
    client, factory = application
    tokens, pid, iid = http.setup_project(client)
    approved = _approve(
        client, tokens, pid, _assess(client, tokens, pid, _ready(client, tokens, pid, iid))
    )
    task, assessment = _replan(client, tokens, pid, approved["task"]), approved["assessment"]
    values = {
        "approved_assessment_id": assessment["id"],
        "approved_assessment_version": assessment["version"],
    }
    if case == "state":
        values["state"] = 2
    elif case == "review":
        values["approved_review_id"] = None
    # Controlled, labelled inconsistent legacy row: normal replan clears these references.
    with factory() as uow:
        uow.gateway.update("tasks", {"id": task["id"]}, values)
    _reject(
        client,
        factory,
        tokens,
        pid,
        task,
        assessment,
        code,
        actor="developer" if case == "role" else "manager",
    )
