"""Opt-in actual HTTP plus MySQL 8.4 application tests in a named project schema."""

import json
import os
from concurrent.futures import ThreadPoolExecutor
from importlib import import_module
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from t44.api import create_app
from t44.persistence import MySQLSettings, SqlAlchemyUnitOfWorkFactory, create_mysql_engine
from t44.persistence.accounts import initialize_user
from t44.persistence.migrations import migrate
from t44.services.identity import HASHER
from t44.settings import Settings

_http = import_module(".986_http", __package__)
EVIDENCE = _http.EVIDENCE
PLAN = _http.PLAN
request = _http.request

pytestmark = [pytest.mark.contract, pytest.mark.integration]


@pytest.fixture(scope="module")
def real_application():
    # CI declares its actual MySQL URL and database; local private files are optional.
    if os.getenv("DATABASE_URL"):
        target = os.getenv("T44_DATABASE")
        if not target:
            pytest.fail("DATABASE_URL requires an explicit T44_DATABASE")
        settings = Settings.from_env().mysql_settings()
        if settings.database != target:
            pytest.fail("HTTP test database does not match the declared database")
    elif os.getenv("T44_HTTP_TEST_CREDENTIALS"):
        target = os.getenv("T44_HTTP_TEST_DATABASE")
        if not target:
            pytest.fail("Private credential mode requires explicit T44_HTTP_TEST_DATABASE")
        secret = json.loads(Path(os.environ["T44_HTTP_TEST_CREDENTIALS"]).read_text())
        settings = MySQLSettings(
            database=target, **{k: secret[k] for k in ("host", "port", "username", "password")}
        )
    elif os.getenv("CI"):
        pytest.fail("CI must supply the real MySQL HTTP test connection")
    else:
        pytest.skip("Supply DATABASE_URL/T44_DATABASE or explicit local HTTP test configuration")
    if target not in ("t44_dev", "t44_test", "t44_ci"):
        pytest.fail("HTTP self-tests are restricted to the named T44 project schemas")
    engine = create_mysql_engine(settings)
    migrate(engine, expected_database=target)
    factory = SqlAlchemyUnitOfWorkFactory(engine)
    names, users, tokens = {}, {}, {}
    suffix, password = uuid4().hex[:12], uuid4().hex
    hashed = HASHER.hash(password)
    for role in ("manager", "developer", "reviewer"):
        names[role] = f"http-{role}-{suffix}"
        users[role] = initialize_user(
            factory, username=names[role], display_name="Synthetic HTTP test", password_hash=hashed
        )
    app = create_app(factory=factory, settings=Settings(login_attempts=1000))
    with TestClient(app) as client:
        for role, name in names.items():
            tokens[role] = request(
                client, "login", body={"username": name, "password": password}, expect=200
            ).json()["data"]["access_token"]
        yield client, factory, users, tokens
    engine.dispose()


@pytest.fixture
def real_task(real_application):
    client, factory, users, tokens = real_application
    pid = request(
        client,
        "createProject",
        token=tokens["manager"],
        body={"name": "Synthetic real MySQL HTTP project"},
        expect=201,
    ).json()["data"]["id"]
    for role, assigned in (("developer", [2]), ("reviewer", [1, 3])):
        with factory() as uow:
            username = uow.gateway.get("users", users[role])["username"]
        request(
            client,
            "addProjectMember",
            token=tokens["manager"],
            project_id=pid,
            body={"username": username, "roles": assigned, "reason": "Synthetic HTTP team"},
            expect=201,
        )
    iteration = request(
        client,
        "createIteration",
        token=tokens["manager"],
        project_id=pid,
        body={
            "name": "HTTP real MySQL",
            **{k: v for k, v in PLAN.items() if k != "estimated_hours"},
            "capacity": [{"user_id": users["developer"], "available_hours": 40}],
        },
        expect=201,
    ).json()["data"]
    task = request(
        client,
        "createTask",
        token=tokens["manager"],
        project_id=pid,
        body={
            "title": "Actual MySQL HTTP flow",
            "owner_id": users["developer"],
            "iteration_id": iteration["id"],
            "plan": PLAN,
            "dependency_task_ids": [],
        },
        expect=201,
    ).json()["data"]["task"]
    return client, factory, users, tokens, pid, iteration, task


