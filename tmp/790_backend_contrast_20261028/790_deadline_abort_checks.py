"""No-network diagnostic-protocol deadline/abort regressions, not product cases."""

import importlib
import importlib.util
import inspect
import json
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import MappingProxyType, SimpleNamespace

import pytest

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE / "edge"))
sys.path.insert(0, str(HERE / "data"))
http = importlib.import_module("790_http")
s1 = importlib.import_module("790_stage1")


class Clock(datetime):
    instant = datetime(2026, 10, 28, 7, 29, 58, tzinfo=UTC)

    @classmethod
    def now(cls, tz=None):
        return cls.instant


@pytest.fixture
def setup(monkeypatch):
    Clock.instant = datetime(2026, 10, 28, 7, 29, 58, tzinfo=UTC)
    control = {
        "url": "https://172.21.182.245:19445",
        "stop_utc": "2026-10-28T07:30:00Z",
        "anchor_at": "2026-10-28T04:00:00Z",
        "namespace": "t44-cloud-r28p7gen01-p",
        "binding_sha256": "a" * 64,
        "api_workers": 7,
        "seed": 44,
    }
    monkeypatch.setattr(http, "CONTROL", MappingProxyType(control))
    monkeypatch.setattr(http, "CONTROL_SHA256", "b" * 64)
    monkeypatch.setattr(http, "datetime", Clock)
    monkeypatch.setattr(s1, "datetime", Clock)
    monkeypatch.setattr(http.ssl, "create_default_context", lambda **_kwargs: object())
    events = []
    timeouts = []
    hooks = {"connect": None, "request": None}

    class Sock:
        def settimeout(self, timeout):
            timeouts.append(timeout)

    class Response:
        status = 200
        will_close = False

        def getheader(self, key):
            return "11111111-1111-4111-8111-111111111111" if key == "X-Request-ID" else None

        def read(self, _limit):
            return json.dumps(
                {
                    "data": {},
                    "meta": {"request_id": self.getheader("X-Request-ID"), "replayed": False},
                }
            ).encode()

    class Connection:
        def __init__(self, *args, timeout=15, **kwargs):
            self.timeout = timeout
            self.sock = Sock()
            timeouts.append(timeout)

        def connect(self):
            if hooks["connect"]:
                hooks["connect"]()

        def request(self, method, path, *args):
            events.append((Clock.instant, method, path))
            if hooks["request"]:
                hooks["request"]()

        def getresponse(self):
            return Response()

        def close(self):
            pass

    monkeypatch.setattr(http.http.client, "HTTPSConnection", Connection)
    return control, events, timeouts, hooks, Connection


@pytest.mark.parametrize(
    "path,body",
    [
        ("/api/v1/auth/login", {"username": "synthetic", "password": "owned-test-only"}),
        ("/api/v1/projects/1/tasks/1", None),
        ("/api/v1/projects/1/contract-validations", {"category": 2}),
        ("/api/v1/internal/projects/1/tasks/2/escalations", {"expected_version": 2}),
    ],
)
@pytest.mark.parametrize("reuse", [False, True])
def test_no_http_dispatch_after_absolute_deadline(setup, path, body, reuse):
    control, events, _timeouts, _hooks, connection = setup
    client = http.Client(control["url"], "unused-owned-ca")
    if reuse:
        client.connection = connection()
    Clock.instant = http.HARDSTOP + timedelta(microseconds=1)
    with pytest.raises(http.InvalidDiagnostic):
        client.call(path, body=body)
    assert events == []


def test_deadline_expiring_during_connect_prevents_http_dispatch(setup):
    control, events, _timeouts, hooks, _connection = setup
    hooks["connect"] = lambda: setattr(Clock, "instant", http.HARDSTOP + timedelta(microseconds=1))
    client = http.Client(control["url"], "unused-owned-ca")
    with pytest.raises(http.InvalidDiagnostic):
        client.call("/api/v1/auth/login", body={"owned": True})
    assert events == []


def test_connect_and_existing_socket_timeout_bounded_by_remaining_window(setup):
    control, events, timeouts, _hooks, _connection = setup
    client = http.Client(control["url"], "unused-owned-ca")
    assert client.call("/api/v1/projects/1/tasks/1") == {}
    assert len(events) == 1 and timeouts and max(timeouts) <= 2


