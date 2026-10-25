"""Offline summary of the explicitly published sequential MySQL diagnostic only."""

import argparse
import hashlib
import json
import os
import statistics
from collections import Counter
from pathlib import Path


def summarize(raw):
    data = json.loads(raw)
    assert data["source"] == "81c909ad753aee7179ee0c464349a07273092fc0"
    assert data["mode"] == "mysql" and not data["cleanup_errors"]
    assert data["status"] == "completed sequential diagnostic only"
    assert Counter(r["phase"] for r in data["requests"]) == {
        "measured": 48,
        "warmup": 4,
        "profile": 4,
    }
    assert all(r["status"] == 200 for r in data["requests"])
    db = {row["request_id"]: row for row in data["database_observer"]["records"]}
    assert len(db) == 56 and set(db) == {r["request_id"] for r in data["requests"]}

    def median_ms(values):
        return statistics.median(values) / 1_000_000

    operations = {}
    for operation in ("getTask", "listTasks", "transitionTask", "validateContractPayload"):
        rows = [
            r for r in data["requests"] if r["phase"] == "measured" and r["operation"] == operation
        ]
        assert len(rows) == 12
        stages = sorted({span["stage"] for r in rows for span in r["spans"]})
        phases = sorted({phase for r in rows for phase in db[r["request_id"]]["phases"]})
        operations[operation] = {
            "ordinary_samples": len(rows),
            "client_wall_median_ms": median_ms(r["client_wall_ns"] for r in rows),
            "stage_medians_ms": {
                stage: {
                    field: median_ms(
                        sum(span[field] for span in r["spans"] if span["stage"] == stage)
                        for r in rows
                    )
                    for field in (
                        "wall_ns",
                        "thread_cpu_ns",
                        "exclusive_wall_ns",
                        "exclusive_thread_cpu_ns",
                    )
                }
                for stage in stages
            },
            "response_schema_thread_cpu_median_ms": median_ms(
                sum(
                    span["thread_cpu_ns"]
                    for span in r["spans"]
                    if span["stage"] == "api_schema_validation" and span["parent_id"] == 0
                )
                for r in rows
            ),
            "database_phase_medians": {
                phase: {
                    **{
                        field.removesuffix("_ns") + "_median_ms": median_ms(
                            db[r["request_id"]]["phases"].get(phase, {}).get(field, 0)
                            for r in rows
                        )
                        for field in ("wall_ns", "thread_cpu_ns")
                    },
                    "count_median": statistics.median(
                        db[r["request_id"]]["phases"].get(phase, {}).get("count", 0) for r in rows
                    ),
                }
                for phase in phases
            },
            "first_sample_sql_shape_counts": dict(
                Counter(
                    f"{sql['verb']}:{','.join(sql['tables'])}"
                    for sql in db[rows[0]["request_id"]]["sql"]
                )
            ),
        }
    return {
        "input_sha256": hashlib.sha256(raw).hexdigest(),
        "input_bytes": len(raw),
        "source": data["source"],
        "source_files": data["source_files"],
        "environment": data["environment"],
        "database_observer_module_sha256": data["database_observer_module_sha256"],
        "operations": operations,
        "inclusive_stages_overlap_do_not_sum": True,
        "profile_only_excluded_from_medians": True,
        "runtime_exclusive_contains_database_calls": True,
        "formal_performance_acceptance": False,
        "old_cloud_root_cause_proven": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = summarize(args.input.read_bytes())
    fd = os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as stream:
        stream.write(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"source": result["source"], "input_sha256": result["input_sha256"]}))


if __name__ == "__main__":
    main()
