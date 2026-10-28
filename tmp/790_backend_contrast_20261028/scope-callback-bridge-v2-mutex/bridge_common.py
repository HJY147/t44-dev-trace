"""Host Python 3.10 primitives; receipts never contain credentials or raw child output."""

import base64
import gzip
import hashlib
import io
import json
import os
import stat
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

UTC = timezone.utc  # noqa: UP017 -- host Python 3.10.
HANDOFF_SECONDS = 120
LEASE_SECONDS = 80
SNAPSHOT_SECONDS = 30
RETURN_MARGIN = 10
APP_MIN_SECONDS = 45
APP_MAX_SECONDS = 60
MAX_PUBLIC_BYTES = 2_000_000


class Refused(Exception):
    pass


def require(condition, code):
    if not condition:
        raise Refused(code)


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def stamp(value):
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))  # noqa: FURB162 -- host3.10.
    require(result.tzinfo is not None and result.utcoffset() == timedelta(), "UTC_REQUIRED")
    return result


def utc(value):
    return value.astimezone(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")


class Clock:
    def now(self):
        return datetime.now(UTC)

    def mono(self):
        return time.monotonic()


class Deadline:
    def __init__(self, clock, end, monotonic_end=None):
        self.clock, self.end = clock, end
        projected = clock.mono() + (end - clock.now()).total_seconds()
        self.monotonic_end = (
            min(projected, monotonic_end) if monotonic_end is not None else projected
        )
        self.remaining()

    def remaining(self, cap=None):
        seconds = min(
            (self.end - self.clock.now()).total_seconds(), self.monotonic_end - self.clock.mono()
        )
        require(seconds > 0, "FINITE_DEADLINE_EXPIRED")
        return min(seconds, cap) if cap else seconds


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "DUPLICATE_JSON_KEY")
        result[key] = value
    return result


def parse(raw):
    return json.loads(
        raw,
        object_pairs_hook=unique_object,
        parse_constant=lambda _value: (_ for _ in ()).throw(Refused("NONFINITE_JSON_NUMBER")),
    )


def read(path, expected=None, private=False):
    path = Path(path)
    require(path.is_absolute() and path.resolve() == path, "CANONICAL_INPUT_REQUIRED")
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(fd, "rb") as stream:
        info = os.fstat(stream.fileno())
        require(
            stat.S_ISREG(info.st_mode) and info.st_size <= MAX_PUBLIC_BYTES, "BOUNDED_REGULAR_INPUT"
        )
        require(not private or not stat.S_IMODE(info.st_mode) & 0o077, "PRIVATE_MODE_REQUIRED")
        raw = stream.read(MAX_PUBLIC_BYTES + 1)
    require(expected is None or sha(raw) == expected, "EXACT_INPUT_SHA_REQUIRED")
    return raw


def reserve(path, raw, mode=0o600, uid=None):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, mode)
    with os.fdopen(fd, "wb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
        if uid is not None:
            os.fchown(stream.fileno(), uid, uid if os.geteuid() == 0 else -1)
        os.fchmod(stream.fileno(), mode)


def mkdir(path, mode=0o700):
    path = Path(path)
    require(path.is_absolute() and path.parent.resolve() == path.parent, "CANONICAL_NEW_DIRECTORY")
    path.mkdir(mode=mode)
    return path


def document(raw):
    return {"sha256": sha(raw), "raw_b64": base64.b64encode(raw).decode()}


def decode_document(value):
    raw = base64.b64decode(value["raw_b64"], validate=True)
    require(len(raw) <= MAX_PUBLIC_BYTES and sha(raw) == value["sha256"], "BOUND_DOCUMENT_CHANGED")
    return parse(raw)


def export_packet(value):
    raw = canonical(value) + b"\n"
    return (
        canonical(
            {
                "kind": "PUBLIC_SCOPE_AUTHORITY_PACKET_V1",
                "authority_sha256": sha(raw),
                "gzip_base64": base64.b64encode(gzip.compress(raw, mtime=0)).decode(),
            }
        )
        + b"\n"
    )


def import_packet(raw, expected):
    require(sha(raw) == expected, "EXACT_TRANSPORT_PACKET_REQUIRED")
    packet = parse(raw)
    require(packet["kind"] == "PUBLIC_SCOPE_AUTHORITY_PACKET_V1", "AUTHORITY_PACKET_KIND")
    with gzip.GzipFile(
        fileobj=io.BytesIO(base64.b64decode(packet["gzip_base64"], validate=True))
    ) as source:
        decoded = source.read(MAX_PUBLIC_BYTES + 1)
    require(
        len(decoded) <= MAX_PUBLIC_BYTES and sha(decoded) == packet["authority_sha256"],
        "AUTHORITY_DIGEST",
    )
    return parse(decoded)
