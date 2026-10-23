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

    race_keys = [uuid4().hex, uuid4().hex]

    def competing_change(index):
        return request(
            client,
            "changeTaskPlan",
            token=tokens["manager"],
            project_id=pid,
            task_id=task["id"],
            key=race_keys[index],
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
            {
                "actor_id": users["manager"],
                "operation_id": "changeTaskPlan",
                "idempotency_key": race_keys,
            },
        )
        assert len(completed) == 2 and all(r["response_request_id"] for r in completed)
        assert all(r["status"] == 2 for r in completed)
        assert {r["idempotency_key"] for r in completed} == set(race_keys)
        assert {r["response_request_id"] for r in completed} == {
            r.headers["x-request-id"] for r in responses
        }
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


@pytest.mark.parametrize("category", [1, 2, 3])
def test_read_uow_real_mysql_success_statement_and_acquire_ledger(real_task, monkeypatch, category):
    from sqlalchemy import event

    client, factory, users, tokens, pid, iteration, task = real_task
    engine = factory._sessions.kw["bind"]
    statements, acquires = [], []
    connect = engine.connect

    def acquire(*args, **kwargs):
        acquires.append(1)
        return connect(*args, **kwargs)

    def statement(_connection, _cursor, _statement, _parameters, context, _many):
        statements.append(
            tuple(table.name for table in context.compiled.statement.get_final_froms())
        )

    candidates = {
        1: {
            "title": "Read statement ledger",
            "owner_id": users["developer"],
            "iteration_id": iteration["id"],
            "plan": PLAN,
            "dependency_task_ids": [],
        },
        2: {"expected_version": task["version"], "action": 1},
        3: _http.assessment_payload(task),
    }
    with factory() as uow:
        before = {
            table: uow.gateway.count(table, {"project_id": pid})
            for table in ("tasks", "audit_events", "outbox_events", "idempotency_requests")
            if table != "idempotency_requests"
        }
        idem_before = uow.gateway.count("idempotency_requests")
    monkeypatch.setattr(engine, "connect", acquire)
    event.listen(engine, "before_cursor_execute", statement)
    try:
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
    finally:
        event.remove(engine, "before_cursor_execute", statement)
        monkeypatch.setattr(engine, "connect", connect)
    expected_tables = [
        (name,) for name in ("auth_sessions", "users", "project_members", "projects")
    ]
    assert statements == expected_tables + ([("tasks",)] if category != 1 else [])
    assert len(acquires) == 1
    result = response.json()
    assert result["data"]["valid"] is True and result["data"]["business_guards_executed"] is False
    assert (
        result["data"]["schema_version"]
        == _http.SPEC["components"]["schemas"]["ContractValidationResult"]["properties"][
            "schema_version"
        ]["const"]
    )
    assert result["meta"]["contract_version"] == _http.SPEC["info"]["version"]
    with factory() as uow:
        assert before == {table: uow.gateway.count(table, {"project_id": pid}) for table in before}
        assert uow.gateway.count("idempotency_requests") == idem_before
        assert uow.gateway.get("tasks", task["id"])["version"] == task["version"]
    print(
        json.dumps(
            {
                "category": category,
                "actual_selects": len(statements),
                "actual_acquires": len(acquires),
                "database": engine.url.database,
            }
        )
    )


