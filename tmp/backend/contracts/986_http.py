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


@pytest.mark.parametrize("operation", ["block", "unblock_pending", "start_empty"])
def test_transition_reads_only_dependencies_consumed_by_its_guard(application, operation, monkeypatch):
    import re
    from collections import Counter

    from sqlalchemy import event

    client, factory = application
    tokens, pid, iid = setup_project(client)
    predecessor = create_task(client, tokens, pid, iid)
    task = create_task(
        client, tokens, pid, iid, [] if operation == "start_empty" else [predecessor["id"]]
    )
    if operation == "unblock_pending":
        task = transition(
            client,
            tokens["manager"],
            pid,
            task,
            2,
            reason="Synthetic intake block with an unfinished predecessor",
            responsibility_stage=1,
            evidence=EVIDENCE,
        )
    counts = Counter()
    engine = factory._sessions.kw["bind"]

    from t44.persistence.rows import RowsGateway

    lock_reads = []
    original_rows = RowsGateway.rows

    def checked_rows(gateway, table, where=None, **options):
        if table == "tasks" and options.get("lock") == "update":
            lock_reads.append((id(gateway), where["project_id"], where["id"]))
        return original_rows(gateway, table, where, **options)

    monkeypatch.setattr(RowsGateway, "rows", checked_rows)

    def selected_tables(connection, cursor, statement, parameters, context, executemany):
        if statement.lstrip().upper().startswith("SELECT"):
            match = re.search(r"\bFROM\s+(task_dependencies|tasks)\b", statement, re.IGNORECASE)
            if match:
                counts[match[1].lower()] += 1

    body = {"expected_version": task["version"]}
    if operation == "block":
        body.update(action=2, reason="Block despite unresolved dependency", responsibility_stage=1)
        body["evidence"] = EVIDENCE
    elif operation == "unblock_pending":
        body.update(
            action=3, basis="Return to intake without starting development", evidence=EVIDENCE
        )
    else:
        body["action"] = 1
    token = tokens["developer" if operation == "start_empty" else "manager"]
    key = str(uuid4())
    event.listen(engine, "before_cursor_execute", selected_tables)
    try:
        response = request(
            client,
            "transitionTask",
            token=token,
            project_id=pid,
            task_id=task["id"],
            body=body,
            key=key,
            expect=200,
        )
    finally:
        event.remove(engine, "before_cursor_execute", selected_tables)
    expected_locks = sorted(
        [task["id"], predecessor["id"]] if operation == "unblock_pending" else [task["id"]]
    )
    assert [entry[2] for entry in lock_reads] == expected_locks
    assert {entry[1] for entry in lock_reads} == {pid}
    assert len({entry[0] for entry in lock_reads}) == 1
    changed = response.json()["data"]["task"]
    assert changed["version"] == task["version"] + 1
    assert changed["state"] == {"block": 3, "unblock_pending": 1, "start_empty": 2}[operation]
    with factory() as uow:
        audit = uow.gateway.get("audit_events", response.json()["data"]["audit_id"])
        assert audit["outcome"] == 1
        assert uow.gateway.get("tasks", task["id"])["version"] == changed["version"]
    replay = request(
        client,
        "transitionTask",
        token=token,
        project_id=pid,
        task_id=task["id"],
        body=body,
        key=key,
        expect=200,
    )
    assert replay.json()["data"] == response.json()["data"]
    assert replay.json()["meta"]["replayed"] is True
    if operation == "unblock_pending":
        rejected = transition(client, tokens["developer"], pid, changed, 1, expect=409)
        assert rejected.json()["code"] == "DEPENDENCIES_UNSATISFIED"
        with factory() as uow:
            rejected_audit = uow.gateway.get("audit_events", rejected.json()["audit_id"])
            assert rejected_audit["outcome"] == 2
            assert uow.gateway.get("tasks", task["id"])["version"] == changed["version"]
    # The same-main-UoW locked target replaces Business.task; audit scope still reads.
    # Original sorted scalar FOR UPDATE locks add K=1/2/1 reads.
    # Pending UNBLOCK locks its predecessor but does not consume it in the business guard.
    assert counts == Counter(
        tasks={"block": 2, "unblock_pending": 3, "start_empty": 2}[operation],
        task_dependencies={"block": 0, "unblock_pending": 1, "start_empty": 2}[operation],
    )


