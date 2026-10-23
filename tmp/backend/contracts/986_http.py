"""Actual TestClient requests/responses and committed SQLite application state."""

from uuid import uuid4

import pytest
from t44.contracts import OPERATIONS, SPEC, violations
from t44.services.reviews import TEMPLATE

pytestmark = pytest.mark.contract
EVIDENCE = [
    {"kind": 2, "locator": "self-test/evidence", "description": "Synthetic module self-test"}
]
PLAN = {
    "planned_start": "2026-10-23T00:00:00Z",
    "planned_end": "2026-10-25T00:00:00Z",
    "estimated_hours": 8,
    "buffer_hours": 1,
    "delay_contingency": "Manager replans with evidence",
}


def request(client, operation, *, token=None, body=None, key=None, expect=None, query=None, **path):
    op = OPERATIONS[operation]
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    if any(p.get("$ref", "").endswith("/IdempotencyKey") for p in op.get("parameters", [])):
        headers["Idempotency-Key"] = key or str(uuid4())
    response = client.request(
        op["method"],
        "/api/v1" + op["path"].format(**path),
        headers=headers,
        json=body,
        params=query,
    )
    if expect is not None:
        assert response.status_code == expect, response.text
    schema = op["responses"][str(response.status_code)]["content"]["application/json"]["schema"]
    assert not violations(schema, response.json()), response.text
    assert response.headers["cache-control"] == "no-store"
    return response


def login(client, name="manager"):
    return request(
        client, "login", body={"username": name, "password": "test-only-password"}, expect=200
    ).json()["data"]["access_token"]


def setup_project(client):
    tokens = {
        name: login(client, name) for name in ("manager", "developer", "reviewer", "outsider")
    }
    project = request(
        client,
        "createProject",
        token=tokens["manager"],
        body={"name": "O'Reilly project"},
        expect=201,
    ).json()["data"]
    pid = project["id"]
    for name, role in (("developer", [2]), ("reviewer", [1, 3])):
        request(
            client,
            "addProjectMember",
            token=tokens["manager"],
            project_id=pid,
            body={"username": name, "roles": role, "reason": "Synthetic team"},
            expect=201,
        )
    iteration = request(
        client,
        "createIteration",
        token=tokens["manager"],
        project_id=pid,
        body={
            "name": "v1",
            **{k: v for k, v in PLAN.items() if k != "estimated_hours"},
            "capacity": [{"user_id": 2, "available_hours": 40}],
        },
        expect=201,
    ).json()["data"]
    return tokens, pid, iteration["id"]


def create_task(client, tokens, pid, iid, deps=()):
    return request(
        client,
        "createTask",
        token=tokens["manager"],
        project_id=pid,
        body={
            "title": "Implement synthetic task",
            "owner_id": 2,
            "iteration_id": iid,
            "plan": PLAN,
            "dependency_task_ids": list(deps),
        },
        expect=201,
    ).json()["data"]["task"]


def transition(client, token, pid, task, action, expect=200, **fields):
    response = request(
        client,
        "transitionTask",
        token=token,
        project_id=pid,
        task_id=task["id"],
        body={"expected_version": task["version"], "action": action, **fields},
        expect=expect,
    )
    return response.json()["data"]["task"] if expect == 200 else response


def review_payload(task, verdict=1):
    return {
        "expected_version": task["version"],
        "template_version": 1,
        "artifact_revision": "a" * 40,
        "verdict": verdict,
        "sections": [
            {"section_id": s["section_id"], "content": "Synthetic review", "evidence": EVIDENCE}
            for s in TEMPLATE["sections"]
        ],
        "checklist": [
            {
                "item_id": i["item_id"],
                "judgment": 1,
                "rationale": "Synthetic proof",
                "evidence": EVIDENCE,
            }
            for i in TEMPLATE["items"]
        ],
    }


def assessment_payload(task):
    return {
        "expected_version": task["version"],
        "risks": [
            {
                "perspective": p,
                "severity": 1,
                "risk": "Synthetic risk",
                "mitigation": "Synthetic mitigation",
                "evidence": EVIDENCE,
            }
            for p in (1, 2, 3, 4)
        ],
        "rollback_plan": {
            "target_version": "v0",
            "trigger": "Failed release",
            "steps": ["Restore v0"],
            "impact": "Brief outage",
            "verification": "Run checks",
            "responsible_user_id": 1,
            "evidence": EVIDENCE,
        },
    }


@pytest.mark.parametrize("old_approved", [True, False])
def test_new_assessment_supersedes_old_approval_without_replay_side_effects(
    application, old_approved
):
    client, factory = application
    tokens, pid, iid = setup_project(client)
    task = create_task(client, tokens, pid, iid)
    task = transition(client, tokens["developer"], pid, task, 1)
    task = transition(
        client,
        tokens["developer"],
        pid,
        task,
        4,
        artifact_revision="a" * 40,
        evidence=EVIDENCE,
    )
    reviewed = request(
        client,
        "createTaskReview",
        token=tokens["reviewer"],
        project_id=pid,
        task_id=task["id"],
        body=review_payload(task),
        expect=201,
    ).json()["data"]
    task = transition(
        client,
        tokens["reviewer"],
        pid,
        reviewed["task"],
        5,
        review_id=reviewed["review"]["id"],
        review_version=1,
    )

    def assess(current, *, body=None, key=None):
        return request(
            client,
            "createReleaseAssessment",
            token=tokens["manager"],
            project_id=pid,
            task_id=task["id"],
            body=body or assessment_payload(current),
            key=key,
            expect=201,
        )

    def approve(current, assessment, expect=200):
        return request(
            client,
            "reviewReleaseAssessment",
            token=tokens["reviewer"],
            project_id=pid,
            task_id=task["id"],
            assessment_id=assessment["id"],
            body={
                "expected_version": current["version"],
                "expected_assessment_version": assessment["version"],
                "verdict": 1,
                "reason": "Synthetic independent review",
                "evidence": EVIDENCE,
            },
            expect=expect,
        )

    created_a = assess(task).json()["data"]
    task, old = created_a["task"], created_a["assessment"]
    if old_approved:
        accepted = approve(task, old).json()["data"]
        task, old = accepted["task"], accepted["assessment"]
        assert task["approved_assessment_id"] == old["id"]
    body, key = assessment_payload(task), str(uuid4())
    created_b = assess(task, body=body, key=key).json()["data"]
    task, latest = created_b["task"], created_b["assessment"]
    assert task["approved_assessment_id"] is None
    assert task["approved_assessment_version"] is None
    assert task["state"] == 5
    if not old_approved:
        assert approve(task, old, 409).json()["code"] == "ASSESSMENT_BASELINE_MISMATCH"
    rejected = transition(
        client,
        tokens["manager"],
        pid,
        task,
        7,
        expect=409,
        assessment_id=old["id"],
        assessment_version=old["version"],
        release_version="synthetic-v1",
        reason="Old approval must not release",
        evidence=EVIDENCE,
    )
    assert rejected.json()["code"] == "RELEASE_APPROVAL_REQUIRED"
    assert rejected.json()["audit_id"] is not None
    accepted = approve(task, latest).json()["data"]
    task, latest = accepted["task"], accepted["assessment"]
    assert task["approved_assessment_id"] == latest["id"]
    assert task["approved_assessment_version"] == latest["version"]
    old_response = approve(task, old, 409)
    assert old_response.json()["code"] == (
        "STATE_CONFLICT" if old_approved else "ASSESSMENT_BASELINE_MISMATCH"
    )
    replay = assess(task, body=body, key=key)
    assert replay.json()["meta"]["replayed"] is True
    assert replay.json()["data"] == created_b
    current = request(
        client,
        "getTask",
        token=tokens["manager"],
        project_id=pid,
        task_id=task["id"],
        expect=200,
    ).json()["data"]
    assert current == task
    with factory() as uow:
        assert uow.gateway.count("release_assessments", {"task_id": task["id"]}) == 2


