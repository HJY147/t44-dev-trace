"""Owned continuous cgroup resource raw + private TLS single-path append mirror; no SUT API."""

import argparse
import hashlib
import hmac
import http.client
import http.server
import ipaddress
import json
import math
import os
import re
import secrets
import signal
import ssl
import stat
import subprocess
import threading
import time
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from uuid import uuid4

GENERATOR_SHA = "95802bf9e2a0d263bc00e1f2e5f046c553e29037e3c100eefebf09e81a95acc3"
SOURCE = "f7cdb5fa3b19f84d8ab0d0b042bf51a5b8484e8f"
HARDSTOP = "2026-10-29T12:00:00Z"
ROLES = ("mysql", "rabbitmq", "api", "consumer", "scheduler", "web", "tls-gateway")
DOCKER = ["docker", "--context", "default"]
CHUNK = 256 * 1024


def stamp():
    return datetime.now(timezone.utc).isoformat()  # noqa: UP017 - Ubuntu22 Python3.10


def expiry(s):
    t = datetime.fromisoformat(s.replace("Z", "+00:00"))  # noqa: FURB162 - Python3.10
    if t.tzinfo is None:
        raise ValueError("EXPLICIT_UTC_REQUIRED")
    return t.timestamp()


def sha(p):
    h = hashlib.sha256()
    with p.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def private(p, directory=False):
    s = p.lstat()
    if (
        p.resolve() != p
        or s.st_uid != os.geteuid()
        or stat.S_IMODE(s.st_mode) != (0o700 if directory else 0o600)
        or not (stat.S_ISDIR(s.st_mode) if directory else stat.S_ISREG(s.st_mode))
    ):
        raise ValueError("OWNED_CANONICAL_PRIVATE_OBJECT_REQUIRED")


def write(p, data):
    fd = os.open(p, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "wb") as f:
        f.write(data)


def save(p, row):
    write(p, (json.dumps(row, indent=2) + "\n").encode())


def command(argv, timeout=15):
    env = {
        k: v
        for k, v in os.environ.items()
        if not k.startswith(("DOCKER_", "COMPOSE_", "T44_", "MYSQL_", "RABBITMQ_"))
    }
    return subprocess.run(
        list(map(str, argv)), capture_output=True, check=True, timeout=timeout, env=env
    ).stdout


def ipv4(s):
    address = ipaddress.IPv4Address(s)
    if not any(
        address in ipaddress.IPv4Network(n)
        for n in ["10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"]
    ):
        raise ValueError("EXPLICIT_PRIVATE_IPV4_REQUIRED")
    return str(address)


def validate_deadlines(sample, serve):
    if (
        not time.time() + 120 <= expiry(sample)
        or expiry(serve) < expiry(sample) + 30
        or expiry(serve) > expiry(HARDSTOP)
    ):
        raise ValueError("FUTURE_SAMPLE_AND_FINALTAIL_WINDOW_WITHIN_PROFILE_REQUIRED")


def binding(directory, expected):
    private(directory, True)
    private(directory / "binding.json")
    if (
        not isinstance(expected, str)
        or not re.fullmatch(r"[0-9a-f]{64}", expected)
        or sha(directory / "binding.json") != expected
    ):
        raise ValueError("EXACT_STREAM_BINDING_SHA_REQUIRED")
    value = json.loads((directory / "binding.json").read_text())
    for name, value_sha in value["file_hashes"].items():
        if sha(directory / name) != value_sha:
            raise ValueError("OWNED_STREAM_OBJECT_CHANGED")
    if expiry(value["serve_until"]) > expiry(HARDSTOP):
        raise ValueError("ABSOLUTE_PROFILE_BOUND_REQUIRED")
    return value


def phase_value(path, expected):
    private(path, True)
    private(path / "binding.json")
    if sha(path / "binding.json") != expected:
        raise ValueError("EXACT_NEW_F4_PHASE_BINDING_REQUIRED")
    v = json.loads((path / "binding.json").read_text())
    if (
        v.get("generation_kind") != "exact-pinned-production-entry-generation-v4"
        or v.get("source_sha") != SOURCE
        or sha(path / "controller.py") != GENERATOR_SHA
    ):
        raise ValueError("NEW_F4_GENERATION_ONLY")
    return v


