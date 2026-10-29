"""Audit explicit consumers only in committed public application/developer-test roots."""

import argparse
import ast
import json
import subprocess
from pathlib import Path

TARGETS = {
    "t44.services.workflow": {
        "t44.domain.commands": 0,
        "t44.domain.models": 0,
        "codes": 1,
    },
    "t44.persistence.schema": {"sqlalchemy": 0},
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not args.run:
        parser.error("Explicit --run required")
    root = Path(__file__).resolve().parents[2]
    removed = {}
    for module, sources in TARGETS.items():
        name = "backend/" + module.replace(".", "/") + ".py"
        tree = ast.parse((root / name).read_text())
        removed[module] = sorted(
            {
                alias.asname or alias.name
                for node in tree.body
                if isinstance(node, ast.ImportFrom) and sources.get(node.module) == node.level
                for alias in node.names
            }
        )
    roots = ["backend", "tmp/backend", "tmp/frontend", "tmp/ci", "tmp/deployment", "scripts"]
    paths = subprocess.check_output(
        [
            "git",
            "ls-tree",
            "-r",
            "--name-only",
            "HEAD",
            "--",
            *roots,
        ],
        cwd=root,
        text=True,
    ).splitlines()
    findings = []
    visited = 0
    for path in paths:
        if not path.endswith(".py"):
            continue
        data = subprocess.check_output(["git", "show", f"HEAD:{path}"], cwd=root)
        tree = ast.parse(data)
        visited += 1
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.level == 0 and node.module in removed:
                for alias in node.names:
                    if alias.name == "*" or alias.name in removed[node.module]:
                        findings.append(
                            {
                                "file": path,
                                "line": node.lineno,
                                "kind": "explicit removed symbol import",
                                "module": node.module,
                                "symbol": alias.name,
                            }
                        )
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                for module, names in removed.items():
                    for name in names:
                        if module + "." + name in node.value:
                            findings.append(
                                {
                                    "file": path,
                                    "line": node.lineno,
                                    "kind": "literal full target reference",
                                    "module": module,
                                    "symbol": name,
                                }
                            )
    result = {
        "source": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=root, text=True
        ).strip(),
        "scanned_git_roots": roots,
        "python_files": visited,
        "removed_implicit_symbols": removed,
        "explicit_consumer_findings": findings,
        "limitations": [
            "No claim about uncommitted/private tests, external consumers, relative aliases or dynamic getattr/monkeypatch",
            "A zero finding count is not a module-export or runtime binding compatibility proof",
            "Namespace changes still need owner review and functional regression before production",
        ],
    }
    with args.output.open("x") as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"python_files": visited, "explicit_consumer_findings": len(findings)}))


if __name__ == "__main__":
    main()