@pytest.mark.parametrize("revocation", ["session", "membership"])
@pytest.mark.parametrize("inflight", [False, True])
def test_read_uow_real_mysql_revocation_and_new_request_order(
    real_task, monkeypatch, revocation, inflight
):
    from threading import Event

    from t44 import api
    from t44.services.common import now
    from t44.services.identity import issue_session

    client, factory, users, tokens, pid, _, task = real_task
    with factory() as uow:
        # Isolated synthetic session for the real reviewer; shared module tokens stay usable.
        reader = issue_session(uow.gateway, clock=now(), ttl=3600, user_id=users["reviewer"])[
            "access_token"
        ]
    entered, release = Event(), Event()
    original = api.validate_request

    def gate(request_, operation, call):
        if (
            call.operation == "validateContractPayload"
            and call.token == reader
            and not entered.is_set()
        ):
            entered.set()
            if not release.wait(10):
                raise AssertionError("Read validation release timed out")
        return original(request_, operation, call)

    monkeypatch.setattr(api, "validate_request", gate)
    body = {
        "category": 2,
        "task_id": task["id"],
        "payload": {"expected_version": task["version"], "action": 1},
    }

    def read():
        return request(client, "validateContractPayload", token=reader, project_id=pid, body=body)

    def revoke():
        if revocation == "session":
            return request(client, "logout", token=reader, expect=200)
        return request(
            client,
            "removeProjectMember",
            token=tokens["manager"],
            project_id=pid,
            user_id=users["reviewer"],
            body={"expected_version": 1, "reason": "Synthetic concurrent read revocation"},
            expect=200,
        )

    if inflight:
        with ThreadPoolExecutor(max_workers=2) as executor:
            prior_read = executor.submit(read)
            try:
                assert entered.wait(10), "Reader never completed its first live authorization"
                # Actual HTTP writer must commit before releasing the reader, proving no new S lock.
                revoked = executor.submit(revoke).result(timeout=10)
                assert revoked.status_code == 200 and not prior_read.done()
            finally:
                release.set()
            result = prior_read.result(timeout=10)
        assert result.status_code == 200 and result.json()["data"]["valid"] is True
    else:
        release.set()
        revoke()
    after = read()
    assert (after.status_code, after.json()["code"]) == (
        (401, "TOKEN_REVOKED") if revocation == "session" else (403, "PROJECT_ACCESS_DENIED")
    )
    with factory() as uow:
        audit = uow.gateway.get("audit_events", after.json()["audit_id"])
        assert (
            audit["request_id"] == after.json()["request_id"]
            and audit["actor_id"] == users["reviewer"]
        )
        assert uow.gateway.get("tasks", task["id"])["version"] == task["version"]
    print(
        json.dumps(
            {
                "revocation": revocation,
                "old_read_inflight": inflight,
                "new_request_status": after.status_code,
                "database": factory._sessions.kw["bind"].url.database,
            }
        )
    )


