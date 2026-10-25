"""Explicit final-source native application binding; no business fixture/DDL/token issue."""

import argparse
import hashlib
import importlib.util
import io
import json
import os
import re
import signal
import ssl
import subprocess
import tarfile
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from urllib.parse import quote, unquote, urlsplit
from uuid import uuid4

PROJECT = Path("/Users/yang/Desktop/nothing/软件开发大作业")
BASE = PROJECT / ".agent-worktrees/.runtime/native-isolated-20261025/runs"
APPENV = PROJECT / ".agent-worktrees/.runtime/continuation-20261025/independent-functional-db/application-env.json"
DATABASE = "t44_i829_20261025"
SUBSET = ("backend/t44", "backend/requirements.lock", "backend/pyproject.toml")


def controller(run):
    if run.absolute().parent != BASE or not re.fullmatch(r"[a-z0-9_]{8,48}", run.name):
        raise ValueError("OWNED_RUN_REQUIRED")
    # The original immutable controller remains the deadline/ownership authority.
    path = run / "controller.py"
    for candidate in (run, path, run / "manifest.json"):
        info = candidate.lstat()
        if candidate.is_symlink() or info.st_uid != os.getuid() or info.st_mode & 0o077:
            raise ValueError("PRIVATE_CONTROLLER_REQUIRED")
    manifest = json.loads((run / "manifest.json").read_text())
    if hashlib.sha256(path.read_bytes()).hexdigest() != manifest["controller_sha256"]:
        raise ValueError("IMMUTABLE_CONTROLLER_CHANGED")
    spec = importlib.util.spec_from_file_location("isolated_immutable_controller", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.load(run)
    return module


def database_env(value):
    if not isinstance(value, dict) or set(value) != {"DATABASE_URL", "T44_DATABASE", "T44_SESSION_TTL_SECONDS"}:
        raise ValueError("EXPLICIT_ENVIRONMENT_REQUIRED")
    url = urlsplit(value["DATABASE_URL"])
    if not (
        url.scheme == "mysql+pymysql"
        and url.hostname == "127.0.0.1"
        and url.port == 13306
        and unquote(url.path[1:]) == value["T44_DATABASE"] == DATABASE
        and unquote(url.username or "") == DATABASE
        and url.password
        and not url.query
        and not url.fragment
    ):
        raise ValueError("ROOT_SELECTED_NEW_DATABASE_REQUIRED")
    if not 60 <= int(value["T44_SESSION_TTL_SECONDS"]) <= 86400:
        raise ValueError("SESSION_TTL_REQUIRED")
    return dict(value)


def token_window(expiry, now=None):
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", expiry):
        raise ValueError("EXPLICIT_TOKEN_EXPIRY_REQUIRED")
    value = datetime.fromisoformat(expiry.replace("Z", "+00:00")).timestamp()
    if value < (time.time() if now is None else now) + 60:
        raise ValueError("TOKEN_EXPIRY_TOO_NEAR")
    return value


def binding(run, module):
    value = module.read(run / "application-binding.json")
    source = Path(value["application_root"])
    if source.parent != run or source.name != "application-" + value["source_commit"]:
        raise ValueError("FINAL_SOURCE_PATH_REQUIRED")
    if module.sha((run / "application-controller.py").read_bytes()) != value["application_controller_sha256"]:
        raise ValueError("APPLICATION_CONTROLLER_CHANGED")
    for name, expected in value["source_files"].items():
        path = source / name
        if path.is_symlink() or module.sha(path.read_bytes()) != expected:
            raise ValueError("FINAL_SOURCE_CHANGED")
    return value


def bind(run, repository, source_sha):
    module = controller(run)
    module.admitted()
    if not re.fullmatch(r"[0-9a-f]{40}", source_sha):
        raise ValueError("EXACT_FINAL_SOURCE_REQUIRED")
    if (run / "application-binding.json").exists():
        raise ValueError("FINAL_BINDING_ALREADY_EXISTS")
    module.private(APPENV)
    env = database_env(module.read(APPENV))
    raw = module.git(repository, "archive", source_sha, *SUBSET)
    source = run / ("application-" + source_sha)
    source.mkdir(mode=0o700)
    files = {}
    with tarfile.open(fileobj=io.BytesIO(raw)) as archive:
        for item in archive:
            path = Path(item.name)
            allowed = (
                not path.is_absolute()
                and ".." not in path.parts
                and any(item.name == p or item.name.startswith(p + "/") for p in SUBSET)
            )
            if not allowed:
                if item.isdir() and item.name == "backend":
                    continue
                raise ValueError("UNEXPECTED_FINAL_ARCHIVE_ENTRY")
            if item.isdir():
                (source / path).mkdir(mode=0o700, parents=True, exist_ok=True)
            elif item.isfile():
                data = archive.extractfile(item).read()
                target = source / path
                target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
                module.write(target, data)
                files[item.name] = module.sha(data)
            else:
                raise ValueError("NONREGULAR_FINAL_SOURCE")
    original = module.read(run / "manifest.json")
    if files["backend/requirements.lock"] != original["dependency_lock_sha256"]:
        raise ValueError("FINAL_DEPENDENCY_LOCK_DIFFERS")
    module.command(
        run, ["/Users/yang/Library/Application Support/MinerU/tools/uv", "pip", "check", "--python", original["python"]]
    )
    broker = module.broker_for(run)
    credentials = module.read(broker.credentials)
    env["AMQP_URL"] = (
        "amqp://"
        + quote(credentials["username"], safe="")
        + ":"
        + quote(credentials["password"], safe="")
        + "@127.0.0.1:"
        + str(module.PORTS["amqp"])
        + "/"
        + quote(credentials["vhost"], safe="")
    )
    env["PYTHONPATH"] = str(source / "backend")
    env["T44_SCHEDULER_LOCK_FILE"] = str(run / "state/final-scheduler.lock")
    imported = json.loads(
        module.command(
            run,
            [
                original["python"],
                "-c",
                "import json,t44,t44.services.runtime;print(json.dumps({'t44':t44.__file__,'runtime':t44.services.runtime.__file__}))",
            ],
            env_extra={"PYTHONPATH": env["PYTHONPATH"]},
        )
    )
    if any(not Path(path).is_relative_to(source) for path in imported.values()):
        raise ValueError("ACTUAL_IMPORTED_SOURCE_DIFFERS")
    module.save(run / "secrets/application-environment.json", env)
    module.write(run / "application-controller.py", Path(__file__).read_bytes())
    value = {
        "source_commit": source_sha,
        "application_root": str(source),
        "source_files": files,
        "source_subset": list(SUBSET),
        "repository_tree_oid": module.git(repository, "rev-parse", source_sha + "^{tree}").decode().strip(),
        "backend_tree_oid": module.git(repository, "rev-parse", source_sha + ":backend/t44").decode().strip(),
        "archive_sha256": module.sha(raw),
        "application_controller_sha256": module.sha(Path(__file__).read_bytes()),
        "baseline_prepare_commit": original["source_commit"],
        "database": DATABASE,
        "ports": original["ports"],
        "python": original["python"],
        "actual_module_files": imported,
        "dependency_lock_sha256": files["backend/requirements.lock"],
        "native_build": "exact selected Python runtime source subset;no Docker image",
        "created_at_utc": module.stamp(),
    }
    module.save(run / "application-binding.json", value)
    return module.receipt(
        run,
        "final_application_bind",
        success=True,
        source_commit=source_sha,
        binding=str(run / "application-binding.json"),
        source_files=len(files),
    )


def cwd_of(pid):
    result = subprocess.run(
        ["/usr/sbin/lsof", "-a", "-p", str(pid), "-d", "cwd", "-F", "n"], capture_output=True, text=True, timeout=5
    )
    paths = [line[1:] for line in result.stdout.splitlines() if line.startswith("n")]
    if result.returncode or len(paths) != 1:
        raise ValueError("APPLICATION_CWD_UNCONFIRMED")
    return Path(paths[0]).resolve()


def spawn(run, role, argv, env, value, module):
    _old, actual = module.owned(run, role)
    if actual is not None:
        raise ValueError("APPLICATION_ALREADY_RUNNING")
    outputs = []
    for suffix in ("stdout", "stderr"):
        path = run / "logs" / (role + "-" + uuid4().hex + "." + suffix)
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        outputs.append(os.fdopen(descriptor, "wb"))
    try:
        child = subprocess.Popen(
            list(map(str, argv)),
            cwd=value["application_root"],
            env=module.environment(env),
            stdin=subprocess.DEVNULL,
            stdout=outputs[0],
            stderr=outputs[1],
            start_new_session=True,
        )
    finally:
        for output in outputs:
            output.close()
    time.sleep(0.2)
    identity = module.broker_module(run).process_identity(child.pid)
    if identity is None or identity["uid"] != os.getuid() or identity["pgid"] != child.pid:
        raise RuntimeError("APPLICATION_SPAWN_UNCONFIRMED")
    record = {key: item for key, item in identity.items() if key != "command"}
    record.update(role=role, source_commit=value["source_commit"], argv=list(map(str, argv)), at_utc=module.stamp())
    module.save(run / "state" / (role + "-" + uuid4().hex + ".history.json"), record)
    module.save(run / "state" / (role + ".json"), record, replace=True)
    if cwd_of(child.pid) != Path(value["application_root"]):
        raise ValueError("APPLICATION_CWD_DIFFERS")
    return record


def api_children(run, value, module):
    record, actual = module.owned(run, "api")
    if actual is None:
        raise ValueError("API_SUPERVISOR_ABSENT")
    result = subprocess.run(["/usr/bin/pgrep", "-P", str(record["pid"])], capture_output=True, text=True, timeout=5)
    children = []
    for pid in result.stdout.split():
        identity = module.broker_module(run).process_identity(int(pid))
        if identity is None:
            continue
        parent = subprocess.run(["/bin/ps", "-p", pid, "-o", "ppid="], capture_output=True, text=True, timeout=3)
        if (
            int(parent.stdout.strip()) != record["pid"]
            or identity["uid"] != os.getuid()
            or identity["pgid"] != record["pgid"]
        ):
            raise ValueError("API_CHILD_OWNERSHIP_DIFFERS")
        if cwd_of(int(pid)) != Path(value["application_root"]):
            raise ValueError("API_CHILD_CWD_DIFFERS")
        children.append(
            {key: item for key, item in identity.items() if key != "command"}
            | {"worker": "spawn_main" in identity["command"]}
        )
    if sum(item["worker"] for item in children) != 4:
        raise ValueError("FOUR_REAL_API_WORKERS_REQUIRED")
    module.save(run / "state/api-children.json", {"supervisor_pid": record["pid"], "children": children}, replace=True)
    return children


def start(run):
    module = controller(run)
    module.admitted()
    value = binding(run, module)
    env = module.read(run / "secrets/application-environment.json")
    module.ports_free([module.PORTS["api"]])
    broker = module.broker_for(run)
    if broker.owner("rabbit")[1] is None or module.owned(run, "guardian")[1] is None:
        raise ValueError("OWNED_BROKER_AND_GUARDIAN_REQUIRED")
    try:
        watcher = spawn(
            run,
            "application_guardian",
            [value["python"], run / "application-controller.py", "watchdog", "--run-dir", run],
            {},
            value,
            module,
        )
        api = spawn(
            run,
            "api",
            [
                value["python"],
                "-m",
                "uvicorn",
                "t44.api:app",
                "--host",
                "127.0.0.1",
                "--port",
                str(module.PORTS["api"]),
                "--workers",
                "4",
                "--no-access-log",
                "--no-proxy-headers",
                "--ssl-certfile",
                run / "tls/server.pem",
                "--ssl-keyfile",
                run / "tls/server.key",
            ],
            env,
            value,
            module,
        )
        context = ssl.create_default_context(cafile=str(run / "tls/ca.pem"))
        deadline = time.monotonic() + 30
        ready = False
        while time.monotonic() < deadline:
            try:
                urllib.request.urlopen(
                    "https://127.0.0.1:" + str(module.PORTS["api"]) + "/api/v1/projects", context=context, timeout=2
                )
            except urllib.error.HTTPError as error:
                ready = error.code == 401
                if ready:
                    break
            except (OSError, urllib.error.URLError):
                pass
            time.sleep(0.2)
        if not ready:
            raise RuntimeError("STRICT_TLS_AUTH_PATH_NOT_READY")
        children = api_children(run, value, module)
        consumer = spawn(run, "consumer", [value["python"], "-m", "t44.messaging"], env, value, module)
        time.sleep(0.5)
        if module.owned(run, "consumer")[1] is None:
            raise RuntimeError("CONSUMER_EARLY_EXIT")
        return module.receipt(
            run,
            "application_start",
            success=True,
            source_commit=value["source_commit"],
            api_pid=api["pid"],
            consumer_pid=consumer["pid"],
            api_worker_pids=[v["pid"] for v in children if v["worker"]],
            strict_ca_ip_unauthenticated_status=401,
            scheduler_started=False,
            application_guardian_pid=watcher["pid"],
        )
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError):
        cleanup = [module.stop_app(run, role) for role in ("consumer", "api")]
        module.receipt(run, "application_start", success=False, cleanup=cleanup)
        raise


