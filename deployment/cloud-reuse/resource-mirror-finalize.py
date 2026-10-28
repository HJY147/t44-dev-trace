"""Verify the sealed P16 mirror against APP's public seal, then original status/owned stop."""

import argparse
import hashlib
import json
import os
import stat
import subprocess
import time
from pathlib import Path

DIRECTORY = Path("/root/t44-r9/resource-mirror-r28p16-02")
BINDING = "97497b2d935ac0c443c8825caf84af9cf351f89a993948598d4424f6b48cf27d"
CONTROLLER = "e5b0324e1576f901cbacb1ba9b973096c6b575318cc9f336a6f7183ce94ca115"
SOURCE = "a12e9e70b963bacafda3242bb6d82e53ee912ff1"


def read(path):
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(fd, "rb") as stream:
        info = os.fstat(stream.fileno())
        if (
            not stat.S_ISREG(info.st_mode)
            or info.st_uid != os.geteuid()
            or stat.S_IMODE(info.st_mode) != 0o600
        ):
            raise ValueError("OWNED_REGULAR_0600_INPUT_REQUIRED")
        return stream.read()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def verify(directory, expected_bytes, expected_sha):
    binding_raw = read(directory / "binding.json")
    if (
        sha(binding_raw) != BINDING
        or sha(read(directory / "controller.py")) != CONTROLLER
    ):
        raise ValueError("EXACT_MIRROR_BINDING_CONTROLLER_REQUIRED")
    binding = json.loads(binding_raw)
    final_raw = read(directory / "mirror-final.json")
    final = json.loads(final_raw)
    if final["transport_complete"] is not True or final["from_offset_zero"] is not True:
        raise ValueError("COMPLETE_OFFSET_ZERO_TRANSPORT_REQUIRED")
    digest = hashlib.sha256()
    prefix = hashlib.sha256()
    size, header, tail = 0, None, None
    fd = os.open(directory / "app-raw.jsonl", os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(fd, "rb") as stream:
        info = os.fstat(stream.fileno())
        if (
            not stat.S_ISREG(info.st_mode)
            or info.st_uid != os.geteuid()
            or stat.S_IMODE(info.st_mode) != 0o600
        ):
            raise ValueError("OWNED_REGULAR_MIRROR_RAW_REQUIRED")
        for raw in stream:
            if tail or not raw.endswith(b"\n"):
                raise ValueError("COMPLETE_FINAL_LAST_RECORD_REQUIRED")
            row = json.loads(raw)
            if header is None:
                if (
                    row.get("kind") != "resource_header"
                    or row.get("source_sha") != SOURCE
                    or row.get("stream_id") != binding["stream_id"]
                ):
                    raise ValueError("EXACT_STREAM_SOURCE_HEADER_REQUIRED")
                header = row
            elif row.get("kind") == "resource_header":
                raise ValueError("SINGLE_STREAM_HEADER_REQUIRED")
            if row.get("kind") == "resource_final":
                if (
                    row["prefix_bytes"] != size
                    or row["prefix_sha256"] != prefix.hexdigest()
                ):
                    raise ValueError("EXACT_FINAL_PREFIX_REQUIRED")
                tail = row
            else:
                prefix.update(raw)
            digest.update(raw)
            size += len(raw)
        after = os.fstat(stream.fileno())
        if (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns) != (
            after.st_dev,
            after.st_ino,
            after.st_size,
            after.st_mtime_ns,
        ):
            raise ValueError("MIRROR_CHANGED_DURING_VERIFICATION")
    if (
        not tail
        or size != expected_bytes
        or digest.hexdigest() != expected_sha
        or final["raw_bytes"] != size
        or final["raw_sha256"] != digest.hexdigest()
    ):
        raise ValueError("APP_SEAL_MIRROR_WHOLE_BYTES_SHA_MISMATCH")
    return {
        "kind": "operator-verified-mirror-final-public",
        "transport_complete": True,
        "from_offset_zero": True,
        "raw_bytes": size,
        "raw_sha256": digest.hexdigest(),
        "mirror_final_sha256": sha(final_raw),
        "binding_sha256": BINDING,
        "final_reason": tail.get("reason"),
        "actual_coverage": final.get("actual_coverage"),
        "business_or_acceptance_verdict": None,
        "raw_or_data_deleted": False,
    }


def main(args):
    if os.geteuid() != 0 or DIRECTORY.resolve() != DIRECTORY:
        raise ValueError("ROOT_AND_EXACT_CANONICAL_MIRROR_REQUIRED")
    if (
        len(args.app_sha256) != 64
        or any(c not in "0123456789abcdef" for c in args.app_sha256)
        or args.app_bytes <= 0
    ):
        raise ValueError("ACTUAL_APP_SEALED_BYTES_SHA_REQUIRED")
    deadline = time.monotonic() + 45
    while not (DIRECTORY / "mirror-final.json").exists():
        if time.monotonic() >= deadline:
            raise ValueError("MIRROR_FINAL_NOT_READY_RAW_PRESERVED_NO_STOP")
        time.sleep(0.25)
    result = verify(DIRECTORY, args.app_bytes, args.app_sha256)
    fd = os.open(
        DIRECTORY / "operator-verified-final.PUBLIC.json",
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
        0o600,
    )
    with os.fdopen(fd, "w") as stream:
        json.dump(result, stream, sort_keys=True)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    print(
        json.dumps(
            {key: value for key, value in result.items() if key != "actual_coverage"}
        ),
        flush=True,
    )
    for action in ("status", "stop"):
        raw = subprocess.run(
            [
                "/usr/bin/python3",
                str(DIRECTORY / "controller.py"),
                action,
                "--directory",
                str(DIRECTORY),
                "--binding-sha256",
                BINDING,
            ],
            capture_output=True,
            check=True,
            timeout=40,
        ).stdout
        value = json.loads(raw)
        print(
            json.dumps(
                {
                    key: value.get(key)
                    for key in [
                        "action",
                        "unit",
                        "observed_before_pid",
                        "observed_after_pid",
                        "owned_process_stopped",
                        "raw_or_data_deleted",
                    ]
                }
            ),
            flush=True,
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--app-bytes", type=int, required=True)
    parser.add_argument("--app-sha256", required=True)
    args = parser.parse_args()
    main(args)
