"""Fixed seven-service read-only sampling. Collection is not a performance verdict."""

import hashlib
import json
import os
import re
import stat
import subprocess
import sys
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path

SERVICES = ("mysql", "rabbitmq", "api", "consumer", "scheduler", "web", "tls-gateway")
PROJECT = "t44"
PRODUCT_C = "0dfb55c2191200d947c5423fd9ee74bb0812cc5a"
END_UTC = datetime(2026, 10, 24, 10, 10, tzinfo=UTC).timestamp()
PROC_FILES = ("/proc/stat", "/proc/meminfo", "/proc/diskstats", "/proc/net/dev", "/proc/net/snmp")
FIELDS = ("ID", "CPUPerc", "MemUsage", "MemPerc", "NetIO", "BlockIO", "PIDs")
STATS_FORMAT = "{" + ",".join('"' + name + '":{{json .' + name + "}}" for name in FIELDS) + "}"
INSPECT_FORMAT = ('{{json .Id}}\t{{json (index .Config.Labels "com.docker.compose.project")}}\t'
                  '{{json (index .Config.Labels "com.docker.compose.service")}}\t{{json .State.Running}}')
DOCKER = ["docker", "--context", "default"]


def utc():
    return datetime.now(UTC).isoformat()


def command(arguments, stop, cap=5):
    remaining = min(stop - time.monotonic(), END_UTC - time.time())
    if remaining <= 0:
        raise ValueError("DEADLINE")
    environment = {k: v for k, v in os.environ.items() if k not in {"DOCKER_HOST", "DOCKER_CONTEXT"}}
    return subprocess.run(arguments, capture_output=True, check=True, timeout=min(cap, remaining),
                          env=environment).stdout.decode()


def identifier(value):
    if not re.fullmatch(r"[0-9a-f]{64}", value):
        raise ValueError("INVALID_CONTAINER_ID")
    return value


def validate_labels(text, mapping):
    seen = set()
    for line in text.splitlines():
        values = [json.loads(part) for part in line.split("\t")]
        if len(values) != 4:
            raise ValueError("INSPECT_FIELDS")
        identity, project, service, running = values
        identifier(identity)
        if (project != PROJECT or service not in SERVICES or mapping.get(service) != identity
                or identity in seen or running is not True):
            raise ValueError("CONTAINER_MAPPING_OR_STATE")
        seen.add(identity)
    if len(mapping) != 7 or len(set(mapping.values())) != 7 or seen != set(mapping.values()):
        raise ValueError("MISSING_OR_DUPLICATE_SERVICE")


def stats_projection(text, mapping):
    result = {}
    reverse = {identity: service for service, identity in mapping.items()}
    for line in text.splitlines():
        row = json.loads(line)
        if not isinstance(row, dict) or set(row) != set(FIELDS) or not all(isinstance(v, str) for v in row.values()):
            raise ValueError("STATS_FIELDS")
        identity = identifier(row["ID"])
        if identity not in reverse or reverse[identity] in result:
            raise ValueError("STATS_FOREIGN_OR_DUPLICATE")
        result[reverse[identity]] = row
    if set(result) != set(SERVICES):
        raise ValueError("STATS_INCOMPLETE")
    return result


def discover(stop):
    mapping = {}
    for service in SERVICES:
        listing = command([*DOCKER, "ps", "--all", "--no-trunc", "--filter",
                           "label=com.docker.compose.project=" + PROJECT, "--filter",
                           "label=com.docker.compose.service=" + service, "--format", "{{.ID}}"], stop).splitlines()
        if len(listing) != 1:
            raise ValueError("SERVICE_NOT_UNIQUE")
        mapping[service] = identifier(listing[0])
    validate_labels(command([*DOCKER, "inspect", "--format", INSPECT_FORMAT, *mapping.values()], stop), mapping)
    return mapping


def proc_projection():
    result = {}
    for name in PROC_FILES:
        with open(name, "rb") as stream:
            data = stream.read(262145)
        if len(data) > 262144 or not data:
            raise ValueError("PROC_SIZE_OR_EMPTY")
        result[name] = data.decode()
    return result


