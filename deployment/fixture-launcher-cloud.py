"""Fixed exact-C fixture launch only; root reviews and executes under outer timeout240."""

import hashlib
import json
import os
import re
import runpy
import stat
import subprocess
import time
from pathlib import Path
from uuid import uuid4

SOURCE = "0dfb55c2191200d947c5423fd9ee74bb0812cc5a"
ROOT = Path("/opt/t44-c-0dfb55c")
DELIVERY = Path("/run/t44-delivery")
RUNTIME = DELIVERY / "tls-C"
INPUTS = DELIVERY / "fixture-inputs"
OUTPUT = DELIVERY / "fixture-output"
TLS_HELPER = DELIVERY / "tls-delivery.py"
NETWORK_ENV = DELIVERY / "private-network.env"
HASHES = {
    TLS_HELPER: "cc6594d0ed18870245df82099f9790e1a425ea8e275e22b9a3b597cef6fd1cd9",
    INPUTS
    / "worker.py": "7b6332517473266b99a6121cd6ddaaaf08a61080b8e0667996689daf4542a626",
    INPUTS
    / "envelope.py": "6a5ddf1226b7e08623a6d8131dbbf742a28359584a34a0e2cf4daa770c2966f7",
    INPUTS
    / "recipient.pem": "496ded07649d49078d9e20cebf4fbd80f989d5d2b777573857eb090d1b38af69",
}
USERS = {"synthetic-manager", "synthetic-developer", "synthetic-reviewer"}
ERRORS = {
    "PATH_REJECTED",
    "SYMLINK_REJECTED",
    "PUBLIC_PARENT_REJECTED",
    "PUBLIC_FILE_REJECTED",
    "PUBLIC_HASH_MISMATCH",
    "OUTPUT_DIRECTORY_REJECTED",
    "OUTPUT_IN_USE",
    "OUTPUT_ALREADY_EXISTS",
    "OUTPUT_NAME_REJECTED",
    "CERTIFICATE_FINGERPRINT_MISMATCH",
    "TARGET_REJECTED",
    "CLI_SOURCE_MISMATCH",
    "SYNTHETIC_USER_ALREADY_EXISTS",
    "BUSINESS_DATA_NOT_EMPTY",
    "PASSWORD_GENERATION_FAILED",
    "ACCOUNT_OUTCOME_UNKNOWN",
    "ACCOUNT_CLI_FAILED",
    "FIXTURE_FAILED",
    "RECEIPT_WRITE_FAILED",
    "WORKER_UID_REJECTED",
    "WORKER_FAILED",
}


def command(values):
    if values["MYSQL_DATABASE"] != "t44" or values["T44_DOCKER_CONTEXT"] != "default":
        raise ValueError("target_rejected")
    arguments = [
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
    ]
    for source, target, mode in (
        (INPUTS / "worker.py", "/run/t44-fixture/worker.py", "ro"),
        (INPUTS / "envelope.py", "/run/t44-fixture/envelope.py", "ro"),
        (INPUTS / "recipient.pem", "/run/t44-fixture/recipient.pem", "ro"),
        (OUTPUT, "/run/t44-fixture-output", "rw"),
    ):
        arguments.extend(["--volume", f"{source}:{target}:{mode}"])
    arguments.extend(
        [
            "admin",
            "/run/t44-fixture/worker.py",
            "--database",
            "t44",
            "--expected-source",
            SOURCE,
            "--certificate",
            "/run/t44-fixture/recipient.pem",
            "--envelope-helper",
            "/run/t44-fixture/envelope.py",
            "--output-dir",
            "/run/t44-fixture-output",
        ]
    )
    return arguments


def environment(values):
    result = {
        k: v
        for k, v in os.environ.items()
        if k not in values and not k.startswith(("COMPOSE_", "DOCKER_"))
    }
    result.update(values)
    return result


def check_path(path, *, owner, mode=None, directory=False):
    for item in (*reversed(path.parents), path):
        if stat.S_ISLNK(item.lstat().st_mode):
            raise ValueError("symlink_rejected")
    entry = path.lstat()
    permitted_type = (
        stat.S_ISDIR(entry.st_mode) if directory else stat.S_ISREG(entry.st_mode)
    )
    if (
        not permitted_type
        or entry.st_uid != owner
        or stat.S_IMODE(entry.st_mode) & 0o022
        or mode is not None
        and stat.S_IMODE(entry.st_mode) != mode
    ):
        raise ValueError("path_permissions_rejected")


