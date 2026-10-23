"""Stage-B-only isolated observer; no workload, connection or server starts on import."""

import argparse
import contextvars
import cProfile
import functools
import hashlib
import importlib
import json
import math
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
from dataclasses import replace
from datetime import UTC, datetime
from importlib.metadata import version
from pathlib import Path
from uuid import uuid4

_RECORD = contextvars.ContextVar("profile_record", default=None)
_URL = "http://127.0.0.1:18083/api/v1"
_POOL_CHOICES = {"A": (5, 10), "B": (15, 0)}


def pool_settings(settings, label):
    size, overflow = _POOL_CHOICES[label]
    return replace(settings, pool_size=size, max_overflow=overflow)


def profile_connections():
    from sqlalchemy import text
    from t44.persistence import create_mysql_engine
    from t44.settings import Settings

    probe = create_mysql_engine(Settings.from_env().mysql_settings())
    try:
        with probe.connect() as connection:
            return connection.execute(
                text(
                    "SELECT COUNT(*) FROM information_schema.PROCESSLIST "
                    "WHERE DB=:database AND ID<>CONNECTION_ID()"
                ),
                {"database": "t44_profile"},
            ).scalar_one()
    finally:
        probe.dispose()


def orchestrate(args, source_sha, sources):
    """Own each child lifecycle in one invocation; never depend on another tool call."""
    args.output.mkdir(mode=0o700, parents=False, exist_ok=False)
    pool_abba = args.mode == "pool-abba"
    duration_limit = 120 if pool_abba else 160
    started, deadline = time.perf_counter(), time.perf_counter() + duration_limit
    receipt = {
        "source_sha": source_sha,
        "imported_modules": sources,
        "argv": sys.argv,
        "started_at": datetime.now(UTC).isoformat(),
        "duration_limit_seconds": duration_limit,
        "pool_abba": pool_abba,
        "continuation_observation_only": args.continue_observation,
        "commands": [],
        "servers": [],
        "pool_segments": [],
    }
    command = [sys.executable, str(Path(__file__).resolve()), "--execute-stage-b"]
    fixture = (
        args.fixture
        if args.continue_observation or pool_abba
        else args.output / "bootstrap/fixture.json"
    )
    previous_alarm = None
    if pool_abba:
        if signal.getitimer(signal.ITIMER_REAL)[0]:
            raise RuntimeError("ABBA controller cannot replace an existing process deadline")
        if fixture.stat().st_mode & 0o077:
            raise ValueError("Existing profile fixture must remain private")
        receipt["fixture_sha256"] = hashlib.sha256(fixture.read_bytes()).hexdigest()

        def cleanup_deadline(_signum, _frame):
            raise TimeoutError("ABBA active window ended; reserved cleanup time begins")

        previous_alarm = signal.signal(signal.SIGALRM, cleanup_deadline)
        signal.setitimer(signal.ITIMER_REAL, duration_limit - 10)

    def client(name, *options):
        argv = [*command, *options, "--output", str(args.output / name)]
        entry = {"argv": argv, "started_at": datetime.now(UTC).isoformat()}
        receipt["commands"].append(entry)
        try:
            remaining = deadline - time.perf_counter() - (10 if pool_abba else 5)
            if remaining <= 0:
                raise TimeoutError("Controller cleanup reserve reached")
            with (args.output / f"{name}.log").open("x") as log:
                result = subprocess.run(
                    argv,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    timeout=min(45, remaining),
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
        if pool_abba and (
            data["fixture_sha256"] != receipt["fixture_sha256"] or data["source_sha"] != source_sha
        ):
            raise RuntimeError("ABBA source or private fixture changed during the comparison")
        print(f"{name}: requests={data['requests']} failures={data['failures']}", flush=True)
        return data

    try:
        modes = (
            ("A1", "B1", "B2", "A2")
            if pool_abba
            else (
                ("timings", "profile")
                if args.continue_observation
                else ("baseline", "timings", "profile")
            )
        )
        for mode in modes:
            try:
                with socket.create_connection(("127.0.0.1", 18083), timeout=0.2):
                    raise RuntimeError("Diagnostic port is already occupied")
            except ConnectionRefusedError:
                pass
            if pool_abba:
                others = profile_connections()
                receipt.setdefault("preflight", []).append(
                    {
                        "segment": mode,
                        "other_profile_connections": others,
                        "port_free": True,
                        "visibility": "current app-visible PROCESSLIST; not cross-account proof",
                    }
                )
                if others:
                    raise RuntimeError("Another profile connection is active")
            argv = [
                *command,
                "--mode",
                "timings" if pool_abba else mode,
                "--seconds",
                "30" if pool_abba else "120",
                "--output",
                str(args.output / f"server-{mode}"),
            ]
            if pool_abba:
                argv.extend(("--pool-retention", mode[0]))
            with (args.output / f"server-{mode}.log").open("x") as log:
                server = subprocess.Popen(argv, stdout=log, stderr=subprocess.STDOUT)
                entry = {
                    "argv": argv,
                    "pid": server.pid,
                    "started_at": datetime.now(UTC).isoformat(),
                }
                receipt["servers"].append(entry)
                try:
                    ready_by = min(deadline - (10 if pool_abba else 5), time.perf_counter() + 8)
                    while True:
                        if server.poll() is not None or time.perf_counter() >= ready_by:
                            raise RuntimeError("Diagnostic server did not become ready")
                        try:
                            with socket.create_connection(("127.0.0.1", 18083), timeout=0.2):
                                break
                        except ConnectionRefusedError:
                            time.sleep(0.05)
                    if pool_abba:
                        for phase, seconds in (("warmup", 1), ("steady", 4)):
                            client(
                                f"{mode}-{phase}",
                                "--mode",
                                "client",
                                "--fixture",
                                str(fixture),
                                "--concurrency",
                                "32",
                                "--seconds",
                                str(seconds),
                                "--sample-phase",
                                phase,
                            )
                    elif mode == "baseline":
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
                    for concurrency in (
                        () if pool_abba else (1,) if mode == "profile" else (1, 8, 32)
                    ):
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
                        server.wait(timeout=1 if pool_abba else 5)
                    entry.update(
                        exit_code=server.returncode, ended_at=datetime.now(UTC).isoformat()
                    )
                    if pool_abba:
                        try:
                            with socket.create_connection(("127.0.0.1", 18083), timeout=0.2):
                                entry["port_free_after"] = False
                        except ConnectionRefusedError:
                            entry["port_free_after"] = True
                if server.returncode or entry.get("forced_kill"):
                    raise RuntimeError("Diagnostic server did not stop normally")
                if pool_abba:
                    if not entry["port_free_after"]:
                        raise RuntimeError("Diagnostic port remains occupied")
                    receipt["pool_segments"].append(pool_segment_summary(args.output, mode))
    except Exception as error:
        receipt["failure"] = type(error).__name__
        raise
    finally:
        if pool_abba:
            try:
                receipt["profile_connections_after"] = profile_connections()
                if receipt["profile_connections_after"]:
                    receipt["postcheck_error"] = "VisibleProfileConnectionsRemain"
            except Exception as error:
                receipt["postcheck_error"] = type(error).__name__
            signal.setitimer(signal.ITIMER_REAL, 0)
            signal.signal(signal.SIGALRM, previous_alarm)
        receipt.update(
            ended_at=datetime.now(UTC).isoformat(), wall_seconds=time.perf_counter() - started
        )
        receipt["all_own_children_exited"] = all(
            "exit_code" in server for server in receipt["servers"]
        )
        if pool_abba and receipt["wall_seconds"] > duration_limit:
            receipt["duration_budget_exceeded"] = True
        (args.output / "orchestrator-metadata.json").write_text(
            json.dumps(receipt, indent=2) + "\n"
        )
    if receipt.get("duration_budget_exceeded"):
        raise TimeoutError("ABBA controller exceeded its bounded window")
    if receipt.get("postcheck_error"):
        raise RuntimeError("Final profile connection check was not clean")
    return 0


def distribution_ns(values):
    ordered = sorted(values)
    return {
        "count": len(ordered),
        "mean_ms": sum(ordered) / len(ordered) / 1e6 if ordered else None,
        "p95_ms": ordered[math.ceil(0.95 * len(ordered)) - 1] / 1e6 if ordered else None,
    }


def pool_segment_summary(output, name):
    server = output / f"server-{name}"
    metadata = json.loads((server / "metadata.json").read_text())
    observed = [json.loads(line) for line in (server / "requests.jsonl").read_text().splitlines()]
    lifecycle = json.loads((server / "pool-lifecycle.json").read_text())
    result = {
        "segment": name,
        "pool_size": metadata["pool_size"],
        "max_overflow": metadata["max_overflow"],
        "phases": {},
        "lifecycle": lifecycle["summary"],
        "server_metadata": metadata,
    }
    for phase in ("warmup", "steady"):
        client = output / f"{name}-{phase}"
        info = json.loads((client / "client-metadata.json").read_text())
        rows = [json.loads(line) for line in (client / "client.jsonl").read_text().splitlines()]
        ids = [row.get("request_id") for row in rows]
        records = [row for row in observed if row["sample_phase"] == phase]
        matched = (
            None not in ids
            and len(ids) == len(set(ids))
            and Counter(ids) == Counter(row.get("request_id") for row in records)
        )
        if (
            not matched
            or metadata["dropped_records"]
            or any(
                row["endpoint_dispatch_count"] != 1 or "runtime" not in row["phases"]
                for row in records
            )
        ):
            raise RuntimeError("Pool diagnostic request observations are incomplete")
        acquire = [row["phases"].get("db_acquire_and_pre_ping", [0, 0, 0]) for row in records]
        if any(value[0] != 1 for value in acquire):
            raise RuntimeError("Pool diagnostic acquire count is not exactly one per request")
        result["phases"][phase] = {
            **info,
            "e2e": distribution_ns(row["e2e_ns"] for row in rows),
            "success_throughput_per_second": sum(row["valid"] for row in rows)
            / (info["sample_active_wall_ns"] / 1e9),
            "error_codes": dict(
                Counter(str(row.get("error_code")) for row in rows if not row["valid"])
            ),
            "exceptions": dict(Counter(row["exception"] for row in rows if "exception" in row)),
            "request_id_matches_exact": matched,
            "acquire_inclusive_wall": distribution_ns(value[1] for value in acquire),
            "acquire_thread_cpu": distribution_ns(value[2] for value in acquire),
        }
    if lifecycle["summary"]["open_after_dispose"] or lifecycle["summary"]["peak_open"] > 15:
        raise RuntimeError("Pool physical connection budget or cleanup violated")
    if lifecycle["summary"]["phase_counts"]["unclassified"]:
        raise RuntimeError("Pool events have no reliable warmup/steady attribution")
    if lifecycle["summary"]["failed_calls"] or lifecycle["summary"]["ping_returned_false"]:
        raise RuntimeError("Pool diagnostic observed a failed DBAPI lifecycle call")
    return result


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
        fixture_bytes = args.fixture.read_bytes()
        fixture = json.loads(fixture_bytes)
        clock = {"deadline": time.perf_counter() + args.seconds}

        def release_workers():
            clock["active_started_ns"] = time.perf_counter_ns()
            clock["deadline"] = time.perf_counter() + args.seconds

        gate = (
            threading.Barrier(args.concurrency, action=release_workers)
            if args.sample_phase
            else None
        )

        def worker(index):
            rows, count = [], 0
            with httpx.Client(base_url=_URL, timeout=30, trust_env=False) as client:
                if gate:
                    gate.wait(timeout=5)
                while time.perf_counter() < clock["deadline"] and (
                    not args.max_requests or count < args.max_requests
                ):
                    candidate = fixture["candidates"][(index + count) % 3]
                    before = time.perf_counter_ns()
                    row = {"worker": index, "ordinal": count, "category": candidate["category"]}
                    try:
                        result = client.post(
                            _URL + f"/projects/{fixture['project_id']}/contract-validations",
                            json=candidate,
                            headers={
                                "Authorization": "Bearer " + fixture["token"],
                                **(
                                    {"X-T44-Pool-Phase": args.sample_phase}
                                    if args.sample_phase
                                    else {}
                                ),
                            },
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
        clock["active_ended_ns"] = time.perf_counter_ns()
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
        "sample_phase": args.sample_phase,
        "fixture_sha256": hashlib.sha256(fixture_bytes).hexdigest()
        if args.mode == "client"
        else None,
        "actual_wall_ns": time.perf_counter_ns() - started,
        "sample_active_wall_ns": clock["active_ended_ns"] - clock.get("active_started_ns", started)
        if args.mode == "client"
        else None,
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


class PoolLifecycle:
    """Only the diagnostic engine's actual DBAPI calls, including final disposal."""

    def __init__(self, engine):
        self.phase, self.events, self.open, self.peak = "startup", [], set(), 0
        self.lock = threading.Lock()
        for method, kind in (("connect", "connect"), ("do_ping", "ping"), ("do_close", "close")):
            setattr(engine.dialect, method, self.wrap(kind, getattr(engine.dialect, method)))

    def wrap(self, kind, function):
        @functools.wraps(function)
        def call(*args, **kwargs):
            record = _RECORD.get()
            phase = record["sample_phase"] if record is not None else self.phase
            before, cpu, success, value = time.perf_counter_ns(), time.thread_time_ns(), False, None
            error_name = None
            try:
                value = function(*args, **kwargs)
                success = True
                return value
            except BaseException as error:
                error_name = type(error).__name__
                raise
            finally:
                wall, thread_cpu = time.perf_counter_ns() - before, time.thread_time_ns() - cpu
                with self.lock:
                    if success and kind == "connect":
                        self.open.add(id(value))
                        self.peak = max(self.peak, len(self.open))
                    elif success and kind == "close":
                        self.open.discard(id(args[0]))
                    self.events.append(
                        {
                            "kind": kind,
                            "phase": phase,
                            "success": success,
                            "ping_returned_false": kind == "ping" and value is False,
                            "error_class": error_name,
                            "wall_ns": wall,
                            "thread_cpu_ns": thread_cpu,
                            "at_monotonic_ns": before,
                        }
                    )

        return call

    def save(self, output, before_dispose):
        summary = {
            "phase_counts": {
                phase: dict(
                    Counter(event["kind"] for event in self.events if event["phase"] == phase)
                )
                for phase in ("startup", "warmup", "steady", "cleanup", "unclassified")
            },
            "failed_calls": sum(not event["success"] for event in self.events),
            "ping_returned_false": sum(event["ping_returned_false"] for event in self.events),
            "peak_open": self.peak,
            "open_after_dispose": len(self.open),
            "before_dispose": before_dispose,
        }
        (output / "pool-lifecycle.json").write_text(
            json.dumps(
                {
                    "summary": summary,
                    "events": self.events,
                    "units": "actual dialect DBAPI call attempts; failures and cleanup separate",
                },
                indent=2,
            )
            + "\n"
        )
        return summary


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
        phase = dict(scope.get("headers", [])).get(b"x-t44-pool-phase", b"")
        record = {
            "sample_id": uuid4().hex,
            "sample_phase": {b"warmup": "warmup", b"steady": "steady"}.get(phase, "unclassified"),
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
        choices=(
            "baseline",
            "timings",
            "profile",
            "bootstrap",
            "client",
            "orchestrate",
            "pool-abba",
        ),
        required=True,
    )
    parser.add_argument("--seconds", type=int, default=30)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--credentials", type=Path)
    parser.add_argument("--fixture", type=Path)
    parser.add_argument("--continue-observation", action="store_true")
    parser.add_argument("--pool-retention", choices=tuple(_POOL_CHOICES))
    parser.add_argument("--sample-phase", choices=("warmup", "steady"))
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
    if args.pool_retention and args.mode != "timings":
        parser.error("A/B settings are restricted to a diagnostic timings server")
    if args.sample_phase and args.mode != "client":
        parser.error("Warmup/steady tags are restricted to a diagnostic client")
    if args.mode == "pool-abba" and (
        args.fixture is None
        or any(
            argument.split("=", 1)[0]
            in (
                "--seconds",
                "--concurrency",
                "--max-requests",
                "--credentials",
                "--pool-retention",
                "--sample-phase",
                "--continue-observation",
            )
            for argument in sys.argv[1:]
        )
    ):
        parser.error("ABBA requires an existing fixture and fixed32/1s+4s/A-B-B-A settings")
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
        "t44.persistence.engine",
        "t44.persistence.uow",
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
    for resource in (
        "resources/review-template.json",
        "resources/escalation-rules.json",
        "persistence/schema_v1.sql",
    ):
        path = source_root / "backend/t44" / resource
        sources[resource] = {
            "file": str(path),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
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
    if args.mode == "pool-abba" or args.pool_retention:
        subprocess.run(
            [
                "git",
                "-C",
                str(source_root),
                "diff",
                "--exit-code",
                "bc5aef9c62393134582affb7a690acb33ac2b833",
                "--",
                "backend/t44",
            ],
            check=True,
            stdout=subprocess.DEVNULL,
        )
        if version("sqlalchemy") != "2.1.6":
            raise ValueError("Pool diagnosis requires the verified SQLAlchemy2.1.6 runtime")
        verified = json.loads(
            (source_root / "agents/database/pool-retention/source-verification.json").read_text()
        )
        for filename in ("impl.py", "base.py"):
            name = "sqlalchemy.pool." + filename.removesuffix(".py")
            path = Path(importlib.import_module(name).__file__).resolve()
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            if digest != verified["sources"][filename]["official_sha256"]:
                raise ValueError("Actual pool source differs from verified official2.1.6 bytes")
            sources[name] = {"file": str(path), "sha256": digest}
    source_sha = subprocess.check_output(
        ["git", "-C", str(source_root), "rev-parse", "HEAD"], text=True
    ).strip()
    if args.mode in ("bootstrap", "client"):
        return client_run(args, source_sha)
    if args.mode in ("orchestrate", "pool-abba"):
        return orchestrate(args, source_sha, sources)
    args.output.mkdir(mode=0o700, parents=False, exist_ok=False)
    if args.pool_retention:
        db = pool_settings(db, args.pool_retention)
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
    if args.pool_retention and (engine.pool.checkedin() or engine.pool.checkedout()):
        raise RuntimeError("Diagnostic lifecycle observer must precede any connection")
    lifecycle = PoolLifecycle(engine) if args.pool_retention else None
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
        before_dispose = {
            "checked_out": engine.pool.checkedout(),
            "checked_in": engine.pool.checkedin(),
            "overflow": engine.pool.overflow(),
            "retained_capacity": engine.pool.size(),
            "overflow_capacity": engine.pool._max_overflow,
        }
        if lifecycle:
            lifecycle.phase = "cleanup"
        cleanup_error = None
        try:
            engine.dispose()
        except Exception as error:
            cleanup_error = type(error).__name__
        pool_summary = lifecycle.save(args.output, before_dispose) if lifecycle else None
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
            "pool_retention_label": args.pool_retention,
            "pool_pre_ping": engine.pool._pre_ping,
            "pool_use_lifo": engine.pool._pool.use_lifo,
            "pool_reset_on_return": str(engine.pool._reset_on_return),
            "pool_lifecycle": pool_summary,
            "cleanup_error_class": cleanup_error,
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
        if cleanup_error or (
            lifecycle
            and (
                before_dispose["checked_out"]
                or pool_summary["open_after_dispose"]
                or pool_summary["peak_open"] > 15
            )
        ):
            raise RuntimeError("Diagnostic engine cleanup or connection budget failed")


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        raise SystemExit("Diagnostic failed: " + type(exc).__name__) from None
