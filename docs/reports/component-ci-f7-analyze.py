"""Read exact public CI originals only; no product import or execution."""
from pathlib import Path, PurePosixPath
import ast
import hashlib
import json
import re
import stat
import xml.etree.ElementTree as ET
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[2]
SOURCE = "f7cdb5fa3b19f84d8ab0d0b042bf51a5b8484e8f"
RUNS = {40692462131: [12818501276, 12817977470, 12817598161, 12817119149],
        40692462380: [12817747564]}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def safe_zip(path):
    with ZipFile(path) as archive:
        assert archive.testzip() is None
        names = archive.namelist()
        assert len(names) == len(set(names))
        for item in archive.infolist():
            name = PurePosixPath(item.filename)
            assert not name.is_absolute() and ".." not in name.parts
            assert "\\" not in item.filename
            assert not stat.S_ISLNK(item.external_attr >> 16)
        return names


def junit(raw):
    root = ET.fromstring(raw)
    tests = list(root.iter("testcase"))
    keys = {(item.get("classname"), item.get("name")) for item in tests}
    assert len(tests) == len(keys) and tests
    counts = {kind: len(list(root.iter(tag))) for kind, tag in
              (("failures", "failure"), ("errors", "error"), ("skipped", "skipped"))}
    assert not any(counts.values())
    return keys, {"passed_unique": len(keys), **counts}


