"""Finite owned native application capability cycle; no migrate/seed/DDL commands."""

from __future__ import annotations

import argparse
import fcntl
import importlib.util
import ipaddress
import json
import os
import re
import signal
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

_SPEC = importlib.util.spec_from_file_location("t44_native_broker", Path(__file__).with_name("runtime.py"))
broker_runtime = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(broker_runtime)
private_write = broker_runtime.private_write
require_private = broker_runtime.require_private
digest = broker_runtime.digest
utc = broker_runtime.utc

NODE = Path("/Users/yang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node")
PNPM = NODE.parent / "node_modules/pnpm/bin/pnpm.mjs"
UV = Path("/Users/yang/Library/Application Support/MinerU/tools/uv")
PYTHON = Path("/Library/Frameworks/Python.framework/Versions/3.12/bin/python3.12")
APP_PORTS = {"api": 18088, "ui": 5178}
ALLOWED_ROOTS = {"backend", "frontend", "specs", "deployment"}


def json_bytes(value):
    def encode(item):
        if isinstance(item, datetime):
            return item.isoformat()
        raise TypeError("PUBLIC_JSON_TYPE_REJECTED")
    return (json.dumps(value, ensure_ascii=False, indent=2, default=encode) + "\n").encode()


def write_json(path, value):
    private_write(path, json_bytes(value))


def replace_json(path, value):
    if path.exists():
        require_private(path)
    temporary = path.with_name(path.name + "." + uuid4().hex)
    write_json(temporary, value)
    os.replace(temporary, path)


def phase_base(project):
    base = project.resolve() / ".agent-worktrees/.runtime/native-demo-20261023"
    require_private(base, directory=True)
    if base.resolve() != base:
        raise ValueError("PROJECT_PHASE_DIRECTORY_REQUIRED")
    return base


def verify_binding(project, path, expected=None):
    binding = json.loads(path.read_text())
    commit = binding["source_commit"]
    if not re.fullmatch(r"[a-f0-9]{40}", commit) or (expected is not None and commit != expected):
        raise ValueError("EXACT_SOURCE_REQUIRED")
    source = project / binding["source_root"]
    if source != phase_base(project) / "source" / commit or source.resolve() != source:
        raise ValueError("SOURCE_PATH_REJECTED")
    for name, sha in binding["source_files"].items():
        relative = Path(name)
        if relative.is_absolute() or ".." in relative.parts or relative.parts[0] not in ALLOWED_ROOTS:
            raise ValueError("SOURCE_MANIFEST_PATH_REJECTED")
        if any(part in {"tmp", "tests", "agents", "records", "node_modules"} for part in relative.parts):
            raise ValueError("NON_SOURCE_PATH_REJECTED")
        target = source / relative
        if target.is_symlink() or not target.is_file() or digest(target.read_bytes()) != sha:
            raise ValueError("SOURCE_HASH_MISMATCH")
    # Coordinator denominators describe backend and frontend/src business source;
    # deployment helpers and vite.config.ts remain hash-checked above.
    py = sum(name.startswith("backend/") and name.endswith(".py") for name in binding["source_files"])
    ts = sum(name.startswith("frontend/src/") and name.endswith((".ts", ".vue")) for name in binding["source_files"])
    if (py, ts) != (binding["python_file_count"], binding["ts_vue_file_count"]):
        raise ValueError("SOURCE_DENOMINATOR_MISMATCH")
    return binding, source


def copy_source(binding, source, target):
    target.mkdir(mode=0o700)
    for name, sha in binding["source_files"].items():
        path = target / name
        path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        data = (source / name).read_bytes()
        if digest(data) != sha:
            raise ValueError("SOURCE_CHANGED_DURING_COPY")
        private_write(path, data)


def verify_copy(binding, source):
    if any(digest((source / name).read_bytes()) != sha
           for name, sha in binding["source_files"].items()):
        raise ValueError("OWNED_SOURCE_CHANGED")


def clean_env(extra=None):
    env = {key: os.environ[key] for key in ("HOME", "home", "CODEX_HOME") if key in os.environ}
    env.update(PATH=str(NODE.parent) + ":/usr/bin:/bin:/usr/sbin:/sbin",
               LANG="en_US.UTF-8", LC_ALL="en_US.UTF-8", PYTHONUNBUFFERED="1")
    if extra:
        env.update(extra)
    return env


