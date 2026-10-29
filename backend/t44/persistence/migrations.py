"""Explicit MySQL 8.4 initialization. DDL is not transactional or automatically dropped."""

import re
from collections import defaultdict

from sqlalchemy import String, inspect, text
from sqlalchemy.exc import SQLAlchemyError

from .engine import validate_identifier
from .schema import DDL_SHA256, SCHEMA_VERSION, TABLES, ddl_text


class MigrationError(RuntimeError):
    pass


def _check_signature(expression):
    """Parse frozen CHECK grammar; preserve precedence, literals and function arguments."""
    source = str(expression).strip()
    pattern = re.compile(
        r"\s*(`[^`]+`|(?:(?:_utf8mb4|_ascii)\s*)?'(?:''|\\.|[^'])*'|[a-zA-Z_]\w*|\d+|<=|>=|<>|!=|[=<>+(),-])",
        re.I,
    )
    tokens, position = [], 0
    while position < len(source):
        match = pattern.match(source, position)
        if not match:
            return None
        lexeme = match[1]
        if lexeme.startswith("_") and "'" in lexeme:
            charset, quoted = lexeme.split("'", 1)
            if charset.strip().lower() == "_ascii" and not quoted.isascii():
                return None
            lexeme = "'" + quoted
        tokens.append(lexeme if lexeme.startswith("'") else lexeme.strip("`").lower())
        position = match.end()
    position = 0
    precedence = {
        operator: priority
        for priority, operators in enumerate(
            (
                ("or",),
                ("and",),
                ("=", "<>", "!=", "<", ">", "<=", ">=", "is", "in", "between"),
                ("+", "-"),
            ),
            start=1,
        )
        for operator in operators
    }

    def pop(expected=None):
        nonlocal position
        lexeme = tokens[position]
        position += 1
        if expected is not None and lexeme != expected:
            raise ValueError("Unsupported CHECK syntax")
        return lexeme

    def peek():
        return tokens[position] if position < len(tokens) else None

    def arguments():
        pop("(")
        values = [parse()]
        while peek() == ",":
            pop(",")
            values.append(parse())
        pop(")")
        return tuple(values)

    def parse(minimum=0):
        lexeme = pop()
        if lexeme == "(":
            left = parse()
            pop(")")
        else:
            left = ("call", lexeme, arguments()) if peek() == "(" else lexeme
        while peek() in precedence and precedence[peek()] >= minimum:
            operator = pop()
            priority = precedence[operator]
            if operator == "in":
                left = (operator, left, arguments())
            elif operator == "between":
                lower = parse(priority + 1)
                pop("and")
                left = (operator, left, lower, parse(priority + 1))
            elif operator == "is":
                negate = peek() == "not"
                if negate:
                    pop("not")
                pop("null")
                left = (operator, left, negate)
            else:
                left = ("<>" if operator == "!=" else operator, left, parse(priority + 1))
        return left

    try:
        result = parse()
        return result if position == len(tokens) else None
    except (IndexError, ValueError):
        return None


