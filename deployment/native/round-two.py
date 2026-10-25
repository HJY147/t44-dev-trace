"""New performance round2 only; preserve every previous runtime and deadline."""

import argparse
import ast
import hashlib
import json
import os
import stat
import subprocess
import types
from pathlib import Path

W7_COMMIT = "3c4ed19bad72907c24d3dcab855128a83faf286a"
W7_SHA = "545bb451cab610db3b41f14b90424427a56c5f13a6ba5bc1bab863d89485121b"


def derive(files):
    result, receipts = {}, {}
    for name, raw in files.items():
        text, changes = raw.decode(), []
        patches = []
        if name == "isolated.py":
            patches = [
                ("native-performance-20261025", "native-performance-round2-20261025", 2),
                ("performance_20261025_", "performance_round2_20261025_", 1),
                (
                    "STOP = datetime(2026, 10, 25, 8, 47, tzinfo=UTC).timestamp()",
                    "STOP = datetime(2026, 10, 25, 9, 12, tzinfo=UTC).timestamp()",
                    1,
                ),
                (
                    "HARD_STOP = datetime(2026, 10, 25, 8, 50, tzinfo=UTC).timestamp()",
                    "HARD_STOP = datetime(2026, 10, 25, 9, 15, tzinfo=UTC).timestamp()",
                    1,
                ),
                (">= STOP - 120:", ">= datetime(2026, 10, 25, 9, 0, tzinfo=UTC).timestamp():", 1),
                (
                    '"planned_stop_utc": "2026-10-25T08:47:00Z",',
                    '"planned_stop_utc": "2026-10-25T09:12:00Z", "first_start_deadline_utc": "2026-10-25T09:00:00Z",',
                    1,
                ),
                ("2026-10-25T08:50:00Z", "2026-10-25T09:15:00Z", 1),
            ]
        elif name == "isolated-application.py":
            patches = [
                ("native-performance-20261025", "native-performance-round2-20261025", 1),
                ("module.STOP - 30", "module.STOP - 90", 1),
                ("original08:47 broker guardian", "round2 09:12 broker guardian", 1),
            ]
        elif name == "isolated-build.py":
            patches = [("2026-10-25T08:46:30Z", "2026-10-25T09:10:30Z", 1)]
        for old, new, count in patches:
            if text.count(old) != count:
                raise ValueError("EXACT_ROUND2_PATCH_POSITION_CHANGED")
            text = text.replace(old, new)
            changes.append({"old": old, "new": new, "occurrences": count})
        data = text.encode()
        ast.parse(data)
        result[name] = data
        receipts[name] = {
            "old_w7_sha256": hashlib.sha256(raw).hexdigest(),
            "new_round2_sha256": hashlib.sha256(data).hexdigest(),
            "allowed_changes": changes,
        }
    return result, receipts


def materialize(repository, output):
    info = output.parent.lstat()
    if (
        not output.is_absolute()
        or output.parent.resolve() != output.parent
        or not stat.S_ISDIR(info.st_mode)
        or info.st_uid != os.getuid()
        or stat.S_IMODE(info.st_mode) != 0o700
    ):
        raise ValueError("PRIVATE_NEW_OUTPUT_REQUIRED")
    raw = subprocess.run(
        ["git", "-C", str(repository), "show", W7_COMMIT + ":deployment/native/worker-seven.py"],
        check=True,
        capture_output=True,
        timeout=5,
    ).stdout
    if hashlib.sha256(raw).hexdigest() != W7_SHA:
        raise ValueError("IMMUTABLE_W7_HELPER_CHANGED")
    module = types.ModuleType("immutable_w7_helper")
    exec(compile(raw, "worker-seven.py", "exec"), module.__dict__)
    output.mkdir(mode=0o700)
    module.materialize(repository, output / "w7-basis")
    files = {p.name: p.read_bytes() for p in (output / "w7-basis").glob("*.py")}
    new, receipts = derive(files)
    manifest = {
        "w7_helper_commit": W7_COMMIT,
        "w7_helper_sha256": W7_SHA,
        "round": "performance-round2",
        "source_sha": "c8cea7e82805de5283ce67501769fa9a4efc1047",
        "api_workers": 7,
        "first_start_deadline_utc": "2026-10-25T09:00:00Z",
        "application_stop_utc": "2026-10-25T09:10:30Z",
        "broker_stop_utc": "2026-10-25T09:12:00Z",
        "force_stop_utc": "2026-10-25T09:15:00Z",
        "old_runtime_or_grants_modified": False,
        "generated_main_executed": False,
        "files": receipts,
    }
    for name, data in {**new, "derivation-round2.json": (json.dumps(manifest, indent=2) + "\n").encode()}.items():
        fd = os.open(output / name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
    return {
        "success": True,
        "output": str(output),
        "derivation_sha256": hashlib.sha256((output / "derivation-round2.json").read_bytes()).hexdigest(),
        "executed": False,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    os.umask(0o077)
    try:
        print(json.dumps(materialize(args.repository, args.output)))
    except (OSError, ValueError, subprocess.SubprocessError):
        print(json.dumps({"success": False, "error": "NEW_ROUND2_DERIVATION_REFUSED"}))
        raise SystemExit(1) from None
