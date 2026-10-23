"""Real QueuePool behavior with synthetic DBAPI only; no HTTP, SQL or network."""

from dataclasses import replace
from unittest.mock import Mock

import pytest
from sqlalchemy import event
from sqlalchemy.exc import TimeoutError as PoolTimeout
from sqlalchemy.pool import QueuePool
from t44.persistence import MySQLSettings, create_mysql_engine
from t44.persistence.engine import initialize_mysql_session
from t44.settings import Settings

CASES = [
    pytest.param({}, 15, 0, id="default"),
    pytest.param({"pool_size": 3}, 3, 0, id="partial-size"),
    pytest.param({"pool_size": 3, "max_overflow": 2}, 3, 2, id="both-explicit"),
    pytest.param({"pool_size": 5, "max_overflow": 10}, 5, 10, id="old-explicit"),
    pytest.param({"max_overflow": 2}, 15, 2, id="partial-overflow"),
]


@pytest.mark.parametrize("overrides,retained,overflow", CASES)
def test_real_pool_capacity_return_reuse_and_dispose(overrides, retained, overflow):
    settings = MySQLSettings("synthetic", "t44_unit", "synthetic", "synthetic", **overrides)
    created = []

    class SyntheticConnection:
        def __init__(self):
            self.closes = 0

        def rollback(self):
            pass  # QueuePool reset calls a synthetic DBAPI method; there is no SQL implementation.

        def close(self):
            self.closes += 1

    def creator():
        connection = SyntheticConnection()
        created.append(connection)
        return connection

    pool = QueuePool(
        creator, pool_size=settings.pool_size, max_overflow=settings.max_overflow, timeout=0
    )
    peak = retained + overflow
    try:
        assert created == []  # Construction remains lazy.
        for wave in range(2):
            borrowed = []
            try:
                for _ in range(peak):
                    borrowed.append(pool.connect())
                with pytest.raises(PoolTimeout):
                    pool.connect()  # No waiting in this synthetic test; production timeout is below.
                assert pool.checkedout() == peak
            finally:
                for connection in borrowed:
                    connection.close()
            assert pool.checkedout() == 0
            assert pool.checkedin() == retained
            assert len(created) == peak + wave * overflow
            assert sum(connection.closes for connection in created) == (wave + 1) * overflow
    finally:
        pool.dispose()
    assert len(created) == retained + 2 * overflow
    assert all(connection.closes == 1 for connection in created)


@pytest.mark.parametrize("overrides,retained,overflow", CASES)
def test_settings_composition_and_actual_lazy_mysql_pool(monkeypatch, overrides, retained, overflow):
    import pymysql

    connect = Mock(side_effect=AssertionError("This unit test must not open a MySQL connection"))
    monkeypatch.setattr(pymysql, "connect", connect)
    monkeypatch.setenv("T44_DATABASE", "t44_unit")
    settings = Settings(database_url="mysql+pymysql://synthetic:synthetic@127.0.0.1/t44_unit")
    configured = replace(settings.mysql_settings(), **overrides)
    engine = create_mysql_engine(configured)
    try:
        assert isinstance(engine.pool, QueuePool)
        assert (engine.pool.size(), engine.pool._max_overflow) == (retained, overflow)
        assert engine.pool.timeout() == 10 and engine.pool._recycle == 1800
        assert engine.pool._pre_ping and engine.pool._pool.use_lifo
        assert engine.pool._reset_on_return.name == "reset_rollback"
        assert engine.dialect._on_connect_isolation_level == "READ COMMITTED"
        assert event.contains(engine, "connect", initialize_mysql_session)
        assert engine.hide_parameters is True
        assert engine.pool.checkedin() == engine.pool.checkedout() == 0
        connect.assert_not_called()
    finally:
        engine.dispose()
    connect.assert_not_called()
