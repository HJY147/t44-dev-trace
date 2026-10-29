"""Fresh exact functional-v7 schema and window; old functional profiles unchanged."""

import argparse
import ast
import hashlib
import json
import os
import stat
import subprocess
import types
from pathlib import Path

PROFILE_COMMIT = "4b27fde1974a6831a0d1e4d5df37fff41e3ede30"
PROFILE_SHA = "46dc107a59483ab39dde91891eae2f4705e77f49da8a014e944d2ac0fc70fa14"


def derive(files):
    result, receipts = {}, {}
    for name, raw in files.items():
        text, changes, patches = raw.decode(), [], []
        if name == "isolated.py":
            patches = [
                ("native-isolated-20261025", "native-functional-v7-20261025", 2),
                ("functional_20261025_", "functional_v7_20261025_", 1),
                ("datetime(2026, 10, 25, 8, 47, tzinfo=UTC)", "datetime(2026, 10, 25, 9, 24, tzinfo=UTC)", 1),
                ("datetime(2026, 10, 25, 8, 50, tzinfo=UTC)", "datetime(2026, 10, 25, 9, 25, tzinfo=UTC)", 1),
                (">= STOP - 120:", ">= datetime(2026, 10, 25, 9, 20, tzinfo=UTC).timestamp():", 1),
                (
                    '"planned_stop_utc": "2026-10-25T08:47:00Z",',
                    '"planned_stop_utc": "2026-10-25T09:24:00Z", "first_start_deadline_utc": "2026-10-25T09:20:00Z",',
                    1,
                ),
                ("2026-10-25T08:50:00Z", "2026-10-25T09:25:00Z", 1),
            ]
        elif name == "isolated-application.py":
            patches = [
                ("native-isolated-20261025", "native-functional-v7-20261025", 1),
                ("independent-functional-db/application-env.json", "functional-db-v7/application-env.json", 1),
                ("t44_i829_20261025", "t44_f817_20261025", 1),
                ("module.STOP - 30", "module.STOP - 90", 1),
                ("original08:47 broker guardian", "functional-v7 09:24 broker guardian", 1),
            ]
        elif name == "isolated-build.py":
            patches = [("2026-10-25T08:46:30Z", "2026-10-25T09:22:30Z", 1)]
        for old, new, count in patches:
            if text.count(old) != count:
                raise ValueError("EXACT_F7_PATCH_POSITION_CHANGED")
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
        ["git", "-C", str(repository), "show", PROFILE_COMMIT + ":deployment/native/profile-prepare.py"],
        check=True,
        capture_output=True,
        timeout=5,
    ).stdout
    if hashlib.sha256(raw).hexdigest() != PROFILE_SHA:
        raise ValueError("IMMUTABLE_PROFILE_HELPER_CHANGED")
    module = types.ModuleType("immutable_functional_profile")
    exec(compile(raw, "profile-prepare.py", "exec"), module.__dict__)
    output.mkdir(mode=0o700)
    module.materialize(repository, "functional", output / "functional-basis")
    files = {p.name: p.read_bytes() for p in (output / "functional-basis").glob("*.py")}
    new, receipts = derive(files)
    manifest = {
        "profile": "new-functional-v7",
        "profile_helper_commit": PROFILE_COMMIT,
        "profile_helper_sha256": PROFILE_SHA,
        "source_sha": "c8cea7e82805de5283ce67501769fa9a4efc1047",
        "api_workers": 4,
        "database_exact": "t44_f817_20261025",
        "first_start_deadline_utc": "2026-10-25T09:20:00Z",
        "app_stop_utc": "2026-10-25T09:22:30Z",
        "broker_stop_utc": "2026-10-25T09:24:00Z",
        "force_stop_utc": "2026-10-25T09:25:00Z",
        "old_namespace_modified": False,
        "generated_main_executed": False,
        "files": receipts,
    }
    for name, data in {
        **new,
        "derivation-functional-v7.json": (json.dumps(manifest, indent=2) + "\n").encode(),
    }.items():
        fd = os.open(output / name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
    return {
        "success": True,
        "output": str(output),
        "derivation_sha256": hashlib.sha256((output / "derivation-functional-v7.json").read_bytes()).hexdigest(),
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
        print(json.dumps({"success": False, "error": "NEW_FUNCTIONAL_V7_DERIVATION_REFUSED"}))
        raise SystemExit(1) from None
