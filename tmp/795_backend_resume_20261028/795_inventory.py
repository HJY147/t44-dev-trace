"""Read only committed product source and reconcile the existing fixed cloc receipt."""

import ast
import hashlib
import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = "22f666e25d2b7280224e58eb1c91cf6be0077ac7"
PRODUCT = "f4bd382d4668130793fc553df9ce6363c4656ea6"
COUNT = "tmp/807_combined_optimizations/messaging-committed-count.json"


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT)


def main():
    output = ROOT / "tmp/795_backend_resume_20261028/inventory.json"
    fd = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o644)
    with os.fdopen(fd, "w") as receipt:
        raw_count = git("show", f"{BASE}:{COUNT}")
        count = json.loads(raw_count)
        source = count["commit"]
        files = count["groups"]["application"]["files"]
        inventory = []
        for name, metrics in sorted(files.items()):
            raw = git("show", f"{BASE}:{name}")
            assert raw == git("show", f"{source}:{name}"), name
            assert raw == git("show", f"{PRODUCT}:{name}"), name
            assert raw == (ROOT / name).read_bytes(), name
            if name == "backend/t44/api.py" or name.startswith(
                ("backend/t44/domain/", "backend/t44/services/", "backend/t44/contracts/")
            ):
                tree = ast.parse(raw, filename=name)
                methods = []
                for node in tree.body:
                    children = node.body if isinstance(node, ast.ClassDef) else [node]
                    for child in children:
                        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            methods.append(
                                {"name": child.name, "start": child.lineno, "end": child.end_lineno}
                            )
                inventory.append(
                    {
                        "path": name,
                        "sha256": hashlib.sha256(raw).hexdigest(),
                        "physical_lines": len(raw.splitlines()),
                        "existing_fixed_cloc": metrics["code"],
                        "functions_or_methods": methods,
                    }
                )
        result = {
            "operator": "backend AI",
            "base": BASE,
            "product": PRODUCT,
            "analysis_script_commit": git("rev-parse", "HEAD").decode().strip(),
            "count_receipt": COUNT,
            "count_receipt_sha256": hashlib.sha256(raw_count).hexdigest(),
            "count_receipt_source": source,
            "all_counted_product_files_byte_equal": len(files),
            "existing_application_lines": count["groups"]["application"]["summary"]["code"],
            "existing_backend_scope_lines": sum(item["existing_fixed_cloc"] for item in inventory),
            "inventory": inventory,
            "new_cloc_executed": False,
            "new_product_tests_executed": False,
            "production_changes": 0,
            "limitations": [
                "Reconciles an existing exact-byte count; does not execute a new cloc run.",
                "AST line spans identify responsibilities, not removable duplication or cloc cost.",
                "No application imports, database, cloud, load, CI, or independent tests executed.",
            ],
        }
        json.dump(result, receipt, ensure_ascii=False, indent=2)
        receipt.write("\n")
        receipt.flush()
        os.fsync(receipt.fileno())
    print(json.dumps({key: value for key, value in result.items() if key != "inventory"}))


if __name__ == "__main__":
    main()
