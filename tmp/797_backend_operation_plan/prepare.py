"""Archive exact public base bytes and build a separately counted temporary probe."""

import ast
import hashlib
import importlib.util
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
BASE = "f4bd382d4668130793fc553df9ce6363c4656ea6"
CLOC = ROOT.parent / ".runtime/cloc-2.10.pl"
TOOL_HASH = "bf59272455172108072a0a106379f7509fd4349bdcfd85203bac038ccd286d83"
TARGETS = {
    "tasks": {"addTaskDependency": "manager", "removeTaskDependency": "manager"},
    "reviews": {"createTaskReview": "reviewer", "createReleaseAssessment": "manager"},
}


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT)


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def main():
    assert hashlib.sha256(CLOC.read_bytes()).hexdigest() == TOOL_HASH
    manifest, proofs = {}, {}
    for module, operations in TARGETS.items():
        relative = Path(f"backend/t44/services/{module}.py")
        raw = git("show", f"{BASE}:{relative}")
        manifest[str(relative)] = hashlib.sha256(raw).hexdigest()
        original = HERE / "baseline" / relative
        original.parent.mkdir(parents=True, exist_ok=True)
        original.write_bytes(raw)
        text = raw.decode()
        tree = ast.parse(text)
        service = next(item for item in tree.body if isinstance(item, ast.ClassDef))
        for method in service.body:
            if isinstance(method, ast.FunctionDef) and method.name in operations:
                role = operations[method.name]
                prefix = f"        c.{role}()\n        row = c.task(g)\n"
                assert text.count(prefix) >= 1
                signature = f"    def {method.name}(self, g, c):\n{prefix}"
                replacement = (
                    f"    @OperationPlan(Call.{role})\n"
                    f"    def {method.name}(self, g, c, row: dict):\n"
                )
                assert text.count(signature) == 1
                text = text.replace(signature, replacement)
        text = text.replace("from .common import ", "from .common import Call, ", 1)
        text = text.replace(
            "from .errors import require\n",
            ("from .errors import require\nfrom .operation_plan import OperationPlan\n"),
        )
        candidate = HERE / "candidate" / relative
        candidate.write_text(text)
        candidate_tree = ast.parse(text)
        candidate_service = next(
            item for item in candidate_tree.body if isinstance(item, ast.ClassDef)
        )
        for before, after in zip(service.body, candidate_service.body, strict=True):
            assert before.name == after.name
            if before.name in operations:
                identical = ast.dump(ast.Module(before.body[2:], [])) == ast.dump(
                    ast.Module(after.body, [])
                )
                assert identical
                proofs[before.name] = {
                    "original_prefix": [ast.unparse(item) for item in before.body[:2]],
                    "remaining_statements_identical_and_ordered": identical,
                    "body_statements": len(after.body),
                }
            else:
                assert ast.dump(before) == ast.dump(after)
    write_json(HERE / "source-manifest.json", {"base": BASE, "sha256": manifest})
    write_json(HERE / "ast-proof.json", proofs)

    spec = importlib.util.spec_from_file_location(
        "source_count", ROOT / "scripts/metrics/source_count.py"
    )
    classifier = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(classifier)
    names = (
        git("ls-tree", "-r", "--name-only", BASE, "--", "backend/t44", "frontend")
        .decode()
        .splitlines()
    )
    selected = [name for name in names if classifier.classify(name) == "application"]
    counts = {}
    for phase in ("baseline", "candidate"):
        snapshot = HERE / "counted" / phase
        for name in selected:
            target = snapshot / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(git("show", f"{BASE}:{name}"))
        if phase == "candidate":
            for source in (HERE / "candidate/backend/t44/services").glob("*.py"):
                (snapshot / "backend/t44/services" / source.name).write_bytes(source.read_bytes())
        targets = sorted(path for path in snapshot.rglob("*") if path.is_file())
        listing = HERE / f"{phase}-count.list"
        listing.write_text("\n".join(map(str, targets)) + "\n")
        output = HERE / f"{phase}-cloc.json"
        subprocess.run(
            [
                "/usr/bin/perl",
                str(CLOC),
                "--quiet",
                "--json",
                "--by-file",
                "--list-file=" + str(listing),
                "--report-file=" + str(output),
            ],
            check=True,
            capture_output=True,
        )
        data = json.loads(output.read_text())
        counts[phase] = {
            "application": data["SUM"]["code"],
            "file_count": data["SUM"]["nFiles"],
            "services": {
                Path(name).name: record["code"]
                for name, record in data.items()
                if name not in ("header", "SUM")
                and Path(name).name in ("tasks.py", "reviews.py", "operation_plan.py")
            },
        }
    write_json(
        HERE / "count.json",
        {
            "base": BASE,
            "tool": "cloc 2.10",
            "tool_sha256": TOOL_HASH,
            **counts,
            "net_saved": counts["baseline"]["application"] - counts["candidate"]["application"],
            "scope": "same fixed application classifier, candidate helper counted at product path",
        },
    )
    print((HERE / "count.json").read_text())


if __name__ == "__main__":
    main()
