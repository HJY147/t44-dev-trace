"""Project a hash-pinned public observer summary; never combine its quantiles."""

import argparse
import hashlib
import json
import os
from pathlib import Path

SOURCE = "935ab5b93bea788672c2b4a088c79cfeed848954"
SHA256 = "d554caf63e38238ab1b3e75abc2823b670b078d60c84a9097b031c03044e3053"
COHORTS = {"baseline1": 20, "clients20": 100, "clients40": 200, "clients400": 2000}
OPERATIONS = {
    "getTask": (200, 2),
    "validateContractPayload": (200, 1),
    "transitionTask": (200, 2),
    "createEscalation": (202, 2),
}


def analyze(raw, projection):
    assert len(raw) == 66110 and hashlib.sha256(raw).hexdigest() == SHA256
    summary = json.loads(raw)
    assert summary["kind"] == "source935-developer-observer-summary-not-acceptance"
    assert summary["all_seven_final_valid"] and len(summary["files"]) == 7
    assert len(summary["finals"]) == 7
    assert sum(item["selected"] for item in summary["finals"]) == summary["total_requests"]
    for item in summary["finals"]:
        assert item["diagnostic_valid"] and item["selected"] == item["written"]
        assert item["cap_skips"] == 0 and item["observer_errors"] == {}
    for item in summary["files"]:
        assert item["final_count"] == 1 and len(item["source_binding"]) == 1
        assert item["source_binding"][0]["product"] == SOURCE
    assert projection["source_sha"] == SOURCE and projection["summary_sha256"] == SHA256
    result = {}
    for name, per_operation in COHORTS.items():
        cohort = summary["cohorts"][name]
        assert cohort["window_count_match"]
        assert cohort["rows"] == cohort["client_completed"] == per_operation * 4
        result[name] = {}
        for operation, (status, calls) in OPERATIONS.items():
            item = cohort["operations"][operation]
            assert item["rows"] == per_operation and item["request_id_mismatches"] == 0
            assert item["statuses"] == {str(status): per_operation}
            phases = item["phases_inclusive_ms"]
            queue = phases["pool_queue_get_inclusive"]
            assert all(queue["calls"][key] == calls for key in ("mean", "p50", "p95", "max"))
            supplied = projection["cohorts"][name]["operations"][operation]
            assert supplied["n"] == per_operation and supplied["statuses"] == item["statuses"]
            assert supplied["peak_checkedout"] == item["peak_checkedout"]
            for phase, value in supplied["phase_wall_p95_ms"].items():
                assert value == phases[phase]["wall"]["p95"]
            for boundary, value in supplied["boundary_p95_ms"].items():
                assert value == item["boundaries_ms"][boundary]["p95"]
            result[name][operation] = {
                "n": per_operation,
                "boundaries_ms": item["boundaries_ms"],
                "pool_queue_get_per_request_calls": calls,
                "pool_queue_get_ms": queue,
                "handler_thread_cpu_ms": phases["sync_handler_inclusive"]["thread_cpu"],
                "cursor_execute_ms": phases["cursor_execute_inclusive"],
                "schema_validation_ms": phases["api_schema_validation"],
                "peak_checkedout": item["peak_checkedout"],
            }
    selected = sum(summary["cohorts"][name]["rows"] for name in COHORTS)
    return {
        "operator": "backend AI",
        "source_sha": SOURCE,
        "summary_sha256": SHA256,
        "public_projection_matches": True,
        "all_seven_final_valid": True,
        "total_requests": summary["total_requests"],
        "selected_cohort_requests": selected,
        "outside_selected_cohorts": summary["total_requests"] - selected,
        "cohorts": result,
        "formal_acceptance": False,
        "new_product_test_or_load_run": False,
        "limits": [summary["scope"], "No per-worker cohort saturation or external request-ID join."],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--projection", type=Path, required=True)
    args = parser.parse_args()
    result = analyze(args.summary.read_bytes(), json.loads(args.projection.read_text()))
    output = Path(__file__).with_name("observer-analysis.json")
    fd = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o644)
    with os.fdopen(fd, "w") as receipt:
        json.dump(result, receipt, ensure_ascii=False, indent=2)
        receipt.write("\n")
        receipt.flush()
        os.fsync(receipt.fileno())
    print(json.dumps({key: value for key, value in result.items() if key != "cohorts"}))


if __name__ == "__main__":
    main()
