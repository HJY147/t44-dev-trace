"""Export explicit completed resource files only. Never enumerate either private directory."""

import argparse
import gzip
import hashlib
import io
import json
import os
import re
import stat
import tarfile
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path

PARENTS = {"app": Path("/run/t44-delivery"), "load": Path("/run/t44-relay852")}
PREFIXES = {"app": "resource-", "load": "host-resource-"}
SERVICES = {"mysql", "rabbitmq", "api", "consumer", "scheduler", "web", "tls-gateway"}
PROC_FILES = {"/proc/stat", "/proc/meminfo", "/proc/diskstats", "/proc/net/dev", "/proc/net/snmp"}
STATS_FIELDS = {"ID", "CPUPerc", "MemUsage", "MemPerc", "NetIO", "BlockIO", "PIDs"}
START = datetime(2026, 10, 24, 10, 10, tzinfo=UTC).timestamp()
LAST_START = datetime(2026, 10, 24, 10, 28, tzinfo=UTC).timestamp()
MAX_FILE = 64 * 1024 * 1024
MAX_TOTAL = 256 * 1024 * 1024
MAX_ARCHIVE = 128 * 1024 * 1024
MAX_LINE = 2 * 1024 * 1024


class SafeParser(argparse.ArgumentParser):
    def error(self, message):
        raise ValueError("INVALID_CLI")


def sources(host, pairs):
    if host not in PARENTS or not 1 <= len(pairs) <= 8:
        raise ValueError("SOURCE_LIMIT")
    result = []
    for name, expected in pairs:
        path = Path(name)
        pattern = PREFIXES[host] + r"[0-9a-f]{32}\.ndjson"
        if (path.parent != PARENTS[host] or not re.fullmatch(pattern, path.name)
                or not re.fullmatch(r"[0-9a-f]{64}", expected)
                or any(path == existing[0] for existing in result)):
            raise ValueError("SOURCE_NOT_ALLOWLISTED")
        result.append((path, expected))
    return result


def timestamp(value):
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("UTC_REQUIRED")
    return parsed.astimezone(UTC)


def sample_fields_complete(row, host):
    counters = row.get("proc")
    if (not isinstance(counters, dict) or set(counters) != PROC_FILES
            or not all(isinstance(value, str) and value.strip() for value in counters.values())):
        return False
    if host == "app":
        services = row.get("services")
        if not isinstance(services, dict) or set(services) != SERVICES:
            return False
        for values in services.values():
            if (not isinstance(values, dict) or set(values) != STATS_FIELDS
                    or not all(isinstance(value, str) and value.strip() for value in values.values())):
                return False
    return True


def summarize(data, host, check=lambda: None):
    count = failed = bad = setup_errors = 0
    times = []
    header_ok = False
    for line in data.splitlines():
        check()
        if not line:
            continue
        if len(line) > MAX_LINE:
            bad += 1
            continue
        try:
            row = json.loads(line)
            kind = row["kind"]
            if kind == "context":
                if header_ok:
                    raise ValueError("DUPLICATE_CONTEXT")
                if host == "app":
                    if (row["project"] != "t44" or set(row["services"]) != SERVICES
                            or row["declared_product_source"] != "0dfb55c2191200d947c5423fd9ee74bb0812cc5a"):
                        raise ValueError("CONTEXT_DIFFERS")
                elif set(row["proc_files"]) != PROC_FILES:
                    raise ValueError("CONTEXT_DIFFERS")
                timestamp(row["utc"])
                header_ok = True
            elif kind == "setup_error" and host == "app" and row["error"] == "SETUP_OBSERVATION_UNAVAILABLE":
                timestamp(row["utc"])
                header_ok = True
                setup_errors += 1
            elif kind == "sample":
                if not header_ok or type(row["number"]) is not int or row["number"] != count + 1:
                    raise ValueError("SAMPLE_SEQUENCE")
                if not sample_fields_complete(row, host):
                    raise ValueError("MISSING_REQUIRED_COUNTERS")
                begin, end = timestamp(row["utc_start"]), timestamp(row["utc_end"])
                if begin > end or not isinstance(row["errors"], list):
                    raise ValueError("SAMPLE_TIME_OR_ERRORS")
                times.extend((begin, end))
                count += 1
                failed += bool(row["errors"]) or row.get("status") == "NOT_PROVEN"
            else:
                raise ValueError("ROW_KIND")
        except (ValueError, TypeError, KeyError, AttributeError):
            bad += 1
    if not header_ok:
        raise ValueError("NOT_RESOURCE_FORMAT")
    return {"utc_min": min(times).isoformat() if times else None,
            "utc_max": max(times).isoformat() if times else None,
            "samples": count if not bad else None, "failed_samples": failed if not bad else None,
            "parsed_samples": count, "parsed_failed_samples": failed,
            "unparsed_or_invalid_rows": bad, "setup_errors": setup_errors,
            "status": "NOT_PROVEN" if bad or setup_errors or failed or not count else "OBSERVED"}