@pytest.mark.parametrize("case", ["block", "unblock", "plan", "escalation", "replay"])
def test_preflight_real_mysql_transaction_and_unchanged_sql_ledger(real_task, monkeypatch, case):
    from collections import Counter
    from datetime import timedelta

    from sqlalchemy import event
    from t44.services import runtime as runtime_module
    from t44.services.common import now, wire
    from t44.services.identity import issue_session

    client, factory, users, tokens, pid, _, task = real_task
    runtime = client.app.state.runtime
    token, operation, body = (
        tokens["manager"],
        "transitionTask",
        {
            "expected_version": task["version"],
            "action": 2,
            "reason": "Ledger block",
            "responsibility_stage": 1,
            "evidence": EVIDENCE,
        },
    )
    key = uuid4().hex
    if case == "unblock":
        task = _http.transition(
            client,
            token,
            pid,
            task,
            2,
            reason="Before unblock",
            responsibility_stage=1,
            evidence=EVIDENCE,
        )
        body = {
            "expected_version": task["version"],
            "action": 3,
            "basis": "Resolved",
            "evidence": EVIDENCE,
        }
    elif case in ("plan", "replay"):
        operation, body = (
            "changeTaskPlan",
            {
                "expected_version": task["version"],
                "plan": PLAN,
                "reason": "Ledger plan",
                "evidence": EVIDENCE,
            },
        )
        if case == "replay":
            request(
                client,
                operation,
                token=token,
                project_id=pid,
                task_id=task["id"],
                body=body,
                key=key,
                expect=200,
            )
    elif case == "escalation":
        clock = now()
        task = request(
            client,
            "changeTaskPlan",
            token=token,
            project_id=pid,
            task_id=task["id"],
            body={
                "expected_version": task["version"],
                "plan": {
                    **PLAN,
                    "planned_start": wire(clock - timedelta(hours=2)),
                    "planned_end": wire(clock - timedelta(hours=1)),
                },
                "reason": "Eligible synthetic event",
                "evidence": EVIDENCE,
            },
            expect=200,
        ).json()["data"]["task"]
        with factory() as uow:
            g = uow.gateway
            service = g.insert(
                "service_accounts",
                {"name": "preflight-" + uuid4().hex, "active": 1, "created_at": clock},
            )
            token = issue_session(
                g,
                clock=clock,
                ttl=3600,
                service_account_id=service,
                project_ids=[pid],
                scopes=["escalation:write"],
            )["access_token"]
        operation, body = (
            "createEscalation",
            {
                "expected_version": task["version"],
                "schedule_version": task["schedule_version"],
                "rule_version": 1,
                "scan_run_id": str(uuid4()),
            },
        )
    records = _http._preflight_transactions(runtime, factory, monkeypatch)
    engine = factory._sessions.kw["bind"]
    statements, acquires, auth_locks = [], [], []
    connect, authenticate = engine.connect, runtime_module.authenticate

    def acquire(*args, **kwargs):
        acquires.append(1)
        return connect(*args, **kwargs)

    def authorize(g, call, **kwargs):
        auth_locks.append(kwargs.get("lock"))
        return authenticate(g, call, **kwargs)

    def statement(_connection, _cursor, _sql, _parameters, context, _many):
        stmt = context.compiled.statement
        statements.append(
            (
                stmt.__visit_name__,
                tuple(t.name for t in stmt.get_final_froms()) if stmt.is_select else (),
            )
        )

    monkeypatch.setattr(engine, "connect", acquire)
    monkeypatch.setattr(runtime_module, "authenticate", authorize)
    event.listen(engine, "before_cursor_execute", statement)
    try:
        response = request(
            client,
            operation,
            token=token,
            project_id=pid,
            task_id=task["id"],
            body=body,
            key=key,
            expect=202 if case == "escalation" else 200,
        )
    finally:
        event.remove(engine, "before_cursor_execute", statement)
        monkeypatch.setattr(engine, "connect", connect)
    counts = Counter(kind for kind, _ in statements)
    expected = {
        "block": (22, 5, 2),
        "unblock": (24, 5, 2),
        "plan": (20, 6, 2),
        "escalation": (26, 7, 6),
        "replay": (9, 0, 0),
    }[case]
    actual = (
        counts["select"],
        sum(counts[k] for k in ("insert", "update", "delete")),
        sum(counts[k] for k in ("savepoint", "release_savepoint", "rollback_to_savepoint")),
    )
    print(
        json.dumps(
            {
                "case": case,
                "SELECT_DML_control": actual,
                "uows": len(records),
                "acquires": len(acquires),
                "commits": sum(r["commits"] for r in records),
                "database": engine.url.database,
            }
        )
    )
    assert actual == expected
    assert auth_locks == ([None, "share"] if case == "replay" else [None, "share", "share"])
    assert all(r["closed"] and r["commits"] == 1 and r["rollbacks"] == 0 for r in records)
    assert response.json()["meta"]["replayed"] == (case == "replay")
    # Only the boundary shrinks: all real authentication and original SQL above remain.
    assert len(records) == len(acquires) == (1 if case == "replay" else 2)


