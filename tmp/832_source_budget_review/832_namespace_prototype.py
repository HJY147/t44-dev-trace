"""Text-only namespace prototype; no application imports, database or network access."""

import argparse
import ast
import hashlib
import json
import subprocess
from pathlib import Path

BASE = "ade5e4c1998b4c2f014afde8c011645c6c5a7412"
CLOC_SHA = "bf59272455172108072a0a106379f7509fd4349bdcfd85203bac038ccd286d83"
PLANS = {
    "backend/t44/domain/state_machine.py": (
        (
            "commands",
            1,
            "t44.domain.commands",
            "domain_commands",
            "from . import commands as domain_commands",
        ),
        (
            "models",
            1,
            "t44.domain.models",
            "domain_models",
            "from . import models as domain_models",
        ),
    ),
    "backend/t44/services/workflow.py": (
        (
            "t44.domain.commands",
            0,
            "t44.domain.commands",
            "domain_commands",
            "from t44.domain import commands as domain_commands",
        ),
        (
            "t44.domain.models",
            0,
            "t44.domain.models",
            "domain_models",
            "from t44.domain import models as domain_models",
        ),
        ("codes", 1, "t44.services.codes", "codes", "from . import codes"),
    ),
    "backend/t44/persistence/schema.py": (
        ("sqlalchemy", 0, "sqlalchemy", "sa", "import sqlalchemy as sa"),
    ),
}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def prototype(source, plans):
    tree = ast.parse(source)
    lines = source.splitlines(keepends=True)
    offsets = [0]
    for line in lines:
        offsets.append(offsets[-1] + len(line))

    def offset(line, byte_column):
        return offsets[line - 1] + len(lines[line - 1].encode()[:byte_column].decode())

    imports = {}
    replacements = []
    for module, level, absolute, alias, statement in plans:
        nodes = [
            node
            for node in tree.body
            if isinstance(node, ast.ImportFrom) and node.module == module and node.level == level
        ]
        if len(nodes) != 1:
            raise ValueError(f"Expected one exact import block: {module}")
        node = nodes[0]
        for name in node.names:
            if name.asname or name.name == "*":
                raise ValueError("Prototype supports explicit non-aliased imports only")
            imports[name.name] = (absolute, alias)
        replacements.append((offsets[node.lineno - 1], offsets[node.end_lineno], statement + "\n"))
    bound = {
        node.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Name) and isinstance(node.ctx, (ast.Store, ast.Del))
    }
    bound.update(node.arg for node in ast.walk(tree) if isinstance(node, ast.arg))
    bound.update(
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
    )
    if bound & imports.keys():
        raise ValueError("A locally bound symbol would shadow a targeted import")
    if bound & {plan[3] for plan in plans}:
        raise ValueError("A chosen module alias would be shadowed")
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load) and node.id in imports:
            alias = imports[node.id][1]
            replacements.append(
                (
                    offset(node.lineno, node.col_offset),
                    offset(node.end_lineno, node.end_col_offset),
                    f"{alias}.{node.id}",
                )
            )
    for start, end, value in sorted(replacements, reverse=True):
        source = source[:start] + value + source[end:]
    return source, {name: module + "." + name for name, (module, _) in imports.items()}


class Canonical(ast.NodeTransformer):
    def __init__(self, symbols):
        self.symbols = symbols

    def _reference(self, node):
        tail = []
        while isinstance(node, ast.Attribute):
            tail.append(node.attr)
            node = node.value
        if isinstance(node, ast.Name) and node.id in self.symbols:
            return ".".join([self.symbols[node.id], *reversed(tail)])
        return None

    def visit_Attribute(self, node):
        reference = self._reference(node)
        if reference is not None:
            return ast.Name(id=reference, ctx=node.ctx)
        return self.generic_visit(node)

    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Load) and node.id in self.symbols:
            return ast.Name(id=self.symbols[node.id], ctx=node.ctx)
        return node

    def visit_ImportFrom(self, node):
        names = {name.asname or name.name for name in node.names}
        return None if names & self.symbols.keys() else node

    def visit_Import(self, node):
        names = {name.asname or name.name.split(".")[0] for name in node.names}
        return None if names & self.symbols.keys() else node


