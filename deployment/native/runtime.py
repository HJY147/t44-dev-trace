"""Project-local native Rabbit lifecycle; no application/database commands in stage1."""

from __future__ import annotations

import argparse
import base64
import fcntl
import hashlib
import ipaddress
import json
import os
import re
import secrets
import signal
import socket
import stat
import subprocess
import sys
import time
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

PORTS = {"amqp": 25674, "epmd": 24369, "distribution": 35674}
CLI_PORTS = (45674, 45683)
RESOURCE_PATTERN = r"^(t44[.]events([.]quarantine)?|t44[.]notifications([.]quarantine)?)$"


def utc():
    return datetime.now(UTC).isoformat()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def private_write(path: Path, data: bytes):
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, "wb") as output:
        output.write(data)
        output.flush()
        os.fsync(output.fileno())


def private_json(path, value):
    private_write(path, (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode())


def require_private(path: Path, *, directory=False):
    info = path.lstat()
    expected = stat.S_ISDIR if directory else stat.S_ISREG
    if not expected(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
        raise ValueError("PRIVATE_PATH_REQUIRED")


def erlang_path(path: Path):
    """ASCII codepoint list avoids args_file quoting and UTF8 lexer ambiguities."""
    return "[" + ",".join(str(ord(character)) for character in str(path)) + "]"


def cookie_expression(cookie: Path, marker: Path):
    # No cookie literal, environment override, global home path or shell quoting.
    return (
        f"case(file:read_file({erlang_path(cookie)}))of"
        "{ok,B}->true=erlang:set_cookie(binary_to_atom(string:trim(B),latin1)),"
        f"ok=file:write_file({erlang_path(marker)},[114,101,97,100,121],[exclusive]);"
        "_->halt(78)end."
    )


def cookie_args(cookie, marker, node, run_id, first_port, last_port):
    if not re.fullmatch(r"t44_(?:native_demo|native_cli)_[a-z0-9_]+@localhost", node):
        raise ValueError("EXPLICIT_LOCAL_NODE_REQUIRED")
    return (
        "-nocookie\n-noinput\n-start_epmd false\n"
        f"-sname {node}\n-t44_native_run {run_id}\n"
        "+S 2:2\n+A 2\n"
        "-kernel inet_dist_use_interface {127,0,0,1}\n"
        f"-kernel inet_dist_listen_min {first_port}\n"
        f"-kernel inet_dist_listen_max {last_port}\n"
        "-kernel logger_level warning\n"
        f"-eval {cookie_expression(cookie, marker)}\n"
    ).encode()


def assert_ports_free():
    for port in [*PORTS.values(), *range(CLI_PORTS[0], CLI_PORTS[1] + 1)]:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
            listener.bind(("127.0.0.1", port))


def process_identity(pid):
    result = subprocess.run(
        ["/bin/ps", "-ww", "-p", str(pid), "-o", "uid=", "-o", "lstart=", "-o", "command="],
        capture_output=True, text=True, check=False,
    )
    if result.returncode or not result.stdout.strip():
        return None
    fields = result.stdout.strip().split(maxsplit=6)
    if len(fields) != 7:
        raise ValueError("PROCESS_IDENTITY_UNAVAILABLE")
    return {
        "pid": pid, "uid": int(fields[0]), "started": " ".join(fields[1:6]),
        "pgid": os.getpgid(pid), "command_sha256": digest(fields[6].encode()),
        "command": fields[6],
    }


def same_owner(record, actual):
    return actual is not None and all(
        record[key] == actual[key] for key in ("pid", "uid", "started", "pgid", "command_sha256")
    ) and actual["uid"] == os.getuid() and actual["pgid"] == actual["pid"]


class NativeBroker:
    def __init__(self, project: Path, run: Path):
        self.project, self.run = project.resolve(), run.absolute()
        allowed = self.project / ".agent-worktrees/.runtime/t44-native-broker"
        if self.run.parent != allowed or not re.fullmatch(r"[a-z0-9_]{8,48}", self.run.name):
            raise ValueError("NEW_PROJECT_RUNTIME_REQUIRED")
        require_private(self.run, directory=True)
        if self.run.resolve() != self.run:
            raise ValueError("SYMLINK_RUNTIME_FORBIDDEN")
        for name in ("config", "secrets", "data", "logs", "state", "receipts", "tmp"):
            require_private(self.run / name, directory=True)
        require_private(self.run / "manifest.json")
        self.manifest = json.loads((self.run / "manifest.json").read_text())
        if self.manifest["run_id"] != self.run.name or self.manifest["project"] != str(self.project):
            raise ValueError("MANIFEST_TARGET_MISMATCH")
        self.layout = self.manifest["dependencies"]
        dependency_base = self.project / ".agent-worktrees/.runtime/native-mq-20261023"
        if any(not Path(self.layout[key]).resolve().is_relative_to(dependency_base.resolve())
               for key in ("prefix", "rabbitmq_binary")):
            raise ValueError("PROJECT_DEPENDENCY_REQUIRED")
        if self.manifest["ports"] != PORTS or tuple(self.manifest["cli_ports"]) != CLI_PORTS:
            raise ValueError("FROZEN_PORTS_REQUIRED")
        self.cookie = self.run / "secrets/erlang.cookie"
        self.credentials = self.run / "secrets/amqp.json"
        require_private(self.cookie)
        require_private(self.credentials)

    @classmethod
    def prepare(cls, project: Path, layout_path: Path, run_id: str | None = None):
        os.umask(0o077)
        project = project.resolve()
        run_id = run_id or datetime.now(UTC).strftime("%Y%m%d_%H%M%S_") + secrets.token_hex(4)
        if not re.fullmatch(r"[a-z0-9_]{8,48}", run_id):
            raise ValueError("INVALID_RUN_IDENTIFIER")
        layout = json.loads(layout_path.read_text())
        dependency_base = project / ".agent-worktrees/.runtime/native-mq-20261023"
        for key in ("prefix", "rabbitmq_binary"):
            value = Path(layout[key])
            if not value.resolve().is_relative_to(dependency_base.resolve()):
                raise ValueError("PROJECT_DEPENDENCY_REQUIRED")
        for executable in (Path(layout["prefix"]) / "bin/erl", Path(layout["prefix"]) / "bin/epmd",
                           Path(layout["rabbitmq_binary"]) / "sbin/rabbitmq-server"):
            if not executable.is_file() or not os.access(executable, os.X_OK):
                raise ValueError("DEPENDENCY_EXECUTABLE_ABSENT")
        base = project / ".agent-worktrees/.runtime/t44-native-broker"
        base.mkdir(mode=0o700, exist_ok=True)
        require_private(base, directory=True)
        run = base / run_id
        run.mkdir(mode=0o700, exist_ok=False)
        for name in ("config", "secrets", "data", "logs", "state", "receipts", "tmp"):
            (run / name).mkdir(mode=0o700)
        cookie = secrets.token_hex(32)
        password, username = secrets.token_urlsafe(32), "native_" + secrets.token_hex(8)
        vhost, node = "t44.native.demo." + run_id, "t44_native_demo_" + run_id + "@localhost"
        private_write(run / "secrets/erlang.cookie", (cookie + "\n").encode())
        private_json(run / "secrets/amqp.json", {"username": username, "password": password,
                                                "vhost": vhost})
        private_write(run / "secrets/amqp.password", (password + "\n").encode())
        salt = secrets.token_bytes(4)
        password_hash = base64.b64encode(salt + hashlib.sha256(salt + password.encode()).digest()).decode()
        private_json(run / "config/definitions.json", {
            "rabbit_version": "4.3.6", "vhosts": [{"name": vhost}],
            "users": [{"name": username, "password_hash": password_hash,
                       "hashing_algorithm": "rabbit_password_hashing_sha256", "tags": []}],
            "permissions": [{"user": username, "vhost": vhost, "configure": RESOURCE_PATTERN,
                             "write": RESOURCE_PATTERN, "read": RESOURCE_PATTERN}],
            "parameters": [], "global_parameters": [], "policies": [], "queues": [],
            "exchanges": [], "bindings": [],
        })
        private_write(run / "config/rabbitmq.conf", (
            f"listeners.tcp.1 = 127.0.0.1:{PORTS['amqp']}\n"
            "distribution.listener.interface = 127.0.0.1\n"
            f"distribution.listener.port_range.min = {PORTS['distribution']}\n"
            f"distribution.listener.port_range.max = {PORTS['distribution']}\n"
            "definitions.import_backend = local_filesystem\n"
            f"definitions.local.path = {run / 'config/definitions.json'}\n"
            "log.console = false\nlog.file.level = warning\n"
            f"log.file = {run / 'logs/rabbit.log'}\n"
        ).encode())
        private_write(run / "config/advanced.config", b"[].\n")
        private_write(run / "config/enabled_plugins", b"[].\n")
        private_write(run / "config/rabbitmq-env.conf", b"# Project-local; no secret environment.\n")
        private_write(run / "state/control.lock", b"")
        private_json(run / "manifest.json", {
            "run_id": run_id, "created_at_utc": utc(), "project": str(project),
            "scope": "stage1 broker capability only; no application/database operations",
            "wrapper_sha256": digest(Path(__file__).read_bytes()), "dependencies": layout,
            "dependency_layout_sha256": digest(layout_path.read_bytes()), "node": node,
            "vhost": vhost, "username": username, "ports": PORTS, "cli_ports": CLI_PORTS,
            "cookie_source": "new random project0600 file; nocookie+sname+early file setter",
            "permissions": RESOURCE_PATTERN,
        })
        return cls(project, run)

    @contextmanager
    def locked(self):
        path = self.run / "state/control.lock"
        require_private(path)
        descriptor = os.open(path, os.O_RDWR | os.O_NOFOLLOW)
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
            yield
        finally:
            os.close(descriptor)

    def receipt(self, action, **fields):
        receipt = {"receipt_id": uuid4().hex, "at_utc": utc(), "action": action,
                   "run_id": self.run.name, **fields}
        private_json(self.run / "receipts" / (receipt["receipt_id"] + ".json"), receipt)
        return receipt

    def env(self, args_file: Path | None = None):
        # Preserve the actual environment homes, but inherit no service secrets/debug options.
        env = {key: os.environ[key] for key in ("HOME", "home", "CODEX_HOME") if key in os.environ}
        env.update({
            "PATH": str(Path(self.layout["prefix"]) / "bin") + ":/usr/bin:/bin:/usr/sbin:/sbin",
            "LANG": "en_US.UTF-8", "LC_ALL": "en_US.UTF-8", "TMPDIR": str(self.run / "tmp"),
            "ERL_EPMD_ADDRESS": "127.0.0.1", "ERL_EPMD_PORT": str(PORTS["epmd"]),
            "ERL_FLAGS": "", "ERL_AFLAGS": "-args_file " + str(args_file) if args_file else "",
            "ERL_ZFLAGS": "", "ERL_CRASH_DUMP": str(self.run / "logs" / (uuid4().hex + ".dump")),
            "RABBITMQ_HOME": self.layout["rabbitmq_binary"],
            "RABBITMQ_NODENAME": self.manifest["node"],
            "RABBITMQ_CONF_ENV_FILE": str(self.run / "config/rabbitmq-env.conf"),
            "RABBITMQ_CONFIG_FILE": str(self.run / "config/rabbitmq.conf"),
            "RABBITMQ_ADVANCED_CONFIG_FILE": str(self.run / "config/advanced.config"),
            "RABBITMQ_ENABLED_PLUGINS_FILE": str(self.run / "config/enabled_plugins"),
            "RABBITMQ_MNESIA_BASE": str(self.run / "data"),
            "RABBITMQ_MNESIA_DIR": str(self.run / "data/node"),
            "RABBITMQ_QUORUM_DIR": str(self.run / "data/quorum"),
            "RABBITMQ_STREAM_DIR": str(self.run / "data/stream"),
            "RABBITMQ_FEATURE_FLAGS_FILE": str(self.run / "data/feature_flags"),
            "RABBITMQ_PLUGINS_EXPAND_DIR": str(self.run / "data/plugins-expand"),
            "RABBITMQ_GENERATED_CONFIG_DIR": str(self.run / "config/generated"),
            "RABBITMQ_PID_FILE": str(self.run / "state/rabbit.pid"),
            "RABBITMQ_LOG_BASE": str(self.run / "logs"),
            "RABBITMQ_LOGS": str(self.run / "logs/rabbit.log"),
            "RABBITMQ_LOG": "warning", "RABBITMQ_ALLOW_INPUT": "true",
            "RABBITMQ_CTL_DIST_PORT_MIN": str(CLI_PORTS[0]),
            "RABBITMQ_CTL_DIST_PORT_MAX": str(CLI_PORTS[1]),
        })
        return env

    def make_args(self, *, server=False):
        invocation = uuid4().hex
        marker = self.run / "state" / ("cookie-init-" + invocation)
        node = self.manifest["node"] if server else "t44_native_cli_" + invocation + "@localhost"
        first, last = (PORTS["distribution"],) * 2 if server else CLI_PORTS
        path = self.run / "config" / ("server-" if server else "cli-")
        path = path.with_name(path.name + invocation + ".args")
        private_write(path, cookie_args(self.cookie, marker, node, self.run.name, first, last))
        return path, marker

    def state_path(self, role):
        if role not in ("rabbit", "epmd"):
            raise ValueError("UNKNOWN_PROCESS_ROLE")
        return self.run / "state" / (role + ".json")

    def owner(self, role):
        path = self.state_path(role)
        if not path.exists():
            return None, None
        require_private(path)
        record = json.loads(path.read_text())
        actual = process_identity(record["pid"])
        if actual is not None and not same_owner(record, actual):
            raise ValueError("PROCESS_OWNER_MISMATCH")
        return record, actual

    def spawn(self, role, argv, env, marker):
        old, actual = self.owner(role)
        if old is not None:
            raise ValueError("PROCESS_RECORD_ALREADY_EXISTS")
        outputs = []
        for suffix in ("stdout", "stderr"):
            path = self.run / "logs" / (role + "-" + uuid4().hex + "." + suffix)
            fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            outputs.append(os.fdopen(fd, "wb"))
        try:
            process = subprocess.Popen(argv, env=env, cwd=self.run, stdin=subprocess.DEVNULL,
                                       stdout=outputs[0], stderr=outputs[1], start_new_session=True)
        finally:
            for output in outputs:
                output.close()
        deadline = time.monotonic() + 10
        actual = None
        while time.monotonic() < deadline:
            actual = process_identity(process.pid)
            if actual and marker in actual["command"]:
                break
            if process.poll() is not None:
                raise RuntimeError("OWNED_PROCESS_EARLY_EXIT")
            time.sleep(0.05)
        if not actual or actual["pgid"] != process.pid or actual["uid"] != os.getuid():
            raise RuntimeError("OWNED_PROCESS_IDENTITY_NOT_READY")
        record = {key: value for key, value in actual.items() if key != "command"}
        record.update(role=role, executable=argv[0], argv=argv, registered_at_utc=utc())
        private_json(self.state_path(role), record)
        if marker not in actual["command"]:
            raise RuntimeError("OWNED_PROCESS_MARKER_NOT_READY")
        return self.receipt("spawn", role=role, success=True, owner=record)

    def execute(self, tool, arguments, *, timeout=20):
        args_file, marker = self.make_args()
        argv = [str(Path(self.layout["rabbitmq_binary"]) / "sbin" / tool),
                "-q", "-n", self.manifest["node"], *arguments]
        start = utc()
        process = subprocess.Popen(argv, env=self.env(args_file), cwd=self.run,
                                   stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, start_new_session=True)
        # CLI may finish before ps observes it. A timeout can signal only a saved,
        # fully matched process identity; no identity means no signal authorization.
        identity = None
        identity_deadline = time.monotonic() + 2
        while time.monotonic() < identity_deadline:
            candidate = process_identity(process.pid)
            if candidate and self.run.name in candidate["command"]:
                identity = candidate
                break
            if process.poll() is not None:
                break
            time.sleep(0.02)
        timed_out = False
        try:
            stdout, stderr = process.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            actual = process_identity(process.pid)
            if identity is not None and same_owner(identity, actual):
                os.killpg(process.pid, signal.SIGTERM)
            try:
                stdout, stderr = process.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                self.receipt("cli", argv=argv, started_at_utc=start, exit_code=None,
                             timed_out=True, success=False, error="CLI_STOP_UNCONFIRMED")
                raise RuntimeError("CLI_STOP_UNCONFIRMED") from None
        tag = uuid4().hex
        for suffix, content in (("stdout", stdout), ("stderr", stderr)):
            private_write(self.run / "logs" / (tag + "." + suffix), content)
        literals = [self.cookie.read_bytes().strip(),
                    json.loads(self.credentials.read_text())["password"].encode()]
        matched = any(value in stdout or value in stderr for value in literals)
        receipt = self.receipt(
            "cli", argv=argv, started_at_utc=start, ended_at_utc=utc(), exit_code=process.returncode,
            timed_out=timed_out, cookie_init_marker=marker.exists(),
            cookie_init_args_sha256=digest(args_file.read_bytes()),
            stdout_sha256=digest(stdout), stderr_sha256=digest(stderr),
            secret_literal_found=matched,
            success=process.returncode == 0 and marker.exists() and not matched and not timed_out,
        )
        if not receipt["success"]:
            raise RuntimeError("CLI_CAPABILITY_FAILED")
        return stdout.decode(), receipt

    def listeners(self, role):
        _record, actual = self.owner(role)
        if actual is None:
            raise RuntimeError("OWNED_PROCESS_ABSENT")
        result = subprocess.run(["/usr/sbin/lsof", "-nP", "-a", "-p", str(actual["pid"]),
                                 "-iTCP", "-sTCP:LISTEN", "-F", "n"],
                                capture_output=True, text=True, check=False)
        if result.returncode:
            raise RuntimeError("LISTENER_INSPECTION_FAILED")
        observed = []
        for line in result.stdout.splitlines():
            if not line.startswith("n"):
                continue
            address, port = line[1:].rsplit(":", 1)
            address = address.strip("[]")
            if not ipaddress.ip_address(address).is_loopback:
                raise RuntimeError("NON_LOOPBACK_LISTENER")
            observed.append({"address": address, "port": int(port)})
        expected = {PORTS["epmd"]} if role == "epmd" else {PORTS["amqp"], PORTS["distribution"]}
        if {item["port"] for item in observed} != expected:
            raise RuntimeError("UNEXPECTED_LISTENER_PORTS")
        return observed

    def inspect(self):
        stdout, auth = self.execute("rabbitmqctl", ["eval",
            f"{{ok,B}}=file:read_file({erlang_path(self.cookie)}),"
            "erlang:get_cookie()=:=binary_to_atom(string:trim(B),latin1)."])
        if stdout.strip() != "true":
            raise RuntimeError("SERVER_FILE_COOKIE_MISMATCH")
        # Exercise the real installed password hash, without a password in argv/output.
        password = self.run / "secrets/amqp.password"
        text, password_receipt = self.execute("rabbitmqctl", ["eval",
            f"{{ok,B}}=file:read_file({erlang_path(password)}),"
            f"case(rabbit_auth_backend_internal:user_login_authentication("
            f'<<"{self.manifest["username"]}">>,[{{password,string:trim(B)}}]))of'
            "{ok,_}->true;_->false end."])
        if text.strip() != "true":
            raise RuntimeError("AMQP_PASSWORD_AUTHENTICATION_FAILED")
        values = {}
        for key, arguments in (
            ("users", ["list_users", "--formatter", "json"]),
            ("vhosts", ["list_vhosts", "name", "--formatter", "json"]),
            ("permissions", ["list_permissions", "-p", self.manifest["vhost"], "--formatter", "json"]),
        ):
            text, _receipt = self.execute("rabbitmqctl", arguments)
            values[key] = json.loads(text)
        if {row.get("user", row.get("name")) for row in values["users"]} != {self.manifest["username"]}:
            raise RuntimeError("UNEXPECTED_USERS_OR_GUEST")
        if {row["name"] for row in values["vhosts"]} != {self.manifest["vhost"]}:
            raise RuntimeError("UNEXPECTED_VHOSTS")
        permissions = values["permissions"]
        if len(permissions) != 1 or permissions[0]["user"] != self.manifest["username"] or any(
            permissions[0][key] != RESOURCE_PATTERN for key in ("configure", "write", "read")
        ) or any(row.get("tags") not in ([], "") for row in values["users"]):
            raise RuntimeError("PERMISSION_SCOPE_MISMATCH")
        return self.receipt("inspect", success=True, server_cookie_matches_file=True,
                            authenticated_cli_receipt=auth["receipt_id"],
                            password_backend_authentication=True,
                            password_auth_receipt=password_receipt["receipt_id"],
                            epmd_listeners=self.listeners("epmd"),
                            rabbit_listeners=self.listeners("rabbit"), **values)

    def wait_epmd_ready(self):
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            try:
                return self.listeners("epmd")
            except RuntimeError:
                time.sleep(0.05)
        raise RuntimeError("OWNED_EPMD_LISTENER_NOT_READY")

    def start(self):
        with self.locked():
            assert_ports_free()
            args_file, marker = self.make_args(server=True)
            self.spawn("epmd", [str(Path(self.layout["prefix"]) / "bin/epmd"),
                                "-address", "127.0.0.1", "-port", str(PORTS["epmd"])],
                       self.env(), "epmd")
            self.wait_epmd_ready()
            self.spawn("rabbit", [str(Path(self.layout["rabbitmq_binary"]) / "sbin/rabbitmq-server")],
                       self.env(args_file), self.manifest["node"])
            deadline = time.monotonic() + 45
            failures = []
            while time.monotonic() < deadline:
                try:
                    self.execute("rabbitmq-diagnostics", ["check_running"], timeout=10)
                    if not marker.exists():
                        raise RuntimeError("SERVER_COOKIE_INIT_MARKER_ABSENT")
                    inspection = self.inspect()
                    return self.receipt("start", success=True, cookie_setter_completed=True,
                                        inspection_receipt=inspection["receipt_id"],
                                        prior_readiness_attempts=len(failures),
                                        cookie_args_sha256=digest(args_file.read_bytes()))
                except RuntimeError:
                    failures.append(utc())
                    _record, actual = self.owner("rabbit")
                    if actual is None:
                        break
                    time.sleep(0.5)
            return self.receipt("start", success=False, error="BROKER_READINESS_FAILED",
                                readiness_attempts=len(failures))

    def signal_owned(self, role):
        record, actual = self.owner(role)
        if actual is None:
            return {"role": role, "needed": False, "signal_sent": False, "success": True}
        # owner() verified UID/start time/path fingerprint/PGID immediately before signal.
        os.killpg(record["pgid"], signal.SIGTERM)
        return {"role": role, "needed": True, "signal_sent": True, "success": True}

    def wait_stopped(self, role, timeout=15):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            _record, actual = self.owner(role)
            if actual is None:
                return True
            time.sleep(0.1)
        return False

    def stop(self, *, cleanup_failed_start=False):
        with self.locked():
            steps, success = [], True
            _record, actual = self.owner("rabbit")
            if actual is not None and not cleanup_failed_start:
                try:
                    _text, receipt = self.execute("rabbitmqctl", ["shutdown"], timeout=25)
                    steps.append({"action": "rabbitmqctl_shutdown", "success": True,
                                  "receipt_id": receipt["receipt_id"]})
                except RuntimeError:
                    success = False
                    steps.append({"action": "rabbitmqctl_shutdown", "success": False})
            elif actual is not None:
                steps.append(self.signal_owned("rabbit"))
            rabbit_stopped = self.wait_stopped("rabbit")
            steps.append({"action": "rabbit_exit_observed", "success": rabbit_stopped})
            success = success and rabbit_stopped
            if rabbit_stopped:
                _record, actual = self.owner("epmd")
                names = []
                if actual is not None:
                    result = subprocess.run(
                        [str(Path(self.layout["prefix"]) / "bin/epmd"),
                         "-port", str(PORTS["epmd"]), "-names"],
                        env=self.env(), capture_output=True, text=True, timeout=5, check=False)
                    names = [line for line in result.stdout.splitlines() if line.startswith("name ")]
                    if result.returncode:
                        raise RuntimeError("EPMD_NAMES_UNCONFIRMED")
                empty = not names
                steps.append({"action": "epmd_registered_nodes_empty", "success": empty,
                              "registered_node_count": len(names)})
                if empty:
                    steps.append(self.signal_owned("epmd"))
                    epmd_stopped = self.wait_stopped("epmd")
                    steps.append({"action": "epmd_exit_observed", "success": epmd_stopped})
                    success = success and epmd_stopped
                else:
                    success = False
            return self.receipt("stop", success=success, failed_start_cleanup=cleanup_failed_start,
                                steps=steps)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", required=True, type=Path)
    sub = parser.add_subparsers(dest="command", required=True)
    prepare = sub.add_parser("prepare")
    prepare.add_argument("--dependency-layout", type=Path, required=True)
    prepare.add_argument("--run-id")
    for command in ("start", "inspect", "stop", "cleanup-failed-start"):
        sub.add_parser(command).add_argument("--run-dir", type=Path, required=True)
    args = parser.parse_args()
    os.umask(0o077)
    broker = None
    try:
        if args.command == "prepare":
            broker = NativeBroker.prepare(args.project_root, args.dependency_layout, args.run_id)
            print(json.dumps({"success": True, "run_dir": str(broker.run),
                              "manifest_sha256": digest((broker.run / "manifest.json").read_bytes())}))
            return 0
        broker = NativeBroker(args.project_root, args.run_dir)
        if args.command == "start":
            result = broker.start()
        elif args.command == "inspect":
            with broker.locked():
                result = broker.inspect()
        else:
            result = broker.stop(cleanup_failed_start=args.command == "cleanup-failed-start")
        print(json.dumps(result, ensure_ascii=False))
        return 0 if result["success"] else 1
    except Exception:
        # Driver/driver state and crash output stay private; don't emit raw exceptions.
        result = {"success": False, "action": args.command, "error": "NATIVE_RUNTIME_FAILED"}
        if broker is not None:
            result = broker.receipt(args.command, success=False, error="NATIVE_RUNTIME_FAILED")
        print(json.dumps(result), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