def _catalog_rows(engine):
    queries = {
        "tables": "SELECT TABLE_NAME,ENGINE,TABLE_COLLATION FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA=DATABASE()",
        "columns": "SELECT TABLE_NAME,COLUMN_NAME,DATA_TYPE,CHARACTER_MAXIMUM_LENGTH,DATETIME_PRECISION,COLUMN_TYPE,IS_NULLABLE,COLUMN_DEFAULT,EXTRA,CHARACTER_SET_NAME,COLLATION_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA=DATABASE()",
        "indexes": "SELECT TABLE_NAME,INDEX_NAME,SEQ_IN_INDEX,COLUMN_NAME,NON_UNIQUE,COLLATION,SUB_PART,INDEX_TYPE,IS_VISIBLE FROM INFORMATION_SCHEMA.STATISTICS WHERE TABLE_SCHEMA=DATABASE()",
        "checks": "SELECT t.TABLE_NAME,t.CONSTRAINT_NAME,c.CHECK_CLAUSE,t.ENFORCED FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS t JOIN INFORMATION_SCHEMA.CHECK_CONSTRAINTS c ON c.CONSTRAINT_SCHEMA=t.CONSTRAINT_SCHEMA AND c.CONSTRAINT_NAME=t.CONSTRAINT_NAME WHERE t.TABLE_SCHEMA=DATABASE() AND t.CONSTRAINT_TYPE='CHECK'",
        "foreigns": "SELECT k.TABLE_NAME,k.CONSTRAINT_NAME,k.ORDINAL_POSITION,k.COLUMN_NAME,k.REFERENCED_TABLE_SCHEMA,k.REFERENCED_TABLE_NAME,k.REFERENCED_COLUMN_NAME,r.UPDATE_RULE,r.DELETE_RULE,r.MATCH_OPTION FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE k JOIN INFORMATION_SCHEMA.REFERENTIAL_CONSTRAINTS r ON r.CONSTRAINT_SCHEMA=k.CONSTRAINT_SCHEMA AND r.CONSTRAINT_NAME=k.CONSTRAINT_NAME AND r.TABLE_NAME=k.TABLE_NAME WHERE k.TABLE_SCHEMA=DATABASE()",
    }
    with engine.connect() as connection:
        rows = {
            kind: [tuple(row) for row in connection.exec_driver_sql(sql)]
            for kind, sql in queries.items()
        }
    rows["columns"] = [
        (
            name,
            column,
            (
                "integer" if kind == "int" else kind,
                length if kind in ("varchar", "char", "binary") else None,
                "unsigned" in specification
                if kind
                in (
                    "int",
                    "tinyint",
                    "smallint",
                    "mediumint",
                    "bigint",
                    "decimal",
                    "float",
                    "double",
                )
                else None,
                precision if kind in ("datetime", "timestamp", "time") else None,
            ),
            nullable == "YES",
            str(default).strip("'\"") if default is not None else None,
            extra,
            charset,
            collation,
        )
        for name, column, kind, length, precision, specification, nullable, default, extra, charset, collation in rows[
            "columns"
        ]
    ]
    return rows


def _expected_rows():
    rows = {kind: [] for kind in ("tables", "columns", "indexes", "checks", "foreigns")}
    for name, table in TABLES.items():
        options = table.dialect_options["mysql"]
        rows["tables"].append((name, options["engine"], options["collate"]))
        for column in table.c:
            kind = column.type
            charset = (kind.charset or options["charset"]) if isinstance(kind, String) else None
            collation = (kind.collation or options["collate"]) if isinstance(kind, String) else None
            rows["columns"].append(
                (
                    name,
                    column.name,
                    (
                        kind.__class__.__name__.lower(),
                        *(getattr(kind, key, None) for key in ("length", "unsigned", "fsp")),
                    ),
                    column.nullable,
                    str(column.server_default.arg) if column.server_default is not None else None,
                    "auto_increment" if column.primary_key else "",
                    charset,
                    collation,
                )
            )
        for item in (*table.indexes, *table.constraints):
            kind = item.__class__.__name__
            if kind in ("Index", "UniqueConstraint", "PrimaryKeyConstraint"):
                key = "PRIMARY" if kind == "PrimaryKeyConstraint" else item.name
                for ordinal, column in enumerate(item.columns, start=1):
                    rows["indexes"].append(
                        (
                            name,
                            key,
                            ordinal,
                            column.name,
                            int(kind == "Index" and not item.unique),
                            "A",
                            None,
                            "BTREE",
                            "YES",
                        )
                    )
            elif kind == "CheckConstraint":
                rows["checks"].append((name, item.name, str(item.sqltext), "YES"))
            elif kind == "ForeignKeyConstraint":
                for ordinal, element in enumerate(item.elements, start=1):
                    rows["foreigns"].append(
                        (
                            name,
                            item.name,
                            ordinal,
                            element.parent.name,
                            element.column.table.schema,
                            element.column.table.name,
                            element.column.name,
                            "RESTRICT",
                            "RESTRICT",
                            "NONE",
                        )
                    )
    return rows


