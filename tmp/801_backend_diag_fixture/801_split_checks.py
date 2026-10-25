"""Owned two-stage checks: real source935 SQLite/API, stdlib TLS config, no cloud/network."""

import contextlib
import errno
import hashlib
import importlib
import io
import json
import os
import ssl
import subprocess
import sys
import time
from pathlib import Path
from types import SimpleNamespace

import pytest
from sqlalchemy import create_engine

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
http = importlib.import_module("801_http")
s1 = importlib.import_module("801_stage1")
s2 = importlib.import_module("801_stage2")


def store(path, value):
    fd = http.reserve(path)
    try:
        http.write_fd(fd, value)
    finally:
        os.close(fd)


def test_s2_import_is_source_free_stdlib_without_app_sql_or_network():
    code = """
import builtins,socket,sys,threading
original=builtins.__import__
def guarded(name,*args,**kwargs):
 if name=='t44' or name.startswith('t44.') or name=='sqlalchemy' or name.startswith('sqlalchemy.') or name=='fastapi' or name.startswith('fastapi.'):
  raise AssertionError('S2 product/SQL import forbidden')
 return original(name,*args,**kwargs)
builtins.__import__=guarded
def forbidden(*args,**kwargs): raise AssertionError('Import network/thread forbidden')
socket.socket.connect=threading.Thread.start=forbidden
sys.path.insert(0,sys.argv[1])
__import__('801_stage2')
print('STDLIB_SOURCE_FREE_OK')
"""
    result = subprocess.run(
        [sys.executable, "-I", "-c", code, str(HERE)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0 and result.stdout.strip() == "STDLIB_SOURCE_FREE_OK"


def test_real_s1_s2_first_tls_config_then_api_and_uncertain_previous_events(
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
            display_name="Owned split801",
            password_hash=HASHER.hash("owned-split-password"),
        )
        accounts[role] = {
            "username": username,
            "password": "owned-split-password",
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

    identities = {
        role: {key: account[key] for key in ("username", "user_id")}
        for role, account in accounts.items()
    }
    identity_path, account_path = (
        tmp_path / "identities.private.json",
        tmp_path / "accounts.private.json",
    )
    store(identity_path, identities)
    store(account_path, accounts)
    stage1_dir = tmp_path / "s1"
    args1 = [
        "--identities",
        str(identity_path),
        "--output-dir",
        str(stage1_dir),
        "--host",
        "owned-mysql",
        "--port",
        "3306",
        "--user",
        "owned",
        "--slots",
        "2",
    ]

    def forbidden_client(*_args, **_kwargs):
        raise AssertionError("S1 must never construct HTTP client")

    with monkeypatch.context() as guard:
        guard.setattr(s1.subprocess, "run", original_cli)
        guard.setattr(http, "Client", forbidden_client)
        assert s1.main(args1) == 0
    candidate_path = stage1_dir / "candidate.private.json"
    candidate = http.private_json(candidate_path)
    digest = hashlib.sha256(candidate_path.read_bytes()).hexdigest()
    assert len(executed) == 1 and executed[0].count("--project-id") == 40
    assert len(candidate["slots"]) == 2 and len(candidate["project_ids"]) == 40
    assert (
        candidate["provenance"]["total_escalation_events_before"]
        == candidate["provenance"]["total_escalation_events_after"]
        == 0
    )
    assert (
        candidate["service"]["session_id"] > 0 and candidate["service"]["access_token"]
    )
    assert candidate["service"]["project_ids"] == candidate["project_ids"]
    assert (
        candidate["service"]["scopes"] == ["escalation:write"]
        and candidate["service"]["actor_kind"] == 2
    )
    assert (
        candidate["provenance"]["event_rows_sha256_before"]
        == candidate["provenance"]["event_rows_sha256_after"]
    )
    assert (
        "owned-split-password" not in candidate_path.read_text()
        and "mysql+pymysql" not in candidate_path.read_text()
    )
    ca_path, key_path = tmp_path / "owned-ca.pem", tmp_path / "owned-ca.key"
    generated = subprocess.run(
        [
            "/usr/bin/openssl",
            "req",
            "-x509",
            "-newkey",
            "rsa:2048",
            "-nodes",
            "-days",
            "1",
            "-subj",
            "/CN=owned-split-root",
            "-keyout",
            str(key_path),
            "-out",
            str(ca_path),
        ],
        capture_output=True,
        check=False,
    )
    assert generated.returncode == 0
    ca_sha = hashlib.sha256(ca_path.read_bytes()).hexdigest()
    args2 = [
        "--accounts",
        str(account_path),
        "--candidate",
        str(candidate_path),
        "--candidate-sha256",
        digest,
        "--ca",
        str(ca_path),
        "--ca-sha256",
        ca_sha,
        "--url",
        "https://172.21.182.245:18445",
    ]
    with pytest.raises(FileNotFoundError):
        s2.main(
            [
                *args2,
                "--ca",
                str(tmp_path / "missing-ca.pem"),
                "--output-dir",
                str(tmp_path / "missing-ca"),
            ]
        )
    missing = json.loads(
        (tmp_path / "missing-ca/status.public.jsonl").read_text().splitlines()[-1]
    )
    assert (
        missing["phase"] == "public_ca_verification"
        and missing["errno"] == errno.ENOENT
    )
    configured = []

    def first_connection_boundary(connection):
        assert isinstance(connection._context, ssl.SSLContext)
        assert (
            connection._context.verify_mode == ssl.CERT_REQUIRED
            and connection._context.check_hostname
        )
        configured.append((connection.host, connection.port))
        raise OSError(errno.ENETUNREACH, "owned-no-real-network-marker")

    with monkeypatch.context() as guard:
        guard.setattr(
            http.http.client.HTTPSConnection, "connect", first_connection_boundary
        )
        with pytest.raises(OSError):
            s2.main([*args2, "--output-dir", str(tmp_path / "first-connect")])
    assert configured == [("172.21.182.245", 18445)]
    failed = (tmp_path / "first-connect/status.public.jsonl").read_text()
    failure = json.loads(failed.splitlines()[-1])
    assert (
        failure["phase"] == "three_real_tls_logins"
        and failure["errno"] == errno.ENETUNREACH
    )
    assert (
        failure["partial_event_commits_may_exist"] is False
        and failure["resumable"] is False
    )
    assert (
        "tls_client_configuration_ready" in failed
        and "owned-no-real-network-marker" not in failed
    )
    actual = TestClient(create_app(factory=factory, settings=Settings()))

    def real_api_call(self, path, token=None, body=None, key=None, sample=True):
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
        return value["data"]

    monkeypatch.setattr(http.Client, "call", real_api_call)
    stage2_dir = tmp_path / "s2"
    try:
        assert s2.main([*args2, "--output-dir", str(stage2_dir)]) == 0
        session_path = stage2_dir / "session.private.json"
        packet = http.private_json(session_path)
        assert len(packet["slots"]) == 2 and packet["stage1_candidate_sha256"] == digest
        assert "owned-split-password" not in session_path.read_text()
        http.check_packet(packet)
        assert (
            http.main(
                [
                    "--packet",
                    str(session_path),
                    "--ca",
                    str(ca_path),
                    "--output",
                    str(tmp_path / "driver.jsonl"),
                    "--updated-packet",
                    str(tmp_path / "updated.private.json"),
                    "--clients",
                    "1",
                    "--cycles",
                    "2",
                    "--seconds",
                    "10",
                ]
            )
            == 0
        )
        updated = http.private_json(tmp_path / "updated.private.json")
        assert updated["slots"][0]["transition"]["state"] == 2
        assert (
            updated["slots"][0]["transition"]["version"]
            == packet["slots"][0]["transition"]["version"] + 2
        )
        with factory() as uow:
            assert uow.gateway.count("escalation_events") == 2
        with monkeypatch.context() as guard:
            guard.setattr(s1.subprocess, "run", original_cli)
            guard.setattr(http, "Client", forbidden_client)
            with pytest.raises(http.InvalidDiagnostic):
                s1.main([*args1, "--output-dir", str(tmp_path / "s1-existing-events")])
        assert len(executed) == 1
        prior = json.loads(
            (tmp_path / "s1-existing-events/status.public.jsonl")
            .read_text()
            .splitlines()[-2]
        )
        assert prior["selected_existing_events"] == 2 and prior["total_events"] == 2
    finally:
        actual.close()
        engine.dispose()
