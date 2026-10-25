"""Actual RowsGateway/Call callback differential, ordered faults, and immutable policy."""

import json
from copy import deepcopy
from dataclasses import FrozenInstanceError
from datetime import UTC, datetime
from importlib import import_module

import pytest
from t44.persistence import PersistenceUnavailable
from t44.services.application import Business
from t44.services.codes import State
from t44.services.common import Call
from t44.services.errors import Rejected

probe = import_module("tmp.797_backend_operation_plan.probe")
http = import_module("tmp.backend.contracts.986_http")
TABLES = ("tasks", "task_dependencies", "reviews", "release_assessments")


class TraceGateway:
    def __init__(self, gateway, fail_at=None):
        self.gateway, self.fail_at, self.events = gateway, fail_at, []

    def __getattr__(self, name):
        callback = getattr(self.gateway, name)

        def execute(*args, **kwargs):
            self.events.append((name, deepcopy(args), deepcopy(kwargs)))
            if len(self.events) == self.fail_at:
                raise PersistenceUnavailable(f"Injected gateway boundary {self.fail_at}")
            return callback(*args, **kwargs)

        return execute


class RestoreSnapshot(Exception):
    pass


def compare_under_savepoint(gateway, method, call, changes, fail_at=None):
    observed = None
    try:
        with gateway.savepoint():
            if changes:
                gateway.update("tasks", {"id": call.path["task_id"]}, changes)
            trace = TraceGateway(gateway, fail_at)
            try:
                result = method(Business(), trace, call)
                outcome = ("result", result)
            except Rejected as error:
                outcome = ("rejected", error.__dict__)
            except PersistenceUnavailable as error:
                outcome = ("unavailable", str(error))
            observed = {
                "outcome": deepcopy(outcome),
                "events": trace.events,
                "state": {table: gateway.rows(table) for table in TABLES},
                "audit_diff": (call.before, call.after),
            }
            raise RestoreSnapshot
    except RestoreSnapshot:
        return observed


