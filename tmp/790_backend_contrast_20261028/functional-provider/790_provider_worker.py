"""One-shot original-product/data-only F provider; stdout contains PUBLIC metadata only."""

import argparse
import importlib
import json
import os
import platform
import re
import stat
import time
from datetime import datetime, timezone
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker
from sqlalchemy import text
from t44.persistence import SqlAlchemyUnitOfWorkFactory, create_mysql_engine
from t44.persistence.schema import TABLES
from t44.settings import Settings

core = importlib.import_module("790_provider_core")
crypto = importlib.import_module("790_provider_crypto")
UTC = timezone.utc  # noqa: UP017 -- host-compatible parser.
SOURCE = "a12e9e70b963bacafda3242bb6d82e53ee912ff1"
BINDING = "192ff29972aef079ad914139f50bcabbfa5c967ad1c8f2253252ecc226efd59d"
CA_SHA = "e2a07c50aaef9343ba881dc484b0b4ec62fdc32dfc8db25c1de8a1796383dc92"
SCHEMA_SHA = "6db48a86054e974be1240cdd6cad8a17a2d5c038166dece32a149b5889f04e56"
STOP = datetime(2026, 10, 28, 7, 30, tzinfo=UTC)


def read(path, private=False):
    path = Path(path)
    if not path.is_absolute() or path.resolve() != path:
        raise ValueError("EXACT_ABSOLUTE_NONSYMLINK_INPUT_REQUIRED")
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(fd, "rb") as stream:
        info = os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_size > 4 * 1024 * 1024:
            raise ValueError("BOUNDED_REGULAR_INPUT_REQUIRED")
        if private and stat.S_IMODE(info.st_mode) & 0o077:
            raise ValueError("PRIVATE_INPUT_MODE_REQUIRED")
        return stream.read()


def write(path, raw):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "wb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())


def validate_descriptor(descriptor, ca):
    identity = descriptor["sut_identity"]
    stop = datetime.fromisoformat(
        descriptor["stop_utc"].replace("Z", "+00:00")  # noqa: FURB162 -- Python 3.10 compatible.
    )
    if (
        descriptor["kind"] != "ROOT_T12_PROVIDER_DESCRIPTOR_V1"
        or descriptor["binding_sha256"] != BINDING
        or identity["source_sha"] != SOURCE
        or identity["schema_name"] != core.F_DATABASE
        or identity["worker_count"] != 4
        or identity["main_http_session_ttl_seconds"] != 3600
        or identity["ca_sha256"] != CA_SHA
        or crypto.sha(ca) != CA_SHA
        or identity["base_url"] != "https://172.21.182.245:19443/api/v1"
        or identity["pinned_ip"] != "172.21.182.245"
        or not re.fullmatch(r"[0-9a-f]{48}", descriptor["recipient_nonce"])
        or not re.fullmatch(r"[0-9a-f]{64}", descriptor["host_public_proof_sha256"])
        or descriptor["expired_subject"] not in core.LABELS
        or descriptor["revocation_subject"] not in core.LABELS
        or stop != STOP
        or (stop - datetime.now(UTC)).total_seconds() < 120
        or descriptor["admin_networks"] != ["data"]
        or core.F_DATABASE not in descriptor["auth_store_resource_id"]
    ):
        raise ValueError("EXACT_ACTUAL_F_DESCRIPTOR_REQUIRED")
    crypto.public_key(
        descriptor["recipient_public_key_pem"],
        descriptor["recipient_public_key_sha256"],
    )
    return stop


def verify_source(wanted):
    root = Path("/app/backend")
    rows = []
    for path in sorted(
        list((root / "t44").rglob("*"))
        + [root / "requirements.lock", root / "pyproject.toml"]
    ):
        info = path.lstat()
        if stat.S_ISLNK(info.st_mode) or not (
            stat.S_ISREG(info.st_mode) or stat.S_ISDIR(info.st_mode)
        ):
            raise ValueError("SOURCE_SPECIAL_OBJECT_FORBIDDEN")
        if path.is_file():
            rows.append(
                {
                    "path": "backend/" + path.relative_to(root).as_posix(),
                    "bytes": info.st_size,
                    "sha256": crypto.sha(path.read_bytes()),
                    "mode": stat.S_IMODE(info.st_mode),
                }
            )
    if len(rows) != 53 or rows != wanted:
        raise ValueError("EXACT_53_PRODUCT_SOURCE_FILES_REQUIRED")


