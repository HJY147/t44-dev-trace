"""Read-only owned MySQL observations and explicit v4 connection-budget admission."""

import fcntl
import hashlib
import json
import os
import re
import selectors
import stat
import subprocess
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

DOCKER = ["docker", "--context", "default"]
POOL_KEYS = ("T44_DB_POOL_SIZE", "T44_DB_MAX_OVERFLOW")
KIND = "exact-pinned-production-entry-generation-v4"
RESERVE = {
    "consumer": 15,
    "scheduler": 15,
    "one_serial_operation": 15,
    "health_probes": 4,
    "persistent_observer": 1,
    "transient_budget_probe": 1,
    "unallocated_safety": 13,
}
SQL = (
    "SELECT JSON_OBJECT('max_connections',@@GLOBAL.max_connections,"
    "'server_uuid',@@GLOBAL.server_uuid,'database',DATABASE(),"
    "'connection_id',CONNECTION_ID(),"
    + ",".join(
        "'"
        + name
        + "',CAST((SELECT VARIABLE_VALUE FROM performance_schema.global_status "
        "WHERE VARIABLE_NAME='" + name + "') AS UNSIGNED)"
        for name in (
            "Connections",
            "Threads_connected",
            "Max_used_connections",
            "Uptime",
            "Threads_running",
        )
    )
    + ");\n"
)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def stamp():
    return datetime.now(timezone.utc).isoformat()  # noqa: UP017 -- cloud Python 3.10.


def expiry(value):
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("ABSOLUTE_UTC_REQUIRED")
    return parsed.timestamp()


def private(path, directory=False):
    current = path.lstat()
    if (
        path.resolve() != path
        or current.st_uid != os.geteuid()
        or stat.S_IMODE(current.st_mode) != (0o700 if directory else 0o600)
        or not (
            stat.S_ISDIR(current.st_mode)
            if directory
            else stat.S_ISREG(current.st_mode)
        )
    ):
        raise ValueError("CANONICAL_OWNED_PRIVATE_OBJECT_REQUIRED")


def checked_binding(phase, expected):
    private(phase, True)
    private(phase / "binding.json")
    raw = (phase / "binding.json").read_bytes()
    if not re.fullmatch(r"[0-9a-f]{64}", expected or "") or digest(raw) != expected:
        raise ValueError("EXACT_V4_PHASE_BINDING_REQUIRED")
    value = json.loads(raw)
    if value.get("generation_kind") != KIND:
        raise ValueError("V4_ONLY_NO_OLD_CAMPAIGN_ADOPTION")
    return value


@contextmanager
def operation_lock(phase, binding_sha256, timeout_seconds=10, *, observer=False):
    """Shared with the backend bridge; never hold this lock across a child GEN call."""
    if type(timeout_seconds) not in (int, float) or not 0 <= timeout_seconds <= 30:
        raise ValueError("LOCK_TIMEOUT_0_TO_30_SECONDS_REQUIRED")
    checked_binding(phase, binding_sha256)
    path = phase / (".v4-observer.lock" if observer else ".v4-operation.lock")
    fd = os.open(path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600)
    try:
        state = os.fstat(fd)
        named = path.lstat()
        if (
            not stat.S_ISREG(state.st_mode)
            or state.st_uid != os.geteuid()
            or stat.S_IMODE(state.st_mode) != 0o600
            or state.st_nlink != 1
            or (state.st_dev, state.st_ino) != (named.st_dev, named.st_ino)
        ):
            raise ValueError("EXACT_OWNED_0600_LOCK_FD_REQUIRED")
        until = time.monotonic() + timeout_seconds
        while True:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.monotonic() >= until:
                    raise ValueError("PHASE_OPERATION_MUTEX_TIMEOUT") from None
                time.sleep(min(0.05, max(0, until - time.monotonic())))
        if path.lstat().st_ino != state.st_ino:
            raise ValueError("LOCK_NAME_CHANGED")
        checked_binding(phase, binding_sha256)
        yield fd
    finally:
        os.close(fd)