def prepare_app(args):
    if os.geteuid() != 0 or not re.fullmatch(r"[a-z][a-z0-9]{5,15}", args.run_id):
        raise ValueError("ROOT_AND_NEW_RESOURCE_RUN_REQUIRED")
    v = phase_value(args.phase_dir, args.phase_binding_sha256)
    if not Path("/sys/fs/cgroup/cgroup.controllers").is_file():
        raise ValueError("CGROUP_V2_HOST_REQUIRED_NO_ESTIMATE_FALLBACK")
    address, load_ip = ipv4(args.app_ip), ipv4(args.load_ip)
    if (
        address != v["app_private_ip"]
        or address == load_ip
        or not 1024 <= args.port <= 65535
        or args.port in {v["tls_port"], 13306}
        or not 0.2 <= args.interval <= 1
        or not 1024 * 1024 <= args.byte_cap <= 512 * 1024 * 1024
    ):
        raise ValueError("EXACT_TWO_NODE_BOUNDED_PRIVATE_RESOURCE_PROFILE_REQUIRED")
    validate_deadlines(args.sample_until, args.serve_until)
    import socket

    with socket.socket() as s:
        s.bind((address, args.port))
    private(args.output.parent, True)
    args.output.mkdir(mode=0o700)
    nonce = secrets.token_hex(32)
    write(args.output / "nonce", nonce.encode())
    write(args.output / "controller.py", Path(__file__).read_bytes())
    server = args.phase_dir / "tls/server"
    ca = args.phase_dir / "tls/ca.pem"
    if (
        sha(ca) != v["tls"]["ca_sha256"]
        or sha(server / "server.pem") != v["tls"]["server_certificate_sha256"]
    ):
        raise ValueError("ORIGINAL_PHASE_CERTIFICATES_CHANGED")
    data = {
        "kind": "app-owned-resource-stream-v1",
        "stream_id": args.run_id,
        "source_sha": SOURCE,
        "phase_dir": str(args.phase_dir),
        "phase_binding_sha256": args.phase_binding_sha256,
        "project": v["project"],
        "image_ids": v["image_ids"],
        "config_ids": v["config_ids"],
        "app_ip": address,
        "load_ip": load_ip,
        "port": args.port,
        "sample_until": args.sample_until,
        "serve_until": args.serve_until,
        "interval_seconds": args.interval,
        "byte_cap": args.byte_cap,
        "certificate": str(server / "server.pem"),
        "key": str(server / "server.key"),
        "certificate_sha256": sha(server / "server.pem"),
        "leaf_key_sha256": sha(server / "server.key"),
        "CA_sha256": sha(ca),
        "unit": "t44-resource-" + args.run_id + ".service",
        "file_hashes": {
            "controller.py": sha(args.output / "controller.py"),
            "nonce": sha(args.output / "nonce"),
        },
        "business_or_SG_IAM_changes": False,
        "CA_key_read": False,
    }
    save(args.output / "binding.json", data)
    handoff = {
        "kind": "private-readonly-resource-stream-handoff-v1",
        "stream_id": args.run_id,
        "source_sha": SOURCE,
        "app_binding_sha256": sha(args.output / "binding.json"),
        "app_ip": address,
        "load_ip": load_ip,
        "port": args.port,
        "nonce": nonce,
        "ca_pem": ca.read_text(),
        "ca_sha256": sha(ca),
        "serve_until": args.serve_until,
        "sample_until": args.sample_until,
        "byte_cap": args.byte_cap,
    }
    save(args.output / "private-mirror-handoff.json", handoff)
    return {
        "success": True,
        "directory": str(args.output),
        "binding_sha256": sha(args.output / "binding.json"),
        "private_handoff_path": str(args.output / "private-mirror-handoff.json"),
        "handoff_sha256": sha(args.output / "private-mirror-handoff.json"),
        "service_started": False,
    }


def prepare_mirror(args):
    private(args.handoff)
    if sha(args.handoff) != args.handoff_sha256 or not re.fullmatch(
        r"[a-z][a-z0-9]{5,15}", args.run_id
    ):
        raise ValueError("ROOT_VERIFIED_PRIVATE_HANDOFF_AND_NEW_RUN_REQUIRED")
    h = json.loads(args.handoff.read_text())
    if (
        h["kind"] != "private-readonly-resource-stream-handoff-v1"
        or h["source_sha"] != SOURCE
        or not re.fullmatch(r"[0-9a-f]{64}", h["nonce"])
        or hashlib.sha256(h["ca_pem"].encode()).hexdigest() != h["ca_sha256"]
        or ipv4(h["app_ip"]) == ipv4(h["load_ip"])
    ):
        raise ValueError("EXACT_PRIVATE_SINGLE_STREAM_HANDOFF_REQUIRED")
    if expiry(h["serve_until"]) <= time.time() + 30 or expiry(
        h["serve_until"]
    ) > expiry(HARDSTOP):
        raise ValueError("BOUNDED_LIVE_MIRROR_WINDOW_REQUIRED")
    if bool(args.required_start) != bool(args.required_end) or (
        args.required_start
        and not expiry(args.required_start)
        <= expiry(args.required_end)
        <= expiry(h["sample_until"])
    ):
        raise ValueError("EXPLICIT_ORDERED_REQUIRED_INTERVAL_WITHIN_SAMPLE_WINDOW")
    private(args.output.parent, True)
    args.output.mkdir(mode=0o700)
    write(args.output / "controller.py", Path(__file__).read_bytes())
    write(args.output / "private-handoff.json", args.handoff.read_bytes())
    v = {
        "kind": "load-append-resource-mirror-v1",
        "stream_id": h["stream_id"],
        "run_id": args.run_id,
        "unit": "t44-mirror-" + args.run_id + ".service",
        "serve_until": h["serve_until"],
        "file_hashes": {
            "controller.py": sha(args.output / "controller.py"),
            "private-handoff.json": sha(args.output / "private-handoff.json"),
        },
        "required_start_utc": args.required_start,
        "required_end_utc": args.required_end,
        "service_started": False,
    }
    save(args.output / "binding.json", v)
    return {
        "success": True,
        "directory": str(args.output),
        "binding_sha256": sha(args.output / "binding.json"),
        "service_started": False,
    }


