"""Read committed source and collect fixed-count/static CSS evidence; no product writes."""

import collections
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
BASE = "a12e9e70b963bacafda3242bb6d82e53ee912ff1"
OLD = "043fc464acd327f6b7639e89dbe4f603fc524880"
CLOC = Path("/Users/yang/Desktop/nothing/软件开发大作业/.agent-worktrees/.runtime/cloc-2.10.pl")


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT)


def save(name, data):
    target = OUT / name
    with target.open("x") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def css_rules(text):
    # Preserve newlines for source positions. This stylesheet has no brace-bearing
    # strings, escaped braces or nested qualified rules; assert those boundaries.
    clean = re.sub(r"/\*.*?\*/", lambda m: "\n" * m.group().count("\n"), text, flags=re.S)
    assert not re.search(r"(['\"])[^\n]*[{}][^\n]*\1", clean)
    rules = []

    def block(start, end, context):
        cursor = start
        while cursor < end:
            opening = clean.find("{", cursor, end)
            if opening < 0:
                assert not clean[cursor:end].strip()
                return
            header = clean[cursor:opening].strip()
            depth = 1
            closing = opening + 1
            while depth:
                if clean[closing] == "{":
                    depth += 1
                elif clean[closing] == "}":
                    depth -= 1
                closing += 1
            body = clean[opening + 1:closing - 1]
            if header.startswith("@"):
                block(opening + 1, closing - 1, context + (header,))
            else:
                assert "{" not in body
                declarations = tuple(re.sub(r"\s+", " ", d.strip()) for d in body.split(";") if d.strip())
                source_start = cursor + len(clean[cursor:opening]) - len(clean[cursor:opening].lstrip())
                rules.append({"selector": header, "context": list(context),
                              "line": clean.count("\n", 0, source_start) + 1,
                              "physical_rule_lines": clean[source_start:closing].count("\n") + 1,
                              "declarations": declarations})
            cursor = closing

    block(0, len(clean), ())
    return rules


head = git("rev-parse", "HEAD").decode().strip()
count_command = [sys.executable, "scripts/metrics/source_count.py", "--cloc", str(CLOC),
                 "--output", str(OUT / "789_committed_count.json"), "--require-range"]
count = subprocess.run(count_command, cwd=ROOT, capture_output=True)
(OUT / "789_count.stdout").write_bytes(count.stdout)
(OUT / "789_count.stderr").write_bytes(count.stderr)
report = json.loads((OUT / "789_committed_count.json").read_text())
assert count.returncode == 1 and report["within_range"] is False
files = report["groups"]["application"]["files"]
frontend = {name: data for name, data in files.items() if name.startswith("frontend/")}
inventory = []
for name in sorted(frontend):
    contents = git("show", head + ":" + name)
    assert contents == git("show", BASE + ":" + name)
    assert contents == (ROOT / name).read_bytes()
    inventory.append({"path": name, "bytes": len(contents), "sha256": hashlib.sha256(contents).hexdigest(),
                      "raw_physical_lines": len(contents.splitlines()), **frontend[name]})
counter = "scripts/metrics/source_count.py"
assert git("show", head + ":" + counter) == git("show", BASE + ":" + counter)
unchanged = subprocess.run(["git", "diff", "--exit-code", BASE, head, "--", "backend/t44", "frontend", counter], cwd=ROOT, capture_output=True)
old_frontend = subprocess.run(["git", "diff", "--exit-code", OLD, BASE, "--", "frontend", counter], cwd=ROOT, capture_output=True)
assert unchanged.returncode == old_frontend.returncode == 0
save("789_source_inventory.json", {
    "count_commit": head, "base_commit": BASE, "count_command": count_command,
    "count_exit": count.returncode, "stderr_bytes": len(count.stderr),
    "application_code": report["groups"]["application"]["summary"]["code"],
    "frontend_code": sum(data["code"] for data in frontend.values()),
    "frontend_files": len(frontend), "frontend": inventory,
    "counter_sha256": hashlib.sha256((ROOT / counter).read_bytes()).hexdigest(),
    "cloc_sha256": hashlib.sha256(CLOC.read_bytes()).hexdigest(),
    "application_frontend_counter_diff_from_base_exit": unchanged.returncode,
    "old_round9_frontend_counter_diff_to_base_exit": old_frontend.returncode,
    "product_changed": False, "tests_executed": False, "cloud_operations": False,
})

css = (ROOT / "frontend/src/styles.css").read_text()
rules = css_rules(css)
groups = collections.defaultdict(list)
for rule in rules:
    groups[(tuple(rule["context"]), tuple(rule["declarations"]))].append(rule)
duplicates = [group for group in groups.values() if len(group) > 1]
all_contexts = collections.defaultdict(list)
for rule in rules:
    all_contexts[tuple(rule["declarations"])].append(rule)
cross_context = [group for group in all_contexts.values()
                 if len({tuple(rule["context"]) for rule in group}) > 1]
save("789_css_static_audit.json", {
    "source": "frontend/src/styles.css", "source_sha256": hashlib.sha256(css.encode()).hexdigest(),
    "method": "recursive at-rule blocks; identical ordered declaration tuples within same at-rule context",
    "limits": ["Static inventory only; no cascade equivalence or browser acceptance claimed",
               "Exact-rule merge upper bound ignores order and specificity conflicts",
               "Partial-declaration reuse leaves original rule lines and adds common selectors/tokens",
               "No source rewrite, minification, property packing or CSS prototype performed"],
    "css_cloc_code": frontend["frontend/src/styles.css"]["code"],
    "frontend_cloc_code": sum(data["code"] for data in frontend.values()),
    "qualified_rule_count": len(rules),
    "same_context_exact_duplicate_groups": duplicates,
    "same_context_mergeable_rule_line_upper_bound": sum(sum(r["physical_rule_lines"] for r in group[1:]) for group in duplicates),
    "same_declarations_different_context_groups": cross_context,
    "rules": rules,
})
print(json.dumps({"count_commit": head, "application_code": report["groups"]["application"]["summary"]["code"],
                  "frontend_code": sum(data["code"] for data in frontend.values()),
                  "css_code": frontend["frontend/src/styles.css"]["code"],
                  "same_context_exact_groups": len(duplicates),
                  "same_context_line_upper_bound": sum(sum(r["physical_rule_lines"] for r in group[1:]) for group in duplicates),
                  "cross_context_groups": len(cross_context)}, ensure_ascii=False))