def pool_plan(phase, workers, size, overflow):
    if any(type(n) is not int for n in (workers, size, overflow)):
        raise ValueError("EXPLICIT_INTEGER_WORKER_AND_POOL_PLAN_REQUIRED")
    permitted = {7: {(5, 10)}, 16: {(5, 10), (15, 0), (20, 0)}, 64: {(5, 0)}}
    if phase == "f":
        if (workers, size, overflow) != (4, 5, 10):
            raise ValueError("F4_DEFAULT_POOL_ONLY")
    elif phase != "p" or (size, overflow) not in permitted.get(workers, set()):
        raise ValueError("EXPLICIT_REVIEWED_P_WORKER_POOL_COMBINATION_REQUIRED")
    reserve = sum(RESERVE.values())
    assert reserve == 64
    return {
        "api_workers": workers,
        "api_pool_size": size,
        "api_max_overflow": overflow,
        "api_capacity": workers * (size + overflow),
        "reserve_breakdown": RESERVE.copy(),
        "reserve_capacity": reserve,
        "required_max_connections": workers * (size + overflow) + reserve,
        "other_settings_roles_default": {"pool_size": 5, "max_overflow": 10},
        "operation_mutex_contract": "one operation at a time; bridge SQL releases before GEN child",
    }


def checked_plan(value):
    expected = pool_plan(
        value["phase"],
        value["api_workers"],
        value["v4_pool_plan"]["api_pool_size"],
        value["v4_pool_plan"]["api_max_overflow"],
    )
    if value["v4_pool_plan"] != expected:
        raise ValueError("FROZEN_COMPLETE_ROLE_BUDGET_CHANGED")
    return expected


def pid_start_ticks(pid):
    if type(pid) is not int or pid <= 1:
        raise ValueError("ACTUAL_MYSQL_HOST_PID_REQUIRED")
    return (Path("/proc") / str(pid) / "stat").read_text().rsplit(")", 1)[1].split()[19]


def identity(row, value):
    state = row.get("state", {})
    if (
        row.get("role") != "mysql"
        or not re.fullmatch(r"[0-9a-f]{64}", row.get("container_id", ""))
        or state.get("Running") is not True
        or row.get("restart_count") != 0
        or row.get("image_id")
        not in {value["image_ids"]["mysql"], value["config_ids"]["mysql"]}
        or not state.get("StartedAt")
    ):
        raise ValueError("EXACT_RUNNING_UNRESTARTED_MYSQL_REQUIRED")
    return {
        "container_id": row["container_id"],
        "image_id": row["image_id"],
        "host_pid": state["Pid"],
        "host_pid_start_ticks": pid_start_ticks(state["Pid"]),
        "container_started_at": state["StartedAt"],
        "project": value["project"],
        "database": value["database"],
    }


def mysql_argv(ident):
    # Only symbolic existing container ENV appears in argv. No credential is copied to the host.
    return [
        *DOCKER,
        "exec",
        "-i",
        ident["container_id"],
        "sh",
        "-c",
        'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" exec mysql --user=root --database="$MYSQL_DATABASE" '
        "--batch --raw --skip-column-names --unbuffered --skip-reconnect",
    ]


def clean_environment():
    return {
        k: v
        for k, v in os.environ.items()
        if not k.startswith(("DOCKER_", "COMPOSE_", "T44_", "MYSQL_", "RABBITMQ_"))
    }


def query_once(ident):
    process = subprocess.run(
        mysql_argv(ident),
        input=SQL.encode(),
        capture_output=True,
        timeout=10,
        check=False,
        env=clean_environment(),
    )
    if process.returncode or len(process.stdout) > 65536:
        raise ValueError("READ_ONLY_MYSQL_QUERY_FAILED")
    try:
        return json.loads(process.stdout)
    except (ValueError, UnicodeError):
        raise ValueError("ONE_MYSQL_NUMERIC_JSON_ROW_REQUIRED") from None