def test_real_mysql_atomic_workflow_and_competing_cas(real_task):
    client, factory, users, tokens, pid, _, task = real_task
    body = {"expected_version": task["version"], "action": 1}
    first = request(
        client,
        "transitionTask",
        token=tokens["developer"],
        project_id=pid,
        task_id=task["id"],
        body=body,
        key="mysql-start-once-" + uuid4().hex,
        expect=200,
    )
    task = first.json()["data"]["task"]

    def competing_change(_):
        return request(
            client,
            "changeTaskPlan",
            token=tokens["manager"],
            project_id=pid,
            task_id=task["id"],
            body={
                "expected_version": task["version"],
                "plan": PLAN,
                "reason": "Competing plan",
                "evidence": EVIDENCE,
            },
        )

    with ThreadPoolExecutor(max_workers=2) as executor:
        responses = list(executor.map(competing_change, range(2)))
    assert sorted(r.status_code for r in responses) == [200, 409]
    rejected = next(r for r in responses if r.status_code == 409)
    assert rejected.json()["code"] == "VERSION_CONFLICT"
    with factory() as uow:
        row = uow.gateway.get("tasks", task["id"])
        assert row["version"] == task["version"] + 1
        assert row["schedule_version"] == 2
        audit = uow.gateway.get("audit_events", rejected.json()["audit_id"])
        assert audit["outcome"] == 2 and audit["observed_version"] == row["version"]
        assert uow.gateway.count("schedule_changes", {"task_id": task["id"]}) == 1
        assert uow.gateway.count("outbox_events", {"task_id": task["id"]}) == 3
        completed = uow.gateway.rows(
            "idempotency_requests",
            {"actor_id": users["manager"], "operation_id": "changeTaskPlan", "status": 2},
        )
        assert len(completed) == 2 and all(r["response_request_id"] for r in completed)
    task = request(
        client, "getTask", token=tokens["manager"], project_id=pid, task_id=task["id"], expect=200
    ).json()["data"]
    request(
        client,
        "transitionTask",
        token=tokens["developer"],
        project_id=pid,
        task_id=task["id"],
        body={
            "expected_version": task["version"],
            "action": 4,
            "artifact_revision": "a" * 40,
            "evidence": EVIDENCE,
        },
        expect=200,
    )


@pytest.mark.parametrize("old_approved", [True, False])
def test_real_mysql_assessment_supersession_and_creation_replay(real_task, old_approved):
    client, _, users, tokens, pid, _, task = real_task
    task = _http.transition(client, tokens["developer"], pid, task, 1)
    task = _http.transition(
        client, tokens["developer"], pid, task, 4, artifact_revision="a" * 40, evidence=EVIDENCE
    )
    reviewed = request(
        client,
        "createTaskReview",
        token=tokens["reviewer"],
        project_id=pid,
        task_id=task["id"],
        body=_http.review_payload(task),
        expect=201,
    ).json()["data"]
    task = _http.transition(
        client,
        tokens["reviewer"],
        pid,
        reviewed["task"],
        5,
        review_id=reviewed["review"]["id"],
        review_version=1,
    )

    def assess(current, key):
        payload = _http.assessment_payload(current)
        payload["rollback_plan"]["responsible_user_id"] = users["manager"]
        return payload, request(
            client,
            "createReleaseAssessment",
            token=tokens["manager"],
            project_id=pid,
            task_id=task["id"],
            body=payload,
            key=key,
            expect=201,
        ).json()["data"]

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
                "reason": "Synthetic review",
                "evidence": EVIDENCE,
            },
            expect=expect,
        )

    _, created = assess(task, str(uuid4()))
    task, old = created["task"], created["assessment"]
    if old_approved:
        accepted = approve(task, old).json()["data"]
        task, old = accepted["task"], accepted["assessment"]
    key = str(uuid4())
    payload, created = assess(task, key)
    task, latest = created["task"], created["assessment"]
    assert task["approved_assessment_id"] is None and task["approved_assessment_version"] is None
    if not old_approved:
        assert approve(task, old, 409).json()["code"] == "ASSESSMENT_BASELINE_MISMATCH"
    approved = approve(task, latest).json()["data"]["task"]
    replay = request(
        client,
        "createReleaseAssessment",
        token=tokens["manager"],
        project_id=pid,
        task_id=task["id"],
        body=payload,
        key=key,
        expect=201,
    )
    assert replay.json()["meta"]["replayed"] is True and replay.json()["data"] == created
    assert (
        request(
            client,
            "getTask",
            token=tokens["manager"],
            project_id=pid,
            task_id=task["id"],
            expect=200,
        ).json()["data"]
        == approved
    )


