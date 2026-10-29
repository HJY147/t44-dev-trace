"""Local owner catalog transcript comparison against the exact parent source."""

import copy
import importlib.util
import subprocess
from contextlib import contextmanager
from pathlib import Path

import pytest
from sqlalchemy.exc import OperationalError
from t44.persistence import migrations

BASE = "a92e5e73da93ba23748c3bab113103036c395d50"


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def comparison(monkeypatch, tmp_path):
    owner = load(
        "r29b_public_native_fixture",
        Path(__file__).parents[1] / "backend/persistence/794_native_catalog.py",
    )
    native = owner.native.__wrapped__(monkeypatch)
    source = tmp_path / "before_migrations.py"
    source.write_bytes(
        subprocess.check_output(["git", "show", f"{BASE}:backend/t44/persistence/migrations.py"])
    )
    before = load("t44.persistence.r29b_before_migrations", source)
    monkeypatch.setattr(before, "TABLES", migrations.TABLES)
    return before, native


def transcript(module, native, fail_at=None):
    events = []

    class Engine:
        @contextmanager
        def connect(self):
            events.append(("enter",))
            try:
                yield self
            finally:
                events.append(("exit",))

        def exec_driver_sql(self, sql):
            events.append(("query", sql))
            if sum(event[0] == "query" for event in events) == fail_at:
                raise OperationalError(sql, {}, RuntimeError("catalog unavailable"))
            return copy.deepcopy(native.exec_driver_sql(sql))

    try:
        result = module._catalog_defects(Engine())
    except OperationalError as error:
        result = type(error).__name__, str(error.orig)
    return result, events


@pytest.mark.parametrize("scenario", ["clean", "combined-defects"])
def test_native_query_defects_and_context_match_exact_parent(comparison, scenario):
    before, native = comparison
    if scenario == "combined-defects":
        native.rows["TABLES"].clear()
        native.rows["COLUMNS"].pop()
        native.rows["STATISTICS"].clear()
        native.rows["TABLE_CONSTRAINTS"].clear()
    result, events = transcript(migrations, native)
    assert (result, events) == transcript(before, native)
    queries = [event[1] for event in events if event[0] == "query"]
    assert len(queries) == 4
    assert events[0] == ("enter",) and events[-1] == ("exit",)
    if scenario == "clean":
        assert result == []
    else:
        assert list(dict.fromkeys(item.rsplit(":", 1)[1] for item in result)) == [
            "table_options",
            "column_options",
            "index_options",
            "check_enforcement",
        ]


@pytest.mark.parametrize("fail_at", [1, 2, 3, 4])
def test_each_native_query_failure_preserves_prefix_and_exit(comparison, fail_at):
    before, native = comparison
    result, events = transcript(migrations, native, fail_at)
    assert (result, events) == transcript(before, native, fail_at)
    assert result == ("OperationalError", "catalog unavailable")
    assert sum(event[0] == "query" for event in events) == fail_at
    assert events[-1] == ("exit",)
