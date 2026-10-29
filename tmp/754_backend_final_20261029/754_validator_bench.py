"""ABBA local CPU-only comparison, never HTTP latency or performance acceptance."""

import json
import statistics
import subprocess
import time
from pathlib import Path
from types import ModuleType

from t44 import api, contracts

BASE = "5868779e949adef066fe26bffbc4f2e8afee7649"
module = ModuleType("_bench_original_contracts")
module.__package__ = "t44.contracts"
exec(
    compile(
        subprocess.check_output(["git", "show", BASE + ":backend/t44/contracts/__init__.py"]),
        BASE + "/contracts.py",
        "exec",
    ),
    module.__dict__,
)
operation = contracts.OPERATIONS["createTask"]
create = api._body_schema(operation["requestBody"]["content"]["application/json"]["schema"], {})
row = {
    "id": 1,
    "project_id": 1,
    "iteration_id": 1,
    "title": "synthetic",
    "description": "",
    "owner_id": 1,
    "state": 1,
    "version": 1,
    "schedule_version": 1,
    "delivery_cycle": 1,
    "review_cycle": 1,
    "plan": {
        "planned_start": "2026-10-29T00:00:00Z",
        "planned_end": "2026-10-30T00:00:00Z",
        "estimated_hours": 1,
        "buffer_hours": 0.25,
        "delay_contingency": "synthetic",
    },
    "blocked_from_state": None,
    "block_reason": None,
    "responsibility_stage": None,
    "latest_review_id": None,
    "approved_review_id": None,
    "approved_assessment_id": None,
    "approved_assessment_version": None,
    "escalation_count": 0,
    "created_at": "2026-10-29T00:00:00Z",
    "updated_at": "2026-10-29T00:00:00Z",
    "artifact_revision": None,
}
body = {
    "title": row["title"],
    "iteration_id": 1,
    "owner_id": 1,
    "plan": row["plan"],
    "dependency_task_ids": [],
}
response = contracts.OPERATIONS["getTask"]["responses"]["200"]["content"]["application/json"][
    "schema"
]
result = {
    "data": row,
    "meta": {
        "request_id": "synthetic",
        "server_time": "2026-10-29T00:00:00Z",
        "contract_version": contracts.VERSION,
        "replayed": False,
        "original_request_id": None,
    },
}
cases = {
    "large-invalid EvidenceRefs": (
        contracts.SPEC["components"]["schemas"]["EvidenceRefs"],
        [None] * 5000,
    ),
    "Task component": (contracts.SPEC["components"]["schemas"]["Task"], row),
    "createTask body": (create, body),
    "getTask HTTP envelope": (response, result),
}
records = {}
for name, (schema, value) in cases.items():
    assert contracts.violations(schema, value) == module.violations(schema, value)
    block_calls = 10 if name.startswith("large-invalid") else 100
    for _ in range(20):
        module.violations(schema, value)
        contracts.violations(schema, value)
    samples = {"baseline": [], "candidate": []}
    for _ in range(5):
        for label, owned in [
            ("baseline", module),
            ("candidate", contracts),
            ("candidate", contracts),
            ("baseline", module),
        ]:
            started = time.perf_counter_ns()
            for _ in range(block_calls):
                owned.violations(schema, value)
            samples[label].append((time.perf_counter_ns() - started) / block_calls / 1000)
    old, new = (statistics.median(samples[label]) for label in ("baseline", "candidate"))
    records[name] = {
        "microseconds_per_call_median": {"baseline": old, "candidate": new},
        "speedup": old / new,
        "calls_per_block": block_calls,
        "samples_microseconds": samples,
    }
output = {
    "scope": "LOCAL_CPU_MICROBENCH_ONLY_NOT_HTTP_P95_OR_CLOUD_ACCEPTANCE",
    "baseline": BASE,
    "rounds": 5,
    "abba_block_calls": 100,
    "cases": records,
}
path = Path("agents/backend/final-20261029/validator-benchmark.PUBLIC.json")
path.write_text(json.dumps(output, indent=2) + "\n")
print(
    json.dumps(
        {
            name: {
                "old_us": round(row["microseconds_per_call_median"]["baseline"], 2),
                "new_us": round(row["microseconds_per_call_median"]["candidate"], 2),
                "speedup": round(row["speedup"], 3),
            }
            for name, row in records.items()
        }
    )
)
