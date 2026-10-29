"""Offline fixed-size transfer parts; explicit trusted hashes, no credentials or network."""

import argparse
import hashlib
import json
import os
import re
import stat
import zipfile
from pathlib import Path

PART_SIZE = 256 * 1024 * 1024
OBJECTS = {"bundle-manifest.json", "images.tar.gz", "source-runtime-context.tar.gz"}


def digest(path):
    result = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def regular(path):
    value = path.lstat()
    if (
        not stat.S_ISREG(value.st_mode)
        or value.st_uid != os.geteuid()
        or value.st_nlink != 1
    ):
        raise ValueError("OWNED_REGULAR_SINGLE_LINK_REQUIRED")
    return value


def write(path, data):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "wb") as stream:
        stream.write(data)


def check_hash(value):
    if not re.fullmatch(r"[0-9a-f]{64}", value):
        raise ValueError("EXPLICIT_TRUSTED_SHA256_REQUIRED")


def split(source, expected, output):
    check_hash(expected)
    initial = regular(source)
    output.mkdir(mode=0o700)
    whole, parts = hashlib.sha256(), []
    fd = os.open(source, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(fd, "rb") as incoming:
        while True:
            data = incoming.read(PART_SIZE)
            if not data:
                break
            name = "payload.part" + str(len(parts)).zfill(4)
            write(output / name, data)
            whole.update(data)
            parts.append(
                {
                    "name": name,
                    "bytes": len(data),
                    "sha256": hashlib.sha256(data).hexdigest(),
                }
            )
        final = os.fstat(incoming.fileno())
    if (
        not parts
        or whole.hexdigest() != expected
        or (initial.st_ino, initial.st_dev, initial.st_size, initial.st_mtime_ns)
        != (final.st_ino, final.st_dev, final.st_size, final.st_mtime_ns)
    ):
        raise ValueError("SOURCE_CHANGED_OR_COMPLETE_HASH_MISMATCH_PARTS_RETAINED")
    manifest = {
        "schema": 1,
        "original_bytes": initial.st_size,
        "original_sha256": expected,
        "part_size_bytes": PART_SIZE,
        "parts": parts,
        "original_is_not_deleted": True,
    }
    path = output / "parts-manifest.json"
    write(path, (json.dumps(manifest, indent=2) + "\n").encode())
    return {
        "success": True,
        "parts": len(parts),
        "original_bytes": initial.st_size,
        "original_sha256": expected,
        "manifest_sha256": digest(path),
        "manifest_path": str(path),
        "network_or_cloud_operation": False,
    }


def join(directory, expected, output):
    check_hash(expected)
    manifest_path = directory / "parts-manifest.json"
    regular(manifest_path)
    if digest(manifest_path) != expected:
        raise ValueError("PARTS_MANIFEST_HASH_MISMATCH")
    manifest = json.loads(manifest_path.read_text())
    if (
        manifest["schema"] != 1
        or manifest["part_size_bytes"] != PART_SIZE
        or not manifest["parts"]
    ):
        raise ValueError("FIXED_PARTS_SCHEMA_REQUIRED")
    check_hash(manifest["original_sha256"])
    total = 0
    for index, row in enumerate(manifest["parts"]):
        if (
            row["name"] != "payload.part" + str(index).zfill(4)
            or not 0 < row["bytes"] <= PART_SIZE
        ):
            raise ValueError("EXACT_ORDERED_PARTS_REQUIRED")
        path = directory / row["name"]
        if regular(path).st_size != row["bytes"] or digest(path) != row["sha256"]:
            raise ValueError("PART_BYTES_OR_HASH_MISMATCH")
        total += row["bytes"]
    if total != manifest["original_bytes"]:
        raise ValueError("COMPLETE_BYTE_COUNT_MISMATCH")
    fd = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    actual = hashlib.sha256()
    with os.fdopen(fd, "wb") as outgoing:
        for row in manifest["parts"]:
            with (directory / row["name"]).open("rb") as incoming:
                for block in iter(lambda: incoming.read(1024 * 1024), b""):
                    actual.update(block)
                    outgoing.write(block)
    if actual.hexdigest() != manifest["original_sha256"]:
        raise ValueError("COMPLETE_JOINED_HASH_MISMATCH_OUTPUT_RETAINED")
    return {
        "success": True,
        "path": str(output),
        "bytes": total,
        "sha256": actual.hexdigest(),
        "source_parts_deleted": False,
    }


def unpack(source, expected, output):
    check_hash(expected)
    regular(source)
    if digest(source) != expected:
        raise ValueError("TRUSTED_GITHUB_ARTIFACT_ZIP_HASH_MISMATCH")
    with zipfile.ZipFile(source) as archive:
        entries = archive.infolist()
        if len(entries) != 3 or {entry.filename for entry in entries} != OBJECTS:
            raise ValueError("EXACT_THREE_CI_OBJECTS_REQUIRED")
        if any(
            entry.is_dir()
            or entry.file_size > 20 * 1024**3
            or stat.S_ISLNK(entry.external_attr >> 16)
            for entry in entries
        ):
            raise ValueError("UNEXPECTED_ZIP_OBJECT_TYPE_OR_SIZE")
        output.mkdir(mode=0o700)
        for entry in entries:
            fd = os.open(
                output / entry.filename,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                0o600,
            )
            with archive.open(entry) as incoming, os.fdopen(fd, "wb") as outgoing:
                while True:
                    block = incoming.read(1024 * 1024)
                    if not block:
                        break
                    outgoing.write(block)
    return {
        "success": True,
        "output": str(output),
        "bundle_manifest_sha256": digest(output / "bundle-manifest.json"),
        "artifact_zip_sha256_verified": expected,
        "images_loaded_or_services_started": False,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("split", "join", "unpack"))
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    os.umask(0o077)
    try:
        result = {"split": split, "join": join, "unpack": unpack}[args.action](
            args.input, args.sha256, args.output
        )
        print(json.dumps(result))
    except (OSError, ValueError, KeyError, TypeError, zipfile.BadZipFile):
        print(
            json.dumps(
                {
                    "success": False,
                    "error": "OFFLINE_PARTS_TRANSFER_REFUSED",
                    "existing_files_and_partial_outputs_retained": True,
                }
            )
        )
        raise SystemExit(1) from None
