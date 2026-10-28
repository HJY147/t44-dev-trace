"""Thin pinned e551 bridge budget adapter; never invokes scope provisioning."""

import hashlib
import importlib
import json
import sys
from contextlib import contextmanager
from pathlib import Path

BRIDGE = "e5512dd264a2199bb599742ea72f671d184ab5e41a3d102bed498d49b244d5f7"
HELPER = "305f9eaeea96b0ef882ec17a457f51852bafc8c34b5fe2e47056bd12625dd82d"


def modules(directory):
    directory = Path(directory)
    if not directory.is_absolute() or directory.resolve() != directory:
        raise ValueError("CANONICAL_APPROVED_SCOPE_BRIDGE_REQUIRED")
    raw = (directory / "manifest.PUBLIC.json").read_bytes()
    if hashlib.sha256(raw).hexdigest() != BRIDGE:
        raise ValueError("APPROVED_E551_BRIDGE_ONLY")
    for name, item in json.loads(raw)["files"].items():
        path = directory / name
        if (
            path.resolve() != path
            or hashlib.sha256(path.read_bytes()).hexdigest() != item["sha256"]
        ):
            raise ValueError("PINNED_SCOPE_BRIDGE_MODULE_CHANGED")
    sys.path.insert(0, str(directory))
    result = importlib.import_module("bridge_common"), importlib.import_module("bridge_backend")
    if any(Path(value.__file__).resolve().parent != directory for value in result):
        raise ValueError("CACHED_BRIDGE_MODULE_FROM_OTHER_DIRECTORY")
    return result


@contextmanager
def admitted(args, binding, stop_utc):
    common, adapter = modules(args.scope_bridge_dir)
    if binding["file_hashes"]["mysql-budget.py"] != HELPER:
        raise ValueError("PINNED_V4_BUDGET_HELPER_REQUIRED")
    receipt = common.read(args.budget_receipt, args.budget_receipt_sha256, private=True)
    clock = common.Clock()
    deadline = common.Deadline(clock, common.stamp(stop_utc))
    backend = adapter.DockerBackend(args.phase_dir, args.scope_bridge_dir, BRIDGE, clock)
    backend.deadline, backend.binding = deadline, binding
    backend.authority = {
        "app_phase_dir": str(args.phase_dir),
        "budget_receipt_path": str(args.budget_receipt),
        "documents": {
            "binding": {"sha256": args.binding_sha256},
            "mysql_budget": common.document(receipt),
        },
    }
    adapter.budget_receipt_binding(backend.authority, binding)
    with backend.phase_operation_lock(deadline) as budget:
        proof = backend.admit_budget(budget, deadline)
        deadline.remaining()
        yield proof
        deadline.remaining()


def verify_roles(args, binding, grant, stop_utc):
    common, adapter = modules(args.scope_bridge_dir)
    clock = common.Clock()
    backend = adapter.DockerBackend(args.phase_dir, args.scope_bridge_dir, BRIDGE, clock)
    backend.binding = binding
    backend.deadline = common.Deadline(clock, common.stamp(stop_utc))
    for role, wanted in grant["roles"].items():
        ids = (
            backend.output(
                adapter.DOCKER
                + [
                    "ps",
                    "--all",
                    "--quiet",
                    "--no-trunc",
                    "--filter",
                    "label=com.docker.compose.project=" + binding["project"],
                    "--filter",
                    "label=com.docker.compose.service=" + role,
                ]
            )
            .decode()
            .split()
        )
        if wanted == {"absent": True}:
            if ids:
                raise ValueError("ROOT_ROLE_ABSENCE_DIFFERS")
            continue
        if ids != [wanted["container_id"]]:
            raise ValueError("ROOT_ROLE_CONTAINER_DIFFERS")
        row = backend.inspect(ids[0])
        actual = {
            "container_id": row["Id"],
            "image_id": row["Image"],
            "running": row["State"]["Running"],
            "restart_count": row["RestartCount"],
        }
        if actual != wanted:
            raise ValueError("ROOT_ROLE_IDENTITY_OR_STATE_DIFFERS")