def main():
    output = {"source_sha": SOURCE, "actor": "AI documentation / documentation_ci_f7_20261028",
              "scope": "development CI and hosted Linux Compose; not independent acceptance or cloud performance",
              "runs": {}}
    for run_id, artifact_ids in RUNS.items():
        directory = ROOT / "records/ci" / str(run_id)
        run = json.loads((directory / "official-run.json").read_bytes())
        assert run["id"] == run_id and run["head_sha"] == SOURCE
        assert run["status"] == "completed" and run["conclusion"] == "success"
        assert run["run_attempt"] == 1
        jobs = json.loads((directory / "official-jobs.json").read_bytes())["jobs"]
        executed = [job for job in jobs if job["conclusion"] != "skipped"]
        assert len(executed) == (4 if run_id == 40692462131 else 1)
        assert all(job["status"] == "completed" and job["conclusion"] == "success" for job in executed)
        records = []
        official_artifacts = json.loads((directory / "official-artifacts.json").read_bytes())["artifacts"]
        assert {item["id"] for item in official_artifacts} == set(artifact_ids)
        rest_artifacts = json.loads((directory / "official-rest-artifacts.json").read_bytes())
        rest_jobs = json.loads((directory / "official-rest-jobs.json").read_bytes())
        assert rest_artifacts["total_count"] == len(official_artifacts) == len(rest_artifacts["artifacts"])
        assert {item["id"] for item in rest_artifacts["artifacts"]} == set(artifact_ids)
        assert rest_jobs["total_count"] == len(jobs) == len(rest_jobs["jobs"])
        assert {item["id"] for item in rest_jobs["jobs"]} == {item["id"] for item in jobs}
        for artifact_id in artifact_ids:
            binding = json.loads((directory / f"{artifact_id}.binding.json").read_bytes())
            path = directory / binding["local_filename"]
            metadata = next(item for item in official_artifacts if item["id"] == artifact_id)
            assert metadata == binding["artifact"]
            assert metadata["workflow_run"]["head_sha"] == SOURCE
            assert path.stat().st_size == metadata["size_in_bytes"] == binding["actual_bytes"]
            assert "sha256:" + digest(path) == metadata["digest"]
            assert digest(path) == binding["actual_sha256"]
            assert safe_zip(path) == binding["members"]
            records.append({"artifact_id": artifact_id, "name": metadata["name"],
                            "bytes": path.stat().st_size, "sha256": digest(path),
                            "official_size_digest_match": True})
        log = directory / "official-run-logs.zip"
        safe_zip(log)
        with ZipFile(log) as archive:
            checkout = {}
            for name in archive.namelist():
                if "Run actions_checkout" not in name or "Post" in name:
                    continue
                lines = archive.read(name).decode().splitlines()
                positions = [index for index, line in enumerate(lines) if "git log -1 --format=%H" in line]
                assert len(positions) == 1
                result_line = lines[positions[0] + 1]
                assert re.fullmatch(r"\S+ " + SOURCE, result_line)
                checkout[name] = {"git_log_result_full_sha": SOURCE, "exact": True}
            assert len(checkout) == len(executed)
        output["runs"][str(run_id)] = {"conclusion": "success", "run_attempt": 1,
            "url": run["html_url"], "actual_jobs": [{"id": job["id"], "name": job["name"],
            "status": job["status"], "conclusion": job["conclusion"]} for job in jobs],
            "artifacts": records, "original_run_log_bytes": log.stat().st_size,
            "original_run_log_sha256": digest(log), "log_digest_source": "local only; no server digest supplied",
            "REST_complete_artifact_count": rest_artifacts["total_count"], "REST_complete_job_count": rest_jobs["total_count"],
            "actual_checkout_full_sha_checks": checkout}
    directory = ROOT / "records/ci/40692462131"
    with ZipFile(directory / "12818501276.zip") as archive:
        full, result = junit(archive.read("coverage/junit.xml"))
        coverage = json.loads(archive.read("coverage/coverage.json"))
        gate = json.loads(archive.read("coverage/gate.json"))
        assert all(item["exit_code"] == 0 and item["real_success"] for item in gate)
        total = coverage["totals"]
        output["backend"] = {**result, "covered_lines": total["covered_lines"],
            "total_lines": total["num_statements"], "line_percent": 100 * total["covered_lines"] / total["num_statements"],
            "covered_branches": total["covered_branches"], "total_branches": total["num_branches"],
            "branch_percent": 100 * total["covered_branches"] / total["num_branches"],
            "mixed_percent_separate": total["percent_covered"], "excluded_lines": total["excluded_lines"],
            "full_gate": gate}
        new_modules = {}
        for path, expected in (("tmp/782_component_call_refactor_20261028/782_backend_component.py", 14),
                               ("tmp/780_messaging_component_20261028/780_facade_semantics.py", 7)):
            names = {item.name for item in ast.parse((ROOT / path).read_text()).body
                     if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and item.name.startswith("test_")}
            actual = sorted(name for _, name in full if name.split("[", 1)[0] in names)
            assert len(actual) == expected
            new_modules[path] = {"actual_passed_cases": len(actual), "actual_JUnit_case_names": actual,
                                 "public_test_function_names_matched_from_AST": sorted(names)}
        output["backend"]["new_modules_in_actual_full_JUnit"] = new_modules
    with ZipFile(directory / "12817598161.zip") as archive:
        keys, groups = [], {}
        for name in ("contract", "integration", "fault"):
            members, counts = junit(archive.read(f"contracts/{name}.xml"))
            keys.append(members)
            groups[name] = counts
        union = set.union(*keys)
        assert union <= full
        output["marked_subsets"] = {"groups": groups, "unique_union": len(union),
                                    "subset_of_full_suite": True, "not_added_to_total": True}
    with ZipFile(directory / "12817977470.zip") as archive:
        result = json.loads(archive.read("frontend/coverage/test-results.json"))
        tests = [test for suite in result["testResults"] for test in suite["assertionResults"]]
        assert result["success"] and all(test["status"] == "passed" for test in tests)
        assert len(tests) == result["numTotalTests"] == result["numPassedTests"]
        identities = [(test["fullName"], suite["name"]) for suite in result["testResults"] for test in suite["assertionResults"]]
        assert len(identities) == len(set(identities))
        output["frontend"] = {"passed_unique_assertions": len(tests), "failed": result["numFailedTests"],
            "pending": result["numPendingTests"], "coverage": json.loads(archive.read("frontend/coverage/coverage-summary.json"))["total"]}
    with ZipFile(directory / "12817119149.zip") as archive:
        bandit = json.loads(archive.read("bandit.json"))
        config = json.loads(archive.read("static.json"))
        assert not bandit["errors"] and not bandit["results"] and not config["missing"]
        assert all(item["exit_code"] == 0 for item in config["commands"])
        output["static"] = {"bandit_errors": 0, "bandit_findings": 0, "commands": config["commands"]}
    with ZipFile(ROOT / "records/ci/40692462380/12817747564.zip") as archive:
        result = json.loads(archive.read("result.json"))
        assert result["source_sha"] == SOURCE and result["passed"]
        restore = result["restoration"]
        assert restore["matched"] and restore["source"] == restore["recovered"]
        assert len(restore["source"]["counts"]) == len(restore["source"]["checksums"]) == 19
        assert result["restored_schema"]["passed"] and not result["restored_schema"]["defects"]
        nonzero = [item for item in result["steps"] if item["exit_code"]]
        assert nonzero == [{"name": "shared-flock-rejects-second-scanner", "exit_code": 1}]
        output["docker"] = {name: result[name] for name in ("scope", "passed", "api_processes", "seed",
            "scheduler_progress", "backup_manifest", "restored_schema", "redacted_secret_occurrences")}
        output["docker"].update(all_19_table_counts_checksums_equal=True, expected_nonzero_steps=nonzero)
    count = json.loads((directory / "source-count.json").read_bytes())
    assert count["commit"] == SOURCE and count["groups"]["application"]["summary"]["code"] == 5898
    assert count["range"] == [3500, 5100] and count["within_range"] is False
    output["source_count"] = {"application_code": 5898, "range": count["range"], "within_range": False,
        "over_upper_bound": 798, "counter_exit_code": 1, "tool": count["tool"], "tool_sha256": count["tool_sha256"]}
    output["not_closed"] = ["strict source-size gate", "independent business/fault acceptance",
        "400 active clients / 600 seconds formal performance", "continuous cloud resource evidence",
        "actual cloud connection budget", "final billing", "student handwritten research"]
    target = directory / "verified-analysis.json"
    target.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"source": SOURCE, "backend": {k: v for k, v in output["backend"].items() if k != "full_gate"},
        "frontend_passed": output["frontend"]["passed_unique_assertions"], "source_count": output["source_count"]}))


if __name__ == "__main__":
    main()
