"""LOAD opaque-only import, never decrypts sessions or launches a matrix."""

import argparse
import base64
import hashlib
import json
import os
from pathlib import Path


def checked(path, wanted):
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(fd, "rb") as stream:
        raw = stream.read(100001)
    if len(raw) > 100000 or hashlib.sha256(raw).hexdigest() != wanted:
        raise ValueError("EXACT_PUBLIC_OR_OPAQUE_INPUT_REQUIRED")
    return json.loads(raw)


def put(path, value):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "wb") as stream:
        stream.write(value)
        stream.flush()
        os.fsync(stream.fileno())


def receive(config, item, kind):
    work = Path(config["work_dir"])
    if not work.is_absolute() or work.parent.resolve() != work.parent:
        raise ValueError("CANONICAL_NEW_LOAD_WORK_DIRECTORY_REQUIRED")
    if kind == "metadata":
        m = item["metadata"]
        if (
            m["source_sha"] != config["source_sha"]
            or m["phase_binding_sha256"] != config["binding_sha256"]
            or m["root_grant_sha256"] != config["root_grant_sha256"]
            or type(m["part_count"]) is not int
            or not 1 <= m["part_count"] <= 4
        ):
            raise ValueError("OPAQUE_METADATA_ACTUAL_RUN_DIFFERS")
        work.mkdir(mode=0o700)
        put(work / "metadata.PUBLIC.json", json.dumps(m, separators=(",", ":")).encode())
    else:
        m = json.loads((work / "metadata.PUBLIC.json").read_bytes())
        data = base64.b64decode(item["data"], validate=True)
        if (
            type(item["index"]) is not int
            or not 0 <= item["index"] < m["part_count"]
            or item["parts"] != m["part_count"]
            or len(data) != item["bytes"]
            or len(data) > 11800
            or hashlib.sha256(data).hexdigest() != item["sha256"]
        ):
            raise ValueError("OPAQUE_PART_METADATA_OR_SHA_DIFFERS")
        put(work / ("part-" + str(item["index"]) + ".OPAQUE"), data)
    return {"kind": "OPAQUE_IMPORT_ONLY_NOT_MATRIX", "work_dir": str(work), "operation": kind}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("metadata", "part"))
    for name in ("configuration", "input"):
        parser.add_argument("--" + name, type=Path, required=True)
        parser.add_argument("--" + name + "-sha256", required=True)
    args = parser.parse_args()
    config = checked(args.configuration, args.configuration_sha256)
    if (
        config["kind"] != "P790_F7_LOAD_CONFIGURATION_V4"
        or config["source_sha"] != "f7cdb5fa3b19f84d8ab0d0b042bf51a5b8484e8f"
    ):
        raise ValueError("EXACT_F7_LOAD_CONFIGURATION_REQUIRED")
    print(json.dumps(receive(config, checked(args.input, args.input_sha256), args.operation)))


if __name__ == "__main__":
    os.umask(0o077)
    main()
