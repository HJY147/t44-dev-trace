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
PUBLIC = PROJECT / "tmp/829_independent_acceptance_20261025/PUBLIC"
ROOT_PRIVATE = PROJECT / ".agent-worktrees/.runtime/continuation-20261025"
RUN = (
    PROJECT
    / ".agent-worktrees/.runtime/native-isolated-20261025/runs/isolated_20261025_dc0fb7a3b96c471e"
)
CONTROLLER_SHA = "508cf4df0541189b4aae06cce0d1dab3d35cb6c334cedc31d416e6ea5cf40abb"


def load(path):
    return json.loads(path.read_text())


def private_json(path, value):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "w") as stream:
        json.dump(value, stream, indent=2)
        stream.write("\n")


def instant(value):
    return datetime.fromisoformat(value).timestamp()


def validate(request, grant, started):
    context = request.get("context", {})
    expected = {
        "tool_freeze_sha256": grant["tool_freeze_sha256"],
        "native_runtime_identity": grant["build"]["runtime_identity"],
        "source_sha": grant["build"]["source_sha"],
        "phase": "functional",
        "resource_ids": grant["isolated_resource_ids"],
    }
    if any(context.get(k) != v for k, v in expected.items()) or not context.get(
        "supervisor_nonce"
    ):
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


def main(grant_path):
    grant, manifest = load(grant_path), load(PUBLIC / "manifest.PUBLIC.json")
    if grant.get("admitted") is not True or grant.get("phase") != "functional":
        raise ValueError("Explicit functional grant required")
    if grant["tool_freeze_sha256"] != manifest["tool_freeze_sha256"]:
        raise ValueError("Frozen tool mismatch")
    helper = PUBLIC / "handoff.PUBLIC.py"
    if (
        hashlib.sha256(helper.read_bytes()).hexdigest()
        != manifest["public_file_inventory"][helper.name]["sha256"]
    ):
        raise ValueError("Public sealer mismatch")
    controller = RUN / "scheduler-control.py"
    if hashlib.sha256(controller.read_bytes()).hexdigest() != CONTROLLER_SHA:
        raise ValueError("Deployment controller mismatch")
    binding = load(RUN / "application-binding.json")
    if binding["source_commit"] != grant["build"]["source_sha"]:
        raise ValueError("CLI source mismatch")
    env = os.environ.copy()
    env.update(load(ROOT_PRIVATE / "independent-functional-db/application-env.json"))
    env["PYTHONPATH"] = str(Path(binding["application_root"]) / "backend")
    python = binding["python"]
    target = ROOT_PRIVATE / "provisioned"
    target.mkdir(mode=0o700, exist_ok=False)
    if target.is_symlink() or target.stat().st_mode & 0o077:
        raise ValueError("Private fresh provider target required")
    started, stop = time.time(), min(time.time() + 1800, instant(grant["expires_at"]))
    stop_mono = time.monotonic() + max(0, stop - time.time())
    private_json(
        target / "provider-start.json",
        {
            "started_utc": datetime.now(UTC).isoformat(),
            "grant_path": str(grant_path),
            "tool": manifest["tool_freeze_sha256"],
            "max_scopes": 40,
        },
    )
    seen, results = set(), []
    while time.time() < stop and time.monotonic() < stop_mono and len(seen) < 40:
        for path in sorted((PUBLIC / "handoff").glob("*.request.PUBLIC.json")):
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
                project_id = validate(request, grant, started)
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
                created = subprocess.run(
                    command,
                    cwd=binding["application_root"],
                    env=env,
                    capture_output=True,
                    check=False,
                    timeout=30,
                )
                if created.returncode:
                    raise RuntimeError("Scoped production CLI failed")
                credential = load(token_file)
                expiry = datetime.fromtimestamp(
                    instant(credential["expires_at"]), UTC
                ).strftime("%Y-%m-%dT%H:%M:%SZ")
                applied = subprocess.run(
                    [
                        python,
                        str(controller),
                        "replace",
                        "--run-dir",
                        str(RUN),
                        "--project-id",
                        str(project_id),
                        "--token-file",
                        str(token_file),
                        "--token-expires-utc",
                        expiry,
                    ],
                    capture_output=True,
                    check=False,
                    timeout=45,
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
                sealed = subprocess.run(
                    [
                        python,
                        str(helper),
                        "--request",
                        str(path),
                        "--output",
                        str(reply),
                    ],
                    input=json.dumps(reply_credential).encode(),
                    capture_output=True,
                    check=False,
                    timeout=20,
                )
                if sealed.returncode:
                    raise RuntimeError("Public credential sealer failed")
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
    main(parser.parse_args().grant)
