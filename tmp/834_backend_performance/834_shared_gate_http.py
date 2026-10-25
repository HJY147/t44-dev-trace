"""Finite opt-in fresh-CI MySQL HTTP races; never formal performance acceptance."""

import contextlib
import hashlib
import importlib.util
import json
import os
import subprocess
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from importlib import import_module
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pytest

PLAN = {
    "planned_start": "2030-01-01T00:00:00Z",
    "planned_end": "2030-01-03T00:00:00Z",
    "estimated_hours": 8,
    "buffer_hours": 1,
    "delay_contingency": "Synthetic finite HTTP lock test",
}
EVIDENCE = [{"kind": 2, "locator": "synthetic/shared-project-gate", "description": "Test"}]


def stamp():
    return {"utc": datetime.now(UTC).isoformat(), "monotonic_ns": time.perf_counter_ns()}


@contextlib.contextmanager
def case_record(env, name):
    row = {"name": name, "started": stamp(), "status": "running"}
    env.report["cases"].append(row)
    try:
        yield row
        row["status"] = "passed development HTTP case only"
    except BaseException as error:
        row.update(status="failed retained", exception_class=type(error).__name__)
        raise
    finally:
        row["ended"] = stamp()


def send(env, operation, *, role="manager", body=None, key=None, expect=200, **path):
    from t44.contracts import OPERATIONS, violations

    op = OPERATIONS[operation]
    headers = {"Authorization": f"Bearer {env.tokens[role]}"} if role else {}
    if any(p.get("$ref", "").endswith("/IdempotencyKey") for p in op.get("parameters", [])):
        headers["Idempotency-Key"] = key or str(uuid4())
    response = env.client.request(
        op["method"], "/api/v1" + op["path"].format(**path), headers=headers, json=body
    )
    value = response.json()
    env.report["responses"].append(
        {
            "operation": operation,
            "status": response.status_code,
            "code": value.get("code"),
            "request_id": response.headers.get("x-request-id"),
            **stamp(),
        }
    )
    assert response.status_code == expect, (operation, response.status_code, value.get("code"))
    schema = op["responses"][str(expect)]["content"]["application/json"]["schema"]
    assert not violations(schema, value), operation
    assert response.headers["cache-control"] == "no-store"
    return value


