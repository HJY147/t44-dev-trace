"""Only explicit functional/performance profiles; materialize immutable native tool copies."""

import argparse
import ast
import hashlib
import json
import os
import stat
import subprocess
from pathlib import Path

BASE = "53d84323370f09d4f7113534279e23ac942ab0db"
SOURCE = "c8cea7e82805de5283ce67501769fa9a4efc1047"
PINS = {
    "isolated.py": "511b2ecdb6c3d8a8d9d2691cb6aebcc9f3e57c30383ed62e018f2c99a1aa7f8e",
    "isolated-application.py": "5309d7d6c3aacf743095739215ed944e3e98174d5fdcbbd025126387d47548f3",
    "isolated-build.py": "cffcbf605ba1eda41d2cf007c75e4b62fa6af0703963bcbc44393cb471660e77",
    "scheduler-control.py": "508cf4df0541189b4aae06cce0d1dab3d35cb6c334cedc31d416e6ea5cf40abb",
    "fault-control.py": "4534b5dd4637c28bb243809c8e2fc7ed394b4415c56a66d66ab39ad208b984b9",
}
PROFILES = {
    "functional": {
        "directory": "native-isolated-20261025",
        "env": "independent-functional-db",
        "database": "t44_i829_20261025",
        "api": 18096,
        "amqp": 25696,
        "epmd": 24396,
        "distribution": 35696,
        "cli_first": 45696,
        "cli_last": 45705,
        "workers": 4,
    },
    "performance": {
        "directory": "native-performance-20261025",
        "env": "performance-db",
        "database": "t44_p829_20261025",
        "api": 18097,
        "amqp": 25697,
        "epmd": 24397,
        "distribution": 35697,
        "cli_first": 45716,
        "cli_last": 45725,
        "workers": 8,
    },
}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def render(profile, originals):
    if profile not in PROFILES or set(originals) != set(PINS):
        raise ValueError("EXACT_PROFILE_AND_TEMPLATE_SET_REQUIRED")
    config = PROFILES[profile]
    files, receipts = {}, {}
    for name, raw in originals.items():
        if digest(raw) != PINS[name]:
            raise ValueError("TEMPLATE_HASH_CHANGED")
        changes = []
        patches = []
        if name == "isolated.py":
            patches = [
                ("ade5e4c1998b4c2f014afde8c011645c6c5a7412", SOURCE, 1),
                ("native-isolated-20261025", config["directory"], 2),
                ("18096", str(config["api"]), 1),
                ("25696", str(config["amqp"]), 2),
                ("24396", str(config["epmd"]), 2),
                ("35696", str(config["distribution"]), 2),
                ("45696", str(config["cli_first"]), 2),
                ("45705", str(config["cli_last"]), 2),
                ("isolated_20261025_", profile + "_20261025_", 1),
            ]
        elif name == "isolated-application.py":
            patches = [
                ("native-isolated-20261025", config["directory"], 1),
                ("independent-functional-db", config["env"], 1),
                ("t44_i829_20261025", config["database"], 1),
                ("!= 4", "!= " + str(config["workers"]), 1),
                ('"4",', repr(str(config["workers"])) + ",", 1),
                (
                    "FOUR_REAL_API_WORKERS_REQUIRED",
                    "EIGHT_REAL_API_WORKERS_REQUIRED" if config["workers"] == 8 else "FOUR_REAL_API_WORKERS_REQUIRED",
                    1,
                ),
            ]
        text = raw.decode()
        for old, new, expected in patches:
            count = text.count(old)
            if count != expected:
                raise ValueError("ALLOWED_PATCH_POSITION_CHANGED")
            text = text.replace(old, new)
            changes.append({"old": old, "new": new, "occurrences": count})
        data = text.encode()
        ast.parse(data)
        files[name] = data
        receipts[name] = {"old_sha256": PINS[name], "new_sha256": digest(data), "allowed_changes": changes}
    return files, {
        "template_commit": BASE,
        "profile": profile,
        "source_sha": SOURCE,
        "config": config,
        "files": receipts,
        "old_files_changed": False,
        "generated_files_executed": False,
    }


def materialize(repository, profile, output):
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
    originals = {
        name: subprocess.run(
            ["git", "-C", str(repository), "show", BASE + ":deployment/native/" + name],
            check=True,
            capture_output=True,
            timeout=5,
        ).stdout
        for name in PINS
    }
    files, manifest = render(profile, originals)
    output.mkdir(mode=0o700)
    for name, data in {**files, "derivation.json": (json.dumps(manifest, indent=2) + "\n").encode()}.items():
        fd = os.open(output / name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
    return {
        "success": True,
        "profile": profile,
        "output": str(output),
        "derivation_sha256": digest((output / "derivation.json").read_bytes()),
        "executed": False,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", choices=tuple(PROFILES), required=True)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    os.umask(0o077)
    try:
        print(json.dumps(materialize(args.repository, args.profile, args.output)))
    except (OSError, ValueError, subprocess.SubprocessError):
        print(json.dumps({"success": False, "error": "EXPLICIT_NATIVE_PROFILE_REFUSED"}))
        raise SystemExit(1) from None
