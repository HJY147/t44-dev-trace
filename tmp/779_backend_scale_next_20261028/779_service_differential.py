"""Compare exact f7 service behavior, DB calls and audit diffs without a second SQL backend."""

import copy
import subprocess
import types
from datetime import UTC, datetime
from pathlib import Path

import pytest
from t44.services import reviews, tasks
from t44.services.common import Call

ROOT = Path(__file__).resolve().parents[2]
BASE = "f7cdb5fa3b19f84d8ab0d0b042bf51a5b8484e8f"


def original(name):
    path = "backend/t44/services/" + name + ".py"
    source = subprocess.check_output(["git", "show", BASE + ":" + path], cwd=ROOT)
    module = types.ModuleType("t44.services._baseline_" + name)
    module.__package__ = "t44.services"
    exec(compile(source, path, "exec"), module.__dict__)  # noqa: S102 -- exact local committed source.
    return module


OLD = {"reviews": original("reviews"), "tasks": original("tasks")}


class Gateway:
    def __init__(self, tables):
        self.tables, self.trace = copy.deepcopy(tables), []

    def get(self, table, identifier, **options):
        self.trace.append(("get", table, identifier, options))
        return copy.deepcopy(self.tables.get(table, {}).get(identifier))

    def rows(self, table, where, **options):
        self.trace.append(("rows", table, copy.deepcopy(where), options))
        rows = [
            copy.deepcopy(row)
            for row in self.tables.get(table, {}).values()
            if all(
                row.get(key) in value
                if isinstance(value, list)
                else row.get(key) == value
                for key, value in where.items()
            )
        ]
        for key in reversed(options.get("order_by", ())):
            rows.sort(key=lambda row: row[key.lstrip("-")], reverse=key.startswith("-"))
        return rows[: options.get("limit")] if "limit" in options else rows

    def insert(self, table, values):
        self.trace.append(("insert", table, copy.deepcopy(values)))
        rows = self.tables.setdefault(table, {})
        identifier = max(rows, default=0) + 1
        rows[identifier] = {"id": identifier, "version": 1, **copy.deepcopy(values)}
        return identifier

    def update(self, table, where, values):
        self.trace.append(
            ("update", table, copy.deepcopy(where), copy.deepcopy(values))
        )
        rows = [
            row
            for row in self.tables.get(table, {}).values()
            if all(row.get(k) == v for k, v in where.items())
        ]
        for row in rows:
            row.update(copy.deepcopy(values))
        return len(rows)

    def delete(self, table, where):
        self.trace.append(("delete", table, copy.deepcopy(where)))
        identifiers = [
            identifier
            for identifier, row in self.tables.get(table, {}).items()
            if all(row.get(k) == v for k, v in where.items())
        ]
        for identifier in identifiers:
            del self.tables[table][identifier]
        return len(identifiers)


class TracedCall(Call):
    def manager(self):
        self.before.append({"test_guard": "manager"})
        return super().manager()

    def reviewer(self):
        self.before.append({"test_guard": "reviewer"})
        return super().reviewer()

    def check_version(self, row, **options):
        self.before.append({"test_guard": "version", "row_id": row["id"]})
        return super().check_version(row, **options)