@pytest.fixture(scope="module")
def environment():
    if os.getenv("CI") != "true" or os.getenv("T44_GATE_ALLOW_MYSQL") != "true":
        pytest.fail("Explicit fresh CI MySQL HTTP gate required; no local/private fallback")
    root = Path(__file__).resolve().parents[2]
    expected = os.environ["T44_GATE_EXPECTED_SOURCE"]
    assert (
        subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
        == expected
    )
    source_names = (
        "backend/t44/services/runtime.py",
        "tmp/834_backend_performance/834_shared_gate_http.py",
        "tmp/backend/contracts/986_http.py",
    )
    hashes = {}
    for name in source_names:
        raw = (root / name).read_bytes()
        assert raw == subprocess.check_output(["git", "show", f"HEAD:{name}"], cwd=root)
        hashes[name] = hashlib.sha256(raw).hexdigest()
    probe_path = Path(os.environ["T44_GATE_DB_PROBE"])
    probe_raw = probe_path.read_bytes()
    assert hashlib.sha256(probe_raw).hexdigest() == os.environ["T44_GATE_DB_PROBE_SHA256"]
    spec = importlib.util.spec_from_file_location("db_lock_probe_public", probe_path)
    probe = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(probe)
    from fastapi.testclient import TestClient
    from sqlalchemy import text
    from t44.api import create_app
    from t44.persistence import SqlAlchemyUnitOfWorkFactory, create_mysql_engine
    from t44.persistence.accounts import initialize_user
    from t44.persistence.schema import TABLES
    from t44.services.identity import HASHER
    from t44.settings import Settings

    settings = Settings.from_env().mysql_settings()
    assert settings.database == os.environ["T44_DATABASE"] == "t44_gate_http"
    assert settings.host in {"localhost", "127.0.0.1"} and settings.port != 13306
    output = Path(os.environ["T44_GATE_REPORT"])
    fd = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    report = {
        "source": expected,
        "source_files": hashes,
        "db_probe_sha256": hashlib.sha256(probe_raw).hexdigest(),
        "started": stamp(),
        "formal_performance_acceptance": False,
        "cases": [],
        "responses": [],
    }
    engine = None
    with os.fdopen(fd, "w", encoding="utf-8") as stream:
        try:
            engine = create_mysql_engine(settings)
            factory = SqlAlchemyUnitOfWorkFactory(engine)
            with factory() as uow:
                assert not any(uow.gateway.count(name) for name in TABLES)
            with engine.connect() as connection:
                report["mysql"] = dict(
                    connection.execute(
                        text("SELECT VERSION() AS version, @@transaction_isolation AS isolation")
                    )
                    .mappings()
                    .one()
                )
            hashed = HASHER.hash("synthetic-http-gate-password")
            users = {
                role: initialize_user(
                    factory, username=role, display_name=role, password_hash=hashed
                )
                for role in ("manager", "developer", "reviewer")
            }
            app = create_app(factory=factory, settings=Settings(login_attempts=1000))
            with TestClient(app) as client:
                env = SimpleNamespace(
                    client=client,
                    factory=factory,
                    engine=engine,
                    users=users,
                    tokens={},
                    report=report,
                    probe=probe,
                )
                for role in users:
                    env.tokens[role] = send(
                        env,
                        "login",
                        role=None,
                        body={"username": role, "password": "synthetic-http-gate-password"},
                    )["data"]["access_token"]
                yield env
        except BaseException as error:
            report["fixture_exception_class"] = type(error).__name__
            raise
        finally:
            if engine is not None:
                report["checkedout_before_dispose"] = engine.pool.checkedout()
                engine.dispose()
                report["disposed"] = True
            report["ended"] = stamp()
            stream.write(json.dumps(report, indent=2) + "\n")


@pytest.fixture
def project(environment):
    env = environment
    pid = send(env, "createProject", expect=201, body={"name": "Finite gate HTTP case"})["data"][
        "id"
    ]
    for role, roles in (("developer", [2]), ("reviewer", [1, 2, 3])):
        send(
            env,
            "addProjectMember",
            project_id=pid,
            expect=201,
            body={"username": role, "roles": roles, "reason": "Synthetic team"},
        )
    iteration = send(
        env,
        "createIteration",
        project_id=pid,
        expect=201,
        body={
            "name": "Finite lock test",
            **{k: v for k, v in PLAN.items() if k != "estimated_hours"},
            "capacity": [{"user_id": env.users["developer"], "available_hours": 40}],
        },
    )["data"]
    return env, pid, iteration


def task(env, pid, iteration, dependencies=()):
    return send(
        env,
        "createTask",
        project_id=pid,
        expect=201,
        body={
            "title": "Synthetic shared gate task",
            "owner_id": env.users["developer"],
            "iteration_id": iteration["id"],
            "plan": PLAN,
            "dependency_task_ids": list(dependencies),
        },
    )["data"]["task"]


def transition(env, pid, row, action, *, role="developer", expect=200, key=None, **fields):
    result = send(
        env,
        "transitionTask",
        role=role,
        project_id=pid,
        task_id=row["id"],
        body={"expected_version": row["version"], "action": action, **fields},
        key=key,
        expect=expect,
    )
    return result["data"]["task"] if expect == 200 else result


