"""Explicit, temporary observer for a single-engine developer diagnostic process."""

import copy
import hashlib
import re
import threading
import time
import uuid
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import UTC, datetime
from functools import wraps


def _utc():
    return datetime.now(UTC).isoformat()


class DatabaseTrace:
    """Inclusive nested times, no credentials, SQL text, bindings or exception messages."""

    def __init__(self, max_requests=64, max_sql_samples=200):
        if type(max_requests) is not int or not 1 <= max_requests <= 1000:
            raise ValueError("max_requests must be an integer in1..1000")
        if type(max_sql_samples) is not int or not 1 <= max_sql_samples <= 1000:
            raise ValueError("max_sql_samples must be an integer in1..1000")
        self.max_requests, self.max_sql_samples = max_requests, max_sql_samples
        self._current = ContextVar("database_diagnostic_record", default=None)
        self._lock = threading.RLock()
        self._records, self._patches, self._listeners = [], [], []
        self._global_phases, self._pending = {}, {}
        self._dbapi_timeouts, self._ping_false = [], 0
        self.engine = None

    def _add(self, record, name, start, cpu, error=None):
        spent = time.thread_time_ns() - cpu
        wall = time.perf_counter_ns() - start
        with self._lock:
            phases = self._global_phases if record is None else record["phases"]
            phase = phases.setdefault(
                name, {"count": 0, "wall_ns": 0, "thread_cpu_ns": 0, "errors": 0}
            )
            phase["count"] += 1
            phase["wall_ns"] += wall
            phase["thread_cpu_ns"] += spent
            phase["errors"] += error is not None
        return wall, spent

    def _timed(self, name, function):
        @wraps(function)
        def measured(*args, **kwargs):
            record = self._current.get()
            start, cpu, error = time.perf_counter_ns(), time.thread_time_ns(), None
            try:
                return function(*args, **kwargs)
            except BaseException as caught:
                error = type(caught).__name__
                raise
            finally:
                self._add(record, name, start, cpu, error)

        return measured

    def _patch(self, owner, name, replacement):
        original = getattr(owner, name)
        if getattr(original, "_t44_database_observer", False):
            raise RuntimeError("A database diagnostic observer is already installed")
        replacement._t44_database_observer = True
        self._patches.append((owner, name, original))
        setattr(owner, name, replacement)

    def _mine(self, session):
        bind = getattr(session, "bind", None)
        return bind is self.engine or getattr(bind, "engine", None) is self.engine

    def install(self, engine):
        if self.engine is not None:
            raise RuntimeError("Observer is single-install")
        from sqlalchemy import event
        from sqlalchemy.orm import Session
        from t44.persistence import rows
        from t44.persistence.uow import SqlAlchemyUnitOfWork

        if engine.dialect.name not in {"mysql", "sqlite"}:
            raise ValueError("Only explicit MySQL/SQLite diagnostic engines are supported")
        self.engine = engine
        self._tables = set(rows.TABLES)
        observer = self
        try:
            self._patch(engine, "connect", self._timed("engine_acquire_inclusive", engine.connect))
            for method in ("connect", "do_ping", "do_close", "do_commit", "do_rollback"):
                original = getattr(engine.dialect, method)

                @wraps(original)
                def lifecycle(*args, _name=method, _fn=original, **kwargs):
                    value = _fn(*args, **kwargs)
                    if _name == "connect":
                        safe = {}
                        for field in ("connect_timeout", "_read_timeout", "_write_timeout"):
                            timeout = getattr(value, field, None)
                            safe[field.removeprefix("_")] = (
                                timeout if type(timeout) in (int, float) else None
                            )
                        if safe not in observer._dbapi_timeouts:
                            observer._dbapi_timeouts.append(safe)
                    elif _name == "do_ping" and value is False:
                        observer._ping_false += 1
                    return value

                self._patch(engine.dialect, method, self._timed("dbapi_" + method, lifecycle))
            original_execute = Session.execute

            @wraps(original_execute)
            def execute(session, *args, **kwargs):
                if not observer._mine(session):
                    return original_execute(session, *args, **kwargs)
                result = observer._timed("session_execute_inclusive", original_execute)(
                    session, *args, **kwargs
                )
                return _Result(result, observer)

            self._patch(Session, "execute", execute)
            for method in ("commit", "rollback", "close"):
                original = getattr(Session, method)

                def session_wrapper(session, *args, _name=method, _fn=original, **kwargs):
                    if not observer._mine(session):
                        return _fn(session, *args, **kwargs)
                    return observer._timed("session_" + _name + "_inclusive", _fn)(
                        session, *args, **kwargs
                    )

                self._patch(Session, method, wraps(original)(session_wrapper))
            for method in ("__enter__", "__exit__"):
                original = getattr(SqlAlchemyUnitOfWork, method)
                # The admitted process is a single-engine application. Do not call its
                # active-session callback an extra time just for instrumentation.
                self._patch(
                    SqlAlchemyUnitOfWork,
                    method,
                    self._timed("uow_" + method.strip("_") + "_inclusive", original),
                )
            self._patch(
                rows.RowsGateway,
                "_execute",
                self._timed("rows_execute_inclusive", rows.RowsGateway._execute),
            )
            self._patch(rows, "from_db_time", self._timed("codec_from_db_time", rows.from_db_time))
            for name, function in (
                ("before_cursor_execute", self._before),
                ("after_cursor_execute", self._after),
                ("handle_error", self._error),
            ):
                event.listen(engine, name, function)
                self._listeners.append((name, function))
        except BaseException:
            self.close()
            raise
        return self

    @contextmanager
    def request(self, operation_id, request_id=None):
        if self.engine is None:
            raise RuntimeError("Install an explicit engine first")
        if not isinstance(operation_id, str) or not re.fullmatch(
            r"[A-Za-z0-9_]{1,80}", operation_id
        ):
            raise ValueError("Operation must be a fixed operationId")
        if request_id is None:
            request_id = str(uuid.uuid4())
        if not isinstance(request_id, str) or str(uuid.UUID(request_id)) != request_id:
            raise ValueError("Request id must be a canonical UUID")
        if self._current.get() is not None:
            raise RuntimeError("Nested diagnostic requests are not supported")
        record = {
            "operation_id": operation_id,
            "request_id": request_id,
            "start_utc": _utc(),
            "start_monotonic_ns": time.monotonic_ns(),
            "start_perf_ns": time.perf_counter_ns(),
            "thread_id": threading.get_ident(),
            "phases": {},
            "sql": [],
            "sql_samples_dropped": 0,
            "mapping_rows": 0,
        }
        with self._lock:
            if len(self._records) >= self.max_requests:
                raise RuntimeError("Diagnostic request limit reached")
            self._records.append(record)
        token = self._current.set(record)
        cpu = time.thread_time_ns()
        try:
            yield record
        except BaseException as error:
            record["exception_class"] = type(error).__name__
            raise
        finally:
            record["thread_cpu_ns"] = time.thread_time_ns() - cpu
            record["end_perf_ns"] = time.perf_counter_ns()
            record["end_monotonic_ns"] = time.monotonic_ns()
            record["end_utc"] = _utc()
            record["wall_ns"] = record["end_perf_ns"] - record["start_perf_ns"]
            self._current.reset(token)

    def _before(self, connection, cursor, statement, parameters, context, executemany):
        record = self._current.get()
        verb = statement.lstrip().split(None, 1)[0].upper() if statement.strip() else "EMPTY"
        tables = {
            match.group(1)
            for match in re.finditer(
                r"\b(?:FROM|JOIN|INTO|UPDATE)\s+[`\"]?([A-Za-z0-9_]+)", statement, re.I
            )
            if match.group(1) in self._tables
        }
        self._pending[id(context)] = (
            record,
            time.perf_counter_ns(),
            time.thread_time_ns(),
            {
                "verb": verb
                if verb in {"SELECT", "INSERT", "UPDATE", "DELETE", "SET"}
                else "OTHER",
                "tables": sorted(tables),
                "shape_sha256": hashlib.sha256(statement.encode()).hexdigest(),
            },
        )

    def _finish(self, context, error=None):
        entry = self._pending.pop(id(context), None)
        if entry is None:
            return
        record, start, cpu, shape = entry
        wall, spent = self._add(record, "cursor_execute_inclusive", start, cpu, error)
        if record is not None:
            sample = {**shape, "wall_ns": wall, "thread_cpu_ns": spent, "error_class": error}
            if len(record["sql"]) < self.max_sql_samples:
                record["sql"].append(sample)
            else:
                record["sql_samples_dropped"] += 1

    def _after(self, connection, cursor, statement, parameters, context, executemany):
        self._finish(context)

    def _error(self, exception_context):
        self._finish(
            exception_context.execution_context,
            type(exception_context.original_exception).__name__,
        )

    def snapshot(self):
        if self.engine is None:
            raise RuntimeError("Observer is not installed")
        pool = self.engine.pool
        metadata = {"type": type(pool).__name__}
        for name in ("size", "checkedin", "checkedout", "overflow"):
            function = getattr(pool, name, None)
            metadata[name] = (
                function() if callable(function) else function if type(function) is int else None
            )
        for field in ("_max_overflow", "_timeout", "_recycle", "_pre_ping"):
            value = getattr(pool, field, None)
            metadata[field.removeprefix("_")] = (
                value if isinstance(value, (int, float, bool)) else None
            )
        with self._lock:
            return copy.deepcopy(
                {
                    "schema": "database_trace_v1",
                    "dialect": self.engine.dialect.name,
                    "driver": self.engine.dialect.driver,
                    "actual_pool": metadata,
                    "records": self._records,
                    "outside_request_phases": self._global_phases,
                    "actual_dbapi_timeout_profiles": self._dbapi_timeouts,
                    "ping_returned_false": self._ping_false,
                    "pending_cursor_spans": len(self._pending),
                    "timing_scope": "nested inclusive times; do not sum or label as pure queue/lock/server time",
                    "clock_scope": "CPU endpoint read before wall endpoint; UTC formatting excluded from CPU; clock reads are not atomic",
                    "rows_uow_scope": "single-engine application assumption; Session and cursor hooks explicitly target installed engine",
                    "result_scope": "proxy preserves operations used by production Rows; not a general Result type substitute",
                    "privacy": "no SQL text, bindings, URL, credentials, body or exception messages",
                }
            )

    def close(self):
        if self.engine is not None:
            from sqlalchemy import event

            for name, function in reversed(self._listeners):
                event.remove(self.engine, name, function)
            self._listeners.clear()
        for owner, name, original in reversed(self._patches):
            setattr(owner, name, original)
        self._patches.clear()
        self.engine = None


class _Result:
    def __init__(self, result, observer):
        self._result, self._observer = result, observer

    def __getattr__(self, name):
        return getattr(self._result, name)

    def __enter__(self):
        self._result.__enter__()
        return self

    def __exit__(self, *args):
        return self._result.__exit__(*args)

    def mappings(self):
        return _Mappings(self._result.mappings(), self._observer)

    def scalar_one(self):
        return self._observer._timed("result_scalar_one_inclusive", self._result.scalar_one)()


class _Mappings:
    def __init__(self, result, observer):
        self._result, self._observer = result, observer

    def __getattr__(self, name):
        return getattr(self._result, name)

    def __iter__(self):
        iterator = iter(self._result)
        while True:
            record = self._observer._current.get()
            start, cpu, error = time.perf_counter_ns(), time.thread_time_ns(), None
            try:
                row = next(iterator)
            except StopIteration:
                return
            except BaseException as caught:
                error = type(caught).__name__
                raise
            finally:
                self._observer._add(record, "mapping_next_inclusive", start, cpu, error)
            if record is not None:
                record["mapping_rows"] += 1
            yield row
