"""Opt-in bounded pure-CPU ABBA diagnostic; no cloud or external service is used."""

import argparse
import gc
import hashlib
import importlib.util
import json
import signal
import statistics
import time
from importlib.metadata import version
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    spec = importlib.util.spec_from_file_location(
        "checks774", ROOT / "tmp/774_backend_scale_20261029/774_contract_reuse.py"
    )
    checks = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(checks)
    from t44 import contracts

    fixture = checks.application.__wrapped__()
    client, _ = next(fixture)
    try:
        tokens, pid, iid = checks.helpers.setup_project(client)
        task = checks.helpers.create_task(client, tokens, pid, iid)
        response = checks.helpers.request(
            client,
            "getTask",
            token=tokens["manager"],
            project_id=pid,
            task_id=task["id"],
            expect=200,
        ).json()
    finally:
        fixture.close()
    selected = {"id-boolean", "plan-valid", "task-valid", "contract-valid", "all105-errors"}
    cases = [case for case in checks.samples if case["name"] in selected]
    operation = contracts.OPERATIONS["getTask"]
    cases += [
        {
            "name": "real-getTask-data",
            "schema": operation["data_schema"],
            "value": response["data"],
        },
        {
            "name": "real-getTask-envelope",
            "schema": operation["responses"]["200"]["content"]["application/json"]["schema"],
            "value": response,
        },
    ]
    before = json.dumps(cases)
    report = {
        "scope": "local sequential CPU only; SQLite HTTP fixture preparation excluded",
        "base": checks.BASE,
        "candidate_contracts_sha256": hashlib.sha256(
            (ROOT / "backend/t44/contracts/__init__.py").read_bytes()
        ).hexdigest(),
        "versions": {name: version(name) for name in ("jsonschema", "referencing", "attrs")},
        "iterations_per_case_per_phase": 100,
        "phase_order": "ABBA" * 4,
        "gc_enabled": gc.isenabled(),
        "phases": [],
    }
    functions = {"A": checks.original.violations, "B": contracts.violations}
    for case in cases:
        checks.same(case["schema"], case["value"])
        for function in functions.values():
            for _ in range(10):
                function(case["schema"], case["value"])
    signal.alarm(40)
    try:
        for number, mode in enumerate(report["phase_order"]):
            for case in cases:
                started_cpu, started_wall = time.process_time(), time.perf_counter()
                error_count = 0
                for _ in range(report["iterations_per_case_per_phase"]):
                    error_count += len(functions[mode](case["schema"], case["value"]))
                report["phases"].append(
                    {
                        "phase": number,
                        "mode": mode,
                        "case": case["name"],
                        "cpu_seconds": time.process_time() - started_cpu,
                        "wall_seconds": time.perf_counter() - started_wall,
                        "error_count": error_count,
                    }
                )
    finally:
        signal.alarm(0)
    assert json.dumps(cases) == before
    summary = {}
    for case in cases:
        times = {
            mode: [
                p["cpu_seconds"]
                for p in report["phases"]
                if p["mode"] == mode and p["case"] == case["name"]
            ]
            for mode in functions
        }
        means = {mode: statistics.median(values) * 10000 for mode, values in times.items()}
        summary[case["name"]] = {
            "median_cpu_us_per_call": means,
            "relative_reduction": 1 - means["B"] / means["A"],
            "range_cpu_seconds_per_batch": {
                mode: [min(values), max(values)] for mode, values in times.items()
            },
        }
    report["summary"] = summary
    report["cache"] = contracts._compiled.cache_info()._asdict()
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
