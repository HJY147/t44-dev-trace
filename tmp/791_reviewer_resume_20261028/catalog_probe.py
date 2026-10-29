"""Reviewer-only offline checks against the immutable DDL; never connect to a DB."""

import copy
import hashlib
import json
import re
from pathlib import Path

from t44.persistence import migrations

ROOT = Path(__file__).resolve().parents[2]
source = ROOT / "backend/t44/persistence/migrations.py"
ddl = (ROOT / "specs/database/schema.sql").read_bytes()
native_path = ROOT / "agents/database/catalog-audit-20261028/native-after-static.json"
native = json.loads(native_path.read_text())
rows = {key: [] for key in ("TABLES", "COLUMNS", "STATISTICS", "TABLE_CONSTRAINTS")}

# Parse each physical DDL line, independently of schema.py and its metadata builder.
for table, body in re.findall(r"CREATE TABLE (\w+) \(\n(.*?)\n\) ENGINE=", ddl.decode(), re.S):
    rows["TABLES"].append((table, "InnoDB", "utf8mb4_0900_ai_ci"))
    for line in body.splitlines():
        line = line.strip().rstrip(",")
        column = re.match(r"(\w+) (INT|TINYINT|SMALLINT|MEDIUMINT|VARCHAR|CHAR|BINARY|DATETIME|JSON)\b", line)
        if column:
            field, kind = column.groups()
            char = kind in ("VARCHAR", "CHAR")
            ascii_char = "CHARACTER SET ascii COLLATE ascii_bin" in line
            rows["COLUMNS"].append((table, field, "auto_increment" if "AUTO_INCREMENT" in line else "", "ascii" if ascii_char else "utf8mb4" if char else None, "ascii_bin" if ascii_char else "utf8mb4_0900_ai_ci" if char else None))
        key = re.fullmatch(r"(PRIMARY KEY|UNIQUE KEY \w+|KEY \w+) \(([^)]+)\)", line)
        if key:
            declaration, fields = key.groups()
            name = "PRIMARY" if declaration == "PRIMARY KEY" else declaration.split()[-1]
            for ordinal, field in enumerate(fields.split(","), start=1):
                rows["STATISTICS"].append((table, name, ordinal, field, int(declaration.startswith("KEY ")), "A", None, "BTREE", "YES"))
        check = re.match(r"CONSTRAINT (\w+) CHECK \(", line)
        if check:
            rows["TABLE_CONSTRAINTS"].append((table, check[1], "YES"))


class Catalog:
    def __init__(self, catalog):
        self.rows = catalog
        self.calls = []
        self.exited = False
        self.fail_at = None

    def connect(self):
        return self

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.exited = True

    def exec_driver_sql(self, sql):
        self.calls.append(sql)
        assert sql.startswith("SELECT ")
        assert " WHERE TABLE_SCHEMA=DATABASE()" in sql
        if len(self.calls) == self.fail_at:
            raise RuntimeError("reviewer synthetic interruption")
        return self.rows[sql.split("INFORMATION_SCHEMA.")[1].split()[0]]


assert hashlib.sha256(ddl).hexdigest() == "c0e740b203a85117fb125c578ab61401275bbe46ea80c629869c6cff39424bc4"
assert len(rows["TABLES"]) == 18 and len(rows["COLUMNS"]) == 226
assert sorted(rows["COLUMNS"]) == sorted(map(tuple, native["baseline_columns"]))
bindings = native["committed_source_bindings"]
for relative, digest in bindings.items():
    assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == digest, relative

baseline = Catalog(rows)
assert migrations._catalog_defects(baseline) == []
assert baseline.exited and len(baseline.calls) == 4

# Additional nonunique helpers are allowed; primary-key direction is still audited.
extra = copy.deepcopy(rows)
extra["STATISTICS"].append(("users", "reviewer_nonunique_helper", 1, "display_name", 1, "D", 8, "BTREE", "NO"))
assert migrations._catalog_defects(Catalog(extra)) == []
pk = copy.deepcopy(rows)
target = next(i for i, row in enumerate(pk["STATISTICS"]) if row[:3] == ("users", "PRIMARY", 1))
changed = list(pk["STATISTICS"][target])
changed[5] = "D"
pk["STATISTICS"][target] = tuple(changed)
assert migrations._catalog_defects(Catalog(pk)) == ["users.PRIMARY.1:index_options"]

# Read failure must close the connection and abort, rather than accept partial data.
failed = Catalog(rows)
failed.fail_at = 3
try:
    migrations._catalog_defects(failed)
except RuntimeError as error:
    assert str(error) == "reviewer synthetic interruption"
else:
    raise AssertionError("catalog failure was silently accepted")
assert failed.exited

print(json.dumps({
    "review_scope": "offline synthetic reviewer probe; no real MySQL connection or server execution",
    "groups_passed": 5,
    "independent_ddl_counts": {key: len(value) for key, value in rows.items()},
    "native_column_snapshot_rows_verified": len(native["baseline_columns"]),
    "native_source_commit": native["source_commit"],
    "native_receipt_sha256": hashlib.sha256(native_path.read_bytes()).hexdigest(),
    "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
    "source_bindings_recomputed": bindings,
    "queries": baseline.calls,
    "passed": True,
}, ensure_ascii=False, indent=2))
