"""Opt-in sequential real HTTP diagnostic; import does not connect or execute."""

import argparse
import contextlib
import contextvars
import cProfile
import functools
import hashlib
import importlib.util
import json
import os
import platform
import pstats
import signal
import subprocess
import time
from datetime import UTC, datetime
from importlib.metadata import version
from pathlib import Path
from uuid import uuid4

SOURCE_FILES = (
    "backend/t44/api.py",
    "backend/t44/contracts/__init__.py",
    "backend/t44/contracts/openapi.json",
    "backend/t44/services/application.py",
    "backend/t44/services/runtime.py",
    "backend/t44/services/common.py",
    "backend/t44/services/workflow.py",
    "backend/t44/persistence/engine.py",
    "backend/t44/persistence/rows.py",
    "backend/t44/persistence/uow.py",
)
PLAN = {
    "planned_start": "2030-01-01T00:00:00Z",
    "planned_end": "2030-01-03T00:00:00Z",
    "estimated_hours": 8,
    "buffer_hours": 1,
    "delay_contingency": "Synthetic sequential CPU diagnostic",
}
EVIDENCE = [{"kind": 2, "locator": "synthetic/cpu-profile", "description": "Diagnostic"}]


def utc():
    return datetime.now(UTC).isoformat()


def safe_file(filename, root):
    if filename.startswith("<") or filename == "~":
        return filename
    path = Path(filename)
    if path.is_relative_to(root):
        return str(path.relative_to(root))
    if "site-packages/" in filename:
        return "site-packages/" + filename.split("site-packages/", 1)[1]
    return "external/" + path.name


class Stages:
    def __init__(self, root, observer=None):
        self.root, self.observer = root, observer
        self.active = contextvars.ContextVar("request_profile", default=None)
        self.mode, self.rows, self.restores = "warmup", [], []

    @contextlib.contextmanager
    def span(self, label):
        current = self.active.get()
        if current is None:
            yield
            return
        spans, stack = current["spans"], current["stack"]
        index = len(spans)
        parent = stack[-1] if stack else None
        row = {"id": index, "stage": label, "parent_id": parent}
        spans.append(row)
        stack.append(index)
        wall, cpu = time.perf_counter_ns(), time.thread_time_ns()
        try:
            yield
        finally:
            row.update(
                wall_ns=time.perf_counter_ns() - wall, thread_cpu_ns=time.thread_time_ns() - cpu
            )
            stack.pop()
            children = [s for s in spans if s["parent_id"] == index]
            row["exclusive_wall_ns"] = row["wall_ns"] - sum(s["wall_ns"] for s in children)
            row["exclusive_thread_cpu_ns"] = row["thread_cpu_ns"] - sum(
                s["thread_cpu_ns"] for s in children
            )

    def wrap(self, owner, name, label):
        original = getattr(owner, name)

        @functools.wraps(original)
        def timed(*args, **kwargs):
            with self.span(label):
                return original(*args, **kwargs)

        setattr(owner, name, timed)
        self.restores.append((owner, name, original))

    def install(self, app):
        from fastapi.routing import APIRoute
        from t44 import api, contracts
        from t44.services import application, runtime

        for owner, name, label in (
            (api, "validate_request", "request_validation"),
            (api, "violations", "api_schema_validation"),
            (api, "wire", "api_wire"),
            (contracts, "validator", "validator_construction"),
            (runtime.Runtime, "execute", "runtime_execute"),
            (runtime, "wire", "runtime_wire"),
            (application.Business, "dispatch", "business_dispatch"),
            (application.Business, "validate_data", "precommit_data_validation"),
            (application, "violations", "business_schema_validation"),
        ):
            self.wrap(owner, name, label)
        for route in app.routes:
            if isinstance(route, APIRoute):
                original = route.dependant.call
                route.dependant.call = self.endpoint(original, route.name)
                self.restores.append((route.dependant, "call", original))

    def endpoint(self, original, operation):
        @functools.wraps(original)
        def measured(request):
            row = {
                "request_id": request.state.request_id,
                "operation": operation,
                "phase": self.mode,
                "utc_start": utc(),
                "monotonic_start_ns": time.perf_counter_ns(),
                "spans": [],
                "stack": [],
            }
            token = self.active.set(row)
            profiler = cProfile.Profile(timer=time.thread_time) if self.mode == "profile" else None
            db_request = (
                self.observer.request(operation, request_id=row["request_id"])
                if self.observer
                else contextlib.nullcontext()
            )
            try:
                with db_request, self.span("endpoint_handle"):
                    if profiler:
                        profiler.enable()
                    try:
                        response = original(request)
                        row["status"] = response.status_code
                        return response
                    finally:
                        if profiler:
                            profiler.disable()
            finally:
                row["monotonic_end_ns"] = time.perf_counter_ns()
                row["utc_end"] = utc()
                del row["stack"]
                if profiler:
                    row["profile"] = sorted(
                        [
                            {
                                "file": safe_file(file, self.root),
                                "line": line,
                                "function": function,
                                "primitive_calls": values[0],
                                "calls": values[1],
                                "exclusive_thread_cpu_seconds": values[2],
                                "inclusive_thread_cpu_seconds": values[3],
                            }
                            for (file, line, function), values in pstats.Stats(
                                profiler
                            ).stats.items()
                        ],
                        key=lambda item: item["inclusive_thread_cpu_seconds"],
                        reverse=True,
                    )
                self.rows.append(row)
                self.active.reset(token)

        return measured

    def close(self):
        for owner, name, original in reversed(self.restores):
            setattr(owner, name, original)