def numeric_sample(row, value):
    fields = (
        "max_connections",
        "connection_id",
        "Connections",
        "Threads_connected",
        "Max_used_connections",
        "Uptime",
        "Threads_running",
    )
    if (
        set(row) != {*fields, "server_uuid", "database"}
        or any(type(row.get(k)) is not int or row[k] < 0 for k in fields)
        or row["max_connections"] <= 0
        or row["connection_id"] <= 0
        or row["database"] != value["database"]
        or not re.fullmatch(r"[0-9a-f-]{36}", row["server_uuid"])
    ):
        raise ValueError("ACTUAL_MYSQL_DATABASE_AND_NUMERIC_COUNTERS_REQUIRED")
    return row


def measure(value, live):
    before = identity(live("mysql"), value)
    sample = numeric_sample(query_once(before), value)
    after = identity(live("mysql"), value)
    if before != after:
        raise ValueError("MYSQL_IDENTITY_CHANGED_DURING_QUERY")
    plan = checked_plan(value)
    if sample["max_connections"] < plan["required_max_connections"]:
        raise ValueError("ACTUAL_MYSQL_MAX_CONNECTIONS_BUDGET_INSUFFICIENT")
    return before, sample, plan


def exclusive_json(path, value):
    raw = (json.dumps(value, sort_keys=True, indent=2) + "\n").encode()
    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "wb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    return digest(raw)


def probe(phase, expected, value, live):
    private(phase / "receipts", True)
    actual, sample, plan = measure(value, live)
    row = {
        "kind": "actual-owned-mysql-budget-v4",
        "utc": stamp(),
        "binding_sha256": expected,
        "source_sha": value["source_sha"],
        "stop_utc": value["stop_utc"],
        "mysql_identity": actual,
        "actual_mysql_sample": sample,
        "connection_budget": plan,
        "actual_query_was_read_only": True,
        "probe_self_peak_connections": 1,
        "business_or_performance_verdict": None,
    }
    path = phase / "receipts" / ("mysql-budget-" + uuid4().hex + ".PUBLIC.json")
    return {
        "success": True,
        "budget_receipt": str(path),
        "budget_receipt_sha256": exclusive_json(path, row),
        "actual_max_connections": sample["max_connections"],
        "connection_budget": plan,
    }


def admit(phase, expected, value, live, receipt, receipt_sha256):
    private(phase / "receipts", True)
    if (
        not isinstance(receipt, Path)
        or receipt.parent != phase / "receipts"
        or not re.fullmatch(r"mysql-budget-[0-9a-f]{32}\.PUBLIC\.json", receipt.name)
        or not re.fullmatch(r"[0-9a-f]{64}", receipt_sha256 or "")
    ):
        raise ValueError("EXPLICIT_CURRENT_PHASE_BUDGET_RECEIPT_AND_SHA_REQUIRED")
    private(receipt)
    raw = receipt.read_bytes()
    if digest(raw) != receipt_sha256:
        raise ValueError("PINNED_ACTUAL_BUDGET_RECEIPT_CHANGED")
    saved = json.loads(raw)
    actual, sample, plan = measure(value, live)
    if (
        saved.get("kind") != "actual-owned-mysql-budget-v4"
        or saved.get("binding_sha256") != expected
        or saved.get("source_sha") != value["source_sha"]
        or saved.get("stop_utc") != value["stop_utc"]
        or saved.get("mysql_identity") != actual
        or saved.get("connection_budget") != plan
        or saved["actual_mysql_sample"]["server_uuid"] != sample["server_uuid"]
    ):
        raise ValueError("SAME_ACTUAL_MYSQL_AND_COMPLETE_ROLE_BUDGET_REQUIRED")
    return {
        "actual_max_connections": sample["max_connections"],
        "server_uuid": sample["server_uuid"],
        "budget_receipt_sha256": receipt_sha256,
        "connection_budget": plan,
    }


