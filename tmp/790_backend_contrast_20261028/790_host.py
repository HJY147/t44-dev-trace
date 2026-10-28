"""Python 3.10 APP host runner: data-only S1, then separately requested stdlib edge S2."""

import argparse
import hashlib
import importlib.util
import json
import os
import platform
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("contrast790_bootstrap", HERE / "790_bootstrap.py")
bootstrap = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bootstrap)
UTC = timezone.utc  # noqa: UP017 -- Python 3.10 cloud host.
DOCKER = bootstrap.DOCKER


def sha(path):
    return hashlib.sha256(bootstrap.raw(path)).hexdigest()


def owned_copy(source, target):
    bootstrap.write(target, bootstrap.raw(source, True))
    os.chown(target, 10001, 10001)


def checked(args):
    phase = args.phase_dir
    if os.geteuid() != 0 or platform.system() != "Linux" or phase.resolve() != phase:
        raise ValueError("ROOT_CANONICAL_LINUX_PHASE_REQUIRED")
    if not phase.is_absolute() or not re.fullmatch(r"[0-9a-f]{64}", args.binding_sha256):
        raise ValueError("EXPLICIT_PHASE_AND_HASH_REQUIRED")
    if sha(phase / "binding.json") != args.binding_sha256:
        raise ValueError("PHASE_BINDING_HASH_DIFFERS")
    binding = json.loads(bootstrap.raw(phase / "binding.json", True))
    bootstrap.validate_binding(binding, datetime.now(UTC))
    for name, wanted in binding["file_hashes"].items():
        path = phase / name
        if path.resolve() != path or sha(path) != wanted:
            raise ValueError("BOUND_FILE_CHANGED")
    if sha(HERE / "manifest.json") != args.manifest_sha256:
        raise ValueError("EXACT_TOOL_MANIFEST_REQUIRED")
    manifest = json.loads(bootstrap.raw(HERE / "manifest.json"))
    for name, item in manifest["files"].items():
        path = HERE / name
        if path.resolve() != path or sha(path) != item["sha256"]:
            raise ValueError("TOOL_BUNDLE_CHANGED")
    if any(
        not re.fullmatch(r"[a-zA-Z0-9-]{1,48}", value)
        for value in (args.fixture_name, args.split_name)
    ):
        raise ValueError("SAFE_EXPLICIT_NEW_DIRECTORY_NAMES_REQUIRED")
    fixture = phase / args.fixture_name
    control_raw = bootstrap.raw(fixture / "control.private.json", True)
    control = json.loads(control_raw)
    if (
        control["binding_sha256"] != args.binding_sha256
        or control["source_sha"] != bootstrap.SOURCE
        or control["namespace"] != binding["project"]
        or control["database"] != binding["database"]
        or control["api_workers"] != binding["api_workers"]
        or control["stop_utc"] != binding["stop_utc"]
        or control["anchor_at"] != bootstrap.ANCHOR
    ):
        raise ValueError("BOOTSTRAP_CONTROL_DIFFERS_FROM_ACTUAL_BINDING")
    if sha(phase / "tls/ca.pem") != control["ca_sha256"]:
        raise ValueError("EXACT_CA_REQUIRED")
    env = bootstrap.environment()
    subprocess.run(
        ["systemctl", "is-active", "--quiet", binding["timer_unit"]],
        check=True,
        timeout=15,
        env=env,
    )
    return phase, fixture, binding, control, hashlib.sha256(control_raw).hexdigest(), env


