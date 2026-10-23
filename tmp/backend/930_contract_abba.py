"""Gated, bounded A/B/B/A contract-read comparison. Import never starts an app or network."""

import argparse
import hashlib
import io
import json
import math
import os
import platform
import runpy
import signal
import socket
import subprocess
import sys
import tarfile
import threading
import time
import traceback
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from importlib.metadata import version
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
PRIVATE = ROOT.parent / ".runtime"
SOURCES = {
    "A": "4c20f32b71635016815420472b9d4bb4fa850df0",
    "B": "5dcb73cc10c38deb14fae68d33318b04d538fecf",
}
URL = "http://127.0.0.1:18083/api/v1"


class Failure(RuntimeError):
    """Messages contain only controlled diagnostics, never external bodies or credentials."""


def utc():
    return datetime.now(UTC).isoformat()


def write(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def git(*args):
    return subprocess.check_output(["git", "-C", str(ROOT), *args], stderr=subprocess.DEVNULL)


def tool_identity():
    commit = git("rev-parse", "HEAD").decode().strip()
    files = {}
    for name in ("930_contract_abba.py", "955_perf_profile.py"):
        path = ROOT / "tmp/backend" / name
        relative = str(path.relative_to(ROOT))
        if git("show", f"{commit}:{relative}") != path.read_bytes():
            raise Failure("Diagnostic tool must match its committed Git object")
        files[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
    return {"commit": commit, "files": files}


def private_json(path, expected):
    if path.resolve() != (PRIVATE / expected).resolve() or path.is_symlink():
        raise Failure("Only the designated neutral private input is allowed")
    stat = path.stat()
    if stat.st_mode & 0o777 != 0o600 or stat.st_uid != os.getuid():
        raise Failure("Private input must be owned by this user and mode0600")
    return json.loads(path.read_text())


def snapshot(commit, target):
    """Verify exported files against Git blob objects without importing the application."""
    target.mkdir(mode=0o700)
    paths = ("backend/t44", "backend/pyproject.toml", "backend/requirements.lock")
    archive = git("archive", commit, *paths)
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
        tar.extractall(target, filter="data")
    algorithm = git("rev-parse", "--show-object-format").decode().strip()
    manifest = {}
    for entry in git("ls-tree", "-rz", commit, "--", *paths).split(b"\0"):
        if not entry:
            continue
        header, name = entry.split(b"\t", 1)
        mode, kind, blob = header.decode().split()
        if kind != "blob" or mode not in ("100644", "100755"):
            raise Failure("Snapshot may contain only regular Git blobs")
        relative = name.decode()
        path = target / relative
        data = path.read_bytes()
        actual_blob = hashlib.new(algorithm, f"blob {len(data)}\0".encode() + data).hexdigest()
        if actual_blob != blob:
            raise Failure("Exported source differs from its Git object")
        manifest[relative] = {"git_blob": blob, "sha256": hashlib.sha256(data).hexdigest()}
    write(target / "manifest.json", {"commit": commit, "files": manifest})
    return manifest


def verify_imports(app_root, commit):
    manifest = json.loads((app_root / "manifest.json").read_text())
    if manifest["commit"] != commit:
        raise Failure("Unexpected application snapshot identity")
    for relative, expected in manifest["files"].items():
        if hashlib.sha256((app_root / relative).read_bytes()).hexdigest() != expected["sha256"]:
            raise Failure("Application snapshot changed after export")
    modules = {}
    for name, module in list(sys.modules.items()):
        if name != "t44" and not name.startswith("t44."):
            continue
        filename = getattr(module, "__file__", None)
        if filename is None:
            paths = [Path(path).resolve() for path in getattr(module, "__path__", ())]
            if not paths or any(
                not path.is_relative_to(app_root / "backend/t44") for path in paths
            ):
                raise Failure("Namespace package belongs to another source tree")
            modules[name] = {"namespace_paths": [str(path) for path in paths]}
            continue
        path = Path(filename).resolve()
        if not path.is_relative_to(app_root / "backend/t44"):
            raise Failure("Imported application module belongs to another source tree")
        relative = str(path.relative_to(app_root))
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != manifest["files"][relative]["sha256"]:
            raise Failure("Actual imported source differs from the pinned Git object")
        modules[name] = {"file": str(path), "sha256": digest}
    return modules


def safe_failure(error):
    return {
        "type": type(error).__name__,
        "reason": str(error) if isinstance(error, Failure) else "External error detail withheld",
        "frames": [
            {"file": f.filename, "line": f.lineno, "function": f.name}
            for f in traceback.extract_tb(error.__traceback__)
        ],
    }


def serve(args):
    start, cpu = time.perf_counter_ns(), time.process_time_ns()
    receipt = {
        "app_commit": SOURCES[args.source],
        "started_at": utc(),
        "pid": os.getpid(),
        "tool": tool_identity(),
    }
    engine = None
    try:
        sys.path.insert(0, str(args.app_root / "backend"))
        from t44.api import create_app
        from t44.persistence import SqlAlchemyUnitOfWorkFactory, create_mysql_engine
        from t44.settings import Settings

        receipt["imports_before"] = verify_imports(args.app_root, receipt["app_commit"])
        settings = Settings.from_env()
        db = settings.mysql_settings()
        if os.environ.get("T44_DATABASE") != "t44_profile" or db.database != "t44_profile":
            raise Failure("Only the explicitly selected t44_profile database is allowed")
        if (db.pool_size, db.max_overflow) != (5, 10):
            raise Failure("Comparison pool must remain5+10")
        engine = create_mysql_engine(db)
        app = create_app(factory=SqlAlchemyUnitOfWorkFactory(engine), settings=settings)
        effective = {}

        async def observe_startup_configuration():
            from anyio.to_thread import current_default_thread_limiter

            effective["thread_tokens"] = current_default_thread_limiter().total_tokens
            if effective["thread_tokens"] != 40:
                raise Failure("Comparison requires40actual thread tokens")

        # Only observe startup configuration; do not wrap any request, runtime or SQL method.
        app.router.add_event_handler("startup", observe_startup_configuration)
        import uvicorn

        server = uvicorn.Server(
            uvicorn.Config(
                app, host="127.0.0.1", port=18083, workers=1, access_log=False, log_level="warning"
            )
        )
        receipt.update(
            workers=1,
            pool_size=db.pool_size,
            max_overflow=db.max_overflow,
            database=db.database,
            port=18083,
            request_instrumentation=False,
            packages={
                n: version(n)
                for n in ("fastapi", "starlette", "sqlalchemy", "pymysql", "jsonschema", "uvicorn")
            },
        )

        def mark_ready():
            while not server.started and not server.should_exit:
                time.sleep(0.01)
            if server.started:
                write(args.output / "ready.json", {**receipt, **effective})

        threading.Thread(target=mark_ready, daemon=True).start()
        previous = signal.signal(signal.SIGTERM, lambda *_: setattr(server, "should_exit", True))
        try:
            server.run()
        finally:
            signal.signal(signal.SIGTERM, previous)
        receipt.update(effective)
        receipt["imports_after"] = verify_imports(args.app_root, receipt["app_commit"])
        receipt["mysql_version"] = engine.dialect.server_version_info
        receipt["pool_status_after"] = engine.pool.status()
    except BaseException as error:
        receipt["failure"] = safe_failure(error)
        raise
    finally:
        if engine is not None:
            engine.dispose()
        receipt.update(
            ended_at=utc(),
            wall_ns=time.perf_counter_ns() - start,
            process_cpu_ns=time.process_time_ns() - cpu,
            cpu_scope="serve-entry through cleanup:app import/startup/sanity/warmup/sample/shutdown; excludes interpreter/tool import; not sample-only CPU",
        )
        write(args.output / "server.json", receipt)


def sample(fixture, output, concurrency, seconds, count_per_worker=0):
    import httpx

    output.mkdir(mode=0o700)
    start, cpu = time.perf_counter_ns(), time.process_time_ns()
    stop, launch, lock = threading.Event(), threading.Event(), threading.Lock()
    ready = threading.Barrier(concurrency + 1)
    deadline = [0.0]
    rows = []
    with (output / "requests.jsonl").open("x", buffering=1) as stream:

        def worker(index):
            count = 0
            with httpx.Client(timeout=2, trust_env=False) as client:
                ready.wait(timeout=3)
                if not launch.wait(timeout=3):
                    raise Failure("Client start barrier did not release")
                while (
                    not stop.is_set()
                    and time.perf_counter() < deadline[0]
                    and (not count_per_worker or count < count_per_worker)
                ):
                    candidate = fixture["candidates"][(index + count) % 3]
                    row = {
                        "worker": index,
                        "ordinal": count,
                        "category": candidate["category"],
                        "started_at": utc(),
                    }
                    before = time.perf_counter_ns()
                    try:
                        result = client.post(
                            URL + f"/projects/{fixture['project_id']}/contract-validations",
                            headers={"Authorization": "Bearer " + fixture["token"]},
                            json=candidate,
                        )
                        row.update(
                            status=result.status_code,
                            request_id=result.headers.get("x-request-id"),
                            server_timing=result.headers.get("server-timing"),
                        )
                        payload = result.json()
                        data = payload.get("data", {})
                        row["valid"] = (
                            result.status_code == 200
                            and data.get("valid") is True
                            and data.get("business_guards_executed") is False
                            and data.get("category") == candidate["category"]
                            and data.get("validated_operation_id")
                            == {1: "createTask", 2: "transitionTask", 3: "createReleaseAssessment"}[
                                candidate["category"]
                            ]
                            and not payload.get("violations")
                            and not data.get("violations")
                        )
                    except Exception as error:
                        row.update(valid=False, exception=type(error).__name__)
                    row["e2e_ns"] = time.perf_counter_ns() - before
                    with lock:
                        rows.append(row)
                        stream.write(json.dumps(row) + "\n")
                    count += 1
                    if not row["valid"]:
                        stop.set()

        with ThreadPoolExecutor(max_workers=concurrency) as executor:
            jobs = [executor.submit(worker, n) for n in range(concurrency)]
            ready.wait(timeout=3)
            deadline[0] = time.perf_counter() + seconds
            measured_start = time.perf_counter_ns()
            launch.set()
            for job in jobs:
                job.result()
    elapsed = time.perf_counter_ns() - measured_start
    ordered = sorted(row["e2e_ns"] / 1e6 for row in rows)
    counts = dict(Counter(str(row["category"]) for row in rows))
    result = {
        "requests": len(rows),
        "errors": sum(not row["valid"] for row in rows),
        "category_counts": counts,
        "concurrency": concurrency,
        "requested_seconds": seconds,
        "sample_wall_ns": elapsed,
        "group_wall_ns": time.perf_counter_ns() - start,
        "client_process_cpu_ns": time.process_time_ns() - cpu,
        "client_cpu_scope": "group setup through worker close and raw JSONL writes; not just HTTP execution",
        "request_rate": len(rows) / (elapsed / 1e9),
        "stat": "nearest-rank ceil(p*n); in-flight requests started before deadline are retained",
        "p50_ms": ordered[math.ceil(len(ordered) * 0.5) - 1] if ordered else None,
        "p95_ms": ordered[math.ceil(len(ordered) * 0.95) - 1] if ordered else None,
        "mean_ms": sum(ordered) / len(ordered) if ordered else None,
        "max_ms": max(ordered) if ordered else None,
        "missing_workers": sorted(set(range(concurrency)) - {r["worker"] for r in rows}),
    }
    write(output / "summary.json", result)
    expected = concurrency * count_per_worker
    if result["errors"] or result["missing_workers"] or (expected and len(rows) != expected):
        raise Failure("Client group failed or did not complete its fixed request count")
    return result


def ps_resource(pid):
    result = subprocess.run(
        ["ps", "-o", "rss=,time=", "-p", str(pid)], capture_output=True, text=True
    )
    return {
        "pid": pid,
        "utc": utc(),
        "rss_kib_and_cpu_time_raw": result.stdout.strip(),
        "host_loadavg": os.getloadavg(),
    }


def controller(args):
    receipt = {
        "started_at": utc(),
        "tool": tool_identity(),
        "phases": [],
        "source_order": ["A", "B", "B", "A"],
    }
    started = time.perf_counter()
    deadline = started + 78  # Leave at least8seconds for controller/supervisor cleanup.
    server = None
    try:
        env = private_json(args.environment, "profile-environment.json")
        private_json(args.credentials, "profile-credentials.json")
        if env.get("T44_DATABASE") != "t44_profile":
            raise Failure("Neutral environment must select profile")
        for key, commit in SOURCES.items():
            snapshot(commit, args.output / key)
        for index, key in enumerate(receipt["source_order"]):
            if time.perf_counter() > deadline - 15:
                raise Failure("Insufficient bounded time to start another phase")
            try:
                with socket.create_connection(("127.0.0.1", 18083), timeout=0.2):
                    raise Failure("Diagnostic port is occupied; do not touch its listener")
            except ConnectionRefusedError:
                pass
            phase = args.output / f"{index + 1}-{key}"
            phase.mkdir(mode=0o700)
            app_root = args.output / key
            child_env = {
                **os.environ,
                **env,
                "PYTHONPATH": str(app_root / "backend"),
                "PYTHONDONTWRITEBYTECODE": "1",
            }
            command = [
                sys.executable,
                str(Path(__file__).resolve()),
                "--execute",
                "--mode",
                "serve",
                "--source",
                key,
                "--app-root",
                str(app_root),
                "--output",
                str(phase),
            ]
            entry = {
                "source": key,
                "app_commit": SOURCES[key],
                "argv": command,
                "started_at": utc(),
            }
            receipt["phases"].append(entry)
            try:
                with (phase / "server.log").open("x") as log:
                    server = subprocess.Popen(
                        command, env=child_env, stdout=log, stderr=subprocess.STDOUT
                    )
                    entry["pid"] = server.pid
                    ready_by = min(deadline, time.perf_counter() + 8)
                    while not (phase / "ready.json").exists():
                        if server.poll() is not None or time.perf_counter() > ready_by:
                            raise Failure("Owned server did not reach listening readiness")
                        time.sleep(0.025)
                    ready = json.loads((phase / "ready.json").read_text())
                    if (
                        ready["pid"] != server.pid
                        or ready["app_commit"] != SOURCES[key]
                        or ready["thread_tokens"] != 40
                    ):
                        raise Failure(
                            "Ready metadata does not match the owned source/configuration"
                        )
                    if index == 0:
                        bootstrap = [
                            sys.executable,
                            str(Path(__file__).resolve()),
                            "--execute",
                            "--mode",
                            "bootstrap",
                            "--output",
                            str(args.output / "bootstrap"),
                            "--credentials",
                            str(args.credentials),
                        ]
                        with (args.output / "bootstrap.log").open("x") as log:
                            result = subprocess.run(
                                bootstrap, stdout=log, stderr=subprocess.STDOUT, timeout=10
                            )
                        if result.returncode:
                            raise Failure("Public bootstrap failed; stop without sampling")
                    fixture_file = args.output / "bootstrap/fixture.json"
                    if fixture_file.stat().st_mode & 0o777 != 0o600:
                        raise Failure("Raw fixture must be private0600")
                    fixture = json.loads(fixture_file.read_text())
                    entry["fixture_sha256"] = hashlib.sha256(fixture_file.read_bytes()).hexdigest()
                    sanity = sample(fixture, phase / "sanity", 1, 3, 3)
                    if sanity["category_counts"] != {"1": 1, "2": 1, "3": 1}:
                        raise Failure("Sanity must validate each of the three categories")
                    entry["warmup"] = sample(fixture, phase / "warmup", 8, 5, 15)
                    if entry["warmup"]["category_counts"] != {"1": 40, "2": 40, "3": 40}:
                        raise Failure("Warmup category distribution must be balanced120")
                    entry["resource_before"] = ps_resource(server.pid)
                    entry["sample"] = sample(fixture, phase / "sample", 8, 8)
                    entry["resource_after"] = ps_resource(server.pid)
            finally:
                if server is not None:
                    if server.poll() is None:
                        server.send_signal(signal.SIGTERM)
                    try:
                        server.wait(timeout=3)
                    except subprocess.TimeoutExpired:
                        entry["forced_kill"] = True
                        server.kill()
                        server.wait(timeout=1)
                    entry.update(exit_code=server.returncode, ended_at=utc())
                    server = None
            if entry["exit_code"] or entry.get("forced_kill"):
                raise Failure("Owned server did not exit normally")
            metadata = json.loads((phase / "server.json").read_text())
            if metadata.get("failure") or any(
                metadata["imports_after"].get(name) != value
                for name, value in metadata["imports_before"].items()
            ):
                raise Failure("Server source verification failed")
            write(args.output / "controller.json", receipt)
    except BaseException as error:
        receipt["failure"] = safe_failure(error)
        raise
    finally:
        receipt.update(ended_at=utc(), wall_seconds=time.perf_counter() - started)
        write(args.output / "controller.json", receipt)


def supervise(args):
    tool = tool_identity()
    args.output.mkdir(mode=0o700, parents=False, exist_ok=False)
    started = time.perf_counter()
    receipt = {
        "started_at": utc(),
        "tool": tool,
        "app_sources": SOURCES,
        "hard_deadline_seconds": 90,
        "host": {
            "system": platform.platform(),
            "machine": platform.machine(),
            "cpu_count": os.cpu_count(),
            "loadavg": os.getloadavg(),
        },
        "scope": "developer short comparison only; not formal400VU/600seconds/4worker or independent acceptance",
    }
    command = [
        sys.executable,
        str(Path(__file__).resolve()),
        "--execute",
        "--mode",
        "controller",
        "--output",
        str(args.output),
        "--environment",
        str(args.environment),
        "--credentials",
        str(args.credentials),
    ]
    child = None
    try:
        with (args.output / "controller.log").open("x") as log:
            child = subprocess.Popen(
                command, stdout=log, stderr=subprocess.STDOUT, start_new_session=True
            )
            receipt.update(controller_pid=child.pid, owned_process_group=child.pid, argv=command)
            try:
                child.wait(timeout=max(0.1, 86 - (time.perf_counter() - started)))
            except subprocess.TimeoutExpired:
                receipt["deadline_stop"] = True
                os.killpg(child.pid, signal.SIGTERM)
                try:
                    child.wait(timeout=max(0.1, 89 - (time.perf_counter() - started)))
                except subprocess.TimeoutExpired:
                    receipt["forced_group_kill"] = True
                    os.killpg(child.pid, signal.SIGKILL)
                    child.wait(timeout=0.5)
            receipt["controller_exit_code"] = child.returncode
    finally:
        if child is not None:
            # Every descendant inherits this newly-created session. Never address another PGID.
            try:
                os.killpg(child.pid, signal.SIGTERM)
                receipt["remaining_owned_group_cleanup"] = True
                time.sleep(0.1)
                os.killpg(child.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        receipt.update(ended_at=utc(), wall_seconds=time.perf_counter() - started)
        write(args.output / "run.json", receipt)
    if receipt.get("controller_exit_code") != 0 or any(
        receipt.get(k)
        for k in ("deadline_stop", "forced_group_kill", "remaining_owned_group_cleanup")
    ):
        raise Failure("Overall controller failed; retain partial phase evidence")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument(
        "--mode", choices=("run", "controller", "serve", "bootstrap"), default="run"
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--environment", type=Path, default=PRIVATE / "profile-environment.json")
    parser.add_argument("--credentials", type=Path, default=PRIVATE / "profile-credentials.json")
    parser.add_argument("--source", choices=tuple(SOURCES))
    parser.add_argument("--app-root", type=Path)
    args = parser.parse_args()
    if not args.execute:
        parser.error("Requires explicit coordinator-authorized execution; no default load")
    args.output = args.output.resolve()
    if not args.output.is_relative_to(PRIVATE) or args.output == PRIVATE:
        parser.error("Output must be a fresh project-private runtime directory")
    if args.mode == "serve" and (args.source is None or args.app_root is None):
        parser.error("Internal serve requires an exact source snapshot")
    os.umask(0o077)
    try:
        if args.mode == "run":
            supervise(args)
        elif args.mode == "controller":

            def stop_requested(*_):
                raise Failure("Supervisor requested bounded controller cleanup")

            signal.signal(signal.SIGTERM, stop_requested)
            controller(args)
        elif args.mode == "serve":
            serve(args)
        else:
            credentials = private_json(args.credentials, "profile-credentials.json")
            if credentials.get("database") != "t44_profile":
                raise Failure("Neutral accounts must belong to profile")
            helper = runpy.run_path(str(ROOT / "tmp/backend/955_perf_profile.py"))["client_run"]
            result = helper(
                SimpleNamespace(
                    mode="bootstrap",
                    output=args.output,
                    credentials=args.credentials,
                    concurrency=1,
                    seconds=5,
                ),
                SOURCES["A"],
            )
            if result:
                raise Failure("Public bootstrap did not complete")
    except BaseException as error:
        # Print types/frames only. External exceptions can include credentials in messages.
        print(json.dumps({"failure": safe_failure(error)}), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
