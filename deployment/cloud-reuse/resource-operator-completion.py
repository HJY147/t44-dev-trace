"""Complete one observed resource readiness refusal; never start, restart or alter frozen code."""

import argparse
import hashlib
import json
import os
import re
import stat
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

HELPER_SHA = "e5b0324e1576f901cbacb1ba9b973096c6b575318cc9f336a6f7183ce94ca115"
SOURCE = "a12e9e70b963bacafda3242bb6d82e53ee912ff1"
REASON = "EXACT_OWNED_SYSTEMD_PROCESS_REQUIRED"
SCOPES = {
    Path("/root/t44-r9/resource-r28p16-02"): (
        "app-owned-resource-stream-v1",
        "t44-resource-",
    ),
    Path("/root/t44-r9/resource-mirror-r28p16-02"): (
        "load-append-resource-mirror-v1",
        "t44-mirror-",
    ),
}
APP = Path("/root/t44-r9/resource-r28p16-02")
APP_BINDING = "f76269ff54bd74bc762e98a2d1a41273b659f50c48eeaa7888bbcd7318988e97"
APP_FAILURE = "failure-23c53697a08f4e84aedef94c3bc953e0.json"
UNIT_ROOT = Path("/etc/systemd/system")
PROC = Path("/proc")
CGROUP = Path("/sys/fs/cgroup")


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read_owned(path, mode=0o600, maximum=262144):
    if path.resolve() != path:
        raise ValueError("CANONICAL_NO_SYMLINK_INPUT_REQUIRED")
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(fd, "rb") as stream:
        info = os.fstat(stream.fileno())
        if (
            not stat.S_ISREG(info.st_mode)
            or info.st_uid != os.geteuid()
            or stat.S_IMODE(info.st_mode) != mode
        ):
            raise ValueError("OWNED_REGULAR_FROZEN_INPUT_REQUIRED")
        raw = stream.read(maximum + 1)
        if len(raw) > maximum:
            raise ValueError("BOUNDED_INPUT_REQUIRED")
        return raw


def absent_receipt(path):
    try:
        path.lstat()
    except FileNotFoundError:
        return
    raise ValueError("START_RESULT_ALREADY_PRESENT_NO_OVERWRITE")


