"""Controlled SQLite lifecycle and mock driver tests, never MySQL acceptance tests."""

from datetime import UTC, datetime
from unittest.mock import Mock

import pytest
from sqlalchemy import (
    Column,
    Integer,
    MetaData,
    String,
    Table,
    create_engine,
    event,
    select,
    text,
)
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session
from t44.persistence import (
    CommitUncertain,
    MySQLSettings,
    PersistenceIntegrityError,
    PersistenceUnavailable,
    SqlAlchemyUnitOfWork,
    SqlAlchemyUnitOfWorkFactory,
    StatementRejected,
    TransactionStateError,
    create_mysql_engine,
)
from t44.persistence.engine import initialize_mysql_session
from t44.persistence.rows import RowsGateway
from t44.persistence.schema import TABLES


@pytest.fixture
def store(tmp_path, monkeypatch):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'controlled.sqlite'}", pool_size=1, max_overflow=1
    )
    table = Table(
        "foundation_rows",
        MetaData(),
        Column("id", Integer, primary_key=True),
        Column("note", String(200)),
    )
    # This isolated toy fixture is not the project DDL or an ORM/business schema.
    table.metadata.create_all(engine)
    import t44.persistence.rows as rows_module

    monkeypatch.setattr(rows_module, "TABLES", {table.name: table})
    binding = table.name
    yield engine, table, binding
    assert engine.pool.checkedout() == 0
    engine.dispose()


def saved(engine, table):
    with engine.connect() as connection:
        return connection.execute(select(table)).all()


def test_commit_and_new_sessions_return_connections(store):
    engine, table, binding = store
    sessions = []

    def track(session, transaction, connection):
        sessions.append(session)

    event.listen(Session, "after_begin", track)
    try:
        factory = SqlAlchemyUnitOfWorkFactory(engine)
        with factory() as first:
            first.gateway.insert(binding, {"id": 1, "note": "committed"})
        with factory() as second:
            assert second.gateway.rows(binding, {"id": 1}, limit=1)[0]["note"] == "committed"
        assert sessions[0] is not sessions[1]
        assert len(saved(engine, table)) == 1
        assert engine.pool.checkedout() == 0
        with pytest.raises(TransactionStateError):
            first.__enter__()
    finally:
        event.remove(Session, "after_begin", track)


def test_business_failure_rolls_back_and_closes(store):
    engine, table, binding = store
    with (
        pytest.raises(RuntimeError, match="business failure"),
        SqlAlchemyUnitOfWorkFactory(engine)() as uow,
    ):
        uow.gateway.insert(binding, {"id": 1, "note": "not committed"})
        raise RuntimeError("business failure")
    assert saved(engine, table) == []


def test_overlapping_units_use_separate_sessions_and_checked_out_connections(store):
    engine, _, binding = store
    sessions, connections = [], []

    def track(session, transaction, connection):
        sessions.append(session)
        connections.append(connection.connection.dbapi_connection)

    event.listen(Session, "after_begin", track)
    try:
        factory = SqlAlchemyUnitOfWorkFactory(engine)
        with factory() as first:
            first.gateway.rows(binding, {"id": 1}, limit=1)
            with factory() as second:
                second.gateway.rows(binding, {"id": 1}, limit=1)
                assert engine.pool.checkedout() == 2
                assert sessions[0] is not sessions[1]
                assert connections[0] is not connections[1]
    finally:
        event.remove(Session, "after_begin", track)


def test_execution_failure_is_sanitized_and_returns_connection(store, monkeypatch):
    engine, _, _ = store
    missing = Table("missing_table", MetaData(), Column("id", Integer))
    import t44.persistence.rows as rows_module

    monkeypatch.setitem(rows_module.TABLES, missing.name, missing)
    binding = missing.name
    with (
        pytest.raises(PersistenceUnavailable) as error,
        SqlAlchemyUnitOfWorkFactory(engine)() as uow,
    ):
        uow.gateway.rows(binding, {"id": 1}, limit=1)
    assert "missing_table" not in str(error.value)
    assert engine.pool.checkedout() == 0


def test_explicit_rollback_and_closed_gateway_cannot_write(store):
    engine, table, binding = store
    with SqlAlchemyUnitOfWorkFactory(engine)() as uow:
        gateway = uow.gateway
        gateway.insert(binding, {"id": 1, "note": "rolled back"})
        uow.rollback()
    assert saved(engine, table) == []
    with pytest.raises(TransactionStateError):
        gateway.insert(binding, {"id": 2})


