"""Exact source935 campaign in fresh namespaces; no change to previous leases."""

import argparse
import ast
import hashlib
import json
import os
import stat
import subprocess
import types
from pathlib import Path

BASIS_COMMIT = "adc5197fa149d931a04d9eb210a6875ad8929cee"
BASIS_SHA = "f54c5ce1ca296a1797132b2e62ad1be2f0f81a58d9c8946cffa9965ce7c5f725"
SOURCE = "935ab5b93bea788672c2b4a088c79cfeed848954"
OLD_SOURCE = "c8cea7e82805de5283ce67501769fa9a4efc1047"
PROFILES = {
    "functional": {
        "database_old": "t44_f817_20261025",
        "database": "t44_f816_20261025",
        "env_old": "functional-db-v7",
        "env": "functional-db-round8",
        "api_old": 18096,
        "api": 18098,
        "amqp_old": 25696,
        "amqp": 25698,
        "epmd_old": 24396,
        "epmd": 24398,
        "distribution_old": 35696,
        "distribution": 35698,
        "cli_first_old": 45696,
        "cli_first": 45736,
        "cli_last_old": 45705,
        "cli_last": 45745,
        "workers": 4,
        "stop_minute": 22,
        "force_minute": 25,
        "app": "11:20:30",
    },
    "performance": {
        "database_old": "t44_p829c_20261025",
        "database": "t44_p816_20261025",
        "env_old": "performance-db-round3",
        "env": "performance-db-round8",
        "api_old": 18097,
        "api": 18099,
        "amqp_old": 25697,
        "amqp": 25699,
        "epmd_old": 24397,
        "epmd": 24399,
        "distribution_old": 35697,
        "distribution": 35699,
        "cli_first_old": 45716,
        "cli_first": 45756,
        "cli_last_old": 45725,
        "cli_last": 45765,
        "workers": 7,
        "stop_minute": 32,
        "force_minute": 35,
        "app": "11:30:30",
    },
}


def derive(profile, files):
    if profile not in PROFILES:
        raise ValueError("EXACT_ROUND8_PROFILE_REQUIRED")
    config = PROFILES[profile]
    expected = {
        "isolated.py",
        "isolated-application.py",
        "isolated-build.py",
        "scheduler-control.py",
        "fault-control.py",
    }
    if profile == "performance":
        expected.add("interval-metrics.py")
    if set(files) != expected:
        raise ValueError("EXACT_ROUND8_TEMPLATE_SET_REQUIRED")
    result, receipts = {}, {}
    for name, raw in files.items():
        text, patches, changes = raw.decode(), [], []
        if name == "isolated.py":
            patches = [
                (OLD_SOURCE, SOURCE, 1),
                (
                    "native-" + profile + "-campaign-20261025",
                    "native-" + profile + "-campaign8-20261025",
                    2,
                ),
                (profile + "_campaign_20261025_", profile + "_campaign8_20261025_", 1),
                (
                    "datetime(2026, 10, 25, 10, 0, tzinfo=UTC)",
                    "datetime(2026, 10, 25, 10, 50, tzinfo=UTC)",
                    1,
                ),
                ("2026-10-25T10:00:00Z", "2026-10-25T10:50:00Z", 1),
            ]
            for key, count in [
                ("api", 1),
                ("amqp", 2),
                ("epmd", 2),
                ("distribution", 2),
                ("cli_first", 2),
                ("cli_last", 2),
            ]:
                patches.append((str(config[key + "_old"]), str(config[key]), count))
            for minute in [config["stop_minute"], config["force_minute"]]:
                patches += [
                    (
                        f"datetime(2026, 10, 25, 10, {minute}, tzinfo=UTC)",
                        f"datetime(2026, 10, 25, 11, {minute}, tzinfo=UTC)",
                        1,
                    ),
                    (f"2026-10-25T10:{minute}:00Z", f"2026-10-25T11:{minute}:00Z", 1),
                ]
        elif name == "isolated-application.py":
            patches = [
                (
                    "native-" + profile + "-campaign-20261025",
                    "native-" + profile + "-campaign8-20261025",
                    1,
                ),
                (
                    config["env_old"] + "/application-env.json",
                    config["env"] + "/application-env.json",
                    1,
                ),
                (config["database_old"], config["database"], 1),
                (
                    f"{profile} campaign 10:{config['stop_minute']} broker guardian",
                    f"{profile} campaign8 11:{config['stop_minute']} broker guardian",
                    1,
                ),
            ]
        elif name == "isolated-build.py":
            patches = [
                (
                    "2026-10-25T" + config["app"].replace("11:", "10:") + "Z",
                    "2026-10-25T" + config["app"] + "Z",
                    1,
                )
            ]
        elif name == "interval-metrics.py":
            patches = [
                (
                    "datetime(2026, 10, 25, 10, 29, tzinfo=UTC)",
                    "datetime(2026, 10, 25, 11, 29, tzinfo=UTC)",
                    1,
                ),
                ("10:29UTC deadline", "11:29UTC deadline", 1),
                ("2026-10-25T10:29:00Z", "2026-10-25T11:29:00Z", 1),
            ]
        for old, new, count in patches:
            if text.count(old) != count:
                raise ValueError("EXACT_ROUND8_PATCH_POSITION_CHANGED")
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