def signature(source, symbols):
    return ast.dump(Canonical(symbols).visit(ast.parse(source)), include_attributes=False)


def count(cloc, files, listing, output):
    listing.write_text("\n".join(str(path) for path in files) + "\n")
    subprocess.run(
        [
            "/usr/bin/perl",
            str(cloc),
            "--quiet",
            "--json",
            "--by-file",
            "--list-file=" + str(listing),
            "--report-file=" + str(output),
        ],
        check=True,
        capture_output=True,
    )
    return json.loads(output.read_text())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--python", type=Path, required=True)
    parser.add_argument("--cloc", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    if not args.run:
        parser.error("Explicit --run is required")
    root = Path(__file__).resolve().parents[2]
    if digest(args.cloc.read_bytes()) != CLOC_SHA:
        raise ValueError("Pinned cloc asset mismatch")
    args.output_dir.mkdir(parents=True, exist_ok=False)
    before, after, originals = [], [], {}
    for path, plans in PLANS.items():
        raw = subprocess.check_output(["git", "show", f"{BASE}:{path}"], cwd=root)
        if (root / path).read_bytes() != raw:
            raise ValueError("Production source drift")
        old = args.output_dir / "before" / path
        new = args.output_dir / "after" / path
        old.parent.mkdir(parents=True, exist_ok=True)
        new.parent.mkdir(parents=True, exist_ok=True)
        old.write_bytes(raw)
        transformed, old_symbols = prototype(raw.decode(), plans)
        new.write_text(transformed)
        originals[path] = (raw, old_symbols)
        before.append(old)
        after.append(new)
    for command in (
        ["check", "--select", "I", "--fix"],
        ["format"],
        ["check"],
    ):
        result = subprocess.run(
            [
                str(args.python),
                "-m",
                "ruff",
                *command,
                "--config",
                str(root / "backend/pyproject.toml"),
                *map(str, after),
            ],
            capture_output=True,
            text=True,
        )
        (args.output_dir / ("ruff-" + "-".join(command[:2]) + ".log")).write_text(
            result.stdout + result.stderr
        )
        result.check_returncode()
    receipt = {
        "source": BASE,
        "operator": "reviewer AI prototype; not independent acceptance",
        "files": {},
    }
    for path, plans in PLANS.items():
        raw, old_symbols = originals[path]
        new = (args.output_dir / "after" / path).read_bytes()
        new_symbols = {plan[3]: plan[2] for plan in plans}
        same = signature(raw.decode(), old_symbols) == signature(new.decode(), new_symbols)
        if not same:
            raise ValueError(f"Canonical AST mismatch: {path}")
        compile(new, path, "exec")
        receipt["files"][path] = {
            "before_sha256": digest(raw),
            "after_sha256": digest(new),
            "resolved_AST_equal": same,
            "syntax_compiles_without_module_execution": True,
        }
    old_count = count(
        args.cloc, before, args.output_dir / "before.list", args.output_dir / "before-cloc.json"
    )
    new_count = count(
        args.cloc, after, args.output_dir / "after.list", args.output_dir / "after-cloc.json"
    )
    receipt.update(
        {
            "cloc_sha256": CLOC_SHA,
            "before": old_count["SUM"],
            "after": new_count["SUM"],
            "net_reduction_in_prototype_only": old_count["SUM"]["code"] - new_count["SUM"]["code"],
            "production_modified": False,
            "actual_production_savings": 0,
            "limitations": [
                "AST compares resolved symbol references; it does not prove runtime behavior or monkeypatch compatibility",
                "Implicit imported module attributes disappear; module export policy needs owner review",
                "No product, database, HTTP, functional or independent acceptance tests were run",
            ],
        }
    )
    with (args.output_dir / "receipt.json").open("x") as stream:
        json.dump(receipt, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(
        json.dumps(
            {
                key: receipt[key]
                for key in (
                    "before",
                    "after",
                    "net_reduction_in_prototype_only",
                    "actual_production_savings",
                )
            }
        )
    )


if __name__ == "__main__":
    main()