@pytest.mark.parametrize("revocation", ["session", "membership"])
@pytest.mark.parametrize("pause", ["validation", "claim"])
def test_preflight_real_mysql_rc_rechecks_revocation_in_both_write_phases(
    real_task, monkeypatch, revocation, pause
):
    from threading import Event

    from sqlalchemy import event
    from t44 import api
    from t44.services import runtime as runtime_module
    from t44.services.common import now
    from t44.services.identity import issue_session

    client, factory, users, tokens, pid, _, task = real_task
    runtime = client.app.state.runtime
    with factory() as uow:
        token = issue_session(uow.gateway, clock=now(), ttl=3600, user_id=users["reviewer"])[
            "access_token"
        ]
    entered, release, revoke_done, writer_started, writer_acquired = (Event() for _ in range(5))
    original_validate, original_auth, original_scope = (
        api.validate_request,
        runtime_module.authenticate,
        runtime.locked_scope,
    )
    authentications, isolations = [], []
    engine = factory._sessions.kw["bind"]

    def gate():
        entered.set()
        assert release.wait(10), "Bounded preflight barrier was not released"

    def validate(request_, op, call):
        if pause == "validation" and call.token == token and call.operation == "changeTaskPlan":
            gate()
        return original_validate(request_, op, call)

    def authenticate(g, call, **kwargs):
        actor = original_auth(g, call, **kwargs)
        if call.token == token and call.operation == "changeTaskPlan":
            authentications.append(g._session())
            # Explicit diagnostic DBAPI metadata query, not part of the separate SQL ledger test.
            isolations.append(g._session().connection().get_isolation_level())
            if pause == "claim" and kwargs.get("lock") == "share":
                gate()
        return actor

    def scope(g, call):
        if pause == "claim" and call.token == token and call.operation == "changeTaskPlan":
            assert revoke_done.wait(10), "Revocation did not commit before main recheck"
        return original_scope(g, call)

    def before_cursor(_c, _cursor, _sql, _params, context, _many):
        stmt = context.compiled.statement
        lock = getattr(stmt, "_for_update_arg", None)
        if (
            stmt.is_select
            and lock is not None
            and not lock.read
            and any(t.name == "auth_sessions" for t in stmt.get_final_froms())
        ):
            writer_started.set()

    def after_cursor(_c, _cursor, _sql, _params, context, _many):
        stmt = context.compiled.statement
        lock = getattr(stmt, "_for_update_arg", None)
        if (
            stmt.is_select
            and lock is not None
            and not lock.read
            and any(t.name == "auth_sessions" for t in stmt.get_final_froms())
        ):
            writer_acquired.set()

    monkeypatch.setattr(api, "validate_request", validate)
    monkeypatch.setattr(runtime_module, "authenticate", authenticate)
    monkeypatch.setattr(runtime, "locked_scope", scope)
    event.listen(engine, "before_cursor_execute", before_cursor)
    event.listen(engine, "after_cursor_execute", after_cursor)
    key = uuid4().hex

    def change():
        return request(
            client,
            "changeTaskPlan",
            token=token,
            project_id=pid,
            task_id=task["id"],
            key=key,
            body={
                "expected_version": task["version"],
                "plan": PLAN,
                "reason": "Revocation barrier",
                "evidence": EVIDENCE,
            },
        )

    def revoke():
        response = (
            request(client, "logout", token=token, expect=200)
            if revocation == "session"
            else request(
                client,
                "removeProjectMember",
                token=tokens["manager"],
                project_id=pid,
                user_id=users["reviewer"],
                body={"expected_version": 1, "reason": "Synthetic write revocation"},
                expect=200,
            )
        )
        revoke_done.set()
        return response

    try:
        with ThreadPoolExecutor(max_workers=2) as executor:
            writing = executor.submit(change)
            try:
                assert entered.wait(10)
                revoking = executor.submit(revoke)
                if pause == "claim" and revocation == "session":
                    assert writer_started.wait(10)
                    assert not writer_acquired.wait(0.2), "Session X unexpectedly passed held S"
                    assert not revoking.done()
                else:
                    assert revoking.result(timeout=10).status_code == 200
                    assert not writing.done()
            finally:
                release.set()
            assert revoking.result(timeout=10).status_code == 200
            response = writing.result(timeout=10)
    finally:
        event.remove(engine, "before_cursor_execute", before_cursor)
        event.remove(engine, "after_cursor_execute", after_cursor)
    code = "TOKEN_REVOKED" if revocation == "session" else "PROJECT_ACCESS_DENIED"
    assert (response.status_code, response.json()["code"]) == (
        401 if revocation == "session" else 403,
        code,
    )
    assert isolations and set(isolations) == {"READ COMMITTED"}
    if pause == "claim":
        # New structural goal: both preflight reads use one real app Session, not cached rows.
        assert len(authentications) == 2 and authentications[0] is authentications[1]
    new_response = change()
    assert (
        new_response.json()["code"] == code
        and new_response.json()["audit_id"] != response.json()["audit_id"]
    )
    with factory() as uow:
        assert uow.gateway.get("tasks", task["id"])["version"] == task["version"]
        audit = uow.gateway.get("audit_events", response.json()["audit_id"])
        assert audit["outcome"] == 2 and audit["request_id"] == response.json()["request_id"]
        idem = uow.gateway.rows("idempotency_requests", {"idempotency_key": key})
        assert len(idem) == int(pause == "claim")
        if idem:
            assert idem[0]["status"] == 2 and idem[0]["response_status"] == response.status_code
    print(
        json.dumps(
            {
                "revocation": revocation,
                "pause": pause,
                "isolation": isolations,
                "database": engine.url.database,
                "session_writer_waited_for_S": pause == "claim" and revocation == "session",
            }
        )
    )


