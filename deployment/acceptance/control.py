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
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from deployment import ops  # noqa: E402

SERVICES = ("mysql", "rabbitmq", "api", "consumer", "scheduler", "web")
SERVICE_ISSUE_SCRIPT = """import json,os,subprocess,sys
from pathlib import Path
from sqlalchemy import create_engine,text
projects=sorted(set(int(value) for value in sys.argv[1:]))
path=Path('/tmp/acceptance-harness-service.json')
command=[sys.executable,'-m','t44.cli','service-token','--name','acceptance-harness','--token-file',str(path)]
for project in projects: command+=['--project-id',str(project)]
result=subprocess.run(command,capture_output=True,check=False)
if result.returncode: raise SystemExit(1)
credential=json.loads(path.read_text()); path.unlink()
engine=create_engine(os.environ['DATABASE_URL'])
with engine.connect() as connection:
 row=connection.execute(text('SELECT actor_kind,project_ids,scopes,TIMESTAMPDIFF(SECOND,UTC_TIMESTAMP(6),expires_at) remaining FROM auth_sessions WHERE id=:id AND revoked_at IS NULL'),{'id':credential['session_id']}).mappings().one()
 actual_projects=json.loads(row['project_ids']) if isinstance(row['project_ids'],str) else row['project_ids']
 scopes=json.loads(row['scopes']) if isinstance(row['scopes'],str) else row['scopes']
 if row['actor_kind']!=2 or sorted(actual_projects)!=projects or scopes!=['escalation:write'] or not 0<row['remaining']<=int(os.environ['T44_SESSION_TTL_SECONDS']): raise SystemExit(1)
engine.dispose()
print(json.dumps({**credential,'project_ids':projects,'scopes':scopes,'ttl_seconds':int(os.environ['T44_SESSION_TTL_SECONDS'])}))
"""


def validate_service_request(projects, ttl, output_name):
    if not projects or any(type(value) is not int or not 1 <= value <= 4294967295 for value in projects):
        raise ValueError("explicit project scopes required")
    if type(ttl) is not int or not 60 <= ttl <= 900:
        raise ValueError("service credential TTL must be 60..900 seconds")
    if output_name is not None and not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,58}\.json", output_name):
        raise ValueError("controlled private JSON filename required")


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


def recovery_receipt():
    return {"schema_version": 1, "recovery_id": uuid4().hex, "recovery_completed": False,
            "started_at": datetime.now(UTC).isoformat(), "finished_at": None,
            "requested_services": list(SERVICES), "restored_services": [], "steps": [], "error": None}


