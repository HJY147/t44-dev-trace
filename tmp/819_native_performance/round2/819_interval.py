"""Pure interval CPU/unit/missing-identity checks; no service or process access."""

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
SPEC = importlib.util.spec_from_file_location("interval_guard", ROOT / "deployment/native/interval-metrics.py")
METRICS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(METRICS)


@pytest.mark.parametrize(
    "raw,seconds", [("0:01.25", 1.25), ("12:01.25", 721.25), ("1:02:03.5", 3723.5), ("1-00:00:01.0", 86401.0)]
)
def test_cumulative_cpu_seconds_units(raw, seconds):
    assert METRICS.cpu_seconds(raw) == seconds


def test_interval_delta_and_memory_sum_are_not_ps_lifetime_percent():
    expected = [
        {"pid": 1, "uid": 501, "pgid": 1, "started": "one"},
        {"pid": 2, "uid": 501, "pgid": 1, "started": "two"},
    ]
    observed = {
        1: expected[0] | {"cpu_seconds": 10.0, "memory_bytes": 1024},
        2: expected[1] | {"cpu_seconds": 20.0, "memory_bytes": 2048},
    }
    first, previous = METRICS.interval_row("api", expected, observed, None, 100.0, "synthetic")
    assert first["cpu_percent"] is None and first["memory_bytes"] == 3072
    observed[1]["cpu_seconds"] += 0.25
    observed[2]["cpu_seconds"] += 0.75
    second, _ = METRICS.interval_row("api", expected, observed, previous, 102.0, "synthetic")
    assert second["cpu_percent"] == 50.0 and second["interval_seconds"] == 2.0


def test_missing_pid_is_null_not_zero_or_fabricated_coverage():
    expected = [{"pid": 1, "uid": 501, "pgid": 1, "started": "one"}]
    row, current = METRICS.interval_row("mysql", expected, {}, None, 100, "synthetic")
    assert row["cpu_percent"] is None and row["memory_bytes"] is None and current is None
    assert row["shared"] is True and "not exclusive" in row["scope"]


def test_reused_pid_identity_is_not_attributed_to_old_resource():
    expected = [{"pid": 1, "uid": 501, "pgid": 1, "started": "old"}]
    observed = {1: expected[0] | {"started": "reused", "cpu_seconds": 10, "memory_bytes": 1024}}
    row, _ = METRICS.interval_row("generator", expected, observed, None, 100, "synthetic")
    assert row["status"] == "missing_or_identity_changed" and row["cpu_percent"] is None
