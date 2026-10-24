"""Owned real-nginx fixture driver, never collected as a pytest test or run against a SUT."""

import hashlib
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
import traceback
from contextlib import contextmanager
from datetime import UTC, datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "agents/deployment/request-id-chain/runtime"
BASE = "30afdefaeb7427ec3b582a85373d5143124e0581"
IMAGE = "nginx:stable-alpine@sha256:47928bf67eb62a1863cb08d9ecb52d3e704304ba614eaee17884204677702951"
FILES = ("deployment/nginx/nginx.conf", "deployment/nginx/api.conf")
UUID = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\Z")
EDGE = re.compile(r"[0-9a-f]{32}\Z")
ORIGINAL = "11111111-1111-4111-8111-111111111111"
SPOOF = "22222222-2222-4222-8222-222222222222"
SECURITY = {"x-content-type-options": "nosniff", "referrer-policy": "same-origin", "x-frame-options": "DENY"}
RECEIPT = {"image_reference": IMAGE, "baseline_sha": BASE, "synthetic_only": True, "cases": [], "commands": []}


def save():
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "receipt.json").write_text(json.dumps(RECEIPT, indent=2) + "\n")


def command(args, timeout=30, check=True):
    result = subprocess.run(args, cwd=ROOT, capture_output=True, text=True, timeout=timeout, check=False)
    RECEIPT["commands"].append({"argv": args, "exit_code": result.returncode,
                               "stdout": result.stdout, "stderr": result.stderr})
    save()
    if check and result.returncode:
        raise RuntimeError(f"owned fixture command failed: {args[0]} exit {result.returncode}")
    return result


class Fixture(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *_args):
        pass

    def do_POST(self):
        self.do_GET()

    def do_GET(self):
        size = int(self.headers.get("Content-Length", "0"))
        if size:
            self.rfile.read(size)
        name = self.path.rsplit("/", 1)[-1]
        if name == "disconnect":
            self.connection.shutdown(socket.SHUT_RDWR)
            self.connection.close()
            return
        rid = str(uuid4())
        status = {"error": 401, "server-error": 500, "replay-error": 409, "api413": 413}.get(name, 200)
        values = [rid]
        if name == "absent":
            values = []
        elif name == "empty":
            values = [""]
        elif name == "invalid":
            values = ["invalid-upstream-id"]
        elif name == "uppercase":
            values = [rid.upper()]
        elif name == "non-v4":
            values = ["11111111-1111-1111-8111-111111111111"]
        elif name == "bad-variant":
            values = ["11111111-1111-4111-7111-111111111111"]
        elif name in ("duplicate-same", "duplicate-mixed-case"):
            values = [rid, rid]
        elif name == "duplicate-different":
            values = [rid, str(uuid4())]
        elif name == "comma":
            values = [f"{rid}, {rid}"]
        payload = {"data": {}, "meta": {"request_id": rid}} if status < 400 else {"request_id": rid}
        payload["fixture"] = {"received_request_id": self.headers.get("X-Request-ID"), "body_bytes": size}
        if name.startswith("replay"):
            payload["original_request_id"] = ORIGINAL
        data = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        for index, value in enumerate(values):
            key = "x-ReQuEsT-Id" if name == "mixed-case" or (name == "duplicate-mixed-case" and index) else "X-Request-ID"
            self.send_header(key, value)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(data)


