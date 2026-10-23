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