def test_complete_delivery_rollback_rework_http(application):
    client, factory = application
    tokens, pid, iid = setup_project(client)
    task = create_task(client, tokens, pid, iid)
    transition(client, tokens["manager"], pid, task, 1, expect=403)
    task = transition(client, tokens["developer"], pid, task, 1)
    task = transition(
        client,
        tokens["developer"],
        pid,
        task,
        2,
        reason="Waiting",
        responsibility_stage=5,
        evidence=EVIDENCE,
    )
    assert task["blocked_from_state"] == 2
    task = transition(
        client, tokens["developer"], pid, task, 3, basis="Dependency available", evidence=EVIDENCE
    )
    task = transition(
        client, tokens["developer"], pid, task, 4, artifact_revision="a" * 40, evidence=EVIDENCE
    )
    result = request(
        client,
        "createTaskReview",
        token=tokens["reviewer"],
        project_id=pid,
        task_id=task["id"],
        body=review_payload(task),
        expect=201,
    ).json()["data"]
    task, review = result["task"], result["review"]
    task = transition(
        client, tokens["reviewer"], pid, task, 5, review_id=review["id"], review_version=1
    )
    result = request(
        client,
        "createReleaseAssessment",
        token=tokens["manager"],
        project_id=pid,
        task_id=task["id"],
        body=assessment_payload(task),
        expect=201,
    ).json()["data"]
    task, assessment = result["task"], result["assessment"]
    request(
        client,
        "reviewReleaseAssessment",
        token=tokens["manager"],
        project_id=pid,
        task_id=task["id"],
        assessment_id=assessment["id"],
        body={
            "expected_version": task["version"],
            "expected_assessment_version": 1,
            "verdict": 1,
            "reason": "Self review forbidden",
            "evidence": EVIDENCE,
        },
        expect=403,
    )
    result = request(
        client,
        "reviewReleaseAssessment",
        token=tokens["reviewer"],
        project_id=pid,
        task_id=task["id"],
        assessment_id=assessment["id"],
        body={
            "expected_version": task["version"],
            "expected_assessment_version": 1,
            "verdict": 1,
            "reason": "Independent synthetic review",
            "evidence": EVIDENCE,
        },
        expect=200,
    ).json()["data"]
    task, assessment = result["task"], result["assessment"]
    task = transition(
        client,
        tokens["manager"],
        pid,
        task,
        7,
        assessment_id=assessment["id"],
        assessment_version=assessment["version"],
        release_version="v1",
        reason="Release",
        evidence=EVIDENCE,
    )
    assert task["state"] == 6
    task = transition(
        client,
        tokens["manager"],
        pid,
        task,
        8,
        assessment_id=assessment["id"],
        rollback_plan_version=1,
        target_version="v0",
        reason="Rollback",
        impact="Outage",
        evidence=EVIDENCE,
    )
    task = transition(
        client, tokens["manager"], pid, task, 9, new_plan=PLAN, reason="Rework", evidence=EVIDENCE
    )
    assert (
        task["state"],
        task["delivery_cycle"],
        task["review_cycle"],
        task["schedule_version"],
    ) == (2, 2, 1, 2)
    assert task["approved_review_id"] is None
    with factory() as uow:
        assert uow.gateway.count("decisions", {"task_id": task["id"]}) == 3
        assert uow.gateway.count("schedule_changes", {"task_id": task["id"]}) == 1
    audit = request(
        client,
        "listProjectAuditEvents",
        token=tokens["manager"],
        project_id=pid,
        query={"task_id": task["id"], "page_size": 100},
        expect=200,
    ).json()["data"]["items"]
    rework = next(
        a
        for a in audit
        if any(v == {"field": "version", "value": str(task["version"])} for v in a["after"])
    )
    assert {v["field"]: v["value"] for v in rework["after"]}["delay_contingency"] == PLAN[
        "delay_contingency"
    ]


def test_idempotency_versions_revocation_and_independent_rejection(application):
    client, factory = application
    tokens, pid, iid = setup_project(client)
    task = create_task(client, tokens, pid, iid)
    body = {"expected_version": task["version"], "action": 1}
    first = request(
        client,
        "transitionTask",
        token=tokens["developer"],
        project_id=pid,
        task_id=task["id"],
        body=body,
        key="stable-retry-key-0001",
        expect=200,
    )
    replay = request(
        client,
        "transitionTask",
        token=tokens["developer"],
        project_id=pid,
        task_id=task["id"],
        body=body,
        key="stable-retry-key-0001",
        expect=200,
    )
    assert replay.json()["data"] == first.json()["data"]
    assert replay.json()["meta"]["original_request_id"] == first.json()["meta"]["request_id"]
    assert replay.json()["meta"]["replayed"] is True
    request(
        client,
        "transitionTask",
        token=tokens["developer"],
        project_id=pid,
        task_id=task["id"],
        body={**body, "action": 4, "artifact_revision": "a" * 40, "evidence": EVIDENCE},
        key="stable-retry-key-0001",
        expect=409,
    )
    failure = request(
        client,
        "transitionTask",
        token=tokens["developer"],
        project_id=pid,
        task_id=task["id"],
        body=body,
        key="stale-version-key-0001",
        expect=409,
    )
    assert failure.json()["code"] == "VERSION_CONFLICT"
    again = request(
        client,
        "transitionTask",
        token=tokens["developer"],
        project_id=pid,
        task_id=task["id"],
        body=body,
        key="stale-version-key-0001",
        expect=409,
    )
    assert again.json()["audit_id"] == failure.json()["audit_id"]
    assert again.headers["idempotency-replayed"] == "true"
    request(client, "logout", token=tokens["developer"], expect=200)
    request(
        client,
        "transitionTask",
        token=tokens["developer"],
        project_id=pid,
        task_id=task["id"],
        body=body,
        key="stable-retry-key-0001",
        expect=401,
    )
    with factory() as uow:
        assert uow.gateway.get("tasks", task["id"])["version"] == task["version"] + 1
        assert uow.gateway.get("audit_events", failure.json()["audit_id"])["outcome"] == 2


@pytest.mark.parametrize("value", ["1", True, 1.5, None])
def test_strict_integer_request_rejects_coercion(application, value):
    client, _ = application
    tokens, pid, iid = setup_project(client)
    response = request(
        client,
        "createTask",
        token=tokens["manager"],
        project_id=pid,
        body={
            "title": "Strict input",
            "owner_id": value,
            "iteration_id": iid,
            "plan": PLAN,
            "dependency_task_ids": [],
        },
        expect=422,
    )
    assert response.json()["code"] == "PARAMETER_INVALID"
    assert "test-only-password" not in response.text


@pytest.mark.parametrize(
    "stamp,valid",
    [
        ("0001-01-01T00:00:00Z", False),
        ("0999-01-01T00:00:00Z", False),
        ("1000-01-01T00:00:00Z", True),
        ("9999-01-01T00:00:00Z", True),
        ("2026-02-30T00:00:00Z", False),
        ("2026-01-01T00:00:00.1234567Z", False),
        ("2026-01-01T00:00:00+00:00", False),
    ],
)
def test_utc_domain_readonly_and_mutation_match(application, stamp, valid):
    client, _ = application
    tokens, pid, iid = setup_project(client)
    payload = {
        "title": "Time boundary",
        "owner_id": 2,
        "iteration_id": iid,
        "plan": {**PLAN, "planned_start": stamp, "planned_end": "9999-12-31T23:59:59.999999Z"},
        "dependency_task_ids": [],
    }
    request(
        client,
        "validateContractPayload",
        token=tokens["manager"],
        project_id=pid,
        body={"category": 1, "payload": payload},
        expect=200 if valid else 422,
    )
    request(
        client,
        "createTask",
        token=tokens["manager"],
        project_id=pid,
        body=payload,
        expect=201 if valid else 422,
    )


def test_dependencies_cycle_guard_and_edit_lock(application):
    client, _ = application
    tokens, pid, iid = setup_project(client)
    predecessor = create_task(client, tokens, pid, iid)
    dependent = create_task(client, tokens, pid, iid, [predecessor["id"]])
    response = request(
        client,
        "addTaskDependency",
        token=tokens["manager"],
        project_id=pid,
        task_id=predecessor["id"],
        body={"expected_version": 1, "depends_on_task_id": dependent["id"], "reason": "Cycle"},
        expect=409,
    )
    assert response.json()["code"] == "DEPENDENCY_CYCLE"
    response = transition(client, tokens["developer"], pid, dependent, 1, expect=409)
    assert response.json()["code"] == "DEPENDENCIES_UNSATISFIED"
    predecessor = transition(client, tokens["developer"], pid, predecessor, 1)
    response = request(
        client,
        "addTaskDependency",
        token=tokens["manager"],
        project_id=pid,
        task_id=predecessor["id"],
        body={
            "expected_version": predecessor["version"],
            "depends_on_task_id": dependent["id"],
            "reason": "Too late",
        },
        expect=409,
    )
    assert response.json()["code"] == "DEPENDENCY_EDIT_LOCKED"


