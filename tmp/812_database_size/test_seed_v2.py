"""Current-version synthetic fixtures: independent relational and chronology properties."""

import importlib.util
import json
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import Mock

import pytest
from sqlalchemy import create_engine, event
from t44.persistence import SqlAlchemyUnitOfWorkFactory, StatementRejected
from t44.persistence.schema import TABLES, metadata
from t44.persistence.seed import OPERATION, VERSION, seed_demo

spec = importlib.util.spec_from_file_location(
    "seed_properties", Path(__file__).parents[1] / "backend/persistence/975_seed.py"
)
properties = importlib.util.module_from_spec(spec)
spec.loader.exec_module(properties)
seed_factory = properties.seed_factory
AT = datetime(2026, 10, 23, tzinfo=UTC)


def snapshot(factory):
    with factory() as uow:
        return {name: uow.gateway.rows(name) for name in TABLES}


def assert_full_properties(factory):
    properties.assert_consistent(factory)
    data = snapshot(factory)
    for table in TABLES.values():
        for foreign in table.foreign_key_constraints:
            parent = foreign.referred_table.name
            targets = {tuple(row[e.column.name] for e in foreign.elements) for row in data[parent]}
            for row in data[table.name]:
                values = tuple(row[e.parent.name] for e in foreign.elements)
                assert any(v is None for v in values) or values in targets, foreign.name
    projects = {p["id"]: p for p in data["projects"]}
    tasks = {t["id"]: t for t in data["tasks"]}
    reviews = {r["id"]: r for r in data["reviews"]}
    assessments = {a["id"]: a for a in data["release_assessments"]}
    iterations = {i["id"]: i for i in data["iterations"]}
    deliveries = {d["task_id"]: d for d in data["decisions"] if d["type"] == 1}
    for task in tasks.values():
        iteration = iterations[task["iteration_id"]]
        assert task["project_id"] == iteration["project_id"]
        assert (
            iteration["planned_start"]
            <= task["planned_start"]
            < task["planned_end"]
            <= iteration["planned_end"]
        )
        assert (
            projects[task["project_id"]]["created_at"]
            <= task["created_at"]
            <= task["planned_start"]
        )
        assert type(task["version"]) is int and task["version"] >= task["review_cycle"] >= 1
        assert (task["blocked_from_state"] is not None) == (task["state"] == 3)
        if task["latest_review_id"]:
            last = reviews[task["latest_review_id"]]
            assert task["review_cycle"] == last["review_cycle"]
            assert (
                last["verdict"] == 1
                and task["planned_start"] <= last["created_at"] <= task["planned_end"]
            )
    for review in reviews.values():
        task = tasks[review["task_id"]]
        assert task["created_at"] <= task["planned_start"] <= review["created_at"] <= AT
    for assessment in assessments.values():
        task = tasks[assessment["task_id"]]
        assert reviews[task["approved_review_id"]]["created_at"] <= assessment["created_at"]
        assert assessment["rollback_plan"]["responsible_user_id"] == task["owner_id"]
        if assessment["status"] == 1:
            assert all(
                assessment[key] is None for key in ("reviewed_by", "reviewed_at", "review_reason")
            )
            assert assessment["review_evidence"] == []
        else:
            assert assessment["created_at"] <= assessment["reviewed_at"] <= AT
            assert assessment["reviewed_by"] != task["owner_id"]
    for decision in data["decisions"]:
        assessment = assessments[decision["assessment_id"]]
        assert (
            assessment["status"] == 2 and assessment["reviewed_at"] <= decision["decided_at"] <= AT
        )
        if decision["type"] == 2:
            assert deliveries[decision["task_id"]]["decided_at"] <= decision["decided_at"]
    for edge in data["task_dependencies"]:
        assert (
            deliveries[edge["depends_on_task_id"]]["decided_at"]
            <= tasks[edge["task_id"]]["planned_start"]
        )
    for project in projects:
        roles = {
            m["roles_mask"]: m["user_id"]
            for m in data["project_members"]
            if m["project_id"] == project
        }
        assert set(roles) == {1, 2, 4} and len(set(roles.values())) == 3
    return data