def proc_stat(path):
    raw = path.read_text()
    fields = raw[raw.rfind(")") + 2 :].split()
    if len(fields) < 22:
        raise ValueError("COMPLETE_LINUX_PROC_STAT_REQUIRED")
    result = {
        "start_ticks": int(fields[19]),
        "rss_bytes": int(fields[21]) * os.sysconf("SC_PAGE_SIZE"),
    }
    if result["start_ticks"] <= 0 or result["rss_bytes"] < 0:
        raise ValueError("NONNEGATIVE_LIVE_PROCESS_COUNTERS_REQUIRED")
    return result


def cgroup_location(pid, cid):
    entries = (Path("/proc") / str(pid) / "cgroup").read_text().splitlines()
    found = [line[3:] for line in entries if line.startswith("0::")]
    if len(found) != 1 or cid not in found[0] or ".." in PurePosixPath(found[0]).parts:
        raise ValueError("EXACT_CONTAINER_CGROUP_V2_REQUIRED")
    root = Path("/sys/fs/cgroup") / found[0].lstrip("/")
    if root.resolve() != root:
        raise ValueError("CANONICAL_CGROUP_REQUIRED")
    return root


def counters(root):
    cpu = dict(line.split() for line in (root / "cpu.stat").read_text().splitlines())
    memory = int((root / "memory.current").read_text())
    extra = dict(
        line.split() for line in (root / "memory.stat").read_text().splitlines()
    )
    return {
        "cpu_usage_usec": int(cpu["usage_usec"]),
        "cgroup_memory_bytes": memory,
        "cgroup_anon_bytes": int(extra["anon"]) if "anon" in extra else None,
    }


def cpu_delta(previous, current, mono):
    if previous is None:
        return None, "first_sample_no_delta"
    usage, before = previous
    if mono <= before or current < usage:
        return None, "cpu_counter_or_clock_reset"
    return (current - usage) * 100000.0 / (mono - before), None


def identities(v):
    ids = (
        command(
            [
                *DOCKER,
                "ps",
                "--all",
                "--quiet",
                "--no-trunc",
                "--filter",
                "label=com.docker.compose.project=" + v["project"],
            ]
        )
        .decode()
        .split()
    )
    if any(not re.fullmatch(r"[0-9a-f]{64}", s) for s in ids):
        raise ValueError("EXACT_CIDS_REQUIRED")
    if not ids:
        return []
    expression = '{{json .Id}}\t{{json .Image}}\t{{json (index .Config.Labels "com.docker.compose.project")}}\t{{json (index .Config.Labels "com.docker.compose.service")}}\t{{json .State.Pid}}\t{{json .State.Running}}\t{{json .State.Restarting}}\t{{json .RestartCount}}'
    raw = (
        command([*DOCKER, "inspect", "--format", expression, *ids])
        .decode()
        .splitlines()
    )
    return [json.loads("[" + line.replace("\t", ",") + "]") for line in raw]


def sample(v, seq, planned, previous):
    started = time.monotonic_ns()
    observed = identities(v)
    rows = []
    for role in ROLES:
        now = time.monotonic_ns()
        row = {
            "kind": "resource_sample",
            "sequence": seq,
            "utc": stamp(),
            "monotonic_ns": now,
            "scheduled_monotonic_ns": planned,
            "sample_lateness_seconds": max(0, (now - planned) / 1e9),
            "role": role,
            "resource_id": v["project"] + "/" + role + "/absent",
            "container_id": None,
            "cpu_percent": None,
            "rss_bytes": None,
            "cgroup_memory_bytes": None,
            "cgroup_anon_bytes": None,
            "cpu_usage_usec": None,
            "pid": None,
            "process_start_ticks": None,
            "rss_semantics": "sum of process RSS, shared pages may repeat; cgroup memory separately includes cache/kernel",
        }
        matches = [r for r in observed if r[2] == v["project"] and r[3] == role]
        try:
            if len(matches) != 1:
                raise ValueError(
                    "missing_role" if not matches else "multiple_role_containers"
                )
            cid, image, _, _, pid, running, restarting, restarts = matches[0]
            mapped = {
                "mysql": "mysql",
                "rabbitmq": "rabbitmq",
                "web": "web",
                "tls-gateway": "nginx",
            }.get(role, "backend")
            if image not in {v["image_ids"][mapped], v["config_ids"][mapped]}:
                raise ValueError("unrecognized_container_image")
            row.update(
                container_id=cid,
                image_id=image,
                resource_id=v["project"] + "/" + role + "/" + cid,
                pid=pid,
                running=running,
                restarting=restarting,
                restart_count=restarts,
            )
            if not running or pid <= 0:
                raise ValueError("container_not_running")
            first = proc_stat(Path("/proc") / str(pid) / "stat")
            group = cgroup_location(pid, cid)
            usage = counters(group)
            cpu_mono = time.monotonic_ns()
            percent, reason = cpu_delta(
                previous.get(cid), usage["cpu_usage_usec"], cpu_mono
            )
            previous[cid] = usage["cpu_usage_usec"], cpu_mono
            pids = set()
            for path in [group / "cgroup.procs", *group.rglob("*/cgroup.procs")]:
                pids.update(int(line) for line in path.read_text().split())
            if not pids or len(pids) > 16384:
                raise ValueError("bounded_live_cgroup_processes_required")
            rss, failed = 0, 0
            for member in sorted(pids):
                try:
                    rss += proc_stat(Path("/proc") / str(member) / "stat")["rss_bytes"]
                except (OSError, ValueError):
                    failed += 1
            after = proc_stat(Path("/proc") / str(pid) / "stat")
            if after["start_ticks"] != first["start_ticks"]:
                raise ValueError("container_pid_reused_during_sample")
            row.update(
                **usage,
                cpu_percent=percent,
                cpu_delta_reason=reason,
                cpu_read_monotonic_ns=cpu_mono,
                process_start_ticks=first["start_ticks"],
                process_ids=sorted(pids),
                rss_bytes=rss if not failed else None,
                unreadable_process_count=failed,
            )
        except (OSError, ValueError, KeyError) as error:
            row["missing_reason"] = type(error).__name__ + ":" + str(error)
        row["sample_duration_seconds"] = (time.monotonic_ns() - now) / 1e9
        rows.append(row)
    return rows, (time.monotonic_ns() - started) / 1e9


