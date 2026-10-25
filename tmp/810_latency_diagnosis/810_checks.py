"""Owned ASGI stubs and SQLite only; no cloud, credentials, or existing database."""

import asyncio
import hashlib
import importlib.util
import json
import subprocess
import sys
import threading
import time
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.pool import QueuePool

MODULE = Path(__file__).with_name("810_stage.py")
SPEC = importlib.util.spec_from_file_location("owned_diag810", MODULE)
stage = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(stage)


def rows(probe):
    return [json.loads(line) for line in probe.path.read_text().splitlines()]


def record():
    return {"phases": {}, "pool_samples": []}


def engine_at(tmp_path):
    return create_engine(
        "sqlite:///" + str(tmp_path / "owned.sqlite"),
        poolclass=QueuePool,
        pool_size=1,
        max_overflow=0,
        pool_timeout=2,
        connect_args={"check_same_thread": False},
    )


def test_import_creates_no_app_thread_or_network():
    code = """
import builtins, importlib.util, socket, threading, sys
original = builtins.__import__
def denied(name, *args, **kwargs):
    if name == 't44' or name.startswith('t44.') or name.startswith('fastapi'):
        raise AssertionError('Application imported at module import')
    return original(name, *args, **kwargs)
builtins.__import__ = denied
def forbidden(*args, **kwargs):
    raise AssertionError('Thread/network side effect')
threading.Thread.start = forbidden
socket.socket.connect = forbidden
spec = importlib.util.spec_from_file_location('probe', sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
print('IMPORT_ONLY_OK')
"""
    result = subprocess.run(
        [sys.executable, "-I", "-c", code, str(MODULE)], capture_output=True, text=True
    )
    assert result.returncode == 0 and result.stdout.strip() == "IMPORT_ONLY_OK"


async def request(app, identifier, selected=True):
    messages = iter(
        [
            {"type": "http.request", "body": b"owned-sensitive-body", "more_body": True},
            {"type": "http.request", "body": b"-tail", "more_body": False},
        ]
    )
    sent = []

    async def receive():
        return next(messages)

    async def send(message):
        sent.append(dict(message))

    await app(
        {
            "type": "http",
            "headers": [(b"x-t44-diag-sample", b"1")] if selected else [],
            "owned_identifier": identifier,
        },
        receive,
        send,
    )
    return sent


def owned_app(handler):
    async def app(scope, receive, send):
        first, last = await receive(), await receive()
        assert first["body"] + last["body"] == b"owned-sensitive-body-tail"
        value = await asyncio.to_thread(
            handler, SimpleNamespace(state=SimpleNamespace(request_id=scope["owned_identifier"]))
        )
        await send(
            {
                "type": "http.response.start",
                "status": value,
                "headers": [(b"x-request-id", scope["owned_identifier"].encode())],
            }
        )
        await send({"type": "http.response.body", "body": b"fixed-public", "more_body": False})

    return app


def test_asgi_transparency_boundaries_and_sample_cap(tmp_path):
    engine = engine_at(tmp_path)
    probe = stage.Probe(engine, tmp_path, limit=1)

    def original(_request):
        return 201

    app = owned_app(probe.handler(original, "owned_stub"))
    wrapped = probe.wrap_asgi(app)
    identifier = str(uuid4())
    baseline = asyncio.run(request(app, identifier, selected=False))
    observed = asyncio.run(request(wrapped, identifier))
    asyncio.run(request(wrapped, str(uuid4())))
    probe.close()
    engine.dispose()
    assert observed == baseline
    item = next(row for row in rows(probe) if row["kind"] == "request")
    assert item["request_id"] == item["response_request_id"] == identifier
    assert item["ingress_ns"] <= item["body_consumed_ns"] <= item["handler_start_ns"]
    assert item["handler_start_ns"] < item["handler_end_ns"] <= item["response_start_ns"]
    assert item["response_start_ns"] <= item["send_end_ns"] <= item["app_return_ns"]
    assert item["response_bytes"] == len(b"fixed-public")
    assert rows(probe)[-1]["selected"] == rows(probe)[-1]["written"] == 1
    assert "owned-sensitive-body" not in probe.path.read_text()


def test_two_concurrent_requests_keep_context_and_actual_worker_thread_cpu(tmp_path):
    engine = engine_at(tmp_path)
    probe = stage.Probe(engine, tmp_path)
    barrier = threading.Barrier(2, timeout=2)

    def handler(request):
        assert probe.active.get()["request_id"] == request.state.request_id
        barrier.wait()
        return 200

    app = probe.wrap_asgi(owned_app(probe.handler(handler, "owned_concurrent")))
    identifiers = [str(uuid4()), str(uuid4())]

    async def run():
        return await asyncio.gather(*(request(app, identifier) for identifier in identifiers))

    asyncio.run(run())
    probe.close()
    engine.dispose()
    items = [row for row in rows(probe) if row["kind"] == "request"]
    assert {row["request_id"] for row in items} == set(identifiers)
    assert len({row["handler_thread"] for row in items}) == 2
    assert all(row["request_id"] == row["response_request_id"] for row in items)
    for row in items:
        phase = row["phases"]["sync_handler_inclusive"]
        assert 0 < phase["thread_cpu_ns"] <= phase["wall_ns"]