def test_real_mysql_invalid_selectors_keep_independent_rejection_audits(real_task):
    client, factory, _, tokens, pid, _, task = real_task
    for invalid in (0, 4294967296):
        for operation in (
            "getTask",
            "listTaskDependencies",
            "listTaskReviews",
            "listReleaseAssessments",
            "listTaskDecisions",
        ):
            error = request(
                client,
                operation,
                token=tokens["manager"],
                project_id=pid,
                task_id=invalid,
                expect=422,
            ).json()
            assert error["code"] == "PARAMETER_INVALID" and error["audit_id"] is not None
            with factory() as uow:
                audit = uow.gateway.get("audit_events", error["audit_id"])
                assert audit["task_id"] is None and audit["request_id"] == error["request_id"]
                assert audit["attempted_task_id"] == (0 if invalid == 0 else None)
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


def test_real_mysql_capacity_plan_audit_and_input_errors(real_task):
    client, factory, users, tokens, pid, iteration, task = real_task
    request(
        client,
        "changeProjectMember",
        token=tokens["manager"],
        project_id=pid,
        user_id=users["manager"],
        body={"expected_version": 1, "roles": [1, 2], "reason": "Second synthetic developer"},
        expect=200,
    )
    error = request(
        client,
        "createTask",
        token=tokens["manager"],
        project_id=pid,
        body={
            "title": "Absent capacity owner",
            "owner_id": users["manager"],
            "iteration_id": iteration["id"],
            "plan": PLAN,
            "dependency_task_ids": [],
        },
        expect=422,
    ).json()
    assert error["code"] == "CAPACITY_REFERENCE_INVALID" and error["audit_id"] is not None
    with factory() as uow:
        assert uow.gateway.count("tasks", {"project_id": pid}) == 1
    for payload, operation, code in (
        (
            {
                "expected_version": 1,
                "action": 2,
                "reason": "Waiting",
                "responsibility_stage": 5,
                "evidence": [],
            },
            "transitionTask",
            "EVIDENCE_REQUIRED",
        ),
        (
            {
                "category": 2,
                "task_id": task["id"],
                "payload": {"expected_version": 1, "action": 1},
                "client_actor_id": users["manager"],
            },
            "validateContractPayload",
            "PARAMETER_INVALID",
        ),
    ):
        error = request(
            client,
            operation,
            token=tokens["manager"],
            project_id=pid,
            task_id=task["id"],
            body=payload,
            expect=422,
        ).json()
        assert error["code"] == code and error["audit_id"] is not None
    changed = request(
        client,
        "changeTaskPlan",
        token=tokens["manager"],
        project_id=pid,
        task_id=task["id"],
        body={
            "expected_version": 1,
            "plan": {**PLAN, "delay_contingency": "合成" * 1000},
            "reason": "Full plan evidence",
            "evidence": EVIDENCE,
        },
        expect=200,
    ).json()["data"]
    audit = request(
        client,
        "listProjectAuditEvents",
        token=tokens["manager"],
        project_id=pid,
        query={"task_id": task["id"], "page_size": 100},
        expect=200,
    ).json()["data"]["items"]
    audit = next(item for item in audit if item["id"] == changed["audit_id"])
    for side, source in (("before", task), ("after", changed["task"])):
        values = {entry["field"]: entry["value"] for entry in audit[side]}
        for key, value in source["plan"].items():
            assert values[key] == str(value)