def preflight(args):
    directory = args.directory
    if directory not in SCOPES or directory.resolve() != directory:
        raise ValueError("EXACT_TWO_NEW_RESOURCE_DIRECTORIES_ONLY")
    info = directory.stat()
    if info.st_uid != os.geteuid() or stat.S_IMODE(info.st_mode) != 0o700:
        raise ValueError("OWNED_PRIVATE_RESOURCE_DIRECTORY_REQUIRED")
    if not re.fullmatch(r"[0-9a-f]{64}", args.binding_sha256):
        raise ValueError("EXPLICIT_BINDING_SHA_REQUIRED")
    if args.failure.parent != directory or not re.fullmatch(
        r"failure-[0-9a-f]{32}\.json", args.failure.name
    ):
        raise ValueError("EXACT_LOCAL_ORIGINAL_FAILURE_REQUIRED")
    if directory == APP and (
        args.binding_sha256 != APP_BINDING or args.failure.name != APP_FAILURE
    ):
        raise ValueError("EXACT_ROOT_APPROVED_APP_REFUSAL_REQUIRED")
    absent_receipt(directory / "start-result.json")
    snapshots = {}

    def collect(path, mode=0o600):
        raw = read_owned(path, mode)
        snapshots[path] = (mode, sha(raw))
        return raw

    binding_raw = collect(directory / "binding.json")
    if sha(binding_raw) != args.binding_sha256:
        raise ValueError("FROZEN_BINDING_CHANGED")
    value = json.loads(binding_raw)
    kind, prefix = SCOPES[directory]
    if value["kind"] != kind or not re.fullmatch(
        re.escape(prefix) + r"[a-z][a-z0-9]{5,15}\.service", value["unit"]
    ):
        raise ValueError("EXACT_RESOURCE_KIND_AND_UNIT_REQUIRED")
    if directory == APP and value["source_sha"] != SOURCE:
        raise ValueError("EXACT_SOURCE_REQUIRED")
    until = datetime.fromisoformat(
        value["serve_until"].replace("Z", "+00:00")
    ).timestamp()
    if (
        not time.time() + 10
        < until
        <= datetime.fromisoformat("2026-10-28T10:30:00+00:00").timestamp()
    ):
        raise ValueError("STILL_LIVE_FROZEN_WINDOW_REQUIRED")
    expected_files = {
        "controller.py",
        "nonce" if directory == APP else "private-handoff.json",
    }
    if (
        set(value["file_hashes"]) != expected_files
        or value["file_hashes"]["controller.py"] != HELPER_SHA
    ):
        raise ValueError("EXACT_FROZEN_RESOURCE_FILE_SET_REQUIRED")
    for name, expected in value["file_hashes"].items():
        if sha(collect(directory / name)) != expected:
            raise ValueError("FROZEN_RESOURCE_OBJECT_CHANGED")
    refusal = json.loads(collect(args.failure))
    if (
        refusal.get("error_class") != "ValueError"
        or refusal.get("reason") != REASON
        or refusal.get("partial_state_preserved") is not True
    ):
        raise ValueError("ONLY_EXACT_OBSERVED_READY_REFUSAL_ALLOWED")
    plan = json.loads(collect(directory / "start-plan.json"))
    action = "daemon-app" if directory == APP else "daemon-mirror"
    expected_argv = [
        "/usr/bin/python3",
        str(directory / "controller.py"),
        action,
        "--directory",
        str(directory),
        "--binding-sha256",
        args.binding_sha256,
    ]
    unit_path = UNIT_ROOT / value["unit"]
    if (
        plan["binding_sha256"] != args.binding_sha256
        or plan["unit"] != value["unit"]
        or plan["unit_path"] != str(unit_path)
        or plan["argv"] != expected_argv
    ):
        raise ValueError("EXACT_FROZEN_START_PLAN_AND_ARGV_REQUIRED")
    unit_raw = collect(unit_path, 0o644)
    if sha(unit_raw) != plan["unit_sha256"]:
        raise ValueError("FROZEN_SYSTEMD_UNIT_CHANGED")
    unit_text = unit_raw.decode()
    match = re.search(r"\nRuntimeMaxSec=([1-9][0-9]{0,5})\n", unit_text)
    if not match or int(match[1]) > 43200:
        raise ValueError("BOUNDED_ORIGINAL_SYSTEMD_RUNTIME_REQUIRED")
    expected_text = (
        "[Unit]\nDescription=T44 bounded private resource observer\n[Service]\nType=simple\nUser=root\nUMask=0077\nNoNewPrivileges=true\nProtectSystem=strict\nReadWritePaths="
        + str(directory)
        + "\nWorkingDirectory="
        + str(directory)
        + "\nEnvironment=PYTHONDONTWRITEBYTECODE=1\nRestart=no\nTimeoutStopSec=15\nKillMode=control-group\nRuntimeMaxSec="
        + match[1]
        + "\nExecStart="
        + " ".join(expected_argv)
        + "\n"
    )
    if unit_text != expected_text:
        raise ValueError("EXACT_FROZEN_SYSTEMD_PROTECTIONS_REQUIRED")
    return value, expected_argv, snapshots


def run(argv, timeout):
    return subprocess.run(argv, capture_output=True, check=True, timeout=timeout).stdout


def proc_ticks(raw, pid):
    head, tail = raw.decode().rsplit(")", 1)
    fields = tail.split()
    if int(head.split("(", 1)[0]) != pid or len(fields) < 20 or fields[0] in {"Z", "X"}:
        raise ValueError("LIVE_EXACT_PROC_PID_REQUIRED")
    return int(fields[19])


def probe(unit, deadline):
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise ValueError("FIVE_SECOND_READY_WAIT_EXPIRED")
    raw = run(
        [
            "systemctl",
            "show",
            unit,
            "--property=MainPID",
            "--property=ActiveState",
            "--property=SubState",
            "--property=ControlGroup",
        ],
        remaining,
    )
    items = [line.split("=", 1) for line in raw.decode().splitlines() if line]
    values = dict(items)
    if len(items) != 4 or set(values) != {
        "MainPID",
        "ActiveState",
        "SubState",
        "ControlGroup",
    }:
        raise ValueError("COMPLETE_SYSTEMD_IDENTITY_REQUIRED")
    pid = int(values["MainPID"])
    group = "/system.slice/" + unit
    if (
        pid <= 0
        or values["ActiveState"] != "active"
        or values["SubState"] != "running"
        or values["ControlGroup"] != group
    ):
        raise ValueError("EXACT_RUNNING_UNIT_CGROUP_REQUIRED")
    process = PROC / str(pid)
    before = proc_ticks((process / "stat").read_bytes(), pid)
    status = (process / "status").read_text().splitlines()
    uids = [line.split()[1:] for line in status if line.startswith("Uid:")]
    if process.stat().st_uid != 0 or uids != [["0", "0", "0", "0"]]:
        raise ValueError("ROOT_REAL_EFFECTIVE_SAVED_FS_UID_REQUIRED")
    actual = (process / "cmdline").read_bytes()
    if (process / "cgroup").read_text().splitlines() != ["0::" + group]:
        raise ValueError("PROC_EXACT_SYSTEMD_CGROUP_REQUIRED")
    members = (CGROUP / group.lstrip("/") / "cgroup.procs").read_text().split()
    after = proc_ticks((process / "stat").read_bytes(), pid)
    if str(pid) not in members or before != after:
        raise ValueError("PID_STARTTICK_OR_CGROUP_CHANGED")
    return {
        "pid": pid,
        "start_ticks": before,
        "cmdline": actual,
        "unit": unit,
        "cgroup": group,
    }


