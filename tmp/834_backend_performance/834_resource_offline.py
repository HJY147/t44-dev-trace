"""Offline supplemental resource description; never repairs independent acceptance."""

import argparse
import hashlib
import json
import math
import os
import statistics
from collections import Counter
from datetime import datetime
from pathlib import Path

RESOURCES = ("api", "generator", "mysql", "consumer", "scheduler", "broker")


def instant(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def describe(rows):
    numeric = [r for r in rows if type(r.get("cpu_percent")) in (int, float)]
    cpu = sorted(r["cpu_percent"] for r in numeric)
    durations = [r["interval_seconds"] for r in numeric]
    assert all(type(d) in (int, float) and d > 0 for d in durations)
    assert all(math.isfinite(value) and value >= 0 for value in cpu)
    memory = [r["memory_bytes"] for r in rows if type(r.get("memory_bytes")) in (int, float)]
    times = sorted(instant(r["utc"]) for r in rows)
    identities = {tuple(r.get("pid_list", ())) for r in rows}
    return {
        "endpoint_rows": len(rows),
        "numeric_cpu_rows": len(numeric),
        "null_cpu_rows": len(rows) - len(numeric),
        "status_counts": dict(Counter(r["status"] for r in rows)),
        "unique_sample_keys": len({(r["utc"], r["monotonic_ns"]) for r in rows}),
        "first_sample_utc": times[0].isoformat() if times else None,
        "last_sample_utc": times[-1].isoformat() if times else None,
        "max_timestamp_gap_seconds": max(
            ((b - a).total_seconds() for a, b in zip(times, times[1:], strict=False)),
            default=None,
        ),
        "numeric_interval_seconds_sum": sum(durations),
        "cpu_percent_interval_weighted_mean": (
            sum(r["cpu_percent"] * r["interval_seconds"] for r in numeric) / sum(durations)
            if durations
            else None
        ),
        "cpu_percent_median": statistics.median(cpu) if cpu else None,
        "cpu_percent_p95_nearest_rank": cpu[math.ceil(0.95 * len(cpu)) - 1] if cpu else None,
        "cpu_percent_min": cpu[0] if cpu else None,
        "cpu_percent_max": cpu[-1] if cpu else None,
        "sampled_group_rss_max_bytes": max(memory) if memory else None,
        "observed_pid_sets": [list(ids) for ids in sorted(identities)],
    }


def analyze(result_path, interface_path):
    public_raw, interface_raw = result_path.read_bytes(), interface_path.read_bytes()
    public, interface = json.loads(public_raw), json.loads(interface_raw)
    assert public["visibility"] == "PUBLIC"
    assert public["source_sha"] == "935ab5b93bea788672c2b4a088c79cfeed848954"
    final_path = Path(interface["final_path"])
    final_raw = final_path.read_bytes()
    final = json.loads(final_raw)
    assert final["action"] == "interval_sampler_final" and final["collection_completed"]
    assert final["output_path"] == interface["raw_path"]
    raw_path = Path(final["output_path"])
    raw = raw_path.read_bytes()
    assert len(raw) == final["output_bytes"]
    assert hashlib.sha256(raw).hexdigest() == final["output_sha256"]
    rows = [json.loads(line) for line in raw.splitlines()]
    assert len(rows) == final["rows_written"]
    assert {r["resource_id"] for r in rows} == set(RESOURCES)
    begin = instant(public["steady_window_begin_utc"])
    end = instant(public["steady_window_end_utc"])
    start_reset = instant(public["transport_error_first_start_utc"])
    end_reset = instant(public["transport_error_last_end_utc"])
    steady = [r for r in rows if begin <= instant(r["utc"]) <= end]
    selected = {res: [r for r in steady if r["resource_id"] == res] for res in RESOURCES}
    around = [
        {
            key: r.get(key)
            for key in ("utc", "resource_id", "cpu_percent", "memory_bytes", "status", "pid_list")
        }
        for r in steady
        if start_reset.timestamp() - 2 <= instant(r["utc"]).timestamp() <= end_reset.timestamp() + 2
    ]
    return {
        "source": public["source_sha"],
        "inputs": {
            "public_result": {
                "path": str(result_path),
                "sha256": hashlib.sha256(public_raw).hexdigest(),
            },
            "interval_interface": {
                "path": str(interface_path),
                "sha256": hashlib.sha256(interface_raw).hexdigest(),
            },
            "root_interval_final": {
                "path": str(final_path),
                "sha256": hashlib.sha256(final_raw).hexdigest(),
            },
            "root_raw": {
                "path": str(raw_path),
                "bytes": len(raw),
                "sha256": final["output_sha256"],
                "rows": len(rows),
            },
        },
        "original_independent_mirror": {
            "sha256": public["resource_raw_mirror_sha256"],
            "bytes": public["resource_raw_mirror_bytes_preserved"],
            "coverage_status_unchanged": public["resource_coverage_status"],
            "not_read_or_repaired": True,
        },
        "window": {
            "begin_utc": begin.isoformat(),
            "end_utc": end.isoformat(),
            "seconds": (end - begin).total_seconds(),
        },
        "method": {
            "selection": "Sample endpoint UTC lies inside PUBLIC steady window; boundary intervals are not reconstructed",
            "mean": "sum(cpu_percent * original interval_seconds) / sum(original interval_seconds)",
            "p95": "descriptive nearest-rank of resource CPU samples, not request latency",
            "cpu_100_means_one_core": True,
            "null_not_zero": True,
            "no_interpolation_or_zero_fill": True,
            "rss_sum_is_not_unique_memory": True,
            "mysql_whole_shared_process_not_schema_attribution": True,
        },
        "resources": {res: describe(selected[res]) for res in RESOURCES},
        "reset_window_neutral_samples": around,
        "acceptance_result_overridden": False,
        "formal_performance_groups_unchanged": public["complete_formal_performance_groups"],
        "root_cause_proven": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--public-result", type=Path, required=True)
    parser.add_argument("--interval-interface", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = analyze(args.public_result, args.interval_interface)
    fd = os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as stream:
        stream.write(json.dumps(report, indent=2) + "\n")
    print(
        json.dumps(
            {
                "root_raw_sha256": report["inputs"]["root_raw"]["sha256"],
                "sample_rows": {k: v["endpoint_rows"] for k, v in report["resources"].items()},
            }
        )
    )


if __name__ == "__main__":
    main()
