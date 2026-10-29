"""Developer differential checks; not independent acceptance or database locking evidence."""

import subprocess
from copy import deepcopy
from datetime import UTC, datetime
from types import ModuleType

import pytest
from t44.services import reviews
from t44.services.common import Call
from t44.services.errors import Rejected

BASE = "a92e5e73da93ba23748c3bab113103036c395d50"


def original_reviews():
    source = subprocess.check_output(
        ["git", "show", f"{BASE}:backend/t44/services/reviews.py"], text=True
    )
    module = ModuleType("t44.services._assessment_query_original")
    exec(compile(source, f"{BASE}/reviews.py", "exec"), module.__dict__)
    return module


class Gateway:
    def __init__(self, task, assessment, latest, responsible):
        self.trace = []
        self.tables = {"tasks": {task["id"]: task}, "release_assessments": {}}
        if assessment:
            self.tables["release_assessments"][assessment["id"]] = assessment
        self.latest, self.responsible = latest, responsible

    def get(self, table, identifier, **options):
        self.trace.append(("get", table, identifier, options))
        return deepcopy(self.tables[table].get(identifier))

    def rows(self, table, where, **options):
        self.trace.append(("rows", table, where, options))
        return deepcopy(self.responsible if table == "project_members" else self.latest)

    def insert(self, table, values):
        self.trace.append(("insert", table, deepcopy(values)))
        identifier = 100
        self.tables[table][identifier] = {"id": identifier, "version": 1, **values}
        return identifier

    def update(self, table, where, values):
        self.trace.append(("update", table, deepcopy(where), deepcopy(values)))
        row = self.tables[table][where["id"]]
        if row["version"] != where["version"]:
            return 0
        row.update(values)
        return 1


def invoke(module, operation, scenario):
    task = {
        "id": 8,
        "project_id": 3,
        "version": 4,
        "state": 5,
        "schedule_version": 2,
        "delivery_cycle": 1,
        "approved_assessment_id": 9,
        "approved_assessment_version": 1,
    }
    assessment = {
        "id": 9,
        "project_id": 3,
        "task_id": 8,
        "version": 1,
        "status": 1,
        "created_by": 12,
        "schedule_version": 2,
        "delivery_cycle": 1,
        "rollback_plan_version": 7,
    }
    body = {
        "expected_version": 4,
        "expected_assessment_version": 1,
        "verdict": 1,
        "reason": "Synthetic developer regression",
        "evidence": [{"kind": 2, "locator": "self-test/evidence"}],
        "risks": [{"perspective": value} for value in (1, 2, 3, 4)],
        "rollback_plan": {"responsible_user_id": 12},
    }
    actor, role, responsible, latest = 11, 5, [{"user_id": 12}], [deepcopy(assessment)]
    if scenario == "empty":
        latest = []
    elif scenario == "forbidden":
        role = 2
    elif scenario == "state":
        task["state"] = 4
    elif scenario == "responsible":
        responsible = []
    elif scenario == "risk":
        body["risks"] = []
    elif scenario == "self":
        actor = 12
    elif scenario == "status":
        assessment["status"] = 2
    elif scenario == "latest":
        latest[0]["id"] = 10
    elif scenario == "baseline":
        assessment["schedule_version"] = 1
    elif scenario == "assessment_version":
        body["expected_assessment_version"] = 2
    elif scenario == "task_version":
        body["expected_version"] = 3
    elif scenario == "reject":
        body["verdict"] = 2
    call = Call(operation, "self-test", None, path={"project_id": 3, "task_id": 8})
    call.path["assessment_id"] = 9
    call.actor = {"actor_id": actor}
    call.membership = {"roles_mask": role}
    call.clock = datetime(2026, 10, 29, tzinfo=UTC)
    call.body = body
    gateway = Gateway(task, assessment, latest, responsible)
    # Isolate query/guard/CAS behavior; full contract serialization runs in HTTP self-tests.
    module.task_model = lambda row: deepcopy(row)
    module.model = lambda name, row: {"schema": name, **deepcopy(row)}
    try:
        result = getattr(module.Reviews(), operation)(gateway, call)
        outcome = ("success", result)
    except Rejected as error:
        outcome = ("rejected", error.code, error.status, error.current_version)
    except IndexError:
        outcome = ("IndexError",)
    return outcome, gateway.trace, gateway.tables, call.before, call.after


@pytest.mark.parametrize(
    ("operation", "scenario", "expected"),
    [
        ("createReleaseAssessment", "normal", "success"),
        ("createReleaseAssessment", "empty", "success"),
        ("createReleaseAssessment", "forbidden", "ACTION_FORBIDDEN"),
        ("createReleaseAssessment", "state", "STATE_CONFLICT"),
        ("createReleaseAssessment", "risk", "PARAMETER_INVALID"),
        ("createReleaseAssessment", "responsible", "RESOURCE_NOT_FOUND"),
        ("createReleaseAssessment", "task_version", "VERSION_CONFLICT"),
        ("reviewReleaseAssessment", "normal", "success"),
        ("reviewReleaseAssessment", "reject", "success"),
        ("reviewReleaseAssessment", "empty", "IndexError"),
        ("reviewReleaseAssessment", "forbidden", "ACTION_FORBIDDEN"),
        ("reviewReleaseAssessment", "self", "ACTION_FORBIDDEN"),
        ("reviewReleaseAssessment", "state", "STATE_CONFLICT"),
        ("reviewReleaseAssessment", "status", "STATE_CONFLICT"),
        ("reviewReleaseAssessment", "latest", "ASSESSMENT_BASELINE_MISMATCH"),
        ("reviewReleaseAssessment", "baseline", "ASSESSMENT_BASELINE_MISMATCH"),
        ("reviewReleaseAssessment", "assessment_version", "VERSION_CONFLICT"),
        ("reviewReleaseAssessment", "task_version", "VERSION_CONFLICT"),
    ],
)
def test_behavior_and_query_order_match(monkeypatch, operation, scenario, expected):
    baseline = invoke(original_reviews(), operation, scenario)
    with monkeypatch.context() as patch:
        patch.setattr(reviews, "model", reviews.model)
        patch.setattr(reviews, "task_model", reviews.task_model)
        candidate = invoke(reviews, operation, scenario)
    assert candidate == baseline
    outcome = candidate[0]
    assert (outcome[1] if outcome[0] == "rejected" else outcome[0]) == expected
    queries = [entry for entry in candidate[1] if entry[:2] == ("rows", "release_assessments")]
    if queries:
        assert queries == [
            (
                "rows",
                "release_assessments",
                {"task_id": 8},
                {"order_by": ("-rollback_plan_version",), "limit": 1},
            )
        ]
