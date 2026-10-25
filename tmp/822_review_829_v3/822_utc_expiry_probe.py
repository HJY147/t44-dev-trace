"""One synthetic UTC-forward boundary probe; no private inputs or network."""

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
expected = "d4d83441fb696fd146b05fe24090e81fa1612b07ba341c2b08bcafbc2936f72d"
raw = path.read_bytes()
assert hashlib.sha256(raw).hexdigest() == expected
control = ModuleType("public_829_v3")
exec(compile(raw, str(path), "exec"), control.__dict__)
anchor = datetime.datetime(2026, 10, 25, tzinfo=datetime.timezone.utc)
clock = {"utc_seconds": 0, "monotonic": 0.0}
calls = {"sockets": 0, "fake_transport_requests": 0}


class ClockDateTime(datetime.datetime):
    @classmethod
    def now(cls, tz=None):
        value = anchor + datetime.timedelta(seconds=clock["utc_seconds"])
        return value if tz is not None else value.replace(tzinfo=None)


def no_socket(*_args, **_kwargs):
    calls["sockets"] += 1
    raise AssertionError("Network forbidden in PUBLIC boundary probe")


class Response:
    status = 200

    def __init__(self):
        self.reads = 0

    def getheaders(self):
        return []

    def read1(self, _size):
        self.reads += 1
        return b"{}" if self.reads == 1 else b""


class Transport:
    def __init__(self, *_args):
        pass

    def request(self, *_args, **_kwargs):
        calls["fake_transport_requests"] += 1

    def getresponse(self):
        return Response()

    def abort(self):
        pass

    def close(self):
        pass


control.dt = SimpleNamespace(datetime=ClockDateTime, timezone=datetime.timezone)
control.time = SimpleNamespace(
    monotonic=lambda: clock["monotonic"],
    monotonic_ns=lambda: int(clock["monotonic"] * 1_000_000_000),
)
control.socket = SimpleNamespace(create_connection=no_socket)
control.PinnedTLS = Transport
records = []
freeze = "synthetic-no-SUT-freeze"
nonce = "synthetic-no-SUT-nonce"
with tempfile.TemporaryDirectory(prefix="utc-probe-", dir=Path(__file__).parent) as temp:
    receipt = Path(temp) / "receipt.json"
    receipt.write_text(
        json.dumps(
            {
                "nonce": nonce,
                "child_pid": os.getpid(),
                "supervisor_pid": os.getppid(),
                "tool_freeze_sha256": freeze,
                "hard_deadline_monotonic": 1000,
            }
        )
    )
    names = ("I829_SUPERVISOR_RECEIPT", "I829_SUPERVISOR_NONCE")
    previous = {name: os.environ.get(name) for name in names}
    os.environ[names[0]], os.environ[names[1]] = str(receipt), nonce
    grant = {
        "admitted": True,
        "tool_freeze_sha256": freeze,
        "operator": "AI",
        "isolated_resource_ids": ["synthetic-no-resource"],
        "build": {
            "kind": "container",
            "source_sha": "a" * 40,
            "image_digest": "sha256:" + "b" * 64,
        },
        "base_url": "https://not-contacted.invalid/api/v1",
        "pinned_ip": "127.0.0.1",
        "network_scope": "loopback",
        "phase": "functional",
        "expires_at": (anchor + datetime.timedelta(seconds=10)).isoformat(),
        "max_wall_seconds": 60,
        "max_requests": 1,
        "max_concurrency": 1,
    }
    try:
        gate = control.Gate(
            grant,
            {"tool_freeze_sha256": freeze},
            [("GET", "/auth/me")],
            SimpleNamespace(append=records.append),
        )
        clock["utc_seconds"] = 20
        result = gate.request("GET", "/auth/me", timeout=0.1)
    finally:
        for name, value in previous.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value
assert ClockDateTime.now(datetime.timezone.utc) >= gate.expires
assert calls["sockets"] == 0
assert calls["fake_transport_requests"] == 1
assert result["complete"] is True and result["status"] == 200 and result["error"] is None
print(
    json.dumps(
        {
            "control_sha256": expected,
            "method": "real PUBLIC Gate initialization/request; synthetic receipt, UTC and transport",
            "grant_expires_at_utc_seconds": 10,
            "request_started_at_fake_utc_seconds": 20,
            "monotonic_seconds": clock["monotonic"],
            "hard_deadline_monotonic": gate.hard_deadline,
            "actual_socket_calls": calls["sockets"],
            "SUT_requests": 0,
            "private_files_read": False,
            "existing_selfchecks_run": False,
            "fake_transport_requests": calls["fake_transport_requests"],
            "returned_status": result["status"],
            "returned_complete": result["complete"],
            "returned_error": result["error"],
            "finding": "UTC expiry is sampled only at initialization; forward UTC step is not checked",
            "limits": "not an actual OS clock change, real supervisor launch or TLS test",
        },
        indent=2,
    )
)