def test_caught_driver_failure_still_prevents_partial_commit(store):
    engine, table, binding = store
    with (
        pytest.raises(TransactionStateError, match="rolled back"),
        SqlAlchemyUnitOfWorkFactory(engine)() as uow,
    ):
        gateway = uow.gateway
        gateway.insert(binding, {"id": 1, "note": "first write"})
        with pytest.raises(PersistenceIntegrityError):
            gateway.insert(binding, {"id": 1, "note": "duplicate"})
    assert saved(engine, table) == []


def test_uncertain_commit_survives_rollback_and_close_error(store):
    engine, table, binding = store

    class LostAcknowledgement(Session):
        def commit(self):
            super().commit()  # Emulate server commit followed by a lost acknowledgement.
            raise OperationalError("secret SQL", {"secret": "synthetic-value"}, Exception("lost"))

        def close(self):
            super().close()
            raise OperationalError("secret cleanup", {}, Exception("closed"))

    with (
        pytest.raises(CommitUncertain) as error,
        SqlAlchemyUnitOfWork(lambda: LostAcknowledgement(bind=engine)) as uow,
    ):
        uow.gateway.insert(binding, {"id": 1, "note": "already committed"})
    assert "secret" not in str(error.value)
    assert len(saved(engine, table)) == 1  # Cleanup rollback cannot undo a committed transaction.


def test_begin_and_rollback_failures_always_close():
    failed_begin = Mock(spec=Session)
    failed_begin.begin.side_effect = OperationalError("private", {}, Exception("unavailable"))
    with pytest.raises(PersistenceUnavailable), SqlAlchemyUnitOfWork(lambda: failed_begin):
        pass
    failed_begin.close.assert_called_once()

    failed_rollback = Mock(spec=Session)
    failed_rollback.rollback.side_effect = OperationalError("private", {}, Exception("unavailable"))
    with pytest.raises(PersistenceUnavailable), SqlAlchemyUnitOfWork(lambda: failed_rollback):
        raise ValueError("business failure")
    failed_rollback.close.assert_called_once()


def test_interrupted_begin_closes_session_and_preserves_interrupt():
    interrupted = Mock(spec=Session)
    interrupted.begin.side_effect = KeyboardInterrupt()
    with pytest.raises(KeyboardInterrupt), SqlAlchemyUnitOfWork(lambda: interrupted):
        pass
    interrupted.close.assert_called_once()


def test_bound_values_stay_out_of_sql_and_cannot_change_identifiers(store):
    engine, table, binding = store
    payload = "x'); DROP TABLE foundation_rows; --"
    commands = []

    def capture(conn, cursor, statement, parameters, context, executemany):
        commands.append((statement, parameters))

    event.listen(engine, "before_cursor_execute", capture)
    with SqlAlchemyUnitOfWorkFactory(engine)() as uow:
        gateway = uow.gateway
        gateway.insert(binding, {"id": 1, "note": payload})
        assert gateway.rows(binding, {"note": payload}, limit=1)[0]["note"] == payload
        gateway.update_where(binding, {"id": 1}, {"note": "updated"})
        count = len(commands)
        with pytest.raises(StatementRejected):
            gateway.update_where(binding, {}, {"note": "all rows"})
        with pytest.raises(StatementRejected):
            gateway.rows(binding, {"id; DROP TABLE foundation_rows": 1}, limit=1)
        with pytest.raises(StatementRejected):
            gateway.insert(binding, {"note": text("malicious expression")})
        assert len(commands) == count
    assert all(payload not in statement for statement, _ in commands)
    assert any(payload in parameters for _, parameters in commands)
    assert saved(engine, table)[0].note == "updated"


def test_null_filter_uses_sql_null_semantics(store):
    engine, _, binding = store
    with SqlAlchemyUnitOfWorkFactory(engine)() as uow:
        gateway = uow.gateway
        gateway.insert(binding, {"id": 1, "note": None})
        assert gateway.rows(binding, {"note": None}, limit=1) == [{"id": 1, "note": None}]


@pytest.mark.parametrize("name", ["rows; DROP TABLE users", "x`", "schema.rows", "has space"])
def test_identifier_policy_rejects_sql_fragments(name, store):
    with pytest.raises(StatementRejected) as error, SqlAlchemyUnitOfWorkFactory(store[0])() as uow:
        uow.gateway.rows(name)
    assert name not in str(error.value)


