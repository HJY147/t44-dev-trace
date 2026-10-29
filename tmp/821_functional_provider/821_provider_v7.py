"""Bounded coordinator provider; only explicit PUBLIC scope requests are inputs."""

import argparse
import hashlib
import json
import os
import re
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path

PROJECT = Path("/Users/yang/Desktop/nothing/软件开发大作业")
PUBLIC = PROJECT / "tmp/829_independent_acceptance_20261025/execution-v7-fresh/PUBLIC"
ROOT_PRIVATE = PROJECT / ".agent-worktrees/.runtime/continuation-20261025"


def load(path):
    return json.loads(path.read_text())


def private_json(path, value):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "w") as stream:
        json.dump(value, stream, indent=2)
        stream.write("\n")


def instant(value):
    return datetime.fromisoformat(value).timestamp()


def remaining(stop_utc, stop_mono, maximum):
    value = min(maximum, stop_utc - time.time(), stop_mono - time.monotonic())
    if value <= 0:
        raise TimeoutError("Provider deadline exhausted; no next action")
    return value


def validate(request, grant, started, expected_nonce):
    context = request.get("context", {})
    expected = {
        "tool_freeze_sha256": grant["tool_freeze_sha256"],
        "native_runtime_identity": grant["build"]["runtime_identity"],
        "source_sha": grant["build"]["source_sha"],
        "phase": "functional",
        "resource_ids": grant["isolated_resource_ids"],
        "supervisor_nonce": expected_nonce,
    }
    if not expected_nonce or any(context.get(k) != v for k, v in expected.items()):
        raise ValueError("Active environment context mismatch")
    ids = request.get("project_ids")
    if request.get("kind") != "SERVICE_SCOPE_REQUEST" or request.get("scope") != [
        "escalation:write"
    ]:
        raise ValueError("Exact service scope required")
    if (
        not isinstance(ids, list)
        or len(ids) != 1
        or type(ids[0]) is not int
        or not 1 <= ids[0] <= 4294967295
    ):
        raise ValueError("One actual positive project identifier required")
    if not re.fullmatch("[a-f0-9]{48}", request.get("nonce", "")):
        raise ValueError("Unexpected nonce")
    requested = instant(request["requested_utc"])
    if (
        requested < started - 2
        or requested > time.time() + 2
        or time.time() >= instant(grant["expires_at"])
    ):
        raise ValueError("Request outside active provider window")
    return ids[0]


def phase_request_anchor(supervisor):
    return instant(supervisor["launch_clock"]["utc"])


