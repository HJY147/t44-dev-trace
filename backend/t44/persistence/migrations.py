"""Explicit MySQL 8.4 initialization. DDL is not transactional or automatically dropped."""

import hashlib
import re

from sqlalchemy import inspect, text
from sqlalchemy.exc import SQLAlchemyError

from .engine import validate_identifier
from .schema import DDL_SHA256, SCHEMA_VERSION, TABLES, ddl_text


class MigrationError(RuntimeError):
    pass


def check_schema(engine) -> dict:
    inspector, defects = inspect(engine), []
    actual_tables = set(inspector.get_table_names())
    for name, expected in TABLES.items():
        if name not in actual_tables:
            defects.append(f"{name}:missing_table")
            continue
        columns = {c["name"]: c for c in inspector.get_columns(name)}
        if set(columns) != set(expected.c.keys()):
            defects.append(f"{name}:column_set")
        for c in expected.c:
            actual = columns.get(c.name)
            if actual is None:
                continue
            native = actual["type"]

            def signature(kind):
                return (
                    kind.__class__.__name__.lower(),
                    getattr(kind, "length", None),
                    getattr(kind, "unsigned", None),
                    getattr(kind, "fsp", None),
                )

            if signature(native) != signature(c.type):
                defects.append(f"{name}.{c.name}:type")
            if actual["nullable"] != c.nullable:
                defects.append(f"{name}.{c.name}:nullable")
            expected_default = str(c.server_default.arg) if c.server_default is not None else None
            actual_default = (
                str(actual["default"]).strip("'\"") if actual["default"] is not None else None
            )
            if actual_default != expected_default:
                defects.append(f"{name}.{c.name}:default")
        if inspector.get_pk_constraint(name)["constrained_columns"] != ["id"]:
            defects.append(f"{name}:primary_key")
        actual_keys = {x["name"] for x in inspector.get_indexes(name)}
        actual_keys |= {x["name"] for x in inspector.get_unique_constraints(name)}
        expected_keys = {x.name for x in expected.indexes}
        expected_keys |= {
            x.name for x in expected.constraints if x.__class__.__name__ == "UniqueConstraint"
        }
        if not expected_keys <= actual_keys:
            defects.append(f"{name}:indexes")
        actual_constraints = {x["name"] for x in inspector.get_foreign_keys(name)}
        actual_constraints |= {x["name"] for x in inspector.get_check_constraints(name)}
        expected_constraints = {
            x.name
            for x in expected.constraints
            if x.__class__.__name__ in ("ForeignKeyConstraint", "CheckConstraint")
        }
        if not expected_constraints <= actual_constraints:
            defects.append(f"{name}:constraints")
    return {
        "tables": len(TABLES),
        "columns": sum(len(t.c) for t in TABLES.values()),
        "defects": defects,
        "passed": not defects,
    }


def migrate(engine, *, expected_database: str) -> dict:
    validate_identifier(expected_database)
    if engine.dialect.name != "mysql" or engine.url.database != expected_database:
        raise MigrationError("Explicit matching MySQL project database is required")
    sql = ddl_text()  # Verify the packaged frozen checksum before touching the database.
    digest = bytes.fromhex(DDL_SHA256)
    with engine.connect() as connection:
        lock_name = f"t44:migrate:{expected_database}"
        locked, step = False, 0
        try:
            server, database = connection.execute(text("SELECT VERSION(), DATABASE()")).one()
            if not re.match(r"8\.4\.", server) or database != expected_database:
                raise MigrationError("MySQL 8.4 and the selected project database are required")
            locked = (
                connection.execute(
                    text("SELECT GET_LOCK(:name, 30)"), {"name": lock_name}
                ).scalar_one()
                == 1
            )
            if not locked:
                raise MigrationError("Project migration lock is unavailable")
            existing = set(inspect(connection).get_table_names())
            if "t44_schema_migrations" in existing:
                row = (
                    connection.execute(
                        text(
                            "SELECT version, ddl_sha256, state FROM t44_schema_migrations WHERE id=1"
                        )
                    )
                    .mappings()
                    .one_or_none()
                )
                if (
                    not row
                    or row["version"] != SCHEMA_VERSION
                    or row["ddl_sha256"] != digest
                    or row["state"] != 2
                ):
                    raise MigrationError(
                        "Migration version/checksum is incompatible or incomplete; no destructive repair"
                    )
                report = check_schema(engine)
                if not report["passed"]:
                    raise MigrationError("Applied database structure differs from frozen v1")
                return {
                    "version": SCHEMA_VERSION,
                    "sha256": DDL_SHA256,
                    "already_applied": True,
                    **report,
                }
            if existing:
                raise MigrationError(
                    "Initial migration requires an empty explicitly selected project schema"
                )
            connection.commit()
            connection.exec_driver_sql(
                "CREATE TABLE t44_schema_migrations (id INT UNSIGNED PRIMARY KEY, "
                "version INT UNSIGNED NOT NULL, ddl_sha256 BINARY(32) NOT NULL, "
                "state TINYINT UNSIGNED NOT NULL, applied_at DATETIME(6) NULL) ENGINE=InnoDB"
            )
            connection.execute(
                text(
                    "INSERT INTO t44_schema_migrations(id,version,ddl_sha256,state) VALUES(1,:version,:digest,1)"
                ),
                {"version": SCHEMA_VERSION, "digest": digest},
            )
            connection.commit()
            executable = re.sub(r"--[^\n]*", "", sql)
            for statement in executable.split(";"):
                if statement.strip():
                    step += 1
                    connection.exec_driver_sql(statement.strip())
                    connection.commit()  # MySQL DDL implicitly commits; do not pretend rollback can undo it.
            report = check_schema(engine)
            if not report["passed"]:
                raise MigrationError(
                    "Created schema failed the frozen field/index/constraint check"
                )
            connection.execute(
                text(
                    "UPDATE t44_schema_migrations SET state=2,applied_at=UTC_TIMESTAMP(6) WHERE id=1"
                )
            )
            connection.commit()
            return {
                "version": SCHEMA_VERSION,
                "sha256": hashlib.sha256(sql.encode()).hexdigest(),
                "already_applied": False,
                **report,
            }
        except SQLAlchemyError as error:
            code = error.orig.args[0] if getattr(error, "orig", None) and error.orig.args else None
            raise MigrationError(
                f"Migration failed at statement {step}, driver code {code}; schema may be partial, no automatic drop/repair"
            ) from None
        finally:
            if locked:
                try:
                    connection.execute(text("SELECT RELEASE_LOCK(:name)"), {"name": lock_name})
                    connection.commit()
                except SQLAlchemyError:
                    pass  # A lost connection releases its server-owned advisory lock.
