"""Reviewer v2 closure probe; exact Git source, memory-only transports, no load."""

import ast
import gzip
import hashlib
import json
import subprocess
import threading
import types
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone

COMMIT = "6f5698f2d2df04a2347b893c55d93cb9c3063aa9"
PREFIX = "tmp/790_backend_contrast_20261028/"


def source(path, commit=COMMIT):
    return subprocess.check_output(["git", "show", commit + ":" + PREFIX + path])


manifest_raw = source("manifest.json")
assert hashlib.sha256(manifest_raw).hexdigest() == "640b3d386a756547d940b638ef6ccfc9bc49adaa2c071a2794aca8464b2edd84"
manifest = json.loads(manifest_raw)
assert manifest["tool_version"] == 2 and len(manifest["files"]) == 7
for path, item in manifest["files"].items():
    value = source(path)
    assert len(value) == item["bytes"] and hashlib.sha256(value).hexdigest() == item["sha256"]
for path in ("790_bootstrap.py", "790_host.py", "790_load.py"):
    ast.parse(source(path), feature_version=(3, 10))

seal = ET.fromstring(source("v2-seal.xml"))
cases = seal.findall(".//testcase")
assert len(cases) == len({c.attrib["name"] for c in cases}) == 33
assert all(not c.findall("failure") and not c.findall("error") and not c.findall("skipped") for c in cases)
archive = json.loads(source("red-archive.json"))
red_gzip = source("deadline-abort-red.xml.gz")
red_raw = gzip.decompress(red_gzip)
assert hashlib.sha256(red_gzip).hexdigest() == archive["gzip_sha256"]
assert hashlib.sha256(red_raw).hexdigest() == archive["raw_sha256"]
assert red_raw == source("deadline-abort-red.xml", "a43f60e4")

http = types.ModuleType("reviewer_exact_790_v2")
exec(compile(source("edge/790_http.py"), COMMIT + ":edge/790_http.py", "exec"), http.__dict__)
http.ssl.create_default_context = lambda **_: object()
future = lambda: (datetime.now(timezone.utc) + timedelta(minutes=1)).isoformat()
past = lambda: (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat()
http.CONTROL = {"url": "https://172.21.182.245:19445", "stop_utc": future()}
sent, waits, hooks = [], [], {"connect": None, "request": None}


class Response:
    status = 200
    will_close = False

    def read(self, _):
        return json.dumps({"meta": {"request_id": "00000000-0000-4000-8000-000000000001", "replayed": False}, "data": {"accepted": True}}).encode()

    def getheader(self, key):
        return "00000000-0000-4000-8000-000000000001" if key == "X-Request-ID" else None


class Connection:
    def __init__(self, *_, timeout=15, **__):
        self.timeout = timeout
        waits.append(timeout)
        self.sock = types.SimpleNamespace(settimeout=waits.append)

    def connect(self):
        if hooks["connect"]:
            hooks["connect"]()

    def request(self, *args):
        sent.append(args)
        if hooks["request"]:
            hooks["request"]()

    def getresponse(self):
        return Response()

    def close(self):
        pass


http.http.client.HTTPSConnection = Connection
client = http.Client(http.CONTROL["url"], "unused-ca")
http.CONTROL["stop_utc"] = past()
try:
    client.call("/offline-expired", body={"synthetic": True})
except http.InvalidDiagnostic:
    pass
else:
    raise AssertionError("expired new dispatch allowed")
assert not sent and not client.last["request_dispatch_attempted"]

http.CONTROL["stop_utc"] = future()
hooks["connect"] = lambda: http.CONTROL.update(stop_utc=past())
client = http.Client(http.CONTROL["url"], "unused-ca")
try:
    client.call("/offline-connect-expired")
except http.InvalidDiagnostic:
    pass
else:
    raise AssertionError("connect expiry did not stop dispatch")
assert not sent

http.CONTROL["stop_utc"] = future()
hooks["connect"] = None
abort = threading.Event()
hooks["request"] = abort.set
client = http.Client(http.CONTROL["url"], "unused-ca", abort=abort)
assert client.call("/offline-inflight") == {"accepted": True}
assert client.last["request_dispatch_attempted"] and client.last["body_read_complete"]
try:
    client.call("/offline-next-blocked")
except http.DiagnosticAborted:
    pass
else:
    raise AssertionError("abort did not stop later dispatch")
assert len(sent) == 1

calls = []


class FailedPeerClient:
    def __init__(self, *_, **__):
        self.last = {}
        self.connects = self.connect_ns = self.requests = 0

    def call(self, *_, **__):
        calls.append("synthetic attempted operation")
        raise http.InvalidDiagnostic("reviewer injected first-peer failure")

    def close(self):
        pass


http.Client = FailedPeerClient
abort = threading.Event()
task = {"id": 1, "project_id": 1, "state": 2, "version": 1, "schedule_version": 1, "blocked_from_state": None}
slot = lambda: {"transition": dict(task), "escalation": {**task, "id": 2}, "transition_role": "developer"}
packet = {"url": "offline", "sessions": {"developer": {"access_token": "synthetic-no-session"}}}
barrier = types.SimpleNamespace(wait=lambda **_: None, abort=lambda: None)
one = http.worker(0, slot(), packet, "unused-ca", barrier, [http.time.perf_counter() + 30], 1, abort)
assert one.get("failed") and abort.is_set()
before = len(calls)
two = http.worker(1, slot(), packet, "unused-ca", barrier, [http.time.perf_counter() + 30], 1, abort)
assert two.get("aborted") and len(calls) == before

print(json.dumps({
    "reviewed_commit": COMMIT,
    "manifest_sha256": hashlib.sha256(manifest_raw).hexdigest(),
    "manifest_files_verified": 7,
    "owner_seal_unique_testcases": 33,
    "owner_seal_no_failures_errors_skips": True,
    "owner_original_red_archive_byte_exact": True,
    "reviewer_checks": {"expired_no_dispatch": True, "connect_expiry_no_dispatch": True, "inflight_result_retained_after_abort": True, "next_dispatch_blocked_after_abort": True, "peer_failure_sets_abort_and_blocks_later_worker": True},
    "real_network_product_DB_CLI_cloud_or_load_calls": 0,
    "scope": "offline closure only, not live TLS or 400-client or six-role execution",
}, indent=2))
