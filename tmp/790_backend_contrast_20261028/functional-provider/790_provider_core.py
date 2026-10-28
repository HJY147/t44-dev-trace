"""Neutral identity core only; no executable cloud adapter or private transport schema yet."""

import json
import re
import secrets
from dataclasses import replace
from datetime import datetime, timezone
from uuid import uuid4

from t44.contracts import OPERATIONS, violations
from t44.persistence.schema import TABLES
from t44.services.application import Business
from t44.services.common import Call, wire
from t44.services.identity import token_digest
from t44.services.runtime import Runtime

UTC = timezone.utc  # noqa: UP017 -- host/parser compatibility; runs in product Python 3.12.
LABELS = ("m", "d", "d2", "r", "x")
F_DATABASE = "t44c_r28p7gen01_f"


def deadline(stop):
    if stop.tzinfo is None or (stop - datetime.now(UTC)).total_seconds() <= 0:
        raise ValueError("PROVIDER_ABSOLUTE_WINDOW_EXPIRED")


def original_cli_runner(argv, password, timeout):
    """Admin/data-only process; caller owns verified environment and original product image."""
    import subprocess
    import sys

    result = subprocess.run(
        [sys.executable, "-m", "t44.cli", *argv],
        input=password,
        capture_output=True,
        check=False,
        timeout=timeout,
    )
    if result.returncode:
        raise ValueError("ORIGINAL_CLI_FAILED_PRIVATE_OUTPUT_SUPPRESSED")
    return json.loads(result.stdout)


def cli_timeout(stop):
    deadline(stop)
    return min(30, (stop - datetime.now(UTC)).total_seconds())


def create_five(factory, settings, *, prefix, stop, cli=original_cli_runner):
    """Return credentials in memory only. Project-role membership is not preassigned."""
    deadline(stop)
    if (
        settings.session_ttl_seconds != 3600
        or settings.mysql_settings().database != F_DATABASE
    ):
        raise ValueError("ORIGINAL_F_DATABASE_AND_MAIN_TTL_REQUIRED")
    if not re.fullmatch(r"[A-Za-z0-9_.-]{1,48}", prefix):
        raise ValueError("NEW_SAFE_ACCOUNT_PREFIX_REQUIRED")
    deadline(stop)
    with factory() as uow:
        counts = {name: uow.gateway.count(name) for name in TABLES}
    if any(counts.values()):
        raise ValueError("FRESH_EMPTY_APPLICATION_TABLES_REQUIRED_NO_RESEED")
    accounts = {}
    for label in LABELS:
        password = secrets.token_urlsafe(32)
        username = prefix + "-" + label
        result = cli(
            [
                "init-user",
                "--username",
                username,
                "--display-name",
                "[synthetic F] " + label,
                "--password-stdin",
            ],
            (password + "\n").encode(),
            cli_timeout(stop),
        )
        if set(result) != {"user_id"} or type(result["user_id"]) is not int:
            raise ValueError("ACTUAL_ORIGINAL_CLI_ID_REQUIRED")
        accounts[label] = {
            "username": username,
            "password": password,
            "user_id": result["user_id"],
        }
    deadline(stop)
    with factory() as uow:
        users = uow.gateway.rows("users", {})
        other = {name: uow.gateway.count(name) for name in TABLES if name != "users"}
    if len(users) != 5 or len({row["id"] for row in users}) != 5 or any(other.values()):
        raise ValueError("EXACT_FIVE_IDENTITIES_AND_NO_BUSINESS_DATA_REQUIRED")
    if {row["id"] for row in users} != {
        row["user_id"] for row in accounts.values()
    } or any(not row["active"] for row in users):
        raise ValueError("ACTUAL_FIVE_ACTIVE_USERS_REQUIRED")
    return accounts


def row_for_token(factory, token):
    with factory() as uow:
        rows = uow.gateway.rows(
            "auth_sessions", {"token_hash": token_digest(token)}, limit=1
        )
    if len(rows) != 1:
        raise ValueError("ONE_REAL_SESSION_DIGEST_REQUIRED")
    return rows[0]


def _validate_login(call):
    schema = OPERATIONS["login"]["requestBody"]["content"]["application/json"]["schema"]
    if violations(schema, call.body):
        raise ValueError("ORIGINAL_LOGIN_REQUEST_CONTRACT_FAILED")


