"""Opt-in source935 developer timings. Import creates no app, engine, thread or connection."""

import atexit
import contextlib
import contextvars
import functools
import hashlib
import json
import os
import re
import sys
import threading
import time
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID, uuid4

from sqlalchemy import event

PRODUCT = "935ab5b93bea788672c2b4a088c79cfeed848954"
HASHES = {
    "api.py": "2db431218d7c182dd114b7e616442478539396dcf86cccca42a537250356075e",
    "services/runtime.py": "9e0d770e4d5a646b406e1b1a3e328a7e369219d8821dbfcc008303547fe6825b",
    "services/workflow.py": "e0db3ff784330adf949c4b38ef7677e78e73a5f0da48f74f0acf1e09595ed41f",
    "contracts/openapi.json": "6f07cb53a7d9314240ba93ec490325d3c63dca7e4d077021047e216e7b26f478",
    "persistence/engine.py": "f7ec591dad711e3755aeda2606cee8dcaa023b416d8c51592b7b87684121ab9d",
}


def utc():
    return datetime.now(UTC).isoformat()


def request_id(value):
    try:
        return str(UUID(value))
    except (ValueError, TypeError, AttributeError):
        return None


class Probe:
    def __init__(self, engine, directory, limit=128, sample_all=False):
        directory = Path(directory)
        if not directory.is_absolute() or directory.is_symlink() or not directory.is_dir():
            raise ValueError("Explicit existing nonsymlink output directory required")
        if type(limit) is not int or not 1 <= limit <= 10000:
            raise ValueError("Sample cap must be 1..10000")
        self.engine, self.limit = engine, limit
        self.sample_all = sample_all
        self.active = contextvars.ContextVar("diag810_record", default=None)
        self.lock, self.write_lock = threading.Lock(), threading.Lock()
        self.selected = self.written = self.capped = self.writer_ns = 0
        self.errors, self.restores, self.listeners = Counter(), [], []
        self.closed, self.queue_get_available = False, False
        self.on_close = None
        self.path = directory / f"stage-{os.getpid()}-{uuid4().hex}.jsonl"
        self.fd = os.open(self.path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        self.emit(
            {
                "kind": "probe_start",
                "utc": utc(),
                "pid": os.getpid(),
                "product_reference": PRODUCT,
                "generic_probe_does_not_attest_product": True,
                "limit": limit,
                "sample_mode": "all" if sample_all else "explicit_header",
                "inclusive_phases_overlap": True,
                "cpu_scope": "same synchronous calling thread only",
                "pool_connect_scope": "includes queue/creation/preping/checkout, not pure wait",
                "queue_get_scope": "actual internal Queue.get incl bookkeeping; Empty can be normal",
                "pool_snapshot_scope": "non-atomic original size/checkedin/checkedout/overflow",
                "writer_scope": "after app returns; overhead nonzero, separately accumulated",
            }
        )

    def emit(self, value):
        start = time.perf_counter_ns()
        try:
            raw = (json.dumps(value, separators=(",", ":")) + "\n").encode()
            with self.write_lock:
                while raw:
                    count = os.write(self.fd, raw)
                    if count <= 0:
                        raise OSError("Diagnostic output did not progress")
                    raw = raw[count:]
            return True
        except Exception as error:
            self.errors[type(error).__name__] += 1
            return False
        finally:
            self.writer_ns += time.perf_counter_ns() - start

    def observe(self, action, *args):
        try:
            return action(*args)
        except Exception as error:
            self.errors[type(error).__name__] += 1
            return None

    def add(self, row, label, wall, cpu, raised=None):
        if row is None:
            return
        try:
            phase = row["phases"].setdefault(
                label, {"calls": 0, "wall_ns": 0, "thread_cpu_ns": 0, "raised_classes": {}}
            )
            phase["calls"] += 1
            phase["wall_ns"] += wall
            phase["thread_cpu_ns"] += cpu
            if raised:
                phase["raised_classes"][raised] = phase["raised_classes"].get(raised, 0) + 1
        except Exception as error:
            self.errors[type(error).__name__] += 1

    @contextlib.contextmanager
    def span(self, label):
        row = self.active.get()
        if row is None:
            yield
            return
        wall, cpu, raised = time.perf_counter_ns(), time.thread_time_ns(), None
        try:
            yield
        except BaseException as error:
            raised = type(error).__name__
            raise
        finally:
            end_cpu, end_wall = time.thread_time_ns(), time.perf_counter_ns()
            self.observe(self.add, row, label, end_wall - wall, end_cpu - cpu, raised)

    def wrap(self, owner, name, label):
        original = getattr(owner, name)

        @functools.wraps(original)
        def timed(*args, **kwargs):
            with self.span(label):
                return original(*args, **kwargs)

        setattr(owner, name, timed)
        self.restores.append((owner, name, original))

    def pool_snapshot(self, label):
        row = self.active.get()
        if row is None:
            return
        try:
            values = {}
            for name in ("size", "checkedin", "checkedout", "overflow"):
                method = getattr(self.engine.pool, name, None)
                values[name] = method() if callable(method) else None
            values.update(at_ns=time.perf_counter_ns(), point=label)
            if len(row["pool_samples"]) < 16:
                row["pool_samples"].append(values)
            peak = row.get("pool_peak_checkedout")
            if values["checkedout"] is not None:
                row["pool_peak_checkedout"] = max(peak or 0, values["checkedout"])
        except Exception as error:
            self.errors[type(error).__name__] += 1

    def install_database(self):
        self.wrap(self.engine.pool, "connect", "pool_connect_inclusive")
        queue = getattr(self.engine.pool, "_pool", None)
        if callable(getattr(queue, "get", None)):
            self.wrap(queue, "get", "pool_queue_get_inclusive")
            self.queue_get_available = True

        def before(_connection, _cursor, _statement, _parameters, context, _many):
            row = self.active.get()
            if row is not None:
                context._diag810 = (row, time.perf_counter_ns(), time.thread_time_ns())

        def finish(context, raised=None):
            saved = getattr(context, "_diag810", None)
            if saved is not None:
                end_cpu, end_wall = time.thread_time_ns(), time.perf_counter_ns()
                del context._diag810
                row, wall, cpu = saved
                self.add(row, "cursor_execute_inclusive", end_wall - wall, end_cpu - cpu, raised)

        def after(_connection, _cursor, _statement, _parameters, context, _many):
            finish(context)

        def failed(context):
            finish(context.execution_context, type(context.original_exception).__name__)

        def checkout(*_args):
            self.pool_snapshot("checkout_callback")

        def checkin(*_args):
            self.pool_snapshot("checkin_callback_before_pool_return")

        for name, callback in (
            ("before_cursor_execute", before),
            ("after_cursor_execute", after),
            ("handle_error", failed),
            ("checkout", checkout),
            ("checkin", checkin),
        ):
            target = self.engine.pool if name in ("checkout", "checkin") else self.engine

            def guarded(*args, _callback=callback):
                return self.observe(_callback, *args)

            event.listen(target, name, guarded)
            self.listeners.append((target, name, guarded))
        return self

    def install_application(self, app):
        from fastapi.responses import JSONResponse
        from fastapi.routing import APIRoute
        from t44 import api
        from t44.services import application, runtime

        for owner, name, label in (
            (api, "validate_request", "request_validation"),
            (api, "violations", "api_schema_validation"),
            (api, "wire", "api_wire"),
            (runtime.Runtime, "execute", "runtime_execute"),
            (runtime, "wire", "runtime_wire"),
            (application.Business, "dispatch", "business_dispatch"),
            (application.Business, "validate_data", "precommit_validation"),
            (JSONResponse, "render", "json_response_render"),
        ):
            self.wrap(owner, name, label)
        for route in app.routes:
            if isinstance(route, APIRoute):
                original = route.dependant.call
                route.dependant.call = self.handler(original, route.name)
                self.restores.append((route.dependant, "call", original))
        return self

    def handler(self, original, operation):
        @functools.wraps(original)
        def called(request):
            row = self.active.get()
            if row is not None:
                row.update(
                    operation=operation,
                    handler_thread=threading.get_ident(),
                    handler_start_ns=time.perf_counter_ns(),
                    request_id=request_id(getattr(request.state, "request_id", None)),
                )
                self.pool_snapshot("handler_start")
            try:
                with self.span("sync_handler_inclusive"):
                    return original(request)
            finally:
                if row is not None:
                    row["handler_end_ns"] = time.perf_counter_ns()
                    self.pool_snapshot("handler_end")

        return called

    def wrap_asgi(self, app):
        probe = self

        async def wrapped(scope, receive, send):
            if scope["type"] != "http":
                try:
                    return await app(scope, receive, send)
                finally:
                    if scope["type"] == "lifespan":
                        probe.close()
            requested = probe.sample_all or (b"x-t44-diag-sample", b"1") in scope.get("headers", ())
            with probe.lock:
                chosen = requested and probe.selected < probe.limit
                if chosen:
                    probe.selected += 1
                elif requested:
                    probe.capped += 1
            if not chosen:
                return await app(scope, receive, send)
            row = {
                "kind": "request",
                "pid": os.getpid(),
                "utc_start": utc(),
                "ingress_ns": time.perf_counter_ns(),
                "request_id": None,
                "phases": {},
                "pool_samples": [],
                "response_bytes": 0,
            }
            token = probe.active.set(row)

            async def received():
                message = await receive()
                if message["type"] == "http.request" and not message.get("more_body", False):
                    row.setdefault("body_consumed_ns", time.perf_counter_ns())
                return message

            async def sent(message):
                if message["type"] == "http.response.start":
                    row.update(response_start_ns=time.perf_counter_ns(), status=message["status"])
                    for key, value in message.get("headers", ()):
                        if key.lower() == b"x-request-id":
                            identifier = request_id(value.decode("ascii", errors="ignore"))
                            row["response_request_id"] = identifier
                            row["request_id_mismatch"] = row["request_id"] not in (None, identifier)
                await send(message)
                if message["type"] == "http.response.body":
                    row["response_bytes"] += len(message.get("body", b""))
                    if not message.get("more_body", False):
                        row["send_end_ns"] = time.perf_counter_ns()

            try:
                return await app(scope, received, sent)
            except BaseException as error:
                row["app_exception_class"] = type(error).__name__
                raise
            finally:
                row.update(
                    app_return_ns=time.perf_counter_ns(),
                    utc_end=utc(),
                    queue_get_available=probe.queue_get_available,
                )
                probe.active.reset(token)
                if probe.emit(row):
                    probe.written += 1

        return wrapped

    def close(self):
        if self.closed:
            return
        self.closed = True
        for target, name, callback in reversed(self.listeners):
            try:
                event.remove(target, name, callback)
            except Exception as error:
                self.errors[type(error).__name__] += 1
        for owner, name, original in reversed(self.restores):
            self.observe(setattr, owner, name, original)
        checkedout = getattr(self.engine.pool, "checkedout", None)
        checkedout = self.observe(checkedout) if callable(checkedout) else None
        if self.on_close is not None:
            self.observe(self.on_close)
        self.emit(
            {
                "kind": "probe_final",
                "utc": utc(),
                "selected": self.selected,
                "written": self.written,
                "cap_skips": self.capped,
                "checkedout_before_owner_dispose": checkedout,
                "owner_dispose_requested": self.on_close is not None,
                "writer_ns_before_final": self.writer_ns,
                "queue_get_available": self.queue_get_available,
                "diagnostic_valid": not self.errors and self.selected == self.written,
                "observer_errors": dict(self.errors),
            }
        )
        try:
            os.close(self.fd)
        except OSError as error:
            self.errors[type(error).__name__] += 1
        if self.errors:
            sys.stderr.write("T44_DIAG_INVALID " + json.dumps(dict(self.errors)) + "\n")


def app_factory():
    if os.environ.get("T44_DIAG_ALLOW") != "source935-development-only":
        raise ValueError("Explicit diagnostic admission required")
    if os.environ.get("T44_DIAG_PRODUCT_SHA") != PRODUCT:
        raise ValueError("Wrong explicit product source")
    module_sha = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    if os.environ.get("T44_DIAG_MODULE_SHA256") != module_sha:
        raise ValueError("Diagnostic module hash mismatch")
    from t44 import api
    from t44.persistence import SqlAlchemyUnitOfWorkFactory, create_mysql_engine
    from t44.settings import Settings

    package = Path(api.__file__).parent
    if any(
        hashlib.sha256((package / name).read_bytes()).hexdigest() != value
        for name, value in HASHES.items()
    ):
        raise ValueError("Product source fingerprint mismatch; not full image attestation")
    settings = Settings.from_env()
    mysql = settings.mysql_settings()
    database = os.environ["T44_DIAG_DATABASE"]
    if database != "t44c_r9diag935_p" and not re.fullmatch(
        r"t44_diag810_[A-Za-z0-9_]{1,40}", database
    ):
        raise ValueError("New diagnostic schema declaration required")
    if (
        mysql.database != database
        or os.environ.get("T44_DATABASE") != database
        or mysql.host != os.environ["T44_DIAG_HOST"]
        or mysql.port != int(os.environ["T44_DIAG_PORT"])
        or mysql.port == 13306
        or mysql.username != os.environ["T44_DIAG_USER"]
        or mysql.username == "root"
    ):
        raise ValueError("Diagnostic target differs from explicit fresh-schema packet")
    mode = os.getenv("T44_DIAG_SAMPLE_MODE", "header")
    if mode not in ("header", "all"):
        raise ValueError("Sample mode must be header or all")
    engine = create_mysql_engine(mysql)
    probe = Probe(
        engine,
        os.environ["T44_DIAG_OUTPUT"],
        int(os.getenv("T44_DIAG_LIMIT", "128")),
        mode == "all",
    )
    probe.on_close = engine.dispose
    probe.emit(
        {
            "kind": "source_binding",
            "product": PRODUCT,
            "verified_subset_sha256": HASHES,
            "module_sha256": module_sha,
            "full_image_attestation_is_external": True,
        }
    )
    try:
        probe.install_database()
        app = api.create_app(factory=SqlAlchemyUnitOfWorkFactory(engine), settings=settings)
        probe.install_application(app)
    except BaseException:
        probe.close()
        engine.dispose()
        raise
    atexit.register(probe.close)
    return probe.wrap_asgi(app)
