"""Finite synthetic SQLite hook checks, not production MySQL/HTTP acceptance."""

import importlib.util
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest
from sqlalchemy import Column, DateTime, Integer, MetaData, String, Table, create_engine
from sqlalchemy.orm import Session
from t44.persistence.errors import PersistenceUnavailable
from t44.persistence.uow import SqlAlchemyUnitOfWorkFactory

PATH = Path(__file__).with_name("833_database_trace.py")
SPEC = importlib.util.spec_from_file_location("database_trace_under_test", PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


@pytest.fixture
def store(tmp_path, monkeypatch):
    import t44.persistence.rows as rows

    engine = create_engine(f"sqlite:///{tmp_path / 'trace.sqlite'}", pool_size=1, max_overflow=0)
    table = Table(
        "diagnostic_rows",
        MetaData(),
        Column("id", Integer, primary_key=True),
        Column("note", String(200)),
        Column("at", DateTime),
    )
    table.metadata.create_all(engine)
    monkeypatch.setattr(rows, "TABLES", {table.name: table})
    trace = MODULE.DatabaseTrace().install(engine)
    yield trace, engine, table
    engine.dispose()
    trace.close()


def test_import_has_no_database_network_or_application_imports():
    script = (
        "import importlib.util,sys,json; "
        "s=importlib.util.spec_from_file_location('observe',sys.argv[1]); "
        "m=importlib.util.module_from_spec(s); s.loader.exec_module(m); "
        "print(json.dumps([n for n in sys.modules if "
        "n.split('.')[0] in {'sqlalchemy','pymysql','t44','socket','httpx'}]))"
    )
    result = subprocess.run(
        [sys.executable, "-I", "-c", script, str(PATH)], capture_output=True, text=True, check=True
    )
    assert json.loads(result.stdout) == []


def test_real_rows_roundtrip_and_layer_times(store):
    trace, engine, table = store
    factory = SqlAlchemyUnitOfWorkFactory(engine)
    with trace.request("controlledRows"), factory() as uow:
        assert uow.gateway.insert(table.name, {"id": 1, "note": "sensitive-bound-note"}) == 1
        assert uow.gateway.count(table.name) == 1
        assert uow.gateway.rows(table.name)[0]["note"] == "sensitive-bound-note"
    snapshot = trace.snapshot()
    record = snapshot["records"][0]
    assert record["phases"]["rows_execute_inclusive"]["count"] == 3
    assert record["phases"]["cursor_execute_inclusive"]["count"] == 3
    assert record["phases"]["session_commit_inclusive"]["count"] == 1
    assert record["phases"]["session_close_inclusive"]["count"] == 1
    assert record["phases"]["mapping_next_inclusive"]["errors"] == 0
    assert record["mapping_rows"] == 1
    assert record["start_perf_ns"] < record["end_perf_ns"]
    assert record["start_monotonic_ns"] < record["end_monotonic_ns"]
    assert record["thread_cpu_ns"] >= 0 and record["wall_ns"] > 0
    assert snapshot["pending_cursor_spans"] == 0
    assert engine.pool.checkedout() == 0
    assert "sensitive-bound-note" not in json.dumps(snapshot)
    assert all(len(row["shape_sha256"]) == 64 for row in record["sql"])


def test_conversion_and_scalar_are_separate(store):
    trace, engine, table = store
    with trace.request("timeConversion"), SqlAlchemyUnitOfWorkFactory(engine)() as uow:
        uow.gateway.insert(table.name, {"id": 1, "at": datetime(2026, 1, 1, tzinfo=UTC)})
        result = uow.gateway.rows(table.name)
        assert result[0]["at"].tzinfo == UTC
        assert uow.gateway.count(table.name) == 1
    phases = trace.snapshot()["records"][0]["phases"]
    assert phases["codec_from_db_time"]["count"] == 1
    assert phases["result_scalar_one_inclusive"]["count"] == 1


def test_failure_records_class_not_message_and_keeps_original_sanitization(store):
    trace, engine, table = store
    with (
        pytest.raises(PersistenceUnavailable),
        trace.request("missingTable"),
        SqlAlchemyUnitOfWorkFactory(engine)() as uow,
    ):
        uow.gateway._execute(table.select().suffix_with("BAD_SECRET_PAYLOAD"), "rows")
    snapshot = trace.snapshot()
    record = snapshot["records"][0]
    assert record["exception_class"] == "PersistenceUnavailable"
    assert record["sql"][0]["error_class"] == "OperationalError"
    assert record["phases"]["session_rollback_inclusive"]["count"] == 1
    assert "BAD_SECRET_PAYLOAD" not in json.dumps(snapshot)
    assert snapshot["pending_cursor_spans"] == 0 and engine.pool.checkedout() == 0


def test_context_boundaries_and_sampling_limits(store):
    trace, engine, table = store
    trace.max_sql_samples = 1
    with trace.request("first"):
        with SqlAlchemyUnitOfWorkFactory(engine)() as uow:
            uow.gateway.count(table.name)
            uow.gateway.count(table.name)
        with pytest.raises(RuntimeError, match="Nested"), trace.request("nested"):
            pass
    with trace.request("second"):
        pass
    snapshot = trace.snapshot()
    assert [r["operation_id"] for r in snapshot["records"]] == ["first", "second"]
    assert snapshot["records"][0]["sql_samples_dropped"] == 1
    assert snapshot["records"][1]["phases"] == {}
    trace.max_requests = 2
    with pytest.raises(RuntimeError, match="limit"), trace.request("third"):
        pass
    for operation, identity in [("free text/secret", None), ("valid", "not-uuid")]:
        with pytest.raises(ValueError), trace.request(operation, request_id=identity):
            pass


def test_restore_original_methods_and_reject_double_install(store):
    trace, engine, _ = store
    original = next(
        fn for owner, name, fn in trace._patches if owner is Session and name == "execute"
    )
    other = MODULE.DatabaseTrace()
    with pytest.raises(RuntimeError, match="already installed"):
        other.install(engine)
    assert getattr(Session.execute, "_t44_database_observer", False)
    trace.close()
    assert Session.execute is original
    assert not getattr(engine.connect, "_t44_database_observer", False)
    with pytest.raises(RuntimeError, match="not installed"):
        trace.snapshot()
