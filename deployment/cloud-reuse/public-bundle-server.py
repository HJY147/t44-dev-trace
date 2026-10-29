"""Short-lived private-IP HTTP for hash-verified public bundles only; no directory listing or secrets."""

import argparse
import hashlib
import http.server
import ipaddress
import json
import os
import re
import signal
import stat
import time
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


def hash_file(path):
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def regular(path):
    value = path.lstat()
    if (
        not stat.S_ISREG(value.st_mode)
        or value.st_uid != os.geteuid()
        or value.st_nlink != 1
    ):
        raise ValueError("OWNED_SINGLE_LINK_REGULAR_REQUIRED")
    return value


def save(path, value):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "w") as stream:
        json.dump(value, stream, indent=2)
        stream.write("\n")


def stamp():
    return datetime.now(timezone.utc).isoformat()  # noqa: UP017 - Ubuntu22 Python3.10


def private_ip(value):
    address = ipaddress.IPv4Address(value)
    if not any(
        address in ipaddress.IPv4Network(net)
        for net in ["10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"]
    ):
        raise ValueError("EXPLICIT_RFC1918_IPV4_REQUIRED")
    return str(address)


def identity(pid):
    root = Path("/proc") / str(pid)
    try:
        text = (root / "stat").read_text()
        fields = text[text.rindex(")") + 2 :].split()
        if fields[0] == "Z":
            return None
        return {
            "pid": pid,
            "uid": root.stat().st_uid,
            "pgid": int(fields[2]),
            "start_ticks": int(fields[19]),
            "argv_sha256": hashlib.sha256((root / "cmdline").read_bytes()).hexdigest(),
        }
    except FileNotFoundError:
        return None


def public_files(directory, kind, expected):
    if not re.fullmatch(r"[0-9a-f]{64}", expected) or directory.resolve() != directory:
        raise ValueError("TRUSTED_MANIFEST_SHA_AND_CANONICAL_PUBLIC_DIRECTORY_REQUIRED")
    meta = directory / (
        "parts-manifest.json" if kind == "parts" else "bundle-manifest.json"
    )
    regular(meta)
    if hash_file(meta) != expected:
        raise ValueError("TRUSTED_PUBLIC_MANIFEST_HASH_MISMATCH")
    manifest = json.loads(meta.read_text())
    if kind == "parts":
        declared = {}
        for index, row in enumerate(manifest["parts"]):
            if (
                row["name"] != "payload.part" + str(index).zfill(4)
                or not 0 < row["bytes"] <= 256 * 1024 * 1024
            ):
                raise ValueError("FIXED_PUBLIC_PARTS_ONLY")
            declared[row["name"]] = row
        if not declared or manifest["schema"] != 1:
            raise ValueError("NONEMPTY_PUBLIC_PARTS_REQUIRED")
    else:
        if (
            set(manifest["files"]) != {"images.tar.gz", "source-runtime-context.tar.gz"}
            or manifest["schema"] != 1
        ):
            raise ValueError("EXACT_PUBLIC_IMAGE_AND_SOURCE_OBJECTS_REQUIRED")
        declared = dict(manifest["files"])
    declared[meta.name] = {"bytes": meta.stat().st_size, "sha256": expected}
    if {p.name for p in directory.iterdir()} != set(declared):
        raise ValueError("ISOLATED_PUBLIC_DIRECTORY_NO_EXTRA_FILES_REQUIRED")
    result = {}
    for name, row in declared.items():
        info = regular(directory / name)
        if info.st_size != row["bytes"] or hash_file(directory / name) != row["sha256"]:
            raise ValueError("PUBLIC_OBJECT_BYTES_OR_HASH_MISMATCH")
        result[name] = {
            "bytes": info.st_size,
            "sha256": row["sha256"],
            "identity": [info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns],
        }
    return result


