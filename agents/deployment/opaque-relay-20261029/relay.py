"""Bounded private TLS transport for existing opaque P790 exports; no SUT client."""

import argparse
import base64
import datetime as dt
import gzip
import hashlib
import http.client
import http.server
import io
import ipaddress
import json
import os
import re
import secrets
import signal
import ssl
import stat
import subprocess
import sys
import time
from pathlib import Path

SHA = re.compile(r"[0-9a-f]{64}")
UTC = dt.timezone.utc
META_CAP, PART_CAP, RAW_CAP = 32768, 17500, 2000000


def need(value, code):
    if not value:
        raise ValueError(code)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def read(path, cap, expected=None):
    path = Path(path)
    need(path.is_absolute() and path.resolve() == path, "EXACT_CANONICAL_FILE")
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
    with os.fdopen(fd, "rb") as stream:
        a = os.fstat(stream.fileno())
        need(stat.S_ISREG(a.st_mode) and a.st_nlink == 1 and a.st_size <= cap,
             "BOUNDED_SINGLE_REGULAR_FILE")
        raw = stream.read(cap + 1)
        b = os.fstat(stream.fileno())
    need((a.st_ino, a.st_size, a.st_mtime_ns) ==
         (b.st_ino, b.st_size, b.st_mtime_ns) and len(raw) == a.st_size,
         "STABLE_CLOSED_FILE")
    if expected is not None:
        need(SHA.fullmatch(expected) and digest(raw) == expected, "EXACT_FILE_SHA")
    return raw


def publish(path, raw):
    """Exclusive complete publication; preserve unfinished temp prefixes on failure."""
    path = Path(path)
    temp = path.parent / (".unpublished-" + secrets.token_hex(12))
    fd = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "wb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    os.link(temp, path, follow_symlinks=False)
    directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(directory)
    finally:
        os.close(directory)
    temp.unlink()


def save(path, obj):
    publish(path, (json.dumps(obj, sort_keys=True) + "\n").encode())


def parse_utc(text):
    value = dt.datetime.fromisoformat(text.replace("Z", "+00:00"))
    need(value.tzinfo is not None and value.utcoffset().total_seconds() == 0,
         "EXPLICIT_UTC")
    return value.timestamp()


def remaining(c):
    value = c["deadline"] - time.monotonic()
    need(value > 0 and time.time() < c["expires_epoch"], "RELAY_WINDOW_EXPIRED")
    return value


def cost_remaining(c):
    value = c["cost_deadline"] - time.monotonic()
    need(value > 0 and time.time() < c["cost_epoch"], "COST_STOP_WINDOW_EXPIRED")
    return value


def configure(path, expected, side):
    c = json.loads(read(path, 65536, expected))
    need(c["kind"] == "T44_OPAQUE_RELAY_" + side + "_V1", "EXACT_RELAY_SIDE")
    for key in ("binding_sha256", "root_grant_sha256", "key_sha256"):
        need(SHA.fullmatch(c[key]), "EXPLICIT_SCOPE_SHA")
    need(re.fullmatch(r"[0-9a-f]{40}", c["source_sha"]), "EXPLICIT_SOURCE_SHA")
    need(re.fullmatch(r"[a-z0-9-]{16,64}", c["nonce"]), "EXPLICIT_NEW_NONCE")
    for key in ("app_ip", "load_ip"):
        need(ipaddress.IPv4Address(c[key]).is_private, "PRIVATE_IPV4_ONLY")
    need(type(c["port"]) is int and 1024 <= c["port"] <= 65535, "PRIVATE_TLS_PORT")
    end, cost = parse_utc(c["expires_at"]), parse_utc(c["cost_stop_utc"])
    need(0 < end - time.time() <= 3600 and end <= cost
         and 0 < cost - time.time() <= 3600, "NEW_RELAY_AND_COST_WINDOW_MAX_ONE_HOUR")
    c["expires_epoch"] = end
    c["deadline"] = time.monotonic() + (end - time.time())
    c["cost_epoch"] = cost
    c["cost_deadline"] = time.monotonic() + (cost - time.time())
    if side == "APP":
        need(re.fullmatch(r"t44-[a-zA-Z0-9-]+(?:\.service)?", c["producer_unit"]),
             "EXACT_OWNED_UNIT")
        export = Path(c["export_dir"])
        need(export.is_absolute() and export.parent.resolve() == export.parent,
             "EXPLICIT_EXPORT_PARENT")
        read(c["tls_certificate"], 65536, c["tls_certificate_sha256"])
    else:
        read(c["ca_file"], 65536, c["ca_sha256"])
        need(type(c["max_wait_seconds"]) is int and 1 <= c["max_wait_seconds"] <= 600,
             "BOUNDED_WAIT_SECONDS")
        load = json.loads(read(c["load_configuration"], 100000,
                               c["load_configuration_sha256"]))
        for k in ("source_sha", "binding_sha256", "root_grant_sha256", "key_sha256"):
            need(load[k] == c[k], "EXACT_ORIGINAL_LOAD_SCOPE")
        need(load["ca_sha256"] == c["ca_sha256"], "EXACT_ORIGINAL_LOAD_CA")
        tools = Path(load["tools_dir"])
        manifest = json.loads(read(tools / "manifest.json", 100000,
                                   load["manifest_sha256"]))
        for name, row in manifest["files"].items():
            p = Path(name)
            need(not p.is_absolute() and ".." not in p.parts, "FLAT_TOOL_SCOPE")
            raw = read(tools / p, 262144, row["sha256"])
            need(len(raw) == row["bytes"], "EXACT_TOOL_SIZE")
        for name, pin in (("790_receive.py", "receiver_sha256"),
                          ("790_consumer.py", "consumer_sha256")):
            need(manifest["files"][name]["sha256"] == c[pin], "EXACT_ORIGINAL_RUNNER")
        need(load["transfer_sha256"] == manifest["files"]["transport/790_transfer.py"]["sha256"],
             "CURRENT_TRANSFER_PIN_NOT_OLD_TEMPLATE")
        c["original_load"] = load
    return c