def test_real_queue_wait_is_causal_and_original_sql_binds_are_not_recorded(tmp_path):
    engine = engine_at(tmp_path)
    held = engine.connect()
    probe = stage.Probe(engine, tmp_path).install_database()
    condition = engine.pool._pool.not_empty
    original_wait = condition.wait
    entered = threading.Event()
    wait_started = []

    def waiting(timeout=None):
        wait_started.append(time.perf_counter_ns())
        entered.set()
        return original_wait(timeout)

    condition.wait = waiting
    row, failures, acquired = record(), [], threading.Event()

    def worker():
        token = probe.active.set(row)
        try:
            with engine.connect() as connection:
                acquired.set()
                assert (
                    connection.execute(
                        text("SELECT :marker"), {"marker": "owned-private-bind-marker"}
                    ).scalar_one()
                    == "owned-private-bind-marker"
                )
        except BaseException as error:
            failures.append(error)
        finally:
            probe.active.reset(token)

    thread = threading.Thread(target=worker)
    thread.start()
    try:
        assert entered.wait(2) and not acquired.is_set()
        assert engine.pool.checkedout() == 1
        release_ns = time.perf_counter_ns()
    finally:
        held.close()
    thread.join(3)
    assert not thread.is_alive() and not failures
    probe.emit({"kind": "owned_database", **row})
    probe.close()
    engine.dispose()
    assert row["phases"]["pool_queue_get_inclusive"]["wall_ns"] >= release_ns - wait_started[0]
    assert row["phases"]["cursor_execute_inclusive"]["calls"] == 1
    assert any(item["checkedout"] == 1 for item in row["pool_samples"])
    assert "owned-private-bind-marker" not in probe.path.read_text()
    assert not probe.errors


def test_actual_sql_error_class_is_preserved(tmp_path):
    engine = engine_at(tmp_path)
    probe = stage.Probe(engine, tmp_path).install_database()
    row = record()
    token = probe.active.set(row)
    try:
        with engine.connect() as connection, pytest.raises(OperationalError):
            connection.execute(text("SELECT no_such_column_owned810"))
    finally:
        probe.active.reset(token)
        probe.close()
        engine.dispose()
    assert row["phases"]["cursor_execute_inclusive"]["raised_classes"] == {"OperationalError": 1}
    assert not probe.errors


def test_observer_callback_failure_must_not_replace_success_or_sql_error(tmp_path, monkeypatch):
    engine = engine_at(tmp_path)
    probe = stage.Probe(engine, tmp_path).install_database()

    def failed_observer(*_args, **_kwargs):
        raise ArithmeticError("owned observation failure")

    monkeypatch.setattr(probe, "add", failed_observer)
    token = probe.active.set(record())
    try:
        with engine.connect() as connection:
            assert connection.execute(text("SELECT 1")).scalar_one() == 1
            with pytest.raises(OperationalError):
                connection.execute(text("SELECT no_such_column_owned810"))
    finally:
        probe.active.reset(token)
        probe.close()
        engine.dispose()
    assert probe.errors["ArithmeticError"] > 0
    assert rows(probe)[-1]["diagnostic_valid"] is False


def test_writer_failure_keeps_original_application_exception(tmp_path, monkeypatch, capsys):
    engine = engine_at(tmp_path)
    probe = stage.Probe(engine, tmp_path)
    original_write = stage.os.write
    error = LookupError("owned app original")

    def failed_write(fd, data):
        if fd == probe.fd:
            raise OSError("owned writer failure")
        return original_write(fd, data)

    async def app(_scope, _receive, _send):
        raise error

    monkeypatch.setattr(stage.os, "write", failed_write)
    try:
        with pytest.raises(LookupError) as observed:
            asyncio.run(request(probe.wrap_asgi(app), str(uuid4())))
        assert observed.value is error
    finally:
        probe.close()
        engine.dispose()
    assert probe.errors["OSError"] > 0 and "T44_DIAG_INVALID" in capsys.readouterr().err