def observer_from(args):
    if args.db_observer is None:
        return None
    data = args.db_observer.read_bytes()
    if hashlib.sha256(data).hexdigest() != args.observer_sha256:
        raise ValueError("Observer hash mismatch")
    spec = importlib.util.spec_from_file_location("diagnostic_database_trace", args.db_observer)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.DatabaseTrace(max_requests=64)


def fixture(args):
    from fastapi.testclient import TestClient
    from sqlalchemy import create_engine
    from sqlalchemy.pool import StaticPool
    from t44.api import create_app
    from t44.persistence import SqlAlchemyUnitOfWorkFactory, create_mysql_engine
    from t44.persistence.accounts import initialize_user
    from t44.persistence.schema import TABLES, metadata
    from t44.services.identity import HASHER
    from t44.settings import Settings

    if args.mode == "mysql":
        if not args.allow_mysql_ci or os.environ.get("CI") != "true":
            raise ValueError("MySQL requires explicit CI-only gate")
        settings = Settings.from_env().mysql_settings()
        if (
            settings.database != args.expected_database
            or args.expected_database != "t44_diagnostics"
            or os.environ.get("T44_DATABASE") != args.expected_database
            or settings.host not in {"127.0.0.1", "localhost"}
        ):
            raise ValueError("MySQL target is not the dedicated local CI schema")
        engine = create_mysql_engine(settings)
    else:
        engine = create_engine(
            "sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False}
        )
        metadata.create_all(engine)
    factory = SqlAlchemyUnitOfWorkFactory(engine)
    try:
        with factory() as uow:
            counts = {table: uow.gateway.count(table) for table in TABLES}
            if any(counts.values()):
                raise ValueError("Diagnostic requires an empty application schema")
        hashed = HASHER.hash("synthetic-diagnostic-password")
        users = {
            role: initialize_user(factory, username=role, display_name=role, password_hash=hashed)
            for role in ("manager", "developer", "reviewer")
        }
        app = create_app(factory=factory, settings=Settings(login_attempts=1000))
        with TestClient(app) as client:
            yield client, app, factory, engine, users
    finally:
        engine.dispose()