@pytest.mark.parametrize(
    "projects,tasks,dependencies,records", [(2, 20, 20, 30), (40, 6000, 9000, 15000)]
)
def test_v2_full_semantics_replay_and_batch_order(
    seed_factory, tmp_path, projects, tasks, dependencies, records
):
    args = dict(
        projects=projects, tasks=tasks, dependencies=dependencies, records=records, anchor_at=AT
    )
    first = seed_demo(seed_factory, **args)
    assert len(seed_factory.seed_commits) == 1
    assert VERSION == 2 and first["manifest"]["version"] == VERSION
    data = assert_full_properties(seed_factory)
    assert len(data["projects"]) == projects and len(data["tasks"]) == tasks
    assert len(data["task_dependencies"]) == dependencies
    assert len(data["reviews"]) + len(data["decisions"]) == records
    assert set(t["state"] for t in data["tasks"]) == set(range(1, 8))
    if tasks == 6000:
        assert {a["status"] for a in data["release_assessments"]} == {1, 2, 3}
    inserts = [
        sql.split()[2].split("(")[0]
        for sql, _ in seed_factory.seed_statements
        if sql.startswith("INSERT")
    ]
    positions = {name: i for i, name in enumerate(TABLES)}
    assert [positions[name] for name in inserts] == sorted(positions[name] for name in inserts)
    statements = [sql for sql, _ in seed_factory.seed_statements]
    assert min(i for i, sql in enumerate(statements) if sql.startswith("UPDATE")) > max(
        i for i, sql in enumerate(statements) if sql.startswith("INSERT")
    )
    digest = properties.persisted_digest(seed_factory)
    engine = create_engine(f"sqlite:///{tmp_path / 'replay.sqlite'}")
    event.listen(engine, "connect", lambda conn, _: conn.execute("PRAGMA foreign_keys=ON"))
    metadata.create_all(engine)
    try:
        replay = SqlAlchemyUnitOfWorkFactory(engine)
        repeat = seed_demo(replay, **args, batch_size=127)
        assert first == repeat and properties.persisted_digest(replay) == digest
    finally:
        engine.dispose()
    assert seed_demo(seed_factory, **args)["already_seeded"]
    assert properties.persisted_digest(seed_factory) == digest
    print(json.dumps(dict(version=VERSION, tasks=tasks, semantics_sha256=digest)))


@pytest.mark.parametrize("marker", ["syntheticSeedV1", OPERATION])
def test_v1_or_incompatible_marker_is_rejected_without_overwrite(seed_factory, marker):
    args = dict(projects=1, tasks=10, dependencies=5, records=20, anchor_at=AT)
    seed_demo(seed_factory, **args)
    with seed_factory() as uow:
        row = uow.gateway.rows("audit_events", {"operation_id": OPERATION})[0]
        manifest = json.loads(row["after_values"][0]["value"])
        manifest["version"] = 1
        uow.gateway.update(
            "audit_events",
            {"id": row["id"]},
            {
                "operation_id": marker,
                "after_values": [{"field": "seed_manifest", "value": json.dumps(manifest)}],
            },
        )
    before = properties.persisted_digest(seed_factory)
    with pytest.raises(StatementRejected):
        seed_demo(seed_factory, **args)
    assert properties.persisted_digest(seed_factory) == before


@pytest.mark.parametrize(
    "changes",
    [
        {"projects": 0},
        {"tasks": True},
        {"dependencies": -1},
        {"records": 1.0},
        {"batch_size": False},
        {"seed": "44"},
        {"tasks": 21},
        {"tasks": 8},
    ],
)
def test_invalid_parameters_never_open_a_unit(changes):
    factory = Mock(side_effect=AssertionError("Invalid input must not touch persistence"))
    with pytest.raises(ValueError):
        seed_demo(factory, **{**dict(projects=2, tasks=20, dependencies=20, records=30), **changes})
    factory.assert_not_called()


def test_insufficient_record_budget_rolls_back_users_and_all_business_rows(seed_factory):
    with pytest.raises(ValueError, match="Record count"):
        seed_demo(seed_factory, projects=1, tasks=10, dependencies=5, records=1, anchor_at=AT)
    assert all(rows == [] for rows in snapshot(seed_factory).values())
