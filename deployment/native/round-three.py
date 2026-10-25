"""New round3 exact schema/time namespace; never alter round2 runtime or grant."""

import argparse
import ast
import hashlib
import json
import os
import stat
import subprocess
import types
from pathlib import Path

R2_COMMIT = "9b578909e9f39f2624f02259b2b999c4ca7b002a"
R2_SHA = "c00741fdd2ba112c311baaa14eadd7bf65d13e83b71eb0e3d82d6ce56ca413e8"
METRICS_COMMIT = "773bfd7d0d240a646ed8b739f6d86331d9c4fdb0"
METRICS_SHA = "ba94524cbda4c12d151dfde552513e5d903e41c2141ddd28b9e08d867ae61b8f"


def derive(files):
    result, receipts = {}, {}
    for name, raw in files.items():
        text, changes, patches = raw.decode(), [], []
        if name == "isolated.py":
            patches = [
                ("native-performance-round2-20261025", "native-performance-round3-20261025", 2),
                ("performance_round2_20261025_", "performance_round3_20261025_", 1),
                ("datetime(2026, 10, 25, 9, 12, tzinfo=UTC)", "datetime(2026, 10, 25, 9, 42, tzinfo=UTC)", 1),
                ("datetime(2026, 10, 25, 9, 15, tzinfo=UTC)", "datetime(2026, 10, 25, 9, 45, tzinfo=UTC)", 1),
                ("datetime(2026, 10, 25, 9, 0, tzinfo=UTC)", "datetime(2026, 10, 25, 9, 20, tzinfo=UTC)", 1),
                ("2026-10-25T09:12:00Z", "2026-10-25T09:42:00Z", 1),
                ("2026-10-25T09:15:00Z", "2026-10-25T09:45:00Z", 1),
                ("2026-10-25T09:00:00Z", "2026-10-25T09:20:00Z", 1),
            ]
        elif name == "isolated-application.py":
            patches = [
                ("native-performance-round2-20261025", "native-performance-round3-20261025", 1),
                ("performance-db/application-env.json", "performance-db-round3/application-env.json", 1),
                ("t44_p829_20261025", "t44_p829c_20261025", 1),
                ("round2 09:12 broker guardian", "round3 09:42 broker guardian", 1),
            ]
        elif name == "isolated-build.py":
            patches = [("2026-10-25T09:10:30Z", "2026-10-25T09:40:30Z", 1)]
        elif name == "interval-metrics.py":
            if hashlib.sha256(raw).hexdigest() != METRICS_SHA:
                raise ValueError("IMMUTABLE_METRICS_TEMPLATE_CHANGED")
            patches = [
                ("datetime(2026, 10, 25, 9, 9, tzinfo=UTC)", "datetime(2026, 10, 25, 9, 39, tzinfo=UTC)", 1),
                ("09:09UTC deadline", "09:39UTC deadline", 1),
                ("2026-10-25T09:09:00Z", "2026-10-25T09:39:00Z", 1),
            ]
        for old, new, count in patches:
            if text.count(old) != count:
                raise ValueError("EXACT_ROUND3_PATCH_POSITION_CHANGED")
            text = text.replace(old, new)
            changes.append({"old": old, "new": new, "occurrences": count})
        data = text.encode()
        ast.parse(data)
        result[name] = data
        receipts[name] = {
            "old_sha256": hashlib.sha256(raw).hexdigest(),
            "new_sha256": hashlib.sha256(data).hexdigest(),
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
        ["git", "-C", str(repository), "show", R2_COMMIT + ":deployment/native/round-two.py"],
        check=True,
        capture_output=True,
        timeout=5,
    ).stdout
    if hashlib.sha256(raw).hexdigest() != R2_SHA:
        raise ValueError("IMMUTABLE_ROUND2_HELPER_CHANGED")
    module = types.ModuleType("immutable_round2_helper")
    exec(compile(raw, "round-two.py", "exec"), module.__dict__)
    output.mkdir(mode=0o700)
    module.materialize(repository, output / "round2-basis")
    files = {p.name: p.read_bytes() for p in (output / "round2-basis").glob("*.py")}
    files["interval-metrics.py"] = subprocess.run(
        ["git", "-C", str(repository), "show", METRICS_COMMIT + ":deployment/native/interval-metrics.py"],
        check=True,
        capture_output=True,
        timeout=5,
    ).stdout
    new, receipts = derive(files)
    manifest = {
        "round": "new-performance-round3",
        "source_sha": "c8cea7e82805de5283ce67501769fa9a4efc1047",
        "api_workers": 7,
        "database_exact": "t44_p829c_20261025",
        "round2_helper_commit": R2_COMMIT,
        "round2_helper_sha256": R2_SHA,
        "metrics_template_commit": METRICS_COMMIT,
        "metrics_template_sha256": METRICS_SHA,
        "first_start_deadline_utc": "2026-10-25T09:20:00Z",
        "application_stop_utc": "2026-10-25T09:40:30Z",
        "broker_stop_utc": "2026-10-25T09:42:00Z",
        "force_stop_utc": "2026-10-25T09:45:00Z",
        "interval_sampler_stop_utc": "2026-10-25T09:39:00Z",
        "old_round_files_grants_changed": False,
        "files": receipts,
        "generated_main_executed": False,
    }
    for name, data in {**new, "derivation-round3.json": (json.dumps(manifest, indent=2) + "\n").encode()}.items():
        descriptor = os.open(output / name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
    return {
        "success": True,
        "output": str(output),
        "derivation_sha256": hashlib.sha256((output / "derivation-round3.json").read_bytes()).hexdigest(),
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
        print(json.dumps({"success": False, "error": "NEW_ROUND3_DERIVATION_REFUSED"}))
        raise SystemExit(1) from None
