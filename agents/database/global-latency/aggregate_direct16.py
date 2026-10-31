"""Offline-only, immutable Git PUBLIC inputs; no DB/network/SUT access."""

import hashlib
import json
import subprocess
from pathlib import Path

REF = "3d6f7eab"
OUT = Path(__file__).parent
DIGESTS = {
    "INSERT/idempotency_requests": "78ceeee04e3c5f9d92f1e2375cb142031ccd5252a477e2b768ebad7d110cf45c",
    "COMMIT": "f2b9be5f0f32ca7507e4ddf133cd2fad0993a1c26fde9caa6f067b1af2b7603c",
}
COUNTERS = [
    "Com_commit",
    "Com_rollback",
    "Connections",
    "Innodb_buffer_pool_pages_flushed",
    "Innodb_buffer_pool_reads",
    "Innodb_buffer_pool_wait_free",
    "Innodb_data_fsyncs",
    "Innodb_data_read",
    "Innodb_data_writes",
    "Innodb_data_written",
    "Innodb_log_waits",
    "Innodb_os_log_written",
    "Innodb_redo_log_current_lsn",
    "Innodb_row_lock_waits",
    "Innodb_row_lock_time",
]


def load(path):
    raw = subprocess.check_output(["git", "show", f"{REF}:{path}"])
    return raw, {
        "git_ref": REF,
        "path": path,
        "sha256": hashlib.sha256(raw).hexdigest(),
        "bytes": len(raw),
    }


def delta(values):
    assert all(b >= a for a, b in zip(values, values[1:], strict=False)), "counter reset"
    return values[-1] - values[0]


def cpu_stat(record, role):
    lines = record["services"][role]["cgroup"]["cpu.stat"]
    return {key: int(value) for key, value in (line.split() for line in lines)}


