"""Derive a new w7 namespace from the exact unexecuted performance-w8 tool profile."""

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
    counts = {
        "isolated-application.py": (4, 3, 3, 1),
        "isolated-build.py": (2, 1, 1, 1),
        "scheduler-control.py": (1, 1, 1, 0),
        "fault-control.py": (1, 1, 1, 0),
        "isolated.py": (0, 0, 0, 0),
    }
    for name, raw in files.items():
        text, changes = raw.decode(), []
        patches = [
            (old, old.replace(".json", "-w7.json").replace(".py", "-w7.py"), count)
            for old, count in zip(
                (
                    "application-binding.json",
                    "application-controller.py",
                    "application-environment.json",
                    "artifact-manifest.json",
                ),
                counts[name],
                strict=True,
            )
            if count
        ]
        if name == "isolated-application.py":
            patches += [
                ('"application-"', '"application-w7-"', 2),
                ('"source-archive-"', '"source-archive-w7-"', 1),
                ("final-scheduler.lock", "final-scheduler-w7.lock", 1),
                ("!= 8", "!= 7", 1),
                ("'8',", "'7',", 1),
                ("EIGHT_REAL_API_WORKERS_REQUIRED", "SEVEN_REAL_API_WORKERS_REQUIRED", 1),
            ]
        for old, new, count in patches:
            if text.count(old) != count:
                raise ValueError("EXACT_W7_PATCH_POSITION_CHANGED")
            text = text.replace(old, new)
            changes.append({"old": old, "new": new, "occurrences": count})
        data = text.encode()
        ast.parse(data)
        result[name] = data
        receipts[name] = {
            "old_w8_sha256": hashlib.sha256(raw).hexdigest(),
            "new_w7_sha256": hashlib.sha256(data).hexdigest(),
            "allowed_changes": changes,
        }
    return result, receipts


def materialize(repository, output):
    raw = subprocess.run(
        ["git", "-C", str(repository), "show", PROFILE_COMMIT + ":deployment/native/profile-prepare.py"],
        check=True,
        capture_output=True,
        timeout=5,
    ).stdout
    if hashlib.sha256(raw).hexdigest() != PROFILE_SHA:
        raise ValueError("PROFILE_HELPER_CHANGED")
    module = types.ModuleType("immutable_profile_helper")
    exec(compile(raw, "profile-prepare.py", "exec"), module.__dict__)
    originals = {
        name: subprocess.run(
            ["git", "-C", str(repository), "show", module.BASE + ":deployment/native/" + name],
            check=True,
            capture_output=True,
            timeout=5,
        ).stdout
        for name in module.PINS
    }
    old, manifest = module.render("performance", originals)
    new, receipts = derive(old)
    parent = output.parent
    info = parent.lstat()
    if (
        not output.is_absolute()
        or parent.resolve() != parent
        or not stat.S_ISDIR(info.st_mode)
        or info.st_uid != os.getuid()
        or stat.S_IMODE(info.st_mode) != 0o700
    ):
        raise ValueError("PRIVATE_NEW_OUTPUT_REQUIRED")
    manifest = {
        "profile_helper_commit": PROFILE_COMMIT,
        "profile_helper_sha256": PROFILE_SHA,
        "source_sha": module.SOURCE,
        "old_profile": manifest,
        "configuration_change": {"api_workers": {"old": 8, "new": 7}},
        "namespace": "w7;old w8 paths/bytes retained",
        "files": receipts,
        "old_runtime_modified": False,
        "generated_main_executed": False,
    }
    output.mkdir(mode=0o700)
    for name, data in {**new, "derivation-w7.json": (json.dumps(manifest, indent=2) + "\n").encode()}.items():
        fd = os.open(output / name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
    return {
        "success": True,
        "output": str(output),
        "derivation_sha256": hashlib.sha256((output / "derivation-w7.json").read_bytes()).hexdigest(),
        "api_workers": 7,
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
        print(json.dumps({"success": False, "error": "EXPLICIT_W7_DERIVATION_REFUSED"}))
        raise SystemExit(1) from None
