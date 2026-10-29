"""Opt-in, bounded a12 CPU diagnostic: fresh SQLite, real HTTP, no network."""

import argparse
import contextvars
import cProfile
import functools
import hashlib
import importlib.util
import io
import json
import os
import platform
import pstats
import signal
import socket
import subprocess
import sys
import tarfile
import tempfile
import time
from collections import Counter
from datetime import UTC, datetime
from importlib.metadata import version
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

SOURCE = "a12e9e70b963bacafda3242bb6d82e53ee912ff1"
FIXTURE_SHA = "e0a49e630957268195adc6d6f1cd924bf6481b533f7c3c276b3e832b21aeba49"
ACTIVE = contextvars.ContextVar("profile_request", default=None)


def export_source(root, destination):
    raw = subprocess.run(["git", "archive", SOURCE, "backend/t44"], cwd=root, capture_output=True, check=True).stdout
    manifests = []
    with tarfile.open(fileobj=io.BytesIO(raw)) as archive:
        for item in archive.getmembers():
            if item.isdir():
                continue
            if not item.isfile() or ".." in Path(item.name).parts or not item.name.startswith("backend/t44/"):
                raise ValueError("REGULAR_SOURCE_ONLY")
            data = archive.extractfile(item).read()
            target = destination / item.name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            expected = subprocess.run(
                ["git", "rev-parse", f"{SOURCE}:{item.name}"], cwd=root, capture_output=True, check=True, text=True
            ).stdout.strip()
            actual = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
            if actual != expected:
                raise ValueError("SOURCE_BLOB_MISMATCH")
            manifests.append({"file": item.name, "git_blob": actual, "sha256": hashlib.sha256(data).hexdigest()})
    return manifests


def safe_path(filename, exported):
    if filename.startswith(str(exported) + "/"):
        return filename.removeprefix(str(exported) + "/")
    if "site-packages/" in filename:
        return "site-packages/" + filename.split("site-packages/", 1)[1]
    if filename.startswith("<") or filename == "~":
        return filename
    return "harness/" + Path(filename).name


class Probe:
    def __init__(self):
        self.phase, self.rows, self.profiles, self.restores = "setup", [], {}, []

    def install(self, app):
        from fastapi.routing import APIRoute
        from t44.persistence.rows import RowsGateway
        from t44.services import runtime

        original_rows = RowsGateway.rows
        original_auth = runtime.authenticate

        @functools.wraps(original_rows)
        def rows(gateway, table, where=None, **options):
            active = ACTIVE.get()
            if active is not None and self.phase == "shape":
                key = (table, tuple(sorted(where or {})), options.get("lock"), options.get("limit"))
                active["queries"][repr(key)] += 1
            return original_rows(gateway, table, where, **options)

        @functools.wraps(original_auth)
        def authenticate(*args, **options):
            active = ACTIVE.get()
            if active is not None and self.phase == "shape":
                active["authenticate_calls"] += 1
            return original_auth(*args, **options)

        self.restores.extend([(RowsGateway, "rows", original_rows), (runtime, "authenticate", original_auth)])
        RowsGateway.rows, runtime.authenticate = rows, authenticate
        for route in app.routes:
            if isinstance(route, APIRoute):
                original = route.dependant.call
                route.dependant.call = self.wrap(original, route.name)
                self.restores.append((route.dependant, "call", original))

    def wrap(self, original, operation):
        @functools.wraps(original)
        def call(request):
            row = {"phase": self.phase, "operation": operation, "queries": Counter(), "authenticate_calls": 0}
            token = ACTIVE.set(row)
            profiler = cProfile.Profile(timer=time.thread_time) if self.phase == "profile" else None
            start_wall, start_cpu = time.perf_counter_ns(), time.thread_time_ns()
            try:
                if profiler:
                    profiler.enable()
                response = original(request)
                row["status"] = response.status_code
                return response
            finally:
                if profiler:
                    profiler.disable()
                end_cpu, end_wall = time.thread_time_ns(), time.perf_counter_ns()
                if profiler:
                    if operation in self.profiles:
                        self.profiles[operation].add(profiler)
                    else:
                        self.profiles[operation] = pstats.Stats(profiler)
                row.update(thread_cpu_ms=(end_cpu - start_cpu) / 1e6, handler_wall_ms=(end_wall - start_wall) / 1e6)
                row["queries"] = dict(row["queries"])
                if self.phase != "setup":
                    self.rows.append(row)
                ACTIVE.reset(token)

        return call

    def close(self):
        for owner, name, original in reversed(self.restores):
            setattr(owner, name, original)


