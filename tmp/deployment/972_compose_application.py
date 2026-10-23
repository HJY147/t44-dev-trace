"""Real, isolated GitHub-hosted Docker integration driver; never a static pytest case."""

import argparse
import hashlib
import json
import os
import platform
import secrets
import subprocess
import sys
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from deployment import ops  # noqa: E402 -- executable driver uses the repository operational module


class ComposeApplication:
    def __init__(self, folder):
        self.folder = folder
        self.folder.mkdir(parents=True, exist_ok=True)
        self.env_file = ROOT / ".env"
        self.values = None
        self.private = ROOT / ".docker-smoke-private"
        self.private.mkdir(mode=0o700)
        self.secrets = []
        self.leaks = 0
        self.report = {"source_sha": os.getenv("GITHUB_SHA"), "runner": platform.platform(),
                       "scope": "synthetic hosted-Linux Compose integration; not independent acceptance or load",
                       "steps": [], "http": [], "passed": False}
        self.recovery_project = "t44-restore-" + os.environ["GITHUB_RUN_ID"]

    def save(self, label, code, output):
        text = output.decode(errors="replace") if isinstance(output, bytes) else output or ""
        for secret in self.secrets:
            if secret and secret in text:
                self.leaks += 1
                text = text.replace(secret, "[REDACTED-SMOKE-SECRET]")
        (self.folder / f"{label}.log").write_text(text)
        self.report["steps"].append({"name": label, "exit_code": code})
        print(json.dumps({"step": label, "exit_code": code}), flush=True)
        return text

    def host(self, label, command, expected=0):
        result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
        output = self.save(label, result.returncode, result.stdout + result.stderr)
        if result.returncode != expected:
            raise RuntimeError(f"host step failed: {label}")
        return output

    def compose(self, label, *arguments, expected=0, values=None, project=None, data=None):
        try:
            result = ops.compose(self.env_file, values or self.values, *arguments, project=project,
                                 input=data, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            code, output = result.returncode, result.stdout
        except subprocess.CalledProcessError as error:
            code, output = error.returncode, error.stdout
        text = self.save(label, code, output)
        if code != expected:
            raise RuntimeError(f"compose step failed: {label}")
        return text

    @staticmethod
    def object_from_output(text):
        for line in reversed(text.splitlines()):
            try:
                value = json.loads(line)
                if isinstance(value, dict):
                    return value
            except ValueError:
                continue
        raise ValueError("expected an operational JSON result")

    def sql(self, label, statement, *, values=None, project=None):
        return self.compose(label, "exec", "-T", "mysql", "sh", "-c",
                            ops.MYSQL + ' --database="$MYSQL_DATABASE"', values=values, project=project,
                            data=statement.encode()).strip()

    def http(self, method, path, *, body=None, token=None, expected=200):
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = "Bearer " + token
        data = json.dumps(body).encode() if body is not None else None
        request = Request("http://127.0.0.1:18081/api/v1" + path, headers=headers, data=data, method=method)
        try:
            with urlopen(request, timeout=20) as response:
                status, content = response.status, response.read()
        except HTTPError as error:
            status, content = error.code, error.read()
        value = json.loads(content)
        self.report["http"].append({"method": method, "path": path, "status": status,
                                    "request_id": value.get("request_id") or value.get("meta", {}).get("request_id")})
        if status != expected:
            raise RuntimeError(f"HTTP status mismatch: {method} {path} {status}")
        return value

    def admin(self, label, *arguments, data=None, values=None, project=None):
        text = self.compose(label, "--profile", "operations", "run", "--rm", "-T", "admin", *arguments,
                            data=data, values=values, project=project)
        return self.object_from_output(text)

    def snapshot(self, label, *, values=None, project=None):
        names = self.sql(label + "-table-names", "SHOW TABLES;", values=values, project=project).splitlines()
        names = [ops.identifier(name) for name in names]
        statement = "SELECT JSON_OBJECT(" + ",".join(
            f"'{name}',(SELECT COUNT(*) FROM `{name}`)" for name in names) + ");"
        counts = json.loads(self.sql(label + "-counts", statement, values=values, project=project))
        checksum = self.sql(label + "-checksums", "CHECKSUM TABLE " + ",".join(f"`{name}`" for name in names) + " EXTENDED;",
                            values=values, project=project)
        checksums = {}
        for line in checksum.splitlines():
            table, value = line.split("\t")
            if value == "NULL":
                raise ValueError("content checksum is unavailable")
            checksums[table.rsplit(".", 1)[1]] = int(value)
        return {"counts": counts, "checksums": checksums}

    def run(self):
        ops.generate_env(self.env_file)
        self.values = ops.load_env(self.env_file)
        self.values.update(COMPOSE_PROJECT_NAME="t44-smoke-" + os.environ["GITHUB_RUN_ID"],
                           MYSQL_DATABASE="t44_smoke", T44_HTTP_PORT="18081")
        self.env_file.write_text("".join(f"{key}={value}\n" for key, value in self.values.items()))
        self.secrets.extend(self.values[name] for name in ["MYSQL_PASSWORD", "MYSQL_ROOT_PASSWORD", "RABBITMQ_DEFAULT_PASS"])
        self.host("docker-version", ["docker", "version"])
        self.host("compose-version", ["docker", "compose", "version"])
        self.compose("build", "--progress", "plain", "build", "api", "web")
        self.compose("infra", "up", "-d", "--wait", "--wait-timeout", "180", "mysql", "rabbitmq")
        self.compose("migration", "--profile", "operations", "run", "--rm", "-T", "migrate")
        password = secrets.token_urlsafe(24)
        self.secrets.append(password)
        self.report["synthetic_user"] = self.admin(
            "init-user", "init-user", "--username", "synthetic-manager", "--display-name", "Synthetic deployment manager",
            "--password-stdin", data=(password + "\n").encode())
        self.report["seed"] = self.admin("seed", "seed-demo", "--projects", "2", "--tasks", "40",
                                         "--dependencies", "30", "--records", "80")
        projects = json.loads(self.sql("project-scopes", "SELECT JSON_ARRAYAGG(id) FROM projects;"))
        if not projects or any(type(value) is not int for value in projects):
            raise ValueError("real project scopes were not initialized")
        credential_args = [sys.executable, str(ROOT / "deployment/ops.py"), "scheduler-token"]
        for project in sorted(projects):
            credential_args += ["--project-id", str(project)]
        issued = self.object_from_output(self.host("credential-issue", credential_args))
        self.report["service_session"] = issued
        self.compose("application-up", "up", "-d", "--wait", "--wait-timeout", "180", "api", "consumer", "scheduler", "web")
        self.compose("application-ps", "ps", "--format", "json")
        worker_code = """import json
from pathlib import Path
commands={p.parent.name:p.read_bytes().split(b'\\0') for p in Path('/proc').glob('[0-9]*/cmdline')}
parents=[pid for pid,args in commands.items() if args[1:4]==[b'-m',b'uvicorn',b't44.api:app']]
workers=0
for pid,args in commands.items():
 if b'spawn_main' not in b' '.join(args): continue
 status=Path('/proc',pid,'status').read_text()
 parent=next(line.split(':')[1].strip() for line in status.splitlines() if line.startswith('PPid:'))
 workers+=parent in parents
print(json.dumps({'api_parents':len(parents),'workers':workers}))
raise SystemExit(0 if len(parents)==1 and workers==4 else 1)
"""
        self.report["api_processes"] = self.object_from_output(self.compose("four-api-workers", "exec", "-T", "api", "python", "-c", worker_code))
        self.http("GET", "/projects", expected=401)
        login = self.http("POST", "/auth/login", body={"username": "synthetic-manager", "password": password})
        token = login["data"]["access_token"]
        self.secrets.append(token)
        listed = self.http("GET", "/projects", token=token)
        if len(listed["data"]["items"]) != 2:
            raise ValueError("seeded project membership is not visible")
        tasks = self.http("GET", f"/projects/{projects[0]}/tasks", token=token)["data"]["items"]
        task = self.http("GET", f"/projects/{projects[0]}/tasks/{tasks[0]['id']}", token=token)["data"]
        self.report["observed_task_id"] = task["id"]
        html_hashes = {}
        for path in ["/", f"/projects/{projects[0]}/tasks"]:
            with urlopen("http://127.0.0.1:18081" + path, timeout=15) as response:
                page = response.read()
                if response.status != 200 or b'<div id="app">' not in page:
                    raise ValueError("frontend history fallback is unavailable")
                html_hashes[path] = hashlib.sha256(page).hexdigest()
        if len(set(html_hashes.values())) != 1:
            raise ValueError("history route does not return the built SPA entry")
        self.report["frontend_routes"] = html_hashes
        for label, count in [("api-one-mib", 1024 * 1024 + 100), ("proxy-two-mib", 2 * 1024 * 1024 + 100)]:
            value = self.http("POST", "/auth/login", body={"padding": "x" * count}, expected=413)
            if value["code"] != "PAYLOAD_TOO_LARGE" or (label == "proxy-two-mib" and value["audit_id"] is not None):
                raise ValueError("request size rejection does not match the JSON contract")
            self.report[label] = {"code": value["code"], "audit_id": value["audit_id"]}
        permission_code = """import errno,json,os,stat
from pathlib import Path
p=Path('/run/t44-secrets/scheduler-token.json')
mode=stat.S_IMODE(p.stat().st_mode)
readonly=False
try:
 fd=os.open(p.parent/'readonly-probe',os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
except OSError as e:
 readonly=e.errno in (errno.EROFS,errno.EACCES)
else:
 os.close(fd); (p.parent/'readonly-probe').unlink()
print(json.dumps({'mode':oct(mode),'uid':p.stat().st_uid,'readonly':readonly}))
raise SystemExit(0 if mode==0o600 and p.stat().st_uid==os.getuid() and readonly else 1)
"""
        self.report["credential_permissions"] = self.object_from_output(self.compose("credential-permissions", "exec", "-T", "scheduler", "python", "-c", permission_code))
        lock_code = """import fcntl,json,os
path=os.environ['T44_SCHEDULER_LOCK_FILE']
fd=os.open(path,os.O_RDWR)
held=False
try:
 fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
except BlockingIOError:
 held=True
print(json.dumps({'shared_lock_held':held,'inode':os.fstat(fd).st_ino}))
os.close(fd)
raise SystemExit(0 if held else 1)
"""
        self.report["shared_flock"] = self.object_from_output(self.compose("shared-flock-probe", "run", "--rm", "-T", "scheduler", "python", "-c", lock_code))
        self.compose("shared-flock-rejects-second-scanner", "run", "--rm", "-T", "scheduler", "python", "-m", "t44.scheduling", "--once", expected=1)
        rotated = self.object_from_output(self.host("credential-rotate", [*credential_args, "--rotate"]))
        if rotated["session_id"] == issued["session_id"] or not rotated["previous_session_revoked"]:
            raise ValueError("service credential did not rotate/revoke")
        self.report["rotated_service_session"] = rotated
        progress = self.sql("scheduler-progress", "SELECT JSON_OBJECT('completed',COUNT(*),'created',COALESCE(SUM(created_count),0)) FROM scan_runs WHERE status=2 AND error_code IS NULL;")
        self.report["scheduler_progress"] = json.loads(progress)
        if self.report["scheduler_progress"]["completed"] < 1:
            raise ValueError("no durable successful scan")
        self.compose("quiesce-writers", "stop", "scheduler", "consumer", "api", "web")
        before = self.snapshot("source")
        dump = self.private / "backup.sql"
        self.host("backup", [sys.executable, str(ROOT / "deployment/ops.py"), "backup", "--database", "t44_smoke", "--output", str(dump)])
        self.report["backup_manifest"] = json.loads(dump.with_name(dump.name + ".manifest.json").read_text())
        self.host("isolated-restore", [sys.executable, str(ROOT / "deployment/ops.py"), "restore", "--database", "t44_recovered", "--project", self.recovery_project,
                                      "--confirm-target", f"{self.recovery_project}/t44_recovered", "--input", str(dump), "--execute"])
        recovered_values = {**self.values, "MYSQL_DATABASE": "t44_recovered"}
        after = self.snapshot("recovered", values=recovered_values, project=self.recovery_project)
        if before != after:
            raise ValueError("isolated restoration differs in table counts/content checksums")
        self.report["restoration"] = {"source": before, "recovered": after, "matched": True}
        self.report["restored_schema"] = self.admin("restored-schema", "migrate", "--database", "t44_recovered", values=recovered_values, project=self.recovery_project)
        if not self.report["restored_schema"]["passed"] or not self.report["restored_schema"]["already_applied"]:
            raise ValueError("restored version/fields/constraints are not verified")
        self.compose("restart-primary", "up", "-d", "--wait", "--wait-timeout", "180", "api", "consumer", "scheduler", "web")
        self.http("GET", f"/projects/{projects[0]}/tasks/{tasks[0]['id']}", token=token)
        self.report["passed"] = True

    def finish(self):
        if self.values:
            for label, project in [("primary", None), ("recovery", self.recovery_project)]:
                try:
                    self.compose(label + "-logs", "logs", "--no-color", project=project)
                    self.compose(label + "-stop", "stop", project=project)
                except (OSError, RuntimeError):
                    self.report["cleanup_warning"] = True
        self.report["redacted_secret_occurrences"] = self.leaks
        if self.leaks:
            self.report["passed"] = False
            self.report["error"] = "sensitive runtime output detected and redacted"
        (self.folder / "result.json").write_text(json.dumps(self.report, indent=2) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report-dir", type=Path, default=ROOT / "reports/docker-integration")
    args = parser.parse_args()
    if os.getenv("GITHUB_ACTIONS") != "true" or platform.system() != "Linux":
        print("Refusing: this integration driver requires isolated GitHub-hosted Linux.", file=sys.stderr)
        return 1
    application = ComposeApplication(args.report_dir)
    try:
        application.run()
    except Exception as error:  # noqa: BLE001 -- credential-safe failure; raw safe step logs are separate
        application.report["error"] = type(error).__name__
        application.report["passed"] = False
    finally:
        application.finish()
    return 0 if application.report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