def test_mysql_engine_is_lazy_pooled_and_redacts_credentials(monkeypatch):
    import pymysql

    connect = Mock(side_effect=AssertionError("Engine construction must not connect"))
    monkeypatch.setattr(pymysql, "connect", connect)
    settings = MySQLSettings("127.0.0.1", "t44_test", "test_user", "synthetic-secret", pool_size=3)
    engine = create_mysql_engine(settings)
    try:
        connect.assert_not_called()
        assert "synthetic-secret" not in repr(settings)
        assert "synthetic-secret" not in str(engine.url)
        assert engine.hide_parameters is True
        assert engine.pool.size() == 3
        assert event.contains(engine, "connect", initialize_mysql_session)
        assert engine.dialect._on_connect_isolation_level == "READ COMMITTED"
    finally:
        engine.dispose()


def test_mock_mysql_connection_initializes_every_session_and_closes_cursor():
    connection = Mock()
    for _ in range(2):
        initialize_mysql_session(connection, None)
    sql = [call.args[0] for call in connection.cursor().execute.call_args_list]
    assert sql.count("SET SESSION time_zone = '+00:00'") == 2
    assert sql.count("SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED") == 2
    assert sum("STRICT_TRANS_TABLES" in statement for statement in sql) == 2
    assert connection.cursor().close.call_count == 2


def test_mock_mysql_initialization_failure_redacts_and_closes():
    connection = Mock()
    connection.cursor().execute.side_effect = RuntimeError("synthetic-secret in driver message")
    with pytest.raises(PersistenceUnavailable) as error:
        initialize_mysql_session(connection, None)
    assert "synthetic-secret" not in str(error.value)
    connection.cursor().close.assert_called_once()


@pytest.fixture
def schedule_store(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'schedule.sqlite'}")
    TABLES["schedule_changes"].create(engine)
    factory = SqlAlchemyUnitOfWorkFactory(engine)
    now = datetime(2026, 10, 23, 20, 0, 1, 123456, tzinfo=UTC)
    plan = {"planned_start": "2026-10-23T20:00:00.000000Z", "nested": {"中文": [1, 2]}}
    records = []
    with factory() as uow:
        for id, project, task, version, iteration in (
            (1, 1, 11, 2, None),
            (2, 1, 11, 3, None),
            (3, 1, 12, 2, None),
            (4, 1, 12, 3, None),
            (5, 2, 21, 2, None),
            (6, 1, None, 2, 31),
        ):
            row = dict(
                id=id,
                project_id=project,
                task_id=task,
                iteration_id=iteration,
                from_version=version - 1,
                to_version=version,
                before_plan=plan,
                after_plan={**plan, "unchanged": False},
                reason="原因\n" + "中" * 1997,
                evidence=[{"url": "https://example.test/evidence"}],
                changed_by=1,
                changed_at=now,
            )
            uow.gateway.insert("schedule_changes", row)
            records.append(row)
    yield engine, factory, records
    assert engine.pool.checkedout() == 0
    engine.dispose()


def test_task_schedule_changes_exact_pairs_complete_codec_and_no_mutation(schedule_store):
    _, factory, original = schedule_store
    with factory() as uow:
        gateway = uow.gateway
        result = gateway.task_schedule_changes(1, ((12, 3), (11, 2), (12, 3)))
        assert result == [original[0], original[3]]
        assert all(set(row) == set(TABLES["schedule_changes"].c.keys()) for row in result)
        assert result[0]["changed_at"].tzinfo is UTC
        assert len(result[0]["reason"]) == 2000
        assert gateway.task_schedule_changes(1, ((21, 2),)) == []
        assert gateway.task_schedule_changes(2, ((21, 2), (11, 2))) == [original[4]]
        assert gateway.rows("schedule_changes") == original


def test_task_schedule_changes_empty_and_invalid_never_acquire_session():
    session = Mock(side_effect=AssertionError("No SQL/session expected"))
    gateway = RowsGateway(session, Mock())
    assert gateway.task_schedule_changes(1, ()) == []
    with pytest.raises(StatementRejected):
        gateway.task_schedule_changes(True, ())
    session.assert_not_called()


@pytest.mark.parametrize(
    "project,pairs",
    [(value, ((1, 2),)) for value in (0, -1, 4294967296, True, "1", None, 1.0)]
    + [(1, value) for value in (None, [], [(1, 2)], ((1,),), ((1, 2, 3),), ([1, 2],))]
    + [(1, ((value, 2),)) for value in (0, -1, 4294967296, True, "1", None, 1.0)]
    + [(1, ((1, value),)) for value in (0, -1, 2147483648, True, "2", None, 2.0)]
    + [(1, ((1, 2),) * 101)],
)
def test_task_schedule_changes_rejects_bad_input_before_sql(project, pairs):
    session = Mock(side_effect=AssertionError("Invalid input must not execute"))
    with pytest.raises(StatementRejected):
        RowsGateway(session, Mock()).task_schedule_changes(project, pairs)
    session.assert_not_called()


