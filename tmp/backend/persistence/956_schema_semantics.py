"""Owner regressions for catalog semantics; dedicated-MySQL drift probe runs explicitly."""

import copy
import json
import os
from pathlib import Path
from types import SimpleNamespace

import pytest
from sqlalchemy import event
from t44.persistence import MySQLSettings, create_mysql_engine, migrations
from t44.persistence.schema import TABLES


class Catalog:
    """Owner Inspector-shaped fixture built from the frozen specification."""

    def __init__(self):
        self.data = {
            name: {}
            for name in (
                "get_columns",
                "get_indexes",
                "get_unique_constraints",
                "get_foreign_keys",
                "get_check_constraints",
                "get_pk_constraint",
            )
        }
        for name, table in TABLES.items():
            unique = [
                c
                for c in table.constraints
                if c.__class__.__name__ == "UniqueConstraint"
            ]
            self.data["get_columns"][name] = [
                dict(
                    name=c.name,
                    type=c.type,
                    nullable=c.nullable,
                    default=None
                    if c.server_default is None
                    else str(c.server_default.arg),
                )
                for c in table.c
            ]
            self.data["get_pk_constraint"][name] = dict(constrained_columns=["id"])
            self.data["get_indexes"][name] = [
                dict(
                    name=i.name,
                    column_names=[c.name for c in i.columns],
                    unique=i.unique,
                )
                for i in table.indexes
            ] + [
                dict(
                    name=c.name,
                    column_names=[col.name for col in c.columns],
                    unique=True,
                )
                for c in unique
            ]
            self.data["get_unique_constraints"][name] = [
                dict(name=c.name, column_names=[col.name for col in c.columns])
                for c in unique
            ]
            self.data["get_foreign_keys"][name] = [
                dict(
                    name=c.name,
                    constrained_columns=[col.name for col in c.columns],
                    referred_schema=None,
                    referred_table=c.referred_table.name,
                    referred_columns=[e.column.name for e in c.elements],
                    options={},
                )
                for c in table.foreign_key_constraints
            ]
            self.data["get_check_constraints"][name] = [
                dict(name=c.name, sqltext=str(c.sqltext))
                for c in table.constraints
                if c.__class__.__name__ == "CheckConstraint"
            ]

    def get_table_names(self):
        return list(TABLES)

    def __getattr__(self, method):
        if method not in self.data:
            raise AttributeError(method)
        return lambda table: copy.deepcopy(self.data[method][table])

    def change(self, method, table, name, **changes):
        next(row for row in self.data[method][table] if row["name"] == name).update(
            changes
        )


@pytest.fixture
def catalog(monkeypatch):
    value = Catalog()
    monkeypatch.setattr(migrations, "inspect", lambda engine: value)
    return value


def report():
    return migrations.check_schema(
        SimpleNamespace(url=SimpleNamespace(database="t44_review"))
    )


def test_956_frozen_catalog_and_mysql_normalization_are_accepted(catalog):
    assert report()["passed"]
    catalog.change(
        "get_check_constraints",
        "users",
        "ck_users_active",
        sqltext="((`active` IN (0,1)))",
    )
    catalog.change(
        "get_check_constraints",
        "users",
        "ck_users_hash_shape",
        sqltext="((LEFT(`password_hash`,10) = _utf8mb4'$argon2id$') AND (CHAR_LENGTH(`password_hash`) > 30))",
    )
    catalog.change(
        "get_foreign_keys",
        "projects",
        "fk_projects_creator",
        referred_schema="t44_review",
        options={"ondelete": "NO ACTION", "onupdate": "RESTRICT"},
    )
    catalog.change(
        "get_indexes",
        "tasks",
        "ix_tasks_project_state",
        column_sorting={"state": ("asc",)},
        dialect_options={"mysql_using": "BTREE"},
    )
    assert report()["passed"]
    # MySQL 8.4 rebuild after restoring a unique index emits this actual ASCII introducer.
    catalog.change(
        "get_check_constraints", "users", "ck_users_hash_shape",
        sqltext="((left(`password_hash`,10) = _ascii'$argon2id$') and (char_length(`password_hash`) > 30))",
    )
    assert report()["passed"]


@pytest.mark.parametrize(
    "method,table,name,changes",
    [
        (
            "get_indexes",
            "tasks",
            "ix_tasks_project_state",
            {"column_names": ["state", "project_id", "id"]},
        ),
        ("get_indexes", "tasks", "ix_tasks_project_state", {"unique": True}),
        (
            "get_indexes",
            "tasks",
            "ix_tasks_project_state",
            {"column_sorting": {"state": ("desc",)}},
        ),
        ("get_indexes", "users", "uq_users_username", {"unique": False}),
        (
            "get_unique_constraints",
            "task_dependencies",
            "uq_dependencies_edge",
            {"column_names": ["project_id", "depends_on_task_id", "task_id"]},
        ),
        (
            "get_foreign_keys",
            "projects",
            "fk_projects_creator",
            {"referred_table": "service_accounts"},
        ),
        (
            "get_foreign_keys",
            "projects",
            "fk_projects_creator",
            {"referred_schema": "another_schema"},
        ),
        (
            "get_foreign_keys",
            "task_dependencies",
            "fk_dependencies_task",
            {"constrained_columns": ["task_id", "project_id"]},
        ),
        (
            "get_foreign_keys",
            "task_dependencies",
            "fk_dependencies_task",
            {"referred_columns": ["id", "project_id"]},
        ),
        (
            "get_foreign_keys",
            "projects",
            "fk_projects_creator",
            {"options": {"ondelete": "CASCADE"}},
        ),
        ("get_check_constraints", "users", "ck_users_active", {"sqltext": "1 = 1"}),
        (
            "get_check_constraints",
            "users",
            "ck_users_active",
            {"sqltext": "active IN (0,1,2)"},
        ),
        (
            "get_check_constraints",
            "users",
            "ck_users_active",
            {"sqltext": "active IN (0,1) OR 1=1"},
        ),
    ],
)
def test_956_same_names_with_changed_semantics_are_rejected(
    catalog, method, table, name, changes
):
    catalog.change(method, table, name, **changes)
    value = report()
    assert not value["passed"] and value["defects"]


