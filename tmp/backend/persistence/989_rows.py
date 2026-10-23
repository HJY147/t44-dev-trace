from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import create_engine, event, text
from t44.persistence import (
    PersistenceIntegrityError,
    Pred,
    SqlAlchemyUnitOfWorkFactory,
    StatementRejected,
)
from t44.persistence.schema import metadata


@pytest.fixture
def database(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'rows.sqlite'}")
    event.listen(engine, "connect", lambda conn, _: conn.execute("PRAGMA foreign_keys=ON"))
    # MySQL-only CHECK expressions are not claimed as SQLite-tested constraints.
    metadata.create_all(engine)
    yield SqlAlchemyUnitOfWorkFactory(engine)
    engine.dispose()


def user(name):
    now = datetime.now(UTC)
    return dict(
        username=name,
        display_name=name,
        password_hash="$argon2id$synthetic-not-login",
        active=1,
        created_at=now,
        updated_at=now,
    )


def test_generated_id_json_time_cas_and_empty_in(database):
    with database() as uow:
        g = uow.gateway
        uid = g.insert("users", user("demo"))
        assert g.get("users", uid)["created_at"].tzinfo is UTC
        pid = g.insert(
            "projects",
            dict(
                name="demo",
                description="synthetic",
                created_by=uid,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            ),
        )
        assert g.update("projects", {"id": pid, "version": 1}, {"version": 2}) == 1
        assert g.update("projects", {"id": pid, "version": 1}, {"version": 2}) == 0
        assert g.rows("users", {"id": []}) == []
        assert g.count("users", {"id": []}) == 0
        assert g.count("users", predicates=(Pred("id", "ge", uid),)) == 1
        now = datetime.now(UTC)
        g.insert(
            "project_members",
            dict(project_id=pid, user_id=uid, roles_mask=3, created_at=now, updated_at=now),
        )
        iteration = g.insert(
            "iterations",
            dict(
                project_id=pid,
                name="fixture",
                planned_start=now,
                planned_end=now + timedelta(days=1),
                capacity=[],
                buffer_quarters=0,
                delay_contingency="fixture",
                created_at=now,
                updated_at=now,
            ),
        )
        task = g.insert(
            "tasks",
            dict(
                project_id=pid,
                iteration_id=iteration,
                title="fixture",
                description="synthetic",
                owner_id=uid,
                planned_start=now,
                planned_end=now + timedelta(hours=1),
                estimated_quarters=1,
                buffer_quarters=0,
                delay_contingency="fixture",
                created_at=now,
                updated_at=now,
            ),
        )
        assert isinstance(task, int) and task > 0
        assert g.get("tasks", task)["id"] == task


def test_savepoint_duplicate_can_be_recovered_without_poisoning_uow(database):
    with database() as uow:
        g = uow.gateway
        g.insert("users", user("first"))
        with pytest.raises(PersistenceIntegrityError) as error, g.savepoint():
            g.insert("users", user("first"))
        assert error.value.kind == "duplicate"
        g.insert("users", user("second"))
    with database() as uow:
        assert uow.gateway.count("users") == 2


def test_nested_expression_and_unbounded_write_are_rejected(database):
    with database() as uow:
        g = uow.gateway
        with pytest.raises(StatementRejected):
            g.rows("users", {"id": [text("1 OR 1=1")]})
        with pytest.raises(StatementRejected):
            g.update("users", {}, {"active": 0})
        with pytest.raises(StatementRejected):
            g.rows("users; DROP TABLE projects")