def test_shared_abort_before_dispatch_is_checked_inside_client(setup):
    control, events, _timeouts, _hooks, _connection = setup
    client = http.Client(control["url"], "unused-owned-ca")
    client.abort = threading.Event()
    client.abort.set()
    with pytest.raises(http.InvalidDiagnostic):
        client.call("/api/v1/internal/projects/1/tasks/2/escalations", body={"owned": True})
    assert events == []


def test_shared_abort_during_connect_prevents_late_dispatch(setup):
    control, events, _timeouts, hooks, _connection = setup
    client = http.Client(control["url"], "unused-owned-ca")
    client.abort = threading.Event()
    hooks["connect"] = client.abort.set
    with pytest.raises(http.InvalidDiagnostic):
        client.call("/api/v1/internal/projects/1/tasks/2/escalations", body={"owned": True})
    assert events == []


def test_already_dispatched_response_can_finish_after_other_client_aborts(setup):
    control, events, _timeouts, hooks, _connection = setup
    client = http.Client(control["url"], "unused-owned-ca")
    client.abort = threading.Event()
    hooks["request"] = client.abort.set
    assert client.call("/api/v1/projects/1/tasks/1") == {}
    assert client.last["request_dispatch_attempted"] and client.last["body_read_complete"]
    assert len(events) == 1
    with pytest.raises(http.InvalidDiagnostic):
        client.call("/api/v1/projects/1/tasks/1")
    assert len(events) == 1


def test_deadline_after_dispatch_preserves_attempt_and_partial_response_state(setup):
    control, events, _timeouts, hooks, _connection = setup
    hooks["request"] = lambda: setattr(Clock, "instant", http.HARDSTOP + timedelta(microseconds=1))
    client = http.Client(control["url"], "unused-owned-ca")
    with pytest.raises(http.InvalidDiagnostic):
        client.call("/api/v1/internal/projects/1/tasks/2/escalations", body={"owned": True})
    assert len(events) == 1
    assert client.last["request_dispatch_attempted"] is True
    assert client.last["body_read_complete"] is False


def test_another_worker_failure_stops_later_operations_after_inflight_get(setup, monkeypatch):
    _control, _events, _timeouts, _hooks, _connection = setup
    rendezvous = threading.Barrier(2)
    failure_handled = threading.Event()
    shared_abort = threading.Event()
    calls = []

    def slot(identifier):
        return {
            "transition": {
                "id": identifier,
                "project_id": 1,
                "state": 2,
                "version": 1,
                "schedule_version": 1,
                "blocked_from_state": None,
            },
            "escalation": {
                "id": identifier + 100,
                "project_id": 1,
                "state": 2,
                "version": 2,
                "schedule_version": 1,
                "blocked_from_state": None,
            },
            "transition_role": "developer",
            "rule_version": 1,
            "scan_run_id": "11111111-1111-4111-8111-111111111111",
            "event_id": identifier + 200,
        }

    owned = [slot(1), slot(2)]

    class Client:
        def __init__(self, url, ca, **kwargs):
            self.last = {}
            self.connects = self.connect_ns = self.requests = 0

        def call(self, path, token=None, body=None, key=None, sample=True):
            if body is None:
                identifier = int(path.rsplit("/", 1)[1])
                self.index = identifier - 1
                calls.append((self.index, "get"))
                rendezvous.wait(timeout=2)
                if self.index == 0:
                    raise http.InvalidDiagnostic("Owned injected first-client failure")
                assert failure_handled.wait(timeout=2)
                return dict(owned[1]["transition"])
            calls.append((self.index, path))
            if path.endswith("contract-validations"):
                return {"valid": True}
            if path.endswith("transitions"):
                task = dict(owned[self.index]["transition"])
                task.update(
                    version=task["version"] + 1,
                    state=3 if task["state"] == 2 else 2,
                    blocked_from_state=2 if task["state"] == 2 else None,
                )
                return {"task": task}
            return {
                "created": False,
                "event": {"id": owned[self.index]["event_id"]},
                "task_version": 2,
            }

        def close(self):
            pass

    monkeypatch.setattr(http, "Client", Client)
    packet = {
        "url": "https://172.21.182.245:19445",
        "sessions": {"developer": {"access_token": "owned"}, "service": {"access_token": "owned"}},
    }
    start = threading.Barrier(3)
    deadline = [time.perf_counter() + 10]

    def run(index):
        args = (index, owned[index], packet, "unused-ca", start, deadline, 1)
        if "abort" in inspect.signature(http.worker).parameters:
            args += (shared_abort,)
        result = http.worker(*args)
        if index == 0:
            failure_handled.set()
        return result

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(run, index) for index in (0, 1)]
        start.wait(timeout=2)
        results = [future.result(timeout=3) for future in futures]
    assert results[0]["failed"] is True
    assert [value for index, value in calls if index == 1] == ["get"]
    assert results[1].get("aborted") is True and shared_abort.is_set()