def child_match(record, actual):
    return (
        actual is not None
        and actual["uid"] == os.getuid()
        and all(actual[key] == record[key] for key in ("pid", "uid", "started", "pgid", "command_sha256"))
    )


def stop_children(run, module):
    path = run / "state/api-children.json"
    if not path.exists():
        return []
    rows = []
    for record in module.read(path)["children"]:
        actual = module.broker_module(run).process_identity(record["pid"])
        if actual is None:
            rows.append({"pid": record["pid"], "success": True, "absent": True})
            continue
        if not child_match(record, actual):
            rows.append({"pid": record["pid"], "success": False, "error": "CHILD_IDENTITY_CHANGED"})
            continue
        os.kill(record["pid"], signal.SIGTERM)
        end = time.monotonic() + 2
        while time.monotonic() < end and module.broker_module(run).process_identity(record["pid"]) is not None:
            time.sleep(0.05)
        actual = module.broker_module(run).process_identity(record["pid"])
        if actual is not None and child_match(record, actual):
            os.kill(record["pid"], signal.SIGKILL)
            time.sleep(0.1)
        rows.append(
            {"pid": record["pid"], "success": module.broker_module(run).process_identity(record["pid"]) is None}
        )
    return rows


def watchdog(run):
    module = controller(run)
    # Stop applications before the original08:47 broker guardian; old guardian remains untouched.
    end_utc = module.STOP - 30
    end_mono = time.monotonic() + max(0, end_utc - time.time())
    requested = []

    def request(signum, _frame):
        requested.append(signum)

    signal.signal(signal.SIGTERM, request)
    signal.signal(signal.SIGINT, request)
    path = run / "state" / ("application-resources-" + uuid4().hex + ".ndjson")
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    failed = False
    try:
        with os.fdopen(descriptor, "w") as output:
            while not requested and time.time() < end_utc and time.monotonic() < end_mono:
                rows = []
                registered = run / "state/api-children.json"
                if registered.exists():
                    for record in module.read(registered)["children"]:
                        actual = module.broker_module(run).process_identity(record["pid"])
                        if actual is not None and child_match(record, actual):
                            raw = subprocess.run(
                                ["/bin/ps", "-p", str(record["pid"]), "-o", "pid=,uid=,%cpu=,rss=,etime="],
                                capture_output=True,
                                text=True,
                                timeout=3,
                            )
                            rows.append(
                                {
                                    "pid": record["pid"],
                                    "worker": record["worker"],
                                    "ps": raw.stdout.strip(),
                                    "exit_code": raw.returncode,
                                }
                            )
                output.write(
                    json.dumps(
                        {
                            "at_utc": module.stamp(),
                            "monotonic_ns": time.monotonic_ns(),
                            "realtime_ns": time.time_ns(),
                            "api_children": rows,
                        }
                    )
                    + "\n"
                )
                output.flush()
                for _ in range(10):
                    if requested or time.time() >= end_utc or time.monotonic() >= end_mono:
                        break
                    time.sleep(1)
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError):
        failed = True
    finally:
        steps = [module.stop_app(run, role) for role in ("scheduler", "consumer", "api")]
        children = stop_children(run, module)
        module.receipt(
            run,
            "application_watchdog_stop",
            success=not failed and all(x["success"] for x in steps + children),
            sampling_failed=failed,
            steps=steps,
            children=children,
        )
    return {"success": not failed and all(x["success"] for x in steps + children)}