def main():
    os.umask(0o077)
    if len(sys.argv) != 1 or os.geteuid() != 0:
        print(json.dumps({"error": "ROOT_AND_NO_ARGUMENTS_REQUIRED"}))
        return 1
    started = time.monotonic()
    stop = started + min(5400, END_UTC - time.time())
    parent = Path("/run/t44-delivery")
    try:
        meta = parent.lstat()
        if (not stat.S_ISDIR(meta.st_mode) or stat.S_IMODE(meta.st_mode) != 0o700 or meta.st_uid != 0
                or time.monotonic() >= stop):
            raise ValueError("PRIVATE_PARENT_OR_DEADLINE")
        path = parent / ("resource-" + uuid.uuid4().hex + ".ndjson")
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    except (OSError, ValueError):
        print(json.dumps({"error": "SAMPLER_PREFLIGHT_FAILED"}))
        return 1
    samples = failed = 0
    setup_ok = False
    with os.fdopen(descriptor, "w", buffering=1) as output:
        def write(row):
            output.write(json.dumps(row, separators=(",", ":")) + "\n")
        try:
            endpoint = command([*DOCKER, "context", "inspect", "default", "--format",
                                "{{.Endpoints.docker.Host}}"], stop).strip()
            if not endpoint.startswith("unix://"):
                raise ValueError("LOCAL_UNIX_REQUIRED")
            head = command(["git", "-C", "/opt/t44-c-0dfb55c", "rev-parse", "HEAD"], stop).strip()
            if head != PRODUCT_C:
                raise ValueError("SOURCE_HEAD_DIFFERS")
            command(["git", "-C", "/opt/t44-c-0dfb55c", "diff", "--quiet", "HEAD", "--"], stop)
            mapping = discover(stop)
            write({"kind": "context", "utc": utc(), "monotonic": time.monotonic(),
                   "declared_product_source": PRODUCT_C, "container_content_attestation": False,
                   "project": PROJECT, "cpu_count": os.cpu_count(), "services": mapping, "daemon_transport": "local_unix",
                   "target_interval_seconds": 10, "maximum_total_seconds": 5400,
                   "absolute_end_utc": "2026-10-24T10:10:00Z",
                   "limitations": "real command/proc/write/scheduling overhead; non-atomic non-peak samples;"
                   "Docker MemUsage cache-adjusted not RSS;PIDs include threads;IO cumulative not rates;"
                   "CPU stats window not full load window;sampler adds overhead;not original six-service qualification;"
                   "no performance verdict;existing scheduler/consumer/health probes continue"})
            setup_ok = True
            while time.monotonic() < stop and time.time() < END_UTC:
                begin = time.monotonic()
                row = {"kind": "sample", "number": samples + 1, "utc_start": utc(), "monotonic_start": begin,
                       "services": None, "proc": None, "errors": []}
                try:
                    validate_labels(command([*DOCKER, "inspect", "--format", INSPECT_FORMAT,
                                             *mapping.values()], stop), mapping)
                    row["services"] = stats_projection(command([*DOCKER, "stats", "--no-stream", "--no-trunc",
                                                               "--format", STATS_FORMAT, *mapping.values()], stop), mapping)
                    row["proc"] = proc_projection()
                except (OSError, ValueError, TypeError, subprocess.SubprocessError):
                    row["errors"] = ["SAMPLE_OBSERVATION_UNAVAILABLE"]
                    failed += 1
                row.update(utc_end=utc(), monotonic_end=time.monotonic())
                samples += 1
                write(row)
                left = min(stop - time.monotonic(), END_UTC - time.time())
                if left > 0:
                    time.sleep(min(left, max(0, begin + 10 - time.monotonic())))
        except (OSError, ValueError, TypeError, subprocess.SubprocessError):
            write({"kind": "setup_error", "utc": utc(), "error": "SETUP_OBSERVATION_UNAVAILABLE"})
        finally:
            output.flush()
            os.fsync(output.fileno())
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(65536), b""):
            digest.update(block)
    print(json.dumps({"file": str(path), "sha256": digest.hexdigest(), "bytes": path.stat().st_size,
                      "actual_samples": samples, "failed_samples": failed, "setup_ok": setup_ok,
                      "actual_elapsed_seconds": round(time.monotonic() - started, 3), "finished_utc": utc(),
                      "performance_verdict": None}))
    return 0 if setup_ok and samples > 0 and failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