class Sink:
    def __init__(self, path, maximum):
        self.fd = os.open(
            path, os.O_RDWR | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600
        )
        self.path = path
        self.identity = os.fstat(self.fd)
        self.lock = threading.RLock()
        self.maximum = maximum
        self.hash = hashlib.sha256()
        self.size = 0
        self.sealed = False
        self.whole_sha = None

    def check_identity(self):
        current = self.path.lstat()
        opened = os.fstat(self.fd)
        if (
            current.st_ino != self.identity.st_ino
            or current.st_dev != self.identity.st_dev
            or opened.st_nlink != 1
            or opened.st_size != self.size
            or not stat.S_ISREG(current.st_mode)
            or stat.S_IMODE(current.st_mode) != 0o600
            or current.st_uid != os.geteuid()
        ):
            raise ValueError("FIXED_RAW_DESCRIPTOR_IDENTITY_CHANGED")

    def append(self, row, final=False):
        data = (json.dumps(row, separators=(",", ":")) + "\n").encode()
        with self.lock:
            self.check_identity()
            if self.sealed or self.size + len(data) > self.maximum - (
                0 if final else 65536
            ):
                raise ValueError("RAW_BYTE_CAP_OR_SEALED")
            if final:
                checked = hashlib.sha256()
                for at in range(0, self.size, 1024 * 1024):
                    checked.update(
                        os.pread(self.fd, min(1024 * 1024, self.size - at), at)
                    )
                if checked.hexdigest() != self.hash.hexdigest():
                    raise ValueError("RAW_PREFIX_BYTES_CHANGED")
            view = memoryview(data)
            while view:
                n = os.write(self.fd, view)
                view = view[n:]
            self.hash.update(data)
            self.size += len(data)
            if final:
                os.fsync(self.fd)
                self.whole_sha = self.hash.hexdigest()
                self.sealed = True

    def chunk(self, offset):
        with self.lock:
            self.check_identity()
            if type(offset) is not int or offset < 0 or offset > self.size:
                raise ValueError("EXACT_EXISTING_PREFIX_OFFSET_REQUIRED")
            data = os.pread(self.fd, min(CHUNK, self.size - offset), offset)
            return data, {
                "bytes": self.size,
                "sealed": self.sealed,
                "whole_sha": self.whole_sha,
            }


def server_for(v, directory, sink, expected):
    nonce = (directory / "nonce").read_text()

    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def do_GET(self):
            if self.client_address[0] != v["load_ip"] or not hmac.compare_digest(
                self.headers.get("X-T44-Telemetry-Nonce", ""), nonce
            ):
                self.send_error(403)
                return
            if self.path != "/raw" or not re.fullmatch(
                r"0|[1-9][0-9]{0,12}", self.headers.get("X-Offset", "")
            ):
                self.send_error(400)
                return
            offset = int(self.headers["X-Offset"])
            try:
                data, meta = sink.chunk(offset)
            except ValueError:
                self.send_error(409)
                return
            self.send_response(200)
            self.send_header("Content-Type", "application/octet-stream")
            self.send_header("Content-Length", str(len(data)))
            for key, value in {
                "X-Stream-ID": v["stream_id"],
                "X-Binding-Sha256": expected,
                "X-Offset": offset,
                "X-Next-Offset": offset + len(data),
                "X-Chunk-Sha256": hashlib.sha256(data).hexdigest(),
                "X-Stream-Bytes": meta["bytes"],
                "X-Stream-Sealed": str(meta["sealed"]).lower(),
                "X-Stream-Sha256": meta["whole_sha"] or "",
            }.items():
                self.send_header(key, str(value))
            self.end_headers()
            self.wfile.write(data)

    class Server(http.server.ThreadingHTTPServer):
        daemon_threads = True
        allow_reuse_address = False

        def get_request(self):
            sock, peer = super().get_request()
            sock.settimeout(3)
            if peer[0] != v["load_ip"]:
                sock.close()
                raise ConnectionAbortedError("PRIVATE_LOAD_PEER_ONLY")
            return ctx.wrap_socket(sock, server_side=True), peer

    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.minimum_version = ssl.TLSVersion.TLSv1_2
    ctx.load_cert_chain(v["certificate"], v["key"])
    server = Server((v["app_ip"], v["port"]), Handler)
    return server


