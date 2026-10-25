"""Bind developer evidence to exact current product bytes; no service or credential use."""

import hashlib
import json
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
files = sorted(
    [
        *ROOT.glob("backend/t44/domain/**/*.py"),
        *ROOT.glob("backend/t44/services/**/*.py"),
        ROOT / "backend/t44/api.py",
        ROOT / "backend/t44/contracts/__init__.py",
    ]
)
manifest = {
    str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest() for path in files
}
PRODUCT_COMMIT = "a07ad028a8efad4ecd186246bf2b7935c361b117"
for path in manifest:
    committed = subprocess.check_output(["git", "show", f"{PRODUCT_COMMIT}:{path}"], cwd=ROOT)
    if hashlib.sha256(committed).hexdigest() != manifest[path]:
        raise RuntimeError("Product bytes changed after the tested stage commit")
counts = {
    phase: json.loads((HERE / (phase + "-cloc.json")).read_text())["SUM"]["code"]
    for phase in ("before", "after")
}
tests = {}
for label, filename in (("domain", "domain-v2-junit.xml"), ("http", "http-v2-junit.xml")):
    cases = list(ET.parse(HERE / filename).getroot().iter("testcase"))
    tests[label] = {
        "tests": len(cases),
        **{
            name: sum(case.find(name) is not None for case in cases)
            for name in ("failure", "error", "skipped")
        },
    }
    assert all(tests[label][key] == 0 for key in ("failure", "error", "skipped"))
receipt = {
    "base": "e45a2b980c6ba8c61761f897414d54a10000409d",
    "product_base": "935ab5b93bea788672c2b4a088c79cfeed848954",
    "rollback_checkpoint": "a19af36",
    "rollback_checkpoint_is_full_test_green": False,
    "candidate_branch": "codex/backend-domain-v2-size-20261025",
    "candidate_product_commit": PRODUCT_COMMIT,
    "product_bytes_equal_stage_commit": True,
    "no_test_runtime_dependency": json.loads(
        (HERE / "no-test-runtime-dependency.json").read_text()
    ),
    "issue3": "https://github.com/HJY147/t44-dev-trace/issues/3#issuecomment-6397299657",
    "operator": "backend AI",
    "product_sha256": manifest,
    "deleted_product_files": ["backend/t44/domain/commands.py"],
    "fixed_cloc": {
        **counts,
        "net_reduction": counts["before"] - counts["after"],
        "version": "2.10",
        "tool_sha256": "bf59272455172108072a0a106379f7509fd4349bdcfd85203bac038ccd286d83",
    },
    "tests": tests,
    "legacy_migration": json.loads((HERE / "legacy-migration-receipt.json").read_text()),
    "differential": json.loads((HERE / "differential-receipt.json").read_text()),
    "static": json.loads((HERE / "static-receipt.json").read_text()),
    "performance": {
        "scope": "offline pure DTO/decision CPU microbench; no SQL/HTTP or formal acceptance",
        "ratios": [
            case["v2_over_old"]
            for case in json.loads((HERE / "microbench.json").read_text())["cases"]
        ],
    },
    "not_proven": [
        "full product CI on combined source",
        "MySQL lock behavior after integration",
        "frontend regression",
        "independent acceptance",
        "formal 400 clients/600 seconds/270ms/zero-error performance",
        "global source <=5100",
    ],
}
(HERE / "validation.json").write_text(json.dumps(receipt, indent=2) + "\n")
print(
    json.dumps(
        {
            "cloc": receipt["fixed_cloc"],
            "tests": tests,
            "legacy_migration": receipt["legacy_migration"],
        }
    )
)
