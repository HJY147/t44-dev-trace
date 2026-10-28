"""Separate source935 factory profile; immutable original Compose/binding/timer remain the stop anchor."""

import argparse
import calendar
import hashlib
import json
import os
import re
import stat
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

SOURCE = "935ab5b93bea788672c2b4a088c79cfeed848954"
TOOLS = {
    "810_stage.py": "8f0dbec80e168a8dbac7f3707b467d16c9146fe7937b7c5c2f6825b20bf966f6",
    "810_net_snapshot.py": "dd776e1fe6c94aa005fa6b00734a6f8cebe54b24a9352917dbea7a771682552b",
}
DOCKER = ["docker", "--context", "default"]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def private(path, directory=False):
    info = path.lstat()
    if (
        path.resolve() != path
        or info.st_uid != os.geteuid()
        or stat.S_IMODE(info.st_mode) != (0o700 if directory else 0o600)
        or not (stat.S_ISDIR(info.st_mode) if directory else stat.S_ISREG(info.st_mode))
    ):
        raise ValueError("OWNED_PRIVATE_CANONICAL_OBJECT_REQUIRED")


def write(path, data):
    descriptor = os.open(
        path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600
    )
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(data)


def save(path, value):
    write(path, (json.dumps(value, indent=2) + "\n").encode())


def stamp():
    return datetime.now(timezone.utc).isoformat()  # noqa: UP017 - Ubuntu22 Python3.10


def command(argv, timeout=120):
    env = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith(("DOCKER_", "COMPOSE_", "T44_", "MYSQL_", "RABBITMQ_"))
    }
    return subprocess.run(
        list(map(str, argv)), capture_output=True, check=True, timeout=timeout, env=env
    ).stdout


def base_phase(path, expected):
    private(path, True)
    private(path / "binding.json")
    if (
        not re.fullmatch(r"[0-9a-f]{64}", expected)
        or sha(path / "binding.json") != expected
    ):
        raise ValueError("EXACT_ORIGINAL_PHASE_BINDING_SHA_REQUIRED")
    value = json.loads((path / "binding.json").read_text())
    if (
        value["kind"] != "isolated-cloud-campaign"
        or value["phase"] != "p"
        or value["source_sha"] != SOURCE
    ):
        raise ValueError("SOURCE935_P_DIAGNOSTIC_PHASE_ONLY")
    for name, digest in value["file_hashes"].items():
        if sha(path / name) != digest:
            raise ValueError("ORIGINAL_PHASE_FILES_CHANGED")
    # Read only the explicit two non-secret selectors. No password, DSN or environment dump.
    selectors = {}
    for line in (path / "application.env").read_text().splitlines():
        key, sep, selected = line.partition("=")
        if sep and key in {"MYSQL_DATABASE", "MYSQL_USER"}:
            if key in selectors:
                raise ValueError("DUPLICATE_DATABASE_SELECTOR")
            selectors[key] = selected
    if (
        selectors.get("MYSQL_DATABASE") != value["database"]
        or selectors.get("MYSQL_USER") != value["database"] + "_app"
    ):
        raise ValueError("ORIGINAL_PRIVATE_DATABASE_SELECTORS_DIFFER")
    return value, selectors


def diagnostic_env(base, selectors, mode):
    if mode not in {"all", "header"}:
        raise ValueError("EXPLICIT_HEADER_OR_ALL_SAMPLE_MODE_REQUIRED")
    return {
        "T44_DIAG_ALLOW": "source935-development-only",
        "T44_DIAG_PRODUCT_SHA": SOURCE,
        "T44_DIAG_MODULE_SHA256": TOOLS["810_stage.py"],
        "T44_DIAG_DATABASE": base["database"],
        "T44_DIAG_HOST": "mysql",
        "T44_DIAG_PORT": "3306",
        "T44_DIAG_USER": selectors["MYSQL_USER"],
        "T44_DIAG_OUTPUT": "/var/lib/t44-diagnostic",
        "T44_DIAG_LIMIT": "10000",
        "T44_DIAG_SAMPLE_MODE": mode,
    }


def render_overlay(base_compose, env, output):
    old = base_compose["services"]["api"]
    argv = list(old["command"])
    if (
        argv.count("t44.api:app") != 1
        or "--factory" in argv
        or old["environment"]["PYTHONPATH"] != "/app/backend"
        or old.get("volumes")
    ):
        raise ValueError("EXACT_UNINSTRUMENTED_API_PREIMAGE_REQUIRED")
    position = argv.index("t44.api:app")
    argv[position : position + 1] = ["810_stage:app_factory", "--factory"]
    return {
        "services": {
            "api": {
                "command": argv,
                "environment": {
                    "PYTHONPATH": "/app/backend:/opt/t44-diagnostic",
                    **env,
                },
                "volumes": [
                    {
                        "type": "bind",
                        "source": str(output / "mounted"),
                        "target": "/opt/t44-diagnostic",
                        "read_only": True,
                    },
                    {
                        "type": "bind",
                        "source": str(output / "output"),
                        "target": "/var/lib/t44-diagnostic",
                    },
                ],
                "labels": {
                    "io.t44.diagnostic.kind": "source935-factory-only",
                    "io.t44.diagnostic.stage-sha256": TOOLS["810_stage.py"],
                    "io.t44.diagnostic.net-sha256": TOOLS["810_net_snapshot.py"],
                    "io.t44.diagnostic.production-entrypoint": "false",
                },
            }
        }
    }


