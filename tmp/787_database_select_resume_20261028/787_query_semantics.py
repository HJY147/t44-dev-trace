"""Contract differential: actual a12 gateway versus current gateway, no external DB."""

import json
import subprocess
import sys
import types
from datetime import UTC, datetime
from pathlib import Path

import pytest
from sqlalchemy import create_engine, event, text
from sqlalchemy.dialects import mysql, sqlite
from t44.persistence import (
    PersistenceUnavailable,
    SqlAlchemyUnitOfWorkFactory,
    StatementRejected,
    TransactionStateError,
)
from t44.persistence import rows as current
from t44.persistence.schema import TABLES, metadata

ROOT = Path(__file__).resolve().parents[2]
BASE = "a12e9e70b963bacafda3242bb6d82e53ee912ff1"
source = subprocess.check_output(
    ["git", "show", f"{BASE}:backend/t44/persistence/rows.py"], cwd=ROOT
)
baseline = types.ModuleType("t44.persistence._a12_rows_contract_probe")
sys.modules[baseline.__name__] = baseline
exec(
    compile(source, f"git:{BASE}:backend/t44/persistence/rows.py", "exec"),
    baseline.__dict__,
)


def statement(module, table, options):
    gateway = module.RowsGateway(
        lambda: pytest.fail("compile must not open a session"), lambda: None
    )
    gateway._execute = lambda stmt, mode: stmt
    args = dict(options)
    if "predicates" in args:
        args["predicates"] = tuple(module.Pred(*pred) for pred in args["predicates"])
    return gateway.rows(table, **args)


def shape(stmt, dialect):
    compiled = stmt.compile(dialect=dialect)
    return {
        "sql": str(compiled),
        "parameters": compiled.params,
        "positiontup": compiled.positiontup,
        "result_columns": [
            (entry.keyname, entry.name, str(entry.type))
            for entry in compiled._result_columns
        ],
        "selected_columns": list(stmt.selected_columns.keys()),
    }


@pytest.mark.parametrize("table", sorted(TABLES))
def test_registered_table_columns_bindings_and_lock_sql_equal_a12(table, tmp_path):
    t = TABLES[table]
    assert not any(column._omit_from_statements for column in t.c)
    fields = tuple(t.c.keys())
    options = [
        {},
        {"where": {"id": [1, 7]}, "order_by": ("-id",), "limit": 2, "offset": 1},
        {"where": {"id": 7}, "lock": "update", "skip_locked": True},
        {"lock": "share", "limit": 1},
        {"predicates": (("id", "ge", 1), ("id", "is_null", False)), "lock": "update"},
        {"columns": fields, "where": {"id": 7}},
        {"columns": (fields[-1], fields[0], fields[-1]), "order_by": (), "limit": 0},
        {"columns": (), "order_by": ()},
    ]
    ledger = []
    for kwargs in options:
        old, new = (statement(module, table, kwargs) for module in (baseline, current))
        assert list(old.selected_columns) == list(new.selected_columns)
        for dialect in (mysql.dialect(), sqlite.dialect()):
            before, after = shape(old, dialect), shape(new, dialect)
            assert before == after
            ledger.append({"dialect": dialect.name, "options": kwargs, "shape": after})
    output = tmp_path / f"compile-{table}.json"
    with output.open("x") as stream:
        json.dump(ledger, stream, indent=2)
        stream.write("\n")


@pytest.mark.parametrize(
    "table,options",
    [
        ("users; DROP TABLE users", {}),
        ("users", {"columns": ("id; --",)}),
        ("users", {"where": {"id": [text("1 OR 1=1")]}}),
        ("users", {"predicates": (("id", "sql", "1 OR 1=1"),)}),
        ("users", {"order_by": ("-id DESC; --",)}),
        ("users", {"limit": True}),
        ("users", {"limit": -1}),
        ("users", {"offset": True}),
        ("users", {"offset": -1}),
        ("users", {"lock": "read"}),
        ("users", {"skip_locked": True}),
    ],
)
def test_rejected_input_remains_rejected_before_execution(table, options):
    for module in (baseline, current):
        with pytest.raises(StatementRejected):
            statement(module, table, options)


def user(name, now):
    return {
        "username": name,
        "display_name": name,
        "password_hash": "$argon2id$synthetic-not-login",
        "active": 1,
        "created_at": now,
        "updated_at": now,
    }


def test_real_mapping_projection_bound_values_and_transaction_contract(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'semantics.sqlite'}")
    event.listen(
        engine, "connect", lambda conn, _: conn.execute("PRAGMA foreign_keys=ON")
    )
    metadata.create_all(engine)
    factory = SqlAlchemyUnitOfWorkFactory(engine)
    now = datetime(2026, 10, 28, 0, 1, 2, 345678, tzinfo=UTC)
    marker = "bound'; DROP TABLE users; --"
    try:
        with factory() as uow:
            first = uow.gateway.insert("users", user(marker, now))
            second = uow.gateway.insert("users", user("second", now))
            project = uow.gateway.insert(
                "projects",
                {
                    "name": "probe",
                    "description": "长文本" * 600,
                    "created_by": first,
                    "created_at": now,
                    "updated_at": now,
                },
            )
            uow.gateway.insert(
                "outbox_events",
                {
                    "event_type": 2,
                    "project_id": project,
                    "payload": {"nullable": None, "text": "值", "array": [1, False]},
                    "recipients": [first, second],
                    "next_attempt_at": now,
                    "created_at": now,
                    "updated_at": now,
                },
            )
        with factory() as uow:
            old = baseline.RowsGateway(uow._require_active, uow._mark_failed)
            for table in ("users", "projects", "outbox_events"):
                before, after = old.rows(table), uow.gateway.rows(table)
                assert before == after and before
                assert list(after[0]) == list(TABLES[table].c.keys())
                assert after[0]["created_at"] == now
                assert after[0]["created_at"].tzinfo is UTC
            assert after[0]["payload"] == {
                "nullable": None,
                "text": "值",
                "array": [1, False],
            }
            assert after[0]["recipients"] == [first, second]
            assert after[0]["task_id"] is None and after[0]["lease_token"] is None
            assert uow.gateway.get("projects", project)["description"] == "长文本" * 600
            assert uow.gateway.rows("users", {"username": marker})[0]["id"] == first
            assert (
                uow.gateway.rows("users", order_by=("-id",), limit=1, offset=1)[0]["id"]
                == first
            )
            assert uow.gateway.rows("users", {"id": []}) == []
            assert uow.gateway.rows("users", columns=("username", "id"), limit=1) == [
                {"username": marker, "id": first}
            ]
            assert uow.gateway.rows("users", limit=0) == []
        with pytest.raises(RuntimeError, match="rollback"):
            with factory() as uow:
                uow.gateway.insert("users", user("rolled-back", now))
                assert uow.gateway.rows("users", {"username": "rolled-back"})
                raise RuntimeError("rollback")
        with factory() as uow:
            assert uow.gateway.rows("users", {"username": "rolled-back"}) == []
        with engine.begin() as connection:
            connection.exec_driver_sql("DROP TABLE notifications")
        with pytest.raises(TransactionStateError):
            with factory() as uow:
                uow.gateway.insert("users", user("must-rollback", now))
                with pytest.raises(PersistenceUnavailable) as error:
                    uow.gateway.rows("notifications")
                assert str(error.value) == "Database operation failed"
                with pytest.raises(TransactionStateError):
                    uow.gateway.rows("users")
        with factory() as uow:
            assert uow.gateway.rows("users", {"username": "must-rollback"}) == []
    finally:
        engine.dispose()