def unit_status(unit):
    p = subprocess.run(["systemctl", "show", unit,
                        "--property=LoadState,ActiveState,SubState,MainPID,Result,ExecMainStatus"],
                       capture_output=True, text=True, timeout=3)
    values = dict(x.split("=", 1) for x in p.stdout.splitlines() if "=" in x)
    if values.get("LoadState") == "not-found":
        return False
    need(p.returncode == 0, "PRODUCER_STATUS_FAILED")
    if (values.get("ActiveState") == "active" and values.get("SubState") == "exited"
            and values.get("MainPID") == "0" and values.get("Result") == "success"
            and values.get("ExecMainStatus") == "0"):
        return True  # Explicit RemainAfterExit=yes keeps the completed proof available.
    if values.get("ActiveState") in ("active", "activating", "deactivating"):
        return False
    need(values.get("ActiveState") == "inactive" and values.get("Result") == "success"
         and values.get("ExecMainStatus") == "0", "PRODUCER_FAILED_NO_RETRY")
    return True


def scope(c, m):
    need(m["source_sha"] == c["source_sha"]
         and m["phase_binding_sha256"] == c["binding_sha256"]
         and m["root_grant_sha256"] == c["root_grant_sha256"]
         and m["original_public_meta"]["key_sha256"] == c["key_sha256"],
         "CIPHERTEXT_SCOPE_DIFFERS")
    need(type(m["part_count"]) is int and 1 <= m["part_count"] <= 4,
         "FOUR_BOUNDED_PARTS_ONLY")


def complete(c, metadata, parts):
    m = json.loads(metadata)
    scope(c, m)
    need(len(parts) == m["part_count"], "ALL_PARTS_REQUIRED")
    fragments = []
    for i, raw in enumerate(parts):
        need(len(raw) <= PART_CAP, "PART_BODY_CAP")
        p = json.loads(raw)
        value = base64.b64decode(p["data"], validate=True)
        need(p["index"] == i and p["parts"] == len(parts) and
             len(value) == p["bytes"] <= 11800 and digest(value) == p["sha256"],
             "OPAQUE_PART_IDENTITY_OR_HASH")
        fragments.append(value)
    compressed = b"".join(fragments)
    need(len(compressed) == m["compressed_bytes"] <= 47200
         and digest(compressed) == m["compressed_sha256"], "COMPLETE_COMPRESSED_SHA")
    with gzip.GzipFile(fileobj=io.BytesIO(compressed)) as stream:
        raw = stream.read(RAW_CAP + 1)
    need(len(raw) == m["raw_bytes"] <= RAW_CAP and digest(raw) == m["raw_sha256"],
         "COMPLETE_OPAQUE_ENVELOPE_SHA")
    return m


class Store:
    def __init__(self, c, status=unit_status):
        self.c, self.status, self.snapshot = c, status, None

    def ready(self):
        remaining(self.c)
        if self.snapshot is None:
            if not self.status(self.c["producer_unit"]):
                return None
            root = Path(self.c["export_dir"])
            metadata = read(root / "metadata.PUBLIC.json", META_CAP)
            m = json.loads(metadata)
            scope(self.c, m)
            parts = [read(root / ("part-" + str(i) + ".OPAQUE.json"), PART_CAP)
                     for i in range(m["part_count"])]
            complete(self.c, metadata, parts)
            self.snapshot = {"metadata": metadata, **{
                "part/" + str(i): raw for i, raw in enumerate(parts)}}
        return self.snapshot