def prepare(args):
    base, selectors = base_phase(args.base_phase, args.base_binding_sha256)
    if args.action == "env-plan":
        private(args.output.parent, True)
        save(args.output, diagnostic_env(base, selectors, args.sample_mode))
        return {
            "success": True,
            "explicit_diag_env_path": str(args.output),
            "sha256": sha(args.output),
            "passwords_or_DSNS_written": False,
        }
    private(args.diag_env)
    env = json.loads(args.diag_env.read_text())
    if env != diagnostic_env(base, selectors, env.get("T44_DIAG_SAMPLE_MODE")):
        raise ValueError("EXACT_DIAGNOSTIC_ENV_ALLOWLIST_AND_DATABASE_REQUIRED")
    for name, expected in TOOLS.items():
        file = args.public_tools_dir / name
        info = file.lstat()
        if (
            not stat.S_ISREG(info.st_mode)
            or info.st_nlink != 1
            or file.is_symlink()
            or sha(file) != expected
        ):
            raise ValueError("EXACT_TWO_PUBLIC_DIAGNOSTIC_SOURCES_REQUIRED")
    private(args.output.parent, True)
    args.output.mkdir(mode=0o700)
    (args.output / "receipts").mkdir(mode=0o700)
    for name in ["mounted", "output"]:
        directory = args.output / name
        directory.mkdir(mode=0o700)
        os.chown(directory, 10001, 10001)
    for name in TOOLS:
        target = args.output / "mounted" / name
        write(target, (args.public_tools_dir / name).read_bytes())
        os.chown(target, 10001, 10001)
    original = json.loads((args.base_phase / "compose.json").read_text())
    overlay = render_overlay(original, env, args.output)
    save(args.output / "diagnostic-env.json", env)
    save(args.output / "overlay.json", overlay)
    write(args.output / "controller.py", Path(__file__).read_bytes())
    value = {
        "kind": "source935-diagnostic-factory-overlay",
        "created_utc": stamp(),
        "source_sha": SOURCE,
        "base_phase": str(args.base_phase),
        "base_binding_sha256": args.base_binding_sha256,
        "base_compose_sha256": sha(args.base_phase / "compose.json"),
        "base_project": base["project"],
        "stop_utc_unchanged": base["stop_utc"],
        "stop_timer_unchanged": base["timer_unit"],
        "database_unchanged": base["database"],
        "image_ids_unchanged": base["image_ids"],
        "config_ids_unchanged": base["config_ids"],
        "api_workers_unchanged": base["api_workers"],
        "public_tool_hashes": TOOLS,
        "private_env_sha256": sha(args.output / "diagnostic-env.json"),
        "overlay_sha256": sha(args.output / "overlay.json"),
        "controller_sha256": sha(args.output / "controller.py"),
        "entrypoint": "810_stage:app_factory --factory",
        "production_entrypoint": False,
        "session_or_business_packet_mounted": False,
        "original_phase_files_modified": False,
        "services_started": False,
    }
    save(args.output / "binding.json", value)
    return {
        "success": True,
        "diagnostic_profile": str(args.output),
        "binding_sha256": sha(args.output / "binding.json"),
        "overlay_sha256": value["overlay_sha256"],
        "entrypoint": value["entrypoint"],
        "production_entrypoint": False,
        "original_phase_modified": False,
        "services_started": False,
    }


def profile(path):
    private(path, True)
    private(path / "binding.json")
    value = json.loads((path / "binding.json").read_text())
    if (
        value["kind"] != "source935-diagnostic-factory-overlay"
        or value["source_sha"] != SOURCE
    ):
        raise ValueError("EXACT_DIAGNOSTIC_PROFILE_REQUIRED")
    for name, key in [
        ("overlay.json", "overlay_sha256"),
        ("controller.py", "controller_sha256"),
        ("diagnostic-env.json", "private_env_sha256"),
    ]:
        if sha(path / name) != value[key]:
            raise ValueError("DIAGNOSTIC_PROFILE_FILE_CHANGED")
    for name, expected in TOOLS.items():
        if sha(path / "mounted" / name) != expected:
            raise ValueError("MOUNTED_PUBLIC_TOOL_CHANGED")
    return value


def receipt(path, action, **fields):
    value = {"utc": stamp(), "action": action, "receipt_id": uuid4().hex, **fields}
    save(path / "receipts" / (value["receipt_id"] + ".json"), value)
    return value