def verify_runtime_environment(value, live):
    result = []
    for role in ("api", "consumer", "scheduler"):
        observed = live(role)
        if (
            observed.get("absent")
            or observed.get("state", {}).get("Running") is not True
        ):
            result.append({"role": role, "actual_environment_observed": False})
            continue
        process = subprocess.run(
            [
                *DOCKER,
                "inspect",
                "--format",
                "{{json .Config.Env}}",
                observed["container_id"],
            ],
            capture_output=True,
            check=False,
            timeout=10,
            env=clean_environment(),
        )
        if process.returncode or len(process.stdout) > 1024 * 1024:
            raise ValueError("ACTUAL_ROLE_CAPACITY_ENV_NOT_OBSERVED")
        entries = json.loads(process.stdout)
        selected = {}
        for entry in entries:
            key, separator, val = entry.partition("=")
            if key in POOL_KEYS:
                if not separator or key in selected:
                    raise ValueError("ONE_EXPLICIT_ROLE_CAPACITY_ENV_REQUIRED")
                selected[key] = val
        expected = {}
        if role == "api" and value["phase"] == "p":
            expected = dict(
                zip(
                    POOL_KEYS,
                    map(
                        str,
                        (
                            value["v4_pool_plan"]["api_pool_size"],
                            value["v4_pool_plan"]["api_max_overflow"],
                        ),
                    ),
                    strict=True,
                )
            )
        if selected != expected:
            raise ValueError("API_ONLY_POOL_OVERRIDE_OR_OTHER_ROLE_DEFAULT_MISMATCH")
        again = live(role)
        # Health timestamps may change; process and image identity must not.
        if any(
            again.get(k) != observed.get(k)
            for k in ("container_id", "image_id", "restart_count")
        ) or any(
            again.get("state", {}).get(k) != observed.get("state", {}).get(k)
            for k in ("Pid", "StartedAt", "Running")
        ):
            raise ValueError("ROLE_IDENTITY_CHANGED_DURING_ENV_PROJECTION")
        result.append(
            {
                "role": role,
                "container_id": observed["container_id"],
                "actual_environment_observed": True,
                "capacity_env_only": selected,
                "effective_pool": {
                    "size": int(selected.get(POOL_KEYS[0], "5")),
                    "max_overflow": int(selected.get(POOL_KEYS[1], "10")),
                },
            }
        )
    return result