def handler(store):
    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_GET(self):
            self.connection.settimeout(3)
            if self.client_address[0] != store.c["load_ip"]:
                self.send_error(403)
                return
            prefix = "/" + store.c["nonce"] + "/"
            if not self.path.startswith(prefix) or self.path[len(prefix):] not in (
                    "metadata", "part/0", "part/1", "part/2", "part/3"):
                self.send_error(404)
                return
            try:
                values = store.ready()
                if values is None:
                    self.send_error(425, "PRODUCER_NOT_READY")
                    return
                raw = values.get(self.path[len(prefix):])
                if raw is None:
                    self.send_error(404)
                    return
                self.send_response(200)
                self.send_header("Content-Type", "application/octet-stream")
                self.send_header("Content-Length", str(len(raw)))
                self.send_header("X-T44-SHA256", digest(raw))
                self.end_headers()
                self.wfile.write(raw)
            except Exception:
                self.send_error(409, "OPAQUE_EXPORT_REFUSED")
    return Handler


def private_server(c, store):
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    context.load_cert_chain(c["tls_certificate"], c["tls_key"])

    class Server(http.server.HTTPServer):
        def get_request(self):
            connection, address = super().get_request()
            try:
                need(address[0] == c["load_ip"], "EXACT_LOAD_SOURCE_ONLY")
                connection.settimeout(min(3, remaining(c)))
                return context.wrap_socket(connection, server_side=True), address
            except BaseException:
                connection.close()
                raise OSError("PRIVATE_TLS_PEER_REFUSED") from None

    return Server((c["app_ip"], c["port"]), handler(store))


def app(c):
    output = Path(c["output_dir"])
    need(output.is_absolute() and output.parent.resolve() == output.parent,
         "NEW_CANONICAL_APP_STATE")
    output.mkdir(mode=0o700)
    server = private_server(c, Store(c))
    server.timeout = .25
    save(output / "APP-ready.PUBLIC.json", {"kind": "PRIVATE_TLS_RELAY_LISTENING",
         "pid": os.getpid(), "nonce": c["nonce"], "source_sha": c["source_sha"],
         "binding_sha256": c["binding_sha256"], "app_ip": c["app_ip"],
         "load_ip": c["load_ip"], "port": c["port"], "expires_at": c["expires_at"],
         "cost_stop_utc": c["cost_stop_utc"], "SUT_or_consumer_started": False})
    try:
        while time.monotonic() < c["deadline"] and time.time() < c["expires_epoch"]:
            server.handle_request()
    finally:
        server.server_close()


def fetch(c, name, cap):
    connection = http.client.HTTPSConnection(
        c["app_ip"], c["port"], timeout=min(5, remaining(c)),
        source_address=(c["load_ip"], 0),
        context=ssl.create_default_context(cafile=c["ca_file"]))
    try:
        connection.request("GET", "/" + c["nonce"] + "/" + name,
                           headers={"Connection": "close"})
        response = connection.getresponse()
        raw = response.read(cap + 1)
        need(len(raw) <= cap, "FETCH_RESPONSE_BODY_CAP")
        if response.status == 425 and name == "metadata":
            return None
        need(response.status == 200, "OPAQUE_HTTP_NOT_READY_OR_SUCCESS")
        need(response.getheader("Content-Length") == str(len(raw))
             and response.getheader("X-T44-SHA256") == digest(raw), "EXACT_HTTP_BODY")
        return raw
    finally:
        connection.close()


def run_original(c, output, argv, name, cap):
    """Keep raw original output; never emit credentials/private stderr."""
    with (output / (name + ".stdout.PUBLIC")).open("xb") as out, \
            (output / (name + ".stderr.PRIVATE")).open("xb") as err:
        p = subprocess.Popen(argv, stdout=out, stderr=err, start_new_session=True)
        try:
            code = p.wait(timeout=min(cap, cost_remaining(c)))
        except BaseException:
            if p.poll() is None:
                os.killpg(p.pid, signal.SIGKILL)
                p.wait()
            raise
    need(code == 0, "ORIGINAL_RUNNER_FAILED_NO_RETRY:" + name)


def cleanup_owned_load(c):
    original = c["original_load"]
    namespace, image = original["namespace"], original["python_image_id"]
    need(re.fullmatch(r"t44-cloud-[a-z0-9-]{6,40}-p", namespace)
         and re.fullmatch(r"sha256:[0-9a-f]{64}", image), "EXACT_LOAD_CLEANUP_SCOPE")
    receipts = []
    for cohort in ("baseline1", "warmup40", "measure400"):
        name = namespace + "-790-" + cohort
        p = subprocess.run(["docker", "--context", "default", "inspect", "--format",
                            "{{json .}}", name], capture_output=True, timeout=5)
        if p.returncode:
            receipts.append({"name": name, "not_observed": True})
            continue
        item = json.loads(p.stdout)
        need(item["Name"] == "/" + name and item["Image"] == image and
             item["Config"]["Labels"].get("io.t44.contrast.owner") == namespace,
             "OWNED_CONTAINER_IDENTITY_DIFFERS_NO_SIGNAL")
        if item["State"]["Running"]:
            subprocess.run(["docker", "--context", "default", "stop", "--time", "15",
                            item["Id"]], capture_output=True, check=True, timeout=25)
        receipts.append({"name": name, "container_id": item["Id"], "owned_stop": True})
    return receipts