def test_task_schedule_changes_one_bound_read_and_hundred_limit(schedule_store):
    engine, factory, _ = schedule_store
    commands = []

    def capture(conn, cursor, statement, parameters, context, executemany):
        commands.append((statement, parameters))

    event.listen(engine, "before_cursor_execute", capture)
    try:
        with factory() as uow:
            gateway = uow.gateway
            assert gateway.task_schedule_changes(1, ()) == []
            assert commands == []
            result = gateway.task_schedule_changes(1, ((11, 2), (12, 3)))
            assert [row["id"] for row in result] == [1, 4]
            assert len(commands) == 1
            sql, parameters = commands[0]
            assert "LIMIT" not in sql and "FOR UPDATE" not in sql
            assert "schedule_changes.iteration_id IS NULL" in sql
            assert "(schedule_changes.task_id, schedule_changes.to_version) IN" in sql
            assert tuple(parameters) == (1, 11, 2, 12, 3)
            commands.clear()
            assert gateway.task_schedule_changes(4294967295, ((4294967295, 2147483647),)) == []
            assert len(commands) == 1
            commands.clear()
            assert [
                row["id"]
                for row in gateway.task_schedule_changes(1, tuple((11, v) for v in range(1, 101)))
            ] == [1, 2]
            assert len(commands) == 1
    finally:
        event.remove(engine, "before_cursor_execute", capture)


@pytest.mark.parametrize(
    "violation",
    [
        "duplicate_pair",
        "duplicate_id",
        "project",
        "task",
        "version",
        "iteration",
        "bool_project",
        "bool_task",
        "bool_version",
        "bad_id",
        "missing_column",
        "extra_column",
        "too_many",
        "not_dict",
        "not_list",
    ],
)
def test_task_schedule_changes_result_violation_is_failure(schedule_store, monkeypatch, violation):
    _, factory, records = schedule_store
    rows = [dict(records[0]), dict(records[3])]
    if violation == "duplicate_pair":
        rows[1] = {**rows[0], "id": 99}
    elif violation == "duplicate_id":
        rows[1]["id"] = rows[0]["id"]
    elif violation == "missing_column":
        del rows[0]["reason"]
    elif violation == "extra_column":
        rows[0]["extra"] = "not in frozen table"
    elif violation == "too_many":
        rows.append(dict(rows[0]))
    elif violation == "not_dict":
        rows[0] = None
    elif violation == "not_list":
        rows = tuple(rows)
    else:
        column, value = {
            "project": ("project_id", 2),
            "task": ("task_id", 13),
            "version": ("to_version", 4),
            "iteration": ("iteration_id", 31),
            "bool_project": ("project_id", True),
            "bool_task": ("task_id", True),
            "bool_version": ("to_version", True),
            "bad_id": ("id", 4294967296),
        }[violation]
        rows[0][column] = value
    with factory() as uow:
        monkeypatch.setattr(uow.gateway, "_execute", Mock(return_value=rows))
        with pytest.raises(PersistenceUnavailable) as error:
            uow.gateway.task_schedule_changes(1, ((11, 2), (12, 3)))
        assert "not in frozen table" not in str(error.value)
        with pytest.raises(TransactionStateError):
            uow.commit()


def test_task_schedule_changes_returns_all_hundred_rows(schedule_store):
    _, factory, records = schedule_store
    expected = [
        {
            **records[0],
            "id": 100 + version,
            "task_id": 99,
            "from_version": version - 1,
            "to_version": version,
        }
        for version in range(2, 102)
    ]
    with factory() as uow:
        gateway = uow.gateway
        gateway.insert_many("schedule_changes", expected)
        assert (
            gateway.task_schedule_changes(1, tuple((99, v) for v in range(101, 1, -1))) == expected
        )


def test_task_schedule_changes_driver_failure_is_sanitized_and_rollback_only():
    session = Mock(spec=Session)
    session.execute.side_effect = OperationalError("secret SQL", {}, Exception("secret driver"))
    with SqlAlchemyUnitOfWork(lambda: session) as uow:
        with pytest.raises(PersistenceUnavailable) as error:
            uow.gateway.task_schedule_changes(1, ((11, 2),))
        assert "secret" not in str(error.value)
        with pytest.raises(TransactionStateError):
            uow.gateway.rows("schedule_changes")
        with pytest.raises(TransactionStateError):
            uow.commit()
