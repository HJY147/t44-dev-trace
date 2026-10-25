"""Offline CHECK parser comparison, using frozen public source and no DB."""

import importlib.util
import json
import subprocess
import tempfile
import time
from pathlib import Path

import sqlglot
from t44.persistence.schema import TABLES


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


with tempfile.TemporaryDirectory() as directory:
    path = Path(directory) / "migrations.py"
    path.write_bytes(subprocess.check_output([
        "git", "show", "935ab5b93bea788672c2b4a088c79cfeed848954:backend/t44/persistence/migrations.py",
    ]))
    old = load("t44.persistence.check_trial_baseline", path)._check_signature
candidate = load("candidate", Path(__file__).with_name("check_candidate_derived.py")).check_signature
checks = [str(c.sqltext) for table in TABLES.values() for c in table.constraints
          if type(c).__name__ == "CheckConstraint"]
pairs = []
for source in checks:
    pairs.extend((source, value) for value in (
        source, f"(({source}))", sqlglot.parse_one(source, read="mysql").sql(dialect="mysql"),
        source.replace("'ARRAY'", "'array'"), source.replace("BETWEEN", "between"),
        source.replace(" = ", " <> "), source.replace(" AND ", " OR "),
    ))
pairs.extend([
    ("a=1", "A = (1)"), ("a=1", "a=+1"),
    ("a is not null", "not a is null"),
    ("a='a''b'", "a='a\\'b'"),
    ("a=_ascii'é'", "a='é'"),
    ("a='ARRAY'", "a='array'"),
    ("char_length(a)>1", "character_length(a)>1"),
    ("left(a,2)=1", "`left`(a,2)=1"),
    ("a=1", "a=1; SELECT 1"), ("a=1", "a=1 /* ignored */"),
    ("a=1", "a=01"), ("a=1", "a=1e0"),
])
differences = [dict(left=a, right=b, old_equal=old(a)==old(b), new_equal=candidate(a)==candidate(b))
               for a,b in pairs if (old(a)==old(b)) != (candidate(a)==candidate(b))]
measurements = {}
for name, normalizer in (("old", old), ("candidate", candidate)):
    begin = time.perf_counter()
    for _ in range(10):
        for expression in checks:
            normalizer(expression)
    measurements[name] = dict(checks=590, elapsed_seconds=time.perf_counter()-begin)
report = dict(sqlglot_version=sqlglot.__version__, frozen_checks=len(checks),
              pair_count=len(pairs), differences=differences, timings=measurements,
              decision="REJECT_CANDIDATE_NOT_PRODUCTION: strict candidate has insufficient LOC gain and measured CHECK-only parser overhead")
Path(__file__).with_name("sqlglot-trial.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report,ensure_ascii=False))
