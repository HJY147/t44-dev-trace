"""One-shot synthetic account worker; never seed, issue sessions or print secrets."""

import argparse
import fcntl
import hashlib
import importlib.util
import json
import os
import secrets
import stat
import subprocess
import sys
import types
from contextlib import suppress
from pathlib import Path

SOURCE = "0dfb55c2191200d947c5423fd9ee74bb0812cc5a"
CLI_SHA256 = "da88377aed1131fb82aea31ef2783e02af01c6b620518f3d1b9e8b01175112db"
HELPER_SHA256 = "6a5ddf1226b7e08623a6d8131dbbf742a28359584a34a0e2cf4daa770c2966f7"
CERT_SHA256 = "496ded07649d49078d9e20cebf4fbd80f989d5d2b777573857eb090d1b38af69"
CERT_FINGERPRINT = "f78e169a626c9eb3978428016996c2370ffd170b3f0cc83f3e96ba4bf199d19e"
ACCOUNTS = (
    ("synthetic-manager", "Synthetic manager", "manager"),
    ("synthetic-developer", "Synthetic developer", "developer"),
    ("synthetic-reviewer", "Synthetic reviewer", "reviewer"),
)
PENDING = "synthetic-users.pending.envelope.json"
FINAL = "synthetic-users.final.envelope.json"
STATUS = "synthetic-users.status.json"


class FixtureFailure(Exception):
    """Only a fixed operational code may cross the public output boundary."""

    def __init__(self, code, *, exit_code=None):
        super().__init__(code)
        self.exit_code = exit_code


def _path(path):
    path = Path(path)
    if not path.is_absolute() or ".." in path.parts:
        raise FixtureFailure("PATH_REJECTED")
    for component in (*reversed(path.parents), path):
        if stat.S_ISLNK(component.lstat().st_mode):
            raise FixtureFailure("SYMLINK_REJECTED")
    return path


def _public_file(path, expected_hash, *, owner=0):
    path = _path(path)
    for parent in path.parents:
        metadata = parent.stat()
        if metadata.st_uid not in {0, owner} or stat.S_IMODE(metadata.st_mode) & 0o022:
            raise FixtureFailure("PUBLIC_PARENT_REJECTED")
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        metadata = os.fstat(descriptor)
        if (
            not stat.S_ISREG(metadata.st_mode)
            or metadata.st_uid != owner
            or stat.S_IMODE(metadata.st_mode) & 0o222
            or metadata.st_size > 1024 * 1024
        ):
            raise FixtureFailure("PUBLIC_FILE_REJECTED")
        with os.fdopen(descriptor, "rb", closefd=False) as stream:
            raw = stream.read(1024 * 1024 + 1)
        if hashlib.sha256(raw).hexdigest() != expected_hash:
            raise FixtureFailure("PUBLIC_HASH_MISMATCH")
        return raw
    finally:
        os.close(descriptor)