def delivered(env, pid, row):
    http = import_module("tmp.backend.contracts.986_http")
    row = transition(env, pid, row, 1)
    row = transition(env, pid, row, 4, artifact_revision="a" * 40, evidence=EVIDENCE)
    reviewed = send(
        env,
        "createTaskReview",
        role="reviewer",
        project_id=pid,
        task_id=row["id"],
        body=http.review_payload(row),
        expect=201,
    )["data"]
    row = transition(
        env,
        pid,
        reviewed["task"],
        5,
        role="reviewer",
        review_id=reviewed["review"]["id"],
        review_version=reviewed["review"]["version"],
    )
    payload = http.assessment_payload(row)
    payload["rollback_plan"]["responsible_user_id"] = env.users["manager"]
    assessed = send(
        env,
        "createReleaseAssessment",
        project_id=pid,
        task_id=row["id"],
        body=payload,
        expect=201,
    )["data"]
    approved = send(
        env,
        "reviewReleaseAssessment",
        role="reviewer",
        project_id=pid,
        task_id=row["id"],
        assessment_id=assessed["assessment"]["id"],
        body={
            "expected_version": assessed["task"]["version"],
            "expected_assessment_version": assessed["assessment"]["version"],
            "verdict": 1,
            "reason": "Synthetic independent review",
            "evidence": EVIDENCE,
        },
    )["data"]
    row = transition(
        env,
        pid,
        approved["task"],
        7,
        role="manager",
        assessment_id=approved["assessment"]["id"],
        assessment_version=approved["assessment"]["version"],
        release_version="synthetic-v1",
        reason="Synthetic delivery",
        evidence=EVIDENCE,
    )
    return row, approved["assessment"]


def rollback(env, pid, row, assessment):
    return transition(
        env,
        pid,
        row,
        8,
        role="manager",
        assessment_id=assessment["id"],
        rollback_plan_version=assessment["rollback_plan_version"],
        target_version="v0",
        reason="Synthetic rollback",
        impact="Synthetic impact",
        evidence=EVIDENCE,
    )


class Pause:
    """Pause one real dispatch after the original locked_scope has succeeded."""

    def __init__(self, monkeypatch, predicate):
        from t44.services.application import Business

        self.entered, self.release = threading.Event(), threading.Event()
        self.connection_ids = {}
        original = Business.dispatch

        def dispatch(business, gateway, call):
            if predicate(call):
                self.connection_ids[call.operation] = (
                    gateway._session()
                    .connection()
                    .exec_driver_sql("SELECT CONNECTION_ID()")
                    .scalar_one()
                )
                self.entered.set()
                if not self.release.wait(10):
                    raise TimeoutError("Controlled HTTP dispatch release not received")
            return original(business, gateway, call)

        monkeypatch.setattr(Business, "dispatch", dispatch)


def observe_wait(env, monkeypatch, predicate, blocking_id):
    from t44.services.runtime import Runtime

    arrived = threading.Event()
    holder = {}
    original = Runtime.locked_scope

    def locked(runtime, gateway, call):
        if predicate(call):
            holder["id"] = (
                gateway._session()
                .connection()
                .exec_driver_sql("SELECT CONNECTION_ID()")
                .scalar_one()
            )
            arrived.set()
        return original(runtime, gateway, call)

    monkeypatch.setattr(Runtime, "locked_scope", locked)

    def wait():
        assert arrived.wait(5), "Second HTTP transaction did not enter original locked_scope"
        assert holder["id"] != blocking_id
        deadline = time.monotonic() + 5
        tick = threading.Event()
        while time.monotonic() < deadline:
            snapshot = env.probe.lock_snapshot(env.engine, [holder["id"], blocking_id])
            if any(
                row["requesting_connection"] == holder["id"]
                and row["blocking_connection"] == blocking_id
                for row in snapshot["waits"]
            ):
                return {**stamp(), **snapshot}
            tick.wait(0.01)
        raise AssertionError("Expected actual MySQL requesting/blocking edge not observed")

    return wait


def rejection_effects(env, result, row, *, key, actor):
    with env.factory() as uow:
        g = uow.gateway
        current = g.get("tasks", row["id"])
        assert current["version"] == row["version"] and current["state"] == row["state"]
        audit = g.get("audit_events", result["audit_id"])
        assert audit["outcome"] == 2 and audit["request_id"] == result["request_id"]
        idem = g.rows(
            "idempotency_requests",
            {
                "actor_id": env.users[actor],
                "operation_id": "transitionTask",
                "idempotency_key": key,
            },
        )
        assert len(idem) == 1 and idem[0]["status"] == 2
        assert idem[0]["response_body"]["error"]["code"] == result["code"]


