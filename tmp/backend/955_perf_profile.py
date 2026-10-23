"""Stage-B-only isolated observer; no workload, connection or server starts on import."""

import argparse
import contextvars
import cProfile
import functools
import hashlib
import importlib
import json
import os
import platform
import signal
import socket
import subprocess
import sys
import threading
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from importlib.metadata import version
from pathlib import Path
from uuid import uuid4

_RECORD = contextvars.ContextVar("profile_record", default=None)
_URL = "http://127.0.0.1:18083/api/v1"


def orchestrate(args, source_sha, sources):
    """Own each child lifecycle in one invocation; never depend on another tool call."""
    args.output.mkdir(mode=0o700, parents=False, exist_ok=False)
    started, deadline = time.perf_counter(), time.perf_counter() + 160
    receipt = {
        "source_sha": source_sha,
        "imported_modules": sources,
        "argv": sys.argv,
        "started_at": datetime.now(UTC).isoformat(),
        "duration_limit_seconds": 160,
        "continuation_observation_only": args.continue_observation,
        "commands": [],
        "servers": [],
    }
    command = [sys.executable, str(Path(__file__).resolve()), "--execute-stage-b"]
    fixture = args.fixture if args.continue_observation else args.output / "bootstrap/fixture.json"

    def client(name, *options):
        argv = [*command, *options, "--output", str(args.output / name)]
        entry = {"argv": argv, "started_at": datetime.now(UTC).isoformat()}
        receipt["commands"].append(entry)
        try:
            with (args.output / f"{name}.log").open("x") as log:
                result = subprocess.run(
                    argv,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    timeout=max(0.1, min(45, deadline - time.perf_counter() - 5)),
                )
            entry["exit_code"] = result.returncode
        except subprocess.TimeoutExpired:
            entry["exit_code"] = "timeout"
            raise
        finally:
            entry["ended_at"] = datetime.now(UTC).isoformat()
        if result.returncode:
            raise RuntimeError("Diagnostic child failed; preserve output and stop")
        data = json.loads((args.output / name / "client-metadata.json").read_text())
        print(f"{name}: requests={data['requests']} failures={data['failures']}", flush=True)
        return data

    try:
        modes = (
            ("timings", "profile")
            if args.continue_observation
            else ("baseline", "timings", "profile")
        )
        for mode in modes:
            try:
                with socket.create_connection(("127.0.0.1", 18083), timeout=0.2):
                    raise RuntimeError("Diagnostic port is already occupied")
            except ConnectionRefusedError:
                pass
            argv = [
                *command,
                "--mode",
                mode,
                "--seconds",
                "120",
                "--output",
                str(args.output / f"server-{mode}"),
            ]
            with (args.output / f"server-{mode}.log").open("x") as log:
                server = subprocess.Popen(argv, stdout=log, stderr=subprocess.STDOUT)
                entry = {
                    "argv": argv,
                    "pid": server.pid,
                    "started_at": datetime.now(UTC).isoformat(),
                }
                receipt["servers"].append(entry)
                try:
                    ready_by = min(deadline - 5, time.perf_counter() + 8)
                    while True:
                        if server.poll() is not None or time.perf_counter() >= ready_by:
                            raise RuntimeError("Diagnostic server did not become ready")
                        try:
                            with socket.create_connection(("127.0.0.1", 18083), timeout=0.2):
                                break
                        except ConnectionRefusedError:
                            time.sleep(0.05)
                    if mode == "baseline":
                        client(
                            "bootstrap",
                            "--mode",
                            "bootstrap",
                            "--credentials",
                            str(args.credentials),
                        )
                        sanity = client(
                            "sanity",
                            "--mode",
                            "client",
                            "--fixture",
                            str(fixture),
                            "--seconds",
                            "5",
                            "--max-requests",
                            "3",
                        )
                        if sanity["category_counts"] != {"1": 1, "2": 1, "3": 1}:
                            raise RuntimeError(
                                "Sanity must validate all three candidate categories"
                            )
                    for concurrency in (1,) if mode == "profile" else (1, 8, 32):
                        sample = client(
                            f"{mode}-{concurrency}",
                            "--mode",
                            "client",
                            "--fixture",
                            str(fixture),
                            "--concurrency",
                            str(concurrency),
                            "--seconds",
                            str(args.seconds),
                            "--max-requests",
                            "3" if mode == "profile" else "0",
                        )
                        if mode == "profile" and sample["category_counts"] != {
                            "1": 1,
                            "2": 1,
                            "3": 1,
                        }:
                            raise RuntimeError(
                                "Profile must contain three valid candidate categories"
                            )
                finally:
                    if server.poll() is None:
                        server.send_signal(signal.SIGTERM)
                    try:
                        server.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        entry["forced_kill"] = True
                        server.kill()
                        server.wait(timeout=5)
                    entry.update(
                        exit_code=server.returncode, ended_at=datetime.now(UTC).isoformat()
                    )
                if server.returncode or entry.get("forced_kill"):
                    raise RuntimeError("Diagnostic server did not stop normally")
    except Exception as error:
        receipt["failure"] = type(error).__name__
        raise
    finally:
        receipt.update(
            ended_at=datetime.now(UTC).isoformat(), wall_seconds=time.perf_counter() - started
        )
        (args.output / "orchestrator-metadata.json").write_text(
            json.dumps(receipt, indent=2) + "\n"
        )
    return 0


