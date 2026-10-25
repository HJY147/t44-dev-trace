"""Application gates reject absent, empty and skipped test runs."""

import argparse
import json
import subprocess
import sys
import xml.etree.ElementTree as ET

from preflight import REPORTS, ROOT, require_application

OPTIMIZATION_TESTS = [
    "tmp/811_backend_size/811_differential.py",
    "tmp/811_backend_size/812_v2_boundary.py",
    "tmp/812_database_size/test_migration_order.py",
    "tmp/812_database_size/test_schema_defaults.py",
    "tmp/812_database_size/test_seed_v2.py",
]


def junit_has_real_success(path) -> bool:
    if not path.is_file():
        return False
    root = ET.parse(path).getroot()
    cases = list(root.iter("testcase"))
    skipped = sum(case.find("skipped") is not None for case in cases)
    failed = sum(case.find("failure") is not None or case.find("error") is not None for case in cases)
    return bool(cases) and skipped == 0 and failed == 0


def run(command: list[str], log) -> int:
    completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
    log.write_text(completed.stdout + completed.stderr)
    print(completed.stdout + completed.stderr, end="")
    return completed.returncode


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("gate", choices=["contracts", "coverage"])
    args = parser.parse_args()
    folder = REPORTS / args.gate
    folder.mkdir(parents=True, exist_ok=True)
    if require_application():
        return 1
    statuses = []
    if args.gate == "contracts":
        for marker in ["contract", "integration", "fault"]:
            report = folder / f"{marker}.xml"
            code = run([sys.executable, "-m", "pytest", "-c", "backend/pyproject.toml", "tmp/backend",
                        "--strict-markers", "-m", marker, f"--junitxml={report}", "-ra"], folder / f"{marker}.log")
            statuses.append({"marker": marker, "exit_code": code, "real_success": junit_has_real_success(report)})
    else:
        report = folder / "junit.xml"
        prefix = [sys.executable, "-m", "coverage"]
        code = run([*prefix, "run", "--rcfile=scripts/ci/coverage.ini", "-m", "pytest", "-c", "backend/pyproject.toml",
                    "tmp/backend", *OPTIMIZATION_TESTS, "--strict-markers",
                    f"--junitxml={report}", "-ra"], folder / "pytest.log")
        statuses.append({"suite": "all", "exit_code": code, "real_success": junit_has_real_success(report)})
        for output in ["xml", "json", "html", "report"]:
            code = run([*prefix, output, "--rcfile=scripts/ci/coverage.ini"], folder / f"{output}.log")
            statuses.append({"output": output, "exit_code": code, "real_success": code == 0})
        coverage_json = folder / "coverage.json"
        if coverage_json.exists():
            data = json.loads(coverage_json.read_text())
            measured = {(ROOT / name).resolve() for name in data["files"]}
            required = {path.resolve() for path in (ROOT / "backend/t44").rglob("*.py")}
            unmeasured = sorted(str(path.relative_to(ROOT)) for path in required - measured)
            statuses.append({"unmeasured_production_files": unmeasured, "exit_code": int(bool(unmeasured)),
                             "real_success": not unmeasured})
            total = data["totals"]["num_statements"]
            covered = data["totals"]["covered_lines"]
            line_passed = total > 0 and covered * 100 >= total * 80
            statuses.append({"metric": "line_coverage", "covered_lines": covered, "total_lines": total,
                             "threshold_percent": 80, "branch_coverage": "reported without an extra threshold",
                             "exit_code": int(not line_passed), "real_success": line_passed})
        else:
            statuses.append({"missing_coverage_json": True, "exit_code": 1, "real_success": False})
    (folder / "gate.json").write_text(json.dumps(statuses, indent=2) + "\n")
    return int(any(item["exit_code"] or not item["real_success"] for item in statuses))


if __name__ == "__main__":
    raise SystemExit(main())