def test_auth_precedes_body_and_project_scope(application):
    client, _ = application
    request(client, "createProject", body={"invalid": "not relevant before auth"}, expect=401)
    tokens, pid, _ = setup_project(client)
    response = request(
        client, "createTask", token=tokens["outsider"], project_id=pid, body={}, expect=403
    )
    assert response.json()["code"] == "PROJECT_ACCESS_DENIED"
    request(client, "getDictionaries", token=tokens["manager"], expect=200)
    request(client, "getMe", token=tokens["manager"], expect=200)
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "manager", "password": "wrong", "secret": "dont-echo"},
    )
    assert response.status_code == 422
    assert "wrong" not in response.text and "dont-echo" not in response.text


def test_crud_queries_members_capacity_and_task_filters(application):
    client, _ = application
    tokens, pid, iid = setup_project(client)
    task = create_task(client, tokens, pid, iid)
    for operation, paths in [
        ("listProjects", {}),
        ("getProject", {"project_id": pid}),
        ("listProjectMembers", {"project_id": pid}),
        ("listIterations", {"project_id": pid}),
        ("listTasks", {"project_id": pid}),
        ("getTask", {"project_id": pid, "task_id": task["id"]}),
        ("getReviewTemplate", {"project_id": pid}),
        ("listTaskDependencies", {"project_id": pid, "task_id": task["id"]}),
        ("listTaskReviews", {"project_id": pid, "task_id": task["id"]}),
        ("listReleaseAssessments", {"project_id": pid, "task_id": task["id"]}),
        ("listTaskDecisions", {"project_id": pid, "task_id": task["id"]}),
        ("listProjectAuditEvents", {"project_id": pid}),
    ]:
        request(client, operation, token=tokens["manager"], expect=200, **paths)
    response = client.get(
        f"/api/v1/projects/{pid}/tasks?state=1&page=1&page_size=1&sort=planned_end",
        headers={"Authorization": f"Bearer {tokens['manager']}"},
    )
    assert response.status_code == 200 and response.json()["data"]["total"] == 1
    members = request(
        client, "listProjectMembers", token=tokens["manager"], project_id=pid, expect=200
    ).json()["data"]["items"]
    developer = next(m for m in members if m["user"]["id"] == 2)
    response = request(
        client,
        "removeProjectMember",
        token=tokens["manager"],
        project_id=pid,
        user_id=2,
        body={"expected_version": developer["version"], "reason": "Active owner"},
        expect=409,
    )
    assert response.json()["code"] == "MEMBER_IN_USE"
    request(
        client,
        "changeProjectMember",
        token=tokens["manager"],
        project_id=pid,
        user_id=2,
        body={
            "expected_version": developer["version"],
            "roles": [2, 3],
            "reason": "Add review role",
        },
        expect=200,
    )
    iteration = request(
        client, "listIterations", token=tokens["manager"], project_id=pid, expect=200
    ).json()["data"]["items"][0]
    changed = request(
        client,
        "changeIteration",
        token=tokens["manager"],
        project_id=pid,
        iteration_id=iid,
        body={
            "expected_version": iteration["version"],
            "plan": iteration["plan"],
            "reason": "New iteration baseline",
            "evidence": EVIDENCE,
        },
        expect=200,
    )
    assert changed.json()["data"]["plan_version"] == 2
    response = request(
        client,
        "changeTaskAssignment",
        token=tokens["manager"],
        project_id=pid,
        task_id=task["id"],
        body={
            "expected_version": task["version"],
            "owner_id": 2,
            "reason": "Confirm owner",
            "evidence": EVIDENCE,
        },
        expect=200,
    )
    task = response.json()["data"]["task"]
    result = request(
        client,
        "changeTaskPlan",
        token=tokens["manager"],
        project_id=pid,
        task_id=task["id"],
        body={
            "expected_version": task["version"],
            "plan": PLAN,
            "reason": "Replan",
            "evidence": EVIDENCE,
        },
        expect=200,
    ).json()["data"]["task"]
    assert result["schedule_version"] == 2 and result["version"] == task["version"] + 1


def test_reject_review_new_cycle_and_release_replan_invalidation(application):
    client, _ = application
    tokens, pid, iid = setup_project(client)
    task = create_task(client, tokens, pid, iid)
    task = transition(client, tokens["developer"], pid, task, 1)
    task = transition(
        client, tokens["developer"], pid, task, 4, artifact_revision="a" * 40, evidence=EVIDENCE
    )
    result = request(
        client,
        "createTaskReview",
        token=tokens["reviewer"],
        project_id=pid,
        task_id=task["id"],
        body=review_payload(task, verdict=2),
        expect=201,
    ).json()["data"]
    task = transition(
        client,
        tokens["reviewer"],
        pid,
        result["task"],
        6,
        review_id=result["review"]["id"],
        review_version=1,
        reason="Changes required",
    )
    assert task["review_cycle"] == 2 and task["artifact_revision"] is None
    task = transition(
        client, tokens["developer"], pid, task, 4, artifact_revision="a" * 40, evidence=EVIDENCE
    )
    payload = review_payload(task)
    payload["checklist"][0]["judgment"] = 3
    request(
        client,
        "createTaskReview",
        token=tokens["reviewer"],
        project_id=pid,
        task_id=task["id"],
        body=payload,
        expect=422,
    )
    result = request(
        client,
        "createTaskReview",
        token=tokens["reviewer"],
        project_id=pid,
        task_id=task["id"],
        body=review_payload(task),
        expect=201,
    ).json()["data"]
    task = transition(
        client,
        tokens["reviewer"],
        pid,
        result["task"],
        5,
        review_id=result["review"]["id"],
        review_version=1,
    )
    result = request(
        client,
        "createReleaseAssessment",
        token=tokens["manager"],
        project_id=pid,
        task_id=task["id"],
        body=assessment_payload(task),
        expect=201,
    ).json()["data"]
    result = request(
        client,
        "reviewReleaseAssessment",
        token=tokens["reviewer"],
        project_id=pid,
        task_id=task["id"],
        assessment_id=result["assessment"]["id"],
        body={
            "expected_version": result["task"]["version"],
            "expected_assessment_version": 1,
            "verdict": 1,
            "reason": "Approved",
            "evidence": EVIDENCE,
        },
        expect=200,
    ).json()["data"]
    old_assessment = result["assessment"]
    task = request(
        client,
        "changeTaskPlan",
        token=tokens["manager"],
        project_id=pid,
        task_id=task["id"],
        body={
            "expected_version": result["task"]["version"],
            "plan": PLAN,
            "reason": "Release postponed",
            "evidence": EVIDENCE,
        },
        expect=200,
    ).json()["data"]["task"]
    assert task["state"] == 5 and task["approved_review_id"] == result["task"]["approved_review_id"]
    assert task["approved_assessment_id"] is None
    response = transition(
        client,
        tokens["manager"],
        pid,
        task,
        7,
        expect=409,
        assessment_id=old_assessment["id"],
        assessment_version=old_assessment["version"],
        release_version="v1",
        reason="Stale release approval",
        evidence=EVIDENCE,
    )
    assert response.json()["code"] in ("ASSESSMENT_BASELINE_MISMATCH", "RELEASE_APPROVAL_REQUIRED")


def test_integer_equivalence_normalizes_idempotency_hash(application):
    client, _ = application
    tokens, pid, iid = setup_project(client)
    payload = {
        "title": "Equivalent numbers",
        "owner_id": 2,
        "iteration_id": iid,
        "plan": PLAN,
        "dependency_task_ids": [],
    }
    first = request(
        client,
        "createTask",
        token=tokens["manager"],
        project_id=pid,
        body=payload,
        key="numeric-equivalence",
        expect=201,
    )
    payload["owner_id"] = 2.0
    replay = request(
        client,
        "createTask",
        token=tokens["manager"],
        project_id=pid,
        body=payload,
        key="numeric-equivalence",
        expect=201,
    )
    assert replay.json()["meta"]["replayed"] is True
    assert replay.json()["data"] == first.json()["data"]


def test_task_owner_must_be_in_selected_iteration_capacity(application):
    client, factory = application
    tokens, pid, _ = setup_project(client)
    request(
        client,
        "addProjectMember",
        token=tokens["manager"],
        project_id=pid,
        body={"username": "outsider", "roles": [2], "reason": "Second developer"},
        expect=201,
    )
    iteration = request(
        client,
        "createIteration",
        token=tokens["manager"],
        project_id=pid,
        body={
            "name": "Only another developer",
            **{k: v for k, v in PLAN.items() if k != "estimated_hours"},
            "capacity": [{"user_id": 4, "available_hours": 40}],
        },
        expect=201,
    ).json()["data"]
    response = request(
        client,
        "createTask",
        token=tokens["manager"],
        project_id=pid,
        body={
            "title": "Owner absent from iteration capacity",
            "owner_id": 2,
            "iteration_id": iteration["id"],
            "plan": PLAN,
            "dependency_task_ids": [],
        },
        expect=422,
    )
    assert response.json()["code"] == "CAPACITY_REFERENCE_INVALID"
    assert response.json()["audit_id"] is not None
    with factory() as uow:
        assert uow.gateway.count("tasks", {"project_id": pid}) == 0