@pytest.mark.parametrize("operation", ["unblock_develop", "rework"])
def test_dependency_guard_still_rejects_reactivation_with_unfinished_predecessor(
    application, operation
):
    from t44.services.codes import ERROR_IDS, State

    client, factory = application
    tokens, pid, iid = setup_project(client)
    predecessor = create_task(client, tokens, pid, iid)
    task = create_task(client, tokens, pid, iid, [predecessor["id"]])
    # Controlled persisted boundary, not evidence of a real rollback/rework lifecycle.
    with factory() as uow:
        g = uow.gateway
        g.update(
            "tasks",
            {"id": task["id"]},
            {"state": State.BLOCKED, "blocked_from_state": State.DEVELOPING}
            if operation == "unblock_develop"
            else {"state": State.ROLLED_BACK},
        )
        before = g.get("tasks", task["id"])
        outbox_count = g.count("outbox_events", {"task_id": task["id"]})
    body = {"expected_version": task["version"], "evidence": EVIDENCE}
    if operation == "unblock_develop":
        body.update(action=3, basis="Dependency still prevents development")
    else:
        body.update(action=9, reason="Manager requests another delivery cycle", new_plan=PLAN)
    response = request(
        client,
        "transitionTask",
        token=tokens["developer" if operation == "unblock_develop" else "manager"],
        project_id=pid,
        task_id=task["id"],
        body=body,
        expect=409,
    )
    assert response.json()["code"] == "DEPENDENCIES_UNSATISFIED"
    with factory() as uow:
        g = uow.gateway
        assert g.get("tasks", task["id"]) == before
        assert g.count("outbox_events", {"task_id": task["id"]}) == outbox_count
        audit = g.get("audit_events", response.json()["audit_id"])
        assert audit["outcome"] == 2
        assert audit["reason_code"] == ERROR_IDS["DEPENDENCIES_UNSATISFIED"]


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


def test_numeric_id_sql_expression_is_security_rejection_before_task_query(application):
    from sqlalchemy import event
    from t44.services.codes import ERROR_IDS

    client, factory = application
    tokens, pid, iid = setup_project(client)
    task = create_task(client, tokens, pid, iid)
    url = f"/api/v1/projects/{pid}/tasks?owner_id=1%20OR%201%3D1"
    engine = factory._sessions.kw["bind"]
    task_selects = []

    def selected(_connection, _cursor, _sql, _parameters, context, _many):
        statement = context.compiled.statement
        if statement.is_select and any(t.name == "tasks" for t in statement.get_final_froms()):
            task_selects.append(1)

    event.listen(engine, "before_cursor_execute", selected)
    try:
        response = client.get(url, headers={"Authorization": f"Bearer {tokens['manager']}"})
    finally:
        event.remove(engine, "before_cursor_execute", selected)
    assert response.status_code == 400
    assert response.json()["code"] == "SECURITY_INPUT_REJECTED"
    assert not violations(
        OPERATIONS["listTasks"]["responses"]["400"]["content"]["application/json"]["schema"],
        response.json(),
    )
    assert task_selects == []
    with factory() as uow:
        audit = uow.gateway.get("audit_events", response.json()["audit_id"])
        assert audit["outcome"] == 2
        assert audit["reason_code"] == ERROR_IDS["SECURITY_INPUT_REJECTED"]
        assert uow.gateway.get("tasks", task["id"])["version"] == task["version"]
    malformed = request(
        client,
        "listTasks",
        token=tokens["manager"],
        project_id=pid,
        query={"owner_id": "one"},
        expect=422,
    )
    assert malformed.json()["code"] == "PARAMETER_INVALID"
    valid = request(
        client,
        "listTasks",
        token=tokens["manager"],
        project_id=pid,
        query={"owner_id": task["owner_id"]},
        expect=200,
    )
    assert [row["id"] for row in valid.json()["data"]["items"]] == [task["id"]]
    assert client.get(url).status_code == 401


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


def _reason_write(client, factory, tokens, pid, iid, task, kind, reason, key):
    if kind == "iteration":
        iteration = request(
            client, "listIterations", token=tokens["manager"], project_id=pid, expect=200
        ).json()["data"]["items"][0]
        operation, path = "changeIteration", {"iteration_id": iid}
        body = {"expected_version": iteration["version"], "plan": iteration["plan"]}
    else:
        operation, path = "changeTaskPlan", {"task_id": task["id"]}
        body = {"expected_version": task["version"], "plan": PLAN}
        if kind == "rework":
            # Explicit synthetic terminal fixture, not an end-to-end release history.
            with factory() as uow:
                uow.gateway.update("tasks", {"id": task["id"]}, {"state": 7})
            operation = "transitionTask"
            body = {"expected_version": task["version"], "action": 9, "new_plan": PLAN}
    body.update(reason=reason, evidence=EVIDENCE)
    args = {"token": tokens["manager"], "project_id": pid, "body": body, "key": key, **path}
    return operation, args, request(client, operation, **args, expect=200)