@pytest.mark.fault
@pytest.mark.parametrize("lost_commit", ["claim", "main"])
def test_preflight_real_mysql_commit_ack_loss_recovers_from_persisted_state(
    real_task, monkeypatch, lost_commit
):
    from datetime import timedelta

    from t44.persistence import CommitUncertain
    from t44.services import runtime as runtime_module
    from t44.services.common import now

    client, factory, users, tokens, pid, _, task = real_task
    runtime = client.app.state.runtime
    observed, original = [], runtime_module.authenticate
    owned_commits, injected = [], []

    def authorize(g, call, **kwargs):
        observed[:] = [call]
        return original(g, call, **kwargs)

    def acknowledged_commit(record):
        if observed and observed[0].idem:
            owned_commits.append(record)
            if len(owned_commits) == (1 if lost_commit == "claim" else 2) and not injected:
                injected.append(True)
                raise CommitUncertain("Controlled ACK loss after real successful commit")

    monkeypatch.setattr(runtime_module, "authenticate", authorize)
    records = _http._preflight_transactions(runtime, factory, monkeypatch, acknowledged_commit)
    key, body = (
        uuid4().hex,
        {
            "expected_version": task["version"],
            "plan": PLAN,
            "reason": "ACK injection",
            "evidence": EVIDENCE,
        },
    )

    def change():
        return request(
            client,
            "changeTaskPlan",
            token=tokens["manager"],
            project_id=pid,
            task_id=task["id"],
            key=key,
            body=body,
        )

    with factory() as uow:
        before = {
            table: uow.gateway.count(table, {"project_id": pid})
            for table in ("audit_events", "outbox_events", "schedule_changes")
        }
    first = change()
    assert (
        first.status_code == 503
        and first.json()["code"] == "TRANSACTION_UNCERTAIN"
        and injected == [True]
    )
    with factory() as uow:
        idem = uow.gateway.rows("idempotency_requests", {"idempotency_key": key})[0]
        assert idem["status"] == (1 if lost_commit == "claim" else 2)
        assert uow.gateway.get("tasks", task["id"])["version"] == task["version"] + int(
            lost_commit == "main"
        )
        if lost_commit == "claim":
            # Explicit isolated fixture lease expiry, not a claim of elapsed wall clock.
            uow.gateway.update(
                "idempotency_requests",
                {"id": idem["id"]},
                {"lease_until": now() - timedelta(seconds=1)},
            )
    recovered = change()
    assert recovered.status_code == 200
    assert recovered.json()["meta"]["replayed"] == (lost_commit == "main")
    replay = change()
    assert replay.status_code == 200 and replay.json()["meta"]["replayed"] is True
    expected_request_id = (
        first.json()["request_id"]
        if lost_commit == "main"
        else recovered.json()["meta"]["request_id"]
    )
    assert replay.json()["meta"]["original_request_id"] == expected_request_id
    with factory() as uow:
        idem = uow.gateway.rows("idempotency_requests", {"idempotency_key": key})[0]
        assert idem["status"] == 2 and idem["response_request_id"] == expected_request_id
        assert uow.gateway.get("tasks", task["id"])["version"] == task["version"] + 1
        for table, count in before.items():
            assert uow.gateway.count(table, {"project_id": pid}) == count + 1
    assert all(r["closed"] for r in records)
    print(
        json.dumps(
            {
                "lost_commit": lost_commit,
                "injection": "after real commit, not network fault",
                "database": factory._sessions.kw["bind"].url.database,
                "business_applications": 1,
            }
        )
    )