def load(c, invoke=run_original):
    output = Path(c["output_dir"])
    need(output.is_absolute() and output.parent.resolve() == output.parent,
         "NEW_CANONICAL_RELAY_OUTPUT")
    output.mkdir(mode=0o700)
    ready_before = min(c["deadline"], time.monotonic() + c["max_wait_seconds"])
    polls = 0
    while True:
        need(time.monotonic() < ready_before, "PRODUCER_READY_WAIT_EXPIRED")
        metadata = fetch(c, "metadata", META_CAP)
        polls += 1
        if metadata is not None:
            break
        time.sleep(min(.25, remaining(c)))
    publish(output / "metadata-raw.PUBLIC.json", metadata)
    m = json.loads(metadata)
    scope(c, m)
    parts = []
    for i in range(m["part_count"]):
        raw = fetch(c, "part/" + str(i), PART_CAP)
        publish(output / ("part-" + str(i) + ".OPAQUE.json"), raw)
        parts.append(raw)
    complete(c, metadata, parts)
    envelope = (json.dumps({"metadata": m}, separators=(",", ":")) + "\n").encode()
    publish(output / "metadata-import.PUBLIC.json", envelope)
    original = c["original_load"]
    base = [sys.executable, "-B", str(Path(original["tools_dir"]) / "790_receive.py")]
    config_args = ["--configuration", c["load_configuration"],
                   "--configuration-sha256", c["load_configuration_sha256"]]
    for operation, path in [("metadata", output / "metadata-import.PUBLIC.json")] + [
            ("part", output / ("part-" + str(i) + ".OPAQUE.json")) for i in range(len(parts))]:
        raw = read(path, max(META_CAP, PART_CAP))
        invoke(c, output, base + [operation] + config_args + ["--input", str(path),
                     "--input-sha256", digest(raw)], operation + "-" + path.stem, 15)
    # 420s parent cap >= original 60+15+300s; cleanup <=90s, receipt margin30s.
    # This is separate from the original 330s control.stop_utc admission check.
    need(cost_remaining(c) >= 540, "RELAY_COST_WINDOW_NEEDS_540S_FOR_CONSUMER_AND_STOP")
    save(output / "CONSUMER_RESERVED.PUBLIC.json", {"nonce": c["nonce"],
         "source_sha": c["source_sha"], "binding_sha256": c["binding_sha256"],
         "root_grant_sha256": c["root_grant_sha256"], "single_consumer": True})
    try:
        invoke(c, output, [sys.executable, "-B", str(Path(original["tools_dir"]) /
               "790_consumer.py")] + config_args, "consumer-once", 420)
    except BaseException:
        save(output / "owned-load-stop.PUBLIC.json", cleanup_owned_load(c))
        raise
    result = {"kind": "ORIGINAL_CONSUMER_COMPLETED_NOT_FORMAL_ACCEPTANCE",
              "source_sha": c["source_sha"], "binding_sha256": c["binding_sha256"],
              "polls_while_not_ready": polls, "parts": len(parts),
              "consumer_started_once": True, "next_iteration_authorized": False}
    save(output / "result.PUBLIC.json", result)
    return result


def main():
    os.umask(0o077)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("app", "load", "check"))
    parser.add_argument("--side", choices=("APP", "LOAD"))
    parser.add_argument("--configuration", required=True)
    parser.add_argument("--configuration-sha256", required=True)
    args = parser.parse_args()
    try:
        side = args.side if args.operation == "check" else args.operation.upper()
        need(side in ("APP", "LOAD"), "EXPLICIT_SIDE")
        c = configure(args.configuration, args.configuration_sha256, side)
        if args.operation == "check":
            result = {"kind": "RELAY_CONFIG_ONLY_CHECKED", "side": side,
                      "consumer_executed": False}
        elif side == "APP":
            app(c)
            result = {"kind": "RELAY_WINDOW_CLOSED", "consumer_executed_here": False}
        else:
            result = load(c)
        print(json.dumps(result))
        return 0
    except Exception as error:
        print(json.dumps({"kind": "OPAQUE_RELAY_FAILED_OR_INCOMPLETE", "error_type":
                          type(error).__name__, "reason": str(error),
                          "next_iteration_authorized": False}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
