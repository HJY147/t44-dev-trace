"""Explicit, isolated SQLGlot experiment; no dependency/import or DB work during collection."""

import argparse
import hashlib
import json
from pathlib import Path

sg = ex = None
allowed = set()


def expression(sql):
    """Strict frozen-expression subset; parse_one alone would drop later statements."""
    if any(token.comments for token in sg.tokenize(sql, read="mysql")):
        raise ValueError("CHECK comments are outside the frozen comparison grammar")
    trees = sg.parse(sql, read="mysql", error_level=sg.ErrorLevel.RAISE)
    if len(trees) != 1 or trees[0] is None:
        raise ValueError("Exactly one CHECK expression is required")
    return canonical(trees[0])


def canonical(node):
    if isinstance(node, ex.Paren):
        return canonical(node.this)  # Tree children already retain grouping/precedence.
    if isinstance(node, ex.Introducer):
        value = node.expression
        if node.this.lower() not in ("_ascii", "_utf8mb4") or not isinstance(value, ex.Literal):
            raise ValueError("Unsupported character introducer")
        if node.this.lower() == "_ascii" and not value.this.isascii():
            raise ValueError("Non-ASCII literal cannot normalize as ASCII")
        return canonical(value)
    if isinstance(node, (ex.Identifier, ex.Var)):
        return (type(node).__name__, node.name.lower())
    if isinstance(node, ex.Expression):
        if allowed and type(node).__name__ not in allowed:
            raise ValueError(f"Unsupported comparison node: {type(node).__name__}")
        return (type(node).__name__, tuple(
            (key, canonical(value)) for key, value in sorted(node.args.items())
            if value is not None
        ))
    if isinstance(node, list):
        return tuple(canonical(value) for value in node)
    return node


def index_columns(expressions):
    result = []
    for item in expressions:
        descending = bool(item.args.get("desc")) if isinstance(item, ex.Ordered) else False
        item = item.this if isinstance(item, ex.Ordered) else item
        prefix = item.expression.this if isinstance(item, ex.ColumnPrefix) else None
        result.append((item.name, prefix, descending))
    return tuple(result)


def add_constraint(catalog, part):
    if isinstance(part, ex.PrimaryKey):
        catalog["pk"] = tuple(item.name for item in part.expressions)
    elif isinstance(part, (ex.UniqueColumnConstraint, ex.IndexColumnConstraint)):
        unique = isinstance(part, ex.UniqueColumnConstraint)
        schema = part.this if unique else part
        options = part.args.get("options") or []
        using = next((item.args["using"] for item in options if item.args.get("using")), None)
        using = using or part.args.get("index_type") or "BTREE"
        catalog["indexes"][schema.name] = (
            unique, index_columns(schema.expressions), str(using).upper(), part.args.get("kind"),
        )
    elif isinstance(part, ex.Constraint):
        for kind in part.expressions:
            if isinstance(kind, ex.ForeignKey):
                reference = kind.args["reference"]
                target = reference.this
                options = reference.args.get("options") or []
                actions = []
                for action in ("ON DELETE", "ON UPDATE"):
                    value = next((s.removeprefix(action).strip() for s in options if s.startswith(action)), "RESTRICT")
                    actions.append("RESTRICT" if value == "NO ACTION" else value)
                catalog["foreigns"][part.name] = (
                    tuple(item.name for item in kind.expressions), target.this.db or None,
                    target.this.name, tuple(item.name for item in target.expressions), tuple(actions),
                )
            elif isinstance(kind, ex.CheckColumnConstraint):
                catalog["checks"][part.name] = expression(kind.this.sql(dialect="mysql"))
            else:
                raise ValueError(f"Unsupported constraint: {kind}")
    else:
        raise ValueError(f"Unsupported DDL item: {type(part).__name__}")


def ddl_catalog(sql):
    trees = sg.parse(sql, read="mysql", error_level=sg.ErrorLevel.RAISE)
    result = {}
    for tree in trees:
        if isinstance(tree, ex.Create) and tree.args.get("kind") == "TABLE":
            if not isinstance(tree.this, ex.Schema):
                raise ValueError("CREATE TABLE must contain a schema, not opaque SQL")
            properties = tree.args.get("properties")
            if any(type(p).__name__ not in {"EngineProperty", "CharacterSetProperty", "CollateProperty"}
                   for p in properties.expressions):
                raise ValueError("Additional table properties need an explicit adapter")
            table = dict(columns={}, indexes={}, foreigns={}, checks={}, pk=(), table_options=tuple(
                sorted((type(p).__name__, p.this.name.lower()) for p in properties.expressions)
            ))
            result[tree.this.this.name] = table
            for part in tree.this.expressions:
                if not isinstance(part, ex.ColumnDef):
                    add_constraint(table, part)
                    continue
                constraints = {type(c.kind).__name__: c.kind for c in part.constraints}
                if set(constraints) - {
                    "DefaultColumnConstraint", "CharacterSetColumnConstraint", "CollateColumnConstraint",
                    "NotNullColumnConstraint", "AutoIncrementColumnConstraint",
                }:
                    raise ValueError("Additional column semantics need an explicit adapter")
                default = constraints.get("DefaultColumnConstraint")
                charset = constraints.get("CharacterSetColumnConstraint")
                collate = constraints.get("CollateColumnConstraint")
                not_null = constraints.get("NotNullColumnConstraint")
                table["columns"][part.name] = (
                    part.args["kind"].sql(dialect="mysql"),
                    not_null is None or bool(not_null.args.get("allow_null")),
                    default.this.sql(dialect="mysql") if default else None,
                    "AutoIncrementColumnConstraint" in constraints,
                    charset.this.name if charset else None, collate.this.name if collate else None,
                )
        elif isinstance(tree, ex.Alter):
            for action in tree.args["actions"]:
                if not isinstance(action, ex.AddConstraint):
                    raise ValueError("Only frozen ADD CONSTRAINT is supported")
                for part in action.expressions:
                    add_constraint(result[tree.this.name], part)
        else:
            raise ValueError(f"Opaque/unsupported DDL: {type(tree).__name__}")
    return result