def inputs(operation, case):
    task = {
        "id": 1,
        "project_id": 1,
        "version": 1,
        "state": 1,
        "blocked_from_state": None,
        "iteration_id": 1,
        "owner_id": 10,
        "delivery_cycle": 2,
        "schedule_version": 3,
        "updated_at": datetime(2026, 1, 1, tzinfo=UTC),
    }
    assessment = {
        "id": 1,
        "project_id": 1,
        "task_id": 1,
        "version": 1,
        "status": 1,
        "created_by": 9,
        "delivery_cycle": 2,
        "schedule_version": 3,
        "rollback_plan_version": 4,
    }
    tables = {
        "tasks": {1: task, 2: {"id": 2, "project_id": 1, "state": 6}},
        "iterations": {1: {"id": 1, "project_id": 1, "capacity": [{"user_id": 11}]}},
        "project_members": {
            1: {"id": 1, "project_id": 1, "user_id": 11, "roles_mask": 2, "active": 1}
        },
        "release_assessments": {1: assessment},
        "task_dependencies": {
            5: {"id": 5, "project_id": 1, "task_id": 1, "depends_on_task_id": 2}
        },
    }
    body = {
        "expected_version": 1,
        "owner_id": 11,
        "depends_on_task_id": 2,
        "risks": [{"perspective": value} for value in (1, 2, 3, 4)],
        "rollback_plan": {"responsible_user_id": 11},
        "verdict": 1,
        "expected_assessment_version": 1,
        "reason": "synthetic decision",
        "evidence": [{"kind": 1, "locator": "synthetic"}],
    }
    call = TracedCall(
        operation,
        "synthetic-request",
        None,
        path={"project_id": 1, "task_id": 1, "dependency_id": 5, "assessment_id": 1},
        body=body,
        actor={"actor_id": 10},
        membership={"roles_mask": 5},
        clock=datetime(2026, 10, 28, 4, tzinfo=UTC),
    )
    if "Assessment" in operation:
        task["state"] = 5
    if operation == "addTaskDependency" and case != "duplicate":
        tables["task_dependencies"] = {}
    if case in {"forbidden", "forbidden_and_missing"}:
        call.membership["roles_mask"] = 2
    if case in {"missing_task", "forbidden_and_missing"}:
        del tables["tasks"][1]
    if case == "locked":
        task["state"] = 2
    if case == "blocked_pending":
        task.update(state=3, blocked_from_state=1)
    if case == "bad_version":
        body["expected_version"] = 2
    if case == "missing_member":
        tables["project_members"] = {}
    if case == "bad_capacity":
        tables["iterations"][1]["capacity"] = []
    if case == "self_dependency":
        body["depends_on_task_id"] = 1
    if case == "missing_dependency":
        body["depends_on_task_id"] = 99
    if case == "missing_edge":
        tables["task_dependencies"] = {}
    if case == "wrong_edge_project":
        tables["task_dependencies"][5]["project_id"] = 2
    if case == "empty_versions":
        tables["release_assessments"] = {}
    if case == "bad_risks":
        body["risks"] = []
    if case == "missing_assessment":
        call.path["assessment_id"] = 99
    if case == "self_review":
        assessment["created_by"] = 10
    if case == "stale_schedule":
        assessment["schedule_version"] = 2
    if case == "old_assessment":
        tables["release_assessments"][2] = {
            **assessment,
            "id": 2,
            "rollback_plan_version": 5,
        }
    if case == "bad_assessment_version":
        body["expected_assessment_version"] = 2
    if case == "bad_assessment_status":
        assessment["status"] = 2
    return Gateway(tables), call


CASES = {
    "changeTaskAssignment": [
        "success",
        "blocked_pending",
        "forbidden",
        "forbidden_and_missing",
        "missing_task",
        "locked",
        "missing_member",
        "bad_version",
        "bad_capacity",
    ],
    "addTaskDependency": [
        "success",
        "blocked_pending",
        "forbidden_and_missing",
        "missing_task",
        "locked",
        "duplicate",
        "self_dependency",
        "missing_dependency",
        "bad_version",
    ],
    "removeTaskDependency": [
        "success",
        "blocked_pending",
        "forbidden_and_missing",
        "missing_task",
        "locked",
        "missing_edge",
        "wrong_edge_project",
        "bad_version",
    ],
    "createReleaseAssessment": [
        "success",
        "empty_versions",
        "forbidden_and_missing",
        "missing_task",
        "locked",
        "bad_risks",
        "missing_member",
    ],
    "reviewReleaseAssessment": [
        "success",
        "forbidden_and_missing",
        "missing_task",
        "locked",
        "missing_assessment",
        "self_review",
        "old_assessment",
        "stale_schedule",
        "bad_assessment_version",
        "bad_assessment_status",
    ],
}


def run(owner, operation, case):
    gateway, call = inputs(operation, case)
    try:
        result = ("result", getattr(owner(), operation)(gateway, call))
    except Exception as error:  # noqa: BLE001 -- compare every original service exception exactly.
        result = ("error", type(error).__name__, str(error), vars(error))
    return result, gateway.trace, gateway.tables, call.before, call.after


@pytest.mark.parametrize(
    "operation,case", [(op, case) for op, cases in CASES.items() for case in cases]
)
def test_original_results_errors_query_order_rows_and_audit_diffs_are_identical(
    monkeypatch, operation, case
):
    name = "reviews" if "Assessment" in operation else "tasks"
    current = {"reviews": reviews, "tasks": tasks}[name]
    for target in (current, OLD[name]):
        monkeypatch.setattr(
            target, "model", lambda _name, row, **extra: {**row, **extra}
        )
        monkeypatch.setattr(target, "task_model", copy.deepcopy)
    class_name = "Reviews" if name == "reviews" else "Tasks"
    assert run(getattr(current, class_name), operation, case) == run(
        getattr(OLD[name], class_name), operation, case
    )


def test_guard_priority_fixture_discriminates_state_before_manager_mutant(monkeypatch):
    # Deliberately wrong local mutant only: prove the dual-error fixture detects a reorder.
    class Mutant(tasks.Tasks):
        def changeTaskAssignment(self, g, c):
            c.task(g)
            return super().changeTaskAssignment(g, c)

    monkeypatch.setattr(tasks, "task_model", copy.deepcopy)
    assert run(Mutant, "changeTaskAssignment", "forbidden_and_missing") != run(
        OLD["tasks"].Tasks, "changeTaskAssignment", "forbidden_and_missing"
    )
