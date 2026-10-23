"""Provision a neutral hosted-Linux environment; execute only a separately frozen harness."""

import argparse
import gzip
import hashlib
import json
import os
import platform
import re
import secrets
import signal
import stat
import subprocess
import sys
import tarfile
import time
from pathlib import Path, PurePosixPath
from urllib.request import Request, urlopen
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parent))
from control import SERVICES, Controls, write_private  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from deployment import ops  # noqa: E402

OUTPUT_NAMES = ("report.md", "results.json", "events.jsonl", "trace.log")
SHA = re.compile(r"[0-9a-f]{40}\Z")


def harness_path(value):
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or len(path.parts) < 3 or path.parts[:2] != ("tmp", "independent"):
        raise ValueError("harness paths must stay under tmp/independent")
    if not re.fullmatch(r"[A-Za-z0-9_./-]+", value):
        raise ValueError("invalid harness path")
    return value


def validate_request(value):
    allowed = {"version", "mode", "product_source_sha", "harness_ref", "harness_path",
               "recipient_certificate_path", "harness_timeout_seconds"}
    if set(value) - allowed or value.get("version") != 1 or value.get("mode") not in ("environment-check", "harness"):
        raise ValueError("unsupported acceptance request")
    if not SHA.fullmatch(value.get("product_source_sha", "")):
        raise ValueError("exact product commit required")
    if value["mode"] == "harness":
        if not SHA.fullmatch(value.get("harness_ref", "")):
            raise ValueError("exact separately frozen harness commit required")
        for field in ("harness_path", "recipient_certificate_path"):
            harness_path(value[field])
        if not value["harness_path"].endswith(".py") or not value["recipient_certificate_path"].endswith(".pem"):
            raise ValueError("Python entry and PEM recipient certificate required")
    elif any(value.get(field) for field in ("harness_ref", "harness_path", "recipient_certificate_path")):
        raise ValueError("environment-check must not select an independent harness")
    timeout = value.get("harness_timeout_seconds", 900)
    if type(timeout) is not int or not 60 <= timeout <= 1200:
        raise ValueError("bounded harness timeout required")
    return {**value, "harness_timeout_seconds": timeout}


def frozen_file(root, relative):
    candidate = root / harness_path(relative)
    if candidate.is_symlink() or root.resolve() not in candidate.resolve().parents or not candidate.is_file():
        raise ValueError("frozen regular harness file required")
    return candidate


def archive_members(folder):
    selected = []
    for name in ("stdout.log", "stderr.log", *OUTPUT_NAMES):
        path = folder / name
        if path.is_symlink():
            raise ValueError("output links cannot be archived")
        if path.exists():
            if path.is_symlink() or not stat.S_ISREG(path.stat().st_mode) or path.stat().st_size > 20 * 1024 * 1024:
                raise ValueError("only bounded regular output files can be archived")
            selected.append(path)
    if sum(path.stat().st_size for path in selected) > 100 * 1024 * 1024:
        raise ValueError("tester archive exceeds limit")
    return selected


def encrypt_archive(folder, certificate, destination):
    plain = folder.parent / "tester-output.tar.gz"
    try:
        with tarfile.open(plain, "w:gz", dereference=False) as archive:
            for path in archive_members(folder):
                archive.add(path, arcname=path.name, recursive=False)
        result = subprocess.run(
            ["openssl", "cms", "-encrypt", "-binary", "-aes-256-gcm", "-in", str(plain),
             "-outform", "DER", "-out", str(destination), "-recip", str(certificate),
             "-keyopt", "rsa_padding_mode:oaep", "-keyopt", "rsa_oaep_md:sha256"],
            capture_output=True, check=False, timeout=30,
        )
        if result.returncode or not destination.is_file():
            destination.unlink(missing_ok=True)
            raise RuntimeError("tester archive encryption failed")
        return {"format": "OpenSSL CMS AuthEnvelopedData AES-256-GCM/RSA-OAEP-SHA256",
                "ciphertext_sha256": hashlib.sha256(destination.read_bytes()).hexdigest(),
                "ciphertext_bytes": destination.stat().st_size,
                "recipient_certificate_sha256": hashlib.sha256(certificate.read_bytes()).hexdigest(),
                "plaintext_files": [path.name for path in archive_members(folder)],
                "retention_days": 14,
                "access": "Ciphertext is downloadable; only the tester-held private key decrypts it. "
                          "Root/developers must not download or read unpublished tester plaintext."}
    except Exception:
        destination.unlink(missing_ok=True)
        raise
    finally:
        plain.unlink(missing_ok=True)


