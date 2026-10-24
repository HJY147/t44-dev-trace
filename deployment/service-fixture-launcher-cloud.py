"""Root-reviewed one-shot cohort launcher. No scheduler mount, rotate, seed or retry."""

import hashlib
import json
import os
import re
import runpy
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

SOURCE = "0dfb55c2191200d947c5423fd9ee74bb0812cc5a"
DELIVERY = Path("/run/t44-delivery")
ROOT = Path("/opt/t44-c-0dfb55c")
RUNTIME = DELIVERY / "tls-C"
INPUTS = DELIVERY / "fixture-inputs"
OUTPUT = DELIVERY / "cohort-secrets"
BASE = DELIVERY / "fixture-launcher-cloud.py"
BASE_SHA = "39f210450c491c8b6407185cf190d333abb80547de64bcd9de3022951fd9cf11"
WORKER_SHA = "d1cd66c13b90874a8519ccc6c307bd41678671232f212632839e3391227dc5b0"
TLS_HELPER = DELIVERY / "tls-delivery-extended.py"
TLS_SHA = "ea1b5873efb359e2e4e4adb8f020bfeab3da8f20e7661ae7bb7a5d883ac121d9"
END = datetime(2026, 10, 24, 10, 28, tzinfo=UTC).timestamp()


def command(values):
    if values["MYSQL_DATABASE"] != "t44" or values["T44_DOCKER_CONTEXT"] != "default":
        raise ValueError("target_rejected")
    argv = [
        "docker",
        "--context",
        "default",
        "compose",
        "--project-name",
        values["COMPOSE_PROJECT_NAME"],
        "--env-file",
        str(ROOT / ".env"),
        "-f",
        str(ROOT / "compose.yaml"),
        "-f",
        str(RUNTIME / "overlay.json"),
        "--profile",
        "operations",
        "run",
        "--rm",
        "-T",
        "--pull",
        "never",
        "--no-deps",
        "--entrypoint",
        "python",
        "-e",
        "T44_SESSION_TTL_SECONDS=5400",
    ]
    for source, target, mode in (
        (INPUTS / "service-worker.py", "/run/t44-cohort/worker.py", "ro"),
        (INPUTS / "worker.py", "/run/t44-cohort/base-worker.py", "ro"),
        (INPUTS / "envelope.py", "/run/t44-cohort/envelope.py", "ro"),
        (INPUTS / "recipient.pem", "/run/t44-cohort/recipient.pem", "ro"),
        (OUTPUT, "/run/t44-secrets", "rw"),
    ):
        argv.extend(["--volume", f"{source}:{target}:{mode}"])
    return [
        *argv,
        "admin",
        "/run/t44-cohort/worker.py",
        "--base-worker",
        "/run/t44-cohort/base-worker.py",
        "--envelope-helper",
        "/run/t44-cohort/envelope.py",
        "--certificate",
        "/run/t44-cohort/recipient.pem",
        "--database",
        "t44",
        "--expected-source",
        SOURCE,
    ]


def safe_receipt(raw):
    result = json.loads(raw)
    if (
        isinstance(result, dict)
        and result.get("success") is False
        and result == {"success": False, "error": "COHORT_FIXTURE_FAILED"}
    ):
        return result
    if (
        not isinstance(result, dict)
        or set(result)
        != {"success", "subject_id", "session_id", "expires_at", "envelope_sha256"}
        or result["success"] is not True
        or any(
            type(result[k]) is not int or not 1 <= result[k] <= 4294967295
            for k in ("subject_id", "session_id")
        )
        or not isinstance(result["envelope_sha256"], str)
        or not re.fullmatch("[0-9a-f]{64}", result["envelope_sha256"])
        or not isinstance(result["expires_at"], str)
        or not re.fullmatch(
            r"2026-10-24T\d{2}:\d{2}:\d{2}\.\d{6}Z", result["expires_at"]
        )
        or datetime.fromisoformat(result["expires_at"].replace("Z", "+00:00"))
        <= datetime(2026, 10, 24, 10, 10, tzinfo=UTC)
    ):
        raise ValueError("receipt_rejected")
    return result


