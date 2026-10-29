"""Single-use, injected session lifecycle with no schema or business-state assumptions."""

from collections.abc import Callable
from contextlib import suppress

from sqlalchemy import Engine
from sqlalchemy.orm import Session, sessionmaker

from .errors import CommitUncertain, PersistenceUnavailable, TransactionStateError
from .rows import RowsGateway


class SqlAlchemyUnitOfWork:
    def __init__(self, session_factory: Callable[[], Session]):
        self._session_factory = session_factory
        self._session: Session | None = None
        self._state = "new"
        self._rollback_only = False
        self._gateway = RowsGateway(self._require_active, self._mark_failed)

    def __enter__(self) -> "SqlAlchemyUnitOfWork":
        if self._state != "new":
            raise TransactionStateError("Unit of work is single-use")
        try:
            self._session = self._session_factory()
            self._session.begin()
            self._state = "active"
        except Exception:
            self._close(suppress_errors=True)
            raise PersistenceUnavailable("Transaction could not start") from None
        except BaseException:
            self._close(suppress_errors=True)
            raise
        return self

    def _require_active(self) -> Session:
        if self._state != "active" or self._session is None:
            raise TransactionStateError("Unit of work is not active")
        if self._rollback_only:
            raise TransactionStateError("Transaction requires rollback")
        return self._session

    @property
    def gateway(self) -> RowsGateway:
        self._require_active()
        return self._gateway

    def _mark_failed(self) -> None:
        self._rollback_only = True

    def commit(self) -> None:
        if self._rollback_only:
            self.rollback()
            raise TransactionStateError("Failed transaction was rolled back")
        session = self._require_active()
        try:
            session.commit()
            self._state = "committed"
        except Exception:
            self._state = "uncertain"
            # Resource cleanup only. The server may already have committed.
            with suppress(Exception):
                session.rollback()
            raise CommitUncertain("Transaction commit was not confirmed") from None

    def rollback(self) -> None:
        if self._state != "active" or self._session is None:
            raise TransactionStateError("Unit of work is not active")
        try:
            self._session.rollback()
            self._state = "rolled_back"
        except Exception:
            self._state = "failed"
            raise PersistenceUnavailable("Transaction rollback failed") from None

    def _close(self, *, suppress_errors: bool = False) -> None:
        try:
            if self._session is not None:
                self._session.close()
        except Exception:
            if not suppress_errors:
                raise PersistenceUnavailable("Transaction resources could not close") from None
        finally:
            self._session = None
            self._state = "closed"

    def __exit__(self, exc_type, exc, traceback) -> bool:
        try:
            if self._state == "active":
                if exc_type is None:
                    self.commit()
                else:
                    self.rollback()
        finally:
            self._close(suppress_errors=self._state == "uncertain" or exc_type is not None)
        return False


class SqlAlchemyUnitOfWorkFactory:
    def __init__(self, engine: Engine):
        self._sessions = sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)

    def __call__(self) -> SqlAlchemyUnitOfWork:
        return SqlAlchemyUnitOfWork(self._sessions)
