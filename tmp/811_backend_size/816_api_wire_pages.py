"""Explicit real SQLite public pages for render CPU measurements; no external service."""

from importlib import import_module

application = import_module("tmp.backend.contracts.conftest").application
http = import_module("tmp.backend.contracts.986_http")


def test_public_twenty_and_hundred_task_pages(application):
    client, _ = application
    tokens, project_id, iteration_id = http.setup_project(client)
    task = None
    for index in range(100):
        task = http.create_task(client, tokens, project_id, iteration_id)
        if index == 19:
            page = http.request(
                client,
                "listTasks",
                token=tokens["manager"],
                project_id=project_id,
                query={"page_size": 20},
                expect=200,
            ).json()["data"]
            assert len(page["items"]) == page["total"] == 20
    page = http.request(
        client,
        "listTasks",
        token=tokens["manager"],
        project_id=project_id,
        query={"page_size": 100},
        expect=200,
    ).json()["data"]
    assert len(page["items"]) == page["total"] == 100
    http.request(
        client,
        "getTask",
        token=tokens["manager"],
        project_id=project_id,
        task_id=task["id"],
        expect=200,
    )
