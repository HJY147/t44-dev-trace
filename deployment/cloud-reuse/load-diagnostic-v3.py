"""Owned15minute tool-only runtime; exact RW data + approved PUBLIC11 RO, no SUT mounts."""

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

RUNTIME_HELPER_SHA = "f30af6894f8fa1dab707115942c7e218c6177b13a27161e7a38936dd4f9b98c4"
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


def public_package(path, name, expected):
    if (
        path.resolve() != path
        or name != "FILES.json"
        or not re.fullmatch(r"[0-9a-f]{64}", expected)
    ):
        raise ValueError("EXACT_PUBLIC_FILES_JSON_AND_OUTER_SHA_REQUIRED")
    root = path.lstat()
    if (
        not stat.S_ISDIR(root.st_mode)
        or root.st_uid != os.geteuid()
        or stat.S_IMODE(root.st_mode) != 0o555
    ):
        raise ValueError("PUBLIC_PACKAGE_ROOT_0555_OWNED_REQUIRED")
    manifest = path / name
    if manifest.is_symlink() or sha(manifest) != expected:
        raise ValueError("PUBLIC_FILES_OUTER_SHA_MISMATCH")
    value = json.loads(manifest.read_text())
    entries = value["files"]
    if not isinstance(entries, list) or len(entries) != 11:
        raise ValueError("EXACT_ELEVEN_PUBLIC_JSON_ENTRIES_REQUIRED")
    canonical = hashlib.sha256(
        json.dumps(
            entries, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode()
    ).hexdigest()
    if (
        not re.fullmatch(r"[0-9a-f]{64}", value.get("package_source_sha256", ""))
        or canonical != value["package_source_sha256"]
    ):
        raise ValueError("PUBLIC_CANONICAL_PACKAGE_SOURCE_COMMITMENT_MISMATCH")
    declared, sizes = {}, {}
    for entry in entries:
        if set(entry) != {"path", "bytes", "sha256"}:
            raise ValueError("EXACT_PUBLIC_JSON_ENTRY_FIELDS_REQUIRED")
        relative = entry["path"]
        parts = Path(relative)
        if (
            not re.fullmatch(r"[A-Za-z0-9_./-]+", relative)
            or parts.is_absolute()
            or ".." in parts.parts
            or str(parts) != relative
            or relative in declared
            or relative == name
            or not re.fullmatch(r"[0-9a-f]{64}", entry["sha256"])
            or type(entry["bytes"]) is not int
            or entry["bytes"] < 0
        ):
            raise ValueError("EXACT_UNIQUE_PUBLIC_RELATIVE_NAMES_AND_BYTES_REQUIRED")
        declared[relative], sizes[relative] = entry["sha256"], entry["bytes"]
    if "entry.py" not in declared:
        raise ValueError("PUBLIC_ENTRY_PY_REQUIRED")
    present = set()
    for file in [path, *path.rglob("*")]:
        info = file.lstat()
        if info.st_uid != os.geteuid():
            raise ValueError("PUBLIC_PACKAGE_OWNERSHIP_CHANGED")
        if stat.S_ISDIR(info.st_mode):
            if stat.S_IMODE(info.st_mode) != 0o555:
                raise ValueError("PUBLIC_DIRECTORIES_0555_REQUIRED")
        elif (
            stat.S_ISREG(info.st_mode)
            and info.st_nlink == 1
            and stat.S_IMODE(info.st_mode) == 0o444
        ):
            present.add(str(file.relative_to(path)))
        else:
            raise ValueError("PUBLIC_REGULAR_SINGLE_LINK_0444_NO_SYMLINK_REQUIRED")
    if present != {*declared, name}:
        raise ValueError("PUBLIC_PACKAGE_EXACT_TWELVE_FILE_SET_REQUIRED")
    for relative, digest in declared.items():
        if (path / relative).stat().st_size != sizes[relative] or sha(
            path / relative
        ) != digest:
            raise ValueError("PUBLIC_PACKAGE_FILE_BYTES_OR_SHA_MISMATCH")
    return {
        "path": str(path),
        "manifest_name": name,
        "manifest_sha256": expected,
        "package_source_sha256": canonical,
        "file_hashes": declared,
        "file_bytes": sizes,
        "mount_read_only": True,
        "entry_sha256": declared["entry.py"],
        "scope": "root-approved PUBLIC tool-only package; no private cases or SUT source",
    }


def prepare(args):
    if os.geteuid() != 0 or not re.fullmatch(r"[a-z][a-z0-9]{5,15}", args.run_id):
        raise ValueError("ROOT_AND_FRESH_RUNID_REQUIRED")
    private(args.runtime_helper)
    if sha(args.runtime_helper) != RUNTIME_HELPER_SHA:
        raise ValueError("EXACT_OFFLINE_TOOL_RUNTIME_BUILDER_REQUIRED")
    spec = importlib.util.spec_from_file_location(
        "approved_tool_runtime", args.runtime_helper
    )
    runtime_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runtime_module)
    runtime, verified = runtime_module.verify_binding(
        args.runtime_binding, args.runtime_binding_sha256, args.image_proof
    )
    if runtime["builder_sha256"] != RUNTIME_HELPER_SHA:
        raise ValueError("RUNTIME_NOT_BUILT_BY_APPROVED_FACTORY")
    package = public_package(
        args.public_package, args.files_manifest_name, args.files_manifest_sha256
    )
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
    value = {
        "kind": "pure-synthetic-linux-calibration-v3",
        "created_utc": stamp(),
        "name": "t44-cal805-" + args.run_id,
        "run_id": args.run_id,
        "image_alias": runtime["image_alias"],
        "actual_image_id": runtime["actual_image_id"],
        "runtime_config_id": runtime["runtime_config_id"],
        "proof_raw_sha256": runtime["base_proof_raw_sha256"],
        "runtime_binding_sha256": args.runtime_binding_sha256,
        "runtime_dockerfile_sha256": runtime["dockerfile_sha256"],
        "runtime_verification": verified,
        "public_package": package,
        "data_dir": str(data),
        "port": 18205,
        "max_seconds": 900,
        "controller_sha256": sha(args.output / "controller.py"),
        "business_env_or_DB_mounts": False,
        "mount_roles": {
            "/diagnostic": "new isolated data RW",
            "/tool805": "approved exact PUBLIC11 RO",
        },
        "initial_data_empty": True,
        "container_started": False,
        "old_82e4_executed_or_modified": False,
        "old_603_v2_executed_or_modified": False,
    }
    save(args.output / "binding.json", value)
    return {
        "success": True,
        "directory": str(args.output),
        "binding_sha256": sha(args.output / "binding.json"),
        "runtime_image_alias": value["image_alias"],
        "runtime_actual_image_id": value["actual_image_id"],
        "public_manifest_sha256": package["manifest_sha256"],
        "public_files_verified": 11,
        "data_dir": str(data),
        "container_started": False,
        "script_or_calibration_outcome": None,
    }