def test_956_check_normalization_preserves_boolean_precedence_and_literal_case():
    normalize = migrations._check_signature
    assert normalize("(a=1 OR b=2) AND c=3") != normalize("a=1 OR (b=2 AND c=3)")
    assert normalize("json_type(value)='ARRAY'") != normalize(
        "json_type(value)='array'"
    )
    assert normalize("left(value,10) = 1") != normalize("left(value,11) = 1")
    assert normalize("a = 1 /* unparsed suffix */") is None
    assert normalize("value=_ascii'é'") is None
    assert normalize("value='_utf8mb4''ARRAY'") != normalize("value='ARRAY'")
    assert normalize("value='_ascii''ARRAY'") != normalize("value='ARRAY'")


def run_mysql_review(engine):
    """Controlled catalog mutations only in the empty, explicitly authorized owner schema."""
    if engine.url.database != "t44_review" or engine.dialect.name != "mysql":
        raise ValueError(
            "Review drift probe requires dedicated t44_review MySQL schema"
        )
    result = dict(
        migration=migrations.migrate(engine, expected_database="t44_review"), cases=[]
    )
    with engine.connect() as connection:
        if any(
            connection.exec_driver_sql(f"SELECT COUNT(*) FROM {name}").scalar_one()
            for name in TABLES
        ):
            raise ValueError("Dedicated review schema must have no business rows")
    cases = [
        (
            "index_column_order",
            "ALTER TABLE tasks DROP INDEX ix_tasks_project_state, ADD INDEX ix_tasks_project_state (state,project_id,id)",
            "ALTER TABLE tasks DROP INDEX ix_tasks_project_state, ADD INDEX ix_tasks_project_state (project_id,state,id)",
        ),
        (
            "unique_attribute",
            "ALTER TABLE users DROP INDEX uq_users_username, ADD INDEX uq_users_username (username)",
            "ALTER TABLE users DROP INDEX uq_users_username, ADD UNIQUE INDEX uq_users_username (username)",
        ),
        (
            "foreign_target",
            "ALTER TABLE projects DROP FOREIGN KEY fk_projects_creator; ALTER TABLE projects ADD CONSTRAINT fk_projects_creator FOREIGN KEY (created_by) REFERENCES service_accounts(id)",
            "ALTER TABLE projects DROP FOREIGN KEY fk_projects_creator; ALTER TABLE projects ADD CONSTRAINT fk_projects_creator FOREIGN KEY (created_by) REFERENCES users(id)",
        ),
        (
            "check_expression",
            "ALTER TABLE users DROP CHECK ck_users_active, ADD CONSTRAINT ck_users_active CHECK (1=1)",
            "ALTER TABLE users DROP CHECK ck_users_active, ADD CONSTRAINT ck_users_active CHECK (active IN (0,1))",
        ),
    ]
    for label, change, restore in cases:
        applied = False
        try:
            with engine.begin() as connection:
                for sql in change.split(";"):
                    connection.exec_driver_sql(sql.strip())
                    applied = True
            changed = migrations.check_schema(engine)
            assert not changed["passed"] and changed["defects"], label
            with pytest.raises(migrations.MigrationError, match="structure differs") as rejected:
                migrations.migrate(engine, expected_database="t44_review")
            result["cases"].append(
                dict(
                    case=label,
                    database="t44_review",
                    change_sql=change,
                    restore_sql=restore,
                    rejected=True,
                    defects=changed["defects"],
                    repeat_rejection=str(rejected.value),
                )
            )
        finally:
            if applied:
                with engine.begin() as connection:
                    for sql in restore.split(";"):
                        # If an ADD failed after DROP, restore the missing FK without dropping twice.
                        if "DROP FOREIGN KEY" in sql and not any(
                            fk["name"] == "fk_projects_creator"
                            for fk in migrations.inspect(connection).get_foreign_keys("projects")
                        ):
                            continue
                        connection.exec_driver_sql(sql.strip())
        restored = migrations.check_schema(engine)
        assert restored["passed"], label + " restore"
        result["cases"][-1]["restored"] = restored
    result["repeat"] = migrations.migrate(engine, expected_database="t44_review")
    return result


if __name__ == "__main__":
    private = json.loads(Path(os.environ["T44_REVIEW_CREDENTIALS"]).read_text())
    engine = create_mysql_engine(
        MySQLSettings(
            database="t44_review",
            **{key: private[key] for key in ("host", "port", "username", "password")},
        )
    )
    try:
        event.listen(
            engine,
            "before_cursor_execute",
            lambda conn, cursor, sql, parameters, context, many: print(
                json.dumps(dict(event="ddl", database="t44_review", sql=sql)), flush=True
            ) if sql.lstrip().upper().startswith(("CREATE", "ALTER")) else None,
        )
        print(json.dumps(run_mysql_review(engine), ensure_ascii=False, indent=2))
    finally:
        engine.dispose()
