"""Read-only fixed host counters. Missing observations are NOT_PROVEN, never a test pass."""

import hashlib
import json
import os
import stat
import sys
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path

PROC_FILES = ("/proc/stat", "/proc/meminfo", "/proc/diskstats", "/proc/net/dev", "/proc/net/snmp")
OUTPUT_PARENT = Path("/run/t44-relay852")
END_UTC = datetime(2026, 10, 24, 10, 10, tzinfo=UTC).timestamp()


def utc():
    return datetime.now(UTC).isoformat()


def read_counters():
    values = dict.fromkeys(PROC_FILES)
    errors = []
    for name in PROC_FILES:
        try:
            with open(name, "rb") as stream:
                data = stream.read(262145)
            if not data or len(data) > 262144:
                raise ValueError("SIZE")
            values[name] = data.decode()
        except (OSError, ValueError):
            errors.append({"source": name, "status": "NOT_PROVEN"})
    return values, errors


def owned_hash(path, identity):
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(descriptor, "rb") as stream:
        info = os.fstat(stream.fileno())
        if ((info.st_dev, info.st_ino) != identity or not stat.S_ISREG(info.st_mode)
                or info.st_uid != 0 or stat.S_IMODE(info.st_mode) != 0o600 or info.st_nlink != 1):
            raise ValueError("OWN_OUTPUT_IDENTITY")
        digest = hashlib.sha256()
        for block in iter(lambda: stream.read(65536), b""):
            digest.update(block)
    return digest.hexdigest(), info.st_size


def main():
    os.umask(0o077)
    path = None
    identity = None
    summary = {"file": None, "sha256": None, "bytes": 0, "nsamples": 0, "fails": 0}
    complete = False
    started = time.monotonic()
    stop = started + min(5400, END_UTC - time.time())
    try:
        if len(sys.argv) != 1 or os.geteuid() != 0 or time.monotonic() >= stop:
            raise ValueError("PREFLIGHT")
        parent = OUTPUT_PARENT.lstat()
        if (not stat.S_ISDIR(parent.st_mode) or parent.st_uid != 0
                or stat.S_IMODE(parent.st_mode) != 0o700):
            raise ValueError("PRIVATE_PARENT")
        candidate = OUTPUT_PARENT / ("host-resource-" + uuid.uuid4().hex + ".ndjson")
        descriptor = os.open(candidate, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        path = candidate  # Never read an existing file if exclusive creation failed.
        info = os.fstat(descriptor)
        identity = (info.st_dev, info.st_ino)
        with os.fdopen(descriptor, "w", buffering=1) as output:
            def write(row):
                output.write(json.dumps(row, separators=(",", ":")) + "\n")
            count = os.cpu_count()
            cpu_count = count if type(count) is int and count > 0 else None
            write({"kind": "context", "utc": utc(), "monotonic": time.monotonic(),
                   "cpu_count": cpu_count, "cpu_count_source": "os.cpu_count logical OS CPU;not cgroup quota",
                   "proc_files": PROC_FILES, "maximum_seconds": 5400, "interval_target_seconds": 10,
                   "absolute_end_utc": "2026-10-24T10:10:00Z",
                   "limitations": "non-atomic/non-peak;real read/write/scheduling overhead;CPU cumulative;"
                   "IO/network counters cumulative not rates;background traffic not excluded;no performance verdict"})
            while time.monotonic() < stop and time.time() < END_UTC:
                begin = time.monotonic()
                utc_begin = utc()
                values, errors = read_counters()
                if cpu_count is None:
                    errors.append({"source": "cpu_count", "status": "NOT_PROVEN"})
                write({"kind": "sample", "number": summary["nsamples"] + 1,
                       "utc_start": utc_begin, "monotonic_start": begin,
                       "utc_end": utc(), "monotonic_end": time.monotonic(), "proc": values,
                       "status": "NOT_PROVEN" if errors else "OBSERVED", "errors": errors})
                summary["nsamples"] += 1
                summary["fails"] += bool(errors)
                remaining = min(stop - time.monotonic(), END_UTC - time.time())
                if remaining > 0:
                    time.sleep(min(remaining, max(0, begin + 10 - time.monotonic())))
            output.flush()
            os.fsync(output.fileno())
        complete = True
    except (OSError, ValueError, TypeError):
        pass  # Stable five-field summary only; no raw exceptions or private content.
    if path is not None:
        summary["file"] = str(path)
        try:
            summary["sha256"], summary["bytes"] = owned_hash(path, identity)
        except (OSError, ValueError):
            complete = False
    print(json.dumps(summary))
    return 0 if complete and summary["nsamples"] > 0 and summary["fails"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
