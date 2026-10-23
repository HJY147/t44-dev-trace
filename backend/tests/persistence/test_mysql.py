"""Real MySQL 8.4 module checks in an explicitly selected CI/local project test schema."""

import hashlib
import json
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from pathlib import Path
from threading import Barrier
from uuid import uuid4

import pytest
from argon2 import PasswordHasher
from sqlalchemy import text
from sqlalchemy.engine import make_url
from t44.persistence import (
    MySQLSettings,
    PersistenceIntegrityError,
    SqlAlchemyUnitOfWorkFactory,
    create_mysql_engine,
)
from t44.persistence.accounts import PasswordHashRejected, initialize_user
from t44.persistence.codecs import utc_now
from t44.persistence.delivery import OutboxStore
from t44.persistence.errors import StatementRejected
from t44.persistence.idempotency import IdempotencyStore
from t44.persistence.migrations import migrate
from t44.persistence.scans import ScanStore

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def mysql():
    if source := os.environ.get("DATABASE_URL"):
        url = make_url(source)
        database = os.environ.get("T44_DATABASE")
        if (
            url.drivername != "mysql+pymysql"
            or database != url.database
            or database not in ("t44_ci", "t44_test")
        ):
            pytest.fail(
                "DATABASE_URL requires the matching explicit disposable project test database"
            )
        app = dict(
            host=url.host, port=url.port or 3306, username=url.username, password=url.password
        )
    elif path := os.environ.get("T44_TEST_CREDENTIALS"):
        database = os.environ.get("T44_TEST_DATABASE")
        if database != "t44_test":
            pytest.fail("Local persistence checks require explicit T44_TEST_DATABASE=t44_test")
        secret = json.loads(Path(path).read_text())
        app = {k: secret[k] for k in ("host", "port", "username", "password")}
    elif os.environ.get("CI"):
        pytest.fail("Real MySQL CI configuration is missing; refusing to skip")
    else:
        pytest.skip("Set DATABASE_URL+T44_DATABASE or local app credentials+T44_TEST_DATABASE")
    engine = create_mysql_engine(MySQLSettings(database=database, **app))
    migrate(engine, expected_database=database)
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
    result = migrate(engine, expected_database=engine.url.database)
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


def test_real_concurrent_claim_takeover_and_result_request_id(mysql, fixture):
    _, factory = mysql
    store, key, now = IdempotencyStore(factory), uuid4().hex, utc_now()
    args = dict(
        actor_kind=1,
        actor_id=fixture["user"],
        operation_id="claimFixture",
        key=key,
        request_hash=hashlib.sha256(b"same-payload").digest(),
        now=now,
        lease_seconds=1,
    )
    barrier = Barrier(2)

    def claim():
        barrier.wait(timeout=10)
        return store.claim(**args)

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: claim(), range(2)))
    assert sorted(r["disposition"] for r in results) == ["claimed", "in_progress"]
    original = next(r["row"] for r in results if r["disposition"] == "claimed")
    later = now + timedelta(seconds=2)
    recovered = store.claim(**{**args, "now": later})["row"]
    assert recovered["owner_token"] != original["owner_token"]
    with factory() as uow:
        with pytest.raises(StatementRejected):
            store.lock_owner(uow.gateway, original["id"], original["owner_token"], now=later)
        store.complete(
            uow.gateway,
            recovered["id"],
            recovered["owner_token"],
            now=later,
            response_status=202,
            response_body={"data": {"created": True}},
            response_request_id="final-result-request",
        )
    replay = store.claim(**args)
    assert replay["disposition"] == "replay"
    assert replay["row"]["response_request_id"] == "final-result-request"
    assert store.claim(**{**args, "request_hash": b"x" * 32})["disposition"] == "mismatch"


def test_real_durable_scan_concurrent_start_and_cursor_recovery(mysql, fixture):
    _, factory = mysql
    store, run = ScanStore(factory), uuid4()
    snapshot = {"rules": [{"level": 1, "start_offset_seconds": -86400}]}
    args = dict(
        rule_version=1,
        rule_snapshot=snapshot,
        rule_hash=hashlib.sha256(b"fixture-rule").digest(),
        cutoff_at=utc_now() + timedelta(days=3),
    )
    with ThreadPoolExecutor(max_workers=2) as pool:
        ids = list(pool.map(lambda _: store.start(run, **args)["id"], range(2)))
    assert ids[0] == ids[1]
    assert fixture["task"] in [r["id"] for r in store.page(run, limit=1000)]
    store.checkpoint(run, last_task_id=fixture["task"], scanned_delta=1, created_delta=1)
    fresh = ScanStore(factory)
    row = fresh.get(run)
    assert row["last_task_id"] == fixture["task"] and row["created_count"] == 1
    assert (
        fresh.checkpoint(run, last_task_id=fixture["task"], created_delta=100)["created_count"] == 1
    )
    with pytest.raises(StatementRejected):
        fresh.checkpoint(run, last_task_id=fixture["task"] - 1)
    assert fresh.checkpoint(run, last_task_id=fixture["task"], finished=True)["status"] == 2
    assert fresh.page(run) == []


