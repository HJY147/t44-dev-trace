"""Narrow v5 recheck of two prior PUBLIC counterexamples; no network."""

import datetime
import hashlib
import json
import os
import tempfile
from pathlib import Path
from types import ModuleType, SimpleNamespace

path = Path(
    "/Users/yang/Desktop/nothing/软件开发大作业/"
    "tmp/829_independent_acceptance_20261025/PUBLIC/control.py"
)
expected = "08ac23736d11f7f11bf9a6c1362adcecca1d8a35fff9ce69ae0e21ef87a65e58"
raw = path.read_bytes()
assert hashlib.sha256(raw).hexdigest() == expected
control = ModuleType("public_829_v5")
exec(compile(raw, str(path), "exec"), control.__dict__)
anchor = datetime.datetime(2026, 10, 25, tzinfo=datetime.timezone.utc)
calls = {"sockets": 0, "transport_constructed": 0, "handoffs": 0}


class Clock:
    def __init__(self):
        self.mono = 0.0
        self.utc_seconds = 0

    def monotonic(self):
        return self.mono

    def monotonic_ns(self):
        return int(self.mono * 1_000_000_000)

    def utc_now(self):
        return anchor + datetime.timedelta(seconds=self.utc_seconds)


def no_socket(*_args, **_kwargs):
    calls["sockets"] += 1
    raise AssertionError("No network allowed")


class Response:
    status = 201

    def __init__(self):
        self.parts = [b'{"data":{"id":1}}', b""]

    def getheaders(self):
        return [("Content-Type", "application/json")]

    def read1(self, _size):
        return self.parts.pop(0)


class Transport:
    def __init__(self, *_args):
        calls["transport_constructed"] += 1

    def request(self, *_args, **_kwargs):
        pass

    def getresponse(self):
        return Response()

    def abort(self):
        pass

    def close(self):
        pass


control.socket = SimpleNamespace(create_connection=no_socket)
control.PinnedTLS = Transport
freeze = "synthetic-v4-no-SUT"
nonce = "synthetic-receipt-no-SUT"
previous = {k: os.environ.get(k) for k in ("I829_SUPERVISOR_RECEIPT", "I829_SUPERVISOR_NONCE")}
with tempfile.TemporaryDirectory(prefix="v5-recheck-", dir=Path(__file__).parent) as temp:
    receipt = Path(temp) / "receipt.json"
    receipt.write_text(json.dumps({"nonce": nonce, "child_pid": os.getpid(), "supervisor_pid": os.getppid(), "tool_freeze_sha256": freeze, "hard_deadline_monotonic": 1000}))
    os.environ["I829_SUPERVISOR_RECEIPT"] = str(receipt)
    os.environ["I829_SUPERVISOR_NONCE"] = nonce

    def gate(clock, seconds, journal):
        grant = {
            "admitted": True, "operator": "AI", "phase": "functional",
            "tool_freeze_sha256": freeze,
            "isolated_resource_ids": ["synthetic-no-resource"],
            "build": {"kind": "container", "source_sha": "a" * 40, "image_digest": "sha256:" + "b" * 64},
            "base_url": "https://not-contacted.invalid/api/v1", "pinned_ip": "127.0.0.1",
            "network_scope": "loopback", "expires_at": (anchor + datetime.timedelta(seconds=seconds)).isoformat(),
            "max_wall_seconds": seconds, "max_requests": 2, "max_concurrency": 1,
        }
        return control.Gate(grant, {"tool_freeze_sha256": freeze}, [("GET", "/auth/me"), ("POST", "/projects")], journal, clock=clock)

    try:
        clock = Clock()
        rows = []
        first = gate(clock, 10, SimpleNamespace(append=rows.append))
        clock.utc_seconds = 20
        utc_denied = False
        try:
            first.request("GET", "/auth/me")
        except control.DeadlineExceeded:
            utc_denied = True
        assert utc_denied and first.count == 0 and calls["transport_constructed"] == 0

        clock = Clock()
        rows = []
        second = gate(clock, 120, SimpleNamespace(append=rows.append))

        def handoff(project_id):
            assert project_id == 1
            calls["handoffs"] += 1
            clock.mono += 20
            clock.utc_seconds += 20
            return {"synthetic": "no actual credential"}

        second.fixture_handoff = SimpleNamespace(request=handoff)
        result = second.request("POST", "/projects", timeout=15)
        http_record = next(row for row in rows if row["kind"] == "request")
        run_live = not second.deadline_state()["expired"]
        assert run_live and http_record["body_complete"] is True
        assert http_record["elapsed_ns"] == 0
        assert result["status"] == 201 and result["complete"] is True
        assert result["error"] is None
        assert result["setup"]["classification"] == "READY"
        assert result["setup"]["elapsed_ns"] == 20_000_000_000
        assert not any(row["kind"] == "request_completion_rejected" for row in rows)
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
assert calls["sockets"] == 0 and calls["handoffs"] == 1
print(json.dumps({
    "control_sha256": expected,
    "method": "real PUBLIC Gate with synthetic receipts, clock, transport and neutral handoff",
    "previous_v3_UTC_forward_counterexample_denied_before_transport": utc_denied,
    "HTTP_timeout_seconds": 15, "run_wall_seconds": 120, "fake_handoff_seconds": 20,
    "HTTP_record_complete_before_handoff": http_record["body_complete"],
    "HTTP_record_elapsed_ns_excluding_handoff": http_record["elapsed_ns"],
    "run_still_live_after_handoff": run_live,
    "returned_http_status": result["status"], "returned_complete": result["complete"],
    "returned_error": result["error"], "actual_socket_calls": calls["sockets"],
    "SUT_requests": 0, "private_inputs_read": False, "existing29_rerun": False,
    "finding": "prior HTTP/handoff counterexample closed; HTTP result preserved and setup separately READY",
    "setup_classification": result["setup"]["classification"],
    "limits": "not actual TLS, provider, business case, supervisor launch or OS clock change",
}, indent=2))
