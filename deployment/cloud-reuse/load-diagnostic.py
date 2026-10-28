"""Owned 15-minute Python3.12 calibration container; one new data mount, no business environment."""

import argparse
import hashlib
import importlib.util
import json
import os
import re
import socket
import stat
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

PROOF_SHA = "47b50d0111737d2b4ff7b47ce37c46bc5d7fc208d2f3933088b8a08dab326fc0"
DOCKER = ["docker", "--context", "default"]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stamp():
    return datetime.now(timezone.utc).isoformat()  # noqa: UP017 - Ubuntu22 Python3.10


def save(path, value):
    descriptor = os.open(
        path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600
    )
    with os.fdopen(descriptor, "w") as stream:
        json.dump(value, stream, indent=2)
        stream.write("\n")


def command(argv, timeout=30):
    env = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith(("DOCKER_", "COMPOSE_", "T44_", "MYSQL_", "RABBITMQ_"))
    }
    return subprocess.run(
        list(map(str, argv)), capture_output=True, check=True, timeout=timeout, env=env
    ).stdout


def private(path, directory=False):
    value = path.lstat()
    if (
        path.resolve() != path
        or value.st_uid != os.geteuid()
        or stat.S_IMODE(value.st_mode) != (0o700 if directory else 0o600)
        or not (
            stat.S_ISDIR(value.st_mode) if directory else stat.S_ISREG(value.st_mode)
        )
    ):
        raise ValueError("ROOT_PRIVATE_CANONICAL_OBJECT_REQUIRED")


