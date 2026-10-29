"""Explicit MySQL 8.4 initialization. DDL is not transactional or automatically dropped."""

import re

from sqlalchemy import String, inspect, text
from sqlalchemy.exc import SQLAlchemyError
from sqlglot import exp, parse
from sqlglot.errors import ParseError, TokenError

from .engine import validate_identifier
from .schema import DDL_SHA256, SCHEMA_VERSION, TABLES, ddl_text


class MigrationError(RuntimeError):
    pass


def _check_signature(expression):
    """Compare MySQL expression trees without optimizing literals or operator order."""
    source = str(expression).strip()
    lexeme = r"`[^`]+`|(?:(?:_utf8mb4|_ascii)\s*)?'(?:''|\\.|[^'])*'|[a-zA-Z_]\w*|\d+|<=|>=|<>|!=|[=<>+(),-]"
    if not re.fullmatch(rf"(?:\s*(?:{lexeme}))*", source, re.I):
        return None
    try:
        expressions = parse(source, read="mysql")
        if len(expressions) != 1 or expressions[0] is None:
            return None
        tree = expressions[0]
        for node in reversed(list(tree.walk())):
            if (
                not isinstance(node, (exp.Condition, exp.Identifier, exp.Introducer))
                or node.comments
            ):
                return None
            if isinstance(node, exp.Introducer) and (
                node.this.lower() not in ("_utf8mb4", "_ascii")
                or (node.this.lower() == "_ascii" and not node.expression.this.isascii())
            ):
                return None
            if isinstance(node, (exp.Identifier, exp.Anonymous)):
                node.set("this", node.this.lower())
                if isinstance(node, exp.Identifier):
                    node.set("quoted", False)
            if isinstance(node, (exp.Paren, exp.Introducer)):
                child = node.this if isinstance(node, exp.Paren) else node.expression
                if node.parent is None:
                    tree = child
                else:
                    node.replace(child)
        return tree
    except (ParseError, TokenError):
        return None


def _index_signature(index):
    options = index.get("dialect_options", {})
    sorting = {
        k: tuple(v for v in values if v.lower() != "asc")
        for k, values in index.get("column_sorting", {}).items()
    }
    return (
        tuple(index["column_names"]),
        bool(index.get("unique")),
        {k: v for k, v in sorting.items() if v},
        options.get("mysql_length"),
        (options.get("mysql_using") or "BTREE").upper(),
    )


def _column_signature(kind, nullable, default):
    return (
        kind.__class__.__name__.lower(),
        *(getattr(kind, field, None) for field in ("length", "unsigned", "fsp")),
        nullable,
        None if default is None else str(default).strip("'\""),
    )


def _foreign_signature(foreign, database):
    options = foreign.get("options", {})
    actions = tuple(
        "RESTRICT"
        if (options.get(key) or "RESTRICT").upper() in ("NO ACTION", "RESTRICT")
        else options[key].upper()
        for key in ("ondelete", "onupdate")
    )
    schema = foreign.get("referred_schema")
    return (
        tuple(foreign["constrained_columns"]),
        None if schema == database else schema,
        foreign["referred_table"],
        tuple(foreign["referred_columns"]),
        actions,
        {
            key: value
            for key, value in options.items()
            if key not in ("ondelete", "onupdate") and value is not None
        },
    )


def _catalog_defects(engine):
    """Audit native properties omitted by MySQL's SQLAlchemy reflection."""
    table_options, column_options, index_options, check_enforcement = {}, {}, {}, {}
    for name, table in TABLES.items():
        options = table.dialect_options["mysql"]
        table_options[(name,)] = (options["engine"], options["collate"])
        for column in table.c:
            charset = collation = None
            if isinstance(column.type, String):
                charset = column.type.charset or options["charset"]
                collation = column.type.collation or options["collate"]
            column_options[(name, column.name)] = (
                "auto_increment" if column.primary_key else "",
                charset,
                collation,
            )
        for index in (*table.indexes, *table.constraints):
            kind = index.__class__.__name__
            if kind in ("Index", "UniqueConstraint", "PrimaryKeyConstraint"):
                key = "PRIMARY" if kind == "PrimaryKeyConstraint" else index.name
                unique = kind != "Index" or index.unique
                for ordinal, column in enumerate(index.columns, start=1):
                    index_options[(name, key, ordinal)] = (
                        column.name,
                        int(not unique),
                        "A",
                        None,
                        "BTREE",
                        "YES",
                    )
            elif kind == "CheckConstraint":
                check_enforcement[(name, index.name)] = ("YES",)
    queries = {
        "table_options": (
            "SELECT TABLE_NAME,ENGINE,TABLE_COLLATION FROM INFORMATION_SCHEMA.TABLES "
            "WHERE TABLE_SCHEMA=DATABASE()",
            table_options,
        ),
        "column_options": (
            "SELECT TABLE_NAME,COLUMN_NAME,EXTRA,CHARACTER_SET_NAME,COLLATION_NAME "
            "FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA=DATABASE()",
            column_options,
        ),
        "index_options": (
            "SELECT TABLE_NAME,INDEX_NAME,SEQ_IN_INDEX,COLUMN_NAME,NON_UNIQUE,COLLATION,"
            "SUB_PART,INDEX_TYPE,IS_VISIBLE FROM INFORMATION_SCHEMA.STATISTICS "
            "WHERE TABLE_SCHEMA=DATABASE()",
            index_options,
        ),
        "check_enforcement": (
            "SELECT TABLE_NAME,CONSTRAINT_NAME,ENFORCED FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS "
            "WHERE TABLE_SCHEMA=DATABASE() AND CONSTRAINT_TYPE='CHECK'",
            check_enforcement,
        ),
    }
    defects = []
    with engine.connect() as connection:
        for label, (query, expected) in queries.items():
            width = len(next(iter(expected)))
            rows = connection.exec_driver_sql(query)
            actual = {tuple(row[:width]): tuple(row[width:]) for row in rows}
            defects.extend(
                f"{'.'.join(map(str, key))}:{label}"
                for key, value in expected.items()
                if actual.get(key) != value
            )
    return defects