def daemon_app(directory, v, expected):
    phase_value(Path(v["phase_dir"]), v["phase_binding_sha256"])
    if (
        sha(Path(v["certificate"])) != v["certificate_sha256"]
        or sha(Path(v["key"])) != v["leaf_key_sha256"]
    ):
        raise ValueError("ORIGINAL_LEAF_IDENTITY_CHANGED")
    sink = Sink(directory / "raw.jsonl", v["byte_cap"])
    flags = {"stop": False, "seal": False, "seal_reason": None}
    signal.signal(signal.SIGTERM, lambda *a: flags.update(stop=True, seal=True))
    signal.signal(signal.SIGUSR1, lambda *a: flags.update(seal=True))
    start = time.monotonic_ns()
    sample_end = time.monotonic() + expiry(v["sample_until"]) - time.time()
    serve_end = time.monotonic() + expiry(v["serve_until"]) - time.time()
    sink.append(
        {
            "kind": "resource_header",
            "utc": stamp(),
            "monotonic_ns": start,
            "stream_id": v["stream_id"],
            "source_sha": SOURCE,
            "binding_sha256": expected,
            "roles": ROLES,
            "interval_seconds": v["interval_seconds"],
            "CPU_semantics": "cgroup cumulative microseconds delta per monotonic interval; one core100percent",
            "credential_data_included": False,
        }
    )
    server = server_for(v, directory, sink, expected)
    thread = threading.Thread(
        target=server.serve_forever, kwargs={"poll_interval": 0.2}, daemon=True
    )
    thread.start()
    previous, seq, reason = {}, 0, "deadline"
    next_tick = time.monotonic()
    try:
        while (
            not flags["stop"]
            and time.time() < expiry(v["serve_until"])
            and time.monotonic() < serve_end
        ):
            if not sink.sealed and (
                flags["seal"]
                or time.monotonic() >= sample_end
                or time.time() >= expiry(v["sample_until"])
            ):
                reason = flags["seal_reason"] or (
                    "explicit_seal" if flags["seal"] else "sample_deadline"
                )
                sink.append(
                    {
                        "kind": "resource_final",
                        "utc": stamp(),
                        "monotonic_ns": time.monotonic_ns(),
                        "samples": seq,
                        "reason": reason,
                        "prefix_sha256": sink.hash.hexdigest(),
                        "prefix_bytes": sink.size,
                    },
                    final=True,
                )
                save(
                    directory / "sealed.json",
                    {
                        "utc": stamp(),
                        "raw_bytes": sink.size,
                        "raw_sha256": sink.whole_sha,
                        "samples": seq,
                        "reason": reason,
                    },
                )
            if not sink.sealed and time.monotonic() >= next_tick:
                seq += 1
                planned = int(next_tick * 1e9)
                try:
                    rows, duration = sample(v, seq, planned, previous)
                    for row in rows:
                        row["whole_round_duration_seconds"] = duration
                        sink.append(row)
                except Exception as error:  # noqa: BLE001 - observer failure must be raw, never invented data
                    if "RAW_BYTE_CAP" in str(error):
                        reason = "byte_cap"
                        flags["seal"] = True
                        flags["seal_reason"] = "byte_cap"
                    else:
                        sink.append(
                            {
                                "kind": "resource_sampling_error",
                                "utc": stamp(),
                                "monotonic_ns": time.monotonic_ns(),
                                "sequence": seq,
                                "error_class": type(error).__name__,
                                "reason": str(error),
                            }
                        )
                next_tick += v["interval_seconds"]
            time.sleep(0.02)
    finally:
        if not sink.sealed:
            reason = "process_stop"
            sink.append(
                {
                    "kind": "resource_final",
                    "utc": stamp(),
                    "monotonic_ns": time.monotonic_ns(),
                    "samples": seq,
                    "reason": "process_stop",
                    "prefix_sha256": sink.hash.hexdigest(),
                    "prefix_bytes": sink.size,
                },
                final=True,
            )
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)
        os.close(sink.fd)
        save(
            directory / "daemon-final.json",
            {
                "utc": stamp(),
                "raw_bytes": sink.size,
                "raw_sha256": sink.whole_sha,
                "samples": seq,
                "sampling_reason": reason,
                "transport_to_load_not_assumed": True,
            },
        )


def verify_chunk(h, offset, headers, body):
    if (
        headers.get("X-Stream-ID") != h["stream_id"]
        or headers.get("X-Binding-Sha256") != h["app_binding_sha256"]
        or headers.get("X-Offset") != str(offset)
        or headers.get("X-Next-Offset") != str(offset + len(body))
        or headers.get("X-Chunk-Sha256") != hashlib.sha256(body).hexdigest()
        or len(body) > CHUNK
    ):
        raise ValueError("EXACT_AUTHENTIC_STREAM_PREFIX_AND_CHUNK_SHA_REQUIRED")
    total = int(headers["X-Stream-Bytes"])
    if total < offset + len(body) or total > h["byte_cap"]:
        raise ValueError("EXACT_BOUNDED_STREAM_BYTES_REQUIRED")
    if headers.get("X-Stream-Sealed") not in {"true", "false"}:
        raise ValueError("EXPLICIT_STREAM_SEAL_STATE_REQUIRED")
    sealed = headers.get("X-Stream-Sealed") == "true"
    if sealed and not re.fullmatch(r"[0-9a-f]{64}", headers.get("X-Stream-Sha256", "")):
        raise ValueError("SEALED_WHOLE_SHA_REQUIRED")
    return total, sealed


