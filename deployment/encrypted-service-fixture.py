"""One initial neutral service credential, encrypted in memory; never seed or rotate."""

import argparse
import fcntl
import hashlib
import ipaddress
import json
import os
import runpy
import stat
import subprocess
import sys
from contextlib import suppress
from datetime import UTC, datetime, timedelta
from pathlib import Path
from urllib.parse import urlsplit

SOURCE = "0dfb55c2191200d947c5423fd9ee74bb0812cc5a"
BASE_SHA = "7b6332517473266b99a6121cd6ddaaaf08a61080b8e0667996689daf4542a626"
ADMIN_SHA = "c24e303b632a502c0e4180d72830d9e94b71d4627260022715047dfe3d14a07f"
NAME = "notification-cohort"
PROJECTS = list(range(1, 41))
MIN_EXPIRY = datetime(2026, 10, 24, 10, 10, tzinfo=UTC)
FINAL = "neutral-service.envelope.json"


def issue_command(admin):
    scopes = [part for project in PROJECTS for part in ("--project-id", str(project))]
    return [sys.executable, "-B", str(admin), "--name", NAME, *scopes]


def origin(raw):
    value = json.loads(raw)
    if not isinstance(value, dict) or set(value) != {"approved_origin"}:
        raise ValueError("origin_shape")
    url = urlsplit(value["approved_origin"])
    address = ipaddress.IPv4Address(url.hostname)
    private = any(
        address in ipaddress.IPv4Network(n)
        for n in ("10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16")
    )
    if not private or value["approved_origin"] != f"https://{address}:8443":
        raise ValueError("origin_rejected")
    return value["approved_origin"]


def preflight(factory, clock):
    if clock + timedelta(seconds=5400) <= MIN_EXPIRY:
        raise ValueError("issuance_too_early")
    with factory() as uow:
        g = uow.gateway
        if g.rows("service_accounts", {"name": NAME}, limit=1):
            raise ValueError("subject_already_exists")
        if g.count("projects", {"id": PROJECTS}) != 40:
            raise ValueError("project_scope_missing")


