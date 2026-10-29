"""Explicit pool configuration contracts only; no database, HTTP or SUT invocation."""

from dataclasses import asdict
from unittest.mock import Mock

import pytest
from sqlalchemy import event
from t44.persistence import MySQLSettings, create_mysql_engine
from t44.persistence.engine import initialize_mysql_session
from t44.settings import Settings

URL = "mysql+pymysql://synthetic:unit%2Fonly@mysql:3308/t44_test"


@pytest.fixture(autouse=True)
def isolated_environment(monkeypatch):
    for name in (
        "T44_DB_POOL_SIZE",
        "T44_DB_MAX_OVERFLOW",
        "T44_DATABASE",
        "DATABASE_URL",
        "T44_SESSION_TTL_SECONDS",
    ):
        monkeypatch.delenv(name, raising=False)
    connect = Mock(
        side_effect=AssertionError("Configuration must not connect to MySQL")
    )
    monkeypatch.setattr("pymysql.connect", connect)
    yield connect
    connect.assert_not_called()


def original_defaults():
    return MySQLSettings("mysql", "t44_test", "synthetic", "unit/only", port=3308)


def test_absent_pool_environment_preserves_every_original_field(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", URL)
    monkeypatch.setenv("T44_DATABASE", "t44_test")
    monkeypatch.setenv("T44_SESSION_TTL_SECONDS", "120")
    settings = Settings.from_env()
    assert asdict(settings.mysql_settings()) == asdict(original_defaults())
    assert asdict(settings) == {
        "database_url": URL,
        "session_ttl_seconds": 120,
        "login_attempts": 10,
        "login_window_seconds": 60,
        "idempotency_lease_seconds": 60,
    }
    assert "unit/only" not in repr(settings.mysql_settings())
    assert "unit%2Fonly" not in repr(settings)


@pytest.mark.parametrize(
    "size,overflow,expected",
    [
        ("5", "10", (5, 10)),
        ("15", "0", (15, 0)),
        ("20", "0", (20, 0)),
        ("5", "0", (5, 0)),
        (" 15 ", "+0", (15, 0)),
    ],
)
def test_explicit_pool_values_change_only_capacity(
    monkeypatch, size, overflow, expected
):
    monkeypatch.setenv("T44_DB_POOL_SIZE", size)
    monkeypatch.setenv("T44_DB_MAX_OVERFLOW", overflow)
    actual = asdict(Settings(database_url=URL).mysql_settings())
    capacity = actual.pop("pool_size"), actual.pop("max_overflow")
    previous = asdict(original_defaults())
    previous.pop("pool_size")
    previous.pop("max_overflow")
    assert capacity == expected
    assert actual == previous


@pytest.mark.parametrize(
    "name,value,expected",
    [("T44_DB_POOL_SIZE", "7", (7, 10)), ("T44_DB_MAX_OVERFLOW", "0", (5, 0))],
)
def test_each_override_keeps_other_default(monkeypatch, name, value, expected):
    monkeypatch.setenv(name, value)
    configured = Settings(database_url=URL).mysql_settings()
    assert (configured.pool_size, configured.max_overflow) == expected


@pytest.mark.parametrize("name", ["T44_DB_POOL_SIZE", "T44_DB_MAX_OVERFLOW"])
@pytest.mark.parametrize("value", ["", "invalid", "15.0", "True", "1e2", "none"])
def test_noninteger_environment_is_rejected_without_default_fallback(
    monkeypatch, name, value
):
    monkeypatch.setenv(name, value)
    with pytest.raises(ValueError):
        Settings(database_url=URL).mysql_settings()


@pytest.mark.parametrize(
    "name,value,message",
    [
        (
            "T44_DB_POOL_SIZE",
            "0",
            "Pool and timeout settings must be positive integers",
        ),
        (
            "T44_DB_POOL_SIZE",
            "-1",
            "Pool and timeout settings must be positive integers",
        ),
        ("T44_DB_MAX_OVERFLOW", "-1", "Pool overflow must be a nonnegative integer"),
    ],
)
def test_original_dataclass_capacity_boundaries_remain(
    monkeypatch, name, value, message
):
    monkeypatch.setenv(name, value)
    with pytest.raises(ValueError) as error:
        Settings(database_url=URL).mysql_settings()
    assert str(error.value) == message


@pytest.mark.parametrize(
    "url,declared,message",
    [
        (
            "sqlite:///unused.sqlite",
            None,
            "DATABASE_URL must select mysql+pymysql and an explicit database",
        ),
        (
            "mysql+pymysql://synthetic:unit-only@mysql",
            None,
            "DATABASE_URL must select mysql+pymysql and an explicit database",
        ),
        (URL, "different", "T44_DATABASE differs from DATABASE_URL"),
    ],
)
def test_original_url_and_declared_database_errors_precede_new_parsing(
    monkeypatch, url, declared, message
):
    monkeypatch.setenv("T44_DB_POOL_SIZE", "invalid")
    monkeypatch.setenv("T44_DB_MAX_OVERFLOW", "invalid")
    if declared is not None:
        monkeypatch.setenv("T44_DATABASE", declared)
    with pytest.raises(ValueError) as error:
        Settings(database_url=url).mysql_settings()
    assert str(error.value) == message


def test_database_url_is_stored_but_pool_environment_is_read_at_conversion(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", URL)
    monkeypatch.setenv("T44_DB_POOL_SIZE", "invalid")
    configured = Settings.from_env()
    monkeypatch.setenv("DATABASE_URL", "sqlite:///must-not-replace-stored-url.sqlite")
    with pytest.raises(ValueError):
        configured.mysql_settings()
    monkeypatch.setenv("T44_DB_POOL_SIZE", "15")
    monkeypatch.setenv("T44_DB_MAX_OVERFLOW", "0")
    actual = configured.mysql_settings()
    assert (
        actual.database == "t44_test" and actual.host == "mysql" and actual.port == 3308
    )
    assert (actual.pool_size, actual.max_overflow) == (15, 0)


@pytest.mark.parametrize("size,overflow", [(5, 10), (15, 0), (20, 0), (5, 0)])
def test_capacity_reaches_original_lazy_engine_without_connecting(
    monkeypatch, size, overflow
):
    monkeypatch.setenv("T44_DB_POOL_SIZE", str(size))
    monkeypatch.setenv("T44_DB_MAX_OVERFLOW", str(overflow))
    engine = create_mysql_engine(Settings(database_url=URL).mysql_settings())
    try:
        assert engine.pool.size() == size and engine.pool._max_overflow == overflow
        assert engine.pool.checkedout() == 0
        assert engine.hide_parameters is True
        assert event.contains(engine, "connect", initialize_mysql_session)
        assert engine.dialect._on_connect_isolation_level == "READ COMMITTED"
    finally:
        engine.dispose()
