"""Neutral, bounded controls for one disposable acceptance Compose project."""

import argparse
import fcntl
import json
import os
import re
import stat
import subprocess
import sys
import time
from contextlib import contextmanager
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from deployment import ops  # noqa: E402

SERVICES = ("mysql", "rabbitmq", "api", "consumer", "scheduler", "web")


def private_json(path):
    path = Path(path)
    if path.is_symlink() or stat.S_IMODE(path.stat().st_mode) != 0o600:
        raise ValueError("private state required")
    return json.loads(path.read_text())


def write_private(path, value):
    descriptor = os.open(path, os.O_CREAT | os.O_TRUNC | os.O_WRONLY | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, "w") as stream:
        json.dump(value, stream, indent=2)
        stream.write("\n")


def audit_statement(value):
    # The SELECT-only database principal is the authorization boundary, not this syntax guard.
    value = value.strip().removesuffix(";").rstrip()
    if not value or len(value.encode()) > 32768 or ";" in value:
        raise ValueError("one bounded read-only statement required")
    if not re.match(r"\A(?:SELECT|SHOW|EXPLAIN)\b", value, re.IGNORECASE):
        raise ValueError("read-only audit statement required")
    if re.search(r"\b(?:SLEEP|BENCHMARK|GET_LOCK|RELEASE_LOCK)\s*\(", value, re.IGNORECASE):
        raise ValueError("blocking functions are unavailable through this audit interface")
    return value


