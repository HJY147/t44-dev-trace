"""Verify one fixed PUBLIC code archive completely before exclusive installation."""

import base64
import hashlib
import io
import json
import os
import stat
import sys
import tarfile
from pathlib import Path, PurePosixPath

EXPECTED_BYTES = 64819
EXPECTED_SHA = "0f2aef008a8cbf69fdfaad27a59eea85a3b5c149301a4018aa064ca4d76bd6c1"
REPO_PATH = "agents/backend/window-20261029/runtime-bundle.PUBLIC.tar.gz"
TARGETS = {"profile": "/root/t44-r9/r29-code-01/profile", "p64": "/root/t44-r9/p790-r29-01"}


def need(ok, code):
    if not ok:
        raise ValueError(code)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def verified(response):
    need(len(response) <= 1048576, "BOUNDED_PUBLIC_RESPONSE_REQUIRED")
    if response.lstrip().startswith(b"{"):
        record = json.loads(response)
        need(record.get("type") == "file" and record.get("path") == REPO_PATH and record.get("size") == EXPECTED_BYTES and record.get("encoding") == "base64", "FIXED_PUBLIC_GITHUB_FILE_REQUIRED")
        response = base64.b64decode("".join(record["content"].split()), validate=True)
    need(len(response) == EXPECTED_BYTES and digest(response) == EXPECTED_SHA, "EXACT_PUBLIC_BUNDLE_REQUIRED")
    files = {}
    with tarfile.open(fileobj=io.BytesIO(response), mode="r:gz") as archive:
        members = archive.getmembers()
        need(len(members) == 21, "EXACT_MEMBER_COUNT_REQUIRED")
        for member in members:
            path = PurePosixPath(member.name)
            need(member.isfile() and not path.is_absolute() and ".." not in path.parts and member.name not in files and 0 <= member.size <= 262144, "ONLY_UNIQUE_BOUNDED_REGULAR_MEMBERS")
            raw = archive.extractfile(member).read(member.size + 1)
            need(len(raw) == member.size, "COMPLETE_MEMBER_REQUIRED")
            files[member.name] = raw
    manifest = json.loads(files.pop("install-manifest.PUBLIC.json"))
    need(manifest.get("source_sha") == "f7cdb5fa3b19f84d8ab0d0b042bf51a5b8484e8f" and manifest.get("stop_utc") == "2026-10-29T12:00:00Z" and manifest.get("targets") == TARGETS and manifest.get("no_SUT_or_sessions_or_keys") is True and manifest.get("services_started") is False, "EXACT_SOURCE_TIME_TARGETS_CODE_ONLY")
    need(len(files) == 20 and set(files) == set(manifest["files"]), "EXACT_INSTALL_FILE_SET_REQUIRED")
    for name, raw in files.items():
        path = PurePosixPath(name)
        need(len(path.parts) >= 2 and path.parts[0] in TARGETS and ".." not in path.parts, "SCOPED_PUBLIC_RELATIVE_PATH_REQUIRED")
        row = manifest["files"][name]
        need(len(raw) == row["bytes"] and digest(raw) == row["sha256"], "EVERY_FILE_SHA_AND_SIZE_REQUIRED")
    return files, manifest


def install(response, base=Path("/root/t44-r9")):
    files, manifest = verified(response)
    need(base.is_absolute() and base.is_dir() and base.resolve() == base, "EXISTING_CANONICAL_OWNED_BASE_REQUIRED")
    targets = {"profile": base / "r29-code-01/profile", "p64": base / "p790-r29-01"}
    for path in targets.values():
        need(not path.exists() and not path.is_symlink() and path.parent.resolve() == path.parent, "ALL_NEW_TARGETS_REQUIRED_PRESERVE_OLD_FILES")
    for path in targets.values():
        path.parent.mkdir(parents=True, mode=0o700, exist_ok=True)
        path.mkdir(mode=0o755)
        path.chmod(0o755)
    installed = []
    for name, raw in sorted(files.items()):
        parts = PurePosixPath(name).parts
        path = targets[parts[0]].joinpath(*parts[1:])
        path.parent.mkdir(parents=True, mode=0o755, exist_ok=True)
        need(path.parent.resolve() == path.parent, "CANONICAL_TARGET_PARENT_REQUIRED")
        path.parent.chmod(0o755)
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o444)
        with os.fdopen(fd, "wb") as stream:
            os.fchmod(stream.fileno(), 0o444)
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        need(path.read_bytes() == raw and stat.S_IMODE(path.stat().st_mode) == 0o444, "INSTALLED_FILE_BYTES_AND_PERMISSION_REQUIRED")
        installed.append({"file": name, "bytes": len(raw), "sha256": digest(raw)})
    return {"visibility": "PUBLIC", "kind": "R29_EXACT_PUBLIC_CODE_INSTALLED", "source_sha": manifest["source_sha"], "stop_utc": manifest["stop_utc"], "targets": {key: str(value) for key, value in targets.items()}, "installed_files": len(installed), "installed": installed, "SUT_or_sessions_or_services_started": False}


if __name__ == "__main__":
    os.umask(0o077)
    print(json.dumps(install(Path(sys.argv[1]).read_bytes()), sort_keys=True))
