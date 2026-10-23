"""Field-independent persistence foundation; no ORM models, migrations or business repositories."""

from .engine import MySQLSettings, create_mysql_engine
from .errors import (
    CommitUncertain,
    PersistenceError,
    PersistenceIntegrityError,
    PersistenceUnavailable,
    StatementRejected,
    TransactionStateError,
)
from .gateway import TableBinding
from .uow import SqlAlchemyUnitOfWork, SqlAlchemyUnitOfWorkFactory

__all__ = [
    "CommitUncertain",
    "MySQLSettings",
    "PersistenceError",
    "PersistenceIntegrityError",
    "PersistenceUnavailable",
    "SqlAlchemyUnitOfWork",
    "SqlAlchemyUnitOfWorkFactory",
    "StatementRejected",
    "TableBinding",
    "TransactionStateError",
    "create_mysql_engine",
]