def api_identity(argv, base, overlay):
    ids = command([*argv, "ps", "--all", "--quiet", "api"]).decode().split()
    if not ids:
        return {"absent": True}
    if len(ids) != 1 or not re.fullmatch(r"[0-9a-f]{64}", ids[0]):
        raise ValueError("ONE_EXACT_DIAGNOSTIC_API_CONTAINER_REQUIRED")
    text = (
        command(
            [
                *DOCKER,
                "inspect",
                "--format",
                "{{json .Id}}\t{{json .Image}}\t{{json .Config.Labels}}\t{{json .Config.Cmd}}\t{{json .State.Running}}",
                ids[0],
            ]
        )
        .decode()
        .strip()
    )
    identity, image, labels, cmd, running = [
        json.loads(part) for part in text.split("\t")
    ]
    if (
        identity != ids[0]
        or image not in {base["image_ids"]["backend"], base["config_ids"]["backend"]}
        or labels.get("com.docker.compose.project") != base["project"]
        or labels.get("com.docker.compose.service") != "api"
        or labels.get("io.t44.diagnostic.stage-sha256") != TOOLS["810_stage.py"]
        or cmd != overlay["services"]["api"]["command"]
    ):
        raise ValueError("DIAGNOSTIC_API_IMAGE_COMMAND_OR_LABELS_CHANGED")
    return {
        "container_id": identity,
        "actual_image_id": image,
        "command": cmd,
        "running": running,
        "production_entrypoint": False,
    }


def operate(args):
    path = args.profile
    value = profile(path)
    base_dir = Path(value["base_phase"])
    base, _ = base_phase(base_dir, value["base_binding_sha256"])
    argv = [
        *DOCKER,
        "compose",
        "--env-file",
        base_dir / "application.env",
        "--file",
        base_dir / "compose.json",
        "--file",
        path / "overlay.json",
        "--project-name",
        base["project"],
    ]
    if args.action in {"config", "up"}:
        deadline = calendar.timegm(
            time.strptime(base["stop_utc"], "%Y-%m-%dT%H:%M:%SZ")
        )
        if time.time() + 120 >= deadline:
            raise ValueError("ORIGINAL_WORKLOAD_WINDOW_CLOSED_NO_EXTENSION")
        command(["systemctl", "is-active", "--quiet", base["timer_unit"]])
        command([*argv, "config", "--quiet"])
        if args.action == "up":
            command(
                [
                    *argv,
                    "up",
                    "-d",
                    "--wait",
                    "--no-build",
                    "--pull",
                    "never",
                    "api",
                    "consumer",
                    "web",
                    "tls-gateway",
                ],
                timeout=180,
            )
    elif args.action == "stop-api":
        api_identity(argv, base, json.loads((path / "overlay.json").read_text()))
        command([*argv, "stop", "--timeout", "30", "api"], timeout=90)
    actual_api = api_identity(
        argv, base, json.loads((path / "overlay.json").read_text())
    )
    states = command([*argv, "ps", "--format", "json"]).decode()
    return receipt(
        path,
        args.action,
        success=True,
        source_sha=SOURCE,
        entrypoint=value["entrypoint"],
        production_entrypoint=False,
        original_binding_sha256=value["base_binding_sha256"],
        original_stop_anchor_unchanged=True,
        actual_compose_ps=states,
        actual_diagnostic_api=actual_api,
        test_or_performance_acceptance_claim=False,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "action", choices=("env-plan", "prepare", "config", "up", "status", "stop-api")
    )
    parser.add_argument("--base-phase", type=Path)
    parser.add_argument("--base-binding-sha256")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--public-tools-dir", type=Path)
    parser.add_argument("--diag-env", type=Path)
    parser.add_argument("--sample-mode", choices=("header", "all"), default="all")
    parser.add_argument("--profile", type=Path)
    args = parser.parse_args()
    os.umask(0o077)
    try:
        print(
            json.dumps(
                prepare(args)
                if args.action in {"prepare", "env-plan"}
                else operate(args)
            )
        )
    except (
        OSError,
        ValueError,
        KeyError,
        TypeError,
        subprocess.SubprocessError,
    ) as error:
        failure = None
        if args.profile and (args.profile / "receipts").is_dir():
            failure = args.profile / "receipts" / ("failure-" + uuid4().hex + ".json")
            row = {
                "error_class": type(error).__name__,
                "reason": str(error),
                "partial_state_preserved": True,
            }
            if isinstance(error, subprocess.CalledProcessError):
                row.update(
                    stdout=error.stdout.decode(errors="replace")
                    if error.stdout
                    else "",
                    stderr=error.stderr.decode(errors="replace")
                    if error.stderr
                    else "",
                )
            save(failure, row)
        print(
            json.dumps(
                {
                    "success": False,
                    "error": "SOURCE935_DIAGNOSTIC_OVERLAY_REFUSED",
                    "private_failure_path": str(failure) if failure else None,
                    "original_phase_modified": False,
                }
            )
        )
        raise SystemExit(1) from None