def summarize(path, v):
    first, last, previous, maximum, samples, nulls, prefix = (
        None,
        None,
        None,
        0.0,
        0,
        0,
        hashlib.sha256(),
    )
    final = None
    header = None
    sampling_errors = 0
    by_role = {}
    with path.open("rb") as f:
        for raw in f:
            row = json.loads(raw)
            if header is None:
                if (
                    row.get("kind") != "resource_header"
                    or row.get("stream_id") != v["stream_id"]
                    or row.get("source_sha") != SOURCE
                ):
                    raise ValueError("EXACT_RESOURCE_STREAM_HEADER_REQUIRED")
                header = row
            elif row["kind"] == "resource_header":
                raise ValueError("ONE_RESOURCE_HEADER_REQUIRED")
            sampling_errors += row["kind"] == "resource_sampling_error"
            if row["kind"] == "resource_final":
                if (
                    final
                    or row["prefix_sha256"] != prefix.hexdigest()
                    or row["prefix_bytes"] != f.tell() - len(raw)
                ):
                    raise ValueError("AUTHENTIC_FINAL_PREFIX_MARKER_REQUIRED")
                final = row
            else:
                if final:
                    raise ValueError("NO_BYTES_AFTER_FINAL_MARKER")
                prefix.update(raw)
            if row["kind"] == "resource_sample":
                first = first or row["utc"]
                last = row["utc"]
                samples += 1
                detail = by_role.setdefault(
                    row["role"],
                    {
                        "first_utc": row["utc"],
                        "last_utc": None,
                        "rows": 0,
                        "CPU_null_rows": 0,
                        "RSS_null_rows": 0,
                        "maximum_start_gap_seconds": None,
                        "last_monotonic_ns": None,
                    },
                )
                if detail["last_monotonic_ns"] is not None:
                    gap = (row["monotonic_ns"] - detail["last_monotonic_ns"]) / 1e9
                    detail["maximum_start_gap_seconds"] = max(
                        detail["maximum_start_gap_seconds"] or 0, gap
                    )
                detail.update(
                    last_utc=row["utc"],
                    last_monotonic_ns=row["monotonic_ns"],
                    rows=detail["rows"] + 1,
                    CPU_null_rows=detail["CPU_null_rows"]
                    + (row.get("cpu_percent") is None),
                    RSS_null_rows=detail["RSS_null_rows"]
                    + (row.get("rss_bytes") is None),
                )
                nulls += row.get("cpu_percent") is None or row.get("rss_bytes") is None
                if row["role"] == "mysql":
                    if previous is not None:
                        maximum = max(maximum, (row["monotonic_ns"] - previous) / 1e9)
                    previous = row["monotonic_ns"]
    if not final:
        raise ValueError("COMPLETE_FINAL_TAIL_REQUIRED")
    return {
        "first_resource_utc": first,
        "last_resource_utc": last,
        "resource_rows": samples,
        "raw_sampling_error_rows": sampling_errors,
        "rows_with_null_CPU_or_RSS": nulls,
        "maximum_mysql_sample_start_gap_seconds": maximum if previous else None,
        "received_final_tail": True,
        "sampling_final_reason": final.get("reason"),
        "per_role_actual_coverage": by_role,
        "at_or_before_required_start": expiry(first) <= expiry(v["required_start_utc"])
        if first and v.get("required_start_utc")
        else None,
        "at_or_after_required_end": expiry(last) >= expiry(v["required_end_utc"])
        if last and v.get("required_end_utc")
        else None,
        "independent_acceptance_verdict": None,
    }