@pytest.mark.parametrize(
    "operation",
    [
        "getTask",
        "listTaskDependencies",
        "listTaskReviews",
        "listReleaseAssessments",
        "listTaskDecisions",
    ],
)
@pytest.mark.parametrize("invalid", [0, 4294967296])
def test_invalid_task_selector_retains_parameter_rejection_audit(application, operation, invalid):
    client, factory = application
    tokens, pid, iid = setup_project(client)
    task = create_task(client, tokens, pid, iid)
    response = request(
        client,
        operation,
        token=tokens["manager"],
        project_id=pid,
        task_id=invalid,
        expect=422,
    )
    error = response.json()
    assert error["code"] == "PARAMETER_INVALID" and error["audit_id"] is not None
    with factory() as uow:
        row = uow.gateway.get("audit_events", error["audit_id"])
        assert row["task_id"] is None and row["request_id"] == error["request_id"]
        assert row["attempted_task_id"] == (0 if invalid == 0 else None)
    assert (
        request(
            client,
            "getTask",
            token=tokens["manager"],
            project_id=pid,
            task_id=task["id"],
            expect=200,
        ).json()["data"]
        == task
    )


def test_task_schedule_audit_exposes_complete_untruncated_plan(application):
    client, _ = application
    tokens, pid, iid = setup_project(client)
    task = create_task(client, tokens, pid, iid)
    for text in ("前" * 2000, "后" * 2000):
        before = task
        changed = request(
            client,
            "changeTaskPlan",
            token=tokens["manager"],
            project_id=pid,
            task_id=task["id"],
            body={
                "expected_version": task["version"],
                "plan": {**PLAN, "delay_contingency": text},
                "reason": "Synthetic complete schedule evidence",
                "evidence": EVIDENCE,
            },
            expect=200,
        ).json()["data"]
        task = changed["task"]
        audit = request(
            client,
            "listProjectAuditEvents",
            token=tokens["manager"],
            project_id=pid,
            query={"task_id": task["id"], "page_size": 100},
            expect=200,
        ).json()["data"]["items"]
        saved = next(a for a in audit if a["id"] == changed["audit_id"])
        for side, source in (("before", before), ("after", task)):
            values = {item["field"]: item["value"] for item in saved[side]}
            for key, value in source["plan"].items():
                assert values[key] == (value if isinstance(value, str) else str(value))
            assert values["version"] == str(source["version"])
            assert values["schedule_version"] == str(source["schedule_version"])
        assert saved["actor_id"] == 1 and saved["evidence"] == EVIDENCE


@pytest.mark.parametrize(
    "kind", ["block", "review", "risk", "rollback", "approval", "notification"]
)
def test_empty_required_evidence_keeps_frozen_business_error(application, kind):
    from t44.services.common import now

    client, factory = application
    tokens, pid, iid = setup_project(client)
    task = create_task(client, tokens, pid, iid)

    def rejected(operation, body, token="manager", **path):
        result = request(
            client,
            operation,
            token=tokens[token],
            project_id=pid,
            task_id=task["id"],
            body=body,
            expect=422,
            **path,
        ).json()
        assert result["code"] == "EVIDENCE_REQUIRED" and result["audit_id"] is not None

    if kind == "block":
        rejected(
            "transitionTask",
            {
                "expected_version": task["version"],
                "action": 2,
                "reason": "Waiting",
                "responsibility_stage": 5,
                "evidence": [],
            },
        )
        return
    if kind == "notification":
        with factory() as uow:
            event = uow.gateway.rows("outbox_events", {"task_id": task["id"]}, limit=1)[0]
            notification = uow.gateway.insert(
                "notifications",
                {
                    "project_id": pid,
                    "task_id": task["id"],
                    "event_id": event["id"],
                    "recipient_id": 1,
                    "level": 1,
                    "title": "Synthetic input-validation fixture",
                    "message": "Synthetic notification",
                    "fallback": 1,
                    "handling_evidence": [],
                    "created_at": now(),
                },
            )
        rejected(
            "handleNotification",
            {"expected_version": 1, "note": "Checked", "evidence": []},
            notification_id=notification,
        )
        with factory() as uow:
            assert uow.gateway.get("notifications", notification)["handled_at"] is None
        return
    task = transition(client, tokens["developer"], pid, task, 1)
    task = transition(
        client, tokens["developer"], pid, task, 4, artifact_revision="a" * 40, evidence=EVIDENCE
    )
    body = review_payload(task)
    if kind == "review":
        body["checklist"][0]["evidence"] = []
        rejected("createTaskReview", body, token="reviewer")
        return
    reviewed = request(
        client,
        "createTaskReview",
        token=tokens["reviewer"],
        project_id=pid,
        task_id=task["id"],
        body=body,
        expect=201,
    ).json()["data"]
    task = transition(
        client,
        tokens["reviewer"],
        pid,
        reviewed["task"],
        5,
        review_id=reviewed["review"]["id"],
        review_version=1,
    )
    body = assessment_payload(task)
    if kind in ("risk", "rollback"):
        (body["risks"][0] if kind == "risk" else body["rollback_plan"])["evidence"] = []
        rejected("createReleaseAssessment", body)
        return
    created = request(
        client,
        "createReleaseAssessment",
        token=tokens["manager"],
        project_id=pid,
        task_id=task["id"],
        body=body,
        expect=201,
    ).json()["data"]
    task = created["task"]
    rejected(
        "reviewReleaseAssessment",
        {
            "expected_version": task["version"],
            "expected_assessment_version": 1,
            "verdict": 1,
            "reason": "Checked",
            "evidence": [],
        },
        token="reviewer",
        assessment_id=created["assessment"]["id"],
    )


@pytest.mark.parametrize(
    "case,code",
    [
        ("outer-extra", "PARAMETER_INVALID"),
        ("outer-task", "PARAMETER_INVALID"),
        ("payload-extra", "CONTRACT_INVALID"),
        ("payload-evidence", "CONTRACT_INVALID"),
    ],
)
def test_contract_validation_outer_shape_is_distinct_from_candidate(application, case, code):
    client, _ = application
    tokens, pid, iid = setup_project(client)
    task = create_task(client, tokens, pid, iid)
    body = {
        "category": 2,
        "task_id": task["id"],
        "payload": {
            "expected_version": 1,
            "action": 2,
            "reason": "Waiting",
            "responsibility_stage": 5,
            "evidence": EVIDENCE,
        },
    }
    if case == "outer-extra":
        body["client_actor_id"] = 1
    elif case == "outer-task":
        body["task_id"] = 0
    elif case == "payload-extra":
        body["payload"]["client_actor_id"] = 1
    else:
        body["payload"]["evidence"] = []
    response = request(
        client,
        "validateContractPayload",
        token=tokens["manager"],
        project_id=pid,
        body=body,
        expect=422,
    ).json()
    assert response["code"] == code and response["audit_id"] is not None


def test_transition_union_stays_strict_and_normalizes_equivalent_integers(application):
    client, _ = application
    tokens, pid, iid = setup_project(client)
    task = create_task(client, tokens, pid, iid)
    for action in (True, "1", 999):
        error = request(
            client,
            "transitionTask",
            token=tokens["developer"],
            project_id=pid,
            task_id=task["id"],
            body={"expected_version": 1, "action": action},
            expect=422,
        ).json()
        assert error["code"] == "PARAMETER_INVALID" and error["audit_id"] is not None
    key = str(uuid4())
    first = request(
        client,
        "transitionTask",
        token=tokens["developer"],
        project_id=pid,
        task_id=task["id"],
        body={"expected_version": 1.0, "action": 1.0},
        key=key,
        expect=200,
    ).json()["data"]
    replay = request(
        client,
        "transitionTask",
        token=tokens["developer"],
        project_id=pid,
        task_id=task["id"],
        body={"expected_version": 1, "action": 1},
        key=key,
        expect=200,
    ).json()
    assert replay["meta"]["replayed"] is True and replay["data"] == first


