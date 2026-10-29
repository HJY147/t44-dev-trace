"""Native SQLite row/statement differential against exact integration baseline, not cloud."""

import importlib
import importlib.util
import os
import subprocess
import sys
import types
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from sqlalchemy import create_engine, event
from t44.contracts import OPERATIONS
from t44.persistence import SqlAlchemyUnitOfWorkFactory
from t44.persistence.schema import metadata
from t44.services.application import Business
from t44.services.common import Call

ROOT = Path(__file__).resolve().parents[2]
BASE = "5868779e949adef066fe26bffbc4f2e8afee7649"


@pytest.fixture(scope="session")
def original_business(tmp_path_factory):
    directory = tmp_path_factory.mktemp("exact-baseline-services")
    for path in (ROOT / "backend/t44/services").glob("*.py"):
        raw = subprocess.check_output(
            ["git", "show", BASE + ":backend/t44/services/" + path.name], cwd=ROOT
        )
        (directory / path.name).write_bytes(raw)
    package = types.ModuleType("_final_original_services")
    package.__path__ = [str(directory)]
    sys.modules[package.__name__] = package
    return importlib.import_module(package.__name__ + ".application").Business


@pytest.fixture
def store():
    engine = create_engine("sqlite://")
    metadata.create_all(engine)
    factory = SqlAlchemyUnitOfWorkFactory(engine)
    timestamp = datetime(2026, 10, 29, 10, tzinfo=UTC)
    with factory() as uow:
        g = uow.gateway
        users = [
            g.insert(
                "users",
                {
                    "username": f"synthetic-{i}",
                    "display_name": f"synthetic-{i}",
                    "password_hash": "unused-not-a-session",
                    "active": 1,
                    "created_at": timestamp,
                    "updated_at": timestamp,
                },
            )
            for i in range(20)
        ]
        project = g.insert(
            "projects",
            {
                "name": "synthetic-project",
                "description": "",
                "created_by": users[0],
                "created_at": timestamp,
                "updated_at": timestamp,
            },
        )
        for uid in users:
            g.insert(
                "project_members",
                {
                    "project_id": project,
                    "user_id": uid,
                    "roles_mask": 1,
                    "active": 1,
                    "created_at": timestamp,
                    "updated_at": timestamp,
                },
            )
        iteration = g.insert(
            "iterations",
            {
                "project_id": project,
                "name": "synthetic-iteration",
                "planned_start": timestamp,
                "planned_end": timestamp + timedelta(days=2),
                "buffer_quarters": 4,
                "capacity": [{"user_id": users[0], "available_hours": 40}],
                "delay_contingency": "synthetic",
                "created_at": timestamp,
                "updated_at": timestamp,
            },
        )
        tasks = [
            g.insert(
                "tasks",
                {
                    "project_id": project,
                    "iteration_id": iteration,
                    "title": f"synthetic-{i}",
                    "description": "",
                    "owner_id": users[0],
                    "planned_start": timestamp,
                    "planned_end": timestamp + timedelta(days=1),
                    "estimated_quarters": 4,
                    "buffer_quarters": 1,
                    "delay_contingency": "synthetic",
                    "created_at": timestamp,
                    "updated_at": timestamp,
                },
            )
            for i in range(21)
        ]
        for predecessor in tasks[1:]:
            g.insert(
                "task_dependencies",
                {
                    "project_id": project,
                    "task_id": tasks[0],
                    "depends_on_task_id": predecessor,
                    "created_by": users[0],
                    "created_at": timestamp,
                },
            )
    statements = []

    def capture(connection, cursor, statement, parameters, context, executemany):
        if statement.lstrip().upper().startswith("SELECT"):
            statements.append(statement)

    event.listen(engine, "before_cursor_execute", capture)
    yield factory, statements, project, users[0], tasks[0]
    engine.dispose()


def read(factory, business, operation, pid, uid, tid, query=None):
    path = {
        "project_id": pid,
        **({"task_id": tid} if "{task_id}" in OPERATIONS[operation]["path"] else {}),
    }
    call = Call(
        operation, "synthetic-request", None, path=path, query=query or {"page": 1, "page_size": 20}
    )
    call.actor = {"actor_id": uid}
    with factory() as uow:
        return business().dispatch(uow.gateway, call)


@pytest.mark.parametrize(
    "operation,bound", [("listProjectMembers", 3), ("listTaskDependencies", 4)]
)
def test_complete_same_page_without_per_item_selects(store, original_business, operation, bound):
    factory, statements, pid, uid, tid = store
    expected = read(factory, original_business, operation, pid, uid, tid)
    baseline_selects = len(statements)
    statements.clear()
    candidate = original_business if os.getenv("FINAL_BACKEND_BASELINE") else Business
    actual = read(factory, candidate, operation, pid, uid, tid)
    assert actual == expected
    assert len(actual["items"]) == 20 and actual["total"] == 20
    assert baseline_selects == bound + 19
    assert len(statements) == bound


@pytest.mark.parametrize("operation", ["listProjectMembers", "listTaskDependencies"])
def test_empty_page_does_not_fetch_related_table(store, original_business, operation):
    factory, statements, pid, uid, tid = store
    query = {"page": 5, "page_size": 20}
    expected = read(factory, original_business, operation, pid, uid, tid, query)
    count = len(statements)
    statements.clear()
    actual = read(factory, Business, operation, pid, uid, tid, query)
    assert actual == expected and not actual["items"]
    assert len(statements) == count


@pytest.mark.parametrize(
    "operation",
    [
        "listProjects",
        "listIterations",
        "listTasks",
        "listTaskReviews",
        "listReleaseAssessments",
        "listTaskDecisions",
        "listProjectAuditEvents",
    ],
)
def test_other_collection_projection_filter_and_paging_unchanged(
    store, original_business, operation
):
    factory, statements, pid, uid, tid = store
    assert read(factory, Business, operation, pid, uid, tid) == read(
        factory, original_business, operation, pid, uid, tid
    )