def run(args):
    bind, client = private_ip(args.bind), private_ip(args.allow_client)
    if (
        bind == client
        or not 1024 <= args.port <= 65535
        or not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", args.stop_utc)
    ):
        raise ValueError("DISTINCT_NODES_PORT_AND_EXACT_UTC_REQUIRED")
    deadline = datetime.fromisoformat(args.stop_utc.replace("Z", "+00:00")).timestamp()  # noqa: FURB162 - Python3.10 needs explicit offset
    seconds = deadline - time.time()
    if not 30 <= seconds <= 3600:
        raise ValueError("THIRTY_SECONDS_TO_ONE_HOUR_WINDOW_REQUIRED")
    end = time.monotonic() + seconds
    files = public_files(args.directory, args.kind, args.manifest_sha256)
    lease_parent = args.lease.parent.lstat()
    if (
        not stat.S_ISDIR(lease_parent.st_mode)
        or lease_parent.st_uid != os.geteuid()
        or stat.S_IMODE(lease_parent.st_mode) != 0o700
    ):
        raise ValueError("PRIVATE_OWNED_LEASE_PARENT_REQUIRED")
    requested, counts = [], {name: 0 for name in files}

    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self, _format, *_values):
            pass

        def setup(self):
            super().setup()
            self.connection.settimeout(5)

        def do_HEAD(self):
            self.respond(False)

        def do_GET(self):
            self.respond(True)

        def respond(self, body):
            if self.client_address[0] != client or self.path not in {
                "/" + name for name in files
            }:
                self.send_error(404)
                return
            name = self.path[1:]
            path = args.directory / name
            fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
            with os.fdopen(fd, "rb") as incoming:
                info = os.fstat(incoming.fileno())
                if [info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns] != files[
                    name
                ]["identity"]:
                    self.send_error(409)
                    return
                self.send_response(200)
                self.send_header("Content-Type", "application/octet-stream")
                self.send_header("Content-Length", str(info.st_size))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                if body:
                    while True:
                        if (
                            requested
                            or time.time() >= deadline
                            or time.monotonic() >= end
                        ):
                            break
                        block = incoming.read(1024 * 1024)
                        if not block:
                            counts[name] += 1
                            break
                        self.wfile.write(block)

    def request(signum, _frame):
        requested.append(signum)

    signal.signal(signal.SIGTERM, request)
    signal.signal(signal.SIGINT, request)
    owner = identity(os.getpid())
    if owner is None or owner["uid"] != os.geteuid():
        raise ValueError("LINUX_PROCESS_IDENTITY_REQUIRED")
    with http.server.HTTPServer((bind, args.port), Handler) as server:
        server.timeout = 0.5
        save(
            args.lease,
            {
                "kind": "public-bundle-http-only",
                "owner": owner,
                "created_utc": stamp(),
                "stop_utc": args.stop_utc,
                "bind": bind,
                "allow_client": client,
                "port": args.port,
                "directory": str(args.directory),
                "manifest_sha256": args.manifest_sha256,
                "public_files": files,
                "script_sha256": hash_file(Path(__file__)),
                "no_secrets_or_directory_listing": True,
            },
        )
        while not requested and time.time() < deadline and time.monotonic() < end:
            try:
                server.handle_request()
            except OSError:
                continue
    final = {
        "kind": "public-bundle-http-final",
        "utc": stamp(),
        "owner": owner,
        "stop_reason": "signal" if requested else "deadline",
        "completed_download_counts": counts,
        "VM_stopped_or_released": False,
    }
    save(args.lease.parent / ("server-final-" + uuid4().hex + ".json"), final)
    return {
        "success": True,
        "HTTP_server_closed": True,
        "stop_reason": final["stop_reason"],
        "VM_stopped_or_released": False,
    }


def stop(path):
    regular(path)
    lease = json.loads(path.read_text())
    if (
        lease["kind"] != "public-bundle-http-only"
        or lease["owner"]["uid"] != os.geteuid()
    ):
        raise ValueError("OWNED_PUBLIC_HTTP_LEASE_REQUIRED")
    owner = lease["owner"]
    actual = identity(owner["pid"])
    if actual is not None:
        if actual != owner:
            raise ValueError("PID_IDENTITY_CHANGED_NO_SIGNAL_SENT")
        os.kill(owner["pid"], signal.SIGTERM)
        end = time.monotonic() + 10
        while time.monotonic() < end and identity(owner["pid"]) == owner:
            time.sleep(0.1)
    gone = identity(owner["pid"]) is None
    result = {
        "success": gone,
        "kind": "public-http-owned-stop",
        "utc": stamp(),
        "pid": owner["pid"],
        "forced": False,
        "VM_or_other_processes_touched": False,
    }
    save(path.parent / ("server-stop-" + uuid4().hex + ".json"), result)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("run", "stop"))
    parser.add_argument("--directory", type=Path)
    parser.add_argument("--kind", choices=("parts", "bundle"))
    parser.add_argument("--manifest-sha256")
    parser.add_argument("--bind")
    parser.add_argument("--allow-client")
    parser.add_argument("--port", type=int, default=18444)
    parser.add_argument("--stop-utc")
    parser.add_argument("--lease", type=Path, required=True)
    args = parser.parse_args()
    os.umask(0o077)
    try:
        print(json.dumps(stop(args.lease) if args.action == "stop" else run(args)))
    except (OSError, ValueError, KeyError, TypeError):
        print(
            json.dumps(
                {
                    "success": False,
                    "error": "PUBLIC_BUNDLE_TRANSFER_REFUSED",
                    "no_forced_kill_or_cloud_operation": True,
                }
            )
        )
        raise SystemExit(1) from None