result = {
    "source_scope": "PUBLIC Git bytes only; no new experiment",
    "git_commit": subprocess.check_output(["git", "rev-parse", REF], text=True).strip(),
    "windows": {},
}
for phase in ["early", "late"]:
    raw, provenance = load(
        f"agents/coordinator/direct-p16/actual-run-20261031/{phase}.PUBLIC.jsonl"
    )
    records = [json.loads(line) for line in raw.splitlines()]
    assert len(records) == 12
    seconds = records[-1]["monotonic"] - records[0]["monotonic"]
    assert seconds > 0
    mysql = [r["services"]["mysql"]["mysql"] for r in records]
    status = [m["status"] for m in mysql]
    assert all(b["Uptime"] > a["Uptime"] for a, b in zip(status, status[1:], strict=False))
    config = mysql[0]["effective_global_config"]["values"]
    assert all(m["effective_global_config"]["values"] == config for m in mysql)
    counters = {k: delta([s[k] for s in status]) for k in COUNTERS}
    digest_total = delta([m["aggregates"]["DIGEST_TOTAL"]["sum_timer_wait_ps"] for m in mysql])
    digests = {}
    for name, digest in DIGESTS.items():
        rows = [{r["digest_hash"]: r for r in m["top20_digests_by_count"]["rows"]} for m in mysql]
        assert all(digest in rows_at_sample for rows_at_sample in rows)
        calls = delta([r[digest]["count_star"] for r in rows])
        ps = delta([r[digest]["sum_timer_wait_ps"] for r in rows])
        digests[name] = {
            "digest": digest,
            "calls": calls,
            "calls_per_second": calls / seconds,
            "mean_ms": ps / 1e9 / calls if calls else None,
            "parallel_aggregate_seconds": ps / 1e12,
            "share_of_digest_timer": ps / digest_total if digest_total else None,
        }
    waits = []
    waitrows = [
        {r["event_name"]: r for r in m["global_waits"]["top20_by_cumulative_timer"]} for m in mysql
    ]
    for name in sorted(set.intersection(*(set(r) for r in waitrows))):
        if not all(r[name]["enabled"] and r[name]["timed"] for r in waitrows):
            continue
        calls = delta([r[name]["count_star"] for r in waitrows])
        ps = delta([r[name]["sum_timer_wait_ps"] for r in waitrows])
        waits.append(
            {
                "event": name,
                "calls": calls,
                "parallel_aggregate_seconds": ps / 1e12,
                "mean_ms": ps / 1e9 / calls if calls else None,
            }
        )
    cpus = {}
    for role in ["api", "mysql"]:
        assert all(
            r["services"][role]["container_id"] == records[0]["services"][role]["container_id"]
            for r in records
        ), "container identity changed"
        stats = [cpu_stat(r, role) for r in records]
        cpus[role] = {k: delta([s[k] for s in stats]) for k in stats[0]}
        cpus[role]["average_cores_over_top_level_window"] = cpus[role]["usage_usec"] / 1e6 / seconds
    host_devices = {}
    for dev, first in records[0]["host_block_io"]["devices"].items():
        samples = [r["host_block_io"]["devices"][dev] for r in records]
        assert all(s["device_name"] == first["device_name"] for s in samples)
        d = {
            k: delta([s["counters"][k] for s in samples])
            for k in first["counters"]
            if k != "io_inflight"
        }
        host_dt = (
            records[-1]["host_block_io"]["observed_monotonic"]
            - records[0]["host_block_io"]["observed_monotonic"]
        )
        host_devices[dev] = {
            "device_name": first["device_name"],
            "seconds": host_dt,
            "deltas": d,
            "read_bytes_per_second": d["sectors_read_512b"] * 512 / host_dt,
            "write_bytes_per_second": d["sectors_written_512b"] * 512 / host_dt,
            "completions_per_second": (d["reads_completed"] + d["writes_completed"]) / host_dt,
        }
    ages = [m["checkpoint_age"]["bytes"] for m in mysql]
    result["windows"][phase] = {
        "input": provenance,
        "samples": len(records),
        "seconds": seconds,
        "utc_start": records[0]["utc"],
        "utc_end": records[-1]["utc"],
        "config": config,
        "digests": digests,
        "counter_deltas": counters,
        "counter_rates_per_second": {k: v / seconds for k, v in counters.items()},
        "checkpoint_age_bytes_range": [min(ages), max(ages)],
        "checkpoint_capacity_fraction_range": [
            min(ages) / config["innodb_redo_log_capacity"],
            max(ages) / config["innodb_redo_log_capacity"],
        ],
        "buffer_pool_free_fraction_range": [
            min(
                s["Innodb_buffer_pool_pages_free"] / s["Innodb_buffer_pool_pages_total"]
                for s in status
            ),
            max(
                s["Innodb_buffer_pool_pages_free"] / s["Innodb_buffer_pool_pages_total"]
                for s in status
            ),
        ],
        "threads_connected_range": [
            min(s["Threads_connected"] for s in status),
            max(s["Threads_connected"] for s in status),
        ],
        "wait_deltas": waits,
        "cpu_deltas": cpus,
        "host_block_io": host_devices,
        "resize_status_samples": [m["redo_resize_status"] for m in mysql],
    }
for name in ["SUMMARY.PUBLIC.json", "DIAGNOSTICS.PUBLIC.json"]:
    raw, provenance = load(f"records/qa/directp16-result-20261031.PUBLIC/{name}")
    data = json.loads(raw)
    keys = [
        "status",
        "classes",
        "universe_steady_requests",
        "diag_incomplete_values",
        "app_ms",
        "paired_e2e_minus_app_ms",
        "paired_e2e_ms",
    ]
    selected = {k: data[k] for k in keys if k in data}
    if "spans" in data:
        selected["database_spans"] = {
            k: v for k, v in data["spans"].items() if k.startswith("diag-db-")
        }
    result[name] = {"input": provenance, "selected": selected}
output = OUT / "DIRECT16_DATABASE_DELTAS.PUBLIC.json"
output.write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result, indent=2))
