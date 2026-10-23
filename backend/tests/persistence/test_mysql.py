"""Opt-in real MySQL 8.4 module checks, restricted to the dedicated t44_test schema."""

import hashlib
import json
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from pathlib import Path
from threading import Barrier
from uuid import uuid4

import pytest
from argon2 import PasswordHasher
from sqlalchemy import text
from t44.persistence import (
    MySQLSettings,
    PersistenceIntegrityError,
    SqlAlchemyUnitOfWorkFactory,
    create_mysql_engine,
)
from t44.persistence.accounts import PasswordHashRejected, initialize_user
from t44.persistence.codecs import utc_now
from t44.persistence.migrations import migrate


@pytest.fixture(scope="module")
def mysql():
    path = os.environ.get("T44_TEST_CREDENTIALS")
    if not path:
        pytest.skip("Set T44_TEST_CREDENTIALS for the dedicated real MySQL project schema")
    secret = json.loads(Path(path).read_text())
    app = {k: secret[k] for k in ("host", "port", "username", "password")}
    engine = create_mysql_engine(MySQLSettings(database="t44_test", **app))
    migrate(engine, expected_database="t44_test")
    yield engine, SqlAlchemyUnitOfWorkFactory(engine)
    engine.dispose()


@pytest.fixture(scope="module")
def fixture(mysql):
    _, factory = mysql
    suffix, now = uuid4().hex[:12], utc_now()
    uid = initialize_user(
        factory,
        username=f"fixture-{suffix}",
        display_name="合成测试账户",
        password_hash=PasswordHasher().hash(uuid4().hex),
    )
    with factory() as uow:
        g = uow.gateway
        pid = g.insert(
            "projects",
            dict(
                name=f"fixture-{suffix}",
                description="模块合成夹具",
                created_by=uid,
                created_at=now,
                updated_at=now,
            ),
        )
        g.insert(
            "project_members",
            dict(project_id=pid, user_id=uid, roles_mask=7, created_at=now, updated_at=now),
        )
        iid = g.insert(
            "iterations",
            dict(
                project_id=pid,
                name="synthetic",
                planned_start=now,
                planned_end=now + timedelta(days=3),
                capacity=[{"user_id": uid, "quarters": 400}],
                buffer_quarters=0,
                delay_contingency="合成预案",
                created_at=now,
                updated_at=now,
            ),
        )
        tid = g.insert(
            "tasks",
            dict(
                project_id=pid,
                iteration_id=iid,
                title="synthetic",
                description="模块数据",
                owner_id=uid,
                planned_start=now,
                planned_end=now + timedelta(days=2),
                estimated_quarters=4,
                buffer_quarters=0,
                delay_contingency="合成预案",
                created_at=now,
                updated_at=now,
            ),
        )
        assert isinstance(tid, int) and g.get("tasks", tid)["id"] == tid
    return dict(user=uid, project=pid, iteration=iid, task=tid)


def test_real_repeat_migration_utc_modes_and_core_shapes(mysql):
    engine, _ = mysql
    result = migrate(engine, expected_database="t44_test")
    assert result["already_applied"] and result["passed"]
    assert (result["tables"], result["columns"]) == (18, 226)
    with engine.connect() as c:
        zone, mode, isolation = c.execute(
            text("SELECT @@session.time_zone, @@session.sql_mode, @@session.transaction_isolation")
        ).one()
        assert zone == "+00:00" and "STRICT_TRANS_TABLES" in mode and isolation == "READ-COMMITTED"
        for name in ("tasks", "task_dependencies", "reviews", "decisions"):
            ddl = c.exec_driver_sql(f"SHOW CREATE TABLE {name}").one()[1]  # fixed test allowlist
            assert "ENGINE=InnoDB" in ddl and "AUTO_INCREMENT" in ddl and "CHECK" in ddl


def test_real_hash_rejection_has_independent_sanitized_audit(mysql):
    _, factory = mysql
    request_id = uuid4().hex
    with pytest.raises(PasswordHashRejected):
        initialize_user(
            factory,
            username="never-created",
            display_name="synthetic",
            password_hash="plaintext-must-not-persist",
            request_id=request_id,
        )
    with factory() as uow:
        rows = uow.gateway.rows("audit_events", {"request_id": request_id})
        assert len(rows) == 1 and rows[0]["reason_code"] == 11
        assert "plaintext" not in str(rows[0]) and rows[0]["before_values"] == []


@pytest.mark.parametrize(
    "changes,kind",
    [
        ({"state": 8}, "check"),
        ({"estimated_quarters": 0}, "check"),
        ({"state": 3}, "check"),
        ({"owner_id": 4294967295}, "foreign_key"),
    ],
)
def test_real_task_constraints_and_savepoint(mysql, fixture, changes, kind):
    _, factory = mysql
    with factory() as uow:
        g = uow.gateway
        with pytest.raises(PersistenceIntegrityError) as error, g.savepoint():
            g.update("tasks", {"id": fixture["task"]}, changes)
        assert error.value.kind == kind
        assert g.get("tasks", fixture["task"])["state"] == 1


def test_real_concurrent_cas_exactly_one_winner(mysql, fixture):
    _, factory = mysql
    barrier = Barrier(2)
    with factory() as uow:
        old = uow.gateway.get("tasks", fixture["task"])["version"]

    def contender():
        with factory() as uow:
            barrier.wait(timeout=10)
            return uow.gateway.update(
                "tasks", {"id": fixture["task"], "version": old}, {"version": old + 1}
            )

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(lambda _: contender(), range(2))) == [0, 1]


def test_real_processing_json_null_and_unique_claim(mysql, fixture):
    engine, factory = mysql
    now, key = utc_now(), uuid4().hex
    value = dict(
        actor_kind=1,
        actor_id=fixture["user"],
        operation_id="fixture",
        idempotency_key=key,
        request_hash=hashlib.sha256(b"fixture").digest(),
        status=1,
        owner_token=uuid4().bytes,
        lease_until=now + timedelta(seconds=60),
        response_status=None,
        response_body=None,
        response_request_id=None,
        created_at=now,
        completed_at=None,
    )
    with factory() as uow:
        id = uow.gateway.insert("idempotency_requests", value)
        with pytest.raises(PersistenceIntegrityError) as error, uow.gateway.savepoint():
            uow.gateway.insert("idempotency_requests", value)
        assert error.value.kind == "duplicate"
    with engine.connect() as c:
        assert (
            c.execute(
                text("SELECT response_body IS NULL FROM idempotency_requests WHERE id=:id"),
                {"id": id},
            ).scalar_one()
            == 1
        )