def _catalog_features(rows, database):
    grouped = {kind: defaultdict(list) for kind in rows}
    for kind, records in rows.items():
        for name, *record in records:
            grouped[kind][name].append(tuple(record))
    facts, conflicts = {}, []
    for name in TABLES:
        present = name in grouped["tables"]
        facts[f"{name}:missing_table"] = present
        if not present:
            continue
        columns = {column: values for column, *values in grouped["columns"][name]}
        facts[f"{name}:column_set"] = set(columns)
        for column, values in columns.items():
            for label, value in zip(("type", "nullable", "default"), values[:3], strict=True):
                facts[f"{name}.{column}:{label}"] = value
        indexes = defaultdict(dict)
        for key, ordinal, *values in grouped["indexes"][name]:
            if ordinal in indexes[key] and indexes[key][ordinal] != tuple(values):
                conflicts.append(f"{name}.{key}:index_catalog_conflict")
            indexes[key][ordinal] = tuple(values)
        indexes = {
            key: [values[ordinal] for ordinal in sorted(values)] for key, values in indexes.items()
        }
        facts[f"{name}:primary_key"] = [row[0] for row in indexes.get("PRIMARY", [])]
        for key, values in indexes.items():
            if key != "PRIMARY":
                facts[f"{name}.{key}:index_definition"] = [row[:-1] for row in values]
        facts[f"{name}:unique_set"] = {
            key
            for key, values in indexes.items()
            if key != "PRIMARY" and any(row[1] == 0 for row in values)
        }
        facts[f"{name}:foreign_key_definition"] = {
            (
                key,
                ordinal,
                column,
                None if schema == database else schema,
                parent,
                target,
                *(
                    "RESTRICT" if action.upper() in ("NO ACTION", "RESTRICT") else action.upper()
                    for action in actions[:2]
                ),
                actions[2],
            )
            for key, ordinal, column, schema, parent, target, *actions in grouped["foreigns"][name]
        }
        facts[f"{name}:check_definition"] = {
            key: _check_signature(expression) for key, expression, _ in grouped["checks"][name]
        }
    for name, engine, collation in rows["tables"]:
        facts[f"{name}:table_options"] = (engine, collation)
    for name, column, *values in rows["columns"]:
        facts[f"{name}.{column}:column_options"] = tuple(values[-3:])
    for name, key, ordinal, *values in rows["indexes"]:
        facts[f"{name}.{key}.{ordinal}:index_options"] = tuple(values)
    for name, key, _, enforced in rows["checks"]:
        facts[f"{name}.{key}:check_enforcement"] = (enforced,)
    return facts, conflicts


def _schema_defects(engine, *, native_only=False):
    database = getattr(getattr(engine, "url", None), "database", None)
    expected, _ = _catalog_features(_expected_rows(), database)
    actual, conflicts = _catalog_features(_catalog_rows(engine), database)
    native = (":table_options", ":column_options", ":index_options", ":check_enforcement")
    defects = []
    for key, value in expected.items():
        label = key.rsplit(":", 1)[1]
        if native_only and not key.endswith(native):
            continue
        if label == "check_definition" and None in value.values():
            raise MigrationError("Frozen CHECK grammar is unsupported")
        table = key.split(":", 1)[0].split(".", 1)[0]
        if not key.endswith(native) and label != "missing_table":
            if not actual.get(f"{table}:missing_table") or (
                label in ("type", "nullable", "default") and key not in actual
            ):
                continue
        if key not in actual or actual[key] != value:
            defects.append(key)
    return defects if native_only else defects + conflicts


def _catalog_defects(engine):
    return _schema_defects(engine, native_only=True)


def check_schema(engine) -> dict:
    defects = _schema_defects(engine)
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
            already_applied = "t44_schema_migrations" in existing
            if already_applied:
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
                    "Applied database structure differs from frozen v1"
                    if already_applied
                    else "Created schema failed the frozen field/index/constraint check"
                )
            if not already_applied:
                connection.execute(
                    text(
                        "UPDATE t44_schema_migrations SET state=2,applied_at=UTC_TIMESTAMP(6) WHERE id=1"
                    )
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
                    connection.execute(text("SELECT RELEASE_LOCK(:name)"), {"name": lock_name})
                    connection.commit()
                except SQLAlchemyError:
                    pass  # A lost connection releases its server-owned advisory lock.
