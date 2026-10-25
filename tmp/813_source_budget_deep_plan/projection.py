"""Verify the existing schema projector on one explicit response mapping only."""

import ast
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
NAME = "backend/t44/scheduling/facade.py"
REPLACEMENT = '''return model(
            "EscalationEvent",
            row,
            id=row["event_id"],
            recipient_ids=outbox["recipients"],
            disposition=disposition,
            scan_run_id=uuid_text(g.get("scan_runs", row["scan_run_id"])["run_key"]),
            created_at=row["observed_at"],
            handled_count=sum(n["handled_at"] is not None for n in notices),
        )'''


def dump(value):
    return ast.dump(value, include_attributes=False)


def main():
    source = (ROOT / NAME).read_text()
    original = ast.parse(source)
    old = next(n for n in ast.walk(original) if isinstance(n, ast.FunctionDef) and n.name == "event")
    statement = old.body[-1]
    lines = source.splitlines(keepends=True)
    start = sum(map(len, lines[:statement.lineno - 1])) + statement.col_offset
    end = sum(map(len, lines[:statement.end_lineno - 1])) + statement.end_col_offset
    changed = source[:start] + REPLACEMENT + source[end:]
    changed = changed.replace("import page, uuid_text, wire", "import model, page, uuid_text, wire")
    tree = ast.parse(changed)
    compile(tree, NAME, "exec")
    new = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "event")
    assert [dump(n) for n in old.body[:-1]] == [dump(n) for n in new.body[:-1]]
    schema = json.loads((ROOT / "backend/t44/contracts/openapi.json").read_text())
    keys = schema["components"]["schemas"]["EscalationEvent"]["properties"]
    extras = {kw.arg: kw.value for kw in new.body[-1].value.keywords}
    expressions = [extras.get(key, ast.parse(f"row[{key!r}]", mode="eval").body) for key in keys]
    expanded = ast.Call(ast.Name("wire", ast.Load()),
                        [ast.Dict([ast.Constant(key) for key in keys], expressions)], [])
    assert dump(statement.value) == dump(expanded)
    info = {"field_expression_ast_equal": True, "schema_fields": list(keys),
            "syntax_compile": True, "product_tests_executed": 0, "production_changes": 0}
    for directory, contents in (("projection-before", source), ("projection-after", changed)):
        target = HERE / directory / NAME
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(contents)
        cloc = HERE / "cloc-2.10.pl"
        assert hashlib.sha256(cloc.read_bytes()).hexdigest() == (
            "bf59272455172108072a0a106379f7509fd4349bdcfd85203bac038ccd286d83")
        output = HERE / (directory + "-cloc.json")
        subprocess.run(["/usr/bin/perl", str(cloc), "--quiet", "--json", "--by-file",
                        "--report-file=" + str(output), str(target)], check=True, capture_output=True)
        info[directory] = json.loads(output.read_text())["SUM"]["code"]
    info["saving"] = info["projection-before"] - info["projection-after"]
    (HERE / "projection-verification.json").write_text(json.dumps(info, indent=2) + "\n")
    print(json.dumps(info, indent=2))


if __name__ == "__main__":
    main()