def diagnose(root, exported, report):
    # This process never contacts a MySQL server or any network endpoint.
    def denied(*args, **kwargs):
        report["network_or_mysql_attempts_blocked"] += 1
        raise RuntimeError("NETWORK_AND_MYSQL_FORBIDDEN")

    socket.socket.connect = denied
    socket.socket.connect_ex = denied
    socket.create_connection = denied
    sys.path.insert(0, str(exported / "backend"))
    from t44 import persistence
    from t44.contracts import OPERATIONS, violations
    from t44.services.codes import Action

    persistence.create_mysql_engine = denied

    fixture_path = root / "tmp/834_backend_performance/834_request_profile.py"
    if hashlib.sha256(fixture_path.read_bytes()).hexdigest() != FIXTURE_SHA:
        raise ValueError("DEVELOPMENT_FIXTURE_HASH_MISMATCH")
    spec = importlib.util.spec_from_file_location("approved_development_fixture", fixture_path)
    fixture = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fixture)
    generator = fixture.fixture(SimpleNamespace(mode="sqlite"))
    probe = Probe()
    requests = 0
    try:
        client, app, _, engine, users = next(generator)
        if engine.url.drivername != "sqlite" or engine.url.database is not None:
            raise ValueError("NEW_MEMORY_SQLITE_ONLY")

        def send(operation, token=None, body=None, **path):
            nonlocal requests
            requests += 1
            if requests > 160:
                raise ValueError("REQUEST_CAP")
            op = OPERATIONS[operation]
            headers = {"Authorization": f"Bearer {token}"} if token else {}
            if any(p.get("$ref", "").endswith("/IdempotencyKey") for p in op.get("parameters", [])):
                headers["Idempotency-Key"] = str(uuid4())
            response = client.request(op["method"], "/api/v1" + op["path"].format(**path), headers=headers, json=body)
            if response.status_code != op["success_status"]:
                raise ValueError(f"HTTP_STATUS_{operation}_{response.status_code}")
            payload = response.json()
            schema = op["responses"][str(response.status_code)]["content"]["application/json"]["schema"]
            if violations(schema, payload):
                raise ValueError("INDEPENDENT_ORIGINAL_RESPONSE_SCHEMA_FAILED")
            return payload["data"]

        tokens = {
            role: send("login", body={"username": role, "password": "synthetic-diagnostic-password"})["access_token"]
            for role in users
        }
        pid = send("createProject", token=tokens["manager"], body={"name": "CPU profile only"})["id"]
        for role, roles in (("developer", [2]), ("reviewer", [1, 3])):
            send(
                "addProjectMember",
                token=tokens["manager"],
                project_id=pid,
                body={"username": role, "roles": roles, "reason": "Synthetic profile"},
            )
        iid = send(
            "createIteration",
            token=tokens["manager"],
            project_id=pid,
            body={
                "name": "profile",
                **{k: v for k, v in fixture.PLAN.items() if k != "estimated_hours"},
                "capacity": [{"user_id": users["developer"], "available_hours": 240}],
            },
        )["id"]
        payload = {
            "title": "Synthetic profile task",
            "iteration_id": iid,
            "owner_id": users["developer"],
            "plan": fixture.PLAN,
            "dependency_task_ids": [],
        }
        tasks = [send("createTask", token=tokens["manager"], project_id=pid, body=payload)["task"] for _ in range(20)]
        task = tasks[0]
        report["setup_requests"] = requests
        probe.install(app)

        def transition():
            nonlocal task
            blocked = task["state"] == 3
            fields = (
                {"basis": "Resume", "evidence": fixture.EVIDENCE}
                if blocked
                else {"reason": "Synthetic block", "responsibility_stage": 1, "evidence": fixture.EVIDENCE}
            )
            task = send(
                "transitionTask",
                token=tokens["manager"],
                project_id=pid,
                task_id=task["id"],
                body={
                    "expected_version": task["version"],
                    "action": Action.UNBLOCK if blocked else Action.BLOCK,
                    **fields,
                },
            )["task"]

        calls = (
            lambda: send("getTask", token=tokens["developer"], project_id=pid, task_id=task["id"]),
            lambda: send("listTasks", token=tokens["developer"], project_id=pid),
            lambda: send(
                "validateContractPayload",
                token=tokens["developer"],
                project_id=pid,
                body={"category": 1, "payload": payload},
            ),
            transition,
        )
        for phase, cycles in (("warmup", 1), ("measured", 20), ("profile", 5), ("shape", 1)):
            probe.phase = phase
            for _ in range(cycles):
                for call in calls:
                    call()
        report.update(
            status="completed",
            total_http_requests=requests,
            rows=probe.rows,
            fixture={"users": 3, "projects": 1, "tasks": 20, "database": "fresh-process-memory-SQLite"},
        )
        report["profiles"] = {}
        for operation, stats in probe.profiles.items():
            items = [
                {
                    "file": safe_path(file, exported),
                    "line": line,
                    "function": name,
                    "primitive_calls": v[0],
                    "calls": v[1],
                    "exclusive_cpu_seconds": v[2],
                    "inclusive_cpu_seconds": v[3],
                }
                for (file, line, name), v in stats.stats.items()
            ]
            report["profiles"][operation] = {
                "samples": 5,
                "total_profiled_cpu_seconds": stats.total_tt,
                "functions": sorted(items, key=lambda r: r["exclusive_cpu_seconds"], reverse=True),
            }
    finally:
        report["total_http_requests"] = requests
        report["rows"] = probe.rows
        probe.close()
        generator.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    if args.output.parent.resolve() != root / "agents/backend/cpu-profile-20261028":
        raise ValueError("ROLE_OUTPUT_ONLY")
    if os.environ.get("DATABASE_URL") or os.environ.get("T44_DATABASE"):
        raise ValueError("DATABASE_ENVIRONMENT_MUST_BE_UNSET")
    fd = os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    report = {
        "status": "started",
        "source": SOURCE,
        "tool_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "utc_started": datetime.now(UTC).isoformat(),
        "network_or_mysql_attempts_blocked": 0,
        "platform": platform.platform(),
        "python": platform.python_version(),
        "versions": {
            p: version(p) for p in ("fastapi", "starlette", "SQLAlchemy", "jsonschema", "httpx", "referencing")
        },
        "clock": "actual handler thread CPU; separate measured/profile phases",
        "formal_acceptance": False,
    }

    def expired(*args):
        raise TimeoutError("LOCAL_60_SECOND_CAP")

    signal.signal(signal.SIGALRM, expired)
    signal.alarm(60)
    try:
        with tempfile.TemporaryDirectory(prefix="t44-a12-profile-") as temporary:
            exported = Path(temporary)
            report["source_manifest"] = export_source(root, exported)
            diagnose(root, exported, report)
    except BaseException as error:
        report.update(status="failed", failure_class=type(error).__name__)
        raise
    finally:
        signal.alarm(0)
        report["utc_finished"] = datetime.now(UTC).isoformat()
        with os.fdopen(fd, "w") as output:
            output.write(json.dumps(report, indent=2) + "\n")
    print(
        json.dumps(
            {"status": report["status"], "http_requests": report["total_http_requests"], "output": str(args.output)}
        )
    )


if __name__ == "__main__":
    main()