def legacy_catalog(tables, dialect):
    """Independent old parser's metadata from the authoritative SQL, never actual reflection."""
    result = {}
    for name, table in tables.items():
        item = dict(columns={}, indexes={}, foreigns={}, checks={}, pk=("id",), table_options=tuple(sorted(
            (kind, table.kwargs[key].lower()) for kind, key in (
                ("EngineProperty", "mysql_engine"), ("CharacterSetProperty", "mysql_charset"),
                ("CollateProperty", "mysql_collate"),
            )
        )))
        result[name] = item
        for column in table.c:
            kind = column.type.copy()
            charset, collate = getattr(kind, "charset", None), getattr(kind, "collation", None)
            if charset:
                kind.charset = kind.collation = None
            sql_type = ex.DataType.build(kind.compile(dialect=dialect), dialect="mysql").sql(dialect="mysql")
            default = str(column.server_default.arg) if column.server_default is not None else None
            item["columns"][column.name] = (sql_type, column.nullable, default, column.primary_key, charset, collate)
        for index in table.indexes:
            item["indexes"][index.name] = (False, tuple((c.name, None, False) for c in index.columns), "BTREE", None)
        for constraint in table.constraints:
            kind = type(constraint).__name__
            if kind == "UniqueConstraint":
                item["indexes"][constraint.name] = (True, tuple((c.name, None, False) for c in constraint.columns), "BTREE", None)
            elif kind == "ForeignKeyConstraint":
                item["foreigns"][constraint.name] = (
                    tuple(c.name for c in constraint.columns), None, constraint.referred_table.name,
                    tuple(e.column.name for e in constraint.elements), ("RESTRICT", "RESTRICT"),
                )
            elif kind == "CheckConstraint":
                item["checks"][constraint.name] = expression(str(constraint.sqltext))
    return result


