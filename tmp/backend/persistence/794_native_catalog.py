"""Native-catalog failure and missing-row checks; real MySQL recipes remain in tmp/794."""

import copy
from contextlib import nullcontext

import pytest
from sqlalchemy import CheckConstraint, Column, Index, MetaData, Table
from sqlalchemy.dialects.mysql import INTEGER, VARCHAR
from sqlalchemy.exc import OperationalError
from t44.persistence import migrations


@pytest.fixture
def native(monkeypatch):
    table = Table(
        "probe",
        MetaData(),
        Column("id", INTEGER(unsigned=True), primary_key=True),
        Column("name", VARCHAR(32)),
        Column("code", VARCHAR(16, charset="ascii", collation="ascii_bin")),
        CheckConstraint("id > 0", name="ck_probe"),
        Index("ix_probe_name", "name"),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_0900_ai_ci",
    )
    monkeypatch.setattr(migrations, "TABLES", {"probe": table})

    class Connection:
        def __init__(self):
            self.queries = []
            self.rows = {
                "TABLES": [("probe", "InnoDB", "utf8mb4_0900_ai_ci")],
                "COLUMNS": [
                    ("probe", "id", "auto_increment", None, None),
                    ("probe", "name", "", "utf8mb4", "utf8mb4_0900_ai_ci"),
                    ("probe", "code", "", "ascii", "ascii_bin"),
                ],
                "STATISTICS": [
                    ("probe", "PRIMARY", 1, "id", 0, "A", None, "BTREE", "YES"),
                    ("probe", "ix_probe_name", 1, "name", 1, "A", None, "BTREE", "YES"),
                ],
                "TABLE_CONSTRAINTS": [("probe", "ck_probe", "YES")],
            }

        def connect(self):
            return nullcontext(self)

        def exec_driver_sql(self, sql):
            self.queries.append(sql)
            assert sql.endswith(" WHERE TABLE_SCHEMA=DATABASE()")
            return copy.deepcopy(self.rows[sql.split("INFORMATION_SCHEMA.")[1].split()[0]])

    return Connection()


def test_794_frozen_native_properties_and_extra_nonunique_helper_are_accepted(native):
    native.rows["STATISTICS"].append(
        ("probe", "extra_helper", 1, "name", 1, "D", None, "BTREE", "NO")
    )
    assert migrations._catalog_defects(native) == []
    assert len(native.queries) == 4


@pytest.mark.parametrize(
    "catalog,row,field,value,label",
    [
        ("TABLES", 0, 1, "MyISAM", "table_options"),
        ("TABLES", 0, 2, "utf8mb4_bin", "table_options"),
        ("COLUMNS", 0, 2, "", "column_options"),
        ("COLUMNS", 1, 2, "VIRTUAL GENERATED", "column_options"),
        ("COLUMNS", 1, 3, "ascii", "column_options"),
        ("COLUMNS", 2, 4, "ascii_general_ci", "column_options"),
        ("STATISTICS", 0, 5, "D", "index_options"),
        ("STATISTICS", 1, 5, "D", "index_options"),
        ("STATISTICS", 1, 8, "NO", "index_options"),
        ("STATISTICS", 1, 6, 8, "index_options"),
        ("STATISTICS", 1, 7, "HASH", "index_options"),
        ("STATISTICS", 1, 4, 0, "index_options"),
        ("TABLE_CONSTRAINTS", 0, 2, "NO", "check_enforcement"),
    ],
)
def test_794_native_properties_cannot_disappear_in_reflection(
    native, catalog, row, field, value, label
):
    changed = list(native.rows[catalog][row])
    changed[field] = value
    native.rows[catalog][row] = tuple(changed)
    defects = migrations._catalog_defects(native)
    assert defects and all(defect.endswith(":" + label) for defect in defects)


@pytest.mark.parametrize("catalog", ["TABLES", "COLUMNS", "STATISTICS", "TABLE_CONSTRAINTS"])
def test_794_missing_required_catalog_rows_fail_closed(native, catalog):
    native.rows[catalog].clear()
    assert migrations._catalog_defects(native)


def test_794_native_query_failure_propagates(native, monkeypatch):
    def lost_connection(sql):
        raise OperationalError(sql, {}, RuntimeError("synthetic catalog unavailable"))

    monkeypatch.setattr(native, "exec_driver_sql", lost_connection)
    with pytest.raises(OperationalError):
        migrations._catalog_defects(native)