def test_actual_source935_api_and_sqlite_preserve_response_and_internal_id(tmp_path):
    from fastapi.testclient import TestClient
    from t44.api import create_app
    from t44.contracts import OPERATIONS
    from t44.persistence import SqlAlchemyUnitOfWorkFactory
    from t44.persistence.accounts import initialize_user
    from t44.persistence.schema import metadata
    from t44.services.identity import HASHER
    from t44.settings import Settings

    engine = engine_at(tmp_path)
    metadata.create_all(engine)
    factory = SqlAlchemyUnitOfWorkFactory(engine)
    initialize_user(
        factory,
        username="owned810",
        display_name="Owned diagnostic user",
        password_hash=HASHER.hash("owned-810-password"),
    )
    with TestClient(create_app(factory=factory, settings=Settings())) as client:
        token = client.post(
            "/api/v1/auth/login", json={"username": "owned810", "password": "owned-810-password"}
        ).json()["data"]["access_token"]
        baseline = client.get(
            "/api/v1" + OPERATIONS["getMe"]["path"], headers={"Authorization": "Bearer " + token}
        )
    app = create_app(factory=factory, settings=Settings())
    probe = stage.Probe(engine, tmp_path).install_database().install_application(app)
    try:
        with TestClient(probe.wrap_asgi(app)) as client:
            observed = client.get(
                "/api/v1" + OPERATIONS["getMe"]["path"],
                headers={"Authorization": "Bearer " + token, "x-t44-diag-sample": "1"},
            )
        assert baseline.status_code == observed.status_code == 200
        assert baseline.json()["data"] == observed.json()["data"]
        item = next(row for row in rows(probe) if row["kind"] == "request")
        assert item["request_id"] == item["response_request_id"] == observed.headers["x-request-id"]
        assert item["request_id"] == observed.json()["meta"]["request_id"]
        assert item["operation"] == "getMe"
        for phase in (
            "sync_handler_inclusive",
            "runtime_execute",
            "api_schema_validation",
            "json_response_render",
            "cursor_execute_inclusive",
        ):
            assert item["phases"][phase]["calls"] > 0
        assert rows(probe)[-1]["diagnostic_valid"] is True
        assert (
            token not in probe.path.read_text()
            and "owned-810-password" not in probe.path.read_text()
        )
    finally:
        probe.close()
        engine.dispose()


def test_network_parser_only_keeps_neutral_counts():
    path = MODULE.with_name("810_net_snapshot.py")
    spec = importlib.util.spec_from_file_location("owned_net810", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    result = module.parse_ss(
        "ESTAB 0 8 10.0.0.2:44556 10.0.0.3:18099\nTIME-WAIT 0 0 10.0.0.2:44557 10.0.0.3:18099\nLISTEN 2 2048 0.0.0.0:18099 0.0.0.0:*",
        18099,
        (32768, 60999),
    )
    assert result["distinct_local_ephemeral_ports"] == 2
    assert result["api_port_states"] == {"ESTAB": 1, "TIME-WAIT": 1, "LISTEN": 1}
    assert result["api_listen_reported_queue_sums"] == {"recvq": 2, "sendq": 2048}
    assert result["sendq_bytes_sum_non_listen"] == 8
    assert "10.0.0" not in json.dumps(result)


@pytest.mark.parametrize("invalid", ["allow", "module", "port", "schema", "host", "user"])
def test_factory_rejects_invalid_admission_before_engine_creation(monkeypatch, tmp_path, invalid):
    from t44 import persistence

    def forbidden(*_args, **_kwargs):
        raise AssertionError("Must not create engine for invalid diagnostic target")

    monkeypatch.setattr(persistence, "create_mysql_engine", forbidden)
    values = {
        "T44_DIAG_ALLOW": "source935-development-only",
        "T44_DIAG_PRODUCT_SHA": stage.PRODUCT,
        "T44_DIAG_MODULE_SHA256": hashlib.sha256(MODULE.read_bytes()).hexdigest(),
        "DATABASE_URL": "mysql+pymysql://owned:synth@owned-mysql:3306/t44_diag810_owned",
        "T44_DATABASE": "t44_diag810_owned",
        "T44_DIAG_DATABASE": "t44_diag810_owned",
        "T44_DIAG_HOST": "owned-mysql",
        "T44_DIAG_PORT": "3306",
        "T44_DIAG_USER": "owned",
        "T44_DIAG_OUTPUT": str(tmp_path),
    }
    for key, value in values.items():
        monkeypatch.setenv(key, value)
    if invalid == "port":
        monkeypatch.setenv("DATABASE_URL", values["DATABASE_URL"].replace(":3306/", ":13306/"))
        monkeypatch.setenv("T44_DIAG_PORT", "13306")
    else:
        key, value = {
            "allow": ("T44_DIAG_ALLOW", "no"),
            "module": ("T44_DIAG_MODULE_SHA256", "0" * 64),
            "schema": ("T44_DIAG_DATABASE", "old_application"),
            "host": ("T44_DIAG_HOST", "another-host"),
            "user": ("T44_DIAG_USER", "another-user"),
        }[invalid]
        monkeypatch.setenv(key, value)
    with pytest.raises(ValueError):
        stage.app_factory()


def test_owned_engine_close_is_once_and_restores_original_pool_methods(tmp_path):
    engine = engine_at(tmp_path)
    probe = stage.Probe(engine, tmp_path).install_database()
    restored = list(probe.restores)
    disposed = []

    def close_owned():
        disposed.append(True)
        engine.dispose()

    probe.on_close = close_owned
    with engine.connect() as connection:
        assert connection.execute(text("SELECT 1")).scalar_one() == 1
    probe.close()
    probe.close()
    assert disposed == [True]
    assert all(getattr(owner, name) == original for owner, name, original in restored)
    final = rows(probe)[-1]
    assert final["checkedout_before_owner_dispose"] == 0
    assert final["owner_dispose_requested"] and final["diagnostic_valid"]
