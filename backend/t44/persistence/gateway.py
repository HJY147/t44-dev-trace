"""Internal Core statements over composition-root allowlists; no raw SQL entry point."""

from collections.abc import Callable, Mapping
from dataclasses import dataclass

from sqlalchemy import Table, bindparam, insert, select, update
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session
from sqlalchemy.sql import ClauseElement

from .engine import validate_identifier
from .errors import PersistenceIntegrityError, PersistenceUnavailable, StatementRejected


@dataclass(frozen=True)
class TableBinding:
    """Trusted internal table/column policy, injected once, never built from request input."""

    table: Table
    readable: tuple[str, ...]
    writable: tuple[str, ...]
    filterable: tuple[str, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.table, Table):
            raise StatementRejected("A trusted Core table is required")
        validate_identifier(self.table.name)
        if self.table.schema is not None:
            validate_identifier(self.table.schema)
        for column in self.table.columns:
            validate_identifier(column.name)
        for policy in (self.readable, self.writable, self.filterable):
            if not isinstance(policy, tuple) or len(set(policy)) != len(policy):
                raise StatementRejected("Column policy must be an immutable unique tuple")
            if any(not isinstance(name, str) or name not in self.table.c for name in policy):
                raise StatementRejected("Column is absent from the trusted table")


class CoreGateway:
    def __init__(
        self,
        binding: TableBinding,
        active_session: Callable[[], Session],
        mark_failed: Callable[[], None],
    ):
        self._binding = binding
        self._active_session = active_session
        self._mark_failed = mark_failed

    def _values(self, values: Mapping, allowed: tuple[str, ...], prefix: str):
        if not isinstance(values, Mapping) or not values:
            raise StatementRejected("Nonempty bound fields are required")
        if any(
            not isinstance(name, str) or name not in allowed or isinstance(value, ClauseElement)
            for name, value in values.items()
        ):
            raise StatementRejected("Field or SQL expression is not permitted")
        columns, params = {}, {}
        for index, (name, value) in enumerate(values.items()):
            key = f"{prefix}_{index}"
            columns[name] = bindparam(key)
            params[key] = value
        return columns, params

    def _where(self, filters: Mapping):
        values, params = self._values(filters, self._binding.filterable, "filter")
        clauses = [
            self._binding.table.c[name].is_(None)
            if params[value.key] is None
            else self._binding.table.c[name] == value
            for name, value in values.items()
        ]
        return clauses, params

    def _execute(self, statement, params: dict, *, rows: bool):
        session = self._active_session()
        try:
            with session.execute(statement, params) as result:
                if rows:
                    return [dict(row) for row in result.mappings()]
                return result.rowcount
        except IntegrityError:
            self._mark_failed()
            raise PersistenceIntegrityError("Database constraint rejected the operation") from None
        except SQLAlchemyError:
            self._mark_failed()
            raise PersistenceUnavailable("Database operation failed") from None

    def find(self, filters: Mapping, *, limit: int) -> list[dict]:
        if type(limit) is not int or limit < 1 or not self._binding.readable:
            raise StatementRejected("A positive limit and readable fields are required")
        clauses, params = self._where(filters)
        statement = select(*(self._binding.table.c[c] for c in self._binding.readable))
        statement = statement.where(*clauses).limit(bindparam("row_limit"))
        return self._execute(statement, {**params, "row_limit": limit}, rows=True)

    def insert(self, values: Mapping) -> int:
        fields, params = self._values(values, self._binding.writable, "value")
        return self._execute(insert(self._binding.table).values(**fields), params, rows=False)

    def update_where(self, filters: Mapping, values: Mapping) -> int:
        fields, params = self._values(values, self._binding.writable, "value")
        clauses, where_params = self._where(filters)
        statement = update(self._binding.table).where(*clauses).values(**fields)
        return self._execute(statement, {**params, **where_params}, rows=False)
