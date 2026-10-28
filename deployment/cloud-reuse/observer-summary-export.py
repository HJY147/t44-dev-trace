"""Read one approved, already sealed observer summary; bounded chunk transport only."""

import argparse
import base64
import gzip
import hashlib
import json
import math
import os
import stat
import zlib
from pathlib import Path

SOURCE = Path("/root/t44-r9/diag-summary-01.json")
RAW_BYTES = 66110
RAW_SHA = "d554caf63e38238ab1b3e75abc2823b670b078d60c84a9097b031c03044e3053"
CHUNK_CHARS = 12000
KIND = "approved-observer-summary-chunk-v1"


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def read_checked(path, expected_bytes, expected_sha):
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode) or before.st_size != expected_bytes:
            raise ValueError("APPROVED_REGULAR_SUMMARY_SIZE_REQUIRED")
        chunks, remaining = [], expected_bytes + 1
        while remaining:
            block = os.read(descriptor, min(65536, remaining))
            if not block:
                break
            chunks.append(block)
            remaining -= len(block)
        after = os.fstat(descriptor)

        def identity(value):
            return (
                value.st_dev,
                value.st_ino,
                value.st_size,
                value.st_mtime_ns,
                value.st_ctime_ns,
            )

        if identity(before) != identity(after):
            raise ValueError("SUMMARY_CHANGED_DURING_READ")
        raw = b"".join(chunks)
        if len(raw) != expected_bytes or digest(raw) != expected_sha:
            raise ValueError("APPROVED_FULL_SUMMARY_SHA_REQUIRED")
        return raw
    finally:
        os.close(descriptor)


def encode(raw, index):
    if len(raw) != RAW_BYTES or digest(raw) != RAW_SHA:
        raise ValueError("APPROVED_SUMMARY_ONLY")
    compressed = gzip.compress(raw, mtime=0)
    encoded = base64.b64encode(compressed).decode("ascii")
    total = math.ceil(len(encoded) / CHUNK_CHARS)
    if type(index) is not int or not 0 <= index < total:
        raise ValueError("CHUNK_INDEX_OUT_OF_RANGE")
    offset = index * CHUNK_CHARS
    value = encoded[offset : offset + CHUNK_CHARS]
    return {
        "kind": KIND,
        "source": str(SOURCE),
        "raw_bytes": RAW_BYTES,
        "raw_sha256": RAW_SHA,
        "gzip_bytes": len(compressed),
        "gzip_sha256": digest(compressed),
        "base64_chars": len(encoded),
        "chunk_chars_limit": CHUNK_CHARS,
        "index": index,
        "chunks": total,
        "offset": offset,
        "chunk_chars": len(value),
        "chunk_sha256": digest(value.encode("ascii")),
        "base64": value,
        "source_changed": False,
        "formal_acceptance": False,
    }


def decode(rows):
    if not rows:
        raise ValueError("ALL_CHUNKS_REQUIRED")
    first = rows[0]
    fields = (
        "kind",
        "source",
        "raw_bytes",
        "raw_sha256",
        "gzip_bytes",
        "gzip_sha256",
        "base64_chars",
        "chunk_chars_limit",
        "chunks",
        "source_changed",
        "formal_acceptance",
    )
    if (
        first.get("kind") != KIND
        or first.get("source") != str(SOURCE)
        or first.get("raw_bytes") != RAW_BYTES
        or first.get("raw_sha256") != RAW_SHA
        or first.get("chunk_chars_limit") != CHUNK_CHARS
        or first.get("source_changed") is not False
        or first.get("formal_acceptance") is not False
        or type(first.get("base64_chars")) is not int
        or not 1 <= first["base64_chars"] <= 2 * RAW_BYTES
        or type(first.get("gzip_bytes")) is not int
        or not 1 <= first["gzip_bytes"] <= RAW_BYTES + 1024
        or type(first.get("chunks")) is not int
        or first["chunks"] != math.ceil(first["base64_chars"] / CHUNK_CHARS)
        or len(rows) != first["chunks"]
    ):
        raise ValueError("EXACT_APPROVED_TRANSPORT_MANIFEST_REQUIRED")
    indices = [row.get("index") for row in rows]
    if any(type(i) is not int for i in indices) or sorted(indices) != list(
        range(len(rows))
    ):
        raise ValueError("MISSING_OR_DUPLICATE_CHUNK")
    chunks = []
    for row in sorted(rows, key=lambda value: value["index"]):
        if any(row.get(name) != first.get(name) for name in fields):
            raise ValueError("CHUNK_MANIFEST_MISMATCH")
        offset = row["index"] * CHUNK_CHARS
        value = row.get("base64")
        expected = min(CHUNK_CHARS, first["base64_chars"] - offset)
        if (
            type(value) is not str
            or row.get("offset") != offset
            or len(value) != expected
            or row.get("chunk_chars") != expected
            or digest(value.encode("ascii")) != row.get("chunk_sha256")
        ):
            raise ValueError("CHUNK_LENGTH_OFFSET_OR_SHA_MISMATCH")
        chunks.append(value)
    compressed = base64.b64decode("".join(chunks), validate=True)
    if (
        len(compressed) != first["gzip_bytes"]
        or digest(compressed) != first["gzip_sha256"]
    ):
        raise ValueError("WHOLE_COMPRESSED_SUMMARY_MISMATCH")
    decoder = zlib.decompressobj(31)
    raw = decoder.decompress(compressed, RAW_BYTES + 1)
    if (
        not decoder.eof
        or decoder.unused_data
        or decoder.unconsumed_tail
        or len(raw) != RAW_BYTES
        or digest(raw) != RAW_SHA
    ):
        raise ValueError("WHOLE_APPROVED_SUMMARY_MISMATCH")
    json.loads(raw)
    return raw


def write_new(path, raw):
    if not path.is_absolute() or path.parent.resolve() != path.parent:
        raise ValueError("CANONICAL_ABSOLUTE_OUTPUT_REQUIRED")
    parent = path.parent.stat()
    if parent.st_uid != os.geteuid() or stat.S_IMODE(parent.st_mode) != 0o700:
        raise ValueError("OWNED_PRIVATE_OUTPUT_DIRECTORY_REQUIRED")
    descriptor = os.open(
        path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600
    )
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="action", required=True)
    emit = commands.add_parser("emit")
    emit.add_argument("--index", type=int, required=True)
    assemble = commands.add_parser("assemble")
    assemble.add_argument("--chunk", type=Path, action="append", required=True)
    assemble.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.action == "emit":
        print(
            json.dumps(
                encode(read_checked(SOURCE, RAW_BYTES, RAW_SHA), args.index),
                separators=(",", ":"),
            )
        )
    else:
        raw = decode([json.loads(path.read_bytes()) for path in args.chunk])
        write_new(args.output, raw)
        print(
            json.dumps(
                {
                    "kind": "approved-observer-summary-reassembled",
                    "bytes": len(raw),
                    "sha256": digest(raw),
                    "output": str(args.output),
                    "source_changed": False,
                    "formal_acceptance": False,
                }
            )
        )


if __name__ == "__main__":
    main()