def test_disjoint_start_readers_reach_business_together(project, monkeypatch):
    from t44.services.application import Business

    env, pid, iteration = project
    rows = [task(env, pid, iteration) for _ in range(2)]
    rendezvous = threading.Barrier(2, timeout=5)
    original = Business.dispatch
    entered = []

    def dispatch(business, gateway, call):
        if call.operation == "transitionTask" and call.path["task_id"] in {r["id"] for r in rows}:
            entered.append({"task_id": call.path["task_id"], **stamp()})
            rendezvous.wait()
        return original(business, gateway, call)

    monkeypatch.setattr(Business, "dispatch", dispatch)
    with case_record(env, "disjoint_start_actual_http") as report:
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(transition, env, pid, row, 1) for row in rows]
            result = [future.result(timeout=12) for future in futures]
        report["both_business_arrivals"] = entered
        assert len(entered) == 2 and all(row["state"] == 2 for row in result)
        assert all(
            after["version"] == before["version"] + 1
            for before, after in zip(rows, result, strict=True)
        )


def test_graph_writer_waits_for_reader_then_edits_other_task(project, monkeypatch):
    env, pid, iteration = project
    reader, target = task(env, pid, iteration), task(env, pid, iteration)
    pause = Pause(
        monkeypatch, lambda c: c.operation == "transitionTask" and c.path["task_id"] == reader["id"]
    )
    with case_record(env, "graph_writer_waits_for_reader_http") as report:
        with ThreadPoolExecutor(max_workers=2) as executor:
            first = executor.submit(transition, env, pid, reader, 1)
            try:
                assert pause.entered.wait(5)
                wait = observe_wait(
                    env,
                    monkeypatch,
                    lambda c: c.operation == "addTaskDependency",
                    pause.connection_ids["transitionTask"],
                )
                second = executor.submit(
                    send,
                    env,
                    "addTaskDependency",
                    project_id=pid,
                    task_id=target["id"],
                    expect=201,
                    body={
                        "expected_version": target["version"],
                        "depends_on_task_id": reader["id"],
                    },
                )
                report["actual_wait"] = wait()
            finally:
                pause.release.set()
            assert first.result(timeout=12)["state"] == 2
            result = second.result(timeout=12)["data"]
        assert result["task"]["version"] == target["version"] + 1
        assert result["dependency"]["depends_on_task_id"] == reader["id"]


def test_predecessor_rollback_commit_rejects_waiting_start(project, monkeypatch):
    env, pid, iteration = project
    predecessor, assessment = delivered(env, pid, task(env, pid, iteration))
    dependent = task(env, pid, iteration, [predecessor["id"]])
    pause = Pause(
        monkeypatch,
        lambda c: c.operation == "transitionTask" and c.path["task_id"] == predecessor["id"],
    )
    key = str(uuid4())
    with case_record(env, "predecessor_rollback_before_start_http") as report:
        with ThreadPoolExecutor(max_workers=2) as executor:
            first = executor.submit(rollback, env, pid, predecessor, assessment)
            try:
                assert pause.entered.wait(5)
                wait = observe_wait(
                    env,
                    monkeypatch,
                    lambda c: (
                        c.operation == "transitionTask" and c.path["task_id"] == dependent["id"]
                    ),
                    pause.connection_ids["transitionTask"],
                )
                second = executor.submit(transition, env, pid, dependent, 1, expect=409, key=key)
                report["actual_wait"] = wait()
            finally:
                pause.release.set()
            assert first.result(timeout=12)["state"] == 7
            result = second.result(timeout=12)
        assert result["code"] == "DEPENDENCIES_UNSATISFIED"
        rejection_effects(env, result, dependent, key=key, actor="developer")


