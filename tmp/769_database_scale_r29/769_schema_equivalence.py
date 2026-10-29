"""Owner differential checks for the hash-bound frozen-DDL adapter; no database access."""

import hashlib
import importlib.util
import re
import subprocess

import pytest
from sqlalchemy.dialects import mysql, sqlite
from sqlalchemy.schema import CreateIndex, CreateTable
from t44.persistence import schema

BASE = "f5e0d95ea68af33dfb213ac6e8d6b496527ed7b2"


@pytest.fixture(scope="module")
def baseline(tmp_path_factory):
    path = tmp_path_factory.mktemp("frozen-schema") / "baseline_schema.py"
    path.write_bytes(
        subprocess.check_output(["git", "show", f"{BASE}:backend/t44/persistence/schema.py"])
    )
    spec = importlib.util.spec_from_file_location("t44.persistence.baseline_schema_r29", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_769_every_frozen_ddl_payload_has_identical_declarations(baseline):
    sql = schema.ddl_text()
    bodies = [
        body for _, body in re.findall(r"CREATE TABLE (\w+) \(\n(.*?)\n\) ENGINE=", sql, re.S)
    ]
    bodies.extend(body for _, body in re.findall(r"ALTER TABLE (\w+)\s+(.*?);", sql, re.S))
    assert len(bodies) == 20
    for body in bodies:
        assert schema._parts(body) == baseline._parts(body)
    assert schema.DDL_SHA256 == baseline.DDL_SHA256
    assert hashlib.sha256(sql.encode()).hexdigest() == schema.DDL_SHA256


@pytest.mark.parametrize("name", tuple(schema.TABLES))
@pytest.mark.parametrize("dialect", (mysql.dialect(), sqlite.dialect()), ids=("mysql", "sqlite"))
def test_769_all_tables_columns_constraints_and_indexes_compile_identically(
    baseline, name, dialect
):
    current, previous = schema.TABLES[name], baseline.TABLES[name]
    assert list(current.c.keys()) == list(previous.c.keys())
    for left, right in zip(current.c, previous.c, strict=True):
        assert (
            str(left.type.compile(dialect=dialect)),
            left.nullable,
            left.primary_key,
            left.autoincrement,
            str(left.server_default.arg) if left.server_default is not None else None,
        ) == (
            str(right.type.compile(dialect=dialect)),
            right.nullable,
            right.primary_key,
            right.autoincrement,
            str(right.server_default.arg) if right.server_default is not None else None,
        )

    def table_ddl(table):
        # SQLAlchemy stores constraints as a set; compare complete declarations independently
        # of that set's iteration order, retaining column order in the separate assertion above.
        sql = str(CreateTable(table).compile(dialect=dialect))
        prefix, separator, body = sql.partition("(\n")
        declarations, closing, suffix = body.rpartition("\n)")
        assert separator and closing
        return prefix, sorted(baseline._parts(declarations)), suffix

    assert table_ddl(current) == table_ddl(previous)
    assert sorted(str(CreateIndex(i).compile(dialect=dialect)) for i in current.indexes) == sorted(
        str(CreateIndex(i).compile(dialect=dialect)) for i in previous.indexes
    )
    assert dict(current.dialect_options["mysql"]) == dict(previous.dialect_options["mysql"])


@pytest.mark.parametrize("change", ("indent", "continuation", "comma", "blankline"))
def test_769_unreviewed_ddl_changes_are_rejected_before_parsing(monkeypatch, change):
    original = schema.ddl_text()
    mutated = {
        "indent": original.replace("    id INT", "  id INT", 1),
        "continuation": original.replace("        OR", "    OR", 1),
        "comma": original.replace("IN (0,1)", "IN (0, 1)", 1),
        "blankline": original.replace("\n", "\n\n", 1),
    }[change]
    assert mutated != original

    class Resource:
        def joinpath(self, name):
            assert name == "schema_v1.sql"
            return self

        def read_text(self, encoding):
            assert encoding == "utf-8"
            return mutated

    monkeypatch.setattr(schema, "files", lambda package: Resource())
    monkeypatch.setattr(schema, "_parts", lambda _: pytest.fail("Unverified DDL reached parser"))
    with pytest.raises(RuntimeError, match="checksum does not match"):
        schema.build_metadata()
