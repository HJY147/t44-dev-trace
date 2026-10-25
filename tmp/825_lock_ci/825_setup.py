"""Only disposable service setup; application credentials remain schema-local CRUD."""

import os
import sys

from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
from importlib import import_module

admission = import_module("825_admission")
database = admission.require_environment(sys.argv[1], os.environ)
engine = create_engine(
    URL.create(
        "mysql+pymysql",
        username="root",
        password="diag-root-disposable",
        host="127.0.0.1",
        port=3306,
        database=database,
    )
)
try:
    from t44.persistence.migrations import migrate

    result = migrate(engine, expected_database=database)
    if not result.get("passed"):
        raise RuntimeError("Disposable migration rejected")
    with engine.begin() as connection:
        connection.execute(
            text(f"REVOKE ALL PRIVILEGES ON `{database}`.* FROM 't44'@'%'")
        )
        connection.execute(
            text(f"GRANT SELECT, INSERT, UPDATE, DELETE ON `{database}`.* TO 't44'@'%'")
        )
        for table in ("data_locks", "data_lock_waits", "threads"):
            connection.execute(
                text(f"GRANT SELECT ON performance_schema.{table} TO 't44'@'%'")
            )
    print(
        "Fresh schema migrated; disposable diagnostic principal granted CRUD and three P_S SELECTs"
    )
finally:
    engine.dispose()
