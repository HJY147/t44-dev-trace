"""Read-only explicit native process interval metrics; no requests, secrets or business I/O."""

import argparse
import hashlib
import importlib.util
import json
import os
import signal
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

END = datetime(2026, 10, 25, 9, 9, tzinfo=UTC).timestamp()


def context(run):
    path = run / "controller.py"
    manifest = json.loads((run / "manifest.json").read_text())
    if path.is_symlink() or hashlib.sha256(path.read_bytes()).hexdigest() != manifest["controller_sha256"]:
        raise ValueError("IMMUTABLE_CONTROLLER_CHANGED")
    spec = importlib.util.spec_from_file_location("interval_owned_controller", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.load(run)
    return module


def cpu_seconds(value):
    days = 0
    if "-" in value:
        day, value = value.split("-", 1)
        days = int(day)
    parts = value.split(":")
    if len(parts) not in (2, 3):
        raise ValueError("UNRECOGNIZED_CUMULATIVE_CPU_TIME")
    result = days * 86400 + float(parts[-1]) + int(parts[-2]) * 60
    if len(parts) == 3:
        result += int(parts[-3]) * 3600
    if result < 0 or not 0 <= float(parts[-1]) < 60:
        raise ValueError("INVALID_CUMULATIVE_CPU_TIME")
    return result


def snapshot(pids):
    if not pids:
        return {}
    result = subprocess.run(
        ["/bin/ps", "-p", ",".join(str(v) for v in sorted(set(pids))), "-o", "pid=,uid=,pgid=,lstart=,time=,rss="],
        capture_output=True,
        text=True,
        timeout=3,
    )
    rows = {}
    for line in result.stdout.splitlines():
        fields = line.split()
        if len(fields) != 10:
            raise ValueError("UNRECOGNIZED_PROCESS_METADATA")
        pid, uid, group = map(int, fields[:3])
        rows[pid] = {
            "pid": pid,
            "uid": uid,
            "pgid": group,
            "started": " ".join(fields[3:8]),
            "cpu_seconds": cpu_seconds(fields[8]),
            "memory_bytes": int(fields[9]) * 1024,
        }
    return rows


def identity(value):
    return {key: value[key] for key in ("pid", "uid", "pgid", "started")}


def targets(run, module):
    result = {name: [] for name in ("api", "consumer", "scheduler", "broker", "mysql", "generator")}
    for role in ("api", "consumer", "scheduler"):
        path = run / "state" / (role + ".json")
        if path.exists():
            result[role].append(identity(module.read(path)))
    children = run / "state/api-children.json"
    if children.exists():
        result["api"] += [identity(row) for row in module.read(children)["children"]]
    broker = Path(module.read(run / "broker-binding.json")["run_dir"])
    expected = module.BASE / "brokers" / run.name
    if broker != expected:
        raise ValueError("OWNED_BROKER_PATH_REQUIRED")
    for role in ("rabbit", "epmd"):
        path = broker / "state" / (role + ".json")
        if path.exists():
            result["broker"].append(identity(module.read(path)))
    inputs = module.read(run / "state/interval-inputs.json")
    result["mysql"] = [inputs["mysql"]]
    if inputs.get("generator"):
        result["generator"] = [inputs["generator"]]
    return result


def interval_row(resource, expected, observed, previous, tick, utc):
    row = {
        "utc": utc,
        "resource_id": resource,
        "cpu_percent": None,
        "memory_bytes": None,
        "shared": resource == "mysql",
        "pid_list": [r["pid"] for r in expected],
        "cpu_semantics": "cumulative process user+system CPU delta / monotonic wall delta;100=one CPU",
        "memory_semantics": "sum process RSS bytes;shared pages may be counted more than once",
    }
    if resource == "api":
        row["aggregation"] = "seven workers plus supervisor and resource tracker"
    elif resource == "broker":
        row["aggregation"] = "new Rabbit VM plus its EPMD"
    elif resource == "mysql":
        row["scope"] = "whole shared MySQL PID7980;not exclusive to the performance schema"
    elif resource == "generator":
        row["scope"] = "explicit root-supplied PID only;no descendant discovery"
    if not expected:
        row["status"] = "not_registered_or_not_started"
        return row, None
    valid = all(r["pid"] in observed and identity(observed[r["pid"]]) == r for r in expected)
    if not valid:
        row["status"] = "missing_or_identity_changed"
        return row, None
    total = sum(observed[r["pid"]]["cpu_seconds"] for r in expected)
    row["memory_bytes"] = sum(observed[r["pid"]]["memory_bytes"] for r in expected)
    current = {"identities": expected, "cpu": total, "tick": tick}
    if previous is None or previous["identities"] != expected:
        row["status"] = "first_sample_no_cpu_delta"
    elif tick <= previous["tick"] or total < previous["cpu"]:
        row["status"] = "invalid_or_regressed_cpu_counter"
    else:
        row["interval_seconds"] = tick - previous["tick"]
        row["cpu_percent"] = (total - previous["cpu"]) * 100 / row["interval_seconds"]
        row["status"] = "observed"
    return row, current


def collect(run):
    module = context(run)
    path = run / "state" / ("interval-resources-" + uuid4().hex + ".jsonl")
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    end_mono = time.monotonic() + max(0, END - time.time())
    requested, previous, counts = [], {}, {}

    def request(signum, _frame):
        requested.append(signum)

    signal.signal(signal.SIGTERM, request)
    signal.signal(signal.SIGINT, request)
    first, last, fatal, rows_written = None, None, None, 0
    next_tick = time.monotonic()
    try:
        with os.fdopen(descriptor, "w") as output:
            while not requested and time.time() < END and time.monotonic() < end_mono:
                tick = time.monotonic()
                utc = datetime.now(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")
                selected = targets(run, module)
                try:
                    observed = snapshot([r["pid"] for values in selected.values() for r in values])
                    error = None
                except (OSError, ValueError, subprocess.SubprocessError):
                    observed, error = {}, "PROCESS_METADATA_UNAVAILABLE"
                for resource, expected in selected.items():
                    row, previous[resource] = interval_row(
                        resource, expected, observed, previous.get(resource), tick, utc
                    )
                    row["monotonic_ns"] = int(tick * 1e9)
                    row["sampling_window_seconds"] = time.monotonic() - tick
                    if error:
                        row["metadata_error"] = error
                    output.write(json.dumps(row, separators=(",", ":")) + "\n")
                    counts[resource + ":" + row["status"]] = counts.get(resource + ":" + row["status"], 0) + 1
                    rows_written += 1
                output.flush()
                first, last = first or utc, utc
                next_tick += 1
                if next_tick < time.monotonic():
                    next_tick = time.monotonic() + 1
                while not requested and time.monotonic() < next_tick and time.time() < END:
                    time.sleep(min(0.1, max(0, next_tick - time.monotonic())))
    except (OSError, ValueError, RuntimeError, KeyError):
        fatal = "SAMPLER_METADATA_OR_OUTPUT_FAILED"
    finally:
        receipt = module.receipt(
            run,
            "interval_sampler_final",
            success=fatal is None,
            collection_completed=fatal is None,
            error=fatal,
            output_path=str(path),
            output_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
            output_bytes=path.stat().st_size,
            first_utc=first,
            last_utc=last,
            rows_written=rows_written,
            resource_status_counts=counts,
            stop_reason="signal" if requested else "09:09UTC deadline",
            resource_coverage_is_separate_from_collection_success=True,
        )
        module.save(run / "interval-final.json", receipt)
    return receipt


def operate(run, action, generator_pid=None):
    module = context(run)
    if action == "run":
        return collect(run)
    if action == "register-generator":
        if generator_pid is None or generator_pid <= 0:
            raise ValueError("EXPLICIT_GENERATOR_PID_REQUIRED")
        observed = snapshot([generator_pid])
        if generator_pid not in observed:
            raise ValueError("EXPLICIT_GENERATOR_PID_ABSENT")
        current = module.read(run / "state/interval-inputs.json")
        current["generator"] = identity(observed[generator_pid])
        module.save(run / "state/interval-inputs.json", current, replace=True)
        return module.receipt(
            run,
            "interval_generator_registered",
            success=True,
            pid=generator_pid,
            identity=current["generator"],
            source="root explicit PID;no test directory read",
        )
    if action == "stop":
        record, actual = module.owned(run, "interval_sampler")
        if actual is not None:
            os.kill(record["pid"], signal.SIGTERM)
            end = time.monotonic() + 5
            while time.monotonic() < end and module.owned(run, "interval_sampler")[1] is not None:
                time.sleep(0.1)
        return module.receipt(run, "interval_sampler_stop", success=module.owned(run, "interval_sampler")[1] is None)
    if time.time() >= END:
        raise ValueError("SAMPLER_WINDOW_CLOSED")
    initial = snapshot([7980])
    if 7980 not in initial:
        raise ValueError("ROOT_SPECIFIED_SHARED_MYSQL_ABSENT")
    module.save(run / "state/interval-inputs.json", {"mysql": identity(initial[7980]), "generator": None})
    module.write(run / "interval-metrics.py", Path(__file__).read_bytes())
    record = module.spawn(
        run,
        "interval_sampler",
        [sys.executable, run / "interval-metrics.py", "run", "--run-dir", run],
        module.environment(),
    )
    return module.receipt(
        run,
        "interval_sampler_start",
        success=True,
        pid=record["pid"],
        stop_utc="2026-10-25T09:09:00Z",
        resources=["api", "consumer", "scheduler", "broker", "mysql", "generator"],
        shared_mysql=True,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("start", "run", "stop", "register-generator"))
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--generator-pid", type=int)
    args = parser.parse_args()
    os.umask(0o077)
    try:
        result = operate(args.run_dir, args.action, args.generator_pid)
        print(json.dumps(result))
        raise SystemExit(0 if result["success"] else 1)
    except (OSError, ValueError, RuntimeError, KeyError, subprocess.SubprocessError):
        print(json.dumps({"success": False, "error": "INTERVAL_RESOURCE_STEP_FAILED"}))
        raise SystemExit(1) from None
