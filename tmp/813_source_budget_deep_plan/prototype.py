"""Build and statically verify a bounded pure scan-row factory candidate."""

import ast
import copy
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
FILES = ("backend/t44/persistence/scans.py", "backend/t44/scheduling/facade.py")
HELPER = '''def scan_run_values(*, run_key, rule_version, rule_snapshot, rule_hash, cutoff_at):
    return dict(
        run_key=run_key,
        rule_version=rule_version,
        rule_snapshot=rule_snapshot,
        rule_hash=rule_hash,
        cutoff_at=cutoff_at,
        status=1,
        last_task_id=0,
        scanned_count=0,
        created_count=0,
        duplicate_count=0,
        started_at=cutoff_at,
        heartbeat_at=cutoff_at,
        finished_at=None,
        error_code=None,
    )


'''
CALLS = (
    '''scan_run_values(
                            run_key=uuid_to_bytes(run_id),
                            rule_version=rule_version,
                            rule_snapshot=rule_snapshot,
                            rule_hash=rule_hash,
                            cutoff_at=now,
                        )''',
    '''scan_run_values(
                            run_key=key,
                            rule_version=rules.version,
                            rule_snapshot=rules.snapshot(),
                            rule_hash=rules.raw_hash,
                            cutoff_at=c.clock,
                        )''',
)
IMPORT = "from t44.persistence.scans import scan_run_values\n"
helper_expr = ast.parse(HELPER).body[0].body[0].value


class Bind(ast.NodeTransformer):
    def __init__(self, arguments):
        self.arguments = arguments

    def visit_Name(self, node):
        return copy.deepcopy(self.arguments.get(node.id, node))


class Inline(ast.NodeTransformer):
    def visit_Call(self, node):
        if isinstance(node.func, ast.Name) and node.func.id == "scan_run_values":
            arguments = {kw.arg: kw.value for kw in node.keywords}
            return Bind(arguments).visit(copy.deepcopy(helper_expr))
        return self.generic_visit(node)


def canonical(tree):
    return ast.dump(tree, include_attributes=False)


def main():
    cloc = HERE / "cloc-2.10.pl"
    expected = "bf59272455172108072a0a106379f7509fd4349bdcfd85203bac038ccd286d83"
    assert hashlib.sha256(cloc.read_bytes()).hexdigest() == expected
    result = {"baseline": "d9e971a631a970d59bdc96923f184c820f6de484", "files": []}
    for name, replacement in zip(FILES, CALLS, strict=True):
        source = (ROOT / name).read_text()
        before = ast.parse(source)
        candidates = [
            node for node in ast.walk(before)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
            and node.func.id == "dict" and node.keywords
            and [kw.arg for kw in node.keywords][:5]
            == ["run_key", "rule_version", "rule_snapshot", "rule_hash", "cutoff_at"]
        ]
        assert len(candidates) == 1
        node = candidates[0]
        lines = source.splitlines(keepends=True)
        start = sum(map(len, lines[:node.lineno - 1])) + node.col_offset
        end = sum(map(len, lines[:node.end_lineno - 1])) + node.end_col_offset
        changed = source[:start] + replacement + source[end:]
        if name.endswith("persistence/scans.py"):
            changed = changed.replace("class ScanStore:", HELPER + "class ScanStore:", 1)
        else:
            changed = changed.replace("from t44.persistence import PersistenceIntegrityError\n",
                                      "from t44.persistence import PersistenceIntegrityError\n" + IMPORT)
        after = ast.parse(changed)
        compile(after, name, "exec")
        stripped = copy.deepcopy(after)
        stripped.body = [
            item for item in stripped.body
            if not (isinstance(item, ast.FunctionDef) and item.name == "scan_run_values")
            and not (isinstance(item, ast.ImportFrom) and item.module == "t44.persistence.scans")
        ]
        assert canonical(before) == canonical(Inline().visit(stripped)), name
        for directory, value in (("before", source), ("after", changed)):
            target = HERE / directory / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(value)
        result["files"].append({"path": name, "inline_ast_equal": True,
                               "syntax_compile": True,
                               "before_sha256": hashlib.sha256(source.encode()).hexdigest(),
                               "after_sha256": hashlib.sha256(changed.encode()).hexdigest()})
    for directory in ("before", "after"):
        output = HERE / (directory + "-cloc.json")
        command = ["/usr/bin/perl", str(cloc), "--quiet", "--json", "--by-file",
                   "--report-file=" + str(output), *[str(HERE / directory / f) for f in FILES]]
        completed = subprocess.run(command, check=True, capture_output=True, text=True)
        result[directory] = {"code": json.loads(output.read_text())["SUM"]["code"],
                             "exit_code": completed.returncode}
    result["saving"] = result["before"]["code"] - result["after"]["code"]
    result["cloc_sha256"] = expected
    result["production_changes"] = 0
    result["application_tests_executed"] = 0
    (HERE / "verification.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