def client_run(args, source_sha):
    import httpx

    args.output.mkdir(mode=0o700, parents=False, exist_ok=False)
    started_at = datetime.now(UTC).isoformat()
    started, cpu = time.perf_counter_ns(), time.process_time_ns()
    if args.mode == "bootstrap":
        accounts = json.loads(args.credentials.read_text())["accounts"]
        if json.loads(args.credentials.read_text())["database"] != "t44_profile":
            raise ValueError("Neutral credentials must belong to profile")
        with httpx.Client(base_url=_URL, timeout=30, trust_env=False) as client:
            response = client.post(
                _URL + "/auth/login",
                json={key: accounts["manager"][key] for key in ("username", "password")},
            )
            response.raise_for_status()
            token = response.json()["data"]["access_token"]
            headers = {"Authorization": "Bearer " + token}

            def create(path, payload):
                result = client.post(
                    _URL + path,
                    json=payload,
                    headers={
                        **headers,
                        "Idempotency-Key": uuid4().hex,
                    },
                )
                result.raise_for_status()
                return result.json()["data"]

            pid = create("/projects", {"name": "Synthetic isolated profile " + uuid4().hex[:8]})[
                "id"
            ]
            create(
                f"/projects/{pid}/members",
                {
                    "username": accounts["developer"]["username"],
                    "roles": [2],
                    "reason": "Profile fixture",
                },
            )
            evidence = [
                {"kind": 2, "locator": "synthetic/profile", "description": "Diagnostic fixture"}
            ]
            plan = {
                "planned_start": "2026-10-23T00:00:00Z",
                "planned_end": "2026-10-25T00:00:00Z",
                "buffer_hours": 1,
                "delay_contingency": "Synthetic diagnostic plan",
            }
            iteration = create(
                f"/projects/{pid}/iterations",
                {
                    **plan,
                    "name": "Profile",
                    "capacity": [
                        {"user_id": accounts["developer"]["user_id"], "available_hours": 40}
                    ],
                },
            )
            registration = {
                "title": "Synthetic profile task",
                "owner_id": accounts["developer"]["user_id"],
                "iteration_id": iteration["id"],
                "plan": {**plan, "estimated_hours": 8},
                "dependency_task_ids": [],
            }
            task = create(f"/projects/{pid}/tasks", registration)["task"]
            assessment = {
                "expected_version": task["version"],
                "risks": [
                    {
                        "perspective": p,
                        "severity": 1,
                        "risk": "Synthetic risk",
                        "mitigation": "Synthetic mitigation",
                        "evidence": evidence,
                    }
                    for p in (1, 2, 3, 4)
                ],
                "rollback_plan": {
                    "target_version": "synthetic-v0",
                    "trigger": "Synthetic trigger",
                    "steps": ["Synthetic restore"],
                    "impact": "Synthetic impact",
                    "verification": "Synthetic check",
                    "responsible_user_id": accounts["manager"]["user_id"],
                    "evidence": evidence,
                },
            }
            fixture = {
                "token": token,
                "project_id": pid,
                "task_id": task["id"],
                "candidates": [
                    {"category": 1, "payload": registration},
                    {
                        "category": 2,
                        "task_id": task["id"],
                        "payload": {"expected_version": task["version"], "action": 1},
                    },
                    {"category": 3, "task_id": task["id"], "payload": assessment},
                ],
            }
            target = args.output / "fixture.json"
            target.write_text(json.dumps(fixture))
            target.chmod(0o600)
            records = []
    else:
        fixture = json.loads(args.fixture.read_text())
        deadline = time.perf_counter() + args.seconds

        def worker(index):
            rows, count = [], 0
            with httpx.Client(base_url=_URL, timeout=30, trust_env=False) as client:
                while time.perf_counter() < deadline and (
                    not args.max_requests or count < args.max_requests
                ):
                    candidate = fixture["candidates"][(index + count) % 3]
                    before = time.perf_counter_ns()
                    row = {"worker": index, "ordinal": count, "category": candidate["category"]}
                    try:
                        result = client.post(
                            _URL + f"/projects/{fixture['project_id']}/contract-validations",
                            json=candidate,
                            headers={"Authorization": "Bearer " + fixture["token"]},
                        )
                        row.update(
                            status=result.status_code,
                            request_id=result.headers.get("x-request-id"),
                            server_timing=result.headers.get("server-timing"),
                        )
                        payload = result.json()
                        row.update(
                            error_code=payload.get("code") if result.status_code >= 400 else None,
                            valid=result.status_code == 200
                            and payload.get("data", {}).get("valid") is True
                            and payload["data"].get("business_guards_executed") is False
                            and payload["data"].get("category") == candidate["category"]
                            and payload["data"].get("validated_operation_id")
                            == {1: "createTask", 2: "transitionTask", 3: "createReleaseAssessment"}[
                                candidate["category"]
                            ]
                            and not payload.get("violations")
                            and not payload["data"].get("violations"),
                        )
                    except Exception as error:
                        row.update(valid=False, exception=type(error).__name__)
                    row["e2e_ns"] = time.perf_counter_ns() - before
                    rows.append(row)
                    count += 1
            return rows

        with ThreadPoolExecutor(max_workers=args.concurrency) as executor:
            records = [
                row for batch in executor.map(worker, range(args.concurrency)) for row in batch
            ]
        with (args.output / "client.jsonl").open("x") as stream:
            for row in records:
                stream.write(json.dumps(row) + "\n")
    metadata = {
        "started_at": started_at,
        "ended_at": datetime.now(UTC).isoformat(),
        "source_sha": source_sha,
        "mode": args.mode,
        "concurrency": args.concurrency,
        "requested_seconds": args.seconds,
        "actual_wall_ns": time.perf_counter_ns() - started,
        "process_cpu_ns": time.process_time_ns() - cpu,
        "requests": len(records),
        "failures": sum(not row["valid"] for row in records),
        "pid": os.getpid(),
        "category_counts": dict(Counter(row["category"] for row in records)),
        "url": _URL,
        "client_trust_env": False,
        "scope": "short developer diagnostic,not formal400VU/600seconds",
    }
    metadata["missing_workers"] = (
        sorted(set(range(args.concurrency)) - {row["worker"] for row in records})
        if args.mode == "client"
        else []
    )
    (args.output / "client-metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    return int(bool(metadata["failures"] or metadata["missing_workers"]))


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
    import fastapi.routing
    from sqlalchemy import event
    from t44 import api, contracts
    from t44.services import runtime as runtime_module

    runtime = app.state.runtime
    runtime_module.authenticate = measured("authenticate", runtime_module.authenticate)
    contracts.validator = measured("schema_construct", contracts.validator)
    dispatch = fastapi.routing.run_in_threadpool

    async def observed_dispatch(func, /, *args, **kwargs):
        record = _RECORD.get()
        submitted = time.perf_counter_ns()

        @functools.wraps(func)
        def entered(*inner_args, **inner_kwargs):
            if record is not None:
                record["endpoint_dispatch_count"] += 1
                record["endpoint_dispatch_wait_ns"] += time.perf_counter_ns() - submitted
            return func(*inner_args, **inner_kwargs)

        return await dispatch(entered, *args, **kwargs)

    fastapi.routing.run_in_threadpool = observed_dispatch
    for name in ("authorize", "claim", "locked_scope", "complete", "rejection", "audit"):
        setattr(runtime, name, measured(name, getattr(runtime, name)))
    for name in ("dispatch", "validate_data"):
        setattr(runtime.business, name, measured(name, getattr(runtime.business, name)))
    for name in ("validate_request", "violations", "wire"):
        setattr(api, name, measured("http_" + name, getattr(api, name)))
    engine.connect = measured("db_acquire_and_pre_ping", engine.connect)
    for method, phase in (
        ("connect", "dbapi_new_connection"),
        ("do_ping", "dbapi_pre_ping"),
        ("do_commit", "dbapi_commit"),
        ("do_rollback", "dbapi_rollback"),
    ):
        setattr(engine.dialect, method, measured(phase, getattr(engine.dialect, method)))

    @event.listens_for(engine, "checkout")
    def checkout(_connection, _record, _proxy):
        record = _RECORD.get()
        if record is not None:
            record["pool_checkouts"] += 1

    @event.listens_for(engine, "before_cursor_execute")
    def before(_conn, _cursor, _statement, _parameters, context, _many):
        context._t44_profile_started = time.perf_counter_ns()
        context._t44_profile_cpu = time.thread_time_ns()
        context._t44_profile_kind = _statement.lstrip().split(None, 1)[0].upper()

    def sql_finished(context, failed=False):
        record = _RECORD.get()
        started = getattr(context, "_t44_profile_started", None)
        if record is not None and started is not None:
            record["sql_count"] += 1
            record["sql_wall_ns"] += time.perf_counter_ns() - started
            record["sql_thread_cpu_ns"] += time.thread_time_ns() - context._t44_profile_cpu
            record["sql_errors"] += int(failed)
            kind = context._t44_profile_kind
            record["sql_kinds"][kind] = record["sql_kinds"].get(kind, 0) + 1

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
            return (
                profiler.runcall(run, call, *args, **kwargs)
                if profiler
                else run(call, *args, **kwargs)
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
            "sql_thread_cpu_ns": 0,
            "sql_kinds": {},
            "sql_errors": 0,
            "pool_checkouts": 0,
            "endpoint_dispatch_count": 0,
            "endpoint_dispatch_wait_ns": 0,
            "receive_wait_ns": 0,
            "status": None,
            "response_bytes": 0,
        }
        token = _RECORD.set(record)

        async def observed_receive():
            before = time.perf_counter_ns()
            try:
                return await receive()
            finally:
                record["receive_wait_ns"] += time.perf_counter_ns() - before

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
            await self.app(scope, observed_receive, observed_send)
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
    parser.add_argument(
        "--mode",
        choices=("baseline", "timings", "profile", "bootstrap", "client", "orchestrate"),
        required=True,
    )
    parser.add_argument("--seconds", type=int, default=30)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--credentials", type=Path)
    parser.add_argument("--fixture", type=Path)
    parser.add_argument("--continue-observation", action="store_true")
    parser.add_argument("--concurrency", type=int, choices=(1, 8, 32), default=1)
    parser.add_argument("--max-requests", type=int, default=0)
    args = parser.parse_args()
    if not args.execute_stage_b or not 1 <= args.seconds <= 120 or args.max_requests < 0:
        parser.error("Requires explicit stage-B execution and a 1..120 second diagnostic window")
    if args.mode == "orchestrate" and args.seconds > 10:
        parser.error("Orchestrated diagnostic samples must be 1..10 seconds")
    if args.continue_observation and (args.mode != "orchestrate" or args.fixture is None):
        parser.error(
            "Observation continuation requires orchestrate and an existing private fixture"
        )
    if (
        args.mode in ("bootstrap", "orchestrate")
        and not args.continue_observation
        and args.credentials is None
    ) or (args.mode == "client" and args.fixture is None):
        parser.error("Bootstrap requires credentials; client requires a private fixture")

    import uvicorn
    from t44.api import create_app
    from t44.persistence import SqlAlchemyUnitOfWorkFactory, create_mysql_engine
    from t44.settings import Settings

    settings = Settings.from_env()
    db = settings.mysql_settings()
    if os.environ.get("T44_DATABASE") != "t44_profile" or db.database != "t44_profile":
        raise ValueError("Only explicitly selected t44_profile is allowed")
    source_root = Path(__file__).resolve().parents[2]
    sources = {}
    for name in (
        "t44",
        "t44.api",
        "t44.contracts",
        "t44.services.application",
        "t44.services.common",
        "t44.services.runtime",
        "t44.services.tasks",
        "t44.services.projects",
        "t44.services.reviews",
        "t44.services.workflow",
        "t44.persistence.rows",
    ):
        path = Path(importlib.import_module(name).__file__).resolve()
        if not path.is_relative_to(source_root / "backend/t44"):
            raise ValueError("Imported module differs from the selected diagnostic source tree")
        sources[name] = {"file": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
    contract = Path(sources["t44.contracts"]["file"]).with_name("openapi.json")
    sources["openapi.json"] = {
        "file": str(contract),
        "sha256": hashlib.sha256(contract.read_bytes()).hexdigest(),
    }
    dirty = subprocess.check_output(
        [
            "git",
            "-C",
            str(source_root),
            "status",
            "--porcelain",
            "--",
            "backend/t44",
            "tmp/backend/955_perf_profile.py",
        ],
        text=True,
    )
    if dirty:
        raise ValueError("Diagnostic source must be committed before stage B")
    source_sha = subprocess.check_output(
        ["git", "-C", str(source_root), "rev-parse", "HEAD"], text=True
    ).strip()
    if args.mode in ("bootstrap", "client"):
        return client_run(args, source_sha)
    if args.mode == "orchestrate":
        return orchestrate(args, source_sha, sources)
    args.output.mkdir(mode=0o700, parents=False, exist_ok=False)
    engine = create_mysql_engine(db)
    app = create_app(factory=SqlAlchemyUnitOfWorkFactory(engine), settings=settings)
    effective = {}

    async def observe_configuration():
        from anyio.to_thread import current_default_thread_limiter

        effective["thread_tokens"] = current_default_thread_limiter().total_tokens

    app.router.add_event_handler("startup", observe_configuration)
    observer = None
    if args.mode != "baseline":
        instrument(app, engine, args.output, args.mode == "profile")
        observer = ObservedASGI(app)
    server = uvicorn.Server(
        uvicorn.Config(observer or app, host="127.0.0.1", port=18083, workers=1, access_log=False)
    )
    timer = threading.Timer(args.seconds, lambda: setattr(server, "should_exit", True))
    started_at = datetime.now(UTC).isoformat()
    started, cpu = time.perf_counter_ns(), time.process_time_ns()
    # Uvicorn re-raises SIGTERM after graceful shutdown; let this tool write its metadata.
    previous_term = signal.signal(signal.SIGTERM, lambda *_: setattr(server, "should_exit", True))
    timer.start()
    try:
        server.run()
    finally:
        signal.signal(signal.SIGTERM, previous_term)
        timer.cancel()
        engine.dispose()
        metadata = {
            "started_at": started_at,
            "ended_at": datetime.now(UTC).isoformat(),
            "mode": args.mode,
            "source_sha": source_sha,
            "imported_modules": sources,
            "python": platform.python_version(),
            "machine": platform.machine(),
            "cpu_count": os.cpu_count(),
            "pid": os.getpid(),
            "workers": 1,
            "port": 18083,
            "database": "t44_profile",
            "pool_size": db.pool_size,
            "max_overflow": db.max_overflow,
            "packages": {
                name: version(name) for name in ("fastapi", "starlette", "sqlalchemy", "uvicorn")
            },
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
        raise SystemExit(main())
    except Exception as exc:
        raise SystemExit("Diagnostic failed: " + type(exc).__name__) from None
