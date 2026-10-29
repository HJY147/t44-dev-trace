"""Create only this run's named empty performance schema and CRUD principal."""

import hashlib
import json
import os
import secrets
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
from t44.persistence.migrations import migrate

PROJECT = Path("/Users/yang/Desktop/nothing/软件开发大作业")
DATABASE = USER = "t44_p829_20261025"
TARGET = PROJECT / ".agent-worktrees/.runtime/continuation-20261025/performance-db"


def save(name, data):
    fd = os.open(
        TARGET / name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600
    )
    with os.fdopen(fd, "w") as stream:
        json.dump(data, stream, indent=2)
        stream.write("\n")


def main():
    admin_file = PROJECT / ".agent-worktrees/.runtime/mysql-8.4/admin.json"
    if admin_file.is_symlink() or admin_file.stat().st_mode & 0o077:
        raise ValueError("Explicit private admin credential required")
    admin = json.loads(admin_file.read_text())
    if not Path(admin["socket"]).resolve().is_relative_to(admin_file.parent):
        raise ValueError("Unexpected admin socket")
    TARGET.mkdir(mode=0o700, exist_ok=False)
    root = URL.create(
        "mysql+pymysql",
        username=admin["username"],
        password=admin["password"],
        query={"unix_socket": admin["socket"]},
    )
    engine = create_engine(root, hide_parameters=True)
    report = {
        "database": DATABASE,
        "user": USER,
        "data_rows_inserted": 0,
        "changes": [],
    }
    try:
        with engine.begin() as connection:
            before = list(connection.execute(text("SHOW DATABASES")).scalars())
            report["before_inventory_sha256"] = hashlib.sha256(
                json.dumps(before).encode()
            ).hexdigest()
            if (
                DATABASE in before
                or connection.execute(
                    text("SELECT COUNT(*) FROM mysql.user WHERE User=:user"),
                    {"user": USER},
                ).scalar_one()
            ):
                raise ValueError("Schema/principal collision")
            if connection.execute(text("SELECT @@partial_revokes")).scalar_one():
                raise ValueError("Explicit wildcard semantics required")
            password = secrets.token_urlsafe(32)
            app_url = URL.create(
                "mysql+pymysql",
                username=USER,
                password=password,
                host="127.0.0.1",
                port=13306,
                database=DATABASE,
            )
            save(
                "application-env.json",
                {
                    "DATABASE_URL": app_url.render_as_string(hide_password=False),
                    "T44_DATABASE": DATABASE,
                    "T44_SESSION_TTL_SECONDS": "3600",
                },
            )
            connection.execute(
                text(
                    f"CREATE DATABASE `{DATABASE}` CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci"
                )
            )
            report["changes"].append("new named schema created")
            connection.execute(
                text(f"CREATE USER '{USER}'@'127.0.0.1' IDENTIFIED BY :password"),
                {"password": password},
            )
            escaped = DATABASE.replace("_", "\\_")
            connection.execute(
                text(
                    f"GRANT SELECT, INSERT, UPDATE, DELETE ON `{escaped}`.* TO '{USER}'@'127.0.0.1'"
                )
            )
            report["changes"].append("new exact schema CRUD-only principal created")
        migration = create_engine(root.set(database=DATABASE), hide_parameters=True)
        try:
            report["migration"] = migrate(migration, expected_database=DATABASE)
        finally:
            migration.dispose()
        with engine.connect() as connection:
            after = set(connection.execute(text("SHOW DATABASES")).scalars())
            if after - set(before) != {DATABASE} or set(before) - after:
                raise AssertionError("Unexpected schema change")
            report["grants"] = list(
                connection.execute(
                    text(f"SHOW GRANTS FOR '{USER}'@'127.0.0.1'")
                ).scalars()
            )
        report["status"] = (
            "fresh empty performance schema prepared; no fixture or SUT launched"
        )
    except BaseException as error:  # noqa: BLE001 -- redact secret-bearing driver exceptions
        report.update(status="failed retained", exception_class=type(error).__name__)
        raise RuntimeError(
            "Preparation failed; sanitized private receipt retained"
        ) from None
    finally:
        engine.dispose()
        save("preparation-receipt.json", report)
    print(json.dumps({"database": DATABASE, "status": report["status"]}))


if __name__ == "__main__":
    main()
