"""Exact committed 790 tool review probe: no DB, cloud, socket, or product calls."""

import ast
import hashlib
import json
import subprocess
import types
from datetime import datetime, timedelta, timezone

COMMIT = "2a832920815ef61784c88796309ef3b53f83932c"
LOAD = "324d16da3e424fd4a196e01adda0e4c45857ac1d"
PREFIX = "tmp/790_backend_contrast_20261028/"


def source(path, commit=COMMIT):
    return subprocess.check_output(["git", "show", commit + ":" + PREFIX + path])


manifest_raw = source("manifest.json")
manifest = json.loads(manifest_raw)
assert hashlib.sha256(manifest_raw).hexdigest() == "9523f0d2da33abab3cc6cf22b4c1d3ffa2e108af8a28d30c2791f760f87935bf"
for path, item in manifest["files"].items():
    value = source(path)
    assert len(value) == item["bytes"]
    assert hashlib.sha256(value).hexdigest() == item["sha256"]
assert hashlib.sha256(source("790_load.py", LOAD)).hexdigest() == "01b7185a73f5a1a1baa42d78f4a9236dd51c433bd2f1592183c29e97dd08965c"
for path in ("790_bootstrap.py", "790_host.py", "790_load.py"):
    ast.parse(source(path, LOAD if path == "790_load.py" else COMMIT), feature_version=(3, 10))

http = types.ModuleType("reviewer_committed_790_http")
exec(compile(source("edge/790_http.py"), COMMIT + ":edge/790_http.py", "exec"), http.__dict__)


class Response:
    status = 200
    will_close = False

    def read(self, _limit):
        return json.dumps({"meta": {"request_id": "00000000-0000-4000-8000-000000000001", "replayed": False}, "data": {"accepted": True}}).encode()

    def getheader(self, key):
        return "00000000-0000-4000-8000-000000000001" if key == "X-Request-ID" else None


class Connection:
    def __init__(self):
        self.sent = []

    def request(self, *args):
        self.sent.append(args)

    def getresponse(self):
        return Response()

    def close(self):
        pass


# This models an already-configured live process whose clock crosses the stop.
http.CONTROL = {"stop_utc": (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat()}
client = http.Client.__new__(http.Client)
client.connection = connection = Connection()
client.connects = client.connect_ns = client.requests = 0
client.last = None
returned = client.call("/reviewer-offline-only", body={"synthetic": True})
assert returned == {"accepted": True} and len(connection.sent) == 1

# Actual worker code has no shared failure latch: another worker can complete
# all four operations even when invoked after a peer already failed.
http.CONTROL = {"stop_utc": (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat()}
calls = []
fail = [True]
task = {"id": 1, "project_id": 1, "state": 2, "version": 1, "schedule_version": 1, "blocked_from_state": None}
escalation = {**task, "id": 2}


class FakeClient:
    def __init__(self, *_):
        self.connects = self.connect_ns = self.requests = 0
        self.last = {}

    def call(self, path, token=None, body=None, key=None, sample=True):
        calls.append(path)
        if fail[0]:
            raise http.InvalidDiagnostic("reviewer synthetic first-peer failure")
        self.requests += 1
        self.last = {"wall_ns": 1, "status": 200}
        if body is None:
            return dict(task)
        if path.endswith("contract-validations"):
            return {"valid": True}
        if path.endswith("transitions"):
            return {"task": {**task, "state": 3, "version": 2, "blocked_from_state": 2}}
        return {"created": False, "event": {"id": 7}, "task_version": 1}

    def close(self):
        pass


http.Client = FakeClient
packet = {"url": "offline-only", "sessions": {role: {"access_token": "synthetic-no-session"} for role in ("developer", "service")}}


def slot():
    return {"transition": dict(task), "escalation": dict(escalation), "transition_role": "developer", "rule_version": 1, "scan_run_id": "offline-only", "event_id": 7}


barrier = types.SimpleNamespace(wait=lambda **_: None)
first = http.worker(0, slot(), packet, "unused-ca", barrier, [http.time.perf_counter() + 60], 1)
assert first.get("failed") is True
fail[0] = False
before = len(calls)
second = http.worker(1, slot(), packet, "unused-ca", barrier, [http.time.perf_counter() + 60], 1)
assert not second.get("failed") and len(calls) - before == 4

print(json.dumps({
    "source_commit": COMMIT,
    "load_commit": LOAD,
    "manifest_files_verified": len(manifest["files"]),
    "host_310_syntax_files": 3,
    "network_or_product_calls": 0,
    "deadline_counterexample": {"expired_before_call": True, "synthetic_requests_dispatched": len(connection.sent), "returned_success": True},
    "peer_failure_counterexample": {"first_peer_failed": True, "later_peer_operations_completed": len(calls) - before},
    "findings_reproduced": 2,
    "approval": False,
}, indent=2))