def scheduler_start(run, token, expiry):
    module = controller(run)
    module.admitted()
    value = binding(run, module)
    module.private(token)
    module.private(token.parent, True)
    if token.name == "admin.json":
        raise ValueError("SERVICE_TOKEN_REQUIRED")
    credential = module.read(token)
    if not isinstance(credential.get("access_token"), str) or not 32 <= len(credential["access_token"]) <= 512:
        raise ValueError("SERVICE_TOKEN_REQUIRED")
    token_window(expiry)
    env = module.read(run / "secrets/application-environment.json")
    record = spawn(
        run, "scheduler", [value["python"], "-m", "t44.scheduling", "--token-file", token], env, value, module
    )
    time.sleep(0.5)
    if module.owned(run, "scheduler")[1] is None:
        raise RuntimeError("SCHEDULER_EARLY_EXIT")
    return module.receipt(
        run,
        "scheduler_start",
        success=True,
        source_commit=value["source_commit"],
        pid=record["pid"],
        declared_token_expiry=expiry,
        actual_scans_observed=False,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("bind", "start", "scheduler-start", "watchdog"))
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--repository", type=Path)
    parser.add_argument("--source")
    parser.add_argument("--token-file", type=Path)
    parser.add_argument("--token-expires-utc")
    args = parser.parse_args()
    os.umask(0o077)
    try:
        if args.command == "bind":
            result = bind(args.run_dir, args.repository, args.source)
        elif args.command == "start":
            result = start(args.run_dir)
        elif args.command == "scheduler-start":
            result = scheduler_start(args.run_dir, args.token_file, args.token_expires_utc)
        else:
            result = watchdog(args.run_dir)
        print(json.dumps(result))
        return 0 if result["success"] else 1
    except (OSError, RuntimeError, ValueError, TypeError, KeyError, subprocess.SubprocessError):
        print(json.dumps({"success": False, "error": "ISOLATED_APPLICATION_STEP_FAILED"}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
