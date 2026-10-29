"""Narrow static identity checks; no claim that the whole v2 rewrite is AST-equivalent."""

import ast
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
BASE = "e45a2b980c6ba8c61761f897414d54a10000409d"


def before(path):
    return subprocess.check_output(["git", "show", f"{BASE}:{path}"], cwd=ROOT).decode()


def node(path, name, original=False):
    source = before(path) if original else (ROOT / path).read_text()
    return next(
        item
        for item in ast.walk(ast.parse(source))
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and item.name == name
    )


def canonical(value):
    return ast.dump(value, include_attributes=False)


identical = {}
for path, names in {
    "backend/t44/services/runtime.py": (
        "_audit_integer",
        "authorize",
        "prepare",
        "audit",
        "rejection",
        "complete",
        "claim",
        "_claim",
        "execute",
    ),
    "backend/t44/services/common.py": (
        "check_version",
        "cas",
        "model",
        "wire",
        "plan",
        "plan_values",
        "page",
    ),
}.items():
    for name in names:
        assert canonical(node(path, name)) == canonical(node(path, name, True)), (path, name)
        identical[path + ":" + name] = True
path = "backend/t44/services/workflow.py"
old, new = node(path, "transitionTask", True), node(path, "transitionTask")
checks = {}
for action in ("DELIVER", "ROLLBACK"):

    def branch(method, action=action):
        return next(
            item
            for item in method.body
            if isinstance(item, ast.If)
            and canonical(item.test)
            == canonical(ast.parse(f"action == Action.{action} and assessment", mode="eval").body)
        )

    # Only the DTO-constructor tail changes; original ordered preflight statements are exact.
    assert [canonical(item) for item in branch(old).body[:2]] == [
        canonical(item) for item in branch(new).body[:2]
    ]
    checks[action + "_preflight_first_two_statements_AST_identical"] = True
# All legacy behavioral assertions and test bodies remain byte-structure-identical.
path = "tmp/backend/backend/domain/994_transitions.py"
old_tests = {
    n.name: canonical(n)
    for n in ast.walk(ast.parse(before(path)))
    if isinstance(n, ast.FunctionDef)
}
new_tests = {
    n.name: canonical(n)
    for n in ast.walk(ast.parse((ROOT / path).read_text()))
    if isinstance(n, ast.FunctionDef)
}
assert old_tests == new_tests
http = {}
for name in (
    "986_http",
    "987_faults",
    "856_release_error_priority",
    "859_dependency_delivered",
    "816_acceptance_followup_20261025",
):
    path = f"tmp/backend/contracts/{name}.py"
    raw = (ROOT / path).read_bytes()
    assert raw == before(path).encode(), path
    http[path] = hashlib.sha256(raw).hexdigest()
for path in (
    "backend/t44/api.py",
    "backend/t44/contracts/openapi.json",
    "specs/contracts/openapi.json",
):
    assert (ROOT / path).read_bytes() == before(path).encode(), path
receipt = {
    "base": BASE,
    "whole_rewrite_AST_equivalent": False,
    "identical_functions": identical,
    "workflow_preflight": checks,
    "legacy_test_function_bodies_and_assertions_AST_identical": True,
    "HTTP_test_sources_byte_identical": http,
    "api_and_frozen_openapi_sources_byte_identical": True,
    "scope": "static checks do not establish MySQL locks, performance or independent acceptance",
}
(HERE / "static-receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
print(
    json.dumps(
        {
            "identical_functions": len(identical),
            "workflow_preflights": checks,
            "HTTP_sources": len(http),
        }
    )
)