def test_s1_reads_crossing_deadline_do_not_dispatch_service_token_cli(setup, monkeypatch, tmp_path):
    from t44 import persistence
    from t44.services import common

    _control, _events, _timeouts, _hooks, _connection = setup
    monkeypatch.setattr(http, "configure", lambda *_args: None)
    monkeypatch.setattr(s1.original, "guarded_settings", lambda *_args: (None, object()))
    monkeypatch.setattr(common, "task_model", lambda row: dict(row))

    class Gateway:
        def rows(self, *args, **kwargs):
            return []

        def count(self, *args, **kwargs):
            return 0

    class Scope:
        gateway = Gateway()

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

    monkeypatch.setattr(
        persistence, "create_mysql_engine", lambda _settings: SimpleNamespace(dispose=lambda: None)
    )
    monkeypatch.setattr(persistence, "SqlAlchemyUnitOfWorkFactory", lambda _engine: Scope)

    def candidates(*args, **kwargs):
        Clock.instant = http.HARDSTOP + timedelta(microseconds=1)
        return list(range(1, 41)), [{"id": 1}], [{"id": 2}], 1

    monkeypatch.setattr(s1.original, "candidates", candidates)
    writes = []

    def command(*args, **kwargs):
        writes.append(args)
        return SimpleNamespace(returncode=1, stdout=b"", stderr=b"")

    monkeypatch.setattr(s1.subprocess, "run", command)
    identities = tmp_path / "identities.private.json"
    fd = http.reserve(identities)
    try:
        http.write_fd(
            fd,
            {
                role: {"username": "owned-" + role, "user_id": index}
                for index, role in enumerate(("manager", "developer", "reviewer"), 1)
            },
        )
    finally:
        import os

        os.close(fd)
    with pytest.raises(http.InvalidDiagnostic):
        s1.main(
            [
                "--identities",
                str(identities),
                "--output-dir",
                str(tmp_path / "new-s1"),
                "--host",
                "mysql",
                "--port",
                "3306",
                "--user",
                "owned",
                "--slots",
                "1",
                "--control",
                "owned-control",
                "--control-sha256",
                "a" * 64,
            ]
        )
    assert writes == []


@pytest.mark.parametrize("expired", [False, True])
def test_host_oneoff_launch_budget_and_prefix_are_bounded(setup, monkeypatch, tmp_path, expired):
    spec = importlib.util.spec_from_file_location("owned_host790_deadline", HERE / "790_host.py")
    host = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(host)
    monkeypatch.setattr(host.bootstrap, "datetime", Clock)
    if expired:
        Clock.instant = http.HARDSTOP + timedelta(microseconds=1)
    calls = []

    def run(command, **kwargs):
        calls.append(kwargs["timeout"])
        Clock.instant = http.HARDSTOP + timedelta(microseconds=1)
        return SimpleNamespace(returncode=0, stdout=b"owned-prefix", stderr=b"")

    monkeypatch.setattr(host.subprocess, "run", run)
    public = tmp_path / "result.public.jsonl"
    host.bootstrap.save(public, {"diagnostic_valid": True})
    with pytest.raises(ValueError):
        host.run_owned(
            "owned",
            ["never-executed"],
            public,
            tmp_path,
            {"owned-image"},
            "owned",
            {},
            "2026-10-28T07:30:00Z",
        )
    if expired:
        assert calls == [] and not (tmp_path / "owned.stdout").exists()
    else:
        assert calls == [2.0]
        assert (tmp_path / "owned.stdout").read_bytes() == b"owned-prefix"
