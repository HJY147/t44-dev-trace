"""Real SQLite Gateway lock-call ledger; SQLite does not prove MySQL row locking."""

from importlib import import_module
from types import SimpleNamespace
from uuid import uuid4

import pytest
from t44.services.common import Call
from t44.services.runtime import Runtime
from t44.settings import Settings

gate = import_module("tmp.834_backend_performance.834_shared_gate_http")
profile = import_module("tmp.834_backend_performance.834_request_profile")


@pytest.fixture(scope="module")
def scope_fixture():
    fixture = profile.fixture(SimpleNamespace(mode="sqlite"))
    try:
        client, _, factory, engine, users = next(fixture)
        env = SimpleNamespace(
            client=client,
            factory=factory,
            engine=engine,
            users=users,
            tokens={},
            report={"cases": [], "responses": []},
        )
        for role in users:
            env.tokens[role] = gate.send(
                env,
                "login",
                role=None,
                body={"username": role, "password": "synthetic-diagnostic-password"},
            )["data"]["access_token"]
        _, pid, iteration = gate.project.__wrapped__(env)
        low = [gate.task(env, pid, iteration) for _ in range(2)]
        target = gate.task(env, pid, iteration, [low[1]["id"], low[0]["id"]])
        high = gate.task(env, pid, iteration)
        added = gate.send(
            env,
            "addTaskDependency",
            project_id=pid,
            task_id=target["id"],
            expect=201,
            body={"expected_version": target["version"], "depends_on_task_id": high["id"]},
        )["data"]
        yield env, pid, added["task"], [*low, high]
    finally:
        fixture.close()


@pytest.mark.parametrize(
    ("operation", "action", "graph", "project_lock"),
    [
        ("transitionTask", 1, True, "share"),
        ("transitionTask", 3, True, "share"),
        ("transitionTask", 9, True, "share"),
        ("addTaskDependency", None, True, "update"),
        ("removeTaskDependency", None, True, "update"),
        ("changeTaskAssignment", None, True, "update"),
        ("changeTaskPlan", None, False, None),
        ("transitionTask", 2, False, None),
        ("transitionTask", 7, False, None),
    ],
)
def test_real_gateway_scalar_lock_order_and_original_scope(
    scope_fixture, operation, action, graph, project_lock
):
    env, pid, target, predecessors = scope_fixture
    body = {"expected_version": target["version"]}
    if action is not None:
        body["action"] = action
    if operation == "addTaskDependency":
        # Duplicate body predecessor must remain one task lock, not a second acquisition.
        body["depends_on_task_id"] = predecessors[-1]["id"]
    call = Call(
        operation,
        str(uuid4()),
        env.tokens["manager"],
        path={"project_id": pid, "task_id": target["id"]},
        body=body,
        key=str(uuid4()),
    )
    runtime = Runtime(env.factory, Settings(), None)
    runtime.prepare(call, lambda _: None)
    ledger = []
    with env.factory() as uow:
        gateway = uow.gateway
        original = gateway.rows

        def rows(table, where=None, **kwargs):
            # Bind values from auth/session/idem are intentionally not copied to the ledger.
            ledger.append(
                {
                    "table": table,
                    "lock": kwargs.get("lock"),
                    **(
                        {"where": dict(where), "limit": kwargs.get("limit")}
                        if table == "tasks"
                        else {}
                    ),
                }
            )
            return original(table, where, **kwargs)

        gateway.rows = rows
        assert runtime.locked_scope(gateway, call) is None
        assert call.membership["active"] and call.actor_id == env.users["manager"]
    locks = [row for row in ledger if row["table"] == "tasks" and row["lock"]]
    expected_ids = (
        sorted({target["id"], *(row["id"] for row in predecessors)}) if graph else [target["id"]]
    )
    assert [row["where"]["id"] for row in locks] == expected_ids
    assert all(
        type(row["where"]["id"]) is int
        and row["where"] == {"project_id": pid, "id": identifier}
        and row["limit"] == 1
        and row["lock"] == "update"
        for row, identifier in zip(locks, expected_ids, strict=True)
    )
    assert [(row["table"], row["lock"]) for row in ledger if row["lock"]][:2] == [
        ("auth_sessions", "share"),
        ("idempotency_requests", "update"),
    ]
    project_locks = [row["lock"] for row in ledger if row["table"] == "projects" and row["lock"]]
    assert project_locks == ([project_lock] if project_lock else [])
    member_index = next(
        i
        for i, row in enumerate(ledger)
        if row["table"] == "project_members" and row["lock"] == "share"
    )
    first_task = next(i for i, row in enumerate(ledger) if row["table"] == "tasks" and row["lock"])
    assert member_index < first_task
    if graph:
        project_index = next(
            i for i, row in enumerate(ledger) if row["table"] == "projects" and row["lock"]
        )
        assert project_index < member_index
    assert sum(row["table"] == "task_dependencies" for row in ledger) == int(graph)


@pytest.mark.parametrize("other_project", [False, True])
def test_point_lock_missing_or_foreign_task_keeps_original_not_found(scope_fixture, other_project):
    env, pid, _, _ = scope_fixture
    if other_project:
        _, second_pid, iteration = gate.project.__wrapped__(env)
        identifier = gate.task(env, second_pid, iteration)["id"]
    else:
        identifier = 4294967294
    result = gate.send(
        env,
        "transitionTask",
        role="developer",
        project_id=pid,
        task_id=identifier,
        expect=404,
        body={"expected_version": 1, "action": 1},
    )
    assert result["code"] == "RESOURCE_NOT_FOUND" and result["audit_id"] is not None
    with env.factory() as uow:
        audit = uow.gateway.get("audit_events", result["audit_id"])
        assert audit["outcome"] == 2 and audit["task_id"] is None
