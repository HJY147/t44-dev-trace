"""Verify the complete production delta is only the catalog registration shape."""

import ast
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = "a92e5e73da93ba23748c3bab113103036c395d50"
SOURCE = "backend/t44/persistence/migrations.py"


def git(*arguments):
    return subprocess.check_output(["git", *arguments], cwd=ROOT).decode().strip()


before = ast.parse(git("show", f"{BASE}:{SOURCE}"))
after = ast.parse(git("show", f"HEAD:{SOURCE}"))
catalog = next(node for node in before.body if getattr(node, "name", None) == "_catalog_defects")
registration = next(
    node
    for node in catalog.body
    if isinstance(node, ast.Assign)
    and isinstance(node.targets[0], ast.Name)
    and node.targets[0].id == "queries"
)
entries = registration.value.elts
labels = [entry.elts[0].value for entry in entries]
assert len(labels) == len(set(labels)) == 4
registration.value = ast.Dict(
    keys=[entry.elts[0] for entry in entries],
    values=[ast.Tuple(elts=entry.elts[1:], ctx=ast.Load()) for entry in entries],
)
loop = next(
    node
    for node in ast.walk(catalog)
    if isinstance(node, ast.For) and isinstance(node.iter, ast.Name) and node.iter.id == "queries"
)
loop.target = ast.parse("label, (query, expected) = ()").body[0].targets[0]
loop.iter = ast.parse("queries.items()", mode="eval").body
assert ast.dump(before) == ast.dump(after)
changed = git("diff", "--name-only", BASE, "HEAD", "--", "backend/t44").splitlines()
assert changed == [SOURCE]
protected = [
    "specs",
    "backend/pyproject.toml",
    "backend/requirements.lock",
    "backend/t44/persistence/schema.py",
    "backend/t44/persistence/schema_v1.sql",
    "backend/t44/persistence/seed.py",
    "backend/t44/persistence/rows.py",
    "backend/t44/persistence/scans.py",
    "backend/t44/persistence/uow.py",
    "backend/t44/persistence/engine.py",
    "tmp/backend",
    "tmp/812_database_size",
    "scripts/metrics",
    "scripts/ci",
]
assert git("diff", "--name-only", BASE, "HEAD", "--", *protected) == ""
report = dict(
    base=BASE,
    source=git("rev-parse", "HEAD"),
    changed_production=changed,
    exact_ast_after_registration_rewrite=True,
    query_labels=labels,
    protected_paths_with_zero_diff=protected,
)
output = ROOT / "agents/database/dry-r29b/boundaries.json"
output.write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report))
