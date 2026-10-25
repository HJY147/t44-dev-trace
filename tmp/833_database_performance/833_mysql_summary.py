"""Offline join of an explicitly selected public request/DB diagnostic; no DB access."""

import argparse
import hashlib
import json
import os
import statistics
from collections import Counter, defaultdict
from pathlib import Path


def stats(values):
    return {
        "mean": statistics.mean(values),
        "min": min(values),
        "max": max(values),
        "median": statistics.median(values),
    }


def summarize(data):
    requests = data["requests"]
    observer = data["database_observer"]
    records = observer["records"]
    by_id = {r["request_id"]: r for r in records}
    if len(by_id) != len(records) or len({r["request_id"] for r in requests}) != len(requests):
        raise ValueError("Duplicate request identifiers")
    if set(by_id) != {r["request_id"] for r in requests}:
        raise ValueError("Request/DB identifiers differ")
    if observer["pending_cursor_spans"] or data["cleanup_errors"]:
        raise ValueError("Incomplete cursor or cleanup evidence")
    groups = defaultdict(list)
    counts = Counter()
    for request in requests:
        row = by_id[request["request_id"]]
        if request["operation"] != row["operation_id"]:
            raise ValueError("Request/DB operation mismatch")
        if row["sql_samples_dropped"] or any(p["errors"] for p in row["phases"].values()):
            raise ValueError("Incomplete or failed request evidence")
        counts[request["phase"]] += 1
        if request["phase"] == "measured":
            groups[row["operation_id"]].append((request, row))
    operations = {}
    for operation, pairs in groups.items():
        phases = {}
        for phase in sorted({p for _, row in pairs for p in row["phases"]}):
            values = [row["phases"].get(phase, {}) for _, row in pairs]
            phases[phase] = {
                key: stats([value.get(key, 0) for value in values])
                for key in ("count", "wall_ns", "thread_cpu_ns")
            }
        sql = defaultdict(list)
        for _, row in pairs:
            for statement in row["sql"]:
                key = (statement["verb"], tuple(statement["tables"]), statement["shape_sha256"])
                sql[key].append(statement)
        operations[operation] = {
            "requests": len(pairs),
            "client_wall_ns": stats([request["client_wall_ns"] for request, _ in pairs]),
            "observer_wall_ns": stats([row["wall_ns"] for _, row in pairs]),
            "observer_thread_cpu_ns": stats([row["thread_cpu_ns"] for _, row in pairs]),
            "sql_count_histogram": dict(sorted(Counter(len(r["sql"]) for _, r in pairs).items())),
            "mapped_rows": stats([row["mapping_rows"] for _, row in pairs]),
            "phases_inclusive_not_additive": phases,
            "sql_shapes": [
                {
                    "verb": key[0],
                    "tables": key[1],
                    "shape_sha256": key[2],
                    "count": len(values),
                    "wall_ns": stats([v["wall_ns"] for v in values]),
                    "thread_cpu_ns": stats([v["thread_cpu_ns"] for v in values]),
                }
                for key, values in sorted(sql.items())
            ],
        }
    return {
        "schema": "offline_mysql_request_join_v1",
        "source": data["source"],
        "observer_sha256": data["database_observer_module_sha256"],
        "environment": data["environment"],
        "utc_start": data["utc_start"],
        "utc_end": data["utc_end"],
        "requests_joined": len(requests),
        "phase_counts": dict(counts),
        "actual_pool_snapshot_after_dispose": observer["actual_pool"],
        "actual_dbapi_timeout_profiles": observer["actual_dbapi_timeout_profiles"],
        "outside_request_phases": observer["outside_request_phases"],
        "ping_returned_false": observer["ping_returned_false"],
        "operations": operations,
        "limits": [
            "Sequential synthetic Linux MySQL diagnostic only, not old cloud root cause or acceptance",
            "Warmup and cProfile requests excluded from measured summaries",
            "Nested inclusive phases are not additive; execute may include buffered network fetch",
            "Commit includes reset/return; DBAPI rollback is not labelled application rollback",
            "Pool snapshot follows dispose; missing connect timing/timeouts remain unobserved",
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--input-sha256", required=True)
    parser.add_argument("--expected-source", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    raw = args.input.read_bytes()
    if len(raw) > 20_000_000 or hashlib.sha256(raw).hexdigest() != args.input_sha256:
        parser.error("Public input size/hash mismatch")
    data = json.loads(raw)
    if data["source"] != args.expected_source or data["mode"] != "mysql":
        parser.error("Expected source/MySQL mode mismatch")
    report = summarize(data)
    report["input_sha256"] = args.input_sha256
    fd = os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as stream:
        stream.write(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"joined": report["requests_joined"], "phases": report["phase_counts"]}))


if __name__ == "__main__":
    main()
