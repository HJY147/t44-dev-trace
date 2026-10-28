"""Read one explicitly hashed resource-stream JSONL; emit no acceptance verdict."""

import argparse
import hashlib
import json
import math
import os
import re
import stat
from datetime import datetime

ROLES = ("mysql", "rabbitmq", "api", "consumer", "scheduler", "web", "tls-gateway")
KINDS = {"resource_header", "resource_sample", "resource_sampling_error", "resource_final"}
MAX_BYTES = 64 * 1024 * 1024
MAX_LINE_BYTES = 256 * 1024


def utc(value):
    if not isinstance(value, str):
        raise ValueError("UTC_STRING_REQUIRED")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.utcoffset() is None or parsed.utcoffset().total_seconds() != 0:
        raise ValueError("UTC_ZERO_OFFSET_REQUIRED")
    return parsed


def read_exact(path, expected):
    if not os.path.isabs(path) or not re.fullmatch(r"[a-f0-9]{64}", expected):
        raise ValueError("ABSOLUTE_PATH_AND_LOWERCASE_SHA256_REQUIRED")
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, "rb") as source:
        before = os.fstat(source.fileno())
        if not stat.S_ISREG(before.st_mode) or not 0 < before.st_size <= MAX_BYTES:
            raise ValueError("BOUNDED_NONEMPTY_REGULAR_FILE_REQUIRED")
        raw = source.read(MAX_BYTES + 1)
        after = os.fstat(source.fileno())
    keys = ("st_dev", "st_ino", "st_size", "st_mtime_ns", "st_ctime_ns")
    if len(raw) != before.st_size or any(getattr(before, k) != getattr(after, k) for k in keys):
        raise ValueError("RAW_CHANGED_DURING_READ")
    if hashlib.sha256(raw).hexdigest() != expected:
        raise ValueError("SHA256_MISMATCH")
    if not raw.endswith(b"\n"):
        raise ValueError("COMPLETE_JSONL_TAIL_REQUIRED")
    return raw


def number(value):
    return type(value) in (int, float) and math.isfinite(value) and value >= 0


def percentile(values, p):
    return sorted(values)[math.ceil(len(values) * p) - 1] if values else None


def metric(rows, key, cpu=False):
    values = [r[key] for _, r in rows if number(r.get(key))]
    result = {
        "valid": len(values),
        "null_or_absent": sum(r.get(key) is None for _, r in rows),
        "invalid": sum(r.get(key) is not None and not number(r[key]) for _, r in rows),
        "max": max(values) if values else None,
    }
    if cpu:
        result.update(p50=percentile(values, 0.50), p95=percentile(values, 0.95))
    return result


def gaps(rows):
    values = []
    nonincreasing = 0
    known = 0
    for (_, a), (_, b) in zip(rows, rows[1:], strict=False):
        if type(a.get("monotonic_ns")) is not int or type(b.get("monotonic_ns")) is not int:
            continue
        known += 1
        delta = b["monotonic_ns"] - a["monotonic_ns"]
        if delta > 0:
            values.append(delta / 1e9)
        else:
            nonincreasing += 1
    return {
        "max_seconds": max(values) if values else None,
        "known_pair_count": known,
        "nonincreasing_pairs": nonincreasing if known else None,
    }


def role_summary(rows, begin, end):
    selected = [(t, r) for t, r in rows if begin <= t <= end]
    before = [(t, r) for t, r in rows if t <= begin]
    after = [(t, r) for t, r in rows if t >= end]
    prior = before[-1:] if before else []
    following = after[:1] if after else []
    bracketed = [(t, r) for t, r in rows if (not prior or t >= prior[0][0]) and (not following or t <= following[0][0])]
    # Preserve file order: never conceal clock/sequence reversal by sorting rows.
    sequences = [r.get("sequence") for _, r in selected]
    known_sequence_pairs = [
        (a, b) for a, b in zip(sequences, sequences[1:], strict=False) if type(a) is int and type(b) is int
    ]
    first, last = (selected[0][0], selected[-1][0]) if selected else (None, None)
    return {
        "rows": len(selected),
        "first_utc": first.isoformat() if first else None,
        "last_utc": last.isoformat() if last else None,
        "head_delay_seconds": (first - begin).total_seconds() if first else None,
        "tail_gap_seconds": (end - last).total_seconds() if last else None,
        "before_or_at_begin_utc": prior[0][0].isoformat() if prior else None,
        "after_or_at_end_utc": following[0][0].isoformat() if following else None,
        "start_gap": gaps(selected),
        "bracketed_start_gap": gaps(bracketed),
        "utc_nonincreasing_pairs": sum(b <= a for (a, _), (b, _) in zip(selected, selected[1:], strict=False))
        if len(selected) > 1
        else None,
        "sequence_numeric_samples": sum(type(s) is int for s in sequences),
        "sequence_known_pair_count": len(known_sequence_pairs),
        "unobserved_sequences_between_samples": sum(max(0, b - a - 1) for a, b in known_sequence_pairs)
        if known_sequence_pairs
        else None,
        "sequence_nonincreasing_pairs": sum(b <= a for a, b in known_sequence_pairs) if known_sequence_pairs else None,
        "resource_identity_count": len(
            {r.get("resource_id") for _, r in selected if isinstance(r.get("resource_id"), str)}
        ),
        "missing_reason_rows": sum(bool(r.get("missing_reason")) for _, r in selected),
        "missing_role_rows": sum(r.get("missing_reason") == "ValueError:missing_role" for _, r in selected),
        "first_cpu_delta_rows": sum(r.get("cpu_delta_reason") == "first_sample_no_delta" for _, r in selected),
        "reset_cpu_delta_rows": sum(r.get("cpu_delta_reason") == "cpu_counter_or_clock_reset" for _, r in selected),
        "unreadable_process_count_max": max(
            (r["unreadable_process_count"] for _, r in selected if number(r.get("unreadable_process_count"))),
            default=None,
        ),
        "cpu_percent": metric(selected, "cpu_percent", cpu=True),
        "rss_bytes": metric(selected, "rss_bytes"),
        "cgroup_memory_bytes": metric(selected, "cgroup_memory_bytes"),
    }