def observe(phase, expected, value, live, args):
    """One owned persistent read-only CLI connection; all other role counters remain unattributed."""
    until = expiry(args.until_utc)
    if (
        not time.time() + 5 <= until <= expiry(value["stop_utc"])
        or not 1 <= args.interval_seconds <= 60
    ):
        raise ValueError("BOUNDED_FUTURE_OBSERVER_WINDOW_REQUIRED")
    if not isinstance(args.output, Path) or args.output.parent != phase / "receipts":
        raise ValueError("NEW_PHASE_RECEIPTS_OBSERVER_OUTPUT_REQUIRED")
    with operation_lock(phase, expected, observer=True):
        with operation_lock(phase, expected):
            admission = admit(
                phase,
                expected,
                value,
                live,
                args.budget_receipt,
                args.budget_receipt_sha256,
            )
            actual = identity(live("mysql"), value)
        descriptor = os.open(
            args.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600
        )
        process = None
        output_hash = hashlib.sha256()
        with os.fdopen(descriptor, "wb") as output:

            def save(row):
                raw = (json.dumps(row, sort_keys=True) + "\n").encode()
                output.write(raw)
                output_hash.update(raw)
                output.flush()
                os.fsync(output.fileno())

            save(
                {
                    "kind": "mysql-observer-header-v4",
                    "utc": stamp(),
                    "mysql_identity": actual,
                    "source_sha": value["source_sha"],
                    "admission": admission,
                    "self_persistent_connections": 1,
                    "health_peak_budget": 4,
                    "one_serial_operation_peak_budget": 15,
                    "transient_budget_probe_peak": 1,
                    "global_counters_include_health_admin_and_this_observer": True,
                    "role_attribution": "not available from global counters",
                    "until_utc": args.until_utc,
                }
            )
            previous = None
            connection = None
            monotonic_stop = time.monotonic() + until - time.time()
            try:
                process = subprocess.Popen(
                    mysql_argv(actual),
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL,
                    env=clean_environment(),
                )
                with selectors.DefaultSelector() as selector:
                    selector.register(process.stdout, selectors.EVENT_READ)
                    while time.time() < until and time.monotonic() < monotonic_stop:
                        if identity(live("mysql"), value) != actual:
                            raise ValueError("OBSERVER_MYSQL_IDENTITY_CHANGED")
                        process.stdin.write(SQL.encode())
                        process.stdin.flush()
                        if not selector.select(
                            min(
                                5,
                                until - time.time(),
                                monotonic_stop - time.monotonic(),
                            )
                        ):
                            raise ValueError("OBSERVER_READ_TIMEOUT")
                        raw = process.stdout.readline(65537)
                        if len(raw) > 65536:
                            raise ValueError("OBSERVER_ROW_TOO_LARGE")
                        sample = numeric_sample(json.loads(raw), value)
                        if (
                            sample["server_uuid"] != admission["server_uuid"]
                            or sample["max_connections"]
                            < admission["connection_budget"]["required_max_connections"]
                            or identity(live("mysql"), value) != actual
                        ):
                            raise ValueError("OBSERVER_ACTUAL_SERVER_OR_BUDGET_CHANGED")
                        if (
                            connection is not None
                            and sample["connection_id"] != connection
                        ):
                            raise ValueError("OBSERVER_MUST_KEEP_ONE_CONNECTION")
                        connection = sample["connection_id"]
                        reset = previous is not None and (
                            sample["Connections"] < previous["Connections"]
                            or sample["Uptime"] < previous["Uptime"]
                        )
                        save(
                            {
                                "kind": "mysql-observer-sample-v4",
                                "utc": stamp(),
                                "sample": sample,
                                "connections_delta": None
                                if previous is None or reset
                                else sample["Connections"] - previous["Connections"],
                                "counter_reset": reset,
                                "observer_connection_id": connection,
                                "threads_connected_minus_this_observer_only": max(
                                    0, sample["Threads_connected"] - 1
                                ),
                            }
                        )
                        previous = sample
                        time.sleep(
                            max(
                                0,
                                min(
                                    args.interval_seconds,
                                    until - time.time(),
                                    monotonic_stop - time.monotonic(),
                                ),
                            )
                        )
            except (OSError, ValueError, KeyError, TypeError):
                save(
                    {
                        "kind": "mysql-observer-incomplete-v4",
                        "utc": stamp(),
                        "missing_or_identity_failure": True,
                    }
                )
                raise ValueError("READ_ONLY_OBSERVER_INCOMPLETE_PRESERVE_RAW") from None
            finally:
                if process is not None:
                    process.stdin.close()
                    try:
                        process.wait(timeout=3)
                    except subprocess.TimeoutExpired:
                        process.terminate()
                        try:
                            process.wait(timeout=3)
                        except subprocess.TimeoutExpired:
                            process.kill()
                            process.wait(timeout=3)
                    save(
                        {
                            "kind": "mysql-observer-final-v4",
                            "utc": stamp(),
                            "own_client_exit_code": process.returncode,
                            "server_connection_close_not_independently_proven": True,
                            "business_or_performance_verdict": None,
                        }
                    )
        return {
            "success": True,
            "observer_raw": str(args.output),
            "sha256": output_hash.hexdigest(),
            "business_or_performance_verdict": None,
        }
