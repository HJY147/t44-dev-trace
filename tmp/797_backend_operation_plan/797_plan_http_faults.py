"""Real SQLite HTTP rollback/replay for opposite create/CAS dependency/review orders."""

from importlib import import_module
from uuid import uuid4

import pytest
from t44.persistence import PersistenceUnavailable

http = import_module("tmp.backend.contracts.986_http")


def prepare(client, operation):
    tokens, project, iteration = http.setup_project(client)
    task = http.create_task(client, tokens, project, iteration)
    path = {"project_id": project, "task_id": task["id"]}
    actor = "manager"
    if operation.endswith("Dependency"):
        predecessor = http.create_task(client, tokens, project, iteration)
        body = {
            "expected_version": task["version"],
            "reason": "Synthetic plan fault",
            "depends_on_task_id": predecessor["id"],
        }
        if operation == "removeTaskDependency":
            data = http.request(
                client, "addTaskDependency", token=tokens[actor], body=body, expect=201, **path
            ).json()["data"]
            body = {"expected_version": data["task"]["version"], "reason": body["reason"]}
            path["dependency_id"] = data["dependency"]["id"]
    else:
        task = http.transition(client, tokens["developer"], project, task, 1)
        task = http.transition(
            client,
            tokens["developer"],
            project,
            task,
            4,
            artifact_revision="a" * 40,
            evidence=http.EVIDENCE,
        )
        body = http.review_payload(task)
        if operation == "createTaskReview":
            actor = "reviewer"
        else:
            reviewed = http.request(
                client, "createTaskReview", token=tokens["reviewer"], body=body, expect=201, **path
            ).json()["data"]
            task = http.transition(
                client,
                tokens["reviewer"],
                project,
                reviewed["task"],
                5,
                review_id=reviewed["review"]["id"],
                review_version=1,
            )
            body = http.assessment_payload(task)
    return tokens[actor], path, body


class FaultFactory:
    def __init__(self, underlying, method, table):
        self.underlying, self.method, self.table = underlying, method, table

    def __call__(self):
        source = self.underlying()
        parent = self

        class Scope:
            def __enter__(self):
                source.__enter__()
                return self

            @property
            def gateway(self):
                original = source.gateway

                class Gateway:
                    def __getattr__(self, name):
                        callback = getattr(original, name)

                        def execute(*args, **kwargs):
                            if name == parent.method and args[0] == parent.table:
                                raise PersistenceUnavailable("Synthetic OperationPlan fault")
                            return callback(*args, **kwargs)

                        return execute

                return Gateway()

            def __exit__(self, typ, value, traceback):
                return source.__exit__(typ, value, traceback)

        return Scope()


def business_snapshot(factory):
    with factory() as uow:
        return {
            table: uow.gateway.rows(table)
            for table in (
                "tasks",
                "task_dependencies",
                "reviews",
                "release_assessments",
                "outbox_events",
            )
        }


@pytest.mark.parametrize(
    "operation,method,table",
    [
        ("addTaskDependency", "insert", "task_dependencies"),
        ("removeTaskDependency", "delete", "task_dependencies"),
        ("createTaskReview", "update", "tasks"),
        ("createReleaseAssessment", "update", "tasks"),
    ],
)
@pytest.mark.parametrize("outbox", [False, True])
def test_original_callback_faults_roll_back_then_retry_and_replay(
    application, operation, method, table, outbox
):
    client, factory = application
    token, path, body = prepare(client, operation)
    before = business_snapshot(factory)
    with factory() as uow:
        audit_before = uow.gateway.count("audit_events")
    runtime = client.app.state.runtime
    runtime.factory = FaultFactory(
        factory, "insert" if outbox else method, "outbox_events" if outbox else table
    )
    failed_key = str(uuid4())
    rejected = http.request(
        client, operation, token=token, body=body, key=failed_key, expect=503, **path
    ).json()
    assert rejected["code"] == "DEPENDENCY_UNAVAILABLE"
    assert rejected["audit_id"] is not None
    assert business_snapshot(factory) == before
    with factory() as uow:
        assert uow.gateway.count("audit_events") == audit_before + 1
        event = uow.gateway.get("audit_events", rejected["audit_id"])
        assert event["outcome"] == 2
        assert event["before_values"] == event["after_values"] == []
        claimed = uow.gateway.rows("idempotency_requests", {"idempotency_key": failed_key})
        assert len(claimed) == 1 and claimed[0]["status"] == 1
    runtime.factory = factory
    retry_key = str(uuid4())
    success = 200 if operation == "removeTaskDependency" else 201
    first = http.request(
        client, operation, token=token, body=body, key=retry_key, expect=success, **path
    ).json()
    after = business_snapshot(factory)
    replay = http.request(
        client, operation, token=token, body=body, key=retry_key, expect=success, **path
    ).json()
    assert first["data"] == replay["data"]
    assert replay["meta"]["replayed"] is True
    assert business_snapshot(factory) == after
    with factory() as uow:
        assert uow.gateway.count("audit_events") == audit_before + 2
        complete = uow.gateway.rows("idempotency_requests", {"idempotency_key": retry_key})
        assert len(complete) == 1 and complete[0]["status"] == 2
