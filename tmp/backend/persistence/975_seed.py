"""Synthetic fixtures are checked against business references and frozen JSON shapes."""

import hashlib
import json
import os
import tempfile
from datetime import UTC, datetime
from importlib.resources import files
from pathlib import Path

import pytest
from sqlalchemy import create_engine, event, text
from t44.contracts import validator
from t44.persistence import (
    MySQLSettings,
    PersistenceIntegrityError,
    SqlAlchemyUnitOfWorkFactory,
    StatementRejected,
    create_mysql_engine,
    migrations,
)
from t44.persistence.schema import TABLES, metadata
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
        histories, decision_types = {tid: [] for tid in tasks}, {tid: set() for tid in tasks}
        for review in reviews.values():
            histories[review["task_id"]].append(review)
        for decision in decisions:
            decision_types[decision["task_id"]].add(decision["type"])
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
            history = sorted(histories[task["id"]], key=lambda r: r["review_cycle"])
            assert [r["review_cycle"] for r in history] == list(range(1, len(history) + 1))
            if task["state"] in (1, 2, 3):
                assert (
                    not history and not task["artifact_revision"] and not task["approved_review_id"]
                )
            if task["state"] in (6, 7):
                assert task["approved_review_id"] and task["approved_assessment_id"]
                types = decision_types[task["id"]]
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


def persisted_digest(factory):
    with factory() as uow:
        snapshot = {name: uow.gateway.rows(name) for name in TABLES}
    for user in snapshot["users"]:
        del user["password_hash"]  # Random Argon2 salts/secrets deliberately are not reproducible.
    canonical = json.dumps(
        snapshot, sort_keys=True, separators=(",", ":"),
        default=lambda value: value.hex() if isinstance(value, bytes) else value.isoformat(),
    )
    return hashlib.sha256(canonical.encode()).hexdigest()


@pytest.mark.parametrize(
    "projects,tasks,dependencies,records,expected_digest",
    [
        (2, 20, 20, 30, "aa4f3affb32b1b55bb685e153bc26a7f52d47416d75ea94b7af2f844e84bdb29"),
        (40, 6000, 9000, 15000, "6d56de112481ca6c6a54210a1a60b06769b9845fad8699462dfbf753505fb3d3"),
    ],
)
def test_seed_references_json_states_capacity_repeat_and_no_overwrite(
    seed_factory, record_property, projects, tasks, dependencies, records, expected_digest
):
    args = dict(
        projects=projects,
        tasks=tasks,
        dependencies=dependencies,
        records=records,
        anchor_at=datetime(2026, 10, 23, tzinfo=UTC),
    )
    first = seed_demo(seed_factory, **args)
    assert len(seed_factory.seed_commits) == 1
    assert any("INSERT INTO tasks" in sql and many for sql, many in seed_factory.seed_statements)
    assert any("UPDATE tasks" in sql and many for sql, many in seed_factory.seed_statements)
    assert first["reviews"] + first["decisions"] == records
    assert_consistent(seed_factory)
    digest = persisted_digest(seed_factory)
    record_property("seed_semantics_sha256", digest)
    # Recorded from unchanged production seed in hosted run39940459708 before row refactoring.
    assert digest == expected_digest
    assert seed_demo(seed_factory, **args)["already_seeded"]
    with pytest.raises(StatementRejected):
        seed_demo(seed_factory, **args, seed=45)
    with seed_factory() as uow:
        assert uow.gateway.count("tasks") == tasks


def test_seed_impossible_dependency_count_rolls_back_entire_dataset(seed_factory):
    with pytest.raises(ValueError, match="capacity"):
        seed_demo(seed_factory, projects=1, tasks=10, dependencies=1000, records=20)
    with seed_factory() as uow:
        assert uow.gateway.count("users") == uow.gateway.count("projects") == 0



def run_mysql_seed(engine):
    """Explicit fresh owner schema only; preserve data after every successful generation."""
    database = "t44_seed_verify_v2"
    if engine.dialect.name != "mysql" or engine.url.database != database:
        raise ValueError("Seed live verification requires the dedicated t44_seed_verify_v2 schema")
    result = dict(database=database, migration=migrations.migrate(engine, expected_database=database))
    factory = SqlAlchemyUnitOfWorkFactory(engine)
    with factory() as uow:
        assert all(uow.gateway.count(name) == 0 for name in TABLES), "Fresh empty business schema required"
    anchor = datetime(2026, 10, 23, tzinfo=UTC)
    result["seed"] = seed_demo(factory, anchor_at=anchor)
    result["consistency"] = assert_consistent(factory)
    before = persisted_digest(factory)
    result["persisted_sha256"] = before
    assert before == "6d56de112481ca6c6a54210a1a60b06769b9845fad8699462dfbf753505fb3d3"
    repeat = seed_demo(factory, anchor_at=anchor)
    assert repeat["already_seeded"] and repeat["manifest_sha256"] == result["seed"]["manifest_sha256"]
    result["repeat"] = repeat
    with pytest.raises(StatementRejected, match="manifest differs") as rejected:
        seed_demo(factory, anchor_at=anchor, seed=45)
    result["changed_parameters_rejected"] = str(rejected.value)
    with tempfile.TemporaryDirectory(prefix="t44-seed-verification-") as temporary:
        changed = Path(temporary) / "rules.json"
        changed.write_bytes(files("t44").joinpath("resources/escalation-rules.json").read_bytes() + b"\n")
        with pytest.raises(StatementRejected, match="manifest differs") as rejected:
            seed_demo(factory, anchor_at=anchor, rules_path=changed)
        result["changed_config_hash_rejected"] = str(rejected.value)
    violations = [
        ("users", {"active": 2}, "check"),
        ("users", {"username": "synthetic-developer"}, "duplicate"),
        ("tasks", {"owner_id": 4294967295}, "foreign_key"),
        ("tasks", {"state": 0}, "check"),
        ("reviews", {"verdict": 0}, "check"),
        ("release_assessments", {"status": 0}, "check"),
        ("decisions", {"type": 0}, "check"),
    ]
    result["native_constraint_rejections"] = []
    with factory() as uow:
        for table, changes, kind in violations:
            with pytest.raises(PersistenceIntegrityError) as rejected:
                with uow.gateway.savepoint():
                    uow.gateway.update(table, {"id": 1}, changes)
            assert rejected.value.kind == kind
            result["native_constraint_rejections"].append(dict(
                table=table, where=dict(id=1), attempted=changes,
                kind=kind, constraint=rejected.value.constraint, rolled_back=True,
            ))
    assert persisted_digest(factory) == before
    result["unchanged_after_rejections"] = True
    result["schema_after"] = migrations.check_schema(engine)
    assert result["schema_after"]["passed"]
    result["migration_repeat"] = migrations.migrate(engine, expected_database=database)
    with engine.connect() as connection:
        row = connection.execute(text(
            "SELECT VERSION(),DATABASE(),@@session.time_zone,@@session.transaction_isolation,@@session.sql_mode"
        )).one()
        result["server"] = dict(zip(("version", "database", "time_zone", "isolation", "sql_mode"), row, strict=True))
    return result


if __name__ == "__main__":
    private = json.loads(Path(os.environ["T44_SEED_VERIFY_CREDENTIALS"]).read_text())
    engine = create_mysql_engine(MySQLSettings(
        database="t44_seed_verify_v2",
        **{key: private[key] for key in ("host", "port", "username", "password")},
    ))
    try:
        print(json.dumps(run_mysql_seed(engine), ensure_ascii=False, indent=2))
    finally:
        engine.dispose()