def prepare(args):
    if os.geteuid() != 0 or not re.fullmatch(r"[a-z][a-z0-9]{5,15}", args.run_id):
        raise ValueError("ROOT_AND_FRESH_RUNID_REQUIRED")
    private(args.image_proof)
    private(args.proof_raw)
    if (
        sha(args.image_proof) != PROOF_SHA
        or not re.fullmatch(r"[0-9a-f]{64}", args.proof_raw_sha256)
        or sha(args.proof_raw) != args.proof_raw_sha256
    ):
        raise ValueError("EXACT_PROOF_CODE_AND_ROOT_VERIFIED_FULL_RAW_REQUIRED")
    rows = [json.loads(line) for line in args.proof_raw.read_text().splitlines()]
    if (
        not rows
        or rows[-1].get("kind") != "proof_final"
        or not rows[-1]["complete"]
        or not rows[-1]["all_seven_proven"]
    ):
        raise ValueError("COMPLETE_ALL_SEVEN_PROOF_REQUIRED")
    python_rows = [
        row
        for row in rows
        if row.get("kind") == "role_proof" and row["role"] == "python"
    ]
    if len(python_rows) != 1 or not python_rows[0]["proof"]["success"]:
        raise ValueError("ONE_PROVEN_OFFICIAL_PYTHON_IMAGE_REQUIRED")
    row = python_rows[0]
    spec = importlib.util.spec_from_file_location(
        "verified_image_proof", args.image_proof
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    current = module.actual_image(row["declared_CI"]["alias"])
    original = row["actual_projection_no_Env_or_Cmd"]
    if any(
        current[key] != original[key]
        for key in [
            "Id",
            "Descriptor",
            "RootFS",
            "Os",
            "Architecture",
            "Variant",
            "Config",
        ]
    ):
        raise ValueError("PROVEN_PYTHON_IDENTITY_CHANGED_NO_RETAG_OR_FALLBACK")
    private(args.output.parent, True)
    args.output.mkdir(mode=0o700)
    (args.output / "receipts").mkdir(mode=0o700)
    data = args.output / "data"
    data.mkdir(mode=0o700)
    os.chown(data, 10001, 10001)
    descriptor = os.open(
        args.output / "controller.py",
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
        0o600,
    )
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(Path(__file__).read_bytes())
    binding = {
        "kind": "pure-synthetic-linux-calibration",
        "created_utc": stamp(),
        "name": "t44-cal-" + args.run_id,
        "run_id": args.run_id,
        "image_alias": row["declared_CI"]["alias"],
        "actual_image_id": row["proof"]["actual_id"],
        "original_config_id": row["proof"]["config_id"],
        "proof_raw_sha256": args.proof_raw_sha256,
        "data_dir": str(data),
        "port": 18205,
        "max_seconds": 900,
        "controller_sha256": sha(args.output / "controller.py"),
        "business_env_or_DB_mounts": False,
        "initial_data_empty": True,
        "container_started": False,
    }
    save(args.output / "binding.json", binding)
    return {
        "success": True,
        "directory": str(args.output),
        "binding_sha256": sha(args.output / "binding.json"),
        "data_dir": str(data),
        "container_started": False,
        "script_or_calibration_outcome": None,
    }


def binding(directory):
    private(directory, True)
    private(directory / "binding.json")
    value = json.loads((directory / "binding.json").read_text())
    if (
        value["kind"] != "pure-synthetic-linux-calibration"
        or not re.fullmatch(r"t44-cal-[a-z][a-z0-9]{5,15}", value["name"])
        or sha(directory / "controller.py") != value["controller_sha256"]
    ):
        raise ValueError("EXACT_CALIBRATION_BINDING_REQUIRED")
    if (
        Path(value["data_dir"]) != directory / "data"
        or value["port"] != 18205
        or value["max_seconds"] != 900
    ):
        raise ValueError("EXACT_DATA_DIRECTORY_LOOPBACK_PORT_AND_WINDOW_REQUIRED")
    return value


def receipt(directory, action, **fields):
    row = {"utc": stamp(), "action": action, "receipt_id": uuid4().hex, **fields}
    save(directory / "receipts" / (row["receipt_id"] + ".json"), row)
    return row


def container(directory, value):
    private(directory / "container.json")
    record = json.loads((directory / "container.json").read_text())
    if not re.fullmatch(r"[0-9a-f]{64}", record["container_id"]):
        raise ValueError("EXACT_CONTAINER_ID_REQUIRED")
    raw = (
        command(
            [
                *DOCKER,
                "inspect",
                "--format",
                "{{json .Id}}\t{{json .Image}}\t{{json .Config.Labels}}\t{{json .State.Running}}\t{{json .Mounts}}\t{{json .HostConfig.PortBindings}}",
                record["container_id"],
            ]
        )
        .decode()
        .strip()
    )
    identity, image, labels, running, mounts, ports = [
        json.loads(part) for part in raw.split("\t")
    ]
    if (
        identity != record["container_id"]
        or image not in {value["actual_image_id"], value["original_config_id"]}
        or labels.get("io.t44.calibration.run") != value["run_id"]
        or labels.get("io.t44.calibration.proof") != value["proof_raw_sha256"]
    ):
        raise ValueError("OWNED_CONTAINER_IMAGE_OR_LABELS_CHANGED")
    binds = [row for row in mounts if row["Type"] == "bind"]
    extras = [row for row in mounts if row["Type"] != "bind"]
    if (
        len(binds) != 1
        or binds[0]["Type"] != "bind"
        or binds[0]["Source"] != value["data_dir"]
        or binds[0]["Destination"] != "/diagnostic"
        or any(row["Type"] != "tmpfs" or row["Destination"] != "/tmp" for row in extras)
        or ports != {"18205/tcp": [{"HostIp": "127.0.0.1", "HostPort": "18205"}]}
    ):
        raise ValueError("CALIBRATION_MOUNT_OR_LOOPBACK_PORT_CHANGED")
    return record, running


def operate(args):
    directory = args.directory
    value = binding(directory)
    if args.action == "start":
        if (directory / "container.json").exists():
            raise ValueError("CALIBRATION_ALREADY_CREATED_NO_RESTART")
        with socket.socket() as check:
            check.bind(("127.0.0.1", 18205))
        stop_epoch = time.time() + 900
        lifespan = (
            "import time\nwall="
            + repr(stop_epoch)
            + "\nmono=time.monotonic()+min(900,max(0,wall-time.time()))\nwhile time.time()<wall and time.monotonic()<mono:\n time.sleep(min(1,max(0,wall-time.time()),max(0,mono-time.monotonic())))"
        )
        argv = [
            *DOCKER,
            "run",
            "--detach",
            "--name",
            value["name"],
            "--label",
            "io.t44.calibration.run=" + value["run_id"],
            "--label",
            "io.t44.calibration.proof=" + value["proof_raw_sha256"],
            "--init",
            "--restart",
            "no",
            "--read-only",
            "--user",
            "10001:10001",
            "--cap-drop",
            "ALL",
            "--security-opt",
            "no-new-privileges:true",
            "--pids-limit",
            "1024",
            "--ulimit",
            "nofile=65536:65536",
            "--memory",
            "4g",
            "--tmpfs",
            "/tmp:rw,size=128m",
            "--publish",
            "127.0.0.1:18205:18205",
            "--mount",
            "type=bind,src=" + value["data_dir"] + ",dst=/diagnostic",
            "--workdir",
            "/diagnostic",
            "--env",
            "PYTHONDONTWRITEBYTECODE=1",
            "--env",
            "PYTHONUNBUFFERED=1",
            value["image_alias"],
            "python",
            "-c",
            lifespan,
        ]
        identity = command(argv).decode().strip()
        if not re.fullmatch(r"[0-9a-f]{64}", identity):
            raise ValueError("NEW_CONTAINER_ID_NOT_RETURNED")
        record = {
            "container_id": identity,
            "started_utc": stamp(),
            "started_monotonic_ns": time.monotonic_ns(),
            "max_seconds": 900,
            "stop_epoch": stop_epoch,
        }
        save(directory / "container.json", record)
        container(directory, value)
        version = (
            command([*DOCKER, "exec", identity, "python", "--version"]).decode().strip()
        )
        return receipt(
            directory,
            "start",
            success=True,
            **record,
            actual_python_version=version,
            application_server_started=False,
            sole_mount=value["data_dir"],
            port_binding="127.0.0.1:18205",
            expiry="PID1 exits at host-wall deadline or <=900monotonicseconds;restart=no",
            business_env_mounted=False,
        )
    record, running = container(directory, value)
    if args.action == "status":
        return receipt(
            directory,
            "status",
            success=True,
            container_id=record["container_id"],
            running=running,
        )
    if args.action == "stop":
        if running:
            command(
                [*DOCKER, "stop", "--time", "10", record["container_id"]], timeout=30
            )
        after = container(directory, value)[1]
        return receipt(
            directory,
            "stop",
            success=not after,
            container_id=record["container_id"],
            running=after,
            data_or_container_deleted=False,
            VM_touched=False,
        )
    if not running:
        raise ValueError("CALIBRATION_WINDOW_EXPIRED_OR_CONTAINER_STOPPED")
    if not re.fullmatch(
        r"[A-Za-z][A-Za-z0-9_.-]{0,90}\.py", args.script or ""
    ) or not re.fullmatch(r"[0-9a-f]{64}", args.script_sha256 or ""):
        raise ValueError("EXPLICIT_NEUTRAL_SCRIPT_AND_SHA256_REQUIRED")
    script = directory / "data" / args.script
    info = script.lstat()
    if (
        not stat.S_ISREG(info.st_mode)
        or info.st_nlink != 1
        or sha(script) != args.script_sha256
    ):
        raise ValueError("APPROVED_SCRIPT_BYTES_DIFFER")
    os.chown(script, 10001, 10001)
    script.chmod(0o600)
    argv = (
        [*DOCKER, "exec"]
        + (["--detach"] if args.detach else [])
        + [
            "--user",
            "10001:10001",
            "--workdir",
            "/diagnostic",
            record["container_id"],
            "python",
            "/diagnostic/" + args.script,
        ]
    )
    output = command(argv, timeout=max(1, min(900, record["stop_epoch"] - time.time())))
    file = directory / "receipts" / ("script-stdout-" + uuid4().hex + ".txt")
    descriptor = os.open(
        file, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600
    )
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(output)
    return receipt(
        directory,
        "exec-neutral-script",
        success=True,
        script=args.script,
        script_sha256=args.script_sha256,
        detached=args.detach,
        private_stdout_path=str(file),
        script_result_requires_separate_review=True,
        business_env_mounted=False,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "action", choices=("prepare", "start", "status", "exec", "stop")
    )
    parser.add_argument("--output", type=Path)
    parser.add_argument("--run-id")
    parser.add_argument("--image-proof", type=Path)
    parser.add_argument("--proof-raw", type=Path)
    parser.add_argument("--proof-raw-sha256")
    parser.add_argument("--directory", type=Path)
    parser.add_argument("--script")
    parser.add_argument("--script-sha256")
    parser.add_argument("--detach", action="store_true")
    args = parser.parse_args()
    os.umask(0o077)
    try:
        print(json.dumps(prepare(args) if args.action == "prepare" else operate(args)))
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError):
        print(
            json.dumps(
                {
                    "success": False,
                    "error": "PURE_LINUX_CALIBRATION_CONTAINER_REFUSED",
                    "existing_data_or_partial_state_preserved": True,
                    "VM_touched": False,
                }
            )
        )
        raise SystemExit(1) from None
