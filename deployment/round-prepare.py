"""Materialize a new explicitly bounded round; never execute generated commands."""

import argparse
import ast
import hashlib
import json
import os
import re
import stat
import subprocess
from datetime import UTC, datetime, timedelta
from pathlib import Path

BASE = "ade5e4c1998b4c2f014afde8c011645c6c5a7412"
OLD_SOURCE = "0dfb55c2191200d947c5423fd9ee74bb0812cc5a"
PINS = {
    "ubuntu24-bootstrap.sh": "9786139dfb39583f8809fd2c39044ea8ea441f9df55ed22032d8c323190f1929",
    "ecr-build-policy-v2.py": "46758e3dbbcfca98994896135dfbcd4f9dcaa307210c7fac4cf8523cae046417",
    "api-pypi-delivery.py": "5950541879e16cbbe2f12f899afc29cb69aa8a84145fff52773d596f2a0e091b",
    "tls-delivery-extended.py": "ea1b5873efb359e2e4e4adb8f020bfeab3da8f20e7661ae7bb7a5d883ac121d9",
    "seven-resource-sampler-v3.py": "4bddc93a20b26d7a86a109a2d7e8d409a004265ebae1c4f6d81beaa6cb98b9d5",
    "host-resource-sampler.py": "7a0f8c9c16aff233f37a1f8f02c27848dc110a7deb28800550ca38f28716259d",
    "resource-evidence-export.py": "78a25242769c393d28394722378f6b80ecb12f1e0efcb600fc32f805bbcd55df",
}
ASSUMPTIONS = ("backend/t44/persistence/engine.py", "backend/t44/settings.py", "compose.yaml")


def digest(data):
    return hashlib.sha256(data).hexdigest()


def source_assumptions(repository, source, read=None):
    """Refuse the declared15-per-engine budget if its source/config basis changed."""
    if read is None:

        def read(revision, name):
            return subprocess.run(
                ["git", "-C", str(repository), "show", revision + ":" + name],
                check=True,
                capture_output=True,
                timeout=5,
            ).stdout

    result = {}
    for name in ASSUMPTIONS:
        original, selected = read(BASE, name), read(source, name)
        if selected != original:
            raise ValueError("POOL_OR_COMPOSE_ASSUMPTION_CHANGED:" + name)
        result[name] = digest(selected)
    return result


def utc(value):
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", value):
        raise ValueError("SECOND_PRECISION_UTC_REQUIRED")
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def checked_plan(value, now):
    fields = {
        "round_id",
        "source_sha",
        "issued_utc",
        "operation_deadline_utc",
        "sample_end_utc",
        "evidence_deadline_utc",
        "release_utc",
        "api_workers",
        "mysql_max_connections",
        "sample_max_seconds",
        "run_budget_cny",
    }
    if not isinstance(value, dict) or set(value) != fields:
        raise ValueError("EXACT_PLAN_FIELDS_REQUIRED")
    if not re.fullmatch(r"[a-z][a-z0-9]{7,19}", value["round_id"]):
        raise ValueError("ROUND_ID_REQUIRED")
    if not re.fullmatch(r"[0-9a-f]{40}", value["source_sha"]):
        raise ValueError("EXACT_SOURCE_REQUIRED")
    clocks = [
        utc(value[n])
        for n in ("issued_utc", "operation_deadline_utc", "sample_end_utc", "evidence_deadline_utc", "release_utc")
    ]
    issued, operation, sample, evidence, release = clocks
    if not (
        now - timedelta(seconds=60) <= issued <= now
        and now + timedelta(seconds=300) < operation <= sample
        and sample + timedelta(seconds=600) <= evidence
        and evidence + timedelta(seconds=600) <= release <= issued + timedelta(hours=4)
    ):
        raise ValueError("EXPLICIT_FRESH_BOUNDED_WINDOW_REQUIRED")
    workers, connections = value["api_workers"], value["mysql_max_connections"]
    if type(workers) is not int or not 1 <= workers <= 64:
        raise ValueError("WORKER_BOUND_REQUIRED")
    minimum = 15 * (workers + 2) + 30
    if type(connections) is not int or not minimum <= connections <= 2048:
        raise ValueError("DECLARED_CONNECTION_BUDGET_INSUFFICIENT")
    if type(value["sample_max_seconds"]) is not int or not 600 <= value["sample_max_seconds"] <= 10800:
        raise ValueError("SAMPLER_CAP_REQUIRED")
    if type(value["run_budget_cny"]) not in (int, float) or not 0 < value["run_budget_cny"] <= 100:
        raise ValueError("ROOT_ALLOCATED_RUN_BUDGET_REQUIRED")
    result = dict(value)
    result.update(
        source_dir="/opt/t44-" + value["round_id"],
        app_runtime="/run/t44-" + value["round_id"] + "/app",
        load_runtime="/run/t44-" + value["round_id"] + "/load",
        project="t44-" + value["round_id"],
        database="t44_" + value["round_id"],
        operation_epoch=int(operation.timestamp()),
        sample_epoch=int(sample.timestamp()),
        evidence_epoch=int(evidence.timestamp()),
        minimum_connections=minimum,
    )
    return result


