"""Stage-B-only isolated observer; no workload, connection or server starts on import."""

import argparse
import contextvars
import cProfile
import functools
import json
import os
import platform
import subprocess
import threading
import time
from importlib.metadata import version
from pathlib import Path
from uuid import uuid4

_RECORD = contextvars.ContextVar("profile_record", default=None)


def measured(name, function):
    @functools.wraps(function)
    def invoke(*args, **kwargs):
        record = _RECORD.get()
        started, cpu = time.perf_counter_ns(), time.thread_time_ns()
        try:
            return function(*args, **kwargs)
        finally:
            if record is not None:
                phase = record["phases"].setdefault(name, [0, 0, 0])
                phase[0] += 1
                phase[1] += time.perf_counter_ns() - started
                phase[2] += time.thread_time_ns() - cpu

    return invoke


def instrument(app, engine, output, profile):
    from sqlalchemy import event
    from t44 import api

    runtime = app.state.runtime
    for name in ("authorize", "claim", "locked_scope", "complete", "rejection", "audit"):
        setattr(runtime, name, measured(name, getattr(runtime, name)))
    for name in ("dispatch", "validate_data"):
        setattr(runtime.business, name, measured(name, getattr(runtime.business, name)))
    for name in ("validate_request", "violations", "wire"):
        setattr(api, name, measured("http_" + name, getattr(api, name)))
    engine.connect = measured("db_acquire_and_pre_ping", engine.connect)

    @event.listens_for(engine, "before_cursor_execute")
    def before(_conn, _cursor, _statement, _parameters, context, _many):
        context._t44_profile_started = time.perf_counter_ns()

    def sql_finished(context, failed=False):
        record = _RECORD.get()
        started = getattr(context, "_t44_profile_started", None)
        if record is not None and started is not None:
            record["sql_count"] += 1
            record["sql_wall_ns"] += time.perf_counter_ns() - started
            record["sql_errors"] += int(failed)

    @event.listens_for(engine, "after_cursor_execute")
    def after(_conn, _cursor, _statement, _parameters, context, _many):
        sql_finished(context)

    @event.listens_for(engine, "handle_error")
    def error(context):
        sql_finished(context.execution_context, True)

    execute = runtime.execute

    @functools.wraps(execute)
    def observed(call, *args, **kwargs):
        record = _RECORD.get()
        if record is None:
            return execute(call, *args, **kwargs)
        record["operation"] = call.operation
        record["pre_runtime_ns"] = time.perf_counter_ns() - record["asgi_started"]
        profiler = cProfile.Profile() if profile else None
        run = measured("runtime", execute)
        try:
            return profiler.runcall(run, call, *args, **kwargs) if profiler else run(
                call, *args, **kwargs
            )
        finally:
            if profiler:
                profiler.dump_stats(str(output / (record["sample_id"] + ".pstats")))

    runtime.execute = observed


class ObservedASGI:
    def __init__(self, app):
        self.app, self.records, self.dropped = app, [], 0

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        record = {
            "sample_id": uuid4().hex,
            "asgi_started": time.perf_counter_ns(),
            "operation": None,
            "phases": {},
            "sql_count": 0,
            "sql_wall_ns": 0,
            "sql_errors": 0,
            "status": None,
            "response_bytes": 0,
        }
        token = _RECORD.set(record)

        async def observed_send(message):
            if message["type"] == "http.response.start":
                record["status"] = message["status"]
                headers = dict(message.get("headers", []))
                record["request_id"] = headers.get(b"x-request-id", b"").decode("ascii")
                record["server_timing"] = headers.get(b"server-timing", b"").decode("ascii")
            elif message["type"] == "http.response.body":
                record["response_bytes"] += len(message.get("body", b""))
            await send(message)

        try:
            await self.app(scope, receive, observed_send)
        finally:
            record["asgi_wall_ns"] = time.perf_counter_ns() - record.pop("asgi_started")
            _RECORD.reset(token)
            if len(self.records) < 50000:
                self.records.append(record)
            else:
                self.dropped += 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute-stage-b", action="store_true")
    parser.add_argument("--mode", choices=("baseline", "timings", "profile"), required=True)
    parser.add_argument("--seconds", type=int, default=30)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not args.execute_stage_b or not 1 <= args.seconds <= 120:
        parser.error("Requires explicit stage-B execution and a 1..120 second diagnostic window")

    import uvicorn
    from t44.api import create_app
    from t44.persistence import SqlAlchemyUnitOfWorkFactory, create_mysql_engine
    from t44.settings import Settings

    settings = Settings.from_env()
    db = settings.mysql_settings()
    if os.environ.get("T44_DATABASE") != "t44_profile" or db.database != "t44_profile":
        raise ValueError("Only explicitly selected t44_profile is allowed")
    args.output.mkdir(mode=0o700, parents=False, exist_ok=False)
    engine = create_mysql_engine(db)
    app = create_app(factory=SqlAlchemyUnitOfWorkFactory(engine), settings=settings)
    effective = {}

    async def observe_configuration():
        from anyio.to_thread import current_default_thread_limiter

        effective["thread_tokens"] = current_default_thread_limiter().total_tokens

    app.add_event_handler("startup", observe_configuration)
    observer = None
    if args.mode != "baseline":
        instrument(app, engine, args.output, args.mode == "profile")
        observer = ObservedASGI(app)
    server = uvicorn.Server(uvicorn.Config(
        observer or app, host="127.0.0.1", port=18082, workers=1, access_log=False
    ))
    timer = threading.Timer(args.seconds, lambda: setattr(server, "should_exit", True))
    started, cpu = time.perf_counter_ns(), time.process_time_ns()
    timer.start()
    try:
        server.run()
    finally:
        timer.cancel()
        engine.dispose()
        metadata = {
            "mode": args.mode,
            "source_sha": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
            "python": platform.python_version(),
            "machine": platform.machine(),
            "cpu_count": os.cpu_count(),
            "pid": os.getpid(),
            "workers": 1,
            "database": "t44_profile",
            "pool_size": db.pool_size,
            "max_overflow": db.max_overflow,
            "packages": {name: version(name) for name in ("fastapi", "starlette", "sqlalchemy", "uvicorn")},
            **effective,
            "wall_ns": time.perf_counter_ns() - started,
            "process_cpu_ns": time.process_time_ns() - cpu,
            "record_count": len(observer.records) if observer else 0,
            "dropped_records": observer.dropped if observer else 0,
            "phase_units": ["inclusive_calls", "wall_ns", "thread_cpu_ns"],
        }
        (args.output / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
        if observer:
            with (args.output / "requests.jsonl").open("x") as stream:
                for record in observer.records:
                    stream.write(json.dumps(record) + "\n")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        raise SystemExit("Diagnostic failed: " + type(exc).__name__) from None
