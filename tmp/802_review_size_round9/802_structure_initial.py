"""Read committed application Python only; report exact clones and record-shape candidates."""

import ast
import hashlib
import json
import subprocess
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REF = "043fc464"


def main():
    source_sha = subprocess.check_output(
        ["git", "rev-parse", REF], cwd=ROOT, text=True
    ).strip()
    names = subprocess.check_output(
        ["git", "ls-tree", "-r", "--name-only", source_sha, "--", "backend/t44"],
        cwd=ROOT,
        text=True,
    ).splitlines()
    clones, shapes, hashes = defaultdict(list), defaultdict(list), {}
    for name in names:
        if not name.endswith(".py"):
            continue
        raw = subprocess.check_output(["git", "show", f"{source_sha}:{name}"], cwd=ROOT)
        hashes[name] = hashlib.sha256(raw).hexdigest()
        tree = ast.parse(raw)
        for node in ast.walk(tree):
            keys = None
            if isinstance(node, ast.Dict) and all(
                isinstance(key, ast.Constant) and isinstance(key.value, str) for key in node.keys
            ):
                keys = tuple(sorted(key.value for key in node.keys))
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                if node.func.id == "dict" and not node.args and all(
                    key.arg is not None for key in node.keywords
                ):
                    keys = tuple(sorted(key.arg for key in node.keywords))
            if keys and len(keys) >= 5:
                shapes[keys].append({"file": name, "line": node.lineno})
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for parent in ast.walk(node):
                for _, value in ast.iter_fields(parent):
                    if not isinstance(value, list) or not all(
                        isinstance(statement, ast.stmt) for statement in value
                    ):
                        continue
                    for index in range(len(value) - 2):
                        block = value[index : index + 3]
                        if any(isinstance(x, (ast.Import, ast.ImportFrom)) for x in block):
                            continue
                        key = ast.dump(ast.Module(body=block, type_ignores=[]))
                        site = {"file": name, "function": node.name, "line": block[0].lineno}
                        if site not in clones[key]:
                            clones[key].append(site)
    result = {
        "source_sha": source_sha,
        "scope": "committed backend/t44/*.py only",
        "source_hashes": hashes,
        "exact_three_statement_groups": [
            {"ast_sha256": hashlib.sha256(key.encode()).hexdigest(), "sites": sites}
            for key, sites in clones.items()
            if len({(site["file"], site["line"]) for site in sites}) > 1
        ],
        "shared_literal_record_shapes": [
            {"keys": keys, "sites": sites}
            for keys, sites in shapes.items()
            if len(sites) > 1
        ],
        "limits": [
            "Exact AST clones do not identify differently named equivalent algorithms",
            "Identical key sets do not prove value, policy, order or transaction equivalence",
            "No product import, database, test or independent artifact is accessed",
            "No physical-code savings is established by this analysis",
        ],
    }
    output = ROOT / "agents/reviewer/evidence/round9/structure-analysis.json"
    with output.open("x") as stream:
        json.dump(result, stream, indent=2)
        stream.write("\n")
    print(json.dumps({"source_sha": source_sha, "exact_groups": len(result["exact_three_statement_groups"]), "record_shapes": len(result["shared_literal_record_shapes"])}))


if __name__ == "__main__":
    main()
