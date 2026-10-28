"""Python 3.10 LOAD host: private inputs, disjoint warmups, then 400-client short diagnostic."""

import argparse
import hashlib
import importlib.util
import json
import os
import platform
import re
import socket
import subprocess
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("load790_bootstrap", HERE / "790_bootstrap.py")
bootstrap = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bootstrap)
UTC = timezone.utc  # noqa: UP017 -- cloud host Python 3.10.
DOCKER = bootstrap.DOCKER
COHORTS = (("baseline1", 1, 20, 0), ("warmup40", 40, 5, 1), ("measure400", 400, 5, 41))


def sha(path):
    return hashlib.sha256(bootstrap.raw(path)).hexdigest()


def private_copy(source, target, expected):
    raw = bootstrap.raw(source, True)
    if hashlib.sha256(raw).hexdigest() != expected:
        raise ValueError("EXACT_TRANSFERRED_PRIVATE_INPUT_HASH_REQUIRED")
    bootstrap.write(target, raw)
    os.chown(target, 10001, 10001)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inputs-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    for name in (
        "control-sha256",
        "packet-sha256",
        "manifest-sha256",
        "expected-host",
        "python-image",
        "python-image-id",
    ):
        parser.add_argument("--" + name, required=True)
    args = parser.parse_args(argv)
    if (
        os.geteuid() != 0
        or platform.system() != "Linux"
        or socket.gethostname().split(".")[0] != args.expected_host
        or not args.inputs_dir.is_absolute()
        or args.inputs_dir.resolve() != args.inputs_dir
        or not args.output_dir.is_absolute()
        or args.output_dir.parent.resolve() != args.output_dir.parent
        or not re.fullmatch(r"sha256:[0-9a-f]{64}", args.python_image_id)
        or not args.python_image.startswith("t44-official-python:")
    ):
        raise ValueError("EXACT_OWNED_LOAD_HOST_PATHS_AND_PROVEN_PYTHON_IMAGE_REQUIRED")
    if sha(HERE / "manifest.json") != args.manifest_sha256:
        raise ValueError("EXACT_TOOL_MANIFEST_REQUIRED")
    manifest = json.loads(bootstrap.raw(HERE / "manifest.json"))
    for name, info in manifest["files"].items():
        if sha(HERE / name) != info["sha256"]:
            raise ValueError("EXACT_TOOL_FILE_HASH_REQUIRED")
    control_raw = bootstrap.raw(args.inputs_dir / "control.private.json", True)
    if hashlib.sha256(control_raw).hexdigest() != args.control_sha256:
        raise ValueError("EXACT_APP_CONTROL_HASH_REQUIRED")
    control = json.loads(control_raw)
    if (
        control["kind"] != "t44-contrast-development-v1"
        or control["source_sha"] != bootstrap.SOURCE
        or control["anchor_at"] != bootstrap.ANCHOR
        or control["seed"] != 44
        or (bootstrap.stamp(control["stop_utc"]) - datetime.now(UTC)).total_seconds() < 330
    ):
        raise ValueError("ACTUAL_NEW_ARM_CONTROL_AND_FULL_MATRIX_TIME_BUDGET_REQUIRED")
    match = re.fullmatch(r"r28p(7|16)gen[0-9]{2}", control.get("run_id", ""))
    if (
        not match
        or control["namespace"] != "t44-cloud-" + control["run_id"] + "-p"
        or control["database"] != "t44c_" + control["run_id"] + "_p"
        or type(control["api_workers"]) is not int
        or control["api_workers"] != int(match[1])
        or bootstrap.stamp(control["stop_utc"]) > bootstrap.HARDSTOP
        or not re.fullmatch(r"[0-9a-f]{64}", control["binding_sha256"])
    ):
        raise ValueError("APP_CONTROL_ARM_NAMESPACE_OR_DEADLINE_DIFFERS")
    if sha(args.inputs_dir / "ca.pem") != control["ca_sha256"]:
        raise ValueError("EXACT_APP_CA_HASH_REQUIRED")
    env = bootstrap.environment()
    actual = (
        subprocess.check_output(
            DOCKER + ["image", "inspect", "--format", "{{.Id}}", args.python_image],
            env=env,
            timeout=15,
        )
        .decode()
        .strip()
    )
    if actual != args.python_image_id:
        raise ValueError("PROVEN_OFFICIAL_PYTHON_IMAGE_CHANGED")
    args.output_dir.mkdir(mode=0o700)
    inputs = args.output_dir / "inputs"
    inputs.mkdir(mode=0o700)
    private_copy(
        args.inputs_dir / "control.private.json",
        inputs / "control.private.json",
        args.control_sha256,
    )
    private_copy(
        args.inputs_dir / "session.private.json",
        inputs / "session.private.json",
        args.packet_sha256,
    )
    bootstrap.write(inputs / "ca.pem", bootstrap.raw(args.inputs_dir / "ca.pem"))
    os.chown(inputs / "ca.pem", 10001, 10001)
    previous, previous_hash = inputs / "session.private.json", args.packet_sha256
    results = []
    for cohort, clients, cycles, offset in COHORTS:
        directory = args.output_dir / cohort
        directory.mkdir(mode=0o700)
        os.chown(directory, 10001, 10001)
        name = control["namespace"] + "-790-" + cohort.lower()
        argv = DOCKER + [
            "run",
            "--rm",
            "--pull",
            "never",
            "--name",
            name,
            "--label",
            "io.t44.contrast.owner=" + control["namespace"],
            "--network",
            "bridge",
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
            "4g",
            "--volume",
            str(HERE / "edge") + ":/opt/790:ro",
            "--volume",
            str(inputs / "control.private.json") + ":/run/control.json:ro",
            "--volume",
            str(inputs / "ca.pem") + ":/run/ca.pem:ro",
            "--volume",
            str(previous) + ":/run/session.json:ro",
            "--volume",
            str(directory) + ":/diagnostic",
            args.python_image,
            "python",
            "-B",
            "/opt/790/790_http.py",
            "--control",
            "/run/control.json",
            "--control-sha256",
            args.control_sha256,
            "--packet",
            "/run/session.json",
            "--packet-sha256",
            previous_hash,
            "--ca",
            "/run/ca.pem",
            "--output",
            "/diagnostic/result.public.jsonl",
            "--updated-packet",
            "/diagnostic/session.private.json",
            "--clients",
            str(clients),
            "--cycles",
            str(cycles),
            "--slot-offset",
            str(offset),
            "--seconds",
            "90",
        ]
        budget = bootstrap.remaining_timeout(control["stop_utc"], 240)
        try:
            completed = subprocess.run(
                argv, capture_output=True, check=False, timeout=budget, env=env
            )
        except subprocess.TimeoutExpired as error:
            bootstrap.write(args.output_dir / (cohort + ".stdout"), error.stdout or b"")
            bootstrap.write(args.output_dir / (cohort + ".stderr"), error.stderr or b"")
            info = json.loads(
                subprocess.check_output(
                    DOCKER + ["inspect", "--format", "{{json .}}", name], env=env, timeout=15
                )
            )
            if (
                info["Image"] != actual
                or info["Config"]["Labels"].get("io.t44.contrast.owner") != control["namespace"]
            ):
                raise RuntimeError("OWNED_LOAD_TIMEOUT_IDENTITY_MISMATCH") from None
            subprocess.run(
                DOCKER + ["stop", "--time", "15", name],
                capture_output=True,
                check=True,
                timeout=30,
                env=env,
            )
            raise RuntimeError("OWNED_LOAD_TIMEOUT_PREFIX_PRESERVED") from None
        bootstrap.write(args.output_dir / (cohort + ".stdout"), completed.stdout)
        bootstrap.write(args.output_dir / (cohort + ".stderr"), completed.stderr)
        report_path = directory / "result.public.jsonl"
        rows = (
            [json.loads(line) for line in bootstrap.raw(report_path, True).decode().splitlines()]
            if report_path.is_file()
            else []
        )
        if rows:
            print(json.dumps({k: v for k, v in rows[0].items() if k != "results"}), flush=True)
        expected = clients * cycles * 4
        if (
            completed.returncode
            or len(rows) != 2
            or rows[-1].get("kind") != "writer_final"
            or rows[0].get("diagnostic_complete") is not True
            or rows[0].get("observed_requests") != expected
            or rows[0].get("expected_requests") != expected
            or rows[0].get("failed_clients")
            or rows[0].get("deadline_clients")
        ):
            raise RuntimeError("INCOMPLETE_OR_FAILED_COHORT_NO_NEXT_COHORT")
        bootstrap.remaining_timeout(control["stop_utc"], 240)
        previous = directory / "session.private.json"
        previous_hash = sha(previous)
        results.append(
            {
                "cohort": cohort,
                "requests": expected,
                "slot_offset": offset,
                "public_result_sha256": sha(report_path),
                "updated_packet_sha256": previous_hash,
            }
        )
    print(
        json.dumps(
            {
                "kind": "contrast790-load-matrix-complete-not-acceptance",
                "source_sha": bootstrap.SOURCE,
                "namespace": control["namespace"],
                "cohorts": results,
                "measurement_requests": 8000,
                "formal_acceptance": False,
                "scope": "developer contrast only; not a seven-role independent 600-second run",
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
        print(json.dumps({"load_failed": type(error).__name__, "partial_state_preserved": True}))
        raise SystemExit(1) from None