def build_packet(descriptor, accounts, sessions, ca, expired_receipt):
    environment_accounts, provenance = {}, {}
    for label, session in sessions.items():
        subject = (
            descriptor["expired_subject"]
            if label == "expired"
            else (descriptor["revocation_subject"] if label == "revocation" else label)
        )
        environment_accounts[label] = {
            "id": session["user_id"],
            "username": accounts[subject]["username"],
            "token": session["access_token"],
        }
        provenance[label] = {
            "session_id": session["session_id"],
            "user_id": session["user_id"],
            "issued_at": session["issued_at"],
            "expires_at": session["expires_at"],
            "session_ttl_seconds": session["ttl_seconds"],
            "issuer_source_sha": SOURCE,
            "auth_store_resource_id": descriptor["auth_store_resource_id"],
            "issuance_path": "original_Runtime.execute(login)-identity.login-issue_session",
            "actual_python_call": "Runtime(factory, replace(main_settings, session_ttl_seconds=ttl), Business()).execute(Call('login', request_id, None, body=credentials), validate_login, source=provider)",
            "normal_new_session_insert": True,
            "normal_login_audit": True,
            "existing_session_records_changed": False,
            "system_clock_changed": False,
            "state_at_delivery": "naturally_expired"
            if label == "expired"
            else "active",
            "dedicated_disposable_session": label in {"expired", "revocation"},
        }
        if label == "expired":
            provenance[label]["natural_wait_completed_at"] = expired_receipt[
                "observed_utc"
            ]
    return {
        "kind": "ROOT_NEUTRAL_FUNCTIONAL_INPUTS_V1",
        "visibility": "PRIVATE",
        "recipient_nonce": descriptor["recipient_nonce"],
        "tool_freeze_sha256": crypto.FREEZE,
        "tool_execution_build_sha256": crypto.EXECUTION_BUILD,
        "root_grant_sha256": descriptor.get("root_grant_sha256"),
        "sut_identity": descriptor["sut_identity"],
        "environment": {
            "accounts": environment_accounts,
            "fixture_ownership": descriptor["fixture_ownership"],
            "phase_scope": "functional only after exact root admission; no fault/performance/retry",
        },
        "ca_pem_b64": crypto.b64(ca),
        "session_provenance": provenance,
        "fixture_state": {
            "business_tables_empty": True,
            "auth_rows_expected": True,
            "existing_project_ids": [],
            "cleanup_authorized": False,
        },
        "scope_provider": {
            "protocol": "nonce-sealed-project-scope",
            "provider_label": descriptor["provider_label"],
            "sut_runtime_identity": descriptor["sut_identity"]["runtime_identity"],
            "before_admission_no_scope_provisioning": True,
        },
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("descriptor", "schema", "ca", "output-dir"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--descriptor-sha256", required=True)
    args = parser.parse_args(argv)
    if platform.system() != "Linux" or os.geteuid() != 10001:
        raise ValueError("ORIGINAL_PRODUCT_ADMIN_UID_REQUIRED")
    raw = read(args.descriptor)
    if (
        crypto.sha(raw) != args.descriptor_sha256
        or crypto.sha(read(args.schema)) != SCHEMA_SHA
    ):
        raise ValueError("EXACT_PUBLIC_DESCRIPTOR_AND_SCHEMA_PINS_REQUIRED")
    descriptor, ca = json.loads(raw), read(args.ca)
    stop = validate_descriptor(descriptor, ca)
    schema = json.loads(read(args.schema))
    Draft202012Validator(
        schema["properties"]["sut_identity"], format_checker=FormatChecker()
    ).validate(descriptor["sut_identity"])
    verify_source(descriptor["source_files"])
    settings = Settings.from_env()
    if (
        settings.session_ttl_seconds != 3600
        or settings.mysql_settings().database != core.F_DATABASE
    ):
        raise ValueError("ORIGINAL_F_MAIN_TTL_AND_DATABASE_REQUIRED")
    if (
        not args.output_dir.is_absolute()
        or args.output_dir.parent.resolve() != args.output_dir.parent
    ):
        raise ValueError("NEW_CANONICAL_PRIVATE_OUTPUT_REQUIRED")
    args.output_dir.mkdir(mode=0o700)
    engine = create_mysql_engine(settings.mysql_settings())
    try:
        core.deadline(stop)
        with engine.connect() as connection:
            if (
                connection.execute(text("SELECT DATABASE()")).scalar_one()
                != core.F_DATABASE
            ):
                raise ValueError("ACTUAL_F_AUTH_STORE_REQUIRED")
        factory = SqlAlchemyUnitOfWorkFactory(engine)
        accounts = core.create_five(
            factory, settings, prefix=descriptor["account_prefix"], stop=stop
        )
        sessions = {
            "expired": core.issue(
                factory,
                settings,
                accounts[descriptor["expired_subject"]],
                ttl=60,
                stop=stop,
            )
        }
        sessions.update(
            {
                label: core.issue(
                    factory, settings, accounts[label], ttl=3600, stop=stop
                )
                for label in core.LABELS
            }
        )
        sessions["revocation"] = core.issue(
            factory,
            settings,
            accounts[descriptor["revocation_subject"]],
            ttl=3600,
            stop=stop,
        )
        expired_row = core.row_for_token(factory, sessions["expired"]["access_token"])
        while datetime.now(UTC) <= expired_row["expires_at"]:
            core.deadline(stop)
            time.sleep(0.2)
        expired_receipt = core.observe_natural_expiry(
            factory, settings, sessions["expired"], stop=stop
        )
        for label, session in sessions.items():
            if (
                label != "expired"
                and core.get_me(factory, settings, session, stop=stop)[0] != 200
            ):
                raise ValueError("ALL_SIX_NONEXPIRED_SESSIONS_MUST_REMAIN_ACTIVE")
        with factory() as uow:
            counts = {name: uow.gateway.count(name) for name in TABLES}
        if (
            counts["users"] != 5
            or counts["auth_sessions"] != 7
            or any(
                count
                for name, count in counts.items()
                if name not in {"users", "auth_sessions", "audit_events"}
            )
        ):
            raise ValueError(
                "EXACT_FIVE_USERS_SEVEN_SESSIONS_AND_EMPTY_BUSINESS_REQUIRED"
            )
        if (
            len({session["session_id"] for session in sessions.values()}) != 7
            or len({session["access_token"] for session in sessions.values()}) != 7
        ):
            raise ValueError("SEVEN_DISTINCT_REAL_SESSIONS_REQUIRED")
        packet = build_packet(descriptor, accounts, sessions, ca, expired_receipt)
        Draft202012Validator(
            json.loads(read(args.schema)), format_checker=FormatChecker()
        ).validate(packet)
        core.deadline(stop)
        sealed = crypto.functional(
            packet,
            descriptor["recipient_public_key_pem"],
            descriptor["recipient_public_key_sha256"],
        )
        core.deadline(stop)
        write(args.output_dir / "functional-material.T44FENV1", sealed)
        receipt = {
            "kind": "PUBLIC_T12_PROVIDER_MATERIAL_PREPARED_NOT_ADMISSION",
            "source_sha": SOURCE,
            "binding_sha256": BINDING,
            "descriptor_sha256": args.descriptor_sha256,
            "host_public_proof_sha256": descriptor["host_public_proof_sha256"],
            "sealed_file": str(args.output_dir / "functional-material.T44FENV1"),
            "sealed_bytes": len(sealed),
            "sealed_sha256": crypto.sha(sealed),
            "recipient_nonce": descriptor["recipient_nonce"],
            "recipient_public_key_sha256": descriptor["recipient_public_key_sha256"],
            "identities": 5,
            "distinct_sessions": 7,
            "revocation_session_still_active": True,
            "main_http_ttl_seconds": settings.session_ttl_seconds,
            "natural_expiry": expired_receipt,
            "actual_python_entry": "Runtime.execute(login)",
            "business_table_counts": counts,
            "no_scope_provisioned": True,
            "no_sut_grant": True,
            "private_output_printed": False,
        }
        write(
            args.output_dir / "receipt.PUBLIC.json", crypto.canonical(receipt) + b"\n"
        )
        print(crypto.canonical(receipt).decode(), flush=True)
    finally:
        engine.dispose()


if __name__ == "__main__":
    os.umask(0o077)
    try:
        main()
    except Exception:  # noqa: BLE001 -- Never print private DB/auth/crypto exceptions.
        print(
            '{"kind":"PUBLIC_T12_PROVIDER_FAILED_NO_SECRET_OUTPUT","no_retry":true}',
            flush=True,
        )
        raise SystemExit(1) from None
