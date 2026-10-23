"""Issue private scheduler credentials through the real backend CLI, never stdout tokens."""

import argparse
import fcntl
import json
import os
import stat
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

CREDENTIAL = Path("/run/t44-secrets/scheduler-token.json")


def private_metadata(path: Path, *, require_fresh: bool = True) -> dict:
    metadata = path.lstat()
    if not stat.S_ISREG(metadata.st_mode) or stat.S_IMODE(metadata.st_mode) != 0o600:
        raise ValueError("credential must be a private regular file")
    content = json.loads(path.read_text())
    if not isinstance(content["access_token"], str) or not 32 <= len(content["access_token"]) <= 512:
        raise ValueError("credential content is invalid")
    if type(content["session_id"]) is not int or content["session_id"] <= 0:
        raise ValueError("credential session is invalid")
    expiry = datetime.fromisoformat(content["expires_at"].replace("Z", "+00:00"))
    if expiry.tzinfo is None or (require_fresh and expiry <= datetime.now(UTC)):
        raise ValueError("credential is expired")
    return {"session_id": content["session_id"], "expires_at": content["expires_at"]}


def backend(*arguments: str) -> dict:
    result = subprocess.run([sys.executable, "-m", "t44.cli", *arguments],
                            capture_output=True, text=True, check=False)
    if result.returncode:
        raise RuntimeError("backend credential command failed")
    return json.loads(result.stdout)


def issue(projects: list[int], *, name: str, rotate: bool, credential: Path = CREDENTIAL) -> dict:
    if not projects or any(type(value) is not int or not 1 <= value <= 4294967295 for value in projects):
        raise ValueError("explicit project scopes required")
    if not credential.parent.is_dir():
        raise ValueError("private credential volume is absent")
    parent = credential.parent.stat()
    if parent.st_uid != os.getuid() or stat.S_IMODE(parent.st_mode) & 0o077:
        raise ValueError("private credential volume ownership/mode is invalid")
    descriptor = os.open(credential.parent / ".credential-admin.lock",
                         os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    temporary = credential.parent / f".scheduler-token-{uuid4().hex}.json"
    published = False
    issued_session = None
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX)
        previous = private_metadata(credential, require_fresh=False) if credential.exists() else None
        if rotate != bool(previous):
            raise ValueError("initial issuance must not overwrite; rotation requires an existing credential")
        command = ["service-token", "--name", name, "--token-file", str(temporary)]
        for project in sorted(set(projects)):
            command += ["--project-id", str(project)]
        result = backend(*command)
        issued_session = result["session_id"]
        current = private_metadata(temporary)
        if current["session_id"] != result["session_id"]:
            raise ValueError("credential/session mismatch")
        if rotate:
            os.replace(temporary, credential)
        else:
            os.link(temporary, credential)
            temporary.unlink()
        published = True
        directory = os.open(credential.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
        revoked = False
        already_inactive = False
        if previous:
            count = backend("revoke-session", "--session-id", str(previous["session_id"]))["revoked_sessions"]
            if type(count) is not int or count not in (0, 1):
                raise RuntimeError("previous credential revocation was not confirmed")
            revoked, already_inactive = count == 1, count == 0
        return {**current, "credential_written": True, "rotated": bool(previous),
                "previous_session_revoked": revoked, "previous_session_already_inactive": already_inactive}
    finally:
        # Only this invocation's unpublished private temporary file can be removed.
        if not published:
            temporary.unlink(missing_ok=True)
            if issued_session is not None:
                try:
                    backend("revoke-session", "--session-id", str(issued_session))
                except (OSError, RuntimeError, ValueError):
                    pass  # The command already fails; no secret or false success is emitted.
        os.close(descriptor)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", default="scheduler")
    parser.add_argument("--project-id", type=int, action="append", required=True)
    parser.add_argument("--rotate", action="store_true")
    args = parser.parse_args()
    try:
        print(json.dumps(issue(args.project_id, name=args.name, rotate=args.rotate)))
    except Exception:  # noqa: BLE001 -- suppress private file/driver details and fail closed
        print(json.dumps({"error": "SERVICE_CREDENTIAL_FAILED"}), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