def test_dependency_remove_and_last_manager_guard(application):
    client, _ = application
    token = login(client)
    pid = request(
        client, "createProject", token=token, body={"name": "Single manager"}, expect=201
    ).json()["data"]["id"]
    response = request(
        client,
        "removeProjectMember",
        token=token,
        project_id=pid,
        user_id=1,
        body={"expected_version": 1, "reason": "Cannot orphan project"},
        expect=409,
    )
    assert response.json()["code"] == "LAST_MANAGER"
    tokens, pid, iid = setup_project(client)
    first = create_task(client, tokens, pid, iid)
    second = create_task(client, tokens, pid, iid)
    result = request(
        client,
        "addTaskDependency",
        token=tokens["manager"],
        project_id=pid,
        task_id=second["id"],
        body={
            "expected_version": 1,
            "depends_on_task_id": first["id"],
            "reason": "Before implementation",
        },
        expect=201,
    ).json()["data"]
    request(
        client,
        "removeTaskDependency",
        token=tokens["manager"],
        project_id=pid,
        task_id=second["id"],
        dependency_id=result["dependency"]["id"],
        body={
            "expected_version": result["task"]["version"],
            "reason": "Scope changed before development",
        },
        expect=200,
    )


@pytest.mark.parametrize(
    "body,status,code",
    [
        ({"name": "A normal 'quote' title"}, 201, None),
        ({"name": "NUL\x00inside"}, 400, "SECURITY_INPUT_REJECTED"),
        ({"name": "extra", "version": 1}, 422, "PARAMETER_INVALID"),
    ],
)
def test_security_boundary_keeps_legitimate_quotes(application, body, status, code):
    client, _ = application
    token = login(client)
    response = request(client, "createProject", token=token, body=body, expect=status)
    if code:
        assert response.json()["code"] == code


def test_internal_escalation_rejects_human_before_missing_owner(application):
    client, _ = application
    tokens, pid, iid = setup_project(client)
    task = create_task(client, tokens, pid, iid)
    result = request(
        client,
        "createEscalation",
        token=tokens["manager"],
        project_id=pid,
        task_id=task["id"],
        body={
            "expected_version": 1,
            "schedule_version": 1,
            "rule_version": 1,
            "scan_run_id": str(uuid4()),
        },
        expect=403,
    )
    assert result.json()["code"] == "SERVICE_SCOPE_REQUIRED"


def test_display_order_never_changes_persisted_audit_or_domain_state(application, monkeypatch):
    import importlib
    import re
    from pathlib import Path

    from t44.domain.models import ProjectRole, ResponsibilityStage, TaskState
    from t44.services import codes
    from t44.services.common import SCHEMAS

    client, factory = application
    tokens, pid, iid = setup_project(client)
    task = create_task(client, tokens, pid, iid)
    expected = {
        name: int(number)
        for number, name in re.findall(
            r"\| (\d+) \| ([A-Z_]+) \|",
            (Path(__file__).parents[3] / "specs/database/field-dictionary.md").read_text(),
        )
    }
    monkeypatch.setitem(SCHEMAS["ErrorCode"], "enum", list(reversed(SCHEMAS["ErrorCode"]["enum"])))
    for enum in (TaskState, ProjectRole, ResponsibilityStage):
        monkeypatch.setattr(enum, "_member_names_", list(reversed(enum._member_names_)))
    importlib.reload(codes)
    assert expected == codes.ERROR_IDS
    assert {value: key for key, value in expected.items()} == codes.ERROR_CODES
    rejected = transition(client, tokens["manager"], pid, task, 1, expect=403)
    with factory() as uow:
        assert uow.gateway.get("audit_events", rejected.json()["audit_id"])["reason_code"] == 6
    audit = request(
        client, "listProjectAuditEvents", token=tokens["manager"], project_id=pid, expect=200
    )
    assert any(row["reason_code"] == "ACTION_FORBIDDEN" for row in audit.json()["data"]["items"])
    task = transition(client, tokens["developer"], pid, task, 1)
    assert task["state"] == 2


@pytest.mark.parametrize(
    "content,content_type,status,code",
    [
        ('{"name":NaN}', "application/json", 400, "INVALID_JSON"),
        ('{"name":"a","name":"b"}', "application/json", 400, "INVALID_JSON"),
        ('{"name":"a"}', "text/plain", 400, "INVALID_JSON"),
        ('{"name":"' + "a" * 1048576 + '"}', "application/json", 413, "PAYLOAD_TOO_LARGE"),
    ],
)
def test_raw_http_json_and_size_errors_are_audited(
    application, content, content_type, status, code
):
    client, factory = application
    token = login(client)
    result = client.post(
        "/api/v1/projects",
        content=content,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": content_type,
            "Idempotency-Key": str(uuid4()),
        },
    )
    assert result.status_code == status
    assert result.json()["code"] == code
    assert not violations(
        OPERATIONS["createProject"]["responses"][str(status)]["content"]["application/json"][
            "schema"
        ],
        result.json(),
    )
    with factory() as uow:
        assert uow.gateway.get("audit_events", result.json()["audit_id"])["outcome"] == 2
        assert uow.gateway.count("projects") == 0


def test_query_selectors_and_project_reference_errors(application):
    client, _ = application
    tokens, pid, iid = setup_project(client)
    task = create_task(client, tokens, pid, iid)
    headers = {"Authorization": f"Bearer {tokens['manager']}"}
    for query, status, code in [
        ("page=true", 422, "PARAMETER_INVALID"),
        ("page=1&page=2", 422, "PARAMETER_INVALID"),
        ("unrecognized=1", 422, "PARAMETER_INVALID"),
        ("sort=%27%20OR%201%3D1--", 400, "SECURITY_INPUT_REJECTED"),
    ]:
        result = client.get(f"/api/v1/projects/{pid}/tasks?{query}", headers=headers)
        assert result.status_code == status
        assert result.json()["code"] == code
    request(
        client, "getTask", token=tokens["manager"], project_id=pid, task_id=4294967295, expect=404
    )
    result = request(
        client,
        "changeTaskAssignment",
        token=tokens["manager"],
        project_id=pid,
        task_id=task["id"],
        body={
            "expected_version": 1,
            "owner_id": 1,
            "reason": "Manager lacks developer",
            "evidence": EVIDENCE,
        },
        expect=422,
    )
    assert result.json()["code"] == "OWNER_NOT_PROJECT_DEVELOPER"
    result = request(
        client,
        "createIteration",
        token=tokens["manager"],
        project_id=pid,
        body={
            "name": "Bad capacity",
            **{k: v for k, v in PLAN.items() if k != "estimated_hours"},
            "capacity": [{"user_id": 1, "available_hours": 10}],
        },
        expect=422,
    )
    assert result.json()["code"] == "CAPACITY_REFERENCE_INVALID"
    result = request(
        client,
        "addTaskDependency",
        token=tokens["manager"],
        project_id=pid,
        task_id=task["id"],
        body={"expected_version": 1, "depends_on_task_id": task["id"], "reason": "Self edge"},
        expect=422,
    )
    assert result.json()["code"] == "DEPENDENCY_SELF_REFERENCE"


def test_sessions_and_login_throttling(application):
    from datetime import timedelta

    from t44.services.common import now
    from t44.services.identity import token_digest

    client, factory = application
    first, second = login(client), login(client)
    request(client, "logout", token=first, expect=200)
    request(client, "getMe", token=first, expect=401)
    request(client, "getMe", token=second, expect=200)
    with factory() as uow:
        uow.gateway.update(
            "auth_sessions",
            {"token_hash": token_digest(second)},
            {"expires_at": now() - timedelta(seconds=1)},
        )
    result = request(client, "getMe", token=second, expect=401)
    assert result.json()["code"] == "TOKEN_EXPIRED"
    client.app.state.runtime.limiter.attempts = 1
    request(client, "login", body={"username": "manager", "password": "wrong-password"}, expect=429)
    request(
        client,
        "login",
        body={"username": "unknown-login", "password": "wrong-password"},
        expect=401,
    )
    result = request(
        client,
        "login",
        body={"username": "unknown-login", "password": "wrong-password"},
        expect=429,
    )
    assert result.headers["retry-after"] == "60"


def capacity_change(client, token, pid, iteration, owners, *, expect=200, key=None):
    return request(
        client,
        "changeIteration",
        token=token,
        project_id=pid,
        iteration_id=iteration["id"],
        key=key,
        body={
            "expected_version": iteration["version"],
            "plan": {
                **iteration["plan"],
                "capacity": [
                    {"user_id": identifier, "available_hours": 40} for identifier in owners
                ],
            },
            "reason": "Synthetic capacity lifecycle",
            "evidence": EVIDENCE,
        },
        expect=expect,
    )