class Controls:
    def __init__(self, state_file):
        self.state_file = Path(state_file)
        self.state = private_json(state_file)
        self.runtime = self.state_file.parent
        self.values = ops.load_env(Path(self.state["env_file"]))
        ops.ROOT = Path(self.state["product_root"])

    @contextmanager
    def locked(self):
        descriptor = os.open(self.runtime / "control.lock", os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX)
            yield
        finally:
            os.close(descriptor)

    def event(self, action, service=None, code=0, **fields):
        value = {"at_unix": time.time(), "action": action, "service": service, "exit_code": code, **fields}
        with (Path(self.state["public_dir"]) / "control-events.jsonl").open("a") as stream:
            stream.write(json.dumps(value) + "\n")

    def compose(self, *arguments, data=None, timeout=210, check=True):
        try:
            result = ops.compose(Path(self.state["env_file"]), self.values,
                                 "--file", self.state["override_file"], *arguments,
                                 input=data, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout)
        except subprocess.CalledProcessError as error:
            result = subprocess.CompletedProcess(error.cmd, error.returncode, error.stdout)
        except subprocess.TimeoutExpired as error:
            result = subprocess.CompletedProcess(error.cmd, 124, error.stdout or b"")
        with (self.runtime / "environment-commands.log").open("ab") as stream:
            stream.write(result.stdout or b"")
        if check and result.returncode:
            raise RuntimeError("environment command failed")
        return result

    def recover(self, *, expired_only=False):
        with self.locked():
            leases = private_json(self.runtime / "fault-leases.json")
            if expired_only and not any(deadline <= time.time() for deadline in leases.values()):
                return
            self.compose("unpause", *SERVICES, check=False, timeout=30)
            self.compose("up", "-d", "--no-deps", "--wait", "--wait-timeout", "150", "mysql", "rabbitmq")
            self.compose("up", "-d", "--no-deps", "--wait", "--wait-timeout", "150",
                         "api", "consumer", "scheduler", "web")
            write_private(self.runtime / "fault-leases.json", {})
            self.event("lease-recovery" if expired_only else "recovery")

    def fault(self, service, action, seconds):
        if service not in SERVICES or action not in ("stop", "pause") or not 1 <= seconds <= 120:
            raise ValueError("bounded service fault required")
        with self.locked():
            leases = private_json(self.runtime / "fault-leases.json")
            # Persist intent first, so a failed control command is still recovered by the owner.
            leases[service] = time.time() + seconds
            write_private(self.runtime / "fault-leases.json", leases)
            result = self.compose(action, service, timeout=45, check=False)
            self.event("fault-" + action, service, result.returncode, lease_seconds=seconds)
            if result.returncode:
                raise RuntimeError("fault control failed")

    def audit(self, statement):
        statement = audit_statement(statement)
        credential = private_json(self.runtime / "audit.json")
        script = 'IFS= read -r MYSQL_PWD; export MYSQL_PWD; exec mysql --user=t44_audit --batch --database="$MYSQL_DATABASE"'
        sql = "SET SESSION MAX_EXECUTION_TIME=5000; SET SESSION TRANSACTION READ ONLY;\n" + statement + ";\n"
        # Never persist the SQL, returned rows, or read-only password in the public control ledger.
        try:
            result = ops.compose(Path(self.state["env_file"]), self.values,
                                 "--file", self.state["override_file"], "exec", "-T", "mysql", "sh", "-c", script,
                                 input=(credential["password"] + "\n" + sql).encode(),
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=12)
        except subprocess.CalledProcessError as error:
            self.event("sql-audit", code=error.returncode)
            raise RuntimeError("read-only audit failed") from None
        except subprocess.TimeoutExpired:
            self.event("sql-audit", code=124)
            raise RuntimeError("read-only audit timeout") from None
        self.event("sql-audit")
        return result.stdout

    def broker(self, kind):
        choices = {
            "queues": ["list_queues", "name", "messages_ready", "messages_unacknowledged", "consumers"],
            "connections": ["list_connections", "name", "state", "channels", "user", "vhost"],
        }
        if kind not in choices:
            raise ValueError("unknown broker audit")
        args = choices[kind]
        if kind == "queues":
            args = [args[0], "--vhost", self.values["RABBITMQ_DEFAULT_VHOST"], *args[1:]]
        result = self.compose("exec", "-T", "rabbitmq", "rabbitmqctl", "--quiet", *args, timeout=20)
        self.event("broker-" + kind)
        return result.stdout

    def account(self, username, display_name, password):
        if not re.fullmatch(r"[A-Za-z0-9_.-]{1,64}", username) or not password or len(password) > 128:
            raise ValueError("invalid account input")
        result = self.compose("--profile", "operations", "run", "--rm", "-T", "admin", "init-user",
                              "--username", username, "--display-name", display_name, "--password-stdin",
                              data=(password + "\n").encode())
        self.event("account-initialization")
        return result.stdout

    def scheduler_scope(self, projects):
        if not projects or any(type(value) is not int or not 1 <= value <= 4294967295 for value in projects):
            raise ValueError("explicit project scopes required")
        with self.locked():
            self.compose("stop", "scheduler", timeout=45)
            args = ["--rotate"]
            for project in sorted(set(projects)):
                args += ["--project-id", str(project)]
            result = self.compose("--profile", "operations", "run", "--rm", "-T", "credential-admin", *args)
            self.compose("up", "-d", "--no-deps", "--wait", "--wait-timeout", "150", "scheduler")
            self.event("scheduler-scope", project_count=len(set(projects)))
            return result.stdout


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state", type=Path, default=os.getenv("T44_ACCEPTANCE_STATE"))
    commands = parser.add_subparsers(dest="command", required=True)
    fault = commands.add_parser("fault")
    fault.add_argument("--service", choices=SERVICES, required=True)
    fault.add_argument("--action", choices=["stop", "pause"], required=True)
    fault.add_argument("--lease-seconds", type=int, default=60)
    commands.add_parser("recover")
    commands.add_parser("audit-sql")
    broker = commands.add_parser("broker")
    broker.add_argument("kind", choices=["queues", "connections"])
    account = commands.add_parser("init-user")
    account.add_argument("--username", required=True)
    account.add_argument("--display-name", required=True)
    scope = commands.add_parser("scheduler-scope")
    scope.add_argument("--project-id", type=int, action="append", required=True)
    args = parser.parse_args()
    try:
        controls = Controls(args.state)
        output = None
        if args.command == "fault":
            controls.fault(args.service, args.action, args.lease_seconds)
        elif args.command == "recover":
            controls.recover()
        elif args.command == "audit-sql":
            output = controls.audit(sys.stdin.read())
        elif args.command == "broker":
            output = controls.broker(args.kind)
        elif args.command == "init-user":
            output = controls.account(args.username, args.display_name, sys.stdin.readline().rstrip("\n"))
        else:
            output = controls.scheduler_scope(args.project_id)
        if output:
            sys.stdout.buffer.write(output)
    except Exception:  # noqa: BLE001 -- private inputs and driver messages never enter public console
        print("Acceptance environment control failed; inspect tester-encrypted evidence.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