def issue(factory, settings, account, *, ttl, stop):
    """Original Runtime login, limiter, password check, session INSERT, response and audit."""
    deadline(stop)
    if settings.session_ttl_seconds != 3600 or ttl not in (60, 3600):
        raise ValueError("MAIN_TTL_3600_AND_EXPLICIT_NEW_SESSION_TTL_REQUIRED")
    deadline(stop)
    with factory() as uow:
        before_sessions = {
            row["id"]: row for row in uow.gateway.rows("auth_sessions", {})
        }
    runtime = Runtime(factory, replace(settings, session_ttl_seconds=ttl), Business())
    call = Call(
        "login",
        str(uuid4()),
        None,
        body={"username": account["username"], "password": account["password"]},
    )
    deadline(stop)
    status, result, replay, original = runtime.execute(
        call, _validate_login, source="neutral-provider790"
    )
    if status != 200 or replay or original is not None:
        raise ValueError("ORIGINAL_RUNTIME_LOGIN_FAILED_NO_SECRET_OUTPUT")
    deadline(stop)
    row = row_for_token(factory, result["access_token"])
    deadline(stop)
    with factory() as uow:
        after_sessions = {
            item["id"]: item for item in uow.gateway.rows("auth_sessions", {})
        }
    deadline(stop)
    with factory() as uow:
        audit_rows = uow.gateway.rows("audit_events", {"request_id": call.request_id})
    if (
        len(audit_rows) != 1
        or audit_rows[0]["operation_id"] != "login"
        or audit_rows[0]["outcome"] != 1
        or audit_rows[0]["actor_id"] != account["user_id"]
    ):
        raise ValueError("ONE_ORIGINAL_SUCCESSFUL_LOGIN_AUDIT_REQUIRED")
    if (
        set(after_sessions) != set(before_sessions) | {row["id"]}
        or row["id"] in before_sessions
        or any(after_sessions[key] != value for key, value in before_sessions.items())
    ):
        raise ValueError(
            "NORMAL_LOGIN_MUST_ADD_ONE_AND_PRESERVE_ALL_EXISTING_AUTH_ROWS"
        )
    if (
        row["user_id"] != account["user_id"]
        or row["actor_kind"] != 1
        or row["revoked_at"] is not None
        or row["scopes"]
        or row["project_ids"]
        or (row["expires_at"] - row["created_at"]).total_seconds() != ttl
        or result["user"]["id"] != account["user_id"]
    ):
        raise ValueError("REAL_SESSION_SUBJECT_OR_TTL_DIFFERS")
    return {
        "access_token": result["access_token"],
        "user_id": account["user_id"],
        "session_id": row["id"],
        "created_at": wire(row["created_at"]),
        "expires_at": wire(row["expires_at"]),
        "ttl_seconds": ttl,
        "issued_at": wire(row["created_at"]),
        "issuance_receipt": {
            "method": "original Runtime.execute(login), isolated Settings TTL, original issue_session INSERT and audit",
            "prior_auth_rows": len(before_sessions),
            "new_auth_rows": 1,
            "prior_auth_rows_unchanged": True,
            "normal_login_audit_verified": True,
            "clock_override_used": False,
            "main_settings_ttl_seconds": settings.session_ttl_seconds,
        },
    }


def get_me(factory, settings, session, *, stop):
    deadline(stop)
    runtime = Runtime(factory, settings, Business())
    call = Call("getMe", str(uuid4()), session["access_token"])
    return runtime.execute(call, lambda _call: None)


def observe_natural_expiry(factory, settings, session, *, stop):
    """Read/normal auth only; caller waits actual wall time, never modifies a stored timestamp."""
    deadline(stop)
    before = row_for_token(factory, session["access_token"])
    if before["expires_at"] > datetime.now(UTC):
        raise ValueError("NOT_NATURALLY_EXPIRED_YET")
    status, body, _, _ = get_me(factory, settings, session, stop=stop)
    after = row_for_token(factory, session["access_token"])
    if before != after or status != 401 or body.get("code") != "TOKEN_EXPIRED":
        raise ValueError("NATURAL_EXPIRY_OR_IMMUTABLE_SESSION_CHECK_FAILED")
    return {
        "method": "original Runtime login with isolated Settings TTL60, actual wall-time wait",
        "ttl_seconds": session["ttl_seconds"],
        "created_at": session["created_at"],
        "expires_at": session["expires_at"],
        "observed_utc": wire(datetime.now(UTC)),
        "unchanged_session_row": True,
        "original_getMe_status": status,
        "original_getMe_code": body["code"],
    }


def revoke_exact(factory, session, *, stop, cli=original_cli_runner):
    deadline(stop)
    before = row_for_token(factory, session["access_token"])
    if before["id"] != session["session_id"] or before["revoked_at"] is not None:
        raise ValueError("EXACT_UNREVOKED_ORIGINAL_SESSION_REQUIRED")
    result = cli(
        ["revoke-session", "--session-id", str(session["session_id"])],
        b"",
        cli_timeout(stop),
    )
    if result != {"revoked_sessions": 1}:
        raise ValueError("ONE_EXACT_ORIGINAL_CLI_REVOCATION_REQUIRED")
    deadline(stop)
    after = row_for_token(factory, session["access_token"])
    if after["revoked_at"] is None or {
        k: v for k, v in after.items() if k != "revoked_at"
    } != {k: v for k, v in before.items() if k != "revoked_at"}:
        raise ValueError("ONLY_TARGET_REVOCATION_FIELD_MAY_CHANGE")
    return {
        "method": "original python -m t44.cli revoke-session --session-id",
        "session_id": session["session_id"],
        "revoked_sessions": 1,
    }


if __name__ == "__main__":
    # No private schema, recipient key or provider nonce has been approved yet.
    raise SystemExit(
        "PROVIDER_PUBLIC_HANDOFF_PROTOCOL_AND_VERIFIED_F_HOST_ADAPTER_REQUIRED"
    )
