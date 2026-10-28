"""New v4 source/time profiles; legacy templates and published generations are immutable."""

import argparse
import importlib.util
import json
import os
import re
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
PARENT_SHA = "1846079ab7500e4c9ea4a206a6a01ff92c5b255b3926f7230bcecaf88bb7b004"
KIND = "exact-pinned-production-entry-generation-v4"


def parent():
    import hashlib

    path = HERE.parent / "derive-resume-profile.py"
    if path.is_symlink() or hashlib.sha256(path.read_bytes()).hexdigest() != PARENT_SHA:
        raise ValueError("EXACT_UNCHANGED_PARENT_DERIVER_REQUIRED")
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location("v4_reviewed_parent", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


WRAPPER = """
def operate(args):
    # Stop/status never need an actual-budget receipt or wait behind an operations lock.
    if args.action in {"stop", "status"}:
        return _operate_without_mutex(args)
    lib, value = phase_binding(args.phase_dir, args.binding_sha256)
    budget = budget_module(args.phase_dir)
    valid_window(lib, value["stop_utc"], 600)
    if args.action == "observe-mysql":
        lib.command(["systemctl", "is-active", "--quiet", value["timer_unit"]])
        return budget.observe(args.phase_dir, args.binding_sha256, value,
                              lambda role: live(lib, value, role), args)
    with budget.operation_lock(args.phase_dir, args.binding_sha256):
        if args.action == "probe-budget":
            lib.command(["systemctl", "is-active", "--quiet", value["timer_unit"]])
            return budget.probe(args.phase_dir, args.binding_sha256, value,
                                lambda role: live(lib, value, role))
        if args.action in {"migrate", "idle", "scheduler-token", "scheduler-rotate", "scheduler-start"}:
            budget.verify_runtime_environment(value, lambda role: live(lib, value, role))
            budget.admit(args.phase_dir, args.binding_sha256, value,
                         lambda role: live(lib, value, role), args.budget_receipt,
                         args.budget_receipt_sha256)
        return _operate_without_mutex(args)

"""


def generation_v4(text, module_sha):
    legacy = parent()
    replace = legacy.replacement
    text = replace(text, legacy.NEW_KIND, KIND, 2)
    text = replace(
        text,
        'DOCKER = ["docker", "--context", "default"]',
        'DOCKER = ["docker", "--context", "default"]\nBUDGET_SHA = "'
        + module_sha
        + '"\n\n\n'
        "def budget_module(phase=None):\n"
        "    directory = phase if phase is not None else Path(__file__).resolve().parent\n"
        '    return load(directory / "mysql-budget.py", BUDGET_SHA, "v4_mysql_budget")',
    )
    text = replace(
        text, "args.p_workers not in {7, 16}", "args.p_workers not in {7, 16, 64}"
    )
    text = replace(
        text,
        "    valid_window(lib, args.stop_utc, 600)",
        "    budget = budget_module()\n"
        '    budget.pool_plan("p", args.p_workers, args.p_pool_size, args.p_max_overflow)\n'
        "    valid_window(lib, args.stop_utc, 600)",
    )
    text = replace(
        text,
        '        lib.save(\n            phase / "compose.json",\n'
        "            lib.compose_profile(images, phase, address, tls_port, http_port, workers),\n        )",
        "        composition = lib.compose_profile(images, phase, address, tls_port, http_port, workers)\n"
        '        plan = budget.pool_plan(role, workers, args.p_pool_size if role == "p" else 5,\n'
        '                                args.p_max_overflow if role == "p" else 10)\n'
        '        if role == "p":\n'
        '            composition["services"]["api"]["environment"].update(\n'
        '                T44_DB_POOL_SIZE=str(plan["api_pool_size"]),\n'
        '                T44_DB_MAX_OVERFLOW=str(plan["api_max_overflow"]))\n'
        '        lib.save(phase / "compose.json", composition)\n'
        '        module_path = Path(__file__).resolve().parent / "mysql-budget.py"\n'
        "        if sha(module_path) != BUDGET_SHA:\n"
        '            raise ValueError("EXACT_V4_BUDGET_MODULE_REQUIRED")\n'
        '        lib.write(phase / "mysql-budget.py", module_path.read_bytes())',
    )
    text = replace(
        text,
        '            "api_workers": workers,',
        '            "api_workers": workers,\n            "v4_pool_plan": plan,',
        2,
    )
    text = replace(
        text,
        '            "mysql_max_connections": 384 if role == "p" else 128,',
        '            "mysql_max_connections_configured_prior": 384 if role == "p" else 128,\n'
        '            "mysql_capacity_is_actual_observation": False,',
    )
    text = replace(
        text,
        '                    "compose.json",',
        '                    "compose.json",\n                    "mysql-budget.py",',
    )
    text = replace(text, "def operate(args):", "def _operate_without_mutex(args):")
    text = replace(
        text,
        "    resources = [live(lib, value, r) for r in lib.PERSISTENT]",
        "    resources = [live(lib, value, r) for r in lib.PERSISTENT]\n"
        "    capacity_environment = []\n"
        '    if args.action in {"migrate", "idle", "scheduler-token", "scheduler-rotate", "scheduler-start"}:\n'
        "        capacity_environment = budget_module(phase).verify_runtime_environment(\n"
        "            value, lambda role: live(lib, value, role))",
    )
    text = replace(
        text,
        "        host_https=host,",
        "        host_https=host,\n        capacity_environment_projection=capacity_environment,",
    )
    text = replace(
        text, 'if __name__ == "__main__":', WRAPPER + '\nif __name__ == "__main__":'
    )
    text = replace(
        text,
        '            "prepare",',
        '            "prepare",\n            "probe-budget",\n            "observe-mysql",',
    )
    text = replace(
        text,
        "    args = p.parse_args()",
        '    p.add_argument("--p-pool-size", type=int)\n'
        '    p.add_argument("--p-max-overflow", type=int)\n'
        '    p.add_argument("--budget-receipt", type=Path)\n'
        '    p.add_argument("--budget-receipt-sha256")\n'
        '    p.add_argument("--until-utc")\n'
        '    p.add_argument("--interval-seconds", type=int, default=5)\n'
        "    args = p.parse_args()",
    )
    compile(text, "v4-generation.py", "exec")
    return text


def derive_texts(legacy, source, stop, count):
    if source == "a12e9e70b963bacafda3242bb6d82e53ee912ff1":
        raise ValueError("OLD_A12_IS_NOT_THE_NEW_ROOT_RELEASE_SOURCE")
    texts = legacy.derive_texts(legacy.checked_templates(), source, stop, count)
    module = (HERE / "mysql-budget.py").read_bytes()
    if (HERE / "mysql-budget.py").is_symlink():
        raise ValueError("REGULAR_REVIEWED_V4_BUDGET_MODULE_REQUIRED")
    original_generation_sha = legacy.digest(texts["generation.py"].encode())
    texts["generation.py"] = generation_v4(
        texts["generation.py"], legacy.digest(module)
    )
    stream = legacy.replacement(texts["resource-stream.py"], legacy.NEW_KIND, KIND)
    texts["resource-stream.py"] = legacy.replacement(
        stream,
        original_generation_sha,
        legacy.digest(texts["generation.py"].encode()),
    )
    texts["mysql-budget.py"] = module.decode()
    for name, text in texts.items():
        compile(text, name, "exec")
    return texts


def derive(args):
    legacy = parent()
    now = datetime.now(timezone.utc)  # noqa: UP017 -- cloud Python 3.10.
    legacy.deadline(args.stop_utc, now)
    if not re.fullmatch(r"[0-9a-f]{40}", args.source or ""):
        raise ValueError("EXPLICIT_NEW_COMPLETE_SOURCE_COMMIT_REQUIRED")
    builder = legacy.reviewed_builder()
    if (
        builder.git(args.repository, "rev-parse", args.source + "^{commit}")
        .decode()
        .strip()
        != args.source
    ):
        raise ValueError("EXACT_ROOT_RELEASE_GIT_COMMIT_REQUIRED")
    files = builder.tree(args.repository, args.source, builder.SOURCE_PATHS)
    frozen = builder.compare_frozen(
        builder.tree(args.repository, builder.BASE, builder.FROZEN),
        builder.tree(args.repository, args.source, builder.FROZEN),
    )
    texts = derive_texts(legacy, args.source, args.stop_utc, len(files))
    legacy.new_directory(args.output)
    metadata = {}
    for name, text in texts.items():
        raw = text.encode()
        legacy.write_new(args.output / name, raw)
        metadata[name] = {"bytes": len(raw), "sha256": legacy.digest(raw)}
    profile = {
        "kind": "explicit-new-source-time-pool-profile-v4",
        "created_utc": now.isoformat(),
        "source_sha": args.source,
        "stop_utc": args.stop_utc,
        "source_file_count": len(files),
        "source_file_set_sha256": legacy.digest(
            json.dumps(files, sort_keys=True, separators=(",", ":")).encode()
        ),
        "frozen_file_set_sha256": frozen["file_set_sha256"],
        "original_template_sha256": legacy.TEMPLATES,
        "parent_deriver_sha256": PARENT_SHA,
        "derived_files": metadata,
        "generation_kind": KIND,
        "old_helpers_modified": False,
        "cloud_or_SUT_executed": False,
        "final_source_CI_approval_is_root_responsibility": True,
        "mysql_max_connections_planned_not_observed": True,
        "phase_order": [
            "prepare-files",
            "arm-timer",
            "infra-only",
            "actual-probe-budget",
            "migrate-and-business-admission",
        ],
    }
    raw = (json.dumps(profile, indent=2, sort_keys=True) + "\n").encode()
    legacy.write_new(args.output / "profile.json", raw)
    return {
        "success": True,
        "profile": str(args.output / "profile.json"),
        "profile_sha256": legacy.digest(raw),
        "derived_files": metadata,
        "source_sha": args.source,
        "stop_utc": args.stop_utc,
        "cloud_or_SUT_executed": False,
    }


def package(args):
    legacy = parent()
    if (
        args.profile.is_symlink()
        or legacy.digest(args.profile.read_bytes()) != args.profile_sha256
    ):
        raise ValueError("ROOT_PINNED_V4_PROFILE_SHA_REQUIRED")
    profile = json.loads(args.profile.read_bytes())
    if profile["kind"] != "explicit-new-source-time-pool-profile-v4":
        raise ValueError("V4_NEW_PROFILE_ONLY")
    for name, record in profile["derived_files"].items():
        path = args.profile.parent / name
        if path.is_symlink() or legacy.digest(path.read_bytes()) != record["sha256"]:
            raise ValueError("EXACT_V4_DERIVED_PROFILE_REQUIRED")
    legacy.new_directory(args.output)
    path = args.profile.parent / "backend-upgrade.py"
    spec = importlib.util.spec_from_file_location("v4_pinned_source_builder", path)
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    result = builder.prepare(
        SimpleNamespace(repository=args.repository, output=args.output / "source")
    )
    files = {
        name: (args.output / "source" / name).read_bytes()
        for name in (
            "source-backend.tar.gz",
            "source-manifest.json",
            "frozen-equality.json",
            "Dockerfile",
        )
    }
    files["backend-upgrade.py"] = path.read_bytes()
    if sum(map(len, files.values())) >= 1024 * 1024:
        raise ValueError("FIVE_FILE_ARTIFACT_SIZE_BOUND")
    artifact = args.output / "source-artifact.zip"
    fd = os.open(artifact, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "w+b") as stream:
        with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for name, raw in sorted(files.items()):
                archive.writestr(name, raw)
        stream.flush()
        os.fsync(stream.fileno())
    return {
        "success": True,
        "source_sha": profile["source_sha"],
        "artifact": str(artifact),
        "bytes": artifact.stat().st_size,
        "sha256": legacy.digest(artifact.read_bytes()),
        "manifest_sha256": result["manifest_sha256"],
        "cloud_or_SUT_executed": False,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="action", required=True)
    for action in ("derive", "package"):
        command = commands.add_parser(action)
        command.add_argument("--repository", type=Path, required=True)
        command.add_argument("--output", type=Path, required=True)
        if action == "derive":
            command.add_argument("--source", required=True)
            command.add_argument("--stop-utc", required=True)
        else:
            command.add_argument("--profile", type=Path, required=True)
            command.add_argument("--profile-sha256", required=True)
    arguments = parser.parse_args()
    os.umask(0o077)
    print(
        json.dumps(
            derive(arguments) if arguments.action == "derive" else package(arguments)
        )
    )