@pytest.mark.parametrize("action", ["assignment", "create", "rework"])
@pytest.mark.parametrize("capacity_first", [True, False])
def test_capacity_v11_real_mysql_activation_vs_capacity_removal(
    real_task, monkeypatch, action, capacity_first
):
    from threading import Event

    client, factory, users, tokens, pid, iteration, task = real_task
    # Give the existing project manager a developer role as a second real owner.
    request(
        client,
        "changeProjectMember",
        token=tokens["manager"],
        project_id=pid,
        user_id=users["manager"],
        body={"expected_version": 1, "roles": [1, 2], "reason": "Synthetic second developer"},
        expect=200,
    )
    owners = [users["developer"], users["manager"]]
    iteration = _http.capacity_change(client, tokens["manager"], pid, iteration, owners).json()[
        "data"
    ]
    target = users["developer"] if action == "rework" else users["manager"]
    if action == "rework":
        # Synthetic terminal fixture, separate from the full real workflow test above.
        with factory() as uow:
            uow.gateway.update("tasks", {"id": task["id"]}, {"state": 7})
        task["state"] = 7
    operation = {
        "assignment": "changeTaskAssignment",
        "create": "createTask",
        "rework": "transitionTask",
    }[action]
    first_operation = "changeIteration" if capacity_first else operation
    locked, second_entered, second_scoped, release = (Event() for _ in range(4))
    runtime = client.app.state.runtime
    original = runtime.locked_scope

    def controlled_scope(g, call):
        if call.operation == first_operation:
            original(g, call)
            locked.set()
            if not release.wait(10):
                raise AssertionError("Capacity race release timed out")
        else:
            second_entered.set()
            original(g, call)
            second_scoped.set()

    monkeypatch.setattr(runtime, "locked_scope", controlled_scope)

    def activate():
        body = {
            "assignment": {
                "expected_version": task["version"],
                "owner_id": target,
                "reason": "Synthetic handover",
                "evidence": EVIDENCE,
            },
            "create": {
                "title": "Concurrent synthetic registration",
                "owner_id": target,
                "iteration_id": iteration["id"],
                "plan": PLAN,
                "dependency_task_ids": [],
            },
            "rework": {
                "expected_version": task["version"],
                "action": 9,
                "new_plan": PLAN,
                "reason": "Synthetic reactivation",
                "evidence": EVIDENCE,
            },
        }[action]
        return request(
            client,
            operation,
            token=tokens["manager"],
            project_id=pid,
            body=body,
            **({} if action == "create" else {"task_id": task["id"]}),
        )

    def remove():
        return _http.capacity_change(
            client,
            tokens["manager"],
            pid,
            iteration,
            [owner for owner in owners if owner != target],
            expect=None,
        )

    with factory() as uow:
        before = {
            table: uow.gateway.count(table, {"project_id": pid})
            for table in ("tasks", "outbox_events", "decisions", "schedule_changes")
        }
    with ThreadPoolExecutor(max_workers=2) as executor:
        first = executor.submit(remove if capacity_first else activate)
        try:
            assert locked.wait(10), "First writer did not reach its real lock boundary"
            second = executor.submit(activate if capacity_first else remove)
            assert second_entered.wait(10), "Second writer did not overlap the first transaction"
            assert not second_scoped.wait(0.15), "Second writer bypassed the held project lock"
        finally:
            release.set()
        first_response, second_response = first.result(timeout=15), second.result(timeout=15)
    assert first_response.status_code == (201 if action == "create" and not capacity_first else 200)
    assert second_response.status_code == 422
    rejected = second_response.json()
    assert rejected["code"] == "CAPACITY_REFERENCE_INVALID" and rejected["audit_id"] is not None
    with factory() as uow:
        g = uow.gateway
        audit = g.get("audit_events", rejected["audit_id"])
        assert audit["reason_code"] == 30 and audit["request_id"] == rejected["request_id"]
        saved = g.get("iterations", iteration["id"])
        present = {entry["user_id"] for entry in saved["capacity"]}
        active = g.rows(
            "tasks", {"project_id": pid, "iteration_id": iteration["id"], "state": [1, 2, 3, 4, 5]}
        )
        assert all(row["owner_id"] in present for row in active)
        assert (target not in present) == capacity_first
        current = g.get("tasks", task["id"])
        assert current["version"] == task["version"] + int(
            not capacity_first and action != "create"
        )
        assert g.count("tasks", {"project_id": pid}) == before["tasks"] + int(
            not capacity_first and action == "create"
        )
        assert g.count("outbox_events", {"project_id": pid}) == before["outbox_events"] + 1
        assert g.count("decisions", {"project_id": pid}) == before["decisions"] + int(
            not capacity_first and action == "rework"
        )
        assert g.count("schedule_changes", {"project_id": pid}) == before["schedule_changes"] + int(
            capacity_first or action == "rework"
        )


def test_capacity_v11_real_mysql_safe_handover_then_removal_both_commit(real_task):
    client, factory, users, tokens, pid, iteration, task = real_task
    request(
        client,
        "changeProjectMember",
        token=tokens["manager"],
        project_id=pid,
        user_id=users["manager"],
        body={"expected_version": 1, "roles": [1, 2], "reason": "Synthetic second developer"},
        expect=200,
    )
    iteration = _http.capacity_change(
        client, tokens["manager"], pid, iteration, [users["developer"], users["manager"]]
    ).json()["data"]
    handed = request(
        client,
        "changeTaskAssignment",
        token=tokens["manager"],
        project_id=pid,
        task_id=task["id"],
        body={
            "expected_version": task["version"],
            "owner_id": users["manager"],
            "reason": "Synthetic safe handover",
            "evidence": EVIDENCE,
        },
        expect=200,
    ).json()["data"]["task"]
    removed = _http.capacity_change(
        client, tokens["manager"], pid, iteration, [users["manager"]]
    ).json()["data"]
    assert handed["owner_id"] == users["manager"]
    assert removed["version"] == iteration["version"] + 1
    with factory() as uow:
        assert uow.gateway.get("tasks", task["id"])["owner_id"] == users["manager"]
        assert (
            uow.gateway.get("iterations", iteration["id"])["capacity"]
            == removed["plan"]["capacity"]
        )