@pytest.mark.parametrize("failure", ["input", "version", "dependency"])
def test_preflight_real_mysql_rejection_closes_before_fresh_audit(real_task, monkeypatch, failure):
    from t44.persistence import PersistenceUnavailable

    client, factory, _, tokens, pid, _, task = real_task
    runtime = client.app.state.runtime
    with factory() as uow:
        before = {
            table: uow.gateway.count(table, {"project_id": pid})
            for table in ("audit_events", "outbox_events", "schedule_changes")
        }
    records = _http._preflight_transactions(runtime, factory, monkeypatch)
    original_audit = runtime.audit

    def audit(g, call, error=None):
        assert all(r["closed"] for r in records[:-1])
        assert len({id(r["session"]) for r in records}) == len(records)
        return original_audit(g, call, error)

    def failed_dispatch(*_):
        raise PersistenceUnavailable("Controlled business dependency failure before commit")

    monkeypatch.setattr(runtime, "audit", audit)
    if failure == "dependency":
        monkeypatch.setattr(runtime.business, "dispatch", failed_dispatch)
    key = uuid4().hex
    response = request(
        client,
        "changeTaskPlan",
        token=tokens["manager"],
        project_id=pid,
        task_id=task["id"],
        key=key,
        body={
            "expected_version": task["version"] + int(failure == "version"),
            "plan": PLAN,
            "reason": "Independent rejection",
            "evidence": EVIDENCE,
            **({"unexpected": True} if failure == "input" else {}),
        },
        expect={"input": 422, "version": 409, "dependency": 503}[failure],
    )
    assert (
        response.json()["code"]
        == {
            "input": "PARAMETER_INVALID",
            "version": "VERSION_CONFLICT",
            "dependency": "DEPENDENCY_UNAVAILABLE",
        }[failure]
    )
    with factory() as uow:
        assert uow.gateway.get("tasks", task["id"])["version"] == task["version"]
        for table, count in before.items():
            assert uow.gateway.count(table, {"project_id": pid}) == count + int(
                table == "audit_events"
            )
        audit_row = uow.gateway.get("audit_events", response.json()["audit_id"])
        assert (
            audit_row["outcome"] == 2 and audit_row["request_id"] == response.json()["request_id"]
        )
        idem = uow.gateway.rows("idempotency_requests", {"idempotency_key": key})
        assert len(idem) == int(failure != "input")
        if idem:
            assert idem[0]["status"] == (2 if failure == "version" else 1)
    assert all(r["closed"] for r in records)
    assert len(records) == (2 if failure == "input" else 3)
    assert (records[0]["commits"], records[0]["rollbacks"]) == (
        (0, 1) if failure == "input" else (1, 0)
    )
