"""One explicit functional/performance campaign; never rewrite earlier round leases."""

import argparse
import ast
import hashlib
import json
import os
import stat
import subprocess
import types
from pathlib import Path

PROFILES = {
    "functional": {
        "commit": "d0bfbd2838a3ecbde4c6fb1e769cf47b131160e5",
        "helper": "functional-seven.py",
        "sha": "fedc35b1b1820854cdd56934eaf07ece3a4b0af424b87ea4f4a46c867fb1f91a",
        "old_base": "native-functional-v7-20261025",
        "new_base": "native-functional-campaign-20261025",
        "old_prefix": "functional_v7_20261025_",
        "new_prefix": "functional_campaign_20261025_",
        "old_stop": "9, 24",
        "new_stop": "10, 22",
        "old_force": "9, 25",
        "new_force": "10, 25",
        "old_stop_utc": "09:24",
        "new_stop_utc": "10:22",
        "old_force_utc": "09:25",
        "new_force_utc": "10:25",
        "old_app_utc": "09:22:30",
        "new_app_utc": "10:20:30",
        "old_comment": "functional-v7 09:24 broker guardian",
        "new_comment": "functional campaign 10:22 broker guardian",
        "database": "t44_f817_20261025",
        "workers": 4,
        "phase_limit": "09:45:00",
    },
    "performance": {
        "commit": "00340a66b4e0f75a0fd5c79d7dbd22804935f0d7",
        "helper": "round-three.py",
        "sha": "d445eaae831420af37cb992c0b13184cc3aec2a245674700826ddacfc1dc6469",
        "old_base": "native-performance-round3-20261025",
        "new_base": "native-performance-campaign-20261025",
        "old_prefix": "performance_round3_20261025_",
        "new_prefix": "performance_campaign_20261025_",
        "old_stop": "9, 42",
        "new_stop": "10, 32",
        "old_force": "9, 45",
        "new_force": "10, 35",
        "old_stop_utc": "09:42",
        "new_stop_utc": "10:32",
        "old_force_utc": "09:45",
        "new_force_utc": "10:35",
        "old_app_utc": "09:40:30",
        "new_app_utc": "10:30:30",
        "old_comment": "round3 09:42 broker guardian",
        "new_comment": "performance campaign 10:32 broker guardian",
        "database": "t44_p829c_20261025",
        "workers": 7,
        "phase_limit": "10:15:00",
    },
}


def derive(profile, files):
    if profile not in PROFILES:
        raise ValueError("EXACT_CAMPAIGN_PROFILE_REQUIRED")
    config = PROFILES[profile]
    result, receipts = {}, {}
    for name, raw in files.items():
        text, changes, patches = raw.decode(), [], []
        if name == "isolated.py":
            patches = [
                (config["old_base"], config["new_base"], 2),
                (config["old_prefix"], config["new_prefix"], 1),
                (
                    "datetime(2026, 10, 25, " + config["old_stop"] + ", tzinfo=UTC)",
                    "datetime(2026, 10, 25, " + config["new_stop"] + ", tzinfo=UTC)",
                    1,
                ),
                (
                    "datetime(2026, 10, 25, " + config["old_force"] + ", tzinfo=UTC)",
                    "datetime(2026, 10, 25, " + config["new_force"] + ", tzinfo=UTC)",
                    1,
                ),
                ("datetime(2026, 10, 25, 9, 20, tzinfo=UTC)", "datetime(2026, 10, 25, 10, 0, tzinfo=UTC)", 1),
                ("2026-10-25T" + config["old_stop_utc"] + ":00Z", "2026-10-25T" + config["new_stop_utc"] + ":00Z", 1),
                ("2026-10-25T" + config["old_force_utc"] + ":00Z", "2026-10-25T" + config["new_force_utc"] + ":00Z", 1),
                ("2026-10-25T09:20:00Z", "2026-10-25T10:00:00Z", 1),
            ]
        elif name == "isolated-application.py":
            patches = [(config["old_base"], config["new_base"], 1), (config["old_comment"], config["new_comment"], 1)]
        elif name == "isolated-build.py":
            patches = [("2026-10-25T" + config["old_app_utc"] + "Z", "2026-10-25T" + config["new_app_utc"] + "Z", 1)]
        elif name == "interval-metrics.py":
            patches = [
                ("datetime(2026, 10, 25, 9, 39, tzinfo=UTC)", "datetime(2026, 10, 25, 10, 29, tzinfo=UTC)", 1),
                ("09:39UTC deadline", "10:29UTC deadline", 1),
                ("2026-10-25T09:39:00Z", "2026-10-25T10:29:00Z", 1),
            ]
        for old, new, count in patches:
            if text.count(old) != count:
                raise ValueError("EXACT_CAMPAIGN_PATCH_POSITION_CHANGED")
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
    config = PROFILES[profile]
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
        ["git", "-C", str(repository), "show", config["commit"] + ":deployment/native/" + config["helper"]],
        check=True,
        capture_output=True,
        timeout=5,
    ).stdout
    if hashlib.sha256(raw).hexdigest() != config["sha"]:
        raise ValueError("IMMUTABLE_BASIS_HELPER_CHANGED")
    module = types.ModuleType("immutable_campaign_basis")
    exec(compile(raw, config["helper"], "exec"), module.__dict__)
    output.mkdir(mode=0o700)
    module.materialize(repository, output / "previous-basis")
    files = {p.name: p.read_bytes() for p in (output / "previous-basis").glob("*.py")}
    new, receipts = derive(profile, files)
    manifest = {
        "campaign_profile": profile,
        "source_sha": "c8cea7e82805de5283ce67501769fa9a4efc1047",
        "database_exact": config["database"],
        "api_workers": config["workers"],
        "basis_helper_commit": config["commit"],
        "basis_helper_sha256": config["sha"],
        "first_spawn_deadline_utc": "2026-10-25T10:00:00Z",
        "app_stop_utc": "2026-10-25T" + config["new_app_utc"] + "Z",
        "broker_stop_utc": "2026-10-25T" + config["new_stop_utc"] + ":00Z",
        "force_stop_utc": "2026-10-25T" + config["new_force_utc"] + ":00Z",
        "coordinator_phase_grant_limit_utc": "2026-10-25T" + config["phase_limit"] + "Z",
        "phase_grant_is_not_resource_lease": True,
        "sampler_stop_utc": "2026-10-25T10:29:00Z" if profile == "performance" else None,
        "old_round_files_grants_modified": False,
        "generated_main_executed": False,
        "files": receipts,
    }
    for name, data in {**new, "derivation-campaign.json": (json.dumps(manifest, indent=2) + "\n").encode()}.items():
        fd = os.open(output / name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
    return {
        "success": True,
        "profile": profile,
        "output": str(output),
        "derivation_sha256": hashlib.sha256((output / "derivation-campaign.json").read_bytes()).hexdigest(),
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
        print(json.dumps({"success": False, "error": "NEW_CAMPAIGN_DERIVATION_REFUSED"}))
        raise SystemExit(1) from None