def run(args, root, report):
    from t44.contracts import OPERATIONS, violations
    from t44.services.codes import Action

    observer = observer_from(args)
    stages = Stages(root, observer)
    fixture_generator = fixture(args)
    try:
        client, app, _, engine, users = next(fixture_generator)

        def send(operation, *, token=None, body=None, **path):
            op = OPERATIONS[operation]
            headers = {"Authorization": f"Bearer {token}"} if token else {}
            if any(p.get("$ref", "").endswith("/IdempotencyKey") for p in op.get("parameters", [])):
                headers["Idempotency-Key"] = str(uuid4())
            start = time.perf_counter_ns()
            response = client.request(
                op["method"], "/api/v1" + op["path"].format(**path), headers=headers, json=body
            )
            client_wall = time.perf_counter_ns() - start
            assert response.status_code == op["success_status"], response.status_code
            data = response.json()
            schema = op["responses"][str(response.status_code)]["content"]["application/json"][
                "schema"
            ]
            assert not violations(schema, data)
            if stages.rows and stages.rows[-1]["request_id"] == response.headers["x-request-id"]:
                stages.rows[-1]["client_wall_ns"] = client_wall
            return data["data"]

        tokens = {
            role: send(
                "login", body={"username": role, "password": "synthetic-diagnostic-password"}
            )["access_token"]
            for role in users
        }
        pid = send("createProject", token=tokens["manager"], body={"name": "CPU diagnostic"})["id"]
        for role, roles in (("developer", [2]), ("reviewer", [1, 3])):
            send(
                "addProjectMember",
                token=tokens["manager"],
                project_id=pid,
                body={"username": role, "roles": roles, "reason": "Synthetic diagnostic"},
            )
        iid = send(
            "createIteration",
            token=tokens["manager"],
            project_id=pid,
            body={
                "name": "diagnostic",
                **{k: v for k, v in PLAN.items() if k != "estimated_hours"},
                "capacity": [{"user_id": users["developer"], "available_hours": 240}],
            },
        )["id"]
        payload = {
            "title": "Synthetic task",
            "iteration_id": iid,
            "owner_id": users["developer"],
            "plan": PLAN,
            "dependency_task_ids": [],
        }
        tasks = [
            send("createTask", token=tokens["manager"], project_id=pid, body=payload)["task"]
            for _ in range(20)
        ]
        task = tasks[0]
        if observer:
            observer.install(engine)
        stages.install(app)

        def get_task():
            return send("getTask", token=tokens["developer"], project_id=pid, task_id=task["id"])

        def list_tasks():
            return send("listTasks", token=tokens["developer"], project_id=pid)

        def contract():
            return send(
                "validateContractPayload",
                token=tokens["developer"],
                project_id=pid,
                body={"category": 1, "payload": payload},
            )

        def transition():
            nonlocal task
            blocked = task["state"] == 3
            fields = (
                {"basis": "Resume intake", "evidence": EVIDENCE}
                if blocked
                else {"reason": "Synthetic block", "responsibility_stage": 1}
            )
            task = send(
                "transitionTask",
                token=tokens["developer"],
                project_id=pid,
                task_id=task["id"],
                body={
                    "expected_version": task["version"],
                    "action": Action.UNBLOCK if blocked else Action.BLOCK,
                    **fields,
                },
            )["task"]
            return task

        operations = (get_task, list_tasks, contract, transition)
        for operation in operations:
            operation()
        stages.mode = "measured"
        for operation in operations:
            for _ in range(args.samples):
                operation()
        stages.mode = "profile"
        for operation in operations:
            operation()
        report["requests"] = stages.rows
        report["setup"] = {
            "projects": 1,
            "tasks": 20,
            "users": 3,
            "measured_setup_excluded": True,
            "pool_already_used_by_setup": True,
        }
    finally:
        stages.close()
        fixture_generator.close()
        if observer:
            report["database_observer"] = observer.snapshot()
            observer.close()
        report["requests"] = stages.rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--expected-source", required=True)
    parser.add_argument("--mode", choices=("sqlite", "mysql"), default="sqlite")
    parser.add_argument("--allow-mysql-ci", action="store_true")
    parser.add_argument("--expected-database")
    parser.add_argument("--samples", type=int, choices=range(1, 13), default=12)
    parser.add_argument("--db-observer", type=Path)
    parser.add_argument("--observer-sha256")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not args.run:
        parser.error("Explicit --run required")
    if bool(args.db_observer) != bool(args.observer_sha256):
        parser.error("Observer path and hash must be paired")
    root = Path(__file__).resolve().parents[2]
    if (
        subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
        != args.expected_source
    ):
        parser.error("Source HEAD differs from explicit expected source")
    files = (*SOURCE_FILES, str(Path(__file__).relative_to(root)))
    hashes = {}
    for name in files:
        data = (root / name).read_bytes()
        if data != subprocess.check_output(["git", "show", f"HEAD:{name}"], cwd=root):
            parser.error("Commit exact source and tool before running")
        hashes[name] = hashlib.sha256(data).hexdigest()
    candidate = args.output.absolute()
    output = candidate.parent.resolve() / candidate.name
    if not output.parent.is_relative_to(root / "agents/backend/performance-20261025"):
        parser.error("Output restricted to this public synthetic diagnostic directory")
    output.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "source": args.expected_source,
        "source_files": hashes,
        "mode": args.mode,
        "utc_start": utc(),
        "monotonic_start_ns": time.perf_counter_ns(),
        "clock": "stages use wall and actual worker thread CPU; cProfile uses thread CPU",
        "inclusive_overlaps": True,
        "cprofile_overhead_in_profile_samples_only": True,
        "formal_concurrency_or_latency_acceptance": False,
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "packages": {
                p: version(p) for p in ("fastapi", "jsonschema", "SQLAlchemy", "referencing")
            },
        },
    }

    def stop(_signal, _frame):
        raise TimeoutError("Diagnostic wall limit")

    signal.signal(signal.SIGALRM, stop)
    signal.alarm(180)
    fd = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    try:
        stream = os.fdopen(fd, "w", encoding="utf-8")
    except BaseException:
        os.close(fd)
        raise
    with stream:
        try:
            run(args, root, report)
            report["status"] = "completed sequential diagnostic only"
        except BaseException as error:
            report["status"], report["exception_class"] = "failed retained", type(error).__name__
            raise
        finally:
            signal.alarm(0)
            report["utc_end"], report["monotonic_end_ns"] = utc(), time.perf_counter_ns()
            stream.write(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(
        json.dumps(
            {
                "status": report["status"],
                "requests": len(report["requests"]),
                "output": str(output.relative_to(root)),
            }
        )
    )


if __name__ == "__main__":
    main()