def request(path, body=b"", spoof=None):
    lines = [f"{'POST' if body else 'GET'} {path} HTTP/1.1", "Host: fixture.invalid", "Connection: close"]
    if body:
        lines.append(f"Content-Length: {len(body)}")
    if spoof:
        lines.append(f"X-Request-ID: {spoof}")
    with socket.create_connection(("127.0.0.1", 8080), timeout=5) as sock:
        sock.settimeout(10)
        sock.sendall(("\r\n".join(lines) + "\r\n\r\n").encode())
        sent = True
        try:
            sock.sendall(body)
        except BrokenPipeError:
            sent = False  # nginx may reject oversized Content-Length before consuming its body.
        raw = b""
        while True:
            block = sock.recv(65536)
            if not block:
                break
            raw += block
            if len(raw) > 4 * 1024 * 1024:
                raise RuntimeError("synthetic response exceeds bound")
    head, separator, payload = raw.partition(b"\r\n\r\n")
    assert separator, "missing raw HTTP header terminator"
    decoded = head.decode("iso-8859-1")
    header_lines = decoded.split("\r\n")
    headers = [tuple(line.split(":", 1)) for line in header_lines[1:]]
    headers = [(key, value.strip()) for key, value in headers]
    return {"path": path, "status": int(header_lines[0].split()[1]), "raw_headers": decoded,
            "header_tuples": headers, "body": payload.decode(), "request_body_bytes": len(body),
            "request_body_send_completed": sent}


def ids(response):
    return [value for key, value in response["header_tuples"] if key.lower() == "x-request-id"]


@contextmanager
def nginx(directory, name):
    args = ["docker", "run", "--rm", "--user", "101:101", "--network", "host", "--add-host", "api:127.0.0.1",
            "--read-only", "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
            "--tmpfs", "/tmp:rw,noexec,nosuid,uid=101,gid=101,mode=0700",
            "--mount", f"type=bind,src={directory / 'nginx.conf'},dst=/etc/nginx/nginx.conf,readonly",
            "--mount", f"type=bind,src={directory / 'api.conf'},dst=/etc/nginx/t44-api.conf,readonly",
            "--mount", f"type=bind,src={directory / 'html'},dst=/usr/share/nginx/html,readonly"]
    command(args + ["--entrypoint", "nginx", IMAGE, "-t"])
    command(args + ["--detach", "--name", name, "--entrypoint", "nginx", IMAGE, "-g", "daemon off;"])
    try:
        for _ in range(50):
            try:
                with socket.create_connection(("127.0.0.1", 8080), timeout=0.1):
                    break
            except OSError:
                time.sleep(0.1)
        else:
            raise RuntimeError("owned nginx did not listen")
        yield
    finally:
        command(["docker", "logs", name], check=False)
        command(["docker", "rm", "--force", name], check=False)


