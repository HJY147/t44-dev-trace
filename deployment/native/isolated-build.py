"""Emit a new immutable native identity snapshot; never an image attestation."""

import argparse
import hashlib
import importlib.util
import json
import os
import platform
import re
from datetime import UTC, datetime
from pathlib import Path


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def emit(run, output):
    info = (run / "application-binding.json").lstat()
    if info.st_uid != os.getuid() or info.st_mode & 0o077 or run.is_symlink():
        raise ValueError("PRIVATE_BINDING_REQUIRED")
    bound = json.loads((run / "application-binding.json").read_text())
    path = run / "application-controller.py"
    if path.is_symlink() or digest(path.read_bytes()) != bound["application_controller_sha256"]:
        raise ValueError("APPLICATION_CONTROLLER_CHANGED")
    spec = importlib.util.spec_from_file_location("isolated_bound_application", path)
    app = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(app)
    module = app.controller(run)
    bound = app.binding(run, module)
    original = module.read(run / "manifest.json")
    artifact = run / "artifact-manifest.json"
    module.private(artifact)
    archive = Path(bound["source_archive_path"])
    module.private(archive)
    if digest(archive.read_bytes()) != bound["archive_sha256"]:
        raise ValueError("ACTUAL_SOURCE_ARCHIVE_CHANGED")
    python = Path(bound["python"])
    executable_sha = digest(python.resolve().read_bytes())
    if executable_sha != original["python_executable_sha256"]:
        raise ValueError("PYTHON_EXECUTABLE_CHANGED")
    artifact_sha = digest(artifact.read_bytes())
    inventory = original["python_inventory"]
    runtime = {
        "source_sha": bound["source_commit"],
        "artifact_manifest_sha256": artifact_sha,
        "python_executable_sha256": executable_sha,
        "dependency_lock_sha256": bound["dependency_lock_sha256"],
    }
    runtime_id = "native-sha256:" + digest(canonical(runtime))
    processes, launch = [], []

    def add(role, record):
        started = (
            datetime.strptime(record["started"], "%a %b %d %H:%M:%S %Y")
            .replace(tzinfo=datetime.now().astimezone().tzinfo)
            .astimezone(UTC)
            .isoformat()
        )
        processes.append(
            {
                "role": role,
                "pid": record["pid"],
                "started_utc": started,
                "runtime_identity": runtime_id,
                "artifact_manifest_sha256": artifact_sha,
                "uid": record["uid"],
                "pgid": record["pgid"],
                "command_sha256": record["command_sha256"],
            }
        )

    for role in ("api", "consumer", "scheduler"):
        record, actual = module.owned(run, role)
        if actual is not None:
            add(role, record)
            launch.append({"role": role, "argv": record["argv"]})
    registered = run / "state/api-children.json"
    if registered.exists():
        for record in module.read(registered)["children"]:
            actual = module.broker_module(run).process_identity(record["pid"])
            if actual is not None and app.child_match(record, actual):
                add("api-worker" if record["worker"] else "api-resource-tracker", record)
    broker = module.broker_for(run)
    text, version_receipt = broker.execute("rabbitmqctl", ["eval", "application:get_key(rabbit,vsn)."])
    match = re.fullmatch(r'\{ok,"([0-9.]+)"\}', text.strip())
    if not match:
        raise ValueError("ACTUAL_BROKER_VERSION_UNRECOGNIZED")
    schema = module.read(run / "secrets/application-environment.json")["T44_DATABASE"]
    value = {
        "kind": "native",
        "image_digest": None,
        "source_sha": bound["source_commit"],
        "source_archive_sha256": digest(archive.read_bytes()),
        "artifact_manifest_sha256": artifact_sha,
        "dependency_lock_sha256": bound["dependency_lock_sha256"],
        "built_utc": bound["created_at_utc"],
        "runtime_identity": runtime_id,
        "launch_argv_sha256": digest(canonical(launch)),
        "launch_argv_canonicalization": "UTF8 JSON;sorted keys;no whitespace;actual credential-free argv arrays",
        "python": {
            "version": inventory["python"],
            "architecture": platform.machine(),
            "executable_sha256": executable_sha,
            "distribution_inventory_sha256": digest(canonical(inventory["distributions"])),
        },
        "processes": processes,
        "data_services": [
            {
                "kind": "mysql",
                "version": "8.4.11",
                "version_provenance": "root-supplied observed existing protected server",
                "endpoint": "127.0.0.1:13306",
                "schema": schema,
                "user": schema,
            },
            {
                "kind": "rabbitmq",
                "version": match[1],
                "endpoint": "127.0.0.1:" + str(module.PORTS["amqp"]),
                "vhost": broker.manifest["vhost"],
                "version_receipt_id": version_receipt["receipt_id"],
            },
        ],
        "provenance_status": "root-supplied native metadata;not image attestation",
        "scheduler_pending_scope": not any(v["role"] == "scheduler" for v in processes),
        "captured_utc": module.stamp(),
        "global_application_stop_utc": "2026-10-25T08:46:30Z",
        "source_archive_path": str(archive),
        "artifact_manifest_path": str(artifact),
        "ca_path": str(run / "tls/ca.pem"),
    }
    if output.parent != run or output.exists() or output.is_symlink():
        raise ValueError("NEW_OWNED_BUILD_OUTPUT_REQUIRED")
    module.save(output, value)
    return {
        "success": True,
        "native_build_path": str(output),
        "sha256": digest(output.read_bytes()),
        "source_sha": value["source_sha"],
        "source_archive_sha256": value["source_archive_sha256"],
        "artifact_manifest_sha256": artifact_sha,
        "runtime_identity": runtime_id,
        "process_count": len(processes),
        "scheduler_pending_scope": value["scheduler_pending_scope"],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    os.umask(0o077)
    try:
        print(json.dumps(emit(args.run_dir, args.output)))
    except (OSError, ValueError, RuntimeError, KeyError):
        print(json.dumps({"success": False, "error": "NATIVE_BUILD_IDENTITY_FAILED"}))
        raise SystemExit(1) from None
