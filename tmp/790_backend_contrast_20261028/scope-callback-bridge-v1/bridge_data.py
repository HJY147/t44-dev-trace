"""Product Python3.12/data network only: readonly verification and private credential seal."""

import argparse
import json
import os
import stat
from datetime import datetime, timezone
from pathlib import Path

import scope_crypto
from bridge_common import canonical, parse, read, require, reserve, sha, stamp, utc

UTC = timezone.utc  # noqa: UP017 -- shared parser conventions.


def verify_source(root, expected):
    rows = []
    for path in sorted(
        list((root / "t44").rglob("*")) + [root / "requirements.lock", root / "pyproject.toml"]
    ):
        info = path.lstat()
        require(
            not stat.S_ISLNK(info.st_mode)
            and (stat.S_ISDIR(info.st_mode) or stat.S_ISREG(info.st_mode)),
            "SPECIAL_SOURCE_OBJECT",
        )
        if path.is_file():
            rows.append(
                {
                    "path": "backend/" + path.relative_to(root).as_posix(),
                    "bytes": info.st_size,
                    "sha256": sha(path.read_bytes()),
                    "mode": stat.S_IMODE(info.st_mode),
                }
            )
    require(rows == expected, "EXACT_PRODUCT_SOURCE_REQUIRED")


def preflight(factory, request):
    scope_crypto.public_key(request["public_key_pem"])
    with factory() as uow:
        projects = uow.gateway.rows("projects", {"id": request["project_ids"]}, columns=("id",))
        require(
            {r["id"] for r in projects} == set(request["project_ids"]), "ACTUAL_PROJECTS_REQUIRED"
        )
        ids = request["iteration_ids"]
        if ids:
            rows = uow.gateway.rows("iterations", {"id": ids}, columns=("id", "project_id"))
            require(
                {r["id"] for r in rows} == set(ids)
                and all(r["project_id"] in request["project_ids"] for r in rows),
                "ACTUAL_ITERATION_OWNERSHIP_REQUIRED",
            )


def service_credential(factory, request, private_raw, clock):
    from t44.services.common import wire
    from t44.services.identity import token_digest

    meta = parse(private_raw)
    token = meta["access_token"]
    require(
        isinstance(token, str) and 32 <= len(token) <= 512, "ORIGINAL_OPAQUE_CREDENTIAL_REQUIRED"
    )
    with factory() as uow:
        rows = uow.gateway.rows("auth_sessions", {"token_hash": token_digest(token)}, limit=1)
        require(len(rows) == 1, "ACTUAL_SESSION_DIGEST_REQUIRED")
        session = rows[0]
        require(
            session["actor_kind"] == 2
            and session["user_id"] is None
            and session["revoked_at"] is None
            and session["expires_at"] > clock(),
            "ACTIVE_ORIGINAL_SERVICE_SESSION_REQUIRED",
        )
        require(
            session["scopes"] == ["escalation:write"]
            and len(session["project_ids"]) == len(request["project_ids"])
            and set(session["project_ids"]) == set(request["project_ids"]),
            "EXACT_ORIGINAL_SERVICE_SCOPE_REQUIRED",
        )
        identity = uow.gateway.get("service_accounts", session["service_account_id"])
        require(identity and identity["active"], "ACTIVE_ORIGINAL_SERVICE_IDENTITY_REQUIRED")
    return {
        "project_ids": request["project_ids"],
        "scope": ["escalation:write"],
        "token": token,
        "applied_to": ["scheduler"],
        "issued_at": wire(session["created_at"]),
        "expires_at": wire(session["expires_at"]),
    }


def main():
    from t44.persistence import SqlAlchemyUnitOfWorkFactory, create_mysql_engine
    from t44.settings import Settings

    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("preflight", "seal"))
    parser.add_argument("--control", type=Path, required=True)
    parser.add_argument("--control-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    control = parse(read(args.control, args.control_sha256))
    require(datetime.now(UTC) < stamp(control["deadline_utc"]), "DATA_DEADLINE_EXPIRED")
    settings = Settings.from_env()
    require(settings.mysql_settings().database == control["database"], "EXACT_F_AUTHSTORE_REQUIRED")
    verify_source(Path("/app/backend"), control["source_files"])
    engine = create_mysql_engine(settings.mysql_settings())
    try:
        factory = SqlAlchemyUnitOfWorkFactory(engine)
        preflight(factory, control["request"])
        if args.mode == "preflight":
            result = (
                canonical(
                    {
                        "kind": "PUBLIC_READONLY_SCOPE_PREFLIGHT",
                        "project_ids": control["request"]["project_ids"],
                        "private_output_printed": False,
                    }
                )
                + b"\n"
            )
        else:
            private_raw = read(Path("/run/scheduler-secrets/scheduler-token.json"), private=True)
            require(
                sha(private_raw) == control["credential_file_sha256"],
                "SAME_APPLIED_PRIVATE_FILE_REQUIRED",
            )
            credential = service_credential(
                factory, control["request"], private_raw, lambda: datetime.now(UTC)
            )
            require(datetime.now(UTC) < stamp(control["deadline_utc"]), "DATA_DEADLINE_EXPIRED")
            result = (
                canonical(
                    scope_crypto.scope(
                        control["request"],
                        credential,
                        control["request"]["context"],
                        utc(datetime.now(UTC)),
                    )
                )
                + b"\n"
            )
        reserve(args.output, result)
        print(
            json.dumps(
                {
                    "kind": "PUBLIC_DATA_SCOPE_COMPLETE",
                    "mode": args.mode,
                    "sha256": sha(result),
                    "bytes": len(result),
                    "private_output_printed": False,
                }
            )
        )
    finally:
        engine.dispose()


if __name__ == "__main__":
    os.umask(0o077)
    try:
        main()
    except Exception:  # noqa: BLE001 -- keep DB/token/key exceptions private.
        print('{"kind":"PUBLIC_DATA_SCOPE_FAILED","private_output_printed":false,"no_retry":true}')
        raise SystemExit(1) from None