def escalation_fixture(factory, fixture):
    now = utc_now()
    run = ScanStore(factory).start(
        uuid4(), rule_version=1, rule_snapshot={"rules": []}, rule_hash=b"r" * 32
    )
    with factory() as uow:
        g = uow.gateway
        task = g.get("tasks", fixture["task"])
        task.pop("id")
        task.update(title="synthetic notification fixture", escalation_count=1)
        tid = g.insert("tasks", task)
        event = g.insert(
            "outbox_events",
            dict(
                event_type=2,
                schema_version=1,
                project_id=fixture["project"],
                task_id=tid,
                payload={"title": "合成升级", "message": "模块测试数据"},
                recipients=[fixture["user"]],
                status=1,
                attempts=0,
                next_attempt_at=now,
                created_at=now,
                updated_at=now,
            ),
        )
        g.insert(
            "escalation_events",
            dict(
                project_id=fixture["project"],
                task_id=tid,
                schedule_version=1,
                level=1,
                rule_version=1,
                rule_snapshot={"rules": []},
                rule_hash=b"r" * 32,
                scan_run_id=run["id"],
                planned_end=task["planned_end"],
                observed_at=now,
                event_id=event,
            ),
        )
    return event


def test_real_outbox_lease_expiry_retry_and_confirm(mysql, fixture):
    _, factory = mysql
    event = escalation_fixture(factory, fixture)
    store, now = OutboxStore(factory), utc_now()
    claimed = next(e for e in store.claim(now=now, limit=1000, lease_seconds=1) if e["id"] == event)
    recovered = next(
        e for e in store.claim(now=now + timedelta(seconds=2), limit=1000) if e["id"] == event
    )
    assert claimed["lease_token"] != recovered["lease_token"]
    assert not store.confirm(event, claimed["lease_token"])
    assert store.retry(event, recovered["lease_token"], delay_seconds=0)
    again = next(e for e in store.claim(limit=1000) if e["id"] == event)
    assert store.confirm(event, again["lease_token"])
    assert store.consume(event)["created"] == 1
    assert store.consume(event)["created"] == 0


def test_real_fallback_races_consume_and_late_confirm_is_fenced(mysql, fixture):
    _, factory = mysql
    event = escalation_fixture(factory, fixture)
    store = OutboxStore(factory)
    claimed = next(e for e in store.claim(limit=1000) if e["id"] == event)
    barrier = Barrier(2)

    def consume():
        barrier.wait(timeout=10)
        return store.consume(event)

    def fallback():
        barrier.wait(timeout=10)
        return store.fallback(event, lease_token=claimed["lease_token"])

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(consume), pool.submit(fallback)]
        results = [f.result(timeout=10) for f in futures]
    assert sum(r["created"] for r in results) == 1
    assert not store.confirm(event, claimed["lease_token"])
    assert store.consume(event)["created"] == 0
    with factory() as uow:
        assert uow.gateway.get("outbox_events", event)["status"] == 4
        assert uow.gateway.count("notifications", {"event_id": event}) == 1


RECOVERY_TIME = datetime(2000, 1, 1, tzinfo=UTC)


def confirm_fixture(factory, fixture, *, consumed=False):
    store = OutboxStore(factory)
    event = escalation_fixture(factory, fixture)
    claim = next(e for e in store.claim(limit=1000) if e["id"] == event)
    assert store.confirm(event, claim["lease_token"], now=RECOVERY_TIME)
    if consumed:
        assert store.consume(event)["created"] == 1
    return event, claim["lease_token"]


def test_confirmed_recovery_excludes_old_complete_events_before_limit(mysql, fixture):
    _, factory = mysql
    store = OutboxStore(factory)
    complete = [confirm_fixture(factory, fixture, consumed=True)[0] for _ in range(3)]
    missing, token = confirm_fixture(factory, fixture)
    now = RECOVERY_TIME
    recovered = store.recover_confirmed(confirmed_before=now, now=now, limit=1)
    assert recovered == [dict(event_id=missing, created=1, fallback=True)]
    assert all(store.get(id)["status"] == 3 for id in complete)
    assert store.recover_confirmed(confirmed_before=now, limit=1) == []
    assert store.consume(missing)["created"] == 0
    assert not store.confirm(missing, token)
    assert store.fallback(missing, lease_token=token)["stale_owner"]


def test_confirmed_recovery_skips_consumer_lock_and_never_marks_complete_fallback(mysql, fixture):
    from threading import Event

    _, factory = mysql
    store = OutboxStore(factory)
    event, _ = confirm_fixture(factory, fixture)
    inserted, finish = Event(), Event()

    class PausedConsumer(OutboxStore):
        def _notices(self, *args, **kwargs):
            count = super()._notices(*args, **kwargs)
            inserted.set()
            assert finish.wait(timeout=10)
            return count

    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(PausedConsumer(factory).consume, event)
        try:
            assert inserted.wait(timeout=10)
            assert store.recover_confirmed(confirmed_before=RECOVERY_TIME, limit=1) == []
        finally:
            finish.set()
        assert future.result(timeout=10)["created"] == 1
    assert store.recover_confirmed(confirmed_before=RECOVERY_TIME, limit=1) == []
    assert store.get(event)["status"] == 3
    with factory() as uow:
        assert uow.gateway.rows("notifications", {"event_id": event})[0]["fallback"] == 0