def daemon_mirror(directory, v):
    h = json.loads((directory / "private-handoff.json").read_text())
    context = ssl.create_default_context(cadata=h["ca_pem"])
    context.check_hostname = True
    context.verify_mode = ssl.CERT_REQUIRED
    fd = os.open(
        directory / "app-raw.jsonl",
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
        0o600,
    )
    mirror_identity = os.fstat(fd)
    stopped = {"value": False}
    signal.signal(signal.SIGTERM, lambda *a: stopped.update(value=True))
    deadline = time.monotonic() + expiry(v["serve_until"]) - time.time()
    offset, digest, complete, error_count = 0, hashlib.sha256(), False, 0
    summary = None
    try:
        while (
            not stopped["value"]
            and time.time() < expiry(v["serve_until"])
            and time.monotonic() < deadline
        ):
            c = http.client.HTTPSConnection(
                h["app_ip"],
                h["port"],
                context=context,
                timeout=5,
                source_address=(h["load_ip"], 0),
            )
            try:
                c.request(
                    "GET",
                    "/raw",
                    headers={
                        "X-T44-Telemetry-Nonce": h["nonce"],
                        "X-Offset": str(offset),
                        "Connection": "close",
                    },
                )
                response = c.getresponse()
                if response.status != 200:
                    raise ValueError("EXPECTED_PRIVATE_RESOURCE_GET_200")
                body = response.read(CHUNK + 1)
                headers = dict(response.getheaders())
                total, sealed = verify_chunk(h, offset, headers, body)
                view = memoryview(body)
                current_mirror = (directory / "app-raw.jsonl").lstat()
                if (
                    current_mirror.st_ino != mirror_identity.st_ino
                    or current_mirror.st_dev != mirror_identity.st_dev
                    or os.fstat(fd).st_nlink != 1
                ):
                    raise ValueError("MIRROR_FIXED_DESCRIPTOR_IDENTITY_CHANGED")
                if os.fstat(fd).st_size != offset:
                    raise ValueError("MIRROR_APPEND_PREFIX_SIZE_CHANGED")
                while view:
                    n = os.write(fd, view)
                    if n <= 0:
                        raise OSError("MIRROR_ZERO_BYTE_WRITE")
                    digest.update(view[:n])
                    offset += n
                    view = view[n:]
                os.fsync(fd)
                if sealed and offset == total:
                    if digest.hexdigest() != headers["X-Stream-Sha256"]:
                        raise ValueError("COMPLETE_RAW_WHOLE_SHA_MISMATCH")
                    summary = summarize(directory / "app-raw.jsonl", v)
                    complete = True
                    break
            except (OSError, ValueError, http.client.HTTPException) as error:
                error_count += 1
                if error_count <= 256:
                    save(
                        directory / ("pull-error-" + uuid4().hex + ".json"),
                        {
                            "utc": stamp(),
                            "offset": offset,
                            "error_class": type(error).__name__,
                            "reason": str(error),
                            "nonce_or_business_credentials_logged": False,
                        },
                    )
            finally:
                c.close()
            time.sleep(0.25)
    finally:
        os.fsync(fd)
        os.close(fd)
        save(
            directory / "mirror-final.json",
            {
                "utc": stamp(),
                "transport_complete": complete,
                "raw_bytes": offset,
                "raw_sha256": digest.hexdigest(),
                "pull_errors": error_count,
                "from_offset_zero": True,
                "actual_coverage": summary,
                "business_or_acceptance_verdict": None,
            },
        )


def unit_text(directory, v, expected):
    action = (
        "daemon-app" if v["kind"] == "app-owned-resource-stream-v1" else "daemon-mirror"
    )
    argv = [
        "/usr/bin/python3",
        str(directory / "controller.py"),
        action,
        "--directory",
        str(directory),
        "--binding-sha256",
        expected,
    ]
    if not re.fullmatch(r"/[A-Za-z0-9_./-]+", str(directory)):
        raise ValueError("SYSTEMD_SAFE_PRIVATE_DIRECTORY_REQUIRED")
    text = (
        "[Unit]\nDescription=T44 bounded private resource observer\n[Service]\nType=simple\nUser=root\nUMask=0077\nNoNewPrivileges=true\nProtectSystem=strict\nReadWritePaths="
        + str(directory)
        + "\nWorkingDirectory="
        + str(directory)
        + "\nEnvironment=PYTHONDONTWRITEBYTECODE=1\nRestart=no\nTimeoutStopSec=15\nKillMode=control-group\nRuntimeMaxSec="
        + str(max(1, math.floor(expiry(v["serve_until"]) - time.time())))
        + "\nExecStart="
        + " ".join(argv)
        + "\n"
    )
    return text, argv


def start_service(directory, v, expected):
    if os.geteuid() != 0 or expiry(v["serve_until"]) <= time.time() + 30:
        raise ValueError("ROOT_AND_BOUNDED_LIVE_RESOURCE_WINDOW_REQUIRED")
    text, argv = unit_text(directory, v, expected)
    path = Path("/etc/systemd/system") / v["unit"]
    write(path, text.encode())
    path.chmod(0o644)
    save(
        directory / "start-plan.json",
        {
            "unit": v["unit"],
            "unit_path": str(path),
            "unit_sha256": sha(path),
            "argv": argv,
            "binding_sha256": expected,
        },
    )
    command(["systemctl", "daemon-reload"])
    command(["systemctl", "start", v["unit"]])
    command(["systemctl", "is-active", "--quiet", v["unit"]])
    pid = int(
        command(["systemctl", "show", "--property=MainPID", "--value", v["unit"]])
    )
    identity = proc_stat(Path("/proc") / str(pid) / "stat")
    actual = (Path("/proc") / str(pid) / "cmdline").read_bytes()
    if (
        actual.rstrip(b"\0").split(b"\0") != [s.encode() for s in argv]
        or (Path("/proc") / str(pid)).stat().st_uid != 0
    ):
        raise ValueError("EXACT_OWNED_SYSTEMD_PROCESS_REQUIRED")
    save(
        directory / "start-result.json",
        {
            "utc": stamp(),
            "pid": pid,
            "start_ticks": identity["start_ticks"],
            "cmdline_sha256": hashlib.sha256(actual).hexdigest(),
        },
    )
    return {
        "success": True,
        "unit": v["unit"],
        "pid": pid,
        "start_ticks": identity["start_ticks"],
        "deadline_utc": v["serve_until"],
    }


