"""Synthetic fixtures are checked against business references and frozen JSON shapes."""

import hashlib
from datetime import UTC, datetime
from importlib.resources import files

import pytest
from sqlalchemy import create_engine, event
from t44.contracts import validator
from t44.persistence import SqlAlchemyUnitOfWorkFactory, StatementRejected
from t44.persistence.schema import metadata
from t44.persistence.seed import seed_demo
from t44.services.common import model, plan, task_model


@pytest.fixture
def seed_factory(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'seed.sqlite'}")
    event.listen(engine, "connect", lambda conn, _: conn.execute("PRAGMA foreign_keys=ON"))
    metadata.create_all(engine)
    factory = SqlAlchemyUnitOfWorkFactory(engine)
    factory.seed_statements, factory.seed_commits = [], []
    event.listen(
        engine,
        "before_cursor_execute",
        lambda conn, cursor, statement, parameters, context, many: factory.seed_statements.append(
            (statement, many)
        ),
    )
    event.listen(engine, "commit", lambda conn: factory.seed_commits.append(True))
    yield factory
    engine.dispose()


def assert_consistent(factory):
    with factory() as uow:
        g = uow.gateway
        tasks = {t["id"]: t for t in g.rows("tasks")}
        reviews = {r["id"]: r for r in g.rows("reviews")}
        assessments = {a["id"]: a for a in g.rows("release_assessments")}
        decisions = g.rows("decisions")
        template_hash = hashlib.sha256(
            files("t44").joinpath("resources/review-template.json").read_bytes()
        ).digest()
        assert set(t["state"] for t in tasks.values()) == set(range(1, 8))
        for edge in g.rows("task_dependencies"):
            child, parent = tasks[edge["task_id"]], tasks[edge["depends_on_task_id"]]
            assert edge["project_id"] == child["project_id"] == parent["project_id"]
            assert parent["id"] < child["id"] and parent["state"] == 6
            assert parent["planned_end"] <= child["planned_start"]
        checks = {
            name: validator({"$ref": f"#/components/schemas/{name}"})
            for name in ("Task", "Review", "ReleaseAssessment", "Decision", "Iteration")
        }
        for task in tasks.values():
            checks["Task"].validate(task_model(task))
            history = sorted(
                (r for r in reviews.values() if r["task_id"] == task["id"]),
                key=lambda r: r["review_cycle"],
            )
            assert [r["review_cycle"] for r in history] == list(range(1, len(history) + 1))
            if task["state"] in (1, 2, 3):
                assert (
                    not history and not task["artifact_revision"] and not task["approved_review_id"]
                )
            if task["state"] in (6, 7):
                assert task["approved_review_id"] and task["approved_assessment_id"]
                types = {d["type"] for d in decisions if d["task_id"] == task["id"]}
                assert types == ({1} if task["state"] == 6 else {1, 2})
            if task["latest_review_id"]:
                r = reviews[task["latest_review_id"]]
                assert (
                    r["task_id"],
                    r["delivery_cycle"],
                    r["review_cycle"],
                    r["artifact_revision"],
                ) == (
                    task["id"],
                    task["delivery_cycle"],
                    task["review_cycle"],
                    task["artifact_revision"],
                )
            if task["approved_review_id"]:
                assert reviews[task["approved_review_id"]]["verdict"] == 1
            if task["approved_assessment_id"]:
                a = assessments[task["approved_assessment_id"]]
                assert a["status"] == 2 and a["version"] == task["approved_assessment_version"]
                assert (a["task_id"], a["schedule_version"], a["delivery_cycle"]) == (
                    task["id"],
                    task["schedule_version"],
                    task["delivery_cycle"],
                )
        for r in reviews.values():
            checks["Review"].validate(model("Review", r))
            assert r["template_hash"] == template_hash
            assert r["reviewer_id"] != tasks[r["task_id"]]["owner_id"]
            assert len({s["section_id"] for s in r["sections"]}) == 8
            assert len({i["item_id"] for i in r["checklist"]}) == 10
            assert all(
                "synthetic" in e["description"] for s in r["sections"] for e in s["evidence"]
            )
            assert r["verdict"] != 1 or all(
                i["judgment"] == 1 and i["evidence"] for i in r["checklist"]
            )
        for a in assessments.values():
            checks["ReleaseAssessment"].validate(model("ReleaseAssessment", a))
            assert {r["perspective"] for r in a["risks"]} == {1, 2, 3, 4}
            assert a["reviewed_by"] != a["created_by"]
        for d in decisions:
            checks["Decision"].validate(model("Decision", d))
            t, a = tasks[d["task_id"]], assessments[d["assessment_id"]]
            assert d["delivery_cycle"] == t["delivery_cycle"] == a["delivery_cycle"]
            assert d["rollback_plan_version"] == a["rollback_plan_version"]
            if d["type"] == 2:
                assert d["target_version"] == a["rollback_plan"]["target_version"]
                assert any(
                    old["task_id"] == d["task_id"]
                    and old["type"] == 1
                    and old["assessment_id"] == d["assessment_id"]
                    for old in decisions
                )
        for iteration in g.rows("iterations"):
            checks["Iteration"].validate(
                model("Iteration", iteration, plan=plan(iteration, iteration=True))
            )
            capacity = sum(entry["available_hours"] for entry in iteration["capacity"])
            load = sum(
                (t["estimated_quarters"] + t["buffer_quarters"]) / 4
                for t in tasks.values()
                if t["iteration_id"] == iteration["id"]
            )
            assert load + iteration["buffer_quarters"] / 4 <= capacity
    return {
        "tasks": len(tasks),
        "reviews": len(reviews),
        "decisions": len(decisions),
        "states": sorted({t["state"] for t in tasks.values()}),
    }


def test_seed_references_json_states_capacity_repeat_and_no_overwrite(seed_factory):
    args = dict(
        projects=2,
        tasks=20,
        dependencies=20,
        records=30,
        anchor_at=datetime(2026, 10, 23, tzinfo=UTC),
    )
    first = seed_demo(seed_factory, **args)
    assert len(seed_factory.seed_commits) == 1
    assert any("INSERT INTO tasks" in sql and many for sql, many in seed_factory.seed_statements)
    assert any("UPDATE tasks" in sql and many for sql, many in seed_factory.seed_statements)
    assert first["reviews"] + first["decisions"] == 30
    assert_consistent(seed_factory)
    assert seed_demo(seed_factory, **args)["already_seeded"]
    with pytest.raises(StatementRejected):
        seed_demo(seed_factory, **args, seed=45)
    with seed_factory() as uow:
        assert uow.gateway.count("tasks") == 20


def test_seed_impossible_dependency_count_rolls_back_entire_dataset(seed_factory):
    with pytest.raises(ValueError, match="capacity"):
        seed_demo(seed_factory, projects=1, tasks=10, dependencies=1000, records=20)
    with seed_factory() as uow:
        assert uow.gateway.count("users") == uow.gateway.count("projects") == 0