def capacity_team(client, tokens, pid):
    request(
        client,
        "addProjectMember",
        token=tokens["manager"],
        project_id=pid,
        body={"username": "outsider", "roles": [2], "reason": "Synthetic replacement developer"},
        expect=201,
    )
    return request(
        client, "listIterations", token=tokens["manager"], project_id=pid, expect=200
    ).json()["data"]["items"][0]


@pytest.mark.parametrize("blocked", [False, True])
def test_capacity_v11_assignment_requires_registration_then_safe_old_owner_removal(
    application, blocked
):
    client, factory = application
    tokens, pid, iid = setup_project(client)
    task = create_task(client, tokens, pid, iid)
    iteration = capacity_team(client, tokens, pid)
    if blocked:
        task = transition(
            client,
            tokens["manager"],
            pid,
            task,
            2,
            reason="Intake blocked",
            responsibility_stage=1,
            evidence=EVIDENCE,
        )
    key = str(uuid4())
    body = {
        "expected_version": task["version"],
        "owner_id": 4,
        "reason": "Synthetic handover",
        "evidence": EVIDENCE,
    }
    rejected = request(
        client,
        "changeTaskAssignment",
        token=tokens["manager"],
        project_id=pid,
        task_id=task["id"],
        body=body,
        key=key,
        expect=422,
    )
    assert rejected.json()["code"] == "CAPACITY_REFERENCE_INVALID"
    assert rejected.json()["audit_id"] is not None
    with factory() as uow:
        stored = uow.gateway.get("tasks", task["id"])
        assert (stored["owner_id"], stored["version"]) == (2, task["version"])
        audit = uow.gateway.get("audit_events", rejected.json()["audit_id"])
        assert audit["reason_code"] == 30
    iteration = capacity_change(client, tokens["manager"], pid, iteration, [2, 4]).json()["data"]
    replay = request(
        client,
        "changeTaskAssignment",
        token=tokens["manager"],
        project_id=pid,
        task_id=task["id"],
        body=body,
        key=key,
        expect=422,
    )
    assert replay.headers["idempotency-replayed"] == "true"
    assert replay.json()["audit_id"] == rejected.json()["audit_id"]
    accepted_key = str(uuid4())
    accepted = request(
        client,
        "changeTaskAssignment",
        token=tokens["manager"],
        project_id=pid,
        task_id=task["id"],
        body=body,
        key=accepted_key,
        expect=200,
    )
    changed = accepted.json()["data"]["task"]
    assert (changed["owner_id"], changed["version"]) == (4, task["version"] + 1)
    removed = capacity_change(client, tokens["manager"], pid, iteration, [4]).json()["data"]
    assert removed["plan"]["capacity"] == [{"user_id": 4, "available_hours": 40}]
    replay = request(
        client,
        "changeTaskAssignment",
        token=tokens["manager"],
        project_id=pid,
        task_id=task["id"],
        body=body,
        key=accepted_key,
        expect=200,
    )
    assert replay.json()["data"] == accepted.json()["data"]
    assert replay.json()["meta"]["replayed"] is True


@pytest.mark.parametrize("state", range(1, 8))
def test_capacity_v11_iteration_protects_active_owners_but_releases_terminal_capacity(
    application, state
):
    client, factory = application
    tokens, pid, iid = setup_project(client)
    task = create_task(client, tokens, pid, iid)
    iteration = capacity_team(client, tokens, pid)
    # Explicit synthetic state fixture isolates the capacity guard, not a workflow journey.
    with factory() as uow:
        uow.gateway.update(
            "tasks",
            {"id": task["id"]},
            {
                "state": state,
                "blocked_from_state": 2 if state == 3 else None,
                "block_reason": "Synthetic block" if state == 3 else None,
                "responsibility_stage": 2 if state == 3 else None,
            },
        )
        before = {
            table: uow.gateway.count(table, {"project_id": pid})
            for table in ("schedule_changes", "outbox_events")
        }
    response = capacity_change(
        client,
        tokens["manager"],
        pid,
        iteration,
        [4],
        expect=422 if state <= 5 else 200,
    )
    if state <= 5:
        assert response.json()["code"] == "CAPACITY_REFERENCE_INVALID"
        assert response.json()["audit_id"] is not None
        with factory() as uow:
            saved = uow.gateway.get("iterations", iid)
            assert (saved["version"], saved["plan_version"], saved["capacity"]) == (
                iteration["version"],
                iteration["plan_version"],
                iteration["plan"]["capacity"],
            )
            assert before == {
                table: uow.gateway.count(table, {"project_id": pid}) for table in before
            }
    else:
        assert response.json()["data"]["version"] == iteration["version"] + 1
    if state == 7:
        member = request(
            client, "listProjectMembers", token=tokens["manager"], project_id=pid, expect=200
        ).json()["data"]["items"]
        owner = next(m for m in member if m["user"]["id"] == 2)
        protected = request(
            client,
            "removeProjectMember",
            token=tokens["manager"],
            project_id=pid,
            user_id=2,
            body={"expected_version": owner["version"], "reason": "Still rolled back"},
            expect=409,
        )
        assert protected.json()["code"] == "MEMBER_IN_USE"


def test_capacity_v11_iteration_checks_all_owners_not_only_removed_entries(application):
    client, factory = application
    tokens, pid, iid = setup_project(client)
    create_task(client, tokens, pid, iid)
    iteration = capacity_team(client, tokens, pid)
    # Model an old inconsistent baseline: the proposed list removes nobody.
    with factory() as uow:
        uow.gateway.update(
            "iterations", {"id": iid}, {"capacity": [{"user_id": 4, "available_hours": 40}]}
        )
    iteration["plan"]["capacity"] = [{"user_id": 4, "available_hours": 40}]
    result = capacity_change(client, tokens["manager"], pid, iteration, [4], expect=422)
    assert result.json()["code"] == "CAPACITY_REFERENCE_INVALID"


@pytest.mark.parametrize("missing", ["capacity", "inactive", "developer_role"])
def test_capacity_v11_rework_requires_current_effective_owner_and_capacity(application, missing):
    client, factory = application
    tokens, pid, iid = setup_project(client)
    task = create_task(client, tokens, pid, iid)
    iteration = capacity_team(client, tokens, pid)
    with factory() as uow:
        uow.gateway.update("tasks", {"id": task["id"]}, {"state": 7})
        member = uow.gateway.rows("project_members", {"project_id": pid, "user_id": 2})[0]
    task["state"] = 7
    if missing == "capacity":
        iteration = capacity_change(client, tokens["manager"], pid, iteration, [4]).json()["data"]
    else:
        with factory() as uow:
            uow.gateway.update(
                "project_members",
                {"id": member["id"]},
                {"active": 0} if missing == "inactive" else {"roles_mask": 4},
            )
    with factory() as uow:
        before = {
            table: uow.gateway.count(table, {"project_id": pid})
            for table in ("decisions", "schedule_changes", "outbox_events")
        }
    result = transition(
        client,
        tokens["manager"],
        pid,
        task,
        9,
        expect=422,
        new_plan=PLAN,
        reason="Synthetic reactivation",
        evidence=EVIDENCE,
    )
    assert result.json()["code"] == "CAPACITY_REFERENCE_INVALID"
    with factory() as uow:
        saved = uow.gateway.get("tasks", task["id"])
        assert (
            saved["state"],
            saved["version"],
            saved["delivery_cycle"],
            saved["schedule_version"],
        ) == (7, 1, 1, 1)
        assert before == {table: uow.gateway.count(table, {"project_id": pid}) for table in before}
        uow.gateway.update("project_members", {"id": member["id"]}, {"active": 1, "roles_mask": 2})
    iteration = capacity_change(client, tokens["manager"], pid, iteration, [2, 4]).json()["data"]
    changed = transition(
        client,
        tokens["manager"],
        pid,
        task,
        9,
        new_plan=PLAN,
        reason="Synthetic reactivation",
        evidence=EVIDENCE,
    )
    assert (changed["state"], changed["delivery_cycle"], changed["schedule_version"]) == (2, 2, 2)


