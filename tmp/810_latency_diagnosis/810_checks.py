"""Owned ASGI stubs and SQLite only; no cloud, credentials, or existing database."""

import asyncio
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
    original = lambda _request: 201
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
