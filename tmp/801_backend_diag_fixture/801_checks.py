"""Owned offline/SQLite diagnostic checks; no live runtime/credential access."""

import contextlib
import importlib
import io
import json
import os
import subprocess
import sys
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pytest
from sqlalchemy import create_engine

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
http = importlib.import_module("801_http")
prepare = importlib.import_module("801_prepare")


def store(path, value):
    fd = http.reserve(path)
    try:
        http.write_fd(fd, value)
    finally:
        os.close(fd)


def test_import_has_no_product_file_network_or_thread_side_effect():
    code = """
import builtins, socket, threading, sys
original = builtins.__import__
def guarded(name, *args, **kwargs):
    if name == 't44' or name.startswith('t44.'):
        raise AssertionError('Product imported')
    return original(name, *args, **kwargs)
builtins.__import__ = guarded
def forbidden(*args, **kwargs):
    raise AssertionError('Side effect')
socket.socket.connect = threading.Thread.start = forbidden
sys.path.insert(0, sys.argv[1])
__import__('801_prepare')
print('IMPORT_OK')
"""
    result = subprocess.run(
        [sys.executable, "-I", "-c", code, str(HERE)],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0 and result.stdout.strip() == "IMPORT_OK"


@pytest.mark.parametrize(
    "url",
    [
        "http://172.21.182.245:18445",
        "https://172.21.182.245:18444",
        "https://other:18445",
        "https://user:secret@172.21.182.245:18445",
    ],
)
def test_exact_tls_admission(url):
    with pytest.raises(http.InvalidDiagnostic):
        http.target(url)


def test_private_file_and_output_are_no_overwrite_no_symlink(tmp_path):
    path = tmp_path / "owned.private.json"
    store(path, {"owned": True})
    assert http.private_json(path) == {"owned": True}
    with pytest.raises(FileExistsError):
        http.reserve(path)
    link = tmp_path / "link"
    link.symlink_to(path)
    with pytest.raises(OSError):
        http.private_json(link)
    path.chmod(0o644)
    with pytest.raises(http.InvalidDiagnostic):
        http.private_json(path)


@pytest.mark.parametrize(
    "database,port,user",
    [
        ("t44_p816", 3306, "owned"),
        (http.DATABASE + "_near", 3306, "owned"),
        (http.DATABASE, 13306, "owned"),
        (http.DATABASE, 3306, "root"),
    ],
)
def test_db_guard_rejects_old_near_port_root_without_engine(
    monkeypatch, database, port, user
):
    from t44 import persistence

    def forbidden(*_args, **_kwargs):
        raise AssertionError("Engine must not be created")

    monkeypatch.setattr(persistence, "create_mysql_engine", forbidden)
    monkeypatch.setenv("T44_DIAG_ALLOW", "source935-development-only")
    monkeypatch.setenv("T44_DIAG_PRODUCT_SHA", http.PRODUCT)
    monkeypatch.setenv("T44_DATABASE", database)
    monkeypatch.setenv(
        "DATABASE_URL", f"mysql+pymysql://{user}:owned@owned-mysql:{port}/{database}"
    )
    with pytest.raises(http.InvalidDiagnostic):
        prepare.guarded_settings("owned-mysql", port, user)


def test_packet_rejects_failed_expired_or_colliding_tasks():
    sessions = {
        role: {"expires_at": (datetime.now(UTC) + timedelta(minutes=30)).isoformat()}
        for role in ("manager", "developer", "reviewer", "service")
    }
    packet = {
        "kind": "source935-development-only",
        "product": http.PRODUCT,
        "database": http.DATABASE,
        "url": "https://172.21.182.245:18445",
        "created_at": http.utc(),
        "resumable": True,
        "sessions": sessions,
        "slots": [{"transition": {"id": 1}, "escalation": {"id": 2}}],
    }
    http.check_packet(packet)
    packet["resumable"] = False
    with pytest.raises(http.InvalidDiagnostic):
        http.check_packet(packet)
    packet["resumable"] = True
    packet["created_at"] = (datetime.now(UTC) - timedelta(seconds=601)).isoformat()
    with pytest.raises(http.InvalidDiagnostic):
        http.check_packet(packet)
    packet["created_at"] = http.utc()
    packet["slots"][0]["escalation"]["id"] = 1
    with pytest.raises(http.InvalidDiagnostic):
        http.check_packet(packet)


def test_transport_strict_ca_reuses_connection_and_never_retries_reset(monkeypatch):
    contexts, connections = [], []
    identifier = str(uuid4())

    def strict_context(*, cafile):
        contexts.append(cafile)
        return "owned-strict-context"

    class Response:
        status, will_close = 200, False

        def read(self, size):
            assert size == 2 * 1048576 + 1
            return json.dumps(
                {
                    "data": {"real": "owned-stub-only"},
                    "meta": {"request_id": identifier, "replayed": False},
                }
            ).encode()

        def getheader(self, name):
            return identifier if name == "X-Request-ID" else "app;dur=1.000"

    class Connection:
        def __init__(self, host, port, timeout, context):
            assert (host, port, context) == (
                "172.21.182.245",
                18445,
                "owned-strict-context",
            )
            self.sent, self.reset = [], False
            self.connected = self.closed = 0
            connections.append(self)

        def connect(self):
            self.connected += 1

        def request(self, *args):
            self.sent.append(args)
            if self.reset:
                raise ConnectionResetError("owned-private-marker-not-in-result")

        def getresponse(self):
            return Response()

        def close(self):
            self.closed += 1

    monkeypatch.setattr(http.ssl, "create_default_context", strict_context)
    monkeypatch.setattr(http.http.client, "HTTPSConnection", Connection)
    client = http.Client("https://172.21.182.245:18445", "owned-ca")
    for _ in range(2):
        assert client.call("/owned", "owned-token")["real"] == "owned-stub-only"
    assert contexts == ["owned-ca"] and len(connections) == client.connects == 1
    assert client.requests == 2 and len(connections[0].sent) == 2
    connections[0].reset = True
    with pytest.raises(ConnectionResetError):
        client.call("/owned", "owned-token")
    assert len(connections) == 1 and len(connections[0].sent) == 3
    assert connections[0].closed == 1 and client.connection is None
    assert "owned-private-marker" not in json.dumps(client.last)


def test_real_original_cli_three_login_sql_create_dedup_and_versioned_http_cycles(
    tmp_path, monkeypatch
):
    from fastapi.testclient import TestClient
    from t44 import cli, persistence
    from t44.api import create_app
    from t44.persistence.accounts import initialize_user
    from t44.persistence.schema import metadata
    from t44.persistence.seed import seed_demo
    from t44.services.identity import HASHER
    from t44.settings import Settings

    engine = create_engine(
        "sqlite:///" + str(tmp_path / "owned.sqlite"),
        connect_args={"check_same_thread": False},
    )
    metadata.create_all(engine)
    factory = persistence.SqlAlchemyUnitOfWorkFactory(engine)
    accounts = {}
    for role in ("manager", "developer", "reviewer"):
        username = "synthetic-" + role
        uid = initialize_user(
            factory,
            username=username,
            display_name="Owned801",
            password_hash=HASHER.hash("owned-801-password"),
        )
        accounts[role] = {
            "username": username,
            "password": "owned-801-password",
            "user_id": uid,
        }
    seed_demo(factory, projects=40, tasks=400, dependencies=400, records=600)
    monkeypatch.setenv("T44_DIAG_ALLOW", "source935-development-only")
    monkeypatch.setenv("T44_DIAG_PRODUCT_SHA", http.PRODUCT)
    monkeypatch.setenv("T44_DATABASE", http.DATABASE)
    monkeypatch.setenv(
        "DATABASE_URL", f"mysql+pymysql://owned:synth@owned-mysql:3306/{http.DATABASE}"
    )
    monkeypatch.setattr(persistence, "create_mysql_engine", lambda _settings: engine)
    monkeypatch.setattr(cli, "create_mysql_engine", lambda _settings: engine)
    executed = []

    def original_cli(command, **kwargs):
        assert kwargs["stdin"] == subprocess.DEVNULL and kwargs["timeout"] == 60
        executed.append(command)
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            status = cli.main(command[3:])
        return SimpleNamespace(
            returncode=status, stdout=output.getvalue().encode(), stderr=b""
        )

    monkeypatch.setattr(prepare.subprocess, "run", original_cli)
    app = create_app(factory=factory, settings=Settings())
    actual = TestClient(app)

    class OwnedASGIClient:
        def __init__(self, url, ca, timeout=15):
            http.target(url)
            assert ca == "owned-ca-not-opened"
            self.last = None
            self.requests = self.connects = self.connect_ns = 0

        def call(self, path, token=None, body=None, key=None, sample=True):
            headers = {}
            if token:
                headers["Authorization"] = "Bearer " + token
            if key:
                headers["Idempotency-Key"] = key
            start = time.perf_counter_ns()
            response = actual.request(
                "GET" if body is None else "POST", path, json=body, headers=headers
            )
            value = response.json()
            self.last = {
                "status": response.status_code,
                "request_id": response.headers.get("x-request-id"),
                "wall_ns": time.perf_counter_ns() - start,
            }
            self.requests += 1
            assert response.status_code < 300, value.get("code")
            assert value["meta"]["replayed"] is False
            assert str(uuid4()) != value["meta"]["request_id"]
            return value["data"]

        def close(self):
            pass

    monkeypatch.setattr(http, "Client", OwnedASGIClient)
    account_path = tmp_path / "accounts.private.json"
    store(account_path, accounts)
    common = [
        "--accounts",
        str(account_path),
        "--url",
        "https://172.21.182.245:18445",
        "--ca",
        "owned-ca-not-opened",
        "--host",
        "owned-mysql",
        "--port",
        "3306",
        "--user",
        "owned",
    ]
    inspected = tmp_path / "readonly-inspection"
    assert (
        prepare.main(
            [
                *common,
                "--output-dir",
                str(inspected),
                "--slots",
                "400",
                "--inspect-only",
            ]
        )
        == 0
    )
    profile = json.loads(
        (inspected / "status.public.jsonl").read_text().splitlines()[0]
    )
    assert (
        profile["eligible_transition_tasks"] == 40 and profile["tasks_observed"] == 400
    )
    assert profile["requested_slots"] == 400 and profile["sufficient_observed"] is False
    assert (
        profile["dependencies_observed"] == 400 and profile["projects_observed"] == 40
    )
    assert executed == [] and not (inspected / "session.private.json").exists()
    insufficient = tmp_path / "insufficient"
    with pytest.raises(http.InvalidDiagnostic):
        prepare.main([*common, "--output-dir", str(insufficient), "--slots", "400"])
    profile = json.loads(
        (insufficient / "status.public.jsonl").read_text().splitlines()[0]
    )
    assert (
        profile["sufficient_observed"] is False
        and profile["not_a_business_defect_if_insufficient"] is True
    )
    assert executed == [] and not (insufficient / "session.private.json").exists()
    failure_status = json.loads(
        (insufficient / "status.public.jsonl").read_text().splitlines()[-1]
    )
    assert failure_status["partial_business_commits_may_exist"] is False
    output = tmp_path / "fresh-prepared"
    try:
        assert (
            prepare.main(
                [
                    "--accounts",
                    str(account_path),
                    "--output-dir",
                    str(output),
                    "--url",
                    "https://172.21.182.245:18445",
                    "--ca",
                    "owned-ca-not-opened",
                    "--host",
                    "owned-mysql",
                    "--port",
                    "3306",
                    "--user",
                    "owned",
                    "--slots",
                    "2",
                ]
            )
            == 0
        )
        assert len(executed) == 1
        assert executed[0].count("--project-id") == 40
        packet = http.private_json(output / "session.private.json")
        assert len(packet["slots"]) == 2
        assert "owned-801-password" not in (output / "session.private.json").read_text()
        initial = packet["slots"][0]["transition"].copy()
        for index, cycles in enumerate((1, 1)):
            previous = output / (
                "session.private.json" if index == 0 else "updated0.private.json"
            )
            report = output / f"http{index}.jsonl"
            updated = output / f"updated{index}.private.json"
            assert (
                http.main(
                    [
                        "--packet",
                        str(previous),
                        "--ca",
                        "owned-ca-not-opened",
                        "--output",
                        str(report),
                        "--updated-packet",
                        str(updated),
                        "--clients",
                        "1",
                        "--cycles",
                        str(cycles),
                        "--seconds",
                        "10",
                    ]
                )
                == 0
            )
            result = json.loads(report.read_text().splitlines()[0])
            assert result["failed_clients"] == 0 and result["status_counts"] == {
                "200": 3,
                "202": 1,
            }
            assert len(result["results"][0]["rows"]) == 4
            latest = http.private_json(updated)
            assert (
                latest["slots"][0]["transition"]["version"]
                == initial["version"] + index + 1
            )
            assert latest["slots"][0]["transition"]["state"] == (3 if index == 0 else 2)
            assert latest["resumable"] is True
            for session in packet["sessions"].values():
                assert session["access_token"] not in report.read_text()
        with factory() as uow:
            assert uow.gateway.count("escalation_events") == 2
        original_call = OwnedASGIClient.call

        def committed_then_disconnected(self, path, *args, **kwargs):
            value = original_call(self, path, *args, **kwargs)
            if path.endswith("/transitions"):
                raise ConnectionResetError("owned-private-failure-detail")
            return value

        monkeypatch.setattr(OwnedASGIClient, "call", committed_then_disconnected)
        uncertain_path = output / "uncertain.private.json"
        failure_path = output / "failure.jsonl"
        assert (
            http.main(
                [
                    "--packet",
                    str(output / "updated1.private.json"),
                    "--ca",
                    "owned-ca-not-opened",
                    "--output",
                    str(failure_path),
                    "--updated-packet",
                    str(uncertain_path),
                    "--clients",
                    "1",
                    "--cycles",
                    "1",
                    "--seconds",
                    "10",
                ]
            )
            == 1
        )
        uncertain = http.private_json(uncertain_path)
        assert uncertain["resumable"] is False
        with pytest.raises(http.InvalidDiagnostic):
            http.check_packet(uncertain)
        with factory() as uow:
            actual_task = uow.gateway.get("tasks", initial["id"])
            assert actual_task["version"] == initial["version"] + 3
            assert actual_task["state"] == 3
            assert (
                uncertain["slots"][0]["transition"]["version"] == initial["version"] + 2
            )
        failure = json.loads(failure_path.read_text().splitlines()[0])
        assert failure["failed_clients"] == 1
        assert failure["results"][0]["rows"][-1]["failure"] == "ConnectionResetError"
        assert "owned-private-failure-detail" not in failure_path.read_text()
    finally:
        actual.close()
        engine.dispose()