@pytest.mark.parametrize("kind", ["plan", "rework", "iteration"])
def test_schedule_reason_new_write_atomic_and_replay(application, kind):
    client, factory = application
    tokens, pid, iid = setup_project(client)
    task = create_task(client, tokens, pid, iid)
    prefix = "2026-10-24\nchangeTaskPlan <b>原文</b> "
    reason = prefix + "理" * (2000 - len(prefix))
    operation, args, response = _reason_write(
        client, factory, tokens, pid, iid, task, kind, reason, uuid4().hex
    )
    with factory() as uow:
        g = uow.gateway
        audit = g.rows("audit_events", {"request_id": response.headers["x-request-id"]})[0]
        schedule = g.rows("schedule_changes", {"project_id": pid})[0]
        assert [d for d in audit["after_values"] if d["field"] == "reason"] == [
            {"field": "reason", "value": reason}
        ]
        assert schedule["reason"] == reason and schedule["changed_at"] == audit["created_at"]
        before = {
            table: g.rows(table, {"project_id": pid})
            for table in ("audit_events", "schedule_changes", "outbox_events", "decisions")
        }
    replay = request(client, operation, **args, expect=200)
    assert replay.json()["meta"]["replayed"] and replay.json()["data"] == response.json()["data"]
    result = request(
        client,
        "listProjectAuditEvents",
        token=tokens["manager"],
        project_id=pid,
        query={"page_size": 100},
        expect=200,
    ).json()["data"]
    saved = next(a for a in result["items"] if a["id"] == audit["id"])
    assert saved["after"] == audit["after_values"]
    with factory() as uow:
        assert {table: uow.gateway.rows(table, {"project_id": pid}) for table in before} == before


def _legacy_reason_fixture(client, factory, tokens, pid, task):
    from copy import deepcopy

    changed = request(
        client,
        "changeTaskPlan",
        token=tokens["manager"],
        project_id=pid,
        task_id=task["id"],
        body={
            "expected_version": task["version"],
            "plan": PLAN,
            "reason": "2026-10-24\nchangeTaskPlan <literal> historical reason",
            "evidence": EVIDENCE,
        },
        expect=200,
    )
    with factory() as uow:
        audit = uow.gateway.get("audit_events", changed.json()["data"]["audit_id"])
        schedule = uow.gateway.rows("schedule_changes", {"task_id": task["id"]})[0]
    legacy = deepcopy(audit)
    legacy.pop("id")
    legacy["after_values"] = [d for d in legacy["after_values"] if d["field"] != "reason"]
    return legacy, schedule


