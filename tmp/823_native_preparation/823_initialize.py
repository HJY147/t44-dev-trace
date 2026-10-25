"""Coordinator-only explicit new-schema preparation; never print credentials."""

import hashlib
import json
import os
import secrets
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

PROJECT = Path("/Users/yang/Desktop/nothing/软件开发大作业")
RUNTIME = PROJECT / ".agent-worktrees/.runtime/continuation-20261025"
DATABASE = USER = "t44_i829_20261025"
BASE = "ade5e4c1998b4c2f014afde8c011645c6c5a7412"


def write_private(path, value):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "w") as stream:
        json.dump(value, stream, indent=2)
        stream.write("\n")


def main():
    from sqlalchemy import create_engine, text
    from sqlalchemy.engine import URL
    from t44.persistence import SqlAlchemyUnitOfWorkFactory
    from t44.persistence.accounts import initialize_user
    from t44.persistence.migrations import migrate
    from t44.services.identity import HASHER

    source = Path(__file__).resolve().parents[2]
    # Identity/migration bytes must remain the original reviewed baseline.
    for name in (
        "backend/t44/persistence/migrations.py",
        "backend/t44/persistence/schema.py",
        "backend/t44/persistence/accounts.py",
        "backend/t44/services/identity.py",
    ):
        expected = subprocess.check_output(
            ["git", "show", f"{BASE}:{name}"], cwd=source
        )
        if (source / name).read_bytes() != expected:
            raise ValueError("Initialization source mismatch")
    for path in (RUNTIME, PROJECT / ".agent-worktrees/.runtime/mysql-8.4"):
        if path.is_symlink() or path.stat().st_mode & 0o077:
            raise ValueError("Private runtime required")
    admin_path = PROJECT / ".agent-worktrees/.runtime/mysql-8.4/admin.json"
    if admin_path.is_symlink() or admin_path.stat().st_mode & 0o077:
        raise ValueError("Private explicit admin credential required")
    admin = json.loads(admin_path.read_text())
    socket = Path(admin["socket"])
    if not socket.resolve().is_relative_to(
        PROJECT / ".agent-worktrees/.runtime/mysql-8.4"
    ):
        raise ValueError("Unexpected admin socket")
    target = RUNTIME / "independent-functional-db"
    target.mkdir(mode=0o700, exist_ok=False)
    root_url = URL.create(
        "mysql+pymysql",
        username=admin["username"],
        password=admin["password"],
        query={"unix_socket": str(socket)},
    )
    engine = create_engine(root_url, hide_parameters=True)
    report = {
        "database": DATABASE,
        "user": USER,
        "initialization_source": BASE,
        "started": datetime.now(UTC).isoformat(),
        "changes": [],
        "formal_acceptance": False,
    }
    try:
        with engine.connect() as connection:
            before = list(connection.execute(text("SHOW DATABASES")).scalars())
            users = [
                list(r)
                for r in connection.execute(
                    text("SELECT User,Host FROM mysql.user ORDER BY User,Host")
                )
            ]
            if DATABASE in before or any(r[0] == USER for r in users):
                raise ValueError("New schema/principal collision")
            report["before_schema_inventory_sha256"] = hashlib.sha256(
                json.dumps(before).encode()
            ).hexdigest()
            report["before_principal_inventory_sha256"] = hashlib.sha256(
                json.dumps(users).encode()
            ).hexdigest()
        password = secrets.token_urlsafe(32)
        write_private(
            target / "app-credentials.json",
            {
                "username": USER,
                "password": password,
                "database": DATABASE,
                "host": "127.0.0.1",
                "port": 13306,
            },
        )
        with engine.begin() as connection:
            connection.execute(
                text(
                    f"CREATE DATABASE `{DATABASE}` CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci"
                )
            )
            report["changes"].append("new named schema created")
            connection.exec_driver_sql(
                f"CREATE USER '{USER}'@'127.0.0.1' IDENTIFIED BY %s", (password,)
            )
            connection.execute(
                text(
                    f"GRANT SELECT, INSERT, UPDATE, DELETE ON `{DATABASE}`.* TO '{USER}'@'127.0.0.1'"
                )
            )
            report["changes"].append("new named CRUD-only principal created")
        migration = create_engine(root_url.set(database=DATABASE), hide_parameters=True)
        try:
            report["migration"] = migrate(migration, expected_database=DATABASE)
        finally:
            migration.dispose()
        app_url = URL.create(
            "mysql+pymysql",
            username=USER,
            password=password,
            host="127.0.0.1",
            port=13306,
            database=DATABASE,
        )
        app = create_engine(app_url, hide_parameters=True)
        identities = {}
        try:
            factory = SqlAlchemyUnitOfWorkFactory(app)
            for role in ("m", "d", "d2", "r", "x"):
                secret = secrets.token_urlsafe(24)
                username = "i829_" + role
                uid = initialize_user(
                    factory,
                    username=username,
                    display_name="Synthetic " + role,
                    password_hash=HASHER.hash(secret),
                )
                identities[role] = {
                    "username": username,
                    "password": secret,
                    "user_id": uid,
                }
            with app.connect() as connection:
                report["app_grants"] = list(
                    connection.execute(text("SHOW GRANTS")).scalars()
                )
        finally:
            app.dispose()
        write_private(target / "identities.json", identities)
        write_private(
            target / "application-env.json",
            {
                "DATABASE_URL": app_url.render_as_string(hide_password=False),
                "T44_DATABASE": DATABASE,
                "T44_SESSION_TTL_SECONDS": "3600",
            },
        )
        with engine.connect() as connection:
            after = list(connection.execute(text("SHOW DATABASES")).scalars())
            after_users = [
                list(r)
                for r in connection.execute(
                    text("SELECT User,Host FROM mysql.user ORDER BY User,Host")
                )
            ]
            if set(after) - set(before) != {DATABASE} or set(before) - set(after):
                raise AssertionError("Unexpected schema inventory change")
            if {tuple(r) for r in after_users} - {tuple(r) for r in users} != {
                (USER, "127.0.0.1")
            }:
                raise AssertionError("Unexpected principal additions")
            if {tuple(r) for r in users} - {tuple(r) for r in after_users}:
                raise AssertionError("Existing principal removed")
        report.update(
            status="prepared; no projects, service token or application process started",
            synthetic_human_accounts=len(identities),
            protected_inventory_preserved=True,
        )
    except BaseException as error:  # noqa: BLE001 -- sanitize every failure before secret-bearing traceback
        report.update(status="failed retained", exception_class=type(error).__name__)
        raise RuntimeError(
            "Initialization failed; sanitized private receipt retained"
        ) from None
    finally:
        engine.dispose()
        report["ended"] = datetime.now(UTC).isoformat()
        write_private(target / "preparation-receipt.json", report)
    print(
        json.dumps(
            {
                "status": report["status"],
                "database": DATABASE,
                "accounts": len(identities),
            }
        )
    )


if __name__ == "__main__":
    try:
        main()
    except BaseException as error:  # noqa: BLE001 -- sanitize every failure before secret-bearing traceback
        print(
            json.dumps({"status": "failed", "exception_class": type(error).__name__}),
            file=sys.stderr,
        )
        sys.exit(1)