@pytest.mark.parametrize(
    "case,code,status",
    [
        ("assignment_role", "ACTION_FORBIDDEN", 403),
        ("assignment_version", "VERSION_CONFLICT", 409),
        ("assignment_state", "ASSIGNMENT_EDIT_LOCKED", 409),
        ("iteration_version", "VERSION_CONFLICT", 409),
        ("rework_role", "ACTION_FORBIDDEN", 403),
        ("rework_version", "VERSION_CONFLICT", 409),
        ("rework_version_ceiling", "VERSION_CONFLICT", 409),
        ("rework_state", "STATE_CONFLICT", 409),
        ("rework_dependency", "DEPENDENCIES_UNSATISFIED", 409),
    ],
)
def test_capacity_v11_keeps_original_guard_precedence(application, case, code, status):
    client, factory = application
    tokens, pid, iid = setup_project(client)
    predecessor = create_task(client, tokens, pid, iid) if case == "rework_dependency" else None
    task = create_task(client, tokens, pid, iid, [predecessor["id"]] if predecessor else [])
    iteration = capacity_team(client, tokens, pid)
    with factory() as uow:
        if case.startswith("rework"):
            uow.gateway.update(
                "tasks", {"id": task["id"]}, {"state": 1 if case == "rework_state" else 7}
            )
            uow.gateway.update(
                "iterations", {"id": iid}, {"capacity": [{"user_id": 4, "available_hours": 40}]}
            )
        if case == "assignment_state":
            uow.gateway.update("tasks", {"id": task["id"]}, {"state": 2})
        if case.endswith("version") or case == "rework_version_ceiling":
            uow.gateway.update(
                "iterations" if case == "iteration_version" else "tasks",
                {"id": iid if case == "iteration_version" else task["id"]},
                {"version": 2147483647 if case == "rework_version_ceiling" else 2},
            )
        if case == "rework_version_ceiling":
            task["version"] = 2147483647
    if case == "iteration_version":
        response = capacity_change(client, tokens["manager"], pid, iteration, [4], expect=status)
    else:
        body = {
            "expected_version": task["version"],
            "reason": "Synthetic precedence",
            "evidence": EVIDENCE,
        }
        body.update(
            {"owner_id": 4} if case.startswith("assignment") else {"action": 9, "new_plan": PLAN}
        )
        response = request(
            client,
            "changeTaskAssignment" if case.startswith("assignment") else "transitionTask",
            token=tokens["developer"] if case.endswith("role") else tokens["manager"],
            project_id=pid,
            task_id=task["id"],
            body=body,
            expect=status,
        )
    assert response.json()["code"] == code and response.json()["audit_id"] is not None


@pytest.mark.parametrize("category", [1, 2, 3])
def test_contract_validation_keeps_candidate_schema_version_separate_from_envelope(
    application, category
):
    client, factory = application
    tokens, pid, iid = setup_project(client)
    task = create_task(client, tokens, pid, iid)
    candidates = {
        1: {
            "title": "Synthetic readonly registration",
            "owner_id": 2,
            "iteration_id": iid,
            "plan": PLAN,
            "dependency_task_ids": [],
        },
        2: {"expected_version": task["version"], "action": 1},
        3: assessment_payload(task),
    }
    with factory() as uow:
        before = {
            table: uow.gateway.count(table)
            for table in ("tasks", "audit_events", "outbox_events", "idempotency_requests")
        }
    response = request(
        client,
        "validateContractPayload",
        token=tokens["manager"],
        project_id=pid,
        body={
            "category": category,
            "payload": candidates[category],
            **({"task_id": task["id"]} if category != 1 else {}),
        },
        expect=200,
    )
    result = response.json()
    assert result["data"]["valid"] is True
    assert result["data"]["business_guards_executed"] is False
    assert result["data"]["category"] == category
    assert (
        result["data"]["schema_version"]
        == SPEC["components"]["schemas"]["ContractValidationResult"]["properties"][
            "schema_version"
        ]["const"]
    )
    assert result["meta"]["contract_version"] == SPEC["info"]["version"]
    with factory() as uow:
        assert before == {table: uow.gateway.count(table) for table in before}
        assert uow.gateway.get("tasks", task["id"])["version"] == task["version"]


@pytest.mark.parametrize("identity", ["missing", "revoked", "expired", "nonmember", "service"])
def test_read_uow_auth_still_precedes_invalid_json(application, identity):
    from datetime import timedelta

    from t44.services.common import now
    from t44.services.identity import issue_session, token_digest

    client, factory = application
    tokens, pid, _ = setup_project(client)
    token = tokens["outsider"] if identity == "nonmember" else tokens["manager"]
    if identity == "missing":
        token = None
    elif identity in ("revoked", "expired", "service"):
        with factory() as uow:
            g, clock = uow.gateway, now()
            if identity == "service":
                service = g.insert(
                    "service_accounts", {"name": "readonly-test", "active": 1, "created_at": clock}
                )
                token = issue_session(
                    g,
                    clock=clock,
                    ttl=3600,
                    service_account_id=service,
                    project_ids=[pid],
                    scopes=["escalation:write"],
                )["access_token"]
            else:
                session = g.rows("auth_sessions", {"token_hash": token_digest(token)})[0]
                values = (
                    {"revoked_at": clock}
                    if identity == "revoked"
                    else {
                        "created_at": clock - timedelta(days=2),
                        "expires_at": clock - timedelta(days=1),
                    }
                )
                g.update("auth_sessions", {"id": session["id"]}, values)
    response = client.post(
        f"/api/v1/projects/{pid}/contract-validations",
        content="{",
        headers={
            "Content-Type": "application/json",
            **({"Authorization": f"Bearer {token}"} if token else {}),
        },
    )
    expected = {
        "missing": (401, "AUTH_REQUIRED"),
        "revoked": (401, "TOKEN_REVOKED"),
        "expired": (401, "TOKEN_EXPIRED"),
        "nonmember": (403, "PROJECT_ACCESS_DENIED"),
        "service": (403, "ACTION_FORBIDDEN"),
    }[identity]
    assert (response.status_code, response.json()["code"]) == expected
    with factory() as uow:
        audit = uow.gateway.get("audit_events", response.json()["audit_id"])
        assert audit["request_id"] == response.json()["request_id"] and audit["outcome"] == 2


@pytest.mark.parametrize("valid_body", [True, False])
def test_read_uow_fresh_expiry_check_preserves_parameter_error_priority(
    application, monkeypatch, valid_body
):
    from datetime import timedelta

    from t44 import api
    from t44.services import identity, runtime
    from t44.services.common import now
    from t44.services.identity import token_digest

    client, factory = application
    tokens, pid, iid = setup_project(client)
    clock = [now()]
    with factory() as uow:
        session = uow.gateway.rows(
            "auth_sessions", {"token_hash": token_digest(tokens["manager"])}
        )[0]
        expiry = clock[0] + timedelta(minutes=1)
        uow.gateway.update("auth_sessions", {"id": session["id"]}, {"expires_at": expiry})
    monkeypatch.setattr(identity, "now", lambda: clock[0])
    monkeypatch.setattr(runtime, "now", lambda: clock[0], raising=False)
    original = api.validate_request

    def advance_after_validation(*args):
        try:
            return original(*args)
        finally:
            clock[0] = expiry + timedelta(microseconds=1)

    monkeypatch.setattr(api, "validate_request", advance_after_validation)
    dispatched = []
    original_dispatch = client.app.state.runtime.business.dispatch

    def track_dispatch(g, c):
        dispatched.append(c.operation)
        return original_dispatch(g, c)

    monkeypatch.setattr(client.app.state.runtime.business, "dispatch", track_dispatch)
    response = request(
        client,
        "validateContractPayload",
        token=tokens["manager"],
        project_id=pid,
        body={
            "category": 1,
            "payload": {
                "title": "Expiry test",
                "owner_id": 2,
                "iteration_id": iid,
                "plan": PLAN,
                "dependency_task_ids": [],
            },
        }
        if valid_body
        else {},
        expect=401 if valid_body else 422,
    )
    assert response.json()["code"] == ("TOKEN_EXPIRED" if valid_body else "PARAMETER_INVALID")
    assert not dispatched
    with factory() as uow:
        assert uow.gateway.get("audit_events", response.json()["audit_id"])["outcome"] == 2