def main(grant_path, supervisor_receipt):
    grant, manifest = load(grant_path), load(PUBLIC / "manifest.PUBLIC.json")
    if grant.get("admitted") is not True or grant.get("phase") != "functional":
        raise ValueError("Explicit functional grant required")
    if grant["tool_freeze_sha256"] != manifest["tool_freeze_sha256"]:
        raise ValueError("Frozen tool mismatch")
    if (
        supervisor_receipt.parent != PUBLIC / "runtime"
        or supervisor_receipt.is_symlink()
    ):
        raise ValueError("Explicit current PUBLIC supervisor receipt required")
    supervisor = load(supervisor_receipt)
    if (
        supervisor.get("tool_freeze_sha256") != grant["tool_freeze_sha256"]
        or instant(supervisor["expires_at"]) != instant(grant["expires_at"])
        or not re.fullmatch("[a-f0-9]{48}", supervisor.get("nonce", ""))
    ):
        raise ValueError("Supervisor receipt identity mismatch")
    for key in ("supervisor_pid", "child_pid"):
        if type(supervisor.get(key)) is not int or supervisor[key] <= 0:
            raise ValueError("Supervisor process identity missing")
        os.kill(supervisor[key], 0)
    helper = PUBLIC / "handoff.PUBLIC.py"
    if hashlib.sha256(helper.read_bytes()).hexdigest() != next(
        item["sha256"]
        for item in manifest["core_files"]
        if item["path"] == "PUBLIC/handoff.PUBLIC.py"
    ):
        raise ValueError("Public sealer mismatch")
    config_path = ROOT_PRIVATE / "functional-provider-v7-binding.json"
    if config_path.is_symlink() or config_path.stat().st_mode & 0o077:
        raise ValueError("Private exact coordinator binding required")
    config_bytes = config_path.read_bytes()
    if hashlib.sha256(config_bytes).hexdigest() != grant["provider_binding_sha256"]:
        raise ValueError("Exact provider binding hash mismatch")
    config = json.loads(config_bytes)
    if set(config) != {
        "run_dir",
        "source_sha",
        "runtime_identity",
        "controller_sha256",
    }:
        raise ValueError("Exact provider configuration fields required")
    run = Path(config["run_dir"])
    allowed = (
        PROJECT / ".agent-worktrees/.runtime/native-functional-campaign-20261025/runs"
    )
    if run.parent != allowed or run.is_symlink():
        raise ValueError("Exact functional campaign runtime required")
    if (
        Path(grant["build"]["build_manifest_path"]).parent != run
        or config["runtime_identity"] != grant["build"]["runtime_identity"]
    ):
        raise ValueError("Exact provider runtime mismatch")
    if config["source_sha"] != grant["build"]["source_sha"]:
        raise ValueError("Provider source binding mismatch")
    controller = run / "scheduler-control.py"
    if (
        hashlib.sha256(controller.read_bytes()).hexdigest()
        != config["controller_sha256"]
    ):
        raise ValueError("Deployment controller mismatch")
    binding = load(run / "application-binding.json")
    if binding["source_commit"] != grant["build"]["source_sha"]:
        raise ValueError("CLI source mismatch")
    env = os.environ.copy()
    env.update(load(ROOT_PRIVATE / "functional-db-v7/application-env.json"))
    env["PYTHONPATH"] = str(Path(binding["application_root"]) / "backend")
    python = binding["python"]
    parent = ROOT_PRIVATE / "provisioned"
    parent.mkdir(mode=0o700, exist_ok=True)
    if parent.is_symlink() or parent.stat().st_mode & 0o077:
        raise ValueError("Private approved provisioned parent required")
    target = parent / ("functional-v7-" + supervisor["nonce"])
    target.mkdir(mode=0o700, exist_ok=False)
    if target.is_symlink() or target.stat().st_mode & 0o077:
        raise ValueError("Private fresh provider target required")
    mono_before = time.monotonic()
    started = time.time()
    stop = min(started + 1800, instant(grant["expires_at"]))
    stop_mono = min(
        mono_before + max(0, stop - started), supervisor["hard_deadline_monotonic"]
    )
    remaining(stop, stop_mono, 1)
    private_json(
        target / "provider-start.json",
        {
            "started_utc": datetime.now(UTC).isoformat(),
            "grant_path": str(grant_path),
            "tool": manifest["tool_freeze_sha256"],
            "max_scopes": 40,
            "supervisor_receipt": str(supervisor_receipt),
            "supervisor_nonce": supervisor["nonce"],
        },
    )
    seen, results = set(), []
    while time.time() < stop and time.monotonic() < stop_mono and len(seen) < 40:
        for path in sorted((PUBLIC / "handoff").glob("*.request.PUBLIC.json")):
            if len(seen) >= 40 or time.time() >= stop or time.monotonic() >= stop_mono:
                break
            if path.name in seen:
                continue
            seen.add(path.name)
            row = {
                "request_file": path.name,
                "started_utc": datetime.now(UTC).isoformat(),
            }
            try:
                if path.is_symlink() or path.stat().st_size > 32768:
                    raise ValueError("Unexpected PUBLIC request path/size")
                request = load(path)
                project_id = validate(
                    request,
                    grant,
                    phase_request_anchor(supervisor),
                    supervisor["nonce"],
                )
                if path.name != request["nonce"] + ".request.PUBLIC.json":
                    raise ValueError("Nonce filename mismatch")
                item = target / request["nonce"]
                item.mkdir(mode=0o700, exist_ok=False)
                token_file = item / "token.json"
                command = [
                    python,
                    "-m",
                    "t44.cli",
                    "service-token",
                    "--name",
                    "i829_" + request["nonce"][:24],
                    "--project-id",
                    str(project_id),
                    "--token-file",
                    str(token_file),
                ]
                row["stage"] = "production_service_cli"
                created = subprocess.run(
                    command,
                    cwd=binding["application_root"],
                    env=env,
                    capture_output=True,
                    check=False,
                    timeout=remaining(stop, stop_mono, 30),
                )
                if created.returncode:
                    raise RuntimeError("Scoped production CLI failed")
                credential = load(token_file)
                expiry = datetime.fromtimestamp(
                    instant(credential["expires_at"]), UTC
                ).strftime("%Y-%m-%dT%H:%M:%SZ")
                row["stage"] = "owned_scheduler_scope"
                applied = subprocess.run(
                    [
                        python,
                        str(controller),
                        "replace",
                        "--run-dir",
                        str(run),
                        "--project-id",
                        str(project_id),
                        "--token-file",
                        str(token_file),
                        "--token-expires-utc",
                        expiry,
                    ],
                    capture_output=True,
                    check=False,
                    timeout=remaining(stop, stop_mono, 45),
                )
                if applied.returncode:
                    private_json(
                        item / "apply-failure.json",
                        {
                            "exit": applied.returncode,
                            "stdout": applied.stdout.decode(errors="replace"),
                            "stderr": applied.stderr.decode(errors="replace"),
                        },
                    )
                    raise RuntimeError("Owned scheduler scope application failed")
                private_json(
                    item / "scheduler-application.json", json.loads(applied.stdout)
                )
                reply_credential = {
                    "token": credential["access_token"],
                    "project_ids": [project_id],
                    "scope": ["escalation:write"],
                    "applied_to": ["scheduler"],
                    "provisioned_utc": datetime.now(UTC).isoformat(),
                    "provider": "source-bound production CLI and owned scheduler replacement",
                    "prior_project_periodic_scanning": "replaced by this exact scope",
                }
                reply = PUBLIC / "handoff" / (request["nonce"] + ".sealed.PUBLIC.json")
                if reply.exists() or reply.is_symlink():
                    raise ValueError("Sealed reply already exists")
                staged_reply = item / "sealed-staged.json"
                row["stage"] = "public_credential_seal"
                sealed = subprocess.run(
                    [
                        python,
                        str(helper),
                        "--request",
                        str(path),
                        "--output",
                        str(staged_reply),
                    ],
                    input=json.dumps(reply_credential).encode(),
                    capture_output=True,
                    check=False,
                    timeout=remaining(stop, stop_mono, 20),
                )
                if sealed.returncode:
                    raise RuntimeError("Public credential sealer failed")
                remaining(stop, stop_mono, 1)
                os.link(staged_reply, reply)
                row.update(
                    status="provisioned and sealed",
                    project_ids=[project_id],
                    session_id=credential["session_id"],
                )
            except Exception as error:  # noqa: BLE001 -- keep only sanitized failed provisioning receipts
                row.update(
                    status="failed retained; no automatic retry",
                    exception_class=type(error).__name__,
                )
            row["ended_utc"] = datetime.now(UTC).isoformat()
            results.append(row)
            private_json(target / (path.name + ".provider.json"), row)
            print(json.dumps(row), flush=True)
        time.sleep(0.1)
    private_json(
        target / "provider-final.json",
        {"ended_utc": datetime.now(UTC).isoformat(), "requests": results},
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--grant", type=Path, required=True)
    parser.add_argument("--supervisor-receipt", type=Path, required=True)
    args = parser.parse_args()
    main(args.grant, args.supervisor_receipt)