def materialize(repository, profile, output):
    if profile not in PROFILES:
        raise ValueError("EXACT_ROUND8_PROFILE_REQUIRED")
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
        [
            "git",
            "-C",
            str(repository),
            "show",
            BASIS_COMMIT + ":deployment/native/campaign-prepare.py",
        ],
        check=True,
        capture_output=True,
        timeout=5,
    ).stdout
    if hashlib.sha256(raw).hexdigest() != BASIS_SHA:
        raise ValueError("IMMUTABLE_CAMPAIGN_HELPER_CHANGED")
    module = types.ModuleType("immutable_campaign_basis")
    exec(compile(raw, "campaign-prepare.py", "exec"), module.__dict__)
    output.mkdir(mode=0o700)
    module.materialize(repository, profile, output / "previous-campaign-basis")
    files = {
        p.name: p.read_bytes()
        for p in (output / "previous-campaign-basis").glob("*.py")
    }
    new, receipts = derive(profile, files)
    config = PROFILES[profile]
    manifest = {
        "profile": profile,
        "product_source_sha": SOURCE,
        "database_exact": config["database"],
        "api_workers": config["workers"],
        "ports": {
            key: config[key]
            for key in ["api", "amqp", "epmd", "distribution", "cli_first", "cli_last"]
        },
        "basis_commit": BASIS_COMMIT,
        "basis_sha256": BASIS_SHA,
        "first_spawn_deadline_utc": "2026-10-25T10:50:00Z",
        "application_stop_utc": "2026-10-25T" + config["app"] + "Z",
        "broker_stop_utc": f"2026-10-25T11:{config['stop_minute']}:00Z",
        "force_stop_utc": f"2026-10-25T11:{config['force_minute']}:00Z",
        "sampler_stop_utc": "2026-10-25T11:29:00Z"
        if profile == "performance"
        else None,
        "phase_grant_supplied_separately_by_root": True,
        "old_files_or_leases_modified": False,
        "generated_main_executed": False,
        "files": receipts,
    }
    for name, data in {
        **new,
        "derivation-campaign8.json": (json.dumps(manifest, indent=2) + "\n").encode(),
    }.items():
        fd = os.open(
            output / name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600
        )
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
    return {
        "success": True,
        "profile": profile,
        "output": str(output),
        "derivation_sha256": hashlib.sha256(
            (output / "derivation-campaign8.json").read_bytes()
        ).hexdigest(),
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
        print(
            json.dumps({"success": False, "error": "NEW_CAMPAIGN8_DERIVATION_REFUSED"})
        )
        raise SystemExit(1) from None
