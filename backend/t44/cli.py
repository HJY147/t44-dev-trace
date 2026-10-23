"""Explicit administrative commands; secrets are read privately and never printed."""

import argparse
import json
import os
import re
import secrets
import sys
from datetime import timedelta
from getpass import getpass

from t44.persistence import SqlAlchemyUnitOfWorkFactory, create_mysql_engine
from t44.services.common import Call, now, wire
from t44.services.identity import HASHER, token_digest
from t44.services.runtime import Runtime
from t44.settings import Settings


def _parser():
    parser = argparse.ArgumentParser(prog="python -m t44.cli")
    commands = parser.add_subparsers(dest="command", required=True)
    migrate = commands.add_parser("migrate")
    migrate.add_argument("--database", required=True)
    user = commands.add_parser("init-user")
    user.add_argument("--username", required=True)
    user.add_argument("--display-name", required=True)
    user.add_argument("--password-stdin", action="store_true")
    revoke = commands.add_parser("revoke-sessions")
    revoke.add_argument("--user-id", type=int, required=True)
    single = commands.add_parser("revoke-session")
    single.add_argument("--session-id", type=int, required=True)
    seed = commands.add_parser("seed-demo")
    for name, default in (
        ("projects", 40),
        ("tasks", 6000),
        ("dependencies", 9000),
        ("records", 15000),
    ):
        seed.add_argument("--" + name, type=int, default=default)
    service = commands.add_parser("service-token")
    service.add_argument("--name", required=True)
    service.add_argument("--project-id", type=int, action="append", required=True)
    service.add_argument("--token-file", required=True)
    return parser


def main(argv=None):
    args = _parser().parse_args(argv)
    try:
        settings = Settings.from_env()
        engine = create_mysql_engine(settings.mysql_settings())
        factory = SqlAlchemyUnitOfWorkFactory(engine)
        if args.command == "migrate":
            from t44.persistence.migrations import migrate

            result = migrate(engine, expected_database=args.database)
        elif args.command == "seed-demo":
            from t44.persistence.seed import seed_demo

            result = seed_demo(
                factory,
                **{k: getattr(args, k) for k in ("projects", "tasks", "dependencies", "records")},
            )
        elif args.command == "init-user":
            from t44.persistence.accounts import initialize_user

            if (
                not re.fullmatch(r"[A-Za-z0-9_.-]{1,64}", args.username)
                or not 1 <= len(args.display_name) <= 100
            ):
                raise ValueError("Invalid account identifiers")
            password = (
                sys.stdin.readline().rstrip("\r\n")
                if args.password_stdin
                else getpass("Password: ")
            )
            if not 1 <= len(password) <= 128:
                raise ValueError("Invalid password length")
            hashed = HASHER.hash(password)
            del password
            result = {
                "user_id": initialize_user(
                    factory,
                    username=args.username,
                    display_name=args.display_name,
                    password_hash=hashed,
                )
            }
        elif args.command in ("revoke-sessions", "revoke-session"):
            target = args.user_id if args.command == "revoke-sessions" else args.session_id
            if not 1 <= target <= 4294967295:
                raise ValueError("Invalid positive identifier")
            with factory() as uow:
                g = uow.gateway
                where = {"user_id": target} if args.command == "revoke-sessions" else {"id": target}
                rows = g.rows("auth_sessions", where, lock="update")
                timestamp = now()
                changed = sum(
                    g.update(
                        "auth_sessions",
                        {"id": r["id"], "revoked_at": None},
                        {"revoked_at": timestamp},
                    )
                    for r in rows
                )
                call = Call(args.command, secrets.token_hex(16), None)
                Runtime(factory, settings, None).audit(g, call)
            result = {"revoked_sessions": changed}
        else:
            if not re.fullmatch(r"[A-Za-z0-9_.-]{1,64}", args.name):
                raise ValueError("Invalid service identifier")
            # O_EXCL prevents overwriting an existing credential; file permissions are enforced.
            descriptor = os.open(args.token_file, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            try:
                with factory() as uow:
                    g, timestamp = uow.gateway, now()
                    projects = sorted(set(args.project_id))
                    if len(g.rows("projects", {"id": projects})) != len(projects):
                        raise ValueError("Project not found")
                    rows = g.rows("service_accounts", {"name": args.name}, lock="update", limit=1)
                    sid = (
                        rows[0]["id"]
                        if rows
                        else g.insert(
                            "service_accounts",
                            {"name": args.name, "active": 1, "created_at": timestamp},
                        )
                    )
                    if rows and not rows[0]["active"]:
                        raise ValueError("Service account is inactive")
                    token = secrets.token_urlsafe(32)
                    expiry = timestamp + timedelta(seconds=settings.session_ttl_seconds)
                    session_id = g.insert(
                        "auth_sessions",
                        {
                            "actor_kind": 2,
                            "user_id": None,
                            "service_account_id": sid,
                            "token_hash": token_digest(token),
                            "project_ids": projects,
                            "scopes": ["escalation:write"],
                            "expires_at": expiry,
                            "revoked_at": None,
                            "created_at": timestamp,
                        },
                    )
                    Runtime(factory, settings, None).audit(
                        g, Call("service-token", secrets.token_hex(16), None)
                    )
                with os.fdopen(descriptor, "w") as output:
                    descriptor = None
                    json.dump(
                        wire(
                            {"access_token": token, "session_id": session_id, "expires_at": expiry}
                        ),
                        output,
                    )
                    output.flush()
                    os.fsync(output.fileno())
                result = {"session_id": session_id, "credential_written": True}
            except BaseException:
                if descriptor is not None:
                    os.close(descriptor)
                os.unlink(args.token_file)
                raise
        print(json.dumps(wire(result), ensure_ascii=False))
        return 0
    except Exception:
        # Database exceptions/configuration may contain secrets; report only an operational code.
        print(json.dumps({"error": "COMMAND_FAILED", "command": args.command}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