def check_schema(engine) -> dict:
    inspector, defects = inspect(engine), []
    actual_tables = set(inspector.get_table_names())
    for name, expected in TABLES.items():
        if name not in actual_tables:
            defects.append(f"{name}:missing_table")
            continue
        columns = {
            c["name"]: _column_signature(c["type"], c["nullable"], c["default"])
            for c in inspector.get_columns(name)
        }
        if set(columns) != set(expected.c.keys()):
            defects.append(f"{name}:column_set")
        for c in expected.c:
            default = c.server_default.arg if c.server_default is not None else None
            if columns.get(c.name) != _column_signature(c.type, c.nullable, default):
                defects.append(f"{name}.{c.name}:column_definition")
        if inspector.get_pk_constraint(name)["constrained_columns"] != ["id"]:
            defects.append(f"{name}:primary_key")
        actual_keys = {x["name"]: _index_signature(x) for x in inspector.get_indexes(name)}
        for unique in inspector.get_unique_constraints(name):
            signature = _index_signature({**unique, "unique": True})
            if unique["name"] in actual_keys and actual_keys[unique["name"]] != signature:
                defects.append(f"{name}.{unique['name']}:index_catalog_conflict")
            actual_keys.setdefault(unique["name"], signature)
        keys = {
            x.name: (tuple(x.columns.keys()), getattr(x, "unique", True), {}, None, "BTREE")
            for x in (*expected.indexes, *expected.constraints)
            if x.__class__.__name__ in ("Index", "UniqueConstraint")
        }
        for key, signature in keys.items():
            if actual_keys.get(key) != signature:
                defects.append(f"{name}.{key}:index_definition")
        if {k for k, v in actual_keys.items() if v[1]} != {k for k, v in keys.items() if v[1]}:
            defects.append(f"{name}:unique_set")
        database = getattr(getattr(engine, "url", None), "database", None)
        foreigns = {
            x.name: (
                tuple(x.column_keys),
                x.referred_table.schema,
                x.referred_table.name,
                tuple(e.column.name for e in x.elements),
                ("RESTRICT", "RESTRICT"),
                {},
            )
            for x in expected.foreign_key_constraints
        }
        actual_foreigns = {
            x["name"]: _foreign_signature(x, database) for x in inspector.get_foreign_keys(name)
        }
        if actual_foreigns != foreigns:
            defects.append(f"{name}:foreign_key_definition")
        checks = {
            x.name: _check_signature(x.sqltext)
            for x in expected.constraints
            if x.__class__.__name__ == "CheckConstraint"
        }
        if None in checks.values():
            raise MigrationError("Frozen CHECK grammar is unsupported")
        if {
            x["name"]: _check_signature(x["sqltext"]) for x in inspector.get_check_constraints(name)
        } != checks:
            defects.append(f"{name}:check_definition")
    defects.extend(_catalog_defects(engine))
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

        def query(statement, parameters=None):
            return connection.execute(text(statement), parameters)

        lock_name = f"t44:migrate:{expected_database}"
        locked, step = False, 0
        try:
            server, database = query("SELECT VERSION(), DATABASE()").one()
            if not re.match(r"8\.4\.", server) or database != expected_database:
                raise MigrationError("MySQL 8.4 and the selected project database are required")
            locked = query("SELECT GET_LOCK(:name, 30)", {"name": lock_name}).scalar_one() == 1
            if not locked:
                raise MigrationError("Project migration lock is unavailable")
            existing = set(inspect(connection).get_table_names())
            already_applied = "t44_schema_migrations" in existing
            if already_applied:
                row = (
                    query("SELECT version, ddl_sha256, state FROM t44_schema_migrations WHERE id=1")
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
            else:
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
                query(
                    "INSERT INTO t44_schema_migrations(id,version,ddl_sha256,state) VALUES(1,:version,:digest,1)",
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
                    "Applied database structure differs from frozen v1"
                    if already_applied
                    else "Created schema failed the frozen field/index/constraint check"
                )
            if not already_applied:
                query(
                    "UPDATE t44_schema_migrations SET state=2,applied_at=UTC_TIMESTAMP(6) WHERE id=1"
                )
                connection.commit()
            return {
                "version": SCHEMA_VERSION,
                "sha256": DDL_SHA256,
                "already_applied": already_applied,
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
                    query("SELECT RELEASE_LOCK(:name)", {"name": lock_name})
                    connection.commit()
                except SQLAlchemyError:
                    pass  # A lost connection releases its server-owned advisory lock.