@pytest.mark.fault
@pytest.mark.parametrize("dependency_fault", [False, True])
@pytest.mark.parametrize("audit_available", [False, True])
def test_read_uow_closes_before_fresh_rejection_transaction(
    application, monkeypatch, dependency_fault, audit_available
):
    from t44.persistence import PersistenceUnavailable
    from t44.services.errors import Rejected

    client, factory = application
    tokens, pid, iid = setup_project(client)
    runtime = client.app.state.runtime
    events, sessions = [], []

    def tracked_factory():
        uow, index = factory(), len(sessions)

        class Scope:
            def __enter__(self):
                uow.__enter__()
                sessions.append(uow._session)
                events.append(("enter", index))
                return uow

            def __exit__(self, *args):
                try:
                    return uow.__exit__(*args)
                finally:
                    assert uow._state == "closed"
                    events.append(("closed", index))

        return Scope()

    def fail_dispatch(g, call):
        if dependency_fault:
            raise PersistenceUnavailable("Injected read dependency failure")
        raise Rejected("CONTRACT_INVALID")

    original_audit = runtime.audit

    def audit(g, call, error=None):
        if not audit_available:
            raise PersistenceUnavailable("Injected audit failure")
        return original_audit(g, call, error)

    monkeypatch.setattr(runtime, "factory", tracked_factory)
    monkeypatch.setattr(runtime.business, "dispatch", fail_dispatch)
    monkeypatch.setattr(runtime, "audit", audit)
    response = request(
        client,
        "validateContractPayload",
        token=tokens["manager"],
        project_id=pid,
        body={
            "category": 1,
            "payload": {
                "title": "Rejected read",
                "owner_id": 2,
                "iteration_id": iid,
                "plan": PLAN,
                "dependency_task_ids": [],
            },
        },
        expect=422 if audit_available and not dependency_fault else 503,
    )
    expected = "DEPENDENCY_UNAVAILABLE" if dependency_fault else "CONTRACT_INVALID"
    assert response.json()["code"] == (expected if audit_available else "AUDIT_UNAVAILABLE")
    assert events == [("enter", 0), ("closed", 0), ("enter", 1), ("closed", 1)]
    assert sessions[0] is not sessions[1]
    with factory() as uow:
        rows = uow.gateway.rows("audit_events", {"request_id": response.json()["request_id"]})
        assert len(rows) == int(audit_available)
        assert uow.gateway.count("tasks", {"project_id": pid}) == 0
    assert (response.json()["audit_id"] is not None) == audit_available


def _preflight_transactions(runtime, factory, monkeypatch, after_commit=None):
    """Observe actual UoW lifecycle; never replace storage, commit or business decisions."""
    records = []

    def tracked():
        uow = factory()
        record = {"commits": 0, "rollbacks": 0, "closed": False}
        commit, rollback = uow.commit, uow.rollback

        def committed():
            commit()
            record["commits"] += 1
            if after_commit:
                after_commit(record)

        def rolled_back():
            rollback()
            record["rollbacks"] += 1

        uow.commit, uow.rollback = committed, rolled_back

        class Scope:
            def __enter__(self):
                uow.__enter__()
                record["session"] = uow._session
                records.append(record)
                return uow

            def __exit__(self, *args):
                try:
                    return uow.__exit__(*args)
                finally:
                    record["closed"] = uow._state == "closed"

        return Scope()

    monkeypatch.setattr(runtime, "factory", tracked)
    return records


@pytest.mark.parametrize("valid_body", [True, False])
def test_preflight_write_expiry_still_follows_original_input_priority(
    application, monkeypatch, valid_body
):
    from datetime import timedelta

    from t44 import api
    from t44.services import identity
    from t44.services.common import now
    from t44.services.identity import token_digest

    client, factory = application
    token = login(client)
    clock = [now()]
    with factory() as uow:
        session = uow.gateway.rows("auth_sessions", {"token_hash": token_digest(token)})[0]
        expiry = clock[0] + timedelta(minutes=1)
        uow.gateway.update("auth_sessions", {"id": session["id"]}, {"expires_at": expiry})
    monkeypatch.setattr(identity, "now", lambda: clock[0])
    original = api.validate_request

    def advance(*args):
        try:
            return original(*args)
        finally:
            clock[0] = expiry + timedelta(microseconds=1)

    monkeypatch.setattr(api, "validate_request", advance)
    key = uuid4().hex
    response = request(
        client,
        "createProject",
        token=token,
        body={"name": "Expiry"} if valid_body else {},
        key=key,
        expect=401 if valid_body else 422,
    )
    assert response.json()["code"] == ("TOKEN_EXPIRED" if valid_body else "PARAMETER_INVALID")
    with factory() as uow:
        assert uow.gateway.count("idempotency_requests", {"idempotency_key": key}) == 0
        assert uow.gateway.get("audit_events", response.json()["audit_id"])["outcome"] == 2


@pytest.mark.fault
@pytest.mark.parametrize("dependency_fault", [False, True])
@pytest.mark.parametrize("audit_available", [False, True])
def test_preflight_input_failure_exits_with_rollback_before_independent_audit(
    application, monkeypatch, dependency_fault, audit_available
):
    from t44 import api
    from t44.persistence import PersistenceUnavailable
    from t44.services.errors import Rejected

    client, factory = application
    token = login(client)
    runtime = client.app.state.runtime
    records = _preflight_transactions(runtime, factory, monkeypatch)
    original_audit = runtime.audit

    def fail_input(*_):
        if dependency_fault:
            raise PersistenceUnavailable("Injected synchronous input dependency failure")
        raise Rejected("PARAMETER_INVALID")

    def audit(g, call, error=None):
        assert all(r["closed"] for r in records[:-1])
        if not audit_available:
            raise PersistenceUnavailable("Injected independent audit failure")
        return original_audit(g, call, error)

    monkeypatch.setattr(api, "validate_request", fail_input)
    monkeypatch.setattr(runtime, "audit", audit)
    result = request(
        client,
        "createProject",
        token=token,
        body={"name": "Rejected"},
        expect=422 if audit_available and not dependency_fault else 503,
    )
    expected = "DEPENDENCY_UNAVAILABLE" if dependency_fault else "PARAMETER_INVALID"
    assert result.json()["code"] == (expected if audit_available else "AUDIT_UNAVAILABLE")
    assert len(records) == 2 and all(r["closed"] for r in records)
    assert records[0]["session"] is not records[1]["session"]
    with factory() as uow:
        assert uow.gateway.count("projects") == 0
        assert uow.gateway.count(
            "audit_events", {"request_id": result.json()["request_id"]}
        ) == int(audit_available)
    # New structural goal: no successful read-only commit before an invalid input is handled.
    assert (records[0]["commits"], records[0]["rollbacks"]) == (0, 1)


@pytest.mark.parametrize("identity", ["missing", "revoked", "expired", "nonmember", "service"])
def test_preflight_write_auth_precedes_invalid_json(application, identity):
    from datetime import timedelta

    from t44.services.common import now
    from t44.services.identity import issue_session, token_digest

    client, factory = application
    tokens, pid, iid = setup_project(client)
    task = create_task(client, tokens, pid, iid)
    token = tokens["outsider"] if identity == "nonmember" else tokens["manager"]
    if identity == "missing":
        token = None
    elif identity in ("revoked", "expired", "service"):
        with factory() as uow:
            g, clock = uow.gateway, now()
            if identity == "service":
                service = g.insert(
                    "service_accounts",
                    {"name": "write-auth-test", "active": 1, "created_at": clock},
                )
                token = issue_session(
                    g,
                    clock=clock,
                    ttl=3600,
                    service_account_id=service,
                    project_ids=[pid],
                    scopes=["escalation:write"],
                )["access_token"]
            else:
                session = g.rows("auth_sessions", {"token_hash": token_digest(token)})[0]
                values = (
                    {"revoked_at": clock}
                    if identity == "revoked"
                    else {
                        "created_at": clock - timedelta(days=2),
                        "expires_at": clock - timedelta(days=1),
                    }
                )
                g.update("auth_sessions", {"id": session["id"]}, values)
    key = uuid4().hex
    response = client.patch(
        f"/api/v1/projects/{pid}/tasks/{task['id']}/plan",
        content="{",
        headers={
            "Content-Type": "application/json",
            "Idempotency-Key": key,
            **({"Authorization": "Bearer " + token} if token else {}),
        },
    )
    expected = {
        "missing": (401, "AUTH_REQUIRED"),
        "revoked": (401, "TOKEN_REVOKED"),
        "expired": (401, "TOKEN_EXPIRED"),
        "nonmember": (403, "PROJECT_ACCESS_DENIED"),
        "service": (403, "ACTION_FORBIDDEN"),
    }[identity]
    assert (response.status_code, response.json()["code"]) == expected
    with factory() as uow:
        assert uow.gateway.get("audit_events", response.json()["audit_id"])["outcome"] == 2
        assert uow.gateway.count("idempotency_requests", {"idempotency_key": key}) == 0
        assert uow.gateway.get("tasks", task["id"])["version"] == task["version"]
