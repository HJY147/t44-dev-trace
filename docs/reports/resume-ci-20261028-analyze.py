"""Analyze verified original CI ZIPs only; never execute application or tests."""

import hashlib
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[2]
OLD = "a12e9e70b963bacafda3242bb6d82e53ee912ff1"
NEW = "8c98eb13dadef13f42e8c9973e6285e5781efb4a"


def junit(raw):
    root = ET.fromstring(raw)
    cases = root.findall(".//testcase")
    identities = [(row.get("classname"), row.get("name")) for row in cases]
    assert len(set(identities)) == len(identities)
    return {
        "tests": len(cases),
        "failures": len(root.findall(".//failure")),
        "errors": len(root.findall(".//error")),
        "skipped": len(root.findall(".//skipped")),
    }, set(identities)


def original(run, sha):
    directory = ROOT / "records/ci" / str(run)
    meta = json.loads((directory / "run-rest.json").read_bytes())
    assert meta["head_sha"] == sha and meta["status"] == "completed"
    binding = json.loads((directory / "archive-binding.json").read_bytes())
    for row in binding["artifacts"]:
        raw = (directory / (row["name"] + ".zip")).read_bytes()
        assert len(raw) == row["bytes"]
        assert hashlib.sha256(raw).hexdigest() == row["sha256"]
    raw_logs = (directory / "official-run-logs.zip").read_bytes()
    assert len(raw_logs) == binding["run_logs"]["bytes"]
    assert hashlib.sha256(raw_logs).hexdigest() == binding["run_logs"]["sha256"]
    checkout = []
    with ZipFile(directory / "official-run-logs.zip") as logs:
        for name in logs.namelist():
            if "checkout" not in name.lower():
                continue
            lines = logs.read(name).decode("utf-8-sig").splitlines()
            for i, line in enumerate(lines):
                if "git log -1 --format=%H" in line:
                    assert re.search(r"\b" + sha + r"$", lines[i + 1])
                    checkout.append({"log": name, "actual_checkout": sha})
    assert checkout
    return directory, {
        "run": run,
        "source_sha": sha,
        "conclusion": meta["conclusion"],
        "run_attempt": meta["run_attempt"],
        "actual_checkout_logs": checkout,
        "artifacts_verified": len(binding["artifacts"]),
        "run_log_zip_official_digest_available": False,
    }


def product(run, sha):
    directory, result = original(run, sha)
    with ZipFile(directory / f"coverage-{sha}.zip") as z:
        result["backend"], full_ids = junit(z.read("coverage/junit.xml"))
        total = json.loads(z.read("coverage/coverage.json"))["totals"]
        result["backend"].update(
            covered_lines=total["covered_lines"],
            total_lines=total["num_statements"],
            line_percent=100 * total["covered_lines"] / total["num_statements"],
            covered_branches=total["covered_branches"],
            total_branches=total["num_branches"],
            branch_percent=100 * total["covered_branches"] / total["num_branches"],
            blended_coveragepy_percent=total["percent_covered"],
            excluded_lines=total["excluded_lines"],
        )
        result["backend_gate"] = json.loads(z.read("coverage/gate.json"))
        assert all(row["real_success"] for row in result["backend_gate"])
    subsets, union = {}, set()
    with ZipFile(directory / f"contracts-{sha}.zip") as z:
        for name in ("contract", "integration", "fault"):
            subsets[name], ids = junit(z.read("contracts/" + name + ".xml"))
            assert ids <= full_ids
            union |= ids
    result["marker_subsets"] = subsets
    result["marker_union_unique_tests"] = len(union)
    result["marker_subsets_inside_backend_full_suite"] = True
    with ZipFile(directory / f"frontend-{sha}.zip") as z:
        tests = json.loads(z.read("frontend/coverage/test-results.json"))
        total = json.loads(z.read("frontend/coverage/coverage-summary.json"))["total"]
        assertions = [row for file in tests["testResults"] for row in file["assertionResults"]]
        assert len(assertions) == tests["numTotalTests"]
        assert len({row["fullName"] for row in assertions}) == len(assertions)
        assert sum(row["status"] == "passed" for row in assertions) == tests["numPassedTests"]
        result["frontend"] = {
            "tests": tests["numTotalTests"],
            "passed": tests["numPassedTests"],
            "failed": tests["numFailedTests"],
            "pending": tests["numPendingTests"],
            "success": tests["success"],
            "coverage": total,
        }
    with ZipFile(directory / f"static-{sha}.zip") as z:
        result["static_commands"] = json.loads(z.read("static.json"))
        result["static_E731"] = "E731" in z.read("static-2.log").decode()
        result["static_unit_log_passed_count"] = int(
            re.search(r"(\d+) passed in", z.read("static-1.log").decode())[1]
        )
        bandit = json.loads(z.read("bandit.json"))
        result["bandit_errors"] = len(bandit["errors"])
        result["bandit_findings"] = len(bandit["results"])
    return result


def docker():
    directory, result = original(40636980359, OLD)
    with ZipFile(directory / f"docker-application-{OLD}.zip") as z:
        data = json.loads(z.read("result.json"))
        assert data["source_sha"] == OLD and data["passed"]
        assert data["restoration"]["source"] == data["restoration"]["recovered"]
        assert data["restoration"]["matched"] and data["restored_schema"]["passed"]
        assert data["api_processes"]["workers"] == 4
        assert all(
            step["exit_code"] == (1 if step["name"] == "shared-flock-rejects-second-scanner" else 0)
            for step in data["steps"]
        )
        result.update(
            scope=data["scope"],
            passed=data["passed"],
            api_processes=data["api_processes"],
            seed=data["seed"],
            backup_tables=data["backup_manifest"]["table_count"],
            source_recovered_counts_checksums_equal=True,
            restored_schema=data["restored_schema"],
            expected_flock_rejection_exit_code=1,
            HTTP_checks=data["http"],
        )
    return result


def main():
    report = {
        "operator": "documentation CI evidence AI",
        "scope": "original development Actions evidence; not independent acceptance or cloud load",
        "old_product": product(40636976337, OLD),
        "old_docker": docker(),
        "application_equality": json.loads(
            (ROOT / "docs/reports/resume-ci-20261028-app-equality.json").read_bytes()
        ),
        "corrected_product": {"run": 40637880409, "source_sha": NEW, "status": "NOT_YET_ARCHIVED"},
    }
    if (ROOT / "records/ci/40637880409/archive-binding.json").is_file():
        report["corrected_product"] = product(40637880409, NEW)
    path = ROOT / "docs/reports/resume-ci-20261028-analysis.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"report": str(path.relative_to(ROOT)), "old_product": report["old_product"]["conclusion"], "backend": report["old_product"]["backend"], "marker_union": report["old_product"]["marker_union_unique_tests"], "new_status": report["corrected_product"].get("conclusion", report["corrected_product"].get("status"))}))


if __name__ == "__main__":
    main()