def main():
    os.umask(0o077)
    started = time.monotonic()
    result = {
        "success": False,
        "error": "COHORT_LAUNCH_FAILED",
        "actual_exit_code": None,
    }
    try:
        if os.getuid() != 0 or os.geteuid() != 0:
            raise ValueError("root_required")
        entry = BASE.lstat()
        if (
            entry.st_uid != 0
            or entry.st_mode & 0o022
            or hashlib.sha256(BASE.read_bytes()).hexdigest() != BASE_SHA
        ):
            raise ValueError("launcher_base_rejected")
        base = runpy.run_path(str(BASE))
        check = base["check_path"]
        check(BASE, owner=0)
        check(DELIVERY, owner=0, mode=0o700, directory=True)
        check(INPUTS, owner=0, mode=0o700, directory=True)
        check(OUTPUT, owner=10001, mode=0o700, directory=True)
        pins = {
            path: digest
            for path, digest in base["HASHES"].items()
            if path != base["TLS_HELPER"]
        }
        pins.update({INPUTS / "service-worker.py": WORKER_SHA, TLS_HELPER: TLS_SHA})
        for path, digest in pins.items():
            check(path, owner=0, mode=None if path == TLS_HELPER else 0o444)
            if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
                raise ValueError("public_source_rejected")
        for argv in (
            ["rev-parse", "HEAD"],
            ["status", "--porcelain", "--untracked-files=normal"],
        ):
            state = (
                subprocess.run(
                    ["git", "-C", str(ROOT), *argv],
                    capture_output=True,
                    check=True,
                    timeout=5,
                )
                .stdout.decode()
                .strip()
            )
            if state != (SOURCE if argv[0] == "rev-parse" else ""):
                raise ValueError("source_not_exact_clean")
        values = runpy.run_path(str(ROOT / "deployment/ops.py"))["load_env"](
            ROOT / ".env"
        )
        tls = runpy.run_path(str(TLS_HELPER))
        private_ip = tls["private_ip"](DELIVERY / "private-network.env")
        check(RUNTIME, owner=0, mode=0o700, directory=True)
        tls["validate_runtime"](RUNTIME, private_ip)
        env = base["environment"](values)
        endpoint = subprocess.run(
            [
                "docker",
                "--context",
                "default",
                "context",
                "inspect",
                "default",
                "--format",
                "{{.Endpoints.docker.Host}}",
            ],
            env=env,
            capture_output=True,
            check=True,
            timeout=5,
        )
        if not endpoint.stdout.decode().strip().startswith("unix://"):
            raise ValueError("local_daemon_required")
        remaining = min(220 - (time.monotonic() - started), END - time.time())
        if remaining <= 0:
            raise ValueError("deadline_reserve")
        prefix = RUNTIME / ("cohort-fixture-" + uuid4().hex)
        output = Path(str(prefix) + ".stdout")
        with (
            base["private_stream"](output) as stdout,
            base["private_stream"](Path(str(prefix) + ".stderr")) as stderr,
        ):
            try:
                process = subprocess.run(
                    command(values),
                    env=env,
                    input=json.dumps(
                        {"approved_origin": f"https://{private_ip}:8443"}
                    ).encode(),
                    stdout=stdout,
                    stderr=stderr,
                    check=False,
                    timeout=remaining,
                )
                result["actual_exit_code"] = process.returncode
            finally:
                stdout.flush()
                stderr.flush()
                os.fsync(stdout.fileno())
                os.fsync(stderr.fileno())
        receipt = safe_receipt(output.read_bytes())
        result = {
            "actual_exit_code": process.returncode,
            "worker": receipt,
            "success": process.returncode == 0 and receipt["success"],
        }
    except Exception:
        pass  # Never disclose private origin, token, configuration or driver messages.
    print(json.dumps(result, sort_keys=True))
    return 0 if result["success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