def safe_receipt(raw):
    if len(raw) > 32768:
        raise ValueError("receipt_rejected")
    value = json.loads(raw)
    booleans = {
        "success",
        "pending_written",
        "final_written",
        "seeded",
        "sessions_created",
        "creation_outcome_may_be_committed",
    }
    constants = {
        "format": "T44-SYNTHETIC-ACCOUNT-RECEIPT-v1",
        "expected_source": SOURCE,
        "cli_sha256": "da88377aed1131fb82aea31ef2783e02af01c6b620518f3d1b9e8b01175112db",
        "database": "t44",
    }
    allowed = (
        booleans
        | constants.keys()
        | {
            "confirmed_users",
            "pending_sha256",
            "final_sha256",
            "attempted_username",
            "cli_exit_code",
            "error",
        }
    )
    if (
        not isinstance(value, dict)
        or set(value) - allowed
        or type(value.get("success")) is not bool
    ):
        raise ValueError("receipt_rejected")
    for key, item in value.items():
        if (
            key in booleans
            and type(item) is not bool
            or key in constants
            and item != constants[key]
            or key.endswith("_sha256")
            and key != "cli_sha256"
            and (not isinstance(item, str) or not re.fullmatch("[0-9a-f]{64}", item))
            or key == "attempted_username"
            and item not in USERS
            or key == "error"
            and item not in ERRORS
            or key == "cli_exit_code"
            and (type(item) is not int or not -255 <= item <= 255)
        ):
            raise ValueError("receipt_rejected")
    users = value.get("confirmed_users", [])
    if not isinstance(users, list) or len(users) > 3:
        raise ValueError("receipt_rejected")
    seen_names, seen_ids = set(), set()
    for user in users:
        if (
            not isinstance(user, dict)
            or set(user) != {"username", "user_id"}
            or user["username"] not in USERS
            or type(user["user_id"]) is not int
            or not 1 <= user["user_id"] <= 4294967295
            or user["username"] in seen_names
            or user["user_id"] in seen_ids
        ):
            raise ValueError("receipt_rejected")
        seen_names.add(user["username"])
        seen_ids.add(user["user_id"])
    if value.get("seeded") or value.get("sessions_created"):
        raise ValueError("receipt_rejected")
    if value["success"] and (
        len(users) != 3
        or not value.get("pending_written")
        or not value.get("final_written")
        or value.get("error")
    ):
        raise ValueError("receipt_rejected")
    return value


def private_stream(path):
    descriptor = os.open(
        path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600
    )
    return os.fdopen(descriptor, "wb")


def main():
    os.umask(0o077)
    started = time.monotonic()
    receipt = {
        "stage": "synthetic-fixture",
        "actual_exit_code": None,
        "state_requires_observation": True,
        "retry_or_seed_attempted": False,
    }
    try:
        if os.getuid() != 0 or os.geteuid() != 0:
            raise ValueError("root_required")
        check_path(DELIVERY, owner=0, mode=0o700, directory=True)
        check_path(INPUTS, owner=0, mode=0o700, directory=True)
        check_path(OUTPUT, owner=10001, mode=0o700, directory=True)
        for path, digest in HASHES.items():
            check_path(path, owner=0, mode=None if path == TLS_HELPER else 0o444)
            if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
                raise ValueError("public_source_hash_rejected")
        tls = runpy.run_path(str(TLS_HELPER))
        values = tls["check_source"](ROOT)  # Uses exact C ops.load_env only in memory.
        status = subprocess.run(
            [
                "git",
                "-C",
                str(ROOT),
                "status",
                "--porcelain",
                "--untracked-files=normal",
            ],
            capture_output=True,
            check=True,
            timeout=5,
        )
        if status.stdout:
            raise ValueError("source_not_clean")
        tls["validate_runtime"](RUNTIME, tls["private_ip"](NETWORK_ENV))
        env = environment(values)
        context = subprocess.run(
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
        if not context.stdout.decode().strip().startswith("unix://"):
            raise ValueError("local_daemon_required")
        argv = command(values)
        remaining = min(
            220 - (time.monotonic() - started), tls["DEADLINE"] - 120 - time.time()
        )
        if remaining <= 0:
            raise ValueError("deadline_reserve_reached")
        prefix = RUNTIME / ("fixture-" + uuid4().hex)
        output, errors = Path(str(prefix) + ".stdout"), Path(str(prefix) + ".stderr")
        with private_stream(output) as stdout, private_stream(errors) as stderr:
            try:
                result = subprocess.run(
                    argv,
                    env=env,
                    stdout=stdout,
                    stderr=stderr,
                    check=False,
                    timeout=remaining,
                )
                receipt["actual_exit_code"] = result.returncode
            finally:
                stdout.flush()
                stderr.flush()
                os.fsync(stdout.fileno())
                os.fsync(stderr.fileno())
        receipt["worker"] = safe_receipt(output.read_bytes())
        success = result.returncode == 0 and receipt["worker"]["success"]
        receipt["state_requires_observation"] = not success
        print(json.dumps(receipt, sort_keys=True))
        return 0 if success else 1
    except Exception:
        receipt["error"] = "FIXTURE_LAUNCH_FAILED"
        print(json.dumps(receipt, sort_keys=True))
        return 1  # No retry, seed or destructive cleanup; inspect private logs/status first.


if __name__ == "__main__":
    raise SystemExit(main())