@pytest.mark.parametrize("writer", ["capacity", "role"])
def test_rework_rechecks_capacity_or_manager_after_wait(project, monkeypatch, writer):
    env, pid, iteration = project
    row, assessment = delivered(env, pid, task(env, pid, iteration))
    row = rollback(env, pid, row, assessment)
    operation = "changeIteration" if writer == "capacity" else "changeProjectMember"
    pause = Pause(monkeypatch, lambda c: c.operation == operation)
    key = str(uuid4())
    with case_record(env, "rework_waits_for_" + writer + "_http") as report:
        with env.factory() as uow:
            member = uow.gateway.rows(
                "project_members", {"project_id": pid, "user_id": env.users["reviewer"]}
            )[0]
            outbox_before = uow.gateway.count("outbox_events", {"task_id": row["id"]})
        body = (
            {
                "expected_version": iteration["version"],
                "plan": {
                    **iteration["plan"],
                    "capacity": [{"user_id": env.users["reviewer"], "available_hours": 40}],
                },
                "reason": "Remove rolled-back owner capacity",
                "evidence": EVIDENCE,
            }
            if writer == "capacity"
            else {
                "expected_version": member["version"],
                "roles": [3],
                "reason": "Remove manager role",
            }
        )
        path = (
            {"iteration_id": iteration["id"]}
            if writer == "capacity"
            else {"user_id": env.users["reviewer"]}
        )
        with ThreadPoolExecutor(max_workers=2) as executor:
            first = executor.submit(send, env, operation, project_id=pid, body=body, **path)
            try:
                assert pause.entered.wait(5)
                wait = observe_wait(
                    env,
                    monkeypatch,
                    lambda c: c.operation == "transitionTask" and c.path["task_id"] == row["id"],
                    pause.connection_ids[operation],
                )
                second = executor.submit(
                    transition,
                    env,
                    pid,
                    row,
                    9,
                    role="reviewer",
                    expect=422 if writer == "capacity" else 403,
                    key=key,
                    new_plan=PLAN,
                    reason="Synthetic rework",
                    evidence=EVIDENCE,
                )
                report["actual_wait"] = wait()
            finally:
                pause.release.set()
            first.result(timeout=12)
            result = second.result(timeout=12)
        assert result["code"] == (
            "CAPACITY_REFERENCE_INVALID" if writer == "capacity" else "ACTION_FORBIDDEN"
        )
        rejection_effects(env, result, row, key=key, actor="reviewer")
        with env.factory() as uow:
            assert uow.gateway.count("outbox_events", {"task_id": row["id"]}) == outbox_before


def test_same_version_start_one_success_one_conflict(project):
    env, pid, iteration = project
    row = task(env, pid, iteration)
    keys = [str(uuid4()), str(uuid4())]
    rendezvous = threading.Barrier(2, timeout=5)

    # Send without an expected outcome; validate each real status against the contract below.
    def competing(key):
        from t44.contracts import OPERATIONS, violations

        rendezvous.wait()
        op = OPERATIONS["transitionTask"]
        response = env.client.request(
            op["method"],
            "/api/v1" + op["path"].format(project_id=pid, task_id=row["id"]),
            headers={"Authorization": "Bearer " + env.tokens["developer"], "Idempotency-Key": key},
            json={"action": 1, "expected_version": row["version"]},
        )
        assert response.status_code in (200, 409)
        value = response.json()
        assert not violations(
            op["responses"][str(response.status_code)]["content"]["application/json"]["schema"],
            value,
        )
        return response.status_code, value, response.headers["x-request-id"]

    with case_record(env, "same_version_start_cas_http") as report:
        with env.factory() as uow:
            before = uow.gateway.count("outbox_events", {"task_id": row["id"]})
        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(competing, keys))
        assert sorted(status for status, _, _ in results) == [200, 409]
        rejected = next(value for status, value, _ in results if status == 409)
        assert rejected["code"] == "VERSION_CONFLICT"
        with env.factory() as uow:
            g = uow.gateway
            current = g.get("tasks", row["id"])
            assert current["state"] == 2 and current["version"] == row["version"] + 1
            assert g.count("outbox_events", {"task_id": row["id"]}) == before + 1
            idems = g.rows(
                "idempotency_requests", {"operation_id": "transitionTask", "idempotency_key": keys}
            )
            assert len(idems) == 2 and all(item["status"] == 2 for item in idems)
            assert {item["response_request_id"] for item in idems} == {
                request_id for _, _, request_id in results
            }
            audit = g.get("audit_events", rejected["audit_id"])
            assert audit["outcome"] == 2 and audit["observed_version"] == current["version"]
        report["responses"] = [
            {"status": status, "code": value.get("code"), "request_id": request_id}
            for status, value, request_id in results
        ]
