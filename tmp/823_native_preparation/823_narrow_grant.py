"""Narrow only the coordinator-created disposable principal's schema grant."""

import importlib.util
import json
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

spec = importlib.util.spec_from_file_location(
    "native_init", Path(__file__).with_name("823_initialize.py")
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
admin = json.loads(
    (module.PROJECT / ".agent-worktrees/.runtime/mysql-8.4/admin.json").read_text()
)
engine = create_engine(
    URL.create(
        "mysql+pymysql",
        username=admin["username"],
        password=admin["password"],
        query={"unix_socket": admin["socket"]},
    ),
    hide_parameters=True,
)
database, user = module.DATABASE, module.USER
target = module.RUNTIME / "independent-functional-db/grant-narrowing-receipt.json"
if target.exists() or target.is_symlink():
    raise ValueError("Receipt already exists")
try:
    with engine.begin() as connection:
        if connection.execute(text("SELECT @@partial_revokes")).scalar_one():
            raise ValueError("Explicit wildcard-grant semantics required")
        before = list(
            connection.execute(text(f"SHOW GRANTS FOR '{user}'@'127.0.0.1'")).scalars()
        )
        expected = {
            f"GRANT USAGE ON *.* TO `{user}`@`127.0.0.1`",
            f"GRANT SELECT, INSERT, UPDATE, DELETE ON `{database}`.* TO `{user}`@`127.0.0.1`",
        }
        if set(before) != expected:
            raise ValueError("Unexpected principal grant; no changes")
        escaped = database.replace("_", "\\_")
        connection.execute(
            text(
                f"GRANT SELECT, INSERT, UPDATE, DELETE ON `{escaped}`.* TO '{user}'@'127.0.0.1'"
            )
        )
        connection.execute(
            text(
                f"REVOKE SELECT, INSERT, UPDATE, DELETE ON `{database}`.* FROM '{user}'@'127.0.0.1'"
            )
        )
        after = list(
            connection.execute(text(f"SHOW GRANTS FOR '{user}'@'127.0.0.1'")).scalars()
        )
        if len(after) != 2 or not any(f"`{escaped}`.*" in item for item in after):
            raise AssertionError("Narrowing postcondition failed")
    module.write_private(
        target,
        {
            "principal": user,
            "before": before,
            "after": after,
            "status": "only newly created principal schema pattern narrowed",
            "existing_other_users_changed": False,
        },
    )
    print(
        json.dumps({"status": "narrowed", "principal": user, "grant_count": len(after)})
    )
finally:
    engine.dispose()
