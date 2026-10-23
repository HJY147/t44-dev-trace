"""Controlled SQLite lifecycle and mock driver tests, never MySQL acceptance tests."""

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
    TableBinding,
    TransactionStateError,
    create_mysql_engine,
)
from t44.persistence.engine import initialize_mysql_session


@pytest.fixture
def store(tmp_path):
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
    binding = TableBinding(table, ("id", "note"), ("id", "note"), ("id", "note"))
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
            first.gateway(binding).insert({"id": 1, "note": "committed"})
        with factory() as second:
            assert second.gateway(binding).find({"id": 1}, limit=1)[0]["note"] == "committed"
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
        uow.gateway(binding).insert({"id": 1, "note": "not committed"})
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
            first.gateway(binding).find({"id": 1}, limit=1)
            with factory() as second:
                second.gateway(binding).find({"id": 1}, limit=1)
                assert engine.pool.checkedout() == 2
                assert sessions[0] is not sessions[1]
                assert connections[0] is not connections[1]
    finally:
        event.remove(Session, "after_begin", track)


def test_execution_failure_is_sanitized_and_returns_connection(store):
    engine, _, _ = store
    missing = Table("missing_table", MetaData(), Column("id", Integer))
    binding = TableBinding(missing, ("id",), (), ("id",))
    with (
        pytest.raises(PersistenceUnavailable) as error,
        SqlAlchemyUnitOfWorkFactory(engine)() as uow,
    ):
        uow.gateway(binding).find({"id": 1}, limit=1)
    assert "missing_table" not in str(error.value)
    assert engine.pool.checkedout() == 0


def test_explicit_rollback_and_closed_gateway_cannot_write(store):
    engine, table, binding = store
    with SqlAlchemyUnitOfWorkFactory(engine)() as uow:
        gateway = uow.gateway(binding)
        gateway.insert({"id": 1, "note": "rolled back"})
        uow.rollback()
    assert saved(engine, table) == []
    with pytest.raises(TransactionStateError):
        gateway.insert({"id": 2})


def test_caught_driver_failure_still_prevents_partial_commit(store):
    engine, table, binding = store
    with (
        pytest.raises(TransactionStateError, match="rolled back"),
        SqlAlchemyUnitOfWorkFactory(engine)() as uow,
    ):
        gateway = uow.gateway(binding)
        gateway.insert({"id": 1, "note": "first write"})
        with pytest.raises(PersistenceIntegrityError):
            gateway.insert({"id": 1, "note": "duplicate"})
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
        uow.gateway(binding).insert({"id": 1, "note": "already committed"})
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
        gateway = uow.gateway(binding)
        gateway.insert({"id": 1, "note": payload})
        assert gateway.find({"note": payload}, limit=1)[0]["note"] == payload
        gateway.update_where({"id": 1}, {"note": "updated"})
        count = len(commands)
        with pytest.raises(StatementRejected):
            gateway.update_where({}, {"note": "all rows"})
        with pytest.raises(StatementRejected):
            gateway.find({"id; DROP TABLE foundation_rows": 1}, limit=1)
        with pytest.raises(StatementRejected):
            gateway.insert({"note": text("malicious expression")})
        assert len(commands) == count
    assert all(payload not in statement for statement, _ in commands)
    assert any(payload in parameters for _, parameters in commands)
    assert saved(engine, table)[0].note == "updated"


def test_null_filter_uses_sql_null_semantics(store):
    engine, _, binding = store
    with SqlAlchemyUnitOfWorkFactory(engine)() as uow:
        gateway = uow.gateway(binding)
        gateway.insert({"id": 1, "note": None})
        assert gateway.find({"note": None}, limit=1) == [{"id": 1, "note": None}]


@pytest.mark.parametrize("name", ["rows; DROP TABLE users", "x`", "schema.rows", "has space"])
def test_identifier_policy_rejects_sql_fragments(name):
    table = Table(name, MetaData(), Column("id", Integer))
    with pytest.raises(StatementRejected) as error:
        TableBinding(table, ("id",), (), ("id",))
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
