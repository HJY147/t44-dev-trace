"""Development regressions for offline join and opt-in guards, never opens MySQL."""

import copy
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
DIRECTORY = Path(__file__).parent


def load(name):
    spec = importlib.util.spec_from_file_location(name, DIRECTORY / name)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sample():
    return {
        "source": "test-source",
        "database_observer_module_sha256": "test-observer",
        "environment": {},
        "utc_start": "start",
        "utc_end": "end",
        "cleanup_errors": [],
        "requests": [
            {
                "request_id": "one",
                "operation": "getTask",
                "phase": "measured",
                "client_wall_ns": 20,
            },
            {
                "request_id": "two",
                "operation": "getTask",
                "phase": "profile",
                "client_wall_ns": 2000,
            },
        ],
        "database_observer": {
            "pending_cursor_spans": 0,
            "actual_pool": {},
            "actual_dbapi_timeout_profiles": [],
            "outside_request_phases": {},
            "ping_returned_false": 0,
            "records": [
                {
                    "request_id": identifier,
                    "operation_id": "getTask",
                    "sql_samples_dropped": 0,
                    "phases": {
                        "cursor_execute_inclusive": {
                            "count": 1,
                            "wall_ns": wall,
                            "thread_cpu_ns": wall // 2,
                            "errors": 0,
                        }
                    },
                    "sql": [
                        {
                            "verb": "SELECT",
                            "tables": ["tasks"],
                            "shape_sha256": "shape",
                            "wall_ns": wall,
                            "thread_cpu_ns": wall // 2,
                        }
                    ],
                    "wall_ns": wall,
                    "thread_cpu_ns": wall // 2,
                    "mapping_rows": 1,
                }
                for identifier, wall in (("one", 10), ("two", 1000))
            ],
        },
    }


def test_join_excludes_profile_and_preserves_source():
    module = load("833_mysql_summary.py")
    result = module.summarize(sample())
    assert result["requests_joined"] == 2
    assert result["operations"]["getTask"]["observer_wall_ns"]["mean"] == 10
    assert result["phase_counts"] == {"measured": 1, "profile": 1}
    assert result["actual_dbapi_timeout_profiles"] == []


@pytest.mark.parametrize(
    "mutation", ("duplicate", "unmatched", "operation", "dropped", "pending", "cleanup")
)
def test_join_refuses_incomplete_or_wrong_requests(mutation):
    data = copy.deepcopy(sample())
    observer = data["database_observer"]
    if mutation == "duplicate":
        observer["records"][1]["request_id"] = "one"
    elif mutation == "unmatched":
        observer["records"][1]["request_id"] = "other"
    elif mutation == "operation":
        observer["records"][1]["operation_id"] = "listTasks"
    elif mutation == "dropped":
        observer["records"][1]["sql_samples_dropped"] = 1
    elif mutation == "pending":
        observer["pending_cursor_spans"] = 1
    else:
        data["cleanup_errors"] = [{"phase": "close"}]
    with pytest.raises(ValueError):
        load("833_mysql_summary.py").summarize(data)


def test_mysql_probe_refuses_local_environment_and_retains_failure(tmp_path):
    output = tmp_path / "guard.json"
    env = {**os.environ, "PYTHONPATH": str(ROOT / "backend"), "DATABASE_URL": "invalid://unused"}
    env.pop("CI", None)
    process = subprocess.run(
        [
            sys.executable,
            str(DIRECTORY / "833_mysql_lock_probe.py"),
            "--allow-fresh-mysql-ci",
            "--expected-reader-lock",
            "update",
            "--expected-task-lock-shape",
            "batch",
            "--expected-runtime-sha256",
            "unused",
            "--output",
            str(output),
        ],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
        timeout=20,
    )
    assert process.returncode != 0
    result = json.loads(output.read_text())
    assert result["failure"]["exception_class"] == "ValueError"
    assert result["status"] == "failed retained"
    assert "Fresh CI MySQL gate required" in process.stderr
    original = output.read_bytes()
    again = subprocess.run(
        process.args, cwd=ROOT, env=env, capture_output=True, check=False, timeout=20
    )
    assert again.returncode != 0
    assert output.read_bytes() == original
