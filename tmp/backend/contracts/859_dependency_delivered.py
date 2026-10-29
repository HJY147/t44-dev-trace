"""Nonempty dependency acceptance through HTTP; SQLite, not MySQL or load evidence."""

from importlib import import_module

import pytest

http = import_module("tmp.backend.contracts.986_http")
pytestmark = pytest.mark.contract


def _deliver(client, tokens, project_id, task):
    task = http.transition(client, tokens["developer"], project_id, task, 1)
    task = http.transition(
        client,
        tokens["developer"],
        project_id,
        task,
        4,
        artifact_revision="a" * 40,
        evidence=http.EVIDENCE,
    )
    result = http.request(
        client,
        "createTaskReview",
        token=tokens["reviewer"],
        project_id=project_id,
        task_id=task["id"],
        body=http.review_payload(task),
        expect=201,
    ).json()["data"]
    task = http.transition(
        client,
        tokens["reviewer"],
        project_id,
        result["task"],
        5,
        review_id=result["review"]["id"],
        review_version=result["review"]["version"],
    )
    result = http.request(
        client,
        "createReleaseAssessment",
        token=tokens["manager"],
        project_id=project_id,
        task_id=task["id"],
        body=http.assessment_payload(task),
        expect=201,
    ).json()["data"]
    result = http.request(
        client,
        "reviewReleaseAssessment",
        token=tokens["reviewer"],
        project_id=project_id,
        task_id=task["id"],
        assessment_id=result["assessment"]["id"],
        body={
            "expected_version": result["task"]["version"],
            "expected_assessment_version": result["assessment"]["version"],
            "verdict": 1,
            "reason": "Independent synthetic approval",
            "evidence": http.EVIDENCE,
        },
        expect=200,
    ).json()["data"]
    task = http.transition(
        client,
        tokens["manager"],
        project_id,
        result["task"],
        7,
        assessment_id=result["assessment"]["id"],
        assessment_version=result["assessment"]["version"],
        release_version="synthetic-dependency-v1",
        reason="Release predecessor for dependency acceptance",
        evidence=http.EVIDENCE,
    )
    assert task["state"] == 6
    return task


def test_nonempty_dependencies_require_all_delivered_then_allow_start(application):
    client, _ = application
    tokens, project_id, iteration_id = http.setup_project(client)
    predecessors = [http.create_task(client, tokens, project_id, iteration_id) for _ in range(2)]
    dependent = http.create_task(
        client, tokens, project_id, iteration_id, [task["id"] for task in predecessors]
    )

    def dependencies():
        return http.request(
            client,
            "listTaskDependencies",
            token=tokens["developer"],
            project_id=project_id,
            task_id=dependent["id"],
            expect=200,
        ).json()["data"]["items"]

    def current_dependent():
        return http.request(
            client,
            "getTask",
            token=tokens["developer"],
            project_id=project_id,
            task_id=dependent["id"],
            expect=200,
        ).json()["data"]

    original_edges = dependencies()
    assert len(original_edges) == 2
    assert {edge["depends_on_task_id"] for edge in original_edges} == {
        task["id"] for task in predecessors
    }
    assert all(edge["satisfied"] is False for edge in original_edges)

    for completed, predecessor in enumerate(predecessors):
        edges = dependencies()
        assert sum(edge["satisfied"] for edge in edges) == completed
        rejected = http.transition(
            client, tokens["developer"], project_id, dependent, 1, expect=409
        )
        assert rejected.json()["code"] == "DEPENDENCIES_UNSATISFIED"
        assert current_dependent() == dependent
        assert dependencies() == edges
        _deliver(client, tokens, project_id, predecessor)

    ready_edges = dependencies()
    assert len(ready_edges) == 2
    assert all(edge["satisfied"] is True for edge in ready_edges)
    assert [edge["id"] for edge in ready_edges] == [edge["id"] for edge in original_edges]
    assert current_dependent() == dependent
    started = http.transition(client, tokens["developer"], project_id, dependent, 1)
    assert started["state"] == 2
    assert started["version"] == dependent["version"] + 1
    assert current_dependent() == started
    assert dependencies() == ready_edges