def _check_legacy_reason_cases(client, factory, tokens, pid, task):
    from copy import deepcopy
    from datetime import timedelta

    legacy, schedule = _legacy_reason_fixture(client, factory, tokens, pid, task)
    variants = {}
    for name in (
        "exact",
        "actor",
        "time",
        "from",
        "to",
        "expected",
        "task_version",
        "missing_plan",
        "duplicate_plan",
        "plan_text",
        "numeric_spelling",
        "evidence",
        "non_plan",
        "reject",
        "iteration",
        "full50",
        "existing",
        "duplicate_reason",
        "unrelated_duplicate",
    ):
        row = deepcopy(legacy)
        row["request_id"] = "reason-fixture-" + uuid4().hex
        before, after = row["before_values"], row["after_values"]

        def replace(side, field, value):
            next(d for d in side if d["field"] == field)["value"] = value

        if name == "actor":
            row["actor_id"] += 1
        elif name == "time":
            row["created_at"] += timedelta(microseconds=1)
        elif name in ("from", "to"):
            replace(before if name == "from" else after, "schedule_version", "3")
        elif name == "expected":
            row["expected_version"] += 1
        elif name == "task_version":
            replace(after, "version", "3")
        elif name == "missing_plan":
            before.pop()
        elif name == "duplicate_plan":
            after.append(deepcopy(after[-1]))
        elif name == "plan_text":
            replace(after, "delay_contingency", "Another plan")
        elif name == "numeric_spelling":
            replace(after, "estimated_hours", "8")
        elif name == "evidence":
            row["evidence"] = []
        elif name == "non_plan":
            row["operation_id"] = "transitionTask"
            before.append({"field": "state", "value": "2"})
            after.append({"field": "state", "value": "3"})
        elif name == "reject":
            row.update(outcome=2, reason_code=13)
        elif name == "iteration":
            row.update(operation_id="changeIteration", task_id=None)
        elif name == "full50":
            after.extend({"field": f"legacy_{n}", "value": "keep"} for n in range(50 - len(after)))
        elif name == "unrelated_duplicate":
            after.extend(
                [{"field": "legacy_note", "value": "one"}, {"field": "legacy_note", "value": "two"}]
            )
        elif name in ("existing", "duplicate_reason"):
            row["created_at"] += timedelta(seconds=1)
            after.append({"field": "reason", "value": "Existing literal reason"})
            if name == "duplicate_reason":
                after.append({"field": "reason", "value": "Second literal reason"})
        with factory() as uow:
            identifier = uow.gateway.insert("audit_events", row)
        variants[name] = identifier, row
    page = request(
        client,
        "listProjectAuditEvents",
        token=tokens["manager"],
        project_id=pid,
        query={"page_size": 100},
        expect=200,
    ).json()["data"]
    found = {a["id"]: a for a in page["items"]}
    for name, (identifier, row) in variants.items():
        expected = row["after_values"] + (
            [{"field": "reason", "value": schedule["reason"]}]
            if name in ("exact", "unrelated_duplicate")
            else []
        )
        assert found[identifier]["after"] == expected, name
        with factory() as uow:
            persisted = uow.gateway.get("audit_events", identifier)
            assert {k: v for k, v in persisted.items() if k != "id"} == row
    with factory() as uow:
        assert uow.gateway.get("schedule_changes", schedule["id"]) == schedule


def test_schedule_reason_legacy_exact_and_mismatched_history(application):
    client, factory = application
    tokens, pid, iid = setup_project(client)
    task = create_task(client, tokens, pid, iid)
    _check_legacy_reason_cases(client, factory, tokens, pid, task)


def _check_reason_page_bound(client, factory, tokens, pid, task, monkeypatch):
    from copy import deepcopy

    from t44.persistence.rows import RowsGateway

    legacy, schedule = _legacy_reason_fixture(client, factory, tokens, pid, task)
    with factory() as uow:
        g = uow.gateway
        task_row = g.get("tasks", task["id"])
        task_row.pop("id")
        count = g.count("audit_events", {"project_id": pid})
        # Audit GET has no sort parameter. Align the next 100-row ascending page.
        padding = (-count) % 100
        for _ in range(padding):
            g.insert(
                "audit_events",
                {
                    **deepcopy(legacy),
                    "request_id": uuid4().hex,
                    "operation_id": "createTask",
                    "before_values": [],
                    "after_values": [],
                    "expected_version": None,
                },
            )
        page_number = (count + padding) // 100 + 1
        for _ in range(100):
            tid = g.insert("tasks", task_row)
            row = {**deepcopy(schedule), "task_id": tid}
            row.pop("id")
            g.insert("schedule_changes", row)
            audit = {**deepcopy(legacy), "task_id": tid, "request_id": uuid4().hex}
            g.insert("audit_events", audit)
        before = g.rows("audit_events", {"project_id": pid})
    calls = []
    original = RowsGateway.task_schedule_changes

    def read(g, project_id, pairs):
        calls.append((project_id, pairs))
        return original(g, project_id, pairs)

    monkeypatch.setattr(RowsGateway, "task_schedule_changes", read)
    first = request(
        client,
        "listProjectAuditEvents",
        token=tokens["manager"],
        project_id=pid,
        query={"page_size": 100, "page": page_number},
        expect=200,
    ).json()["data"]
    assert len(first["items"]) == 100 and first["total"] == len(before)
    assert len(calls) == 1 and calls[0][0] == pid and len(calls[0][1]) == 100
    assert len(set(calls[0][1])) == 100
    assert all(
        a["after"][-1] == {"field": "reason", "value": schedule["reason"]} for a in first["items"]
    )
    offset = (page_number - 1) * 100
    assert [a["id"] for a in first["items"]] == sorted(a["id"] for a in before)[
        offset : offset + 100
    ]
    calls.clear()
    first_page = request(
        client,
        "listProjectAuditEvents",
        token=tokens["manager"],
        project_id=pid,
        query={"page_size": 100, "page": 1},
        expect=200,
    ).json()["data"]
    assert first_page["total"] == first["total"] and calls == []
    assert not ({a["id"] for a in first_page["items"]} & {a["id"] for a in first["items"]})
    with factory() as uow:
        assert uow.gateway.rows("audit_events", {"project_id": pid}) == before
    return legacy, schedule