def render(value, originals, now):
    plan = checked_plan(value, now)
    if set(originals) != set(PINS):
        raise ValueError("TEMPLATE_SET_DIFFERS")
    for name, expected in PINS.items():
        if digest(originals[name]) != expected:
            raise ValueError("IMMUTABLE_TEMPLATE_HASH_DIFFERS")
    files, deltas = {}, {}
    for name, raw in originals.items():
        text, changes = raw.decode(), []

        def replace(old, new, count=None, _name=name, _changes=changes):
            nonlocal text
            actual = text.count(old)
            if actual == 0 or count is not None and actual != count:
                raise ValueError("ALLOWED_PATCH_POSITION_DIFFERS:" + _name)
            text = text.replace(old, new)
            _changes.append({"old": old, "new": new, "occurrences": actual})

        if OLD_SOURCE in text:
            replace(OLD_SOURCE, plan["source_sha"])
        if "/opt/t44-c-0dfb55c" in text:
            replace("/opt/t44-c-0dfb55c", plan["source_dir"])
        if "/run/t44-delivery" in text:
            replace("/run/t44-delivery", plan["app_runtime"])
        if "/run/t44-relay852" in text:
            replace("/run/t44-relay852", plan["load_runtime"])
        if name == "ubuntu24-bootstrap.sh":
            replace("2026-10-24T09:00:00Z", plan["operation_deadline_utc"], 1)
            replace(
                "Original17:00 Beijing deadline is near/past; do not extend it.",
                "This round deadline is near/past; do not extend it.",
                1,
            )
        if name == "tls-delivery-extended.py":
            replace("datetime(2026, 10, 24, 10, 30, tzinfo=UTC).timestamp()", str(plan["operation_epoch"]), 1)
            mysql_command = [
                "--character-set-server=utf8mb4",
                "--collation-server=utf8mb4_0900_ai_ci",
                "--max-connections=" + str(plan["mysql_max_connections"]),
            ]
            api_command = [
                "python",
                "-m",
                "uvicorn",
                "t44.api:app",
                "--host",
                "0.0.0.0",
                "--port",
                "8000",
                "--workers",
                str(plan["api_workers"]),
                "--no-access-log",
                "--no-proxy-headers",
            ]
            replace(
                '"mysql": {"image": IMAGES["mysql"]}',
                '"mysql": {"image": IMAGES["mysql"], "command": ' + repr(mysql_command) + "}, "
                '"api": {"command": ' + repr(api_command) + "}",
                1,
            )
            replace("API4workers", "API" + str(plan["api_workers"]) + "workers", 1)
            replace(
                "    return values\n",
                '    if (values["COMPOSE_PROJECT_NAME"] != '
                + repr(plan["project"])
                + ' or values["MYSQL_DATABASE"] != '
                + repr(plan["database"])
                + "):\n"
                '        raise ValueError("round_project_or_database_differs")\n    return values\n',
                1,
            )
        if name in {"seven-resource-sampler-v3.py", "host-resource-sampler.py"}:
            replace("datetime(2026, 10, 24, 10, 10, tzinfo=UTC).timestamp()", str(plan["sample_epoch"]), 1)
            replace("2026-10-24T10:10:00Z", plan["sample_end_utc"], 1)
            replace("5400", str(plan["sample_max_seconds"]), 2)
            if name == "seven-resource-sampler-v3.py":
                replace('PROJECT = "t44"', "PROJECT = " + repr(plan["project"]), 1)
                replace(
                    '"project": PROJECT, "cpu_count": os.cpu_count(),',
                    '"project": PROJECT, "clock_anchor": {"realtime_ns": time.time_ns(), '
                    '"perf_counter_ns": time.perf_counter_ns(), "monotonic_ns": time.monotonic_ns()}, '
                    '"cpu_count": os.cpu_count(),',
                    1,
                )
            else:
                replace(
                    '"cpu_count": cpu_count, "cpu_count_source":',
                    '"clock_anchor": {"realtime_ns": time.time_ns(), "perf_counter_ns": time.perf_counter_ns(), '
                    '"monotonic_ns": time.monotonic_ns()}, "cpu_count": cpu_count, "cpu_count_source":',
                    1,
                )
        if name == "resource-evidence-export.py":
            replace("datetime(2026, 10, 24, 10, 10, tzinfo=UTC).timestamp()", str(plan["sample_epoch"]), 1)
            replace("datetime(2026, 10, 24, 10, 28, tzinfo=UTC).timestamp()", str(plan["evidence_epoch"]), 1)
            replace('row["project"] != "t44"', 'row["project"] != ' + repr(plan["project"]), 1)
        data = text.encode()
        if name.endswith(".py"):
            ast.parse(data, filename=name)
        files[name], deltas[name] = data, changes
    manifest = {
        "format": "t44-explicit-new-round-v1",
        "template_git_commit": BASE,
        "plan": plan,
        "files": {
            name: {
                "template_sha256": PINS[name],
                "sha256": digest(data),
                "bytes": len(data),
                "allowed_changes": deltas[name],
            }
            for name, data in files.items()
        },
        "old_templates_modified_or_executed": False,
        "generated_files_executed": False,
        "network_or_cloud_api_used": False,
        "source_policy_output_sha256_unchanged": "f9101355c4bf7b9d51e9feda2d8e48361e0d3a9ff81cb5f71ccd49bbb775e1f8",
        "declared_pool_capacity_per_process": 15,
        "runtime_values_observed": False,
        "not_generated": [
            "fixture-launcher-cloud.py",
            "service-fixture-launcher-cloud.py",
            "encrypted-service-fixture.py",
            "new independent test tools or credentials",
        ],
        "not_generated_reason": "Fresh recipient certificate and source-bound fixture worker/admin pins require separate approval",
        "performance_verdict": None,
    }
    return files, manifest


