"""Owner parser differential and atomic notification batching; no acceptance claims."""

import importlib.util
import re
import subprocess
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from sqlglot import parse_one
from t44.persistence import PersistenceIntegrityError, StatementRejected, migrations
from t44.persistence.delivery import OutboxStore
from t44.persistence.schema import TABLES
from t44.persistence.seed import seed_demo

BASE = "5868779e949adef066fe26bffbc4f2e8afee7649"
AT = datetime(2026, 10, 29, tzinfo=UTC)


@pytest.fixture(scope="module")
def previous(tmp_path_factory):
    path = tmp_path_factory.mktemp("parser") / "previous.py"
    path.write_bytes(
        subprocess.check_output(["git", "show", f"{BASE}:backend/t44/persistence/migrations.py"])
    )
    spec = importlib.util.spec_from_file_location("t44.persistence.previous", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def expressions():
    frozen = [
        str(c.sqltext)
        for t in TABLES.values()
        for c in t.constraints
        if c.__class__.__name__ == "CheckConstraint"
    ]
    equivalent = [f"(({value}))" for value in frozen]
    equivalent += [
        re.sub(
            r"NOT (`\w+`) IS NULL",
            r"\1 IS NOT NULL",
            parse_one(value, read="mysql").sql("mysql", identify=True),
        )
        for value in frozen
    ]
    return (
        frozen
        + equivalent
        + [
            "(a=1 OR b=2) AND c=3",
            "a=1 OR (b=2 AND c=3)",
            "json_type(value)='ARRAY'",
            "json_type(value)='array'",
            "left(value,10)=1",
            "left(value,11)=1",
            "value=1+2",
            "value=1-2",
            "value='ARRAY'",
            "value=_utf8mb4'ARRAY'",
            "value=_ascii'ARRAY'",
            "value='_utf8mb4''ARRAY'",
            "value='_ascii''ARRAY'",
            "a!=1",
            "a<>1",
            "a is null",
            "a is not null",
            "length(value)>0",
            "char_length(value)>0",
        ]
    )


def test_755_frozen_checks_and_normalized_surface_preserve_every_equality(previous):
    cases = expressions()
    old = [previous._check_signature(value) for value in cases]
    new = [migrations._check_signature(value) for value in cases]
    assert all(value is not None for value in old + new)
    for i, left in enumerate(cases):
        for j, right in enumerate(cases):
            assert (old[i] == old[j]) == (new[i] == new[j]), (left, right)


@pytest.mark.parametrize(
    "source",
    [
        "a = 1 /* unparsed suffix */",
        "a=1 -- suffix",
        "a=1; SELECT 1",
        "a=1;",
        "a=1 AS harmless",
        "a=1 harmless",
        "value=_ascii'é'",
        "value=_latin1'ARRAY'",
        "a=1 / 2",
        "a=1 * 2",
        "a=1 # suffix",
        "a=1 $ suffix",
        "a=1)",
        "(a=1",
    ],
)
def test_755_unsupported_lexemes_statements_aliases_and_suffixes_fail_closed(previous, source):
    assert previous._check_signature(source) is None
    assert migrations._check_signature(source) is None


@pytest.fixture
def factory(tmp_path):
    from sqlalchemy import create_engine, event
    from t44.persistence import SqlAlchemyUnitOfWorkFactory
    from t44.persistence.schema import metadata

    engine = create_engine(f"sqlite:///{tmp_path / 'batch.sqlite'}")
    event.listen(
        engine,
        "connect",
        lambda connection, _: connection.execute("PRAGMA foreign_keys=ON"),
    )
    metadata.create_all(engine)
    factory = SqlAlchemyUnitOfWorkFactory(engine)
    seed_demo(factory, projects=1, tasks=10, dependencies=5, records=20, anchor_at=AT)
    yield factory, engine
    engine.dispose()


def event_row(factory, recipients):
    with factory() as uow:
        g = uow.gateway
        project, task = g.rows("projects")[0], g.rows("tasks")[0]
        uid = g.rows("users")[0]["id"]
        run = g.insert(
            "scan_runs",
            dict(
                run_key=b"x" * 16,
                rule_version=1,
                rule_snapshot={},
                rule_hash=b"y" * 32,
                status=1,
                cutoff_at=AT,
                started_at=AT,
                heartbeat_at=AT,
            ),
        )
        eid = g.insert(
            "outbox_events",
            dict(
                event_type=2,
                schema_version=1,
                project_id=project["id"],
                task_id=task["id"],
                payload={},
                status=1,
                attempts=0,
                recipients=recipients(uid),
                next_attempt_at=AT,
                created_at=AT,
                updated_at=AT,
            ),
        )
        g.insert(
            "escalation_events",
            dict(
                project_id=project["id"],
                task_id=task["id"],
                schedule_version=1,
                level=1,
                rule_version=1,
                rule_snapshot={},
                rule_hash=b"y" * 32,
                scan_run_id=run,
                planned_end=task["planned_end"],
                observed_at=AT,
                event_id=eid,
            ),
        )
        return eid, uid


def test_755_notifications_use_one_batch_and_replay_creates_none(factory):
    from sqlalchemy import event

    store, engine = factory
    eid, uid = event_row(store, lambda uid: [uid + 2, uid, uid + 1, uid])
    statements = []
    event.listen(
        engine,
        "before_cursor_execute",
        lambda c, cur, sql, p, ctx, many: statements.append((sql, many)),
    )
    result = OutboxStore(store).consume(eid, now=AT)
    assert result == dict(event_id=eid, created=3, fallback=False)
    inserts = [
        (sql, many) for sql, many in statements if sql.startswith("INSERT INTO notifications")
    ]
    assert len(inserts) == 1 and inserts[0][1] is True
    assert OutboxStore(store).consume(eid, now=AT)["created"] == 0
    with store() as uow:
        notices = uow.gateway.rows("notifications", {"event_id": eid})
    assert [row["recipient_id"] for row in notices] == [uid, uid + 1, uid + 2]
    assert all(row["fallback"] == 0 for row in notices)


def test_755_batch_integrity_failure_rolls_back_every_notice(factory):
    store, _ = factory
    eid, _ = event_row(store, lambda uid: [uid, 4294967295])
    with pytest.raises(PersistenceIntegrityError):
        OutboxStore(store).fallback(eid, now=AT)
    with store() as uow:
        assert uow.gateway.rows("notifications", {"event_id": eid}) == []
        assert uow.gateway.get("outbox_events", eid)["status"] == 1


def test_755_missing_ledger_is_rejected_before_batch():
    gateway = SimpleNamespace(
        rows=lambda *a, **kw: [],
        insert_many=lambda *a: pytest.fail("A missing ledger must not create notices"),
    )
    with pytest.raises(StatementRejected, match="ledger"):
        OutboxStore(None)._notices(gateway, dict(event_type=2, id=1), fallback=False, now=AT)