def capture(argv, cwd, env, logs, *, timeout=180):
    """Every argv must already be credential-free. Raw output remains private."""
    start = utc()
    process = subprocess.Popen(argv, cwd=cwd, env=env, stdin=subprocess.DEVNULL,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
    time.sleep(0.05)
    identity = broker_runtime.process_identity(process.pid)
    try:
        stdout, stderr = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        actual = broker_runtime.process_identity(process.pid)
        if identity is not None and broker_runtime.same_owner(identity, actual):
            os.kill(process.pid, signal.SIGTERM)
        try:
            stdout, stderr = process.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            raise RuntimeError("COMMAND_STOP_UNCONFIRMED") from None
    invocation = uuid4().hex
    for suffix, value in (("stdout", stdout), ("stderr", stderr)):
        private_write(logs / (invocation + "." + suffix), value)
    receipt = {"started_at_utc": start, "ended_at_utc": utc(), "argv": list(map(str, argv)),
               "cwd": str(cwd), "exit_code": process.returncode,
               "stdout_sha256": digest(stdout), "stderr_sha256": digest(stderr),
               "private_output_id": invocation}
    write_json(logs / (invocation + ".json"), receipt)
    if process.returncode:
        raise RuntimeError("OWNED_COMMAND_FAILED")
    return stdout, receipt


def prepare_dependencies(project, binding_path):
    os.umask(0o077)
    binding, source = verify_binding(project, binding_path)
    base = phase_base(project) / "dependencies"
    base.mkdir(mode=0o700, exist_ok=True)
    backend_lock = binding["source_files"]["backend/requirements.lock"]
    frontend_lock = binding["source_files"]["frontend/pnpm-lock.yaml"]
    target = base / (backend_lock[:16] + "_" + frontend_lock[:16])
    if target.exists():
        require_private(target, directory=True)
        ready = json.loads((target / "ready.json").read_text())
        if ready["backend_lock_sha256"] != backend_lock or ready["frontend_lock_sha256"] != frontend_lock:
            raise ValueError("DEPENDENCY_BINDING_MISMATCH")
        return {"success": True, "reused": True, "dependency_dir": str(target), **ready}
    target.mkdir(mode=0o700)
    logs = target / "logs"
    logs.mkdir(mode=0o700)
    copy_source(binding, source, target / "source")
    cache = target / "uv-cache"
    store = target / "pnpm-store"
    env = clean_env({"UV_CACHE_DIR": str(cache), "CI": "true"})
    commands = [
        [str(PYTHON), "--version"], [str(UV), "--version"], [str(NODE), "--version"],
        [str(NODE), str(PNPM), "--version"],
        [str(UV), "--no-config", "venv", "--python", str(PYTHON), str(target / "venv")],
        [str(UV), "--no-config", "pip", "sync", "--python", str(target / "venv/bin/python"),
         "--require-hashes", "--default-index", "https://pypi.org/simple",
         str(source / "backend/requirements.lock")],
        [str(UV), "--no-config", "pip", "check", "--python", str(target / "venv/bin/python")],
    ]
    receipts = []
    versions = []
    for index, argv in enumerate(commands):
        stdout, receipt = capture(argv, target, env, logs)
        receipts.append(receipt)
        if index < 4:
            versions.append(stdout.decode().strip())
        if index == 3 and (not versions[0].startswith("Python 3.12.")
                           or not versions[2].startswith("v24.") or versions[3] != "11.25.0"):
            raise ValueError("PINNED_TOOL_VERSION_REQUIRED")
    frontend = target / "source/frontend"
    _stdout, receipt = capture([str(NODE), str(PNPM), "install", "--frozen-lockfile", "--ignore-scripts",
                                "--ignore-workspace", "--store-dir", str(store)], frontend, env, logs)
    receipts.append(receipt)
    for argv in ([str(NODE), str(frontend / "node_modules/vue-tsc/bin/vue-tsc.js"), "--noEmit"],
                 [str(NODE), str(frontend / "node_modules/vite/bin/vite.js"), "build"]):
        _stdout, receipt = capture(argv, frontend, env, logs)
        receipts.append(receipt)
    inventory, receipt = capture([str(target / "venv/bin/python"), "-c",
        ("import importlib.metadata as m,json;print(json.dumps(sorted((d.metadata['Name'],d.version)"
         "for d in m.distributions())))")], target, env, logs)
    receipts.append(receipt)
    verify_copy(binding, target / "source")
    ready = {"source_commit_used_for_dependency_copy": binding["source_commit"],
             "backend_lock_sha256": backend_lock, "frontend_lock_sha256": frontend_lock,
             "completed_at_utc": utc(), "commands": receipts,
             "tool_versions": versions, "python_distributions": json.loads(inventory), "source_unchanged": True}
    write_json(target / "ready.json", ready)
    return {"success": True, "reused": False, "dependency_dir": str(target), **ready}


def load_inputs(project):
    base = phase_base(project)
    values = {}
    for name in ("environment", "credentials", "database"):
        path = base / (name + ".json")
        require_private(path)
        values[name] = json.loads(path.read_text())
    db, env = values["database"], values["environment"]
    url = urllib.parse.urlsplit(env["DATABASE_URL"])
    if not (db["host"] == url.hostname == "127.0.0.1"
            and type(db["port"]) is int and db["port"] == url.port == 13306
            and db["database"] == env["T44_DATABASE"] == urllib.parse.unquote(url.path[1:]) == "t44_native_demo"
            and db["username"] == urllib.parse.unquote(url.username or "") == "t44_native_app"
            and db["password"] == urllib.parse.unquote(url.password or "")
            and url.scheme == "mysql+pymysql"):
        raise ValueError("EXPLICIT_NEW_DATABASE_REQUIRED")
    if set(values["credentials"]) != {"manager", "developer", "reviewer"}:
        raise ValueError("EXPLICIT_SYNTHETIC_ROLES_REQUIRED")
    for account in values["credentials"].values():
        if set(account) != {"username", "password"} or any(not isinstance(v, str) or not v for v in account.values()):
            raise ValueError("INVALID_PRIVATE_ACCOUNT")
    return values


def assert_app_ports_free():
    for port in APP_PORTS.values():
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
            listener.bind(("127.0.0.1", port))


def current_cwd(pid):
    result = subprocess.run(["/usr/sbin/lsof", "-a", "-p", str(pid), "-d", "cwd", "-F", "n"],
                            capture_output=True, text=True, check=False)
    paths = [line[1:] for line in result.stdout.splitlines() if line.startswith("n")]
    if result.returncode or len(paths) != 1:
        raise ValueError("PROCESS_CWD_UNCONFIRMED")
    return Path(paths[0]).resolve()


def matches_process(record, actual, *, leader=True):
    return actual is not None and actual["uid"] == os.getuid() and all(
        actual[key] == record[key] for key in ("pid", "uid", "started", "pgid", "command_sha256")
    ) and (not leader or actual["pgid"] == actual["pid"])


class Application:
    def __init__(self, project, run):
        self.project = project.resolve()
        base = phase_base(self.project) / "runs"
        self.run = run.absolute()
        if self.run.parent != base or self.run.resolve() != self.run:
            raise ValueError("OWNED_APPLICATION_RUN_REQUIRED")
        require_private(self.run, directory=True)
        require_private(self.run / "manifest.json")
        self.manifest = json.loads((self.run / "manifest.json").read_text())
        self.binding = self.manifest["source_binding"]
        self.source = self.run / "source"
        verify_copy(self.binding, self.source)
        self.dependency = Path(self.manifest["dependency_dir"])
        if not self.dependency.resolve().is_relative_to(phase_base(self.project) / "dependencies"):
            raise ValueError("PROJECT_DEPENDENCY_REQUIRED")
        self.python = self.dependency / "venv/bin/python"
        self.inputs = load_inputs(self.project)
        require_private(self.run / "secrets/environment.json")
        self.environment = json.loads((self.run / "secrets/environment.json").read_text())
        if self.environment["PYTHONPATH"] != str(self.source / "backend"):
            raise ValueError("EXACT_APPLICATION_PYTHONPATH_REQUIRED")
        self.broker = broker_runtime.NativeBroker(self.project, Path(self.manifest["broker_run"]))
        self.processes = {}
        user = self.run / "secrets/manager-session.json"
        reclaimed = self.run / "state/user-session-reclaimed.json"
        self.user_token = json.loads(user.read_text())["data"]["access_token"] if user.exists() and not reclaimed.exists() else None
        issued = self.run / "state/issued-sessions.json"
        self.issued = json.loads(issued.read_text())["session_ids"] if issued.exists() else []

    @classmethod
    def prepare(cls, project, binding_path, expected, dependency):
        os.umask(0o077)
        binding, source = verify_binding(project, binding_path, expected)
        inputs = load_inputs(project)
        if not dependency.resolve().is_relative_to(phase_base(project) / "dependencies"):
            raise ValueError("PROJECT_DEPENDENCY_REQUIRED")
        require_private(dependency, directory=True)
        require_private(dependency / "ready.json")
        ready = json.loads((dependency / "ready.json").read_text())
        if any(ready[key] != binding["source_files"][name] for key, name in (
            ("backend_lock_sha256", "backend/requirements.lock"),
            ("frontend_lock_sha256", "frontend/pnpm-lock.yaml"))):
            raise ValueError("EXACT_DEPENDENCY_LOCK_REQUIRED")
        parent = phase_base(project) / "runs"
        parent.mkdir(mode=0o700, exist_ok=True)
        run = parent / (datetime.now(UTC).strftime("app_%Y%m%d_%H%M%S_") + uuid4().hex[:6])
        run.mkdir(mode=0o700)
        for name in ("secrets", "state", "logs", "receipts", "cache"):
            (run / name).mkdir(mode=0o700)
        copy_source(binding, source, run / "source")
        broker = broker_runtime.NativeBroker.prepare(project,
            project / ".agent-worktrees/.runtime/native-mq-20261023/layout.json",
            run.name)
        amqp = json.loads(broker.credentials.read_text())
        env = dict(inputs["environment"])
        env.update(PYTHONPATH=str(run / "source/backend"), T44_SESSION_TTL_SECONDS="300",
                   AMQP_URL="amqp://" + urllib.parse.quote(amqp["username"], safe="") + ":"
                   + urllib.parse.quote(amqp["password"], safe="") + "@127.0.0.1:25674/"
                   + urllib.parse.quote(amqp["vhost"], safe=""),
                   T44_SCHEDULER_TOKEN_FILE=str(run / "secrets/scheduler-token.json"),
                   T44_SCHEDULER_LOCK_FILE=str(run / "state/scanner.lock"))
        write_json(run / "secrets/environment.json", env)
        frontend = run / "source/frontend"
        (frontend / "node_modules").symlink_to(dependency / "source/frontend/node_modules", target_is_directory=True)
        overlay = ("import { mergeConfig } from 'vite';\nimport base from './vite.config.ts';\n"
                   "export default mergeConfig(base," + json.dumps({
                       "cacheDir": str(run / "cache/vite"), "server": {
                           "host": "127.0.0.1", "port": 5178, "strictPort": True,
                           "fs": {"allow": [str(run / "source"), str(dependency / "source/frontend/node_modules")]},
                           "proxy": {"/api/v1": {"target": "http://127.0.0.1:18088", "changeOrigin": False}}}},
                       ensure_ascii=False) + ");\n")
        private_write(frontend / "vite.native.config.mjs", overlay.encode())
        write_json(run / "manifest.json", {
            "created_at_utc": utc(), "source_commit": expected, "source_binding": binding,
            "source_binding_sha256": digest(binding_path.read_bytes()),
            "controller_sha256": digest(Path(__file__).read_bytes()),
            "broker_controller_sha256": digest(Path(__file__).with_name("runtime.py").read_bytes()),
            "dependency_dir": str(dependency), "broker_run": str(broker.run),
            "database": "t44_native_demo", "ports": APP_PORTS, "bounded_seconds": 210,
            "application_start_requires_explicit_final_binding": True,
            "rules_sha256": binding["source_files"]["backend/t44/resources/escalation-rules.json"],
        })
        return cls(project, run)

    def receipt(self, action, **fields):
        value = {"receipt_id": uuid4().hex, "at_utc": utc(), "action": action,
                 "source_commit": self.manifest["source_commit"], **fields}
        self.safe_public(value)
        write_json(self.run / "receipts" / (value["receipt_id"] + ".json"), value)
        return value

    def secret_literals(self):
        values = [self.inputs["database"]["password"], self.inputs["environment"]["DATABASE_URL"]]
        values += [account["password"] for account in self.inputs["credentials"].values()]
        values += [self.broker.cookie.read_text().strip(),
                   json.loads(self.broker.credentials.read_text())["password"]]
        for path in (self.run / "secrets").glob("*.json"):
            content = json.loads(path.read_text())
            candidate = content.get("data", content)
            if isinstance(candidate, dict) and "access_token" in candidate:
                values.append(candidate["access_token"])
        return [value.encode() for value in values if isinstance(value, str) and value]

    def safe_public(self, value):
        raw = json_bytes(value)
        if any(secret in raw for secret in self.secret_literals()):
            raise ValueError("PUBLIC_SECRET_REJECTED")
        return raw

    def env(self, *, ui=False):
        return clean_env({"TMPDIR": str(self.run / "cache"), **({} if ui else self.environment)})

    def select(self, sql, parameters=()):
        if not sql.lstrip().upper().startswith("SELECT "):
            raise ValueError("READ_ONLY_SQL_REQUIRED")
        import pymysql
        db = self.inputs["database"]
        with pymysql.connect(host=db["host"], port=db["port"], user=db["username"], password=db["password"],
                             database=db["database"], charset="utf8mb4", autocommit=True,
                             cursorclass=pymysql.cursors.DictCursor) as connection, connection.cursor() as cursor:
            cursor.execute(sql, parameters)
            return cursor.fetchall()

    def http(self, path, *, method="GET", body=None, token=None, ui=False):
        headers = {"X-Request-ID": str(uuid4())}
        if token:
            headers["Authorization"] = "Bearer " + token
        raw = None if body is None else json.dumps(body).encode()
        if raw is not None:
            headers["Content-Type"] = "application/json"
        request = urllib.request.Request("http://127.0.0.1:" + str(APP_PORTS["ui" if ui else "api"]) + path,
                                         data=raw, headers=headers, method=method)
        try:
            response = urllib.request.urlopen(request, timeout=4)
        except urllib.error.HTTPError as error:
            response = error
        with response:
            payload = response.read()
            status = response.status
        self.receipt("http", path=path, method=method, port=APP_PORTS["ui" if ui else "api"], status=status)
        return status, json.loads(payload) if payload.startswith(b"{") else payload

    def cli(self, *args):
        self.safe_public({"argv": list(args)})
        output, command = capture([str(self.python), "-m", "t44.cli", *args],
                                  self.source, self.env(), self.run / "logs", timeout=20)
        self.receipt("backend_cli", command=args[0], exit_code=command["exit_code"],
                     output_sha256=digest(output))
        return json.loads(output)

    def current_record(self, role):
        pointer = self.run / "state" / (role + "-current.json")
        if not pointer.exists():
            return None
        require_private(pointer)
        name = json.loads(pointer.read_text())["record"]
        if Path(name).name != name:
            raise ValueError("PROCESS_RECORD_PATH_REJECTED")
        path = self.run / "state" / name
        require_private(path)
        return json.loads(path.read_text())

    def own(self, record, *, leader=True):
        process = self.processes.get(record["pid"])
        if process is not None:
            process.poll()
        actual = broker_runtime.process_identity(record["pid"])
        if actual is not None and (not matches_process(record, actual, leader=leader)
                                   or current_cwd(record["pid"]) != Path(record["cwd"])):
            raise ValueError("APPLICATION_PROCESS_OWNER_MISMATCH")
        return actual

    def spawn(self, role):
        previous = self.current_record(role)
        if previous is not None and self.own(previous) is not None:
            raise ValueError("OWNED_ROLE_ALREADY_RUNNING")
        commands = {
            "api": [str(self.python), "-m", "uvicorn", "t44.api:app", "--app-dir", str(self.source / "backend"),
                    "--host", "127.0.0.1", "--port", "18088", "--workers", "4", "--no-access-log"],
            "consumer": [str(self.python), "-m", "t44.messaging"],
            "scanner": [str(self.python), "-m", "t44.scheduling", "--token-file",
                        str(self.run / "secrets/scheduler-token.json")],
            "ui": [str(NODE), str(self.source / "frontend/node_modules/vite/bin/vite.js"),
                   "--config", str(self.source / "frontend/vite.native.config.mjs"), "--host", "127.0.0.1",
                   "--port", "5178", "--strictPort"],
        }
        argv = commands[role]
        self.safe_public({"argv": argv})
        cwd = self.source / "frontend" if role == "ui" else self.source
        invocation = uuid4().hex
        files = []
        for suffix in ("stdout", "stderr"):
            fd = os.open(self.run / "logs" / (role + "-" + invocation + "." + suffix),
                         os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            files.append(os.fdopen(fd, "wb"))
        try:
            process = subprocess.Popen(argv, cwd=cwd, env=self.env(ui=role == "ui"), stdin=subprocess.DEVNULL,
                                       stdout=files[0], stderr=files[1], start_new_session=True)
            self.processes[process.pid] = process
        finally:
            for file in files:
                file.close()
        time.sleep(0.1)
        actual = broker_runtime.process_identity(process.pid)
        if actual is None or actual["uid"] != os.getuid() or actual["pgid"] != process.pid:
            raise RuntimeError("APPLICATION_EARLY_EXIT")
        record = {key: value for key, value in actual.items() if key != "command"}
        record.update(role=role, cwd=str(cwd.resolve()), argv=argv,
                      source_commit=self.manifest["source_commit"], generation=invocation)
        self.own(record)
        filename = role + "-" + invocation + ".json"
        write_json(self.run / "state" / filename, record)
        replace_json(self.run / "state" / (role + "-current.json"), {"record": filename})
        return self.receipt("spawn", success=True, role=role, owner=record)

    def api_workers(self):
        parent = self.current_record("api")
        if parent is None or self.own(parent) is None:
            raise RuntimeError("API_PARENT_ABSENT")
        result = subprocess.run(["/usr/bin/pgrep", "-P", str(parent["pid"])],
                                capture_output=True, text=True, check=False)
        workers, tracker = [], []
        for text in result.stdout.split():
            actual = broker_runtime.process_identity(int(text))
            if actual is None or actual["uid"] != os.getuid() or actual["pgid"] != parent["pgid"]:
                raise ValueError("API_CHILD_OWNER_MISMATCH")
            if current_cwd(actual["pid"]) != self.source:
                raise ValueError("API_CHILD_SOURCE_CWD_MISMATCH")
            record = {key: value for key, value in actual.items() if key != "command"}
            record.update(cwd=str(self.source), source_commit=self.manifest["source_commit"])
            if "multiprocessing.spawn" in actual["command"]:
                workers.append(record)
            elif "multiprocessing.resource_tracker" in actual["command"]:
                tracker.append(record)
            else:
                raise ValueError("UNEXPECTED_API_CHILD")
        if len(workers) != 4:
            raise RuntimeError("FOUR_API_WORKERS_REQUIRED")
        replace_json(self.run / "state/api-children.json", {"workers": workers, "tracker": tracker})
        return self.receipt("api_workers", success=True, worker_count=4, workers=workers, tracker=tracker)

    def listeners(self, role):
        record = self.current_record(role)
        if record is None or self.own(record) is None:
            raise RuntimeError("APPLICATION_LISTENER_OWNER_ABSENT")
        result = subprocess.run(["/usr/sbin/lsof", "-nP", "-a", "-p", str(record["pid"]),
                                 "-iTCP", "-sTCP:LISTEN", "-F", "n"],
                                capture_output=True, text=True, check=False)
        if result.returncode:
            raise RuntimeError("APPLICATION_LISTENER_INSPECTION_FAILED")
        observed = []
        for line in result.stdout.splitlines():
            if line.startswith("n"):
                address, port = line[1:].rsplit(":", 1)
                address = address.strip("[]")
                if not ipaddress.ip_address(address).is_loopback or int(port) != APP_PORTS[role]:
                    raise ValueError("APPLICATION_LISTENER_SCOPE_REJECTED")
                observed.append({"address": address, "port": int(port)})
        if not observed:
            raise RuntimeError("APPLICATION_LISTENER_ABSENT")
        return self.receipt("application_listeners", success=True, role=role, listeners=observed)

    def scanner_lock(self):
        record = self.current_record("scanner")
        if record is None or self.own(record) is None:
            raise RuntimeError("SCANNER_LOCK_OWNER_ABSENT")
        lock = self.run / "state/scanner.lock"
        require_private(lock)
        descriptor = os.open(lock, os.O_RDWR | os.O_NOFOLLOW)
        try:
            try:
                fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                return self.receipt("scanner_lock", success=True, held=True, owner_pid=record["pid"])
            fcntl.flock(descriptor, fcntl.LOCK_UN)
            raise RuntimeError("SCANNER_SHARED_LOCK_NOT_HELD")
        finally:
            os.close(descriptor)

    def pika_connections(self):
        text, command = self.broker.execute("rabbitmqctl", ["list_connections", "user", "vhost", "peer_host",
                                                          "client_properties", "--formatter", "json"])
        rows = json.loads(text)
        products = []
        for row in rows:
            if row["user"] != self.broker.manifest["username"] or row["vhost"] != self.broker.manifest["vhost"] \
                    or not ipaddress.ip_address(row["peer_host"]).is_loopback:
                raise ValueError("AMQP_CONNECTION_SCOPE_REJECTED")
            properties = row["client_properties"]
            if not isinstance(properties, dict):
                raise TypeError("AMQP_CLIENT_PROPERTIES_SHAPE_REJECTED")
            products.append(properties.get("product"))
        if not products or any(not isinstance(product, str) or "pika" not in product.lower() for product in products):
            raise RuntimeError("REAL_PIKA_CONNECTION_UNCONFIRMED")
        return self.receipt("pika_connections", success=True, connection_count=len(rows), products=products,
                            broker_cli_receipt=command["receipt_id"], all_loopback=True, own_user_vhost=True)

    def stop_role(self, role):
        record = self.current_record(role)
        if record is None or self.own(record) is None:
            return self.receipt("stop_role", success=True, role=role, needed=False)
        os.kill(record["pid"], signal.SIGTERM)
        deadline = time.monotonic() + 20
        while time.monotonic() < deadline:
            if self.own(record) is None:
                return self.receipt("stop_role", success=True, role=role, needed=True, signal="SIGTERM")
            time.sleep(0.1)
        return self.receipt("stop_role", success=False, role=role, needed=True, error="STOP_UNCONFIRMED")

    def verify_stopped(self):
        records = []
        for path in (self.run / "state").glob("*.json"):
            value = json.loads(path.read_text())
            if "pid" in value:
                records.append((value, True))
        children = self.run / "state/api-children.json"
        if children.exists():
            value = json.loads(children.read_text())
            records += [(item, False) for item in value["workers"] + value["tracker"]]
        deadline = time.monotonic() + 10
        while True:
            observations = []
            for record, leader in records:
                try:
                    actual = self.own(record, leader=leader)
                    observations.append({"pid": record["pid"], "absent": actual is None})
                except ValueError:
                    observations.append({"pid": record["pid"], "absent": False,
                                         "error": "IDENTITY_CHANGED_NO_SIGNAL"})
            if all(item["absent"] for item in observations) or time.monotonic() >= deadline:
                return self.receipt("post_stop_processes", success=all(item["absent"] for item in observations),
                                    observations=observations)
            time.sleep(0.1)

    def issue_service(self, projects):
        credential = self.run / "secrets" / ("session-" + uuid4().hex + ".json")
        args = ["service-token", "--name", "native_" + self.run.name, "--token-file", str(credential)]
        for project in projects:
            if type(project) is not int or project < 1:
                raise ValueError("EXPLICIT_PROJECT_IDS_REQUIRED")
            args += ["--project-id", str(project)]
        issued = self.cli(*args)
        require_private(credential)
        data = json.loads(credential.read_text())
        if data["session_id"] != issued["session_id"] or not isinstance(data["access_token"], str):
            raise ValueError("SERVICE_CREDENTIAL_MISMATCH")
        self.issued.append(data["session_id"])
        replace_json(self.run / "state/issued-sessions.json", {"session_ids": self.issued})
        row = self.select("SELECT id,actor_kind,project_ids,scopes,created_at,expires_at,revoked_at "
                          "FROM auth_sessions WHERE id=%s", (data["session_id"],))[0]
        projects_actual = json.loads(row["project_ids"]) if isinstance(row["project_ids"], str) else row["project_ids"]
        scopes = json.loads(row["scopes"]) if isinstance(row["scopes"], str) else row["scopes"]
        if row["actor_kind"] != 2 or sorted(projects_actual) != sorted(projects) or scopes != ["escalation:write"] \
                or (row["expires_at"] - row["created_at"]).total_seconds() != 300 or row["revoked_at"] is not None:
            raise ValueError("SERVICE_SCOPE_TTL_MISMATCH")
        stable = self.run / "secrets/scheduler-token.json"
        temporary = stable.with_name(".publish-" + uuid4().hex)
        os.link(credential, temporary)
        os.replace(temporary, stable)
        return self.receipt("service_credential", success=True, session_id=data["session_id"],
                            project_ids=projects_actual, scopes=scopes, ttl_seconds=300,
                            expires_at=row["expires_at"], credential_mode="0600")

    def revoke_service(self, session):
        result = self.cli("revoke-session", "--session-id", str(session))
        row = self.select("SELECT id,revoked_at FROM auth_sessions WHERE id=%s", (session,))[0]
        if row["revoked_at"] is None or result["revoked_sessions"] not in (0, 1):
            raise RuntimeError("SERVICE_REVOCATION_UNCONFIRMED")
        return self.receipt("service_revoked", success=True, session_id=session,
                            revoked_sessions=result["revoked_sessions"], revoked_at=row["revoked_at"])

    def scan_rows(self, baseline):
        return self.select("SELECT id,status,rule_hash,cutoff_at,started_at,heartbeat_at,finished_at,"
                           "scanned_count,created_count,duplicate_count,error_code FROM scan_runs "
                           "WHERE id>%s ORDER BY id", (baseline,))

    def wait_scans(self, baseline, *, count=2, timeout=140):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if self.own(self.current_record("scanner")) is None:
                raise RuntimeError("SCANNER_EXITED")
            rows = self.scan_rows(baseline)
            if any(row["status"] == 3 for row in rows):
                raise RuntimeError("PERSISTED_SCAN_FAILED")
            completed = [row for row in rows if row["status"] == 2]
            if len(completed) >= count:
                for row in completed:
                    if row["rule_hash"].hex() != self.manifest["rules_sha256"] or row["finished_at"] is None:
                        raise ValueError("SCAN_RULE_OR_FINISH_MISMATCH")
                if count > 1:
                    interval = (completed[1]["started_at"] - completed[0]["started_at"]).total_seconds()
                    if interval < 60:
                        raise RuntimeError("REAL_SIXTY_SECOND_INTERVAL_REQUIRED")
                else:
                    interval = None
                public = [{key: value for key, value in row.items() if key != "rule_hash"} for row in completed]
                return self.receipt("persisted_scans", success=True, completed=public,
                                    actual_first_interval_seconds=interval, declared_interval_seconds=60)
            time.sleep(0.5)
        raise RuntimeError("PERSISTED_SCANS_TIMEOUT")

    def delivery(self, baseline):
        deadline = time.monotonic() + 20
        while time.monotonic() < deadline:
            events = self.select("SELECT id,recipients,status,confirmed_at,fallback_at FROM outbox_events "
                                 "WHERE id>%s AND event_type=2 ORDER BY id", (baseline,))
            notices = self.select("SELECT id,event_id,recipient_id,fallback FROM notifications "
                                  "WHERE event_id>%s ORDER BY id", (baseline,))
            if events and all(event["status"] == 3 and event["confirmed_at"] is not None
                              and event["fallback_at"] is None for event in events):
                good = True
                for event in events:
                    recipients = json.loads(event["recipients"]) if isinstance(event["recipients"], str) else event["recipients"]
                    actual = [n["recipient_id"] for n in notices if n["event_id"] == event["id"] and n["fallback"] == 0]
                    good = good and sorted(set(recipients)) == sorted(actual)
                if good:
                    return self.receipt("normal_delivery", success=True, event_ids=[e["id"] for e in events],
                                        confirmed_events=len(events), notification_count=len(notices),
                                        fallback_notification_count=sum(n["fallback"] for n in notices))
            time.sleep(0.2)
        raise RuntimeError("NORMAL_PIKA_DELIVERY_UNCONFIRMED")

    def run_cycle(self):
        actions, failure, broker_started = [], None, False
        try:
            verify_copy(self.binding, self.source)
            assert_app_ports_free()
            imports, command = capture([str(self.python), "-c",
                ("import t44,t44.api,t44.messaging.worker,t44.scheduling.runtime,json,pathlib;"
                "modules=[t44,t44.api,t44.messaging.worker,t44.scheduling.runtime];"
                f"root=pathlib.Path({str(self.source / 'backend')!r});"
                "paths=[str(pathlib.Path(m.__file__).resolve())for m in modules];"
                 "assert all(pathlib.Path(p).is_relative_to(root)for p in paths);print(json.dumps(paths))")],
                self.source, self.env(), self.run / "logs", timeout=20)
            actions.append(self.receipt("exact_import_preflight", success=True,
                                        module_paths=json.loads(imports), exit_code=command["exit_code"]))
            if json.loads((self.source / "backend/t44/resources/escalation-rules.json").read_text())["scan_interval_seconds"] != 60:
                raise ValueError("FROZEN_SIXTY_SECOND_RULE_REQUIRED")
            initial = self.select("SELECT (SELECT COUNT(*) FROM projects) AS projects,"
                                  "(SELECT COUNT(*) FROM tasks) AS tasks,"
                                  "(SELECT COALESCE(MAX(id),0) FROM scan_runs) AS scan_id,"
                                  "(SELECT COALESCE(MAX(id),0) FROM outbox_events) AS outbox_id")[0]
            if (initial["projects"], initial["tasks"]) != (2, 40):
                raise ValueError("EXISTING_DEMO_DATA_REQUIRED")
            status = self.broker.start()
            actions.append(status)
            broker_started = status["success"]
            if not broker_started:
                raise RuntimeError("FRESH_BROKER_START_FAILED")
            self.spawn("api")
            deadline = time.monotonic() + 25
            while time.monotonic() < deadline:
                try:
                    code, _body = self.http("/api/v1/projects")
                    if code == 401:
                        break
                    raise RuntimeError("UNAUTHENTICATED_READY_STATUS_MISMATCH")
                except (urllib.error.URLError, ConnectionError):
                    time.sleep(0.2)
            else:
                raise RuntimeError("API_READINESS_TIMEOUT")
            actions.append(self.api_workers())
            actions.append(self.listeners("api"))
            code, body = self.http("/api/v1/auth/login", method="POST", body=self.inputs["credentials"]["manager"])
            if code != 200:
                raise RuntimeError("SYNTHETIC_LOGIN_FAILED")
            self.user_token = body["data"]["access_token"]
            write_json(self.run / "secrets/manager-session.json", body)
            # Login deliberately omits session_id. Read only this known bearer digest
            # privately to recover its real ID; never archive or print the digest.
            import hashlib
            user_session = self.select("SELECT id FROM auth_sessions WHERE token_hash=%s",
                                       (hashlib.sha256(self.user_token.encode()).digest(),))
            if len(user_session) != 1:
                raise RuntimeError("OWN_USER_SESSION_UNCONFIRMED")
            replace_json(self.run / "state/user-session.json", {"session_id": user_session[0]["id"]})
            code, body = self.http("/api/v1/projects", token=self.user_token)
            projects = sorted(item["id"] for item in body["data"]["items"])
            database_projects = sorted(row["id"] for row in self.select("SELECT id FROM projects ORDER BY id"))
            if code != 200 or projects != database_projects or len(projects) != 2:
                raise RuntimeError("REAL_PROJECT_SCOPE_UNCONFIRMED")
            actions.append(self.receipt("authenticated_projects", success=True, project_ids=projects))
            self.spawn("consumer")
            issued = self.issue_service(projects)
            actions.append(issued)
            self.spawn("scanner")
            self.spawn("ui")
            deadline = time.monotonic() + 25
            while time.monotonic() < deadline:
                try:
                    code, body = self.http("/", ui=True)
                    if code == 200 and b"<html" in body.lower():
                        break
                except (urllib.error.URLError, ConnectionError):
                    time.sleep(0.2)
            else:
                raise RuntimeError("UI_READINESS_TIMEOUT")
            code, _body = self.http("/api/v1/auth/me", token=self.user_token, ui=True)
            if code != 200:
                raise RuntimeError("UI_API_PROXY_FAILED")
            actions.append(self.receipt("ui_ready", success=True, port=5178, proxy_api_port=18088))
            actions.append(self.listeners("ui"))
            actions.append(self.wait_scans(initial["scan_id"]))
            actions.append(self.scanner_lock())
            actions.append(self.pika_connections())
            actions.append(self.delivery(initial["outbox_id"]))
            code, body = self.http("/api/v1/me/notifications", token=self.user_token)
            if code != 200 or body["data"]["total"] < 1:
                raise RuntimeError("AUTHENTICATED_NOTIFICATIONS_UNCONFIRMED")
            actions.append(self.receipt("notifications_api", success=True, total=body["data"]["total"]))
            stopped = self.stop_role("scanner")
            actions.append(stopped)
            if not stopped["success"]:
                raise RuntimeError("SCANNER_DRAIN_FAILED")
            before_rotation = self.select("SELECT COALESCE(MAX(id),0) AS id FROM scan_runs")[0]["id"]
            replacement = self.issue_service(projects)
            actions.append(replacement)
            actions.append(self.revoke_service(issued["session_id"]))
            self.spawn("scanner")
            actions.append(self.wait_scans(before_rotation, count=1, timeout=20))
            actions.append(self.scanner_lock())
            actions.append(self.api_workers())
        except Exception as error:  # noqa: BLE001 - every runtime failure must reach owned cleanup
            message = str(error)
            failure = message if re.fullmatch(r"[A-Z_]+", message) else type(error).__name__
            actions.append(self.receipt("cycle_failure", success=False, error=failure))
        finally:
            cleanup = self.cleanup(broker_started=broker_started)
        return self.receipt("application_cycle", success=failure is None and cleanup["success"],
                            error=failure, actions=actions, cleanup=cleanup)

    def cleanup(self, *, broker_started=True):
        steps = []
        for role in ("ui", "scanner", "consumer"):
            try:
                steps.append(self.stop_role(role))
            except Exception:  # noqa: BLE001 - preserve partial cleanup and continue other owned resources
                steps.append({"role": role, "success": False, "error": "OWNED_STOP_FAILED"})
        for session in list(self.issued):
            try:
                steps.append(self.revoke_service(session))
            except Exception:  # noqa: BLE001 - preserve revocation failure without exposing driver details
                steps.append({"session_id": session, "success": False, "error": "REVOCATION_FAILED"})
        if self.user_token is not None:
            try:
                code, _body = self.http("/api/v1/auth/logout", method="POST", token=self.user_token)
                user_record = self.run / "state/user-session.json"
                user_id = json.loads(user_record.read_text())["session_id"]
                revocation = self.revoke_service(user_id)
                steps.append({"action": "own_user_logout", "success": code == 200 and revocation["success"],
                              "status": code, "session_id": user_id})
                if code == 200 and revocation["success"]:
                    replace_json(self.run / "state/user-session-reclaimed.json", {"session_id": user_id})
            except Exception:  # noqa: BLE001 - preserve logout failure and continue process cleanup
                steps.append({"action": "own_user_logout", "success": False})
        try:
            steps.append(self.stop_role("api"))
        except Exception:  # noqa: BLE001 - a failed API stop must not skip broker cleanup
            steps.append({"role": "api", "success": False, "error": "OWNED_STOP_FAILED"})
        steps.append(self.verify_stopped())
        try:
            steps.append(self.broker.stop(cleanup_failed_start=not broker_started))
        except Exception:  # noqa: BLE001 - return truthful bounded cleanup failure, not a secret traceback
            steps.append({"role": "broker", "success": False, "error": "OWNED_BROKER_STOP_FAILED"})
        verify_copy(self.binding, self.source)
        return self.receipt("cleanup", success=all(step["success"] for step in steps), steps=steps)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, required=True)
    commands = parser.add_subparsers(dest="command", required=True)
    deps = commands.add_parser("prepare-dependencies")
    deps.add_argument("--source-binding", type=Path, required=True)
    prepare = commands.add_parser("prepare")
    prepare.add_argument("--source-binding", type=Path, required=True)
    prepare.add_argument("--expected-source", required=True)
    prepare.add_argument("--dependency-dir", type=Path, required=True)
    for command in ("run", "cleanup"):
        commands.add_parser(command).add_argument("--run-dir", type=Path, required=True)
    args = parser.parse_args()
    os.umask(0o077)
    try:
        project = args.project_root.resolve()
        if args.command == "prepare-dependencies":
            result = prepare_dependencies(project, args.source_binding)
        elif args.command == "prepare":
            app = Application.prepare(project, args.source_binding, args.expected_source, args.dependency_dir)
            result = {"success": True, "run_dir": str(app.run), "source_commit": args.expected_source}
        else:
            app = Application(project, args.run_dir)
            result = app.run_cycle() if args.command == "run" else app.cleanup()
        print(json.dumps(result, ensure_ascii=False, default=str))
        return 0 if result["success"] else 1
    except Exception:  # noqa: BLE001 - CLI emits no exception text that could contain a private URL/token
        print(json.dumps({"success": False, "action": args.command, "error": "NATIVE_APPLICATION_FAILED"}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