class RecoveryFailure(RuntimeError):
    def __init__(self, receipt):
        super().__init__("RECOVERY_FAILED")
        self.receipt = receipt


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
        receipt = recovery_receipt()
        phase = "read-recovery-state"

        def command(name, *arguments, timeout=210, restored=()):
            nonlocal phase
            phase = name
            step = {"name": name, "started_at": datetime.now(UTC).isoformat(), "exit_code": None}
            receipt["steps"].append(step)
            result = self.compose(*arguments, check=False, timeout=timeout)
            step.update(exit_code=result.returncode, finished_at=datetime.now(UTC).isoformat())
            if result.returncode:
                raise RuntimeError("RECOVERY_COMMAND_FAILED")
            receipt["restored_services"].extend(restored)
            return result

        try:
            with self.locked():
                leases = private_json(self.runtime / "fault-leases.json")
                if expired_only and not any(deadline <= time.time() for deadline in leases.values()):
                    return None
                paused = command("inspect-paused", "ps", "--all", "--services", "--status", "paused", *SERVICES,
                                 timeout=30).stdout.decode().split()
                if any(service not in SERVICES for service in paused):
                    raise ValueError("RECOVERY_SCOPE_INVALID")
                receipt["paused_services"] = sorted(set(paused))
                if paused:
                    command("unpause", "unpause", *sorted(set(paused)), timeout=30)
                    deadline = time.monotonic() + 60
                    while True:
                        state = command("unpaused-health", "ps", "--all", "--format", "json", *sorted(set(paused)),
                                        timeout=30).stdout.decode()
                        try:
                            decoded = json.loads(state)
                            rows = decoded if isinstance(decoded, list) else [decoded]
                        except json.JSONDecodeError:
                            rows = [json.loads(line) for line in state.splitlines() if line.strip()]
                        observed = []
                        for row in rows:
                            if row.get("Service") not in paused:
                                continue
                            status, health = row.get("State", ""), row.get("Health", "")
                            observed.append({"service": row["Service"],
                                             "state": status if status in {"running", "paused", "created", "exited",
                                                                           "restarting", "dead", "removing"} else "unknown",
                                             "health": health if health in {"healthy", "unhealthy", "starting", ""}
                                             else "unknown"})
                        receipt["steps"][-1]["observed_health"] = observed
                        if ({row["service"] for row in observed} == set(paused)
                                and all(row["state"] == "running" and row["health"] == "healthy" for row in observed)):
                            break
                        if time.monotonic() >= deadline:
                            phase = "unpaused-health-timeout"
                            raise RuntimeError("RECOVERY_READINESS_TIMEOUT")
                        time.sleep(1)
                else:
                    receipt["steps"].append({"name": "unpause", "needed": False, "exit_code": None})
                command("infrastructure-ready", "up", "-d", "--no-deps", "--wait", "--wait-timeout", "150",
                        "mysql", "rabbitmq", restored=("mysql", "rabbitmq"))
                command("application-ready", "up", "-d", "--no-deps", "--wait", "--wait-timeout", "150",
                        "api", "consumer", "scheduler", "web", restored=("api", "consumer", "scheduler", "web"))
                phase = "clear-fault-leases"
                write_private(self.runtime / "fault-leases.json", {})
                receipt.update(recovery_completed=True, finished_at=datetime.now(UTC).isoformat())
                phase = "record-recovery"
                self.event("lease-recovery" if expired_only else "recovery", recovery_receipt=receipt)
                return receipt
        except Exception:
            receipt.update(recovery_completed=False, finished_at=datetime.now(UTC).isoformat(),
                           error="RECOVERY_FAILED", failed_step=phase)
            try:
                self.event("lease-recovery" if expired_only else "recovery", code=1, recovery_receipt=receipt)
            except OSError:
                pass  # stdout still carries the redacted false receipt if the event file is unavailable.
            raise RecoveryFailure(receipt) from None

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

    def service_credential(self, projects, ttl=300, output_name=None):
        validate_service_request(projects, ttl, output_name)
        projects = sorted(set(projects))
        descriptor, path, created, completed = None, None, False, False
        try:
            if output_name:
                directory = self.runtime / "tester-secrets"
                directory.mkdir(mode=0o700, exist_ok=True)
                if directory.is_symlink() or directory.stat().st_uid != os.getuid() or directory.stat().st_mode & 0o077:
                    raise ValueError("private credential directory required")
                path = directory / output_name
                descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o600)
                created = True
            # Bypass compose()'s raw environment log: this stdout contains an actual bearer, never a stored hash.
            result = ops.compose(Path(self.state["env_file"]), self.values,
                                 "--file", self.state["override_file"], "--profile", "operations", "run", "--rm", "-T",
                                 "-e", f"T44_SESSION_TTL_SECONDS={ttl}", "--entrypoint", "python", "admin",
                                 "-c", SERVICE_ISSUE_SCRIPT, *map(str, projects),
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=45)
            credential = json.loads(result.stdout)
            if (credential["project_ids"] != projects or credential["scopes"] != ["escalation:write"]
                    or credential["ttl_seconds"] != ttl or not 32 <= len(credential["access_token"]) <= 512):
                raise ValueError("issued service metadata does not match the explicit request")
            metadata = {key: value for key, value in credential.items() if key != "access_token"}
            if descriptor is not None:
                with os.fdopen(descriptor, "w") as stream:
                    descriptor = None
                    json.dump(credential, stream)
                    stream.write("\n")
                    stream.flush()
                    os.fsync(stream.fileno())
                metadata["credential_file"] = str(path)
            self.event("service-credential", session_id=credential["session_id"], expires_at=credential["expires_at"],
                       project_count=len(projects), ttl_seconds=ttl)
            completed = True
            return metadata if output_name else credential
        except Exception as error:
            self.event("service-credential-failed", code=getattr(error, "returncode", 1),
                       exception_type=type(error).__name__, project_count=len(projects))
            raise
        finally:
            if descriptor is not None:
                os.close(descriptor)
            if path is not None and created and not completed:
                path.unlink(missing_ok=True)


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
    service = commands.add_parser("service-credential")
    service.add_argument("--project-id", type=int, action="append", required=True)
    service.add_argument("--ttl-seconds", type=int, default=300)
    service.add_argument("--output-name")
    args = parser.parse_args()
    try:
        controls = Controls(args.state)
        output = None
        if args.command == "fault":
            controls.fault(args.service, args.action, args.lease_seconds)
        elif args.command == "recover":
            output = (json.dumps(controls.recover()) + "\n").encode()
        elif args.command == "audit-sql":
            output = controls.audit(sys.stdin.read())
        elif args.command == "broker":
            output = controls.broker(args.kind)
        elif args.command == "init-user":
            output = controls.account(args.username, args.display_name, sys.stdin.readline().rstrip("\n"))
        elif args.command == "scheduler-scope":
            output = controls.scheduler_scope(args.project_id)
        else:
            output = (json.dumps(controls.service_credential(args.project_id, args.ttl_seconds, args.output_name))
                      + "\n").encode()
        if output:
            sys.stdout.buffer.write(output)
    except RecoveryFailure as error:
        print(json.dumps(error.receipt))
        return 1
    except Exception:  # noqa: BLE001 -- private inputs and driver messages never enter public console
        if args.command == "recover":
            receipt = recovery_receipt()
            receipt.update(finished_at=datetime.now(UTC).isoformat(), error="RECOVERY_CONTROL_UNAVAILABLE")
            print(json.dumps(receipt))
            return 1
        print("Acceptance environment control failed; inspect tester-encrypted evidence.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