def identity(info):
    return (info.st_dev, info.st_ino, info.st_mode, info.st_uid, info.st_gid,
            info.st_nlink, info.st_size, info.st_mtime_ns, info.st_ctime_ns)


def read_completed(path, expected):
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(descriptor, "rb") as stream:
        before = os.fstat(stream.fileno())
        if (not stat.S_ISREG(before.st_mode) or stat.S_IMODE(before.st_mode) != 0o600
                or before.st_uid != 0 or before.st_nlink != 1 or before.st_size > MAX_FILE):
            raise ValueError("UNSAFE_OR_OVERSIZED_RESOURCE")
        data = stream.read(MAX_FILE + 1)
        after = os.fstat(stream.fileno())
    if len(data) != before.st_size or identity(before) != identity(after):
        raise ValueError("RESOURCE_CHANGED")
    actual = hashlib.sha256(data).hexdigest()
    if actual != expected:
        raise ValueError("COMPLETION_SHA_DIFFERS")
    return data, actual


class HashedWriter:
    def __init__(self, stream, check):
        self.stream, self.check = stream, check
        self.digest = hashlib.sha256()
        self.size = 0

    def write(self, data):
        self.check()
        if self.size + len(data) > MAX_ARCHIVE:
            raise ValueError("ARCHIVE_SIZE_LIMIT")
        written = self.stream.write(data)
        if written != len(data):
            raise OSError("SHORT_WRITE")
        self.digest.update(data)
        self.size += written
        return written

    def flush(self):
        self.stream.flush()


def add_bytes(archive, name, data):
    info = tarfile.TarInfo(name)
    info.size, info.mode, info.uid, info.gid, info.mtime = len(data), 0o600, 0, 0, 0
    archive.addfile(info, io.BytesIO(data))


def main():
    os.umask(0o077)
    archive_path = None
    try:
        parser = SafeParser(description=__doc__)
        parser.add_argument("--host", choices=PARENTS, required=True)
        parser.add_argument("--source", nargs=2, action="append", required=True, metavar=("PATH", "COMPLETION_SHA256"))
        args = parser.parse_args()
        selected = sources(args.host, args.source)
        if os.geteuid() != 0 or not START <= time.time() < LAST_START:
            raise ValueError("ROOT_OR_RECOVERY_WINDOW")
        parent = PARENTS[args.host]
        meta = parent.lstat()
        if (not stat.S_ISDIR(meta.st_mode) or stat.S_IMODE(meta.st_mode) != 0o700
                or meta.st_uid != 0 or parent.resolve() != parent):
            raise ValueError("PRIVATE_PARENT_REQUIRED")
        finish = min(time.monotonic() + 60, time.monotonic() + LAST_START - time.time())
        def check():
            if time.monotonic() >= finish or time.time() >= LAST_START:
                raise ValueError("EXPORT_BUDGET")
        candidate = parent / ("resource-evidence-" + args.host + "-" + uuid.uuid4().hex + ".tar.gz")
        descriptor = os.open(candidate, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        archive_path = candidate
        entries, total = [], 0
        with os.fdopen(descriptor, "wb") as output:
            writer = HashedWriter(output, check)
            with gzip.GzipFile(filename="", mode="wb", fileobj=writer, compresslevel=1, mtime=0) as compressed:
                with tarfile.open(fileobj=compressed, mode="w|") as archive:
                    for path, expected in selected:
                        check()
                        data, actual = read_completed(path, expected)
                        total += len(data)
                        if total > MAX_TOTAL:
                            raise ValueError("TOTAL_RESOURCE_LIMIT")
                        statistics = summarize(data, args.host, check)
                        name = "raw/" + path.name
                        add_bytes(archive, name, data)
                        entries.append({"member": name, "sha256": actual, "bytes": len(data), **statistics})
                    manifest = {"format": "t44-neutral-resource-evidence-v1", "host": args.host,
                                "created_utc": datetime.now(UTC).isoformat(), "sources": entries,
                                "provenance": "explicit paths and SHA from completed role sampler summaries;no directory scan",
                                "performance_verdict": None, "raw_bytes_unchanged": True}
                    add_bytes(archive, "manifest.json", (json.dumps(manifest, indent=2) + "\n").encode())
            output.flush()
            os.fsync(output.fileno())
            if os.fstat(output.fileno()).st_size != writer.size:
                raise ValueError("ARCHIVE_WRITE_SIZE_DIFFERS")
        print(json.dumps({"completed": True, "archive": str(archive_path), "sha256": writer.digest.hexdigest(),
                          "bytes": writer.size, "files": entries, "performance_verdict": None}))
        return 0
    except (OSError, ValueError, TypeError, KeyError, tarfile.TarError):
        print(json.dumps({"completed": False, "error": "RESOURCE_EXPORT_NOT_PROVEN",
                          "partial_archive": str(archive_path) if archive_path else None}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
