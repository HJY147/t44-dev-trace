"""Composition-root engine construction; no connection at import or business-call time."""

import re
from dataclasses import dataclass, field

from sqlalchemy import URL, Engine, create_engine, event

from .errors import PersistenceUnavailable, StatementRejected

_IDENTIFIER = re.compile(r"[a-zA-Z_][a-zA-Z0-9_]{0,63}\Z")
_MYSQL_SESSION_SQL = (
    "SET SESSION time_zone = '+00:00'",
    "SET SESSION sql_mode = 'STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,"
    "ERROR_FOR_DIVISION_BY_ZERO,ONLY_FULL_GROUP_BY,NO_ENGINE_SUBSTITUTION'",
    "SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED",
)


def validate_identifier(value: str) -> None:
    """Only trusted configuration identifiers, never SQL fragments or user selectors."""
    if not isinstance(value, str) or not _IDENTIFIER.fullmatch(value):
        raise StatementRejected("Identifier is not permitted")


@dataclass(frozen=True)
class MySQLSettings:
    host: str
    database: str
    username: str
    password: str = field(repr=False)
    port: int = 3306
    pool_size: int = 5
    max_overflow: int = 10
    pool_timeout: int = 10
    pool_recycle: int = 1800
    connect_timeout: int = 10
    read_timeout: int = 30
    write_timeout: int = 30

    def __post_init__(self) -> None:
        validate_identifier(self.database)
        if (
            not isinstance(self.host, str)
            or not self.host
            or not isinstance(self.username, str)
            or not self.username
            or not isinstance(self.password, str)
        ):
            raise ValueError("Database credentials/configuration are incomplete")
        positive = (
            self.pool_size,
            self.pool_timeout,
            self.pool_recycle,
            self.connect_timeout,
            self.read_timeout,
            self.write_timeout,
        )
        if any(type(n) is not int or n <= 0 for n in positive):
            raise ValueError("Pool and timeout settings must be positive integers")
        if type(self.max_overflow) is not int or self.max_overflow < 0:
            raise ValueError("Pool overflow must be a nonnegative integer")
        if type(self.port) is not int or not 1 <= self.port <= 65535:
            raise ValueError("Database port is invalid")


def initialize_mysql_session(dbapi_connection, _connection_record) -> None:
    """Called for each new physical DBAPI connection, before it enters the pool."""
    try:
        cursor = dbapi_connection.cursor()
        try:
            for statement in _MYSQL_SESSION_SQL:
                cursor.execute(statement)
        finally:
            cursor.close()
    except Exception:
        raise PersistenceUnavailable("Database session initialization failed") from None


def create_mysql_engine(settings: MySQLSettings) -> Engine:
    url = URL.create(
        "mysql+pymysql",
        username=settings.username,
        password=settings.password,
        host=settings.host,
        port=settings.port,
        database=settings.database,
        query={"charset": "utf8mb4"},
    )
    engine = create_engine(
        url,
        pool_size=settings.pool_size,
        max_overflow=settings.max_overflow,
        pool_timeout=settings.pool_timeout,
        pool_recycle=settings.pool_recycle,
        pool_pre_ping=True,
        pool_use_lifo=True,
        pool_reset_on_return="rollback",
        isolation_level="READ COMMITTED",
        hide_parameters=True,
        echo=False,
        echo_pool=False,
        connect_args={
            "connect_timeout": settings.connect_timeout,
            "read_timeout": settings.read_timeout,
            "write_timeout": settings.write_timeout,
        },
    )
    event.listen(engine, "connect", initialize_mysql_session, insert=True)
    return engine