def binding(directory):
    private(directory, True)
    private(directory / "binding.json")
    value = json.loads((directory / "binding.json").read_text())
    if (
        value["kind"] != "pure-synthetic-linux-calibration-v3"
        or not re.fullmatch(r"t44-cal805-[a-z][a-z0-9]{5,15}", value["name"])
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
        or image not in {value["actual_image_id"], value["runtime_config_id"]}
        or labels.get("io.t44.calibration.run") != value["run_id"]
        or labels.get("io.t44.calibration.proof") != value["proof_raw_sha256"]
        or labels.get("io.t44.calibration.runtime") != value["runtime_binding_sha256"]
        or labels.get("io.t44.calibration.public")
        != value["public_package"]["manifest_sha256"]
    ):
        raise ValueError("OWNED_CONTAINER_IMAGE_OR_LABELS_CHANGED")
    binds = [row for row in mounts if row["Type"] == "bind"]
    extras = [row for row in mounts if row["Type"] != "bind"]
    by_target = {row["Destination"]: row for row in binds}
    if (
        len(binds) != 2
        or set(by_target) != {"/diagnostic", "/tool805"}
        or by_target["/diagnostic"]["Source"] != value["data_dir"]
        or by_target["/diagnostic"].get("RW") is not True
        or by_target["/tool805"]["Source"] != value["public_package"]["path"]
        or by_target["/tool805"].get("RW") is not False
        or any(row["Type"] != "tmpfs" or row["Destination"] != "/tmp" for row in extras)
        or ports != {"18205/tcp": [{"HostIp": "127.0.0.1", "HostPort": "18205"}]}
    ):
        raise ValueError("EXACT_RW_DATA_RO_PUBLIC_AND_LOOPBACK_MOUNTS_REQUIRED")
    return record, running


def operate(args):
    directory = args.directory
    value = binding(directory)
    if args.action == "start":
        public_package(
            Path(value["public_package"]["path"]),
            value["public_package"]["manifest_name"],
            value["public_package"]["manifest_sha256"],
        )
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
            "--label",
            "io.t44.calibration.runtime=" + value["runtime_binding_sha256"],
            "--label",
            "io.t44.calibration.public=" + value["public_package"]["manifest_sha256"],
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
            "--mount",
            "type=bind,src="
            + value["public_package"]["path"]
            + ",dst=/tool805,readonly",
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
            RW_data_mount=value["data_dir"],
            RO_public_mount=value["public_package"]["path"],
            public_manifest_sha256=value["public_package"]["manifest_sha256"],
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


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("prepare", "start", "status", "stop"))
    parser.add_argument("--output", type=Path)
    parser.add_argument("--run-id")
    parser.add_argument("--image-proof", type=Path)
    parser.add_argument("--runtime-helper", type=Path)
    parser.add_argument("--runtime-binding", type=Path)
    parser.add_argument("--runtime-binding-sha256")
    parser.add_argument("--public-package", type=Path)
    parser.add_argument("--files-manifest-name", default="FILES.json")
    parser.add_argument("--files-manifest-sha256")
    parser.add_argument("--directory", type=Path)
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