def control(directory, v, expected, action):
    private(directory / "start-plan.json")
    plan = json.loads((directory / "start-plan.json").read_text())
    if (
        plan["binding_sha256"] != expected
        or plan["unit"] != v["unit"]
        or sha(Path(plan["unit_path"])) != plan["unit_sha256"]
    ):
        raise ValueError("EXACT_FROZEN_OWNED_SYSTEMD_UNIT_REQUIRED")
    pid = int(
        command(["systemctl", "show", "--property=MainPID", "--value", v["unit"]])
    )
    if pid:
        started = json.loads((directory / "start-result.json").read_text())
        actual = (Path("/proc") / str(pid) / "cmdline").read_bytes()
        if (
            pid != started["pid"]
            or proc_stat(Path("/proc") / str(pid) / "stat")["start_ticks"]
            != started["start_ticks"]
            or hashlib.sha256(actual).hexdigest() != started["cmdline_sha256"]
            or (Path("/proc") / str(pid)).stat().st_uid != 0
        ):
            raise ValueError("PROCESS_OWNER_STARTTIME_OR_ARGV_CHANGED_NO_SIGNAL")
    if action == "seal" and pid:
        if v["kind"] != "app-owned-resource-stream-v1":
            raise ValueError("ONLY_APP_STREAM_CAN_BE_SEALED")
        command(["systemctl", "kill", "--signal=USR1", "--kill-who=main", v["unit"]])
    elif action == "stop" and pid:
        command(["systemctl", "stop", v["unit"]], timeout=30)
    after = int(
        command(["systemctl", "show", "--property=MainPID", "--value", v["unit"]])
    )
    progress = {}
    raw_path = directory / (
        "raw.jsonl" if v["kind"] == "app-owned-resource-stream-v1" else "app-raw.jsonl"
    )
    if raw_path.is_file():
        with raw_path.open("rb") as f:
            size = os.fstat(f.fileno()).st_size
            f.seek(max(0, size - 65536))
            data = f.read(65536)
        progress["raw_bytes_observed"] = size
        lines = data.split(b"\n")
        for raw in reversed(lines[:-1]):
            try:
                item = json.loads(raw)
                progress["last_complete_record"] = {
                    k: item.get(k)
                    for k in [
                        "kind",
                        "utc",
                        "role",
                        "resource_id",
                        "cpu_percent",
                        "rss_bytes",
                        "cgroup_memory_bytes",
                        "missing_reason",
                    ]
                }
                break
            except (ValueError, UnicodeError):
                continue
    for name in ["sealed.json", "daemon-final.json", "mirror-final.json"]:
        if (directory / name).is_file():
            progress[name] = json.loads((directory / name).read_text())
    row = {
        "utc": stamp(),
        "action": action,
        "progress": progress,
        "unit": v["unit"],
        "observed_before_pid": pid,
        "observed_after_pid": after,
        "owned_process_stopped": after == 0 if action == "stop" else None,
        "raw_or_data_deleted": False,
    }
    save(directory / ("control-" + uuid4().hex + ".json"), row)
    return row


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "action",
        choices=[
            "prepare-app",
            "prepare-mirror",
            "start",
            "seal",
            "stop",
            "status",
            "daemon-app",
            "daemon-mirror",
        ],
    )
    for name in ["output", "phase-dir", "handoff", "directory"]:
        p.add_argument("--" + name, type=Path)
    for name in [
        "phase-binding-sha256",
        "handoff-sha256",
        "binding-sha256",
        "app-ip",
        "load-ip",
        "run-id",
        "sample-until",
        "serve-until",
        "required-start",
        "required-end",
    ]:
        p.add_argument("--" + name)
    p.add_argument("--port", type=int, default=18446)
    p.add_argument("--interval", type=float, default=1.0)
    p.add_argument("--byte-cap", type=int, default=256 * 1024 * 1024)
    args = p.parse_args()
    os.umask(0o077)
    try:
        if args.action == "prepare-app":
            result = prepare_app(args)
        elif args.action == "prepare-mirror":
            result = prepare_mirror(args)
        else:
            value = binding(args.directory, args.binding_sha256)
            if args.action == "start":
                result = start_service(args.directory, value, args.binding_sha256)
            elif args.action == "daemon-app":
                if value["kind"] != "app-owned-resource-stream-v1":
                    raise ValueError("EXACT_APP_DAEMON_KIND_REQUIRED")
                daemon_app(args.directory, value, args.binding_sha256)
                result = {"success": True, "daemon_exited": True}
            elif args.action == "daemon-mirror":
                if value["kind"] != "load-append-resource-mirror-v1":
                    raise ValueError("EXACT_MIRROR_DAEMON_KIND_REQUIRED")
                daemon_mirror(args.directory, value)
                result = {"success": True, "daemon_exited": True}
            else:
                result = control(
                    args.directory, value, args.binding_sha256, args.action
                )
        print(json.dumps(result))
    except Exception as error:  # noqa: BLE001 - preserve failure privately; never print handoff/nonce
        location = args.directory or args.output
        failure = None
        if location and location.is_dir():
            failure = location / ("failure-" + uuid4().hex + ".json")
            row = {
                "utc": stamp(),
                "error_class": type(error).__name__,
                "reason": str(error),
                "partial_state_preserved": True,
            }
            if isinstance(error, subprocess.CalledProcessError):
                row.update(
                    stdout=(error.stdout or b"").decode(errors="replace"),
                    stderr=(error.stderr or b"").decode(errors="replace"),
                )
            save(failure, row)
        print(
            json.dumps(
                {
                    "success": False,
                    "error": "RESOURCE_STREAM_REFUSED",
                    "private_failure_path": str(failure) if failure else None,
                }
            )
        )
        raise SystemExit(1) from None
