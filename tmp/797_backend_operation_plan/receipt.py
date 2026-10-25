"""Bind retained probe evidence to exact source bytes without touching product or runtime."""

import gzip
import hashlib
import json
import subprocess
from pathlib import Path
from xml.etree import ElementTree

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
BASE = "f4bd382d4668130793fc553df9ce6363c4656ea6"
ORIGINAL_TESTS = [
    "986_http.py",
    "987_faults.py",
    "856_release_error_priority.py",
    "859_dependency_delivered.py",
    "816_acceptance_followup_20261025.py",
]


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def evidence_bytes(name):
    path = HERE / name
    return (
        path.read_bytes()
        if path.exists()
        else gzip.decompress((HERE / (name + ".gz")).read_bytes())
    )


def main():
    names = (
        git("ls-tree", "-r", "--name-only", BASE, "--", "backend/t44", "frontend")
        .decode()
        .splitlines()
    )
    product = {}
    for name in names:
        raw = git("show", f"{BASE}:{name}")
        actual = (ROOT / name).read_bytes()
        assert raw == actual, name
        product[name] = sha(actual)
    tests = {}
    for name in ORIGINAL_TESTS:
        path = "tmp/backend/contracts/" + name
        raw = git("show", f"{BASE}:{path}")
        assert raw == (ROOT / path).read_bytes()
        tests[path] = sha(raw)
    suites = ElementTree.parse(HERE / "candidate-junit.xml").getroot().findall("testsuite")
    totals = {
        key: sum(int(suite.attrib[key]) for suite in suites)
        for key in ("tests", "failures", "errors", "skipped")
    }
    assert totals == {"tests": 153, "failures": 0, "errors": 0, "skipped": 0}
    differential = json.loads((HERE / "differential.json").read_text())
    count = json.loads((HERE / "count.json").read_text())
    assert count["net_saved"] == -14
    candidate = {
        str(path.relative_to(HERE / "candidate")): sha(path.read_bytes())
        for path in sorted((HERE / "candidate").rglob("*.py"))
    }
    evidence = {
        name: sha(evidence_bytes(name))
        for name in (
            "candidate-initial.log",
            "candidate-junit.xml",
            "differential-initial.log",
            "differential-initial.xml",
            "differential-fixed.log",
            "differential-fixed.xml",
            "differential.json",
            "count.json",
            "baseline-cloc.json",
            "candidate-cloc.json",
            "source-manifest.json",
            "ast-proof.json",
            "format-ast-proof.json",
            "static-initial.log",
            "format-initial.log",
            "format-applied.log",
            "static-final.log",
            "format-final.log",
        )
    }
    report = {
        "base": BASE,
        "actual_operator": "backend AI",
        "prompt": "ROLE-backend-OPERATION-PLAN-v1",
        "decision": "REJECTED: temporary probe grows application by 14; below minimum 20 saving",
        "product_unchanged_bytes": product,
        "original_tests_unchanged_bytes": tests,
        "candidate_source_sha256": candidate,
        "evidence_sha256": evidence,
        "source_counter_sha256": sha((ROOT / "scripts/metrics/source_count.py").read_bytes()),
        "count": count,
        "developer_tests": totals,
        "developer_case_accounting": {"original_http": 143, "new_probe": 10},
        "differential": {
            "scenarios": len(differential["scenario_comparisons"]),
            "gateway_fault_positions": len(differential["gateway_fault_comparisons"]),
            "compared": [
                "result/error",
                "ordered gateway calls+arguments",
                "four actual table states",
                "Call audit diff",
            ],
        },
        "ast_scope": "four callbacks after only authorization/task-load prefix; all other methods identical",
        "not_proved": [
            "all possible inputs",
            "MySQL lock/deadlock behavior",
            "performance benefit",
            "any architecture's minimum LOC",
        ],
        "not_run": ["full CI", "Docker", "MySQL", "cloud", "independent acceptance"],
        "initial_harness_failure": "all comparisons reached receipt writing; static template_hash bytes were not JSON serializable; narrowed receipt to method/table without changing comparisons",
    }
    (HERE / "validation.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    print(
        json.dumps(
            {
                "tests": totals,
                "net_saved": count["net_saved"],
                "product_files_unchanged": len(product),
                "decision": "REJECTED",
            }
        )
    )


if __name__ == "__main__":
    main()
