"""Trusted 18-table facade. Predicates/identifiers are compiled from allowlists only."""

from collections.abc import Mapping
from contextlib import contextmanager
from dataclasses import dataclass

from sqlalchemy import DateTime, bindparam, delete, func, insert, select, text, tuple_, update
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.sql import ClauseElement

from .codecs import from_db_time, to_db_time
from .errors import (
    PersistenceIntegrityError,
    PersistenceUnavailable,
    StatementRejected,
    TransactionStateError,
)
from .schema import TABLES


@dataclass(frozen=True)
class Pred:
    column: str
    op: str
    value: object = None


class RowsGateway:
    def __init__(self, active_session, mark_failed):
        self._session, self._mark_failed = active_session, mark_failed
        self._scopes = []

    def _table(self, name):
        if not isinstance(name, str) or name not in TABLES:
            raise StatementRejected("Table is outside the frozen registry")
        return TABLES[name]

    def _fields(self, table, values):
        if not isinstance(values, Mapping):
            raise StatementRejected("Bound fields must be a mapping")
        if any(not isinstance(k, str) or k not in table.c for k in values):
            raise StatementRejected("Field or SQL expression is not permitted")

        def safe(value):
            if isinstance(value, ClauseElement):
                raise StatementRejected("SQL expressions cannot be bound values")
            if isinstance(value, (list, tuple, set)):
                for item in value:
                    safe(item)
            elif isinstance(value, dict):
                for item in value.values():
                    safe(item)

        for value in values.values():
            safe(value)
        return {
            k: to_db_time(v) if isinstance(table.c[k].type, DateTime) and v is not None else v
            for k, v in values.items()
        }

    def _clauses(self, table, where, predicates):
        values = self._fields(table, where or {})
        parts = [
            Pred(k, "in" if isinstance(v, (list, tuple, set)) else "eq", v)
            for k, v in values.items()
        ]
        parts.extend(predicates)
        clauses = []
        for p in parts:
            if not isinstance(p, Pred) or p.column not in table.c:
                raise StatementRejected("Predicate is outside the frozen registry")
            column = table.c[p.column]
            value = (
                self._fields(table, {p.column: p.value})[p.column] if p.op != "is_null" else p.value
            )
            if p.op == "eq":
                clause = column.is_(None) if value is None else column == value
            elif p.op == "ne":
                clause = column.is_not(None) if value is None else column != value
            elif p.op == "is_null":
                clause = column.is_(None) if value is not False else column.is_not(None)
            elif p.op == "in":
                clause = column.in_(tuple(value))
            elif p.op in ("lt", "le", "gt", "ge"):
                clause = getattr(
                    column, {"lt": "__lt__", "le": "__le__", "gt": "__gt__", "ge": "__ge__"}[p.op]
                )(value)
            else:
                raise StatementRejected("Predicate operator is not permitted")
            clauses.append(clause)
        return clauses

    def _execute(self, statement, mode, parameters=None):
        try:
            with self._session().execute(statement, parameters) as result:
                if mode == "rows":
                    return [
                        {k: from_db_time(v) if hasattr(v, "tzinfo") else v for k, v in row.items()}
                        for row in result.mappings()
                    ]
                if mode == "id":
                    return int(result.inserted_primary_key[0])
                return result.scalar_one() if mode == "count" else result.rowcount
        except SQLAlchemyError as error:
            self._failed()
            original = getattr(error, "orig", None)
            code = original.args[0] if original is not None and original.args else None
            message = str(original)
            # PyMySQL reports MySQL CHECK 3819 as OperationalError, not IntegrityError.
            if not isinstance(error, IntegrityError) and code != 3819:
                raise PersistenceUnavailable("Database operation failed") from None
            kind = (
                "duplicate"
                if code == 1062 or "UNIQUE constraint" in message
                else (
                    "foreign_key"
                    if code in (1451, 1452) or "FOREIGN KEY constraint" in message
                    else "check"
                    if code == 3819 or "CHECK constraint" in message
                    else "other"
                )
            )
            known = [c.name for t in TABLES.values() for c in t.constraints if c.name]
            constraint = next((name for name in known if name in message), None)
            raise PersistenceIntegrityError(
                "Database constraint rejected the operation", kind=kind, constraint=constraint
            ) from None

    def _failed(self):
        if self._scopes:
            self._scopes[-1] = True
        else:
            self._mark_failed()

    @contextmanager
    def savepoint(self):
        transaction = self._session().begin_nested()
        self._scopes.append(False)
        try:
            yield self
            if self._scopes[-1]:
                raise TransactionStateError("Failed savepoint requires rollback")
            transaction.commit()
        except BaseException:
            transaction.rollback()
            raise
        finally:
            self._scopes.pop()

    def rows(
        self,
        table,
        where=None,
        *,
        columns=None,
        order_by=("id",),
        limit=None,
        offset=0,
        lock=None,
        skip_locked=False,
        predicates=(),
    ):
        t = self._table(table)
        fields = (
            tuple(t.c)
            if columns is None
            else tuple(t.c[k] for k in self._fields(t, dict.fromkeys(columns)))
        )
        order = []
        for field in order_by:
            descending = field.startswith("-")
            key = field.removeprefix("-")
            if key not in t.c:
                raise StatementRejected("Sort field is not permitted")
            order.append(t.c[key].desc() if descending else t.c[key])
        stmt = select(*fields).where(*self._clauses(t, where, predicates)).order_by(*order)
        if limit is not None:
            if type(limit) is not int or limit < 0:
                raise StatementRejected("Limit must be a nonnegative integer")
            stmt = stmt.limit(limit)
        if type(offset) is not int or offset < 0:
            raise StatementRejected("Offset must be a nonnegative integer")
        if offset:
            stmt = stmt.offset(offset)
        if lock not in (None, "share", "update") or (skip_locked and lock is None):
            raise StatementRejected("Lock mode is not permitted")
        if lock:
            stmt = stmt.with_for_update(read=lock == "share", skip_locked=skip_locked)
        return self._execute(stmt, "rows")

    def get(self, table, id, *, lock=None):
        rows = self.rows(table, {"id": id}, limit=1, lock=lock)
        return rows[0] if rows else None

    def task_schedule_changes(
        self, project_id: int, pairs: tuple[tuple[int, int], ...]
    ) -> list[dict]:
        """Read exact task/version pairs within one already authorized project page."""

        def integer(value, maximum):
            return type(value) is int and 1 <= value <= maximum

        if not integer(project_id, 4294967295) or type(pairs) is not tuple or len(pairs) > 100:
            raise StatementRejected("Schedule history requires a project and at most 100 pairs")
        if any(
            type(pair) is not tuple
            or len(pair) != 2
            or not integer(pair[0], 4294967295)
            or not integer(pair[1], 2147483647)
            for pair in pairs
        ):
            raise StatementRejected(
                "Schedule history pairs require bounded integer IDs and versions"
            )
        wanted = tuple(dict.fromkeys(pairs))
        if not wanted:
            return []
        table = TABLES["schedule_changes"]
        result = self._execute(
            select(table)
            .where(
                table.c.project_id == project_id,
                table.c.iteration_id.is_(None),
                tuple_(table.c.task_id, table.c.to_version).in_(wanted),
            )
            .order_by(table.c.task_id, table.c.to_version, table.c.id),
            "rows",
        )

        def unavailable():
            self._failed()
            raise PersistenceUnavailable(
                "Schedule history result violated its bounded read contract"
            )

        if type(result) is not list or len(result) > len(wanted):
            unavailable()
        seen, ids = set(), set()
        for row in result:
            if (
                not isinstance(row, dict)
                or set(row) != set(table.c.keys())
                or any(
                    not integer(row[key], maximum)
                    for key, maximum in (
                        ("id", 4294967295),
                        ("project_id", 4294967295),
                        ("task_id", 4294967295),
                        ("to_version", 2147483647),
                    )
                )
                or row["project_id"] != project_id
                or row["iteration_id"] is not None
            ):
                unavailable()
            pair = row["task_id"], row["to_version"]
            if pair not in wanted or pair in seen or row["id"] in ids:
                unavailable()
            seen.add(pair)
            ids.add(row["id"])
        return result

    def confirmed_missing(self, *, confirmed_before, limit):
        """Fixed MySQL query: complete old events must not consume the recovery limit."""
        if type(limit) is not int or limit < 1:
            raise StatementRejected("Recovery limit must be a positive integer")
        event = TABLES["outbox_events"]
        # Only this fixed internal fragment uses JSON_TABLE; no dynamic SQL/identifier input.
        missing = text("""EXISTS (
            SELECT 1 FROM JSON_TABLE(outbox_events.recipients, '$[*]'
                COLUMNS(recipient_id INT UNSIGNED PATH '$')) AS wanted
            WHERE NOT EXISTS (SELECT 1 FROM notifications AS notice
                WHERE notice.event_id=outbox_events.id
                  AND notice.recipient_id=wanted.recipient_id))""")
        statement = (
            select(event)
            .where(
                event.c.status == 3,
                event.c.event_type == 2,
                event.c.confirmed_at <= to_db_time(confirmed_before),
                missing,
            )
            .order_by(event.c.id)
            .limit(limit)
            .with_for_update(skip_locked=True)
        )
        return self._execute(statement, "rows")

    def insert(self, table, values):
        t = self._table(table)
        if not values:
            raise StatementRejected("Insert requires bound values")
        return self._execute(insert(t).values(**self._fields(t, values)), "id")

    def insert_many(self, table, values):
        t = self._table(table)
        if not values:
            return 0
        fields = [self._fields(t, row) for row in values]
        if not fields[0] or any(set(row) != set(fields[0]) for row in fields):
            raise StatementRejected("Batch inserts require identical nonempty fields")
        return self._execute(insert(t), "count_rows", fields)

    def update_many(self, table, values):
        t = self._table(table)
        if not values:
            return 0
        fields = [self._fields(t, row) for row in values]
        keys = set(fields[0]) - {"id"}
        if not keys or any(set(row) != keys | {"id"} for row in fields):
            raise StatementRejected("Batch updates require IDs and identical nonempty changes")
        parameters = [{"_pk": row["id"], **{k: row[k] for k in keys}} for row in fields]
        statement = (
            update(t).where(t.c.id == bindparam("_pk")).values({k: bindparam(k) for k in keys})
        )
        return self._execute(statement, "count_rows", parameters)

    def update(self, table, where, values, *, predicates=()):
        t = self._table(table)
        if not where or not values:
            raise StatementRejected("Update needs nonempty filters and values")
        return self._execute(
            update(t).where(*self._clauses(t, where, predicates)).values(**self._fields(t, values)),
            "count_rows",
        )

    update_where = update

    def delete(self, table, where):
        t = self._table(table)
        if not where:
            raise StatementRejected("Delete needs nonempty filters")
        return self._execute(delete(t).where(*self._clauses(t, where, ())), "count_rows")

    def count(self, table, where=None, *, predicates=()):
        t = self._table(table)
        return self._execute(
            select(func.count()).select_from(t).where(*self._clauses(t, where, predicates)), "count"
        )