def test_schedule_reason_100_row_current_page_uses_one_exact_batch(application, monkeypatch):
    client, factory = application
    tokens, pid, iid = setup_project(client)
    task = create_task(client, tokens, pid, iid)
    _check_reason_page_bound(client, factory, tokens, pid, task, monkeypatch)


def test_schedule_reason_failed_write_rolls_back_reason_and_plan(application, monkeypatch):
    from t44.persistence.errors import PersistenceUnavailable

    client, factory = application
    tokens, pid, iid = setup_project(client)
    task = create_task(client, tokens, pid, iid)
    with factory() as uow:
        original_task = uow.gateway.get("tasks", task["id"])
        original_outbox = uow.gateway.rows("outbox_events", {"task_id": task["id"]})
    runtime = client.app.state.runtime
    audit = runtime.audit

    def fail_success(g, call, error=None):
        if call.operation == "changeTaskPlan" and error is None:
            raise PersistenceUnavailable("Controlled post-schedule failure")
        return audit(g, call, error)

    monkeypatch.setattr(runtime, "audit", fail_success)
    response = request(
        client,
        "changeTaskPlan",
        token=tokens["manager"],
        project_id=pid,
        task_id=task["id"],
        body={
            "expected_version": task["version"],
            "plan": {**PLAN, "delay_contingency": "Must not persist changed plan"},
            "reason": "Must roll back",
            "evidence": EVIDENCE,
        },
        expect=503,
    )
    with factory() as uow:
        assert uow.gateway.get("tasks", task["id"]) == original_task
        assert uow.gateway.rows("outbox_events", {"task_id": task["id"]}) == original_outbox
        assert not uow.gateway.rows("schedule_changes", {"task_id": task["id"]})
        rejected = uow.gateway.get("audit_events", response.json()["audit_id"])
        assert rejected["outcome"] == 2 and rejected["after_values"] == []


def test_schedule_reason_authorization_and_empty_page_do_not_load_history(application, monkeypatch):
    from t44.persistence.rows import RowsGateway

    client, _ = application
    tokens, pid, _ = setup_project(client)
    calls = []

    def forbidden_batch(*args):
        calls.append(1)
        raise AssertionError("History read was not needed/authorized")

    monkeypatch.setattr(RowsGateway, "task_schedule_changes", forbidden_batch)
    valid = request(
        client,
        "listProjectAuditEvents",
        token=tokens["manager"],
        project_id=pid,
        query={"task_id": 4294967295},
        expect=200,
    )
    assert valid.json()["data"]["items"] == [] and valid.json()["data"]["total"] == 0
    rejected = request(
        client, "listProjectAuditEvents", token=tokens["outsider"], project_id=pid, expect=403
    )
    assert rejected.json()["code"] == "PROJECT_ACCESS_DENIED" and calls == []


def test_schedule_reason_malformed_candidate_plan_is_unverifiable_not_guessed(
    application, monkeypatch
):
    from copy import deepcopy

    from t44.persistence.rows import RowsGateway

    client, factory = application
    tokens, pid, iid = setup_project(client)
    task = create_task(client, tokens, pid, iid)
    legacy, schedule = _legacy_reason_fixture(client, factory, tokens, pid, task)
    legacy["request_id"] = uuid4().hex
    with factory() as uow:
        identifier = uow.gateway.insert("audit_events", legacy)
    # Controlled returned-payload corruption only; original database rows stay unchanged.
    for bad in (
        None,
        {},
        {**schedule["before_plan"], "unexpected": "extra"},
        {**schedule["before_plan"], "estimated_hours": True},
        {**schedule["before_plan"], "buffer_hours": "1.0"},
        {**schedule["before_plan"], "planned_start": "0001-01-01T00:00:00Z"},
    ):

        def malformed(_g, _project_id, _pairs, plan=bad):
            return [{**deepcopy(schedule), "before_plan": plan}]

        monkeypatch.setattr(RowsGateway, "task_schedule_changes", malformed)
        response = request(
            client,
            "listProjectAuditEvents",
            token=tokens["manager"],
            project_id=pid,
            query={"task_id": task["id"]},
            expect=200,
        ).json()["data"]
        record = next(row for row in response["items"] if row["id"] == identifier)
        assert record["after"] == legacy["after_values"]
    with factory() as uow:
        assert uow.gateway.get("schedule_changes", schedule["id"]) == schedule