def private_bytes(path):
    if not path.is_absolute() or path.parent.resolve() != path.parent:
        raise ValueError("CANONICAL_PRIVATE_INPUT_REQUIRED")
    parent = path.parent.lstat()
    if not stat.S_ISDIR(parent.st_mode) or parent.st_uid != os.geteuid() or stat.S_IMODE(parent.st_mode) != 0o700:
        raise ValueError("PRIVATE_INPUT_PARENT_REQUIRED")
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(fd, "rb") as stream:
        before = os.fstat(stream.fileno())
        if (
            not stat.S_ISREG(before.st_mode)
            or before.st_uid != os.geteuid()
            or before.st_nlink != 1
            or stat.S_IMODE(before.st_mode) != 0o600
            or before.st_size > 65536
        ):
            raise ValueError("PRIVATE_PLAN_REQUIRED")
        data = stream.read(65537)
        after = os.fstat(stream.fileno())
    if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (
        after.st_dev,
        after.st_ino,
        after.st_size,
        after.st_mtime_ns,
        after.st_ctime_ns,
    ) or len(data) != before.st_size:
        raise ValueError("PLAN_CHANGED")
    return data


def write_bundle(output, files, manifest):
    if not output.is_absolute() or output.parent.resolve() != output.parent or ".." in output.parts:
        raise ValueError("CANONICAL_NEW_OUTPUT_REQUIRED")
    parent = output.parent.lstat()
    if not stat.S_ISDIR(parent.st_mode) or parent.st_uid != os.geteuid() or stat.S_IMODE(parent.st_mode) != 0o700:
        raise ValueError("PRIVATE_OUTPUT_PARENT_REQUIRED")
    output.mkdir(mode=0o700)
    for name, data in {**files, "derivation.json": (json.dumps(manifest, indent=2) + "\n").encode()}.items():
        fd = os.open(output / name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    os.umask(0o077)
    try:
        value = json.loads(private_bytes(args.plan))
        admitted_now = datetime.now(UTC)
        checked_plan(value, admitted_now)
        subprocess.run(
            ["git", "-C", str(args.repository), "cat-file", "-e", value["source_sha"] + "^{commit}"],
            check=True,
            capture_output=True,
            timeout=5,
        )
        originals = {
            name: subprocess.run(
                ["git", "-C", str(args.repository), "show", BASE + ":deployment/" + name],
                check=True,
                capture_output=True,
                timeout=5,
            ).stdout
            for name in PINS
        }
        assumptions = source_assumptions(args.repository, value["source_sha"])
        files, manifest = render(value, originals, admitted_now)
        manifest["selected_source_assumption_sha256"] = assumptions
        write_bundle(args.output, files, manifest)
        print(
            json.dumps(
                {
                    "materialized": True,
                    "files": len(files),
                    "output": str(args.output),
                    "derivation_sha256": digest((args.output / "derivation.json").read_bytes()),
                    "executed": False,
                }
            )
        )
        return 0
    except (OSError, ValueError, TypeError, KeyError, SyntaxError, subprocess.SubprocessError):
        print(
            json.dumps(
                {
                    "materialized": False,
                    "error": "ROUND_PREPARATION_REFUSED",
                    "partial_output_may_exist": True,
                    "executed": False,
                }
            )
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