def main():
    global sg, ex, allowed
    import sqlglot
    from sqlalchemy.dialects import mysql
    from sqlglot import exp
    from t44.persistence.migrations import _check_signature
    from t44.persistence.schema import TABLES

    sg, ex = sqlglot, exp
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    sql = Path("specs/database/schema.sql").read_text()
    assert hashlib.sha256(sql.encode()).hexdigest() == "c0e740b203a85117fb125c578ab61401275bbe46ea80c629869c6cff39424bc4"
    checks = [c for t in TABLES.values() for c in t.constraints if type(c).__name__ == "CheckConstraint"]
    allowed = {type(n).__name__ for c in checks for n in sg.parse_one(str(c.sqltext), read="mysql").walk()}
    baseline = ddl_catalog(sql)
    old = legacy_catalog(TABLES, mysql.dialect())
    outcomes = []

    def record(name, condition, detail=None):
        outcomes.append(dict(name=name, passed=bool(condition), detail=detail))

    record("authoritative18/226", len(baseline) == 18 and sum(len(t["columns"]) for t in baseline.values()) == 226)
    for component in ("columns", "indexes", "foreigns", "checks", "pk", "table_options"):
        differences = [name for name in baseline if baseline[name][component] != old[name][component]]
        record("old-vs-AST:" + component, not differences, differences)
    roundtrip = [c.name for c in checks if _check_signature(str(c.sqltext)) != _check_signature(
        sg.parse_one(str(c.sqltext), read="mysql").sql(dialect="mysql")
    )]
    record("old-CHECK-reference:59-roundtrips", not roundtrip, roundtrip)
    candidate_roundtrip = [c.name for c in checks if expression(str(c.sqltext)) != expression(
        sg.parse_one(str(c.sqltext), read="mysql").sql(dialect="mysql")
    )]
    record("candidate-CHECK-AST:59-roundtrips", not candidate_roundtrip, candidate_roundtrip)
    mutations = [
        ("type", "display_name VARCHAR(100)", "display_name VARCHAR(101)"),
        ("unsigned", "id INT UNSIGNED", "id INT"),
        ("datetime-precision", "created_at DATETIME(6)", "created_at DATETIME(3)"),
        ("nullable", "display_name VARCHAR(100) NOT NULL", "display_name VARCHAR(100) NULL"),
        ("default", "active TINYINT UNSIGNED NOT NULL DEFAULT 1", "active TINYINT UNSIGNED NOT NULL DEFAULT 0"),
        ("index-order", "ix_tasks_project_state (project_id,state,id)", "ix_tasks_project_state (state,project_id,id)"),
        ("unique", "UNIQUE KEY uq_users_username", "KEY uq_users_username"),
        ("index-prefix", "uq_users_username (username)", "uq_users_username (username(10))"),
        ("index-type", "ix_tasks_project_state (project_id,state,id)", "ix_tasks_project_state (project_id,state,id) USING HASH"),
        ("index-type-before", "ix_tasks_project_state (project_id,state,id)", "ix_tasks_project_state USING HASH (project_id,state,id)"),
        ("index-sort", "ix_tasks_project_state (project_id,state,id)", "ix_tasks_project_state (project_id,state DESC,id)"),
        ("FK-table", "REFERENCES users(id)", "REFERENCES service_accounts(id)"),
        ("FK-database", "REFERENCES users(id)", "REFERENCES other_db.users(id)"),
        ("FK-column-order", "REFERENCES tasks(project_id,id)", "REFERENCES tasks(id,project_id)"),
        ("FK-source-order", "FOREIGN KEY (project_id,task_id) REFERENCES tasks", "FOREIGN KEY (task_id,project_id) REFERENCES tasks"),
        ("FK-action", "REFERENCES users(id)", "REFERENCES users(id) ON DELETE CASCADE"),
        ("FK-update-action", "REFERENCES users(id)", "REFERENCES users(id) ON UPDATE CASCADE"),
        ("CHECK-tautology", "CHECK (active IN (0,1))", "CHECK (1=1)"),
        ("table-engine", "ENGINE=InnoDB", "ENGINE=MyISAM"),
    ]
    for name, before, after in mutations:
        assert before in sql
        record(name, ddl_catalog(sql.replace(before, after, 1)) != baseline)
    pairs = [
        ("parentheses-quotes", "active IN (0,1)", "((`active` IN (0,1)))", True),
        ("ascii", "LEFT(password_hash,10)='$argon2id$'", "LEFT(`password_hash`,10)=_ascii'$argon2id$'", True),
        ("utf8mb4", "LEFT(password_hash,10)='$argon2id$'", "LEFT(password_hash,10)=_utf8mb4'$argon2id$'", True),
        ("precedence", "(a=1 OR b=2) AND c=3", "a=1 OR (b=2 AND c=3)", False),
        ("literal-case", "JSON_TYPE(v)='ARRAY'", "JSON_TYPE(v)='array'", False),
        ("function-argument", "LEFT(v,10)='x'", "LEFT(v,11)='x'", False),
        ("function-bytes", "LENGTH(v)>0", "CHAR_LENGTH(v)>0", False),
        ("literal-prefix-content", "v='_ascii''ARRAY'", "v='ARRAY'", False),
        ("IN-expansion", "active IN (0,1)", "active IN (0,1,2)", False),
        ("tautology-or", "active IN (0,1)", "active IN (0,1) OR 1=1", False),
        ("IS-NOT-NULL-form", "v IS NOT NULL", "NOT v IS NULL", True),
        ("utf8mb4-nonascii", "v='数组'", "v=_utf8mb4'数组'", True),
    ]
    for name, left, right, equal in pairs:
        record(name, (expression(left) == expression(right)) == equal)
    for value in ("v=_ascii'é'", "v=1 garbage", "v=1;2=2", "v=1 /* suffix */", "SELECT v FROM t"):
        try:
            expression(value)
            record("strict-reject:" + value, False)
        except ValueError as error:
            record("strict-reject:" + value, True, str(error))
    for value in ("CREATE TABLE t(x INT, SOMETHING BOGUS)", "SELECT 1"):
        try:
            ddl_catalog(value)
            record("strict-DDL-reject:" + value, False)
        except (ValueError, sg.errors.ParseError) as error:
            record("strict-DDL-reject:" + value, True, type(error).__name__)
    report = dict(version=sg.__version__,scope="Pure parse only; no DB/seed/production dependency change",outcomes=outcomes,
                  passed=sum(r["passed"] for r in outcomes),failed=sum(not r["passed"] for r in outcomes),
                  checks=len(checks),tables=len(baseline),columns=sum(len(t["columns"]) for t in baseline.values()))
    report["mixed_old_checker_blockers"] = roundtrip
    report["production_replacement_ready"] = False
    Path(args.output).write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps(report,ensure_ascii=False,indent=2))
    return int(report["failed"] != 0)


if __name__ == "__main__":
    raise SystemExit(main())
