"""Zero-network probe of the explicitly PUBLIC Gate's total deadline boundary.

This simulates an overlong transport call. It is not a SUT or TLS test and does
not establish anything about the private suite. No private paths are opened.
"""

import datetime
import hashlib
import json
from pathlib import Path
from types import ModuleType, SimpleNamespace


CONTROL = Path(
    "/Users/yang/Desktop/nothing/软件开发大作业/"
    "tmp/829_independent_acceptance_20261025/PUBLIC/control.py"
)
EXPECTED = "3a1de1e9080937d0c6195caae6c7ead04e8a88ec158bf39934d5b69780e0579d"
assert hashlib.sha256(CONTROL.read_bytes()).hexdigest() == EXPECTED
control = ModuleType("public_829_control")
exec(compile(CONTROL.read_bytes(), str(CONTROL), "exec"), control.__dict__)

now = datetime.datetime(2026, 10, 25, tzinfo=datetime.timezone.utc)
clock = {"seconds": 0.0}
calls = {"socket": 0, "fake_close": 0}


class ClockDateTime(datetime.datetime):
    @classmethod
    def now(cls, tz=None):
        value = now + datetime.timedelta(seconds=clock["seconds"])
        return value if tz is not None else value.replace(tzinfo=None)


def no_socket(*_args, **_kwargs):
    calls["socket"] += 1
    raise AssertionError("No socket creation is allowed in this probe")


class FakeResponse:
    status = 200

    def getheaders(self):
        return []

    def read(self, _maximum):
        clock["seconds"] = 61.0
        return b"{}"


class FakeTLS:
    def __init__(self, *_args):
        self.timeout = _args[-1]

    def request(self, *_args, **_kwargs):
        pass

    def getresponse(self):
        return FakeResponse()

    def close(self):
        calls["fake_close"] += 1


records = []
control.socket = SimpleNamespace(create_connection=no_socket)
control.dt = SimpleNamespace(datetime=ClockDateTime, timezone=datetime.timezone)
control.time = SimpleNamespace(
    monotonic=lambda: clock["seconds"],
    monotonic_ns=lambda: int(clock["seconds"] * 1_000_000_000),
)
control.PinnedTLS = FakeTLS
grant = {
    "admitted": True,
    "tool_freeze_sha256": "synthetic-public-probe",
    "operator": "AI",
    "isolated_resource_ids": ["synthetic-no-resource"],
    "build": {"source_sha": "0" * 40, "image_digest": "synthetic-no-image"},
    "base_url": "https://not-contacted.invalid/api/v1",
    "pinned_ip": "127.0.0.1",
    "phase": "functional",
    "expires_at": (now + datetime.timedelta(seconds=1)).isoformat(),
    "max_wall_seconds": 2,
    "max_requests": 1,
    "max_concurrency": 1,
}
gate = control.Gate(
    grant,
    {"tool_freeze_sha256": grant["tool_freeze_sha256"]},
    [("GET", "/auth/me")],
    SimpleNamespace(append=records.append),
)
result = gate.request("GET", "/auth/me", timeout=0.1)
assert calls["socket"] == 0
assert result["status"] == 200 and result["complete"] is True
assert result["error"] is None and result["elapsed_ns"] == 61_000_000_000
assert len(records) == 1
print(
    json.dumps(
        {
            "control_sha256": EXPECTED,
            "method": "real PUBLIC Gate with fake transport and simulated time only",
            "actual_socket_calls": calls["socket"],
            "SUT_requests": 0,
            "private_files_read": False,
            "grant_expiry_after_seconds": 1,
            "grant_wall_seconds": 2,
            "requested_socket_timeout_seconds": 0.1,
            "simulated_transport_duration_seconds": 61,
            "returned_status": result["status"],
            "returned_complete": result["complete"],
            "returned_error": result["error"],
            "fake_connection_close_calls": calls["fake_close"],
            "finding": "PUBLIC Gate does not itself enforce a total in-flight deadline",
            "not_proven": "actual socket/TLS behavior or private suite watchdog behavior",
        },
        indent=2,
    )
)