def package(factory, credential, approved_origin, clock):
    token, session_id = credential["access_token"], credential["session_id"]
    if (
        not isinstance(token, str)
        or not 32 <= len(token) <= 512
        or token.startswith("Bearer ")
        or type(session_id) is not int
        or not 1 <= session_id <= 4294967295
    ):
        raise ValueError("credential_shape")
    with factory() as uow:
        g = uow.gateway
        session = g.get("auth_sessions", session_id)
        if not session:
            raise ValueError("session_missing")
        subject_id = session["service_account_id"]
        if type(subject_id) is not int or not 1 <= subject_id <= 4294967295:
            raise ValueError("subject_id")
        subject = g.get("service_accounts", subject_id)
    if (
        not subject
        or subject["name"] != NAME
        or subject["active"] != 1
        or subject["created_at"] != session["created_at"]
        or session["actor_kind"] != 2
        or session["user_id"] is not None
        or session["revoked_at"] is not None
        or session["token_hash"] != hashlib.sha256(token.encode()).digest()
        or session["scopes"] != ["escalation:write"]
        or session["project_ids"] != PROJECTS
        or any(type(n) is not int for n in session["project_ids"])
    ):
        raise ValueError("session_binding")
    issued, expires = session["created_at"], session["expires_at"]
    if (
        issued.tzinfo is None
        or expires.tzinfo is None
        or expires <= max(clock, MIN_EXPIRY)
        or expires - issued != timedelta(seconds=5400)
        or datetime.fromisoformat(credential["expires_at"].replace("Z", "+00:00"))
        != expires
    ):
        raise ValueError("expiry_rejected")
    return {
        "format": "852-neutral-service-credential-v1",
        "synthetic": True,
        "source_commit": SOURCE,
        "approved_origin": approved_origin,
        "service": {
            "subject_id": subject_id,
            "token": token,
            "scopes": ["escalation:write"],
            "allowed_project_ids": PROJECTS,
            "issued_at": issued.astimezone(UTC)
            .isoformat(timespec="microseconds")
            .replace("+00:00", "Z"),
            "expires_at": expires.astimezone(UTC)
            .isoformat(timespec="microseconds")
            .replace("+00:00", "Z"),
        },
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for field in (
        "base-worker",
        "envelope-helper",
        "certificate",
        "database",
        "expected-source",
    ):
        parser.add_argument("--" + field, required=True)
    args = parser.parse_args(argv)
    engine, directory = None, None
    result = {"success": False, "error": "COHORT_FIXTURE_FAILED"}
    try:
        if (
            os.getuid() != 10001
            or os.geteuid() != 10001
            or os.getenv("T44_SESSION_TTL_SECONDS") != "5400"
        ):
            raise ValueError("identity_or_ttl")
        os.umask(0o077)
        base_path = Path(args.base_worker)
        metadata = base_path.lstat()
        if (
            not stat.S_ISREG(metadata.st_mode)
            or metadata.st_uid != 0
            or stat.S_IMODE(metadata.st_mode) != 0o444
            or hashlib.sha256(base_path.read_bytes()).hexdigest() != BASE_SHA
        ):
            raise ValueError("base_worker_rejected")
        base = runpy.run_path(str(base_path))
        base["_public_file"](base_path, BASE_SHA)
        helper, certificate = base["_load_envelope"](
            args.envelope_helper, args.certificate
        )
        settings = base["_database_settings"](args.database, args.expected_source)
        approved_origin = origin(sys.stdin.buffer.read(2049))
        output = base["_path"]("/run/t44-secrets")
        directory = os.open(output, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        metadata = os.fstat(directory)
        if metadata.st_uid != 10001 or stat.S_IMODE(metadata.st_mode) != 0o700:
            raise ValueError("private_directory")
        fcntl.flock(directory, fcntl.LOCK_EX | fcntl.LOCK_NB)
        for filename in ("scheduler-token.json", FINAL):
            try:
                os.stat(filename, dir_fd=directory, follow_symlinks=False)
            except FileNotFoundError:
                continue
            raise ValueError("output_exists")
        admin = Path("/app/deployment/credential_admin.py")
        if hashlib.sha256(admin.read_bytes()).hexdigest() != ADMIN_SHA:
            raise ValueError("admin_source_rejected")
        from t44.persistence import SqlAlchemyUnitOfWorkFactory, create_mysql_engine

        engine = create_mysql_engine(settings)
        factory = SqlAlchemyUnitOfWorkFactory(engine)
        preflight(factory, datetime.now(UTC))
        issued = subprocess.run(
            issue_command(admin),
            capture_output=True,
            check=False,
            timeout=90,
        )
        if issued.returncode:
            raise ValueError("issuance_failed_or_unknown")
        public = helper.strict_json(issued.stdout)
        descriptor = os.open(
            "scheduler-token.json", os.O_RDONLY | os.O_NOFOLLOW, dir_fd=directory
        )
        with os.fdopen(descriptor, "rb") as stream:
            metadata = os.fstat(stream.fileno())
            if (
                not stat.S_ISREG(metadata.st_mode)
                or metadata.st_uid != 10001
                or stat.S_IMODE(metadata.st_mode) != 0o600
                or metadata.st_size > 8192
            ):
                raise ValueError("private_credential_rejected")
            credential = helper.strict_json(stream.read(8193))
        if (
            not public.get("credential_written")
            or public["session_id"] != credential["session_id"]
        ):
            raise ValueError("receipt_mismatch")
        payload = package(factory, credential, approved_origin, datetime.now(UTC))
        encrypted = (
            helper.canonical(
                helper.encrypt(
                    helper.canonical(payload), certificate, "neutral-environment"
                )
            )
            + b"\n"
        )
        descriptor = os.open(
            FINAL,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
            0o600,
            dir_fd=directory,
        )
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(encrypted)
            stream.flush()
            os.fsync(stream.fileno())
        os.fsync(directory)
        result = {
            "success": True,
            "subject_id": payload["service"]["subject_id"],
            "session_id": credential["session_id"],
            "expires_at": payload["service"]["expires_at"],
            "envelope_sha256": hashlib.sha256(encrypted).hexdigest(),
        }
    except Exception:
        pass  # Fail closed; no token/origin/driver exception text crosses stdout.
    finally:
        if directory is not None:
            os.close(directory)
        if engine is not None:
            with suppress(Exception):
                engine.dispose()
    print(json.dumps(result, sort_keys=True))
    return 0 if result["success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