class Environment:
    def __init__(self, request, product, harness, runtime, public):
        self.request, self.product, self.harness = request, product.resolve(), harness.resolve()
        self.runtime, self.public = runtime.resolve(), public.resolve()
        self.runtime.mkdir(mode=0o700, parents=True, exist_ok=False)
        self.public.mkdir(parents=True, exist_ok=True)
        self.output = self.runtime / "tester-output"
        self.output.mkdir(mode=0o700)
        self.secrets = []
        self.controls = None
        self.certificate = None
        self.report = {"schema_version": 1, "mode": request["mode"], "product_source_sha": request["product_source_sha"],
                       "harness_ref": request.get("harness_ref"), "harness_path": request.get("harness_path"),
                       "workflow_sha": os.environ.get("GITHUB_SHA"), "steps": [], "environment_ready": False,
                       "harness_started": False, "harness_exit_code": None, "recovery_completed": False,
                       "meaning": "Environment capability/execution metadata; not an independent acceptance conclusion."}

    def mask(self, secret):
        self.secrets.append(secret)
        print("::add-mask::" + secret, flush=True)

    def step(self, name, operation):
        print(json.dumps({"environment_step": name}), flush=True)
        try:
            value = operation()
        except Exception:
            self.report["steps"].append({"name": name, "completed": False})
            raise
        self.report["steps"].append({"name": name, "completed": True})
        return value

    @staticmethod
    def result_json(result):
        for line in reversed(result.stdout.decode().splitlines()):
            try:
                value = json.loads(line)
                if isinstance(value, dict):
                    return value
            except ValueError:
                pass
        raise RuntimeError("expected environment CLI metadata")

    def http(self, path, body, token=None):
        headers = {"Content-Type": "application/json", "Idempotency-Key": str(uuid4())}
        if token:
            headers["Authorization"] = "Bearer " + token
        with urlopen(Request("http://127.0.0.1:18082/api/v1" + path, data=json.dumps(body).encode(),
                             headers=headers), timeout=15) as response:
            return json.load(response)["data"]

    def prepare_recipient(self):
        if self.request["mode"] == "harness":
            self.certificate = frozen_file(self.harness, self.request["recipient_certificate_path"])
            frozen_file(self.harness, self.request["harness_path"])
            if b"PRIVATE KEY" in self.certificate.read_bytes():
                raise ValueError("only a recipient certificate may be committed")
        else:
            self.certificate = self.runtime / "environment-check-recipient.pem"
            subprocess.run(["openssl", "req", "-x509", "-newkey", "rsa:3072", "-nodes", "-days", "1",
                            "-subj", "/CN=Ephemeral environment capability check/",
                            "-keyout", str(self.runtime / "environment-check-key.pem"),
                            "-out", str(self.certificate)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                           check=True, timeout=30)
        subprocess.run(["openssl", "x509", "-in", str(self.certificate), "-noout", "-checkend", "3600"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

    def provision(self):
        current = subprocess.check_output(["git", "-C", str(self.product), "rev-parse", "HEAD"], text=True).strip()
        if current != self.request["product_source_sha"]:
            raise ValueError("product checkout does not match requested SHA")
        if self.request["mode"] == "harness":
            current = subprocess.check_output(["git", "-C", str(self.harness), "rev-parse", "HEAD"], text=True).strip()
            if current != self.request["harness_ref"]:
                raise ValueError("harness checkout does not match frozen SHA")
        self.prepare_recipient()
        env_file = self.runtime / ".env"
        ops.generate_env(env_file)
        values = ops.load_env(env_file)
        values.update(COMPOSE_PROJECT_NAME="t44-acceptance-" + os.environ["GITHUB_RUN_ID"],
                      MYSQL_DATABASE="t44_acceptance", T44_HTTP_PORT="18082", T44_IMAGE_TAG="acceptance")
        env_file.write_text("".join(f"{key}={value}\n" for key, value in values.items()))
        for field in ("MYSQL_PASSWORD", "MYSQL_ROOT_PASSWORD", "RABBITMQ_DEFAULT_PASS"):
            self.mask(values[field])
        override = self.runtime / "compose.acceptance.yaml"
        override.write_text('services:\n  mysql:\n    ports: ["127.0.0.1:13306:3306"]\n'
                            '  rabbitmq:\n    ports: ["127.0.0.1:15673:5672"]\n')
        state = self.runtime / "state.json"
        write_private(state, {"product_root": str(self.product), "env_file": str(env_file),
                              "override_file": str(override), "public_dir": str(self.public)})
        write_private(self.runtime / "fault-leases.json", {})
        self.controls = Controls(state)
        c = self.controls
        self.step("image-build", lambda: c.compose("build", "api", "web", timeout=600))
        self.step("mysql-rabbitmq", lambda: c.compose("up", "-d", "--wait", "--wait-timeout", "180", "mysql", "rabbitmq"))
        self.step("explicit-migration", lambda: c.compose("--profile", "operations", "run", "--rm", "-T", "migrate"))
        password = secrets.token_urlsafe(32)
        self.mask(password)
        user = self.step("bootstrap-account", lambda: self.result_json(c.compose(
            "--profile", "operations", "run", "--rm", "-T", "admin", "init-user", "--username", "acceptance-manager",
            "--display-name", "Synthetic acceptance administrator", "--password-stdin", data=(password + "\n").encode())))
        self.step("http-entry", lambda: c.compose("up", "-d", "--wait", "--wait-timeout", "150", "api", "web"))
        login = self.http("/auth/login", {"username": "acceptance-manager", "password": password})
        self.mask(login["access_token"])
        project = self.step("bootstrap-project", lambda: self.http("/projects", {"name": "Synthetic acceptance bootstrap"},
                                                                   login["access_token"]))
        self.step("private-scanner-credential", lambda: c.compose(
            "--profile", "operations", "run", "--rm", "-T", "credential-admin", "--project-id", str(project["id"])))
        self.step("independent-workers", lambda: c.compose("up", "-d", "--wait", "--wait-timeout", "150",
                                                           "api", "consumer", "scheduler", "web"))
        audit_password = secrets.token_hex(32)
        self.mask(audit_password)
        sql = (f"CREATE USER 't44_audit'@'%' IDENTIFIED BY '{audit_password}';"
               f"GRANT SELECT ON `{values['MYSQL_DATABASE']}`.* TO 't44_audit'@'%';\n")
        self.step("read-only-audit-principal", lambda: c.compose("exec", "-T", "mysql", "sh", "-c", ops.MYSQL,
                                                                data=sql.encode()))
        write_private(self.runtime / "audit.json", {"password": audit_password})
        write_private(self.runtime / "manager.json", {"username": "acceptance-manager", "password": password,
                                                      "access_token": login["access_token"], "user_id": user["user_id"]})
        context = {
            "version": 1, "product_source_sha": self.request["product_source_sha"],
            "api_base_url": "http://127.0.0.1:18082/api/v1", "web_base_url": "http://127.0.0.1:18082",
            "bootstrap_project_id": project["id"], "bootstrap_data": "one synthetic manager/project; no tasks or test cases",
            "manager_credentials_file": str(self.runtime / "manager.json"),
            "readonly_database_url": f"mysql+pymysql://t44_audit:{audit_password}@127.0.0.1:13306/t44_acceptance",
            "amqp_url": f"amqp://{values['RABBITMQ_DEFAULT_USER']}:{values['RABBITMQ_DEFAULT_PASS']}@127.0.0.1:15673/t44",
            "python": sys.executable, "control_cli": str(Path(__file__).with_name("control.py")),
            "control_state": str(state), "harness_output_directory": str(self.output),
            "archive_output_whitelist": list(OUTPUT_NAMES), "per_file_limit_bytes": 20 * 1024 * 1024,
            "archive": {"artifact": "acceptance-" + os.environ["GITHUB_RUN_ID"], "file": "tester-output.cms",
                        "retention_days": 14, "plaintext": "runner temporary only; destroyed after job",
                        "retrieval": "tester downloads encrypted artifact within14days, decrypts with local private key, "
                                     "reviews/redacts then explicitly publishes; root/dev do not read unpublished plaintext"},
            "faults": {"services": list(SERVICES), "actions": ["stop", "pause"], "max_lease_seconds": 120,
                       "recovery": "explicit recover, automatic expired lease, and finally recovery before stop"},
            "isolation": "disposable hosted runner/project, not an OS sandbox for a malicious harness",
        }
        write_private(self.runtime / "context.json", context)
        self.report["environment_ready"] = True

    def environment_check(self):
        # Capability checks only: no business assertions or independent acceptance cases.
        self.step("readonly-select-connectivity", lambda: self.controls.audit("SELECT 1"))
        self.step("rabbitmq-audit-connectivity", lambda: self.controls.broker("queues"))
        self.step("loopback-database-amqp-clients", self.client_connections)
        self.step("reversible-control", lambda: self.controls.fault("rabbitmq", "stop", 30))
        self.step("control-recovery", self.controls.recover)
        self.step("recovered-loopback-clients", self.client_connections)
        (self.output / "stdout.log").write_text("Synthetic environment archive transport check.\n")
        self.report["environment_capability_check_completed"] = True

    def client_connections(self):
        import pika
        import pymysql

        context = json.loads((self.runtime / "context.json").read_text())
        audit = json.loads((self.runtime / "audit.json").read_text())
        with pymysql.connect(host="127.0.0.1", port=13306, user="t44_audit", password=audit["password"],
                             database="t44_acceptance", connect_timeout=5, read_timeout=5) as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                if cursor.fetchone() != (1,):
                    raise RuntimeError("read-only loopback client is unavailable")
        parameters = pika.URLParameters(context["amqp_url"])
        parameters.socket_timeout, parameters.blocked_connection_timeout = 5, 5
        connection = pika.BlockingConnection(parameters)
        connection.close()

    def execute_harness(self):
        entry = frozen_file(self.harness, self.request["harness_path"])
        env = {key: value for key, value in os.environ.items()
               if key not in {"GITHUB_TOKEN", "GH_TOKEN", "ACTIONS_RUNTIME_TOKEN"}}
        env.update(T44_ACCEPTANCE_CONTEXT=str(self.runtime / "context.json"),
                   T44_ACCEPTANCE_STATE=str(self.runtime / "state.json"), T44_HARNESS_OUTPUT_DIR=str(self.output))
        self.report["harness_started"] = True
        started = time.monotonic()
        with (self.output / "stdout.log").open("wb") as stdout, (self.output / "stderr.log").open("wb") as stderr:
            child = subprocess.Popen([sys.executable, str(entry)], cwd=self.harness, env=env,
                                     stdout=stdout, stderr=stderr, start_new_session=True)
            try:
                while child.poll() is None:
                    if time.monotonic() - started > self.request["harness_timeout_seconds"]:
                        raise TimeoutError("frozen harness timeout")
                    self.controls.recover(expired_only=True)
                    time.sleep(2)
                self.report["harness_exit_code"] = child.returncode
            finally:
                if child.poll() is None:
                    os.killpg(child.pid, signal.SIGTERM)
                    try:
                        child.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        os.killpg(child.pid, signal.SIGKILL)
                        child.wait(timeout=5)

    def finish(self):
        if self.controls:
            try:
                self.controls.recover()
                self.report["recovery_completed"] = True
            except Exception:
                self.report["recovery_error"] = "ENVIRONMENT_RECOVERY_FAILED"
            try:
                self.controls.compose("stop", timeout=60)
            except Exception:
                self.report["stop_error"] = "ENVIRONMENT_STOP_FAILED"
        if self.certificate:
            try:
                metadata = encrypt_archive(self.output, self.certificate, self.public / "tester-output.cms")
                if self.request["mode"] == "environment-check":
                    recovered = self.runtime / "transport-check.tar.gz"
                    subprocess.run(["openssl", "cms", "-decrypt", "-binary", "-inform", "DER", "-recip",
                                    str(self.certificate), "-inkey", str(self.runtime / "environment-check-key.pem"),
                                    "-in", str(self.public / "tester-output.cms"), "-out", str(recovered)],
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
                    with tarfile.open(recovered, "r:gz") as archive:
                        expected = (self.output / "stdout.log").read_bytes()
                        if archive.extractfile("stdout.log").read() != expected:
                            raise RuntimeError("archive transport differs")
                    metadata["synthetic_roundtrip_verified"] = True
                (self.public / "encrypted-archive.json").write_text(json.dumps(metadata, indent=2) + "\n")
            except Exception:
                self.report["archive_error"] = "ENCRYPTED_ARCHIVE_FAILED_NO_PLAINTEXT_PUBLISHED"
        if self.request["mode"] == "environment-check":
            path = self.runtime / "environment-commands.log"
            if path.exists():
                content = path.read_text(errors="replace")
                for secret in self.secrets:
                    content = content.replace(secret, "[REDACTED-EPHEMERAL-CREDENTIAL]")
                (self.public / "environment-diagnostics.log.gz").write_bytes(gzip.compress(content.encode(), mtime=0))
        (self.public / "execution.json").write_text(json.dumps(self.report, indent=2) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    request = sub.add_parser("request")
    request.add_argument("--file", type=Path)
    request.add_argument("--normalized", type=Path, required=True)
    run = sub.add_parser("run")
    run.add_argument("--request", type=Path, required=True)
    run.add_argument("--product", type=Path, required=True)
    run.add_argument("--harness", type=Path, required=True)
    run.add_argument("--runtime", type=Path, required=True)
    run.add_argument("--public", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "request":
        raw = json.loads(args.file.read_text()) if args.file else json.loads(os.environ["ACCEPTANCE_INPUT_JSON"])
        if not args.file:
            raw["version"] = 1
            raw["harness_timeout_seconds"] = int(raw.get("harness_timeout_seconds") or "900")
        value = validate_request(raw)
        write_private(args.normalized, value)
        with Path(os.environ["GITHUB_OUTPUT"]).open("a") as stream:
            stream.write("product_source_sha=" + value["product_source_sha"] + "\n")
            stream.write("harness_ref=" + value.get("harness_ref", "") + "\n")
            stream.write("has_harness=" + str(value["mode"] == "harness").lower() + "\n")
        return 0
    if os.getenv("GITHUB_ACTIONS") != "true" or platform.system() != "Linux":
        raise SystemExit("Requires a disposable GitHub-hosted Linux runner.")
    os.umask(0o077)
    environment = Environment(validate_request(json.loads(args.request.read_text())), args.product, args.harness,
                              args.runtime, args.public)
    def interrupted(*_):
        raise InterruptedError("runner termination requested")

    previous_signal = signal.signal(signal.SIGTERM, interrupted)
    try:
        environment.provision()
        if environment.request["mode"] == "environment-check":
            environment.environment_check()
        else:
            environment.execute_harness()
    except Exception:  # noqa: BLE001 -- raw exceptions may contain ephemeral credentials or harness details
        environment.report["execution_error"] = "ENVIRONMENT_OR_HARNESS_EXECUTION_FAILED"
    finally:
        environment.finish()
        signal.signal(signal.SIGTERM, previous_signal)
    report = environment.report
    completed = report.get("environment_capability_check_completed") if report["mode"] == "environment-check" else (
        report["harness_started"] and report["harness_exit_code"] == 0)
    return 0 if completed and report["recovery_completed"] and not any(
        key in report for key in ("execution_error", "archive_error", "recovery_error", "stop_error")) else 1


if __name__ == "__main__":
    raise SystemExit(main())