def run_owned(name, argv, result_path, private, accepted, owner, env):
    try:
        result = subprocess.run(argv, capture_output=True, check=False, timeout=600, env=env)
    except subprocess.TimeoutExpired as error:
        bootstrap.write(private / (name + ".stdout"), error.stdout or b"")
        bootstrap.write(private / (name + ".stderr"), error.stderr or b"")
        info = json.loads(
            subprocess.check_output(
                DOCKER + ["inspect", "--format", "{{json .}}", name], env=env, timeout=15
            )
        )
        if (
            info["Image"] not in accepted
            or info["Config"]["Labels"].get("io.t44.contrast.owner") != owner
        ):
            raise RuntimeError("OWNED_TIMEOUT_IDENTITY_MISMATCH") from None
        subprocess.run(
            DOCKER + ["stop", "--time", "15", name],
            capture_output=True,
            check=True,
            timeout=30,
            env=env,
        )
        raise RuntimeError("OWNED_ONEOFF_TIMEOUT_PREFIX_PRESERVED") from None
    bootstrap.write(private / (name + ".stdout"), result.stdout)
    bootstrap.write(private / (name + ".stderr"), result.stderr)
    if result_path.is_file():
        for line in bootstrap.raw(result_path, True).decode().splitlines():
            row = json.loads(line)
            print(
                json.dumps({key: value for key, value in row.items() if key != "results"}),
                flush=True,
            )
    if result.returncode:
        raise RuntimeError("ONEOFF_FAILED_NO_RETRY_PREFIX_PRESERVED")
    rows = [json.loads(line) for line in bootstrap.raw(result_path, True).decode().splitlines()]
    if rows[-1].get("diagnostic_valid") is not True:
        raise ValueError("EXPLICIT_COMPLETE_STAGE_FINAL_REQUIRED")
    return rows[-1]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("stage1", "edge"))
    parser.add_argument("--phase-dir", type=Path, required=True)
    for name in ("binding-sha256", "manifest-sha256", "fixture-name", "split-name"):
        parser.add_argument("--" + name, required=True)
    args = parser.parse_args(argv)
    phase, fixture, binding, control, control_sha, env = checked(args)
    directory = fixture / args.split_name
    owner = binding["project"]
    if args.action == "stage1":
        composition = json.loads(bootstrap.raw(phase / "compose.json", True))
        if set(composition["services"]["admin"]["networks"]) != {"data"}:
            raise ValueError("ADMIN_MUST_REMAIN_DATA_ONLY")
        alias = binding["images"]["backend"]["alias"]
        accepted = {binding["image_ids"]["backend"], binding["config_ids"]["backend"]}
        actual = (
            subprocess.check_output(
                DOCKER + ["image", "inspect", "--format", "{{.Id}}", alias], env=env, timeout=15
            )
            .decode()
            .strip()
        )
        if actual not in accepted:
            raise ValueError("BACKEND_IMAGE_CHANGED")
        directory.mkdir(mode=0o700)
        for name in ("inputs", "receipts", "s1", "s2"):
            (directory / name).mkdir(mode=0o700)
        for name in ("s1", "s2"):
            os.chown(directory / name, 10001, 10001)
        for name in ("control.private.json", "identities.private.json", "accounts.private.json"):
            owned_copy(fixture / name, directory / "inputs" / name)
        bootstrap.write(directory / "inputs/ca.pem", bootstrap.raw(phase / "tls/ca.pem"))
        os.chown(directory / "inputs/ca.pem", 10001, 10001)
        name = binding["project"] + "-790s1"
        argv = DOCKER + [
            "compose",
            "--env-file",
            str(phase / "application.env"),
            "--file",
            str(phase / "compose.json"),
            "--project-name",
            binding["project"],
            "--profile",
            "operations",
            "run",
            "--rm",
            "--no-deps",
            "-T",
            "--name",
            name,
            "--label",
            "io.t44.contrast.owner=" + owner,
            "--entrypoint",
            "python",
            "--env",
            "T44_CONTRAST_ALLOW=t44-contrast-development-v1",
            "--env",
            "T44_CONTRAST_SOURCE=" + bootstrap.SOURCE,
            "--volume",
            str(HERE) + ":/opt/790:ro",
            "--volume",
            str(directory / "inputs/identities.private.json") + ":/run/identities.json:ro",
            "--volume",
            str(directory / "inputs/control.private.json") + ":/run/control.json:ro",
            "--volume",
            str(directory / "s1") + ":/diag-output",
            "admin",
            "-B",
            "/opt/790/data/790_stage1.py",
            "--identities",
            "/run/identities.json",
            "--output-dir",
            "/diag-output/candidate-01",
            "--host",
            "mysql",
            "--port",
            "3306",
            "--user",
            binding["database"] + "_app",
            "--slots",
            "441",
            "--control",
            "/run/control.json",
            "--control-sha256",
            control_sha,
        ]
        final = run_owned(
            name,
            argv,
            directory / "s1/candidate-01/status.public.jsonl",
            directory / "receipts",
            accepted,
            owner,
            env,
        )
        if sha(directory / "s1/candidate-01/candidate.private.json") != final["candidate_sha256"]:
            raise ValueError("S1_CANDIDATE_HASH_DIFFERS")
        print(
            json.dumps(
                {
                    "kind": "contrast790-s1-host-complete",
                    "source_sha": bootstrap.SOURCE,
                    "candidate_sha256": final["candidate_sha256"],
                    "directory": str(directory),
                    "control_sha256": control_sha,
                    "formal_acceptance": False,
                }
            )
        )
        return
    if directory.resolve() != directory:
        raise ValueError("UNCHANGED_CANONICAL_SPLIT_DIRECTORY_REQUIRED")
    status = [
        json.loads(line)
        for line in bootstrap.raw(directory / "s1/candidate-01/status.public.jsonl", True)
        .decode()
        .splitlines()
    ]
    final = status[-1]
    candidate = directory / "s1/candidate-01/candidate.private.json"
    if final.get("diagnostic_valid") is not True or sha(candidate) != final["candidate_sha256"]:
        raise ValueError("EXACT_COMPLETED_S1_CANDIDATE_REQUIRED")
    alias = binding["images"]["python"]["alias"]
    accepted = {binding["image_ids"]["python"], binding["config_ids"]["python"]}
    actual = (
        subprocess.check_output(
            DOCKER + ["image", "inspect", "--format", "{{.Id}}", alias], env=env, timeout=15
        )
        .decode()
        .strip()
    )
    if actual not in accepted:
        raise ValueError("PROVEN_PYTHON_IMAGE_CHANGED")
    network = binding["project"] + "_edge"
    labels = json.loads(
        subprocess.check_output(
            DOCKER + ["network", "inspect", "--format", "{{json .Labels}}", network],
            env=env,
            timeout=15,
        )
    )
    if (
        labels.get("com.docker.compose.project") != owner
        or labels.get("com.docker.compose.network") != "edge"
    ):
        raise ValueError("OWNED_EDGE_NETWORK_REQUIRED")
    name = binding["project"] + "-790s2"
    argv = DOCKER + [
        "run",
        "--rm",
        "--name",
        name,
        "--label",
        "io.t44.contrast.owner=" + owner,
        "--network",
        network,
        "--read-only",
        "--user",
        "10001:10001",
        "--cap-drop",
        "ALL",
        "--security-opt",
        "no-new-privileges:true",
        "--pids-limit",
        "1024",
        "--memory",
        "2g",
        "--volume",
        str(HERE / "edge") + ":/opt/790:ro",
        "--volume",
        str(directory / "inputs/accounts.private.json") + ":/run/accounts.json:ro",
        "--volume",
        str(directory / "inputs/control.private.json") + ":/run/control.json:ro",
        "--volume",
        str(directory / "inputs/ca.pem") + ":/run/ca.pem:ro",
        "--volume",
        str(candidate) + ":/run/candidate.json:ro",
        "--volume",
        str(directory / "s2") + ":/diag-output",
        alias,
        "python",
        "-B",
        "/opt/790/790_stage2.py",
        "--control",
        "/run/control.json",
        "--control-sha256",
        control_sha,
        "--accounts",
        "/run/accounts.json",
        "--candidate",
        "/run/candidate.json",
        "--candidate-sha256",
        final["candidate_sha256"],
        "--output-dir",
        "/diag-output/session-01",
        "--ca",
        "/run/ca.pem",
        "--ca-sha256",
        control["ca_sha256"],
        "--url",
        control["url"],
    ]
    run_owned(
        name,
        argv,
        directory / "s2/session-01/status.public.jsonl",
        directory / "receipts",
        accepted,
        owner,
        env,
    )
    packet = directory / "s2/session-01/session.private.json"
    print(
        json.dumps(
            {
                "kind": "contrast790-s2-host-complete",
                "source_sha": bootstrap.SOURCE,
                "packet_path": str(packet),
                "packet_sha256": sha(packet),
                "control_path": str(directory / "inputs/control.private.json"),
                "control_sha256": control_sha,
                "ca_path": str(directory / "inputs/ca.pem"),
                "formal_acceptance": False,
                "password_or_session_printed": False,
            }
        )
    )


if __name__ == "__main__":
    os.umask(0o077)
    try:
        main()
    except (
        OSError,
        ValueError,
        RuntimeError,
        KeyError,
        TypeError,
        AssertionError,
        subprocess.SubprocessError,
    ) as error:
        print(
            json.dumps({"split_host_failed": type(error).__name__, "partial_state_preserved": True})
        )
        raise SystemExit(1) from None