def _output_directory(path):
    descriptor = os.open(_path(path), os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        metadata = os.fstat(descriptor)
        if metadata.st_uid != os.geteuid() or stat.S_IMODE(metadata.st_mode) != 0o700:
            raise FixtureFailure("OUTPUT_DIRECTORY_REJECTED")
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise FixtureFailure("OUTPUT_IN_USE") from None
        for name in (PENDING, FINAL, STATUS):
            try:
                os.stat(name, dir_fd=descriptor, follow_symlinks=False)
            except FileNotFoundError:
                continue
            raise FixtureFailure("OUTPUT_ALREADY_EXISTS")
        return descriptor
    except BaseException:
        os.close(descriptor)
        raise


def _write_json(directory, name, content):
    if name not in {PENDING, FINAL, STATUS}:
        raise FixtureFailure("OUTPUT_NAME_REJECTED")
    raw = (
        json.dumps(content, ensure_ascii=True, sort_keys=True, allow_nan=False).encode()
        + b"\n"
    )
    descriptor = os.open(
        name,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
        0o600,
        dir_fd=directory,
    )
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    os.fsync(directory)
    return hashlib.sha256(raw).hexdigest()


def _load_envelope(helper_path, certificate_path):
    certificate = _public_file(certificate_path, CERT_SHA256)
    raw = _public_file(helper_path, HELPER_SHA256)
    helper = types.ModuleType("t44_public_envelope_v1")
    # Only the exact SHA-pinned public helper bytes are executable input.
    exec(compile(raw, "<pinned-public-envelope-v1>", "exec"), helper.__dict__)  # nosec B102
    _, fingerprint = helper.recipient(certificate)
    if fingerprint != CERT_FINGERPRINT:
        raise FixtureFailure("CERTIFICATE_FINGERPRINT_MISMATCH")
    return helper, certificate


def _database_settings(database, expected_source):
    from t44.settings import Settings

    if (
        expected_source != SOURCE
        or database != "t44"
        or os.getenv("T44_DATABASE") != database
    ):
        raise FixtureFailure("TARGET_REJECTED")
    settings = Settings.from_env().mysql_settings()
    if settings.database != database:
        raise FixtureFailure("TARGET_REJECTED")
    spec = importlib.util.find_spec("t44.cli")
    if (
        not spec
        or not spec.origin
        or hashlib.sha256(Path(spec.origin).read_bytes()).hexdigest() != CLI_SHA256
    ):
        raise FixtureFailure("CLI_SOURCE_MISMATCH")
    return settings


def _preflight(factory):
    from t44.persistence.schema import TABLES

    with factory() as uow:
        gateway = uow.gateway
        if gateway.count("users", {"username": [account[0] for account in ACCOUNTS]}):
            raise FixtureFailure("SYNTHETIC_USER_ALREADY_EXISTS")
        for table in TABLES:
            if table not in {
                "users",
                "service_accounts",
                "auth_sessions",
            } and gateway.count(table):
                raise FixtureFailure("BUSINESS_DATA_NOT_EMPTY")


def _create_user(account, runner):
    command = [
        sys.executable,
        "-B",
        "-m",
        "t44.cli",
        "init-user",
        "--username",
        account["username"],
        "--display-name",
        account["display_name"],
        "--password-stdin",
    ]
    try:
        completed = runner(
            command,
            input=(account["password"] + "\n").encode(),
            capture_output=True,
            check=False,
            timeout=60,
        )
    except (OSError, subprocess.TimeoutExpired):
        raise FixtureFailure("ACCOUNT_OUTCOME_UNKNOWN") from None
    if completed.returncode:
        raise FixtureFailure("ACCOUNT_CLI_FAILED", exit_code=completed.returncode)
    try:
        result = json.loads(completed.stdout)
        if (
            not isinstance(result, dict)
            or set(result) != {"user_id"}
            or type(result["user_id"]) is not int
            or not 1 <= result["user_id"] <= 4294967295
        ):
            raise ValueError
    except (TypeError, ValueError):
        raise FixtureFailure("ACCOUNT_OUTCOME_UNKNOWN") from None
    return result["user_id"]


def provision(directory, helper, certificate, factory, *, runner=subprocess.run):
    status = {
        "format": "T44-SYNTHETIC-ACCOUNT-RECEIPT-v1",
        "expected_source": SOURCE,
        "cli_sha256": CLI_SHA256,
        "database": "t44",
        "success": False,
        "pending_written": False,
        "final_written": False,
        "confirmed_users": [],
        "seeded": False,
        "sessions_created": False,
    }
    try:
        _preflight(factory)
        accounts = [
            {
                "username": username,
                "display_name": display,
                "role_after_seed": role,
                "password": secrets.token_urlsafe(32),
            }
            for username, display, role in ACCOUNTS
        ]
        if len({account["password"] for account in accounts}) != len(ACCOUNTS):
            raise FixtureFailure("PASSWORD_GENERATION_FAILED")
        package = {
            "source": SOURCE,
            "synthetic": True,
            "database": "t44",
            "accounts": accounts,
        }
        envelope = helper.encrypt(
            helper.canonical({**package, "status": "pending"}),
            certificate,
            "neutral-environment",
        )
        status["pending_sha256"] = _write_json(directory, PENDING, envelope)
        status["pending_written"] = True
        for account in accounts:
            status["attempted_username"] = account["username"]
            user_id = _create_user(account, runner)
            if user_id in {user["user_id"] for user in status["confirmed_users"]}:
                raise FixtureFailure("ACCOUNT_OUTCOME_UNKNOWN")
            account["user_id"] = user_id
            status["cli_exit_code"] = 0
            status["confirmed_users"].append(
                {"username": account["username"], "user_id": account["user_id"]}
            )
        envelope = helper.encrypt(
            helper.canonical({**package, "status": "accounts-created-not-seeded"}),
            certificate,
            "neutral-environment",
        )
        status["final_sha256"] = _write_json(directory, FINAL, envelope)
        status.update(final_written=True, success=True)
    except FixtureFailure as error:
        status["error"] = str(error)
        if error.exit_code is not None:
            status["cli_exit_code"] = error.exit_code
        status["creation_outcome_may_be_committed"] = str(error) in {
            "ACCOUNT_CLI_FAILED",
            "ACCOUNT_OUTCOME_UNKNOWN",
        }
    except Exception:
        status["error"] = "FIXTURE_FAILED"
    try:
        _write_json(directory, STATUS, status)
    except Exception:
        status.update(success=False, error="RECEIPT_WRITE_FAILED")
    return status


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in (
        "database",
        "expected-source",
        "certificate",
        "envelope-helper",
        "output-dir",
    ):
        parser.add_argument("--" + name, required=True)
    args = parser.parse_args(argv)
    directory, engine = None, None
    try:
        if os.getuid() != 10001 or os.geteuid() != 10001:
            raise FixtureFailure("WORKER_UID_REJECTED")
        os.umask(0o077)
        helper, certificate = _load_envelope(args.envelope_helper, args.certificate)
        directory = _output_directory(args.output_dir)
        settings = _database_settings(args.database, args.expected_source)
        from t44.persistence import SqlAlchemyUnitOfWorkFactory, create_mysql_engine

        engine = create_mysql_engine(settings)
        result = provision(
            directory, helper, certificate, SqlAlchemyUnitOfWorkFactory(engine)
        )
    except FixtureFailure as error:
        result = {"success": False, "error": str(error)}
    except Exception:
        result = {"success": False, "error": "WORKER_FAILED"}
    finally:
        if directory is not None:
            os.close(directory)
        if engine is not None:
            # Preserve the primary account outcome; never leak driver details.
            with suppress(Exception):
                engine.dispose()
    print(json.dumps(result, sort_keys=True))
    return 0 if result["success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