def check_case(name, path=None, *, status=200, fallback=False, body=b"", spoof=None, local=False, replay=False):
    result = request(path or f"/api/v1/{name}", body, spoof)
    result["case"] = name
    RECEIPT["cases"].append(result)
    save()  # Preserve the actual raw response before any failing assertion.
    assert result["status"] == status, (name, result["status"])
    values = ids(result)
    assert len(values) == 1, (name, values)
    rid = values[0]
    assert (EDGE if fallback else UUID).fullmatch(rid), (name, rid)
    headers = {key.lower(): value for key, value in result["header_tuples"]}
    for key, value in SECURITY.items():
        assert headers.get(key) == value, (name, key)
    if local:
        payload = json.loads(result["body"])
        assert payload["request_id"] == rid and payload["audit_id"] is None
    elif not fallback:
        payload = json.loads(result["body"])
        current = payload["meta"]["request_id"] if status < 400 else payload["request_id"]
        assert current == rid
        if replay:
            assert payload["original_request_id"] == ORIGINAL != rid
        if body:
            assert payload["fixture"]["body_bytes"] == len(body)
        if spoof:
            received = payload["fixture"]["received_request_id"]
            assert EDGE.fullmatch(received) and received != spoof != rid
    result["passed"] = True
    save()
    return rid


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    RECEIPT["started_utc"] = datetime.now(UTC).isoformat()
    save()
    assert sys.platform == "linux" and shutil.which("docker"), "real hosted Linux Docker is required; no skip"
    assert os.environ.get("GITHUB_ACTIONS") == "true", "run only in the owned hosted fixture job"
    manifest = json.loads((ROOT / "agents/deployment/request-id-chain/run-request.json").read_text())
    target = manifest["candidate_source_sha"]
    assert re.fullmatch(r"[0-9a-f]{40}", target)
    assert manifest["mode"] == "synthetic-pinned-nginx"
    command(["git", "merge-base", "--is-ancestor", target, "HEAD"])
    guarded = [*FILES, "tmp/deployment/840_nginx_request_id.py", ".github/workflows/nginx-request-id.yml"]
    command(["git", "diff", "--exit-code", target, "--", *guarded])
    RECEIPT["candidate_source_sha"] = target
    RECEIPT["execution_sha"] = command(["git", "rev-parse", "HEAD"]).stdout.strip()
    RECEIPT["candidate_hashes"] = {path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest() for path in guarded}
    command(["docker", "pull", "--platform", "linux/amd64", IMAGE], timeout=180)
    RECEIPT["image_identity"] = command(["docker", "image", "inspect", "--format",
                                        "{{.Id}} {{json .RepoDigests}}", IMAGE]).stdout.strip()
    server = ThreadingHTTPServer(("127.0.0.1", 8000), Fixture)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with tempfile.TemporaryDirectory(prefix="t44-request-id-") as temporary:
            root = Path(temporary)
            root.chmod(0o755)
            for mode in ("baseline", "candidate"):
                directory = root / mode
                directory.mkdir(mode=0o755)
                (directory / "html").mkdir(mode=0o755)
                (directory / "html/index.html").write_text("<html>public synthetic SPA fixture</html>\n")
                for path, filename in zip(FILES, ("nginx.conf", "api.conf"), strict=True):
                    data = command(["git", "show", f"{BASE}:{path}"]).stdout if mode == "baseline" else (ROOT / path).read_text()
                    (directory / filename).write_text(data)
                    (directory / filename).chmod(0o644)
                with nginx(directory, f"t44-request-id-{mode}-{uuid4().hex[:10]}"):
                    if mode == "baseline":
                        result = request("/api/v1/success")
                        result["case"] = "baseline-one-header-counterexample"
                        RECEIPT["baseline"] = result
                        save()
                        assert len(ids(result)) == 2, "baseline did not reproduce; do not invent the failure"
                        try:
                            assert len(ids(result)) == 1
                        except AssertionError:
                            RECEIPT["baseline_expected_assertion_failed"] = True
                        else:
                            raise AssertionError("baseline one-header assertion unexpectedly passed")
                        save()
                        continue
                    first = check_case("success")
                    assert check_case("repeated-success", "/api/v1/success") != first
                    check_case("error", status=401)
                    check_case("server-error", status=500)
                    check_case("replay-success", replay=True)
                    check_case("replay-error", status=409, replay=True)
                    check_case("spoof", spoof=SPOOF)
                    check_case("mixed-case")
                    for invalid in ("absent", "empty", "invalid", "uppercase", "non-v4", "bad-variant",
                                    "duplicate-same", "duplicate-different", "duplicate-mixed-case", "comma"):
                        check_case(invalid, fallback=True)
                    check_case("local413", status=413, fallback=True, local=True, body=b"x" * (2 * 1024 * 1024 + 1))
                    check_case("api413", status=413, body=b"x" * (1024 * 1024 + 1))
                    check_case("disconnect", status=502, fallback=True)
                    check_case("static", "/index.html", fallback=True)
                    check_case("spa", "/synthetic/deep/route", fallback=True)
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
    RECEIPT["completed_utc"] = datetime.now(UTC).isoformat()
    RECEIPT["candidate_case_count"] = len(RECEIPT["cases"])
    RECEIPT["status"] = "passed"
    RECEIPT["scope"] = "real pinned nginx with synthetic upstream; not actual API/TLS/independent acceptance/performance"
    save()


if __name__ == "__main__":
    try:
        main()
    except Exception:
        RECEIPT["status"] = "failed"
        RECEIPT["failure"] = traceback.format_exc()
        save()
        raise
