"""Source-bound smoke and immutable-function checks for a rejected prototype."""

import ast
import importlib.util
import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = "7374b3637b06465d448fc2e81952ba18fc676315"
CANDIDATE = "009b7acdbfa0e0497d7cc36bbbae86805283dcfd"
MODULE = "backend/t44/persistence/migrations.py"


def git(*arguments):
    return subprocess.check_output(["git", *arguments], cwd=ROOT).decode()


def functions(source):
    lines = source.splitlines(keepends=True)
    return {
        node.name: "".join(lines[node.lineno - 1 : node.end_lineno])
        for node in ast.parse(source).body
        if isinstance(node, ast.FunctionDef)
    }


before = git("show", f"{BASE}:{MODULE}")
candidate = git("show", f"{CANDIDATE}:{MODULE}")
unchanged = ["_check_signature", "migrate"]
for name in unchanged:
    assert functions(before)[name] == functions(candidate)[name], name
protected = [
    "specs",
    "backend/t44/persistence/schema.py",
    "backend/t44/persistence/schema_v1.sql",
    "backend/t44/persistence/rows.py",
    "backend/t44/persistence/uow.py",
    "backend/t44/persistence/seed.py",
    "backend/t44/persistence/scans.py",
    "backend/t44/persistence/accounts.py",
    "backend/t44/persistence/delivery.py",
    "backend/t44/persistence/engine.py",
    "backend/pyproject.toml",
    "backend/requirements.lock",
    "tmp/backend",
    "tmp/812_database_size",
    "scripts/metrics",
    "agents/database/dry-r29b",
]
assert git("diff", "--name-only", BASE, CANDIDATE, "--", *protected) == ""
with tempfile.TemporaryDirectory(prefix="r30-rejected-catalog-") as temporary:
    source = Path(temporary) / "candidate_migrations.py"
    source.write_text(candidate)
    spec = importlib.util.spec_from_file_location("t44.persistence.rejected_r30", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    rows = module._expected_rows()
    facts, conflicts = module._catalog_features(rows, "t44_review")
    smoke = dict(
        row_counts={kind: len(values) for kind, values in rows.items()},
        projected_features=len(facts),
        expected_conflicts=conflicts,
        limitation="Construction smoke only; no database or behavior acceptance",
    )
report = dict(
    base=BASE,
    candidate=CANDIDATE,
    exact_unchanged_functions=unchanged,
    protected_paths_with_zero_diff=protected,
    smoke=smoke,
)
output = ROOT / "agents/database/architecture-r30/candidate-boundary.json"
output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
print(json.dumps(report, ensure_ascii=False))