@pytest.mark.parametrize("legacy_format", ["integer_hours", "short_utc"])
def test_schedule_reason_matching_nonproducer_spelling_still_unverifiable(
    application, monkeypatch, legacy_format
):
    from copy import deepcopy

    from t44.persistence.rows import RowsGateway

    client, factory = application
    tokens, pid, iid = setup_project(client)
    task = create_task(client, tokens, pid, iid)
    legacy, schedule = _legacy_reason_fixture(client, factory, tokens, pid, task)
    legacy["request_id"] = uuid4().hex
    if legacy_format == "integer_hours":
        field, value, text = "estimated_hours", 8, "8"
    else:
        field = "planned_start"
        value = text = schedule["before_plan"][field].replace(".000000Z", "Z")
    next(d for d in legacy["before_values"] if d["field"] == field)["value"] = text
    with factory() as uow:
        identifier = uow.gateway.insert("audit_events", legacy)

    # This is synthetic identical alternate spelling, not an observed legacy database format.
    def old_format(_g, _project_id, _pairs):
        return [{**deepcopy(schedule), "before_plan": {**schedule["before_plan"], field: value}}]

    monkeypatch.setattr(RowsGateway, "task_schedule_changes", old_format)
    result = request(
        client,
        "listProjectAuditEvents",
        token=tokens["manager"],
        project_id=pid,
        query={"task_id": task["id"]},
        expect=200,
    ).json()["data"]
    record = next(row for row in result["items"] if row["id"] == identifier)
    assert record["after"] == legacy["after_values"]


@pytest.mark.parametrize(
    "case", ["boolean_kind", "float_kind", "exact", "reordered_keys", "changed_text", "array_order"]
)
def test_schedule_reason_evidence_json_types_and_exact_values(application, case):
    import json
    from copy import deepcopy

    client, factory = application
    tokens, pid, iid = setup_project(client)
    task = create_task(client, tokens, pid, iid)
    legacy, schedule = _legacy_reason_fixture(client, factory, tokens, pid, task)
    evidence = [
        {
            "kind": 1,
            "locator": "https://example.test/repo",
            "revision": "fixed",
            "description": "Same visible evidence except JSON type",
        }
    ]
    if case == "array_order":
        evidence.append({"kind": 2, "locator": "synthetic/additional", "description": "Second"})
    candidate = deepcopy(evidence)
    if case == "boolean_kind":
        candidate[0]["kind"] = True
    elif case == "float_kind":
        candidate[0]["kind"] = 1.0
    elif case == "reordered_keys":
        candidate[0] = dict(reversed(list(candidate[0].items())))
    elif case == "changed_text":
        candidate[0]["description"] += " "
    elif case == "array_order":
        candidate.reverse()
    evidence_schema = SPEC["components"]["schemas"]["EvidenceRefs"]
    assert not violations(evidence_schema, evidence)
    assert bool(violations(evidence_schema, candidate)) == (case == "boolean_kind")
    if case in ("boolean_kind", "float_kind"):
        assert evidence == candidate  # This is the old Python equality false-positive.
    legacy["evidence"] = evidence
    legacy["request_id"] = "evidence-type-fixture-" + uuid4().hex
    with factory() as uow:
        g = uow.gateway
        # Own synthetic historical JSON only, not a normal API write or real observed dataset.
        g.update("schedule_changes", {"id": schedule["id"]}, {"evidence": candidate})
        audit_id = g.insert("audit_events", legacy)
        before = [
            json.dumps(g.get(table, identifier), sort_keys=True, default=str)
            for table, identifier in (
                ("audit_events", audit_id),
                ("schedule_changes", schedule["id"]),
            )
        ]
    response = request(
        client,
        "listProjectAuditEvents",
        token=tokens["manager"],
        project_id=pid,
        query={"task_id": task["id"]},
        expect=200,
    ).json()["data"]
    record = next(row for row in response["items"] if row["id"] == audit_id)
    expected = (
        [{"field": "reason", "value": schedule["reason"]}]
        if case in ("exact", "reordered_keys")
        else []
    )
    assert [item for item in record["after"] if item["field"] == "reason"] == expected
    assert record["evidence"] == evidence
    with factory() as uow:
        after = [
            json.dumps(uow.gateway.get(table, identifier), sort_keys=True, default=str)
            for table, identifier in (
                ("audit_events", audit_id),
                ("schedule_changes", schedule["id"]),
            )
        ]
        assert after == before