def summarize(raw, digest, begin, end):
    if begin >= end:
        raise ValueError("POSITIVE_WINDOW_REQUIRED")
    rows = {role: [] for role in ROLES}
    counts = dict.fromkeys(sorted(KINDS), 0)
    window_errors = 0
    first_kind = last_kind = None
    header = None
    final = None
    for line in raw.splitlines():
        if not line or len(line) > MAX_LINE_BYTES:
            raise ValueError("NONEMPTY_BOUNDED_JSONL_RECORD_REQUIRED")
        row = json.loads(line)
        if not isinstance(row, dict) or row.get("kind") not in KINDS:
            raise ValueError("RESOURCE_STREAM_RECORD_REQUIRED")
        kind = row["kind"]
        timestamp = utc(row.get("utc"))
        first_kind = first_kind or kind
        last_kind = kind
        counts[kind] += 1
        if kind == "resource_sample":
            role = row.get("role")
            if role not in rows:
                raise ValueError("EXPECTED_SEVEN_ROLE_REQUIRED")
            rows[role].append((timestamp, row))
        elif kind == "resource_sampling_error":
            window_errors += begin <= timestamp <= end
        elif kind == "resource_header":
            header = row
        else:
            final = row
    return {
        "kind": "read-only-resource-window-summary-not-acceptance",
        "raw_sha256": digest,
        "raw_bytes": len(raw),
        "begin_utc": begin.isoformat(),
        "end_utc": end.isoformat(),
        "window_seconds": (end - begin).total_seconds(),
        "selection": "inclusive resource_sample.utc in [begin,end]; CPU is preceding cgroup interval, may overlap window boundary",
        "cpu_semantics": "cgroup CPU-use delta / monotonic elapsed; one core=100%, may exceed100; nearest-rank unweighted p50/p95 of observed rows",
        "memory_semantics": "RSS=sum of process RSS, shared pages may repeat; cgroup memory.current includes cache/kernel; maxima are separate observed samples",
        "record_counts": counts,
        "sampling_error_rows_in_window": window_errors,
        "stream_header_first": first_kind == "resource_header" and counts["resource_header"] == 1,
        "stream_final_last": last_kind == "resource_final" and counts["resource_final"] == 1,
        "header_interval_seconds": header.get("interval_seconds") if header else None,
        "stream_final_utc": final.get("utc") if final else None,
        "roles": {role: role_summary(rows[role], begin, end) for role in ROLES},
        "performance_verdict": None,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", required=True, help="explicit absolute JSONL path, read-only")
    parser.add_argument("--sha256", required=True, help="expected sealed raw SHA256")
    parser.add_argument("--begin", required=True, help="actual cohort utc_started, UTC")
    parser.add_argument("--end", required=True, help="actual cohort utc_finished, UTC")
    args = parser.parse_args()
    try:
        begin, end = utc(args.begin), utc(args.end)
        if begin >= end:
            raise ValueError("POSITIVE_WINDOW_REQUIRED")
        result = summarize(read_exact(args.raw, args.sha256), args.sha256, begin, end)
        output = json.dumps(result, separators=(",", ":"), allow_nan=False)
        if len(output) > 32768:
            raise ValueError("OUTPUT_BOUND_EXCEEDED")
    except (OSError, ValueError, TypeError, OverflowError, KeyError):
        # No raw text, path, credential, or unbounded exception representation.
        print('{"error":"RESOURCE_WINDOW_INPUT_REJECTED","performance_verdict":null}')
        return 2
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