def test_archived_and_candidate_callbacks_keep_order_results_and_fault_boundaries(application):
    client, factory = application
    tokens, project, iteration = http.setup_project(client)
    predecessor = http.create_task(client, tokens, project, iteration)
    task = http.create_task(client, tokens, project, iteration)
    blocked_prestart = {"state": State.BLOCKED, "blocked_from_state": State.PENDING}
    cycle_prestart = {"state": State.BLOCKED, "blocked_from_state": State.DEVELOPING}
    base = probe.methods("baseline")
    candidate = probe.methods("candidate")
    with factory() as uow:
        gateway = uow.gateway
        edge = gateway.insert(
            "task_dependencies",
            {
                "project_id": project,
                "task_id": task["id"],
                "depends_on_task_id": predecessor["id"],
                "created_by": 1,
                "created_at": datetime(2026, 10, 25, tzinfo=UTC),
            },
        )
    scenarios = []

    def scenario(
        operation, name, *, body=None, changes=None, role=None, actor=1, path=None, expected=None
    ):
        review = operation == "createTaskReview"
        default_role = 4 if review else 1
        default_body = {
            "addTaskDependency": {"expected_version": 1, "depends_on_task_id": predecessor["id"]},
            "removeTaskDependency": {"expected_version": 1},
            "createTaskReview": http.review_payload(task),
            "createReleaseAssessment": http.assessment_payload(task),
        }[operation]
        default_state = (
            State.PENDING_REVIEW
            if review
            else (
                State.PENDING_RELEASE if operation == "createReleaseAssessment" else State.PENDING
            )
        )
        call = Call(
            operation=operation,
            request_id="plan-differential",
            token=None,
            path={
                "project_id": project,
                "task_id": task["id"],
                "dependency_id": edge,
                **(path or {}),
            },
            body={**default_body, **(body or {})},
            actor={"actor_id": actor},
            membership={"roles_mask": default_role if role is None else role},
            clock=datetime(2026, 10, 25, 12, tzinfo=UTC),
        )
        scenarios.append(
            (
                operation,
                name,
                call,
                {"state": default_state, "artifact_revision": "a" * 40, **(changes or {})},
                expected,
            )
        )

    for operation in probe.OPERATIONS:
        scenario(
            operation,
            "unauthorized_before_missing_task",
            role=0,
            path={"task_id": 99999},
            expected="ACTION_FORBIDDEN",
        )
        scenario(operation, "missing_task", path={"task_id": 99999}, expected="RESOURCE_NOT_FOUND")
        scenario(
            operation,
            "wrong_project",
            path={"project_id": project + 9},
            expected="RESOURCE_NOT_FOUND",
        )
        scenario(
            operation,
            "state_before_version",
            changes={"state": State.DELIVERED},
            body={"expected_version": 0},
            expected="DEPENDENCY_EDIT_LOCKED"
            if operation.endswith("Dependency")
            else "STATE_CONFLICT",
        )
    for operation in ("addTaskDependency", "removeTaskDependency"):
        scenario(
            operation,
            "blocked_from_developing",
            changes=cycle_prestart,
            expected="DEPENDENCY_EDIT_LOCKED",
        )
    # Existing edge is for task -> predecessor; alternate predecessor is a fresh task.
    alternate = http.create_task(client, tokens, project, iteration)
    scenario("addTaskDependency", "success", body={"depends_on_task_id": alternate["id"]})
    scenario(
        "addTaskDependency",
        "blocked_pending",
        changes=blocked_prestart,
        body={"depends_on_task_id": alternate["id"]},
    )
    scenario(
        "addTaskDependency",
        "duplicate_before_version",
        body={"expected_version": 0},
        expected="STATE_CONFLICT",
    )
    scenario(
        "addTaskDependency",
        "self_before_version",
        body={"depends_on_task_id": task["id"], "expected_version": 0},
        expected="DEPENDENCY_SELF_REFERENCE",
    )
    scenario(
        "addTaskDependency",
        "missing_predecessor_before_version",
        body={"depends_on_task_id": 99999, "expected_version": 0},
        expected="RESOURCE_NOT_FOUND",
    )
    scenario(
        "addTaskDependency",
        "cycle_before_version",
        path={"task_id": predecessor["id"]},
        body={"depends_on_task_id": task["id"], "expected_version": 0},
        expected="DEPENDENCY_CYCLE",
    )
    scenario(
        "addTaskDependency",
        "stale_version",
        body={"depends_on_task_id": alternate["id"], "expected_version": 0},
        expected="VERSION_CONFLICT",
    )
    scenario(
        "addTaskDependency",
        "version_overflow",
        changes={"version": 2147483647},
        body={"depends_on_task_id": alternate["id"], "expected_version": 2147483647},
        expected="VERSION_CONFLICT",
    )
    scenario("removeTaskDependency", "success")
    scenario("removeTaskDependency", "blocked_pending", changes=blocked_prestart)
    scenario(
        "removeTaskDependency",
        "missing_edge_before_version",
        path={"dependency_id": 99999},
        body={"expected_version": 0},
        expected="RESOURCE_NOT_FOUND",
    )
    scenario(
        "removeTaskDependency",
        "wrong_task_edge",
        path={"task_id": alternate["id"]},
        expected="RESOURCE_NOT_FOUND",
    )
    scenario(
        "removeTaskDependency",
        "stale_version",
        body={"expected_version": 0},
        expected="VERSION_CONFLICT",
    )
    scenario("createTaskReview", "success")
    scenario(
        "createTaskReview",
        "owner_before_state",
        actor=2,
        changes={"state": State.DELIVERED},
        expected="ACTION_FORBIDDEN",
    )
    scenario(
        "createTaskReview",
        "template_before_version",
        body={"template_version": 2, "expected_version": 0},
        expected="REVIEW_BASELINE_MISMATCH",
    )
    scenario(
        "createTaskReview",
        "artifact_before_shape",
        body={"artifact_revision": "b" * 40, "sections": []},
        expected="REVIEW_BASELINE_MISMATCH",
    )
    scenario(
        "createTaskReview", "missing_sections", body={"sections": []}, expected="PARAMETER_INVALID"
    )
    checklist = http.review_payload(task)["checklist"]
    scenario(
        "createTaskReview",
        "duplicate_items",
        body={"checklist": checklist + checklist},
        expected="PARAMETER_INVALID",
    )
    no_evidence = [{**item, "evidence": []} for item in checklist]
    scenario(
        "createTaskReview",
        "passing_without_evidence",
        body={"checklist": no_evidence, "expected_version": 0},
        expected="EVIDENCE_REQUIRED",
    )
    scenario(
        "createTaskReview",
        "rejected_verdict_without_evidence",
        body={"checklist": no_evidence, "verdict": 2},
    )
    scenario(
        "createTaskReview",
        "stale_version",
        body={"expected_version": 0},
        expected="VERSION_CONFLICT",
    )
    scenario("createReleaseAssessment", "success")
    scenario(
        "createReleaseAssessment",
        "risks_before_member_and_version",
        body={"risks": [], "rollback_plan": {"responsible_user_id": 99999}, "expected_version": 0},
        expected="PARAMETER_INVALID",
    )
    scenario(
        "createReleaseAssessment",
        "missing_responsible_before_version",
        body={"rollback_plan": {"responsible_user_id": 99999}, "expected_version": 0},
        expected="RESOURCE_NOT_FOUND",
    )
    scenario(
        "createReleaseAssessment",
        "outsider_responsible",
        body={"rollback_plan": {"responsible_user_id": 4}},
        expected="RESOURCE_NOT_FOUND",
    )
    scenario(
        "createReleaseAssessment",
        "stale_version",
        body={"expected_version": 0},
        expected="VERSION_CONFLICT",
    )

    receipt = {
        "base": "f4bd382d4668130793fc553df9ce6363c4656ea6",
        "scenario_comparisons": [],
        "gateway_fault_comparisons": [],
    }
    for operation, name, call, changes, expected in scenarios:
        with factory() as uow:
            original = compare_under_savepoint(
                uow.gateway, base[operation], deepcopy(call), changes
            )
            actual = compare_under_savepoint(
                uow.gateway, candidate[operation], deepcopy(call), changes
            )
            assert original == actual, (operation, name)
            if expected:
                assert original["outcome"][0] == "rejected"
                assert original["outcome"][1]["code"] == expected
            else:
                assert original["outcome"][0] == "result", (operation, name, original["outcome"])
            receipt["scenario_comparisons"].append(
                {
                    "operation": operation,
                    "name": name,
                    "gateway_events": len(original["events"]),
                    "outcome": original["outcome"][0],
                }
            )
            if name == "success":
                for stop in range(1, len(original["events"]) + 1):
                    before = compare_under_savepoint(
                        uow.gateway, base[operation], deepcopy(call), changes, stop
                    )
                    after = compare_under_savepoint(
                        uow.gateway, candidate[operation], deepcopy(call), changes, stop
                    )
                    assert before == after, (operation, stop)
                    assert before["outcome"][0] == "unavailable"
                    assert len(before["events"]) == stop
                    receipt["gateway_fault_comparisons"].append(
                        {
                            "operation": operation,
                            "stop": stop,
                            "last_event": {
                                "method": before["events"][-1][0],
                                "table": before["events"][-1][1][0],
                            },
                        }
                    )
    (probe.HERE / "differential.json").write_text(json.dumps(receipt, indent=2) + "\n")


def test_plan_policy_is_immutable_and_does_not_capture_request_state():
    probe.modules("candidate")
    plan_type = import_module("t44.services.operation_plan").OperationPlan
    plan = plan_type(Call.manager)
    with pytest.raises(FrozenInstanceError):
        plan.authorize = Call.reviewer
    assert vars(plan) == {"authorize": Call.manager}
    assert vars(probe.methods("candidate")["addTaskDependency"])["__wrapped__"].__name__ == (
        "addTaskDependency"
    )
