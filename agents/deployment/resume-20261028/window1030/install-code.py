import base64
import hashlib
import json
import os
import zlib
from pathlib import Path

TRANSPORT_SHA = '0710d7d77e80c28733148f2da5dd2f6e072eb69cf78ca3e324cbf28dec42c563'
EXPECTED_SOURCE = "a12e9e70b963bacafda3242bb6d82e53ee912ff1"
EXPECTED_STOP = "2026-10-28T10:30:00Z"
ALLOWED = {"profile.json", "generation.py", "resource-stream.py"}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def unpack(raw):
    if sha(raw) != TRANSPORT_SHA:
        raise ValueError("EXACT_PUBLIC_TRANSPORT_SHA_REQUIRED")
    value = json.loads(raw)
    if (
        value["kind"] != "public-resume-window1030-code-transport-v1"
        or value["source_sha"] != EXPECTED_SOURCE
        or value["stop_utc"] != EXPECTED_STOP
        or value["source_file_count"] != 53
    ):
        raise ValueError("EXACT_FUNCTIONAL_SOURCE_WINDOW_REQUIRED")
    rows = value["files"]
    if len(rows) != 3 or {r["path"] for r in rows} != ALLOWED:
        raise ValueError("EXACT_THREE_PUBLIC_FILES_REQUIRED")
    files = {}
    for row in rows:
        compressed = base64.b64decode(row["gzip_base64"], validate=True)
        if (
            len(compressed) != row["gzip_bytes"]
            or sha(compressed) != row["gzip_sha256"]
        ):
            raise ValueError("COMPRESSED_FILE_MISMATCH")
        if type(row["bytes"]) is not int or not 0 < row["bytes"] < 50000:
            raise ValueError("BOUNDED_FILE_REQUIRED")
        decoder = zlib.decompressobj(31)
        data = decoder.decompress(compressed, row["bytes"] + 1)
        if (
            not decoder.eof
            or decoder.unused_data
            or decoder.unconsumed_tail
            or len(data) != row["bytes"]
            or sha(data) != row["sha256"]
        ):
            raise ValueError("EXACT_PUBLIC_FILE_SHA_REQUIRED")
        files[row["path"]] = data
    profile = json.loads(files["profile.json"])
    if (
        profile["source_sha"] != EXPECTED_SOURCE
        or profile["stop_utc"] != EXPECTED_STOP
        or profile["source_file_count"] != 53
    ):
        raise ValueError("PROFILE_SOURCE_WINDOW_MISMATCH")
    for name in ["generation.py", "resource-stream.py"]:
        if sha(files[name]) != profile["derived_files"][name]["sha256"]:
            raise ValueError("PROFILE_DERIVATION_MISMATCH")
        compile(files[name], name, "exec")
    return files


def install(directory: Path, files):
    if not directory.is_absolute() or directory.parent.resolve() != directory.parent:
        raise ValueError("CANONICAL_NEW_DIRECTORY_REQUIRED")
    directory.mkdir(mode=0o700)
    for name, data in sorted(files.items()):
        if name not in ALLOWED:
            raise ValueError("LITERAL_ALLOWED_BASENAME_REQUIRED")
        fd = os.open(
            directory / name,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
            0o600,
        )
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
    return {
        "directory": str(directory),
        "files": [
            {"path": name, "bytes": len(data), "sha256": sha(data)}
            for name, data in sorted(files.items())
        ],
        "source_sha": EXPECTED_SOURCE,
        "stop_utc": EXPECTED_STOP,
        "cloud_or_SUT_started": False,
        "old_diagnostic_files_modified": False,
    }