def stable_identity(value, anchor):
    if (
        value["pid"] != anchor["pid"]
        or value["start_ticks"] != anchor["start_ticks"]
        or value["cgroup"] != anchor["cgroup"]
    ):
        raise ValueError("PID_STARTTICK_OR_CGROUP_SWITCH_REFUSED")


def complete(args):
    value, expected, snapshots = preflight(args)
    deadline = time.monotonic() + 5
    anchor = probe(value["unit"], deadline)
    current = anchor
    while current["cmdline"].rstrip(b"\0").split(b"\0") != [
        s.encode() for s in expected
    ]:
        if time.monotonic() >= deadline:
            raise ValueError("FIVE_SECOND_ARGV_MATCH_EXPIRED")
        time.sleep(min(0.05, max(0, deadline - time.monotonic())))
        current = probe(value["unit"], deadline)
        stable_identity(current, anchor)
    time.sleep(min(0.05, max(0, deadline - time.monotonic())))
    final = probe(value["unit"], deadline)
    stable_identity(final, anchor)
    if final["cmdline"] != current["cmdline"]:
        raise ValueError("ARGV_NOT_STABLE_NO_COMPLETION")
    for path, (mode, expected_sha) in snapshots.items():
        if sha(read_owned(path, mode)) != expected_sha:
            raise ValueError("INPUT_CHANGED_DURING_COMPLETION")
    receipt_path = args.directory / "start-result.json"
    absent_receipt(receipt_path)
    result = {
        "utc": datetime.now(timezone.utc).isoformat(),  # noqa: UP017 -- Linux Python 3.10.
        "pid": final["pid"],
        "start_ticks": final["start_ticks"],
        "cmdline_sha256": sha(final["cmdline"]),
        "late": True,
        "operator_completion": True,
        "not_original_start_success": True,
        "original_refusal": args.failure.name,
        "original_refusal_sha256": snapshots[args.failure][1],
        "binding_sha256": args.binding_sha256,
        "controller_sha256": HELPER_SHA,
        "unit": final["unit"],
        "cgroup": final["cgroup"],
        "proof": "two stable root UID argv MainPID starttick cgroup observations; frozen inputs rechecked",
    }
    fd = os.open(
        receipt_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600
    )
    with os.fdopen(fd, "w") as stream:
        json.dump(result, stream, sort_keys=True)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    status = run(
        [
            "/usr/bin/python3",
            str(args.directory / "controller.py"),
            "status",
            "--directory",
            str(args.directory),
            "--binding-sha256",
            args.binding_sha256,
        ],
        10,
    )
    observed = json.loads(status)
    if (
        observed.get("action") != "status"
        or observed.get("unit") != value["unit"]
        or observed.get("observed_before_pid") != final["pid"]
        or observed.get("observed_after_pid") != final["pid"]
    ):
        raise ValueError("LATE_RECEIPT_WRITTEN_BUT_ORIGINAL_STATUS_NOT_PROVEN")
    after = probe(value["unit"], time.monotonic() + 2)
    stable_identity(after, final)
    if after["cmdline"] != final["cmdline"]:
        raise ValueError("LATE_RECEIPT_WRITTEN_BUT_PROCESS_CHANGED_AFTER_STATUS")
    return {
        "operator_completed": True,
        "late": True,
        "not_original_start_success": True,
        "receipt_path": str(receipt_path),
        "receipt_sha256": sha(read_owned(receipt_path)),
        "pid": final["pid"],
        "start_ticks": final["start_ticks"],
        "original_status_rechecked": True,
        "original_status_stdout_sha256": sha(status),
        "frozen_code_or_binding_changed": False,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--binding-sha256", required=True)
    parser.add_argument("--failure", type=Path, required=True)
    args = parser.parse_args()
    if os.geteuid() != 0:
        raise SystemExit("ROOT_OPERATOR_ONLY")
    os.umask(0o077)
    try:
        print(json.dumps(complete(args)))
    except (
        OSError,
        ValueError,
        KeyError,
        TypeError,
        subprocess.SubprocessError,
    ) as error:
        print(
            json.dumps(
                {
                    "operator_completed": False,
                    "error_class": type(error).__name__,
                    "reason": str(error),
                    "original_refusal_and_frozen_code_preserved": True,
                }
            )
        )
        raise SystemExit(1) from None
