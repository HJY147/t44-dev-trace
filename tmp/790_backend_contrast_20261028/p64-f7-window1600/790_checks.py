"""Owned local tool guards; no cloud operations or independent cases."""

import ast
import contextlib
import hashlib
import importlib.util
import io
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

UTC = timezone.utc  # noqa: UP017 -- validate host Python 3.10 compatibility.
HERE = Path(__file__).parent


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


bootstrap = load(HERE / "790_bootstrap.py", "owned_bootstrap790")


@pytest.fixture
def real_derived_binding(tmp_path):
    tree = ast.parse((HERE / "fixtures/generation-f7.PUBLIC.py").read_text())
    prepare = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "prepare")
    binding = next(
        n.value
        for n in ast.walk(prepare)
        if isinstance(n, ast.Assign)
        and len(n.targets) == 1
        and isinstance(n.targets[0], ast.Name)
        and n.targets[0].id == "binding"
    )
    hashes = []

    def sha(path):
        hashes.append(path.name)
        return "c" * 64

    context = {
        "lib": SimpleNamespace(stamp=lambda: "2026-10-28T05:00:00Z"),
        "role": "p",
        "project": "t44-cloud-r28p64gen01-p",
        "database": "t44c_r28p64gen01_p",
        "SOURCE": bootstrap.SOURCE,
        "OLD_SOURCE": "935ab5b93bea788672c2b4a088c79cfeed848954",
        "SOURCE_COUNT": 53,
        "phase": tmp_path / "p",
        "sha": sha,
        "manifest": {"source_archive_sha256": "a" * 64},
        "args": SimpleNamespace(
            source_manifest_sha256="b" * 64,
            upgrade_binding_sha256="d" * 64,
            output=tmp_path,
            stop_utc="2026-10-28T16:00:00Z",
        ),
        "proofs": {
            "backend": {"actual_id": "sha256:" + "e" * 64, "config_id": "sha256:" + "f" * 64}
        },
        "images": {"backend": {"alias": "owned-backend"}, "web": {"alias": "owned-web"}},
        "upgrade": {"frozen_file_set_sha256": "a" * 64},
        "address": "172.21.182.245",
        "tls_port": 19445,
        "workers": 64,
        "plan": {"api_workers": 64, "api_pool_size": 5, "api_max_overflow": 0},
        "tls": {"ca_sha256": "a" * 64},
    }
    result = eval(compile(ast.Expression(binding), "real-derived-binding", "eval"), context)
    assert "actual-source-files.json" in hashes and "actual53-source-files.json" not in hashes
    assert result["source_file_count"] == 53
    assert "source_actual_proof_sha256" in result and "source53_actual_proof_sha256" not in result
    return result


def test_real_derived_binding_shape_and_live_gate(real_derived_binding):
    assert (
        bootstrap.validate_binding(real_derived_binding, datetime(2026, 10, 28, 5, tzinfo=UTC))
        == "r28p64gen01"
    )


@pytest.mark.parametrize(
    "key,value",
    [
        ("source_sha", "935ab5b93bea788672c2b4a088c79cfeed848954"),
        ("generation_kind", "exact-f4-production-entry-generation"),
        ("phase", "f"),
        ("database", "t44c_old_p"),
        ("api_workers", 7),
        ("entrypoint", "810_stage:app_factory"),
        ("profiling", True),
        ("source_file_count", True),
        ("stop_utc", "2026-10-28T17:00:00Z"),
    ],
)
def test_wrong_binding_rejected(real_derived_binding, key, value):
    with pytest.raises(ValueError):
        bootstrap.validate_binding(
            {**real_derived_binding, key: value}, datetime(2026, 10, 28, 5, tzinfo=UTC)
        )


def test_expired_and_near_deadline_rejected(real_derived_binding):
    for hour, minute in [(15, 59), (17, 0)]:
        with pytest.raises(ValueError):
            bootstrap.validate_binding(
                real_derived_binding, datetime(2026, 10, 28, hour, minute, tzinfo=UTC)
            )


def test_host_310_syntax_and_utc_parser():
    raw = (HERE / "790_bootstrap.py").read_text()
    for name in ("790_host.py", "790_load.py"):
        host_tree = ast.parse((HERE / name).read_text(), feature_version=(3, 10))
        assert not any(
            isinstance(n, ast.ImportFrom)
            and n.module == "datetime"
            and any(a.name == "UTC" for a in n.names)
            for n in ast.walk(host_tree)
        )
    tree = ast.parse(raw, feature_version=(3, 10))
    assert not any(
        isinstance(n, ast.ImportFrom)
        and n.module == "datetime"
        and any(a.name == "UTC" for a in n.names)
        for n in ast.walk(tree)
    )
    assert bootstrap.stamp("2026-10-28T16:00:00Z") == datetime(2026, 10, 28, 16, 0, tzinfo=UTC)
    with pytest.raises(ValueError):
        bootstrap.stamp("2026-10-28T16:00:00")


def test_private_file_symlink_and_output_preservation(tmp_path):
    path = tmp_path / "owned.json"
    bootstrap.save(path, {"owned": True})
    with pytest.raises(FileExistsError):
        bootstrap.save(path, {"owned": False})
    assert bootstrap.raw(path, True) == b'{\n  "owned": true\n}\n'
    link = tmp_path / "link"
    link.symlink_to(path)
    with pytest.raises(OSError):
        bootstrap.raw(link, True)
    path.chmod(0o644)
    with pytest.raises(ValueError):
        bootstrap.raw(path, True)


def test_source_free_edge_import_without_file_network_or_threads():
    code = """import builtins,socket,threading,sys
original=builtins.__import__
def guarded(name,*args,**kwargs):
 if name=='t44' or name.startswith('t44.') or name in ('sqlalchemy','fastapi','pymysql'): raise AssertionError('product import')
 return original(name,*args,**kwargs)
builtins.__import__=guarded
def forbidden(*args,**kwargs):raise AssertionError('network/thread started')
socket.socket.connect=threading.Thread.start=forbidden
sys.path.insert(0,sys.argv[1]);__import__('790_http');__import__('790_stage2')
print('SOURCE_FREE_IMPORT_OK')
"""
    result = subprocess.run(
        [sys.executable, "-I", "-c", code, str(HERE / "edge")],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0 and result.stdout.strip() == "SOURCE_FREE_IMPORT_OK"


def test_real_f7_v2_seed_candidates_cli_sessions_and_original_http(tmp_path, monkeypatch):
    from uuid import UUID

    from fastapi.testclient import TestClient
    from sqlalchemy import create_engine
    from t44 import cli, persistence
    from t44.api import create_app
    from t44.persistence.schema import metadata
    from t44.persistence.seed import seed_demo
    from t44.settings import Settings

    assert "product-source" in cli.__file__
    sys.path.insert(0, str(HERE / "edge"))
    sys.path.insert(0, str(HERE / "data"))
    http = __import__("790_http")
    s1 = __import__("790_stage1")
    s2 = __import__("790_stage2")
    select = __import__("790_select")
    http.CONTROL = None
    control = {
        "kind": http.KIND,
        "source_sha": bootstrap.SOURCE,
        "run_id": "r28p64gen01",
        "binding_sha256": "c" * 64,
        "namespace": "t44-cloud-r28p64gen01-p",
        "database": "t44c_r28p64gen01_p",
        "api_workers": 64,
        "url": "https://172.21.182.245:19445",
        "ca_sha256": hashlib.sha256(b"owned-ca").hexdigest(),
        "stop_utc": "2026-10-28T16:00:00Z",
        "seed": 44,
        "anchor_at": bootstrap.ANCHOR,
    }
    from grant_fixture import pressure
    control = pressure(control)
    control_path = tmp_path / "control.private.json"
    bootstrap.save(control_path, control)
    control_sha = hashlib.sha256(control_path.read_bytes()).hexdigest()
    ca = tmp_path / "ca.pem"
    ca.write_bytes(b"owned-ca")
    http.configure(str(control_path), control_sha)
    engine = create_engine(
        "sqlite:///" + str(tmp_path / "owned.sqlite"), connect_args={"check_same_thread": False}
    )
    metadata.create_all(engine)
    factory = persistence.SqlAlchemyUnitOfWorkFactory(engine)
    monkeypatch.setenv(
        "DATABASE_URL", "mysql+pymysql://owned:synthetic@mysql:3306/" + control["database"]
    )
    monkeypatch.setenv("T44_DATABASE", control["database"])
    monkeypatch.setenv("T44_CONTRAST_ALLOW", http.KIND)
    monkeypatch.setenv("T44_CONTRAST_SOURCE", bootstrap.SOURCE)
    monkeypatch.setattr(persistence, "create_mysql_engine", lambda _settings: engine)
    monkeypatch.setattr(cli, "create_mysql_engine", lambda _settings: engine)
    accounts = {}
    try:
        for role in ("manager", "developer", "reviewer"):
            output = io.StringIO()
            monkeypatch.setattr(sys, "stdin", io.StringIO("owned-contrast-password\n"))
            with contextlib.redirect_stdout(output):
                assert (
                    cli.main(
                        [
                            "init-user",
                            "--username",
                            "synthetic-" + role,
                            "--display-name",
                            "[synthetic] owned",
                            "--password-stdin",
                        ]
                    )
                    == 0
                )
            accounts[role] = {
                "username": "synthetic-" + role,
                "password": "owned-contrast-password",
                "user_id": json.loads(output.getvalue())["user_id"],
            }
        seeded = seed_demo(factory, seed=44, anchor_at=http.parse_utc(bootstrap.ANCHOR))
        assert (
            seeded["manifest"]["version"] == 2
            and seeded["tasks"] == 6000
            and seeded["dependencies"] == 9000
        )
        assert seeded["reviews"] + seeded["decisions"] == 15000
        with factory() as u:
            projects, left, right, _ = select.candidates(
                u.gateway, accounts, 441, http.parse_utc(bootstrap.ANCHOR), lambda _v: None
            )
            assert len(projects) == 40 and len(left) == len(right) == 441
            assert len({r["id"] for r in left + right}) == 882

        def actual_cli(command, **kwargs):
            assert command[1:3] == ["-m", "t44.cli"]
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                status = cli.main(command[3:])
            return SimpleNamespace(returncode=status, stdout=output.getvalue().encode(), stderr=b"")

        monkeypatch.setattr(s1.subprocess, "run", actual_cli)
        identities = {
            role: {k: v[k] for k in ("username", "user_id")} for role, v in accounts.items()
        }
        identity_path = tmp_path / "identities.private.json"
        bootstrap.save(identity_path, identities)
        account_path = tmp_path / "accounts.private.json"
        bootstrap.save(account_path, accounts)
        s1_dir = tmp_path / "s1"
        assert (
            s1.main(
                [
                    "--identities",
                    str(identity_path),
                    "--output-dir",
                    str(s1_dir),
                    "--host",
                    "mysql",
                    "--port",
                    "3306",
                    "--user",
                    "owned",
                    "--slots",
                    "4",
                    "--control",
                    str(control_path),
                    "--control-sha256",
                    control_sha,
                ]
            )
            == 0
        )
        candidate_path = s1_dir / "candidate.private.json"
        candidate_sha = hashlib.sha256(candidate_path.read_bytes()).hexdigest()
        app = create_app(factory=factory, settings=Settings(login_attempts=1000))
        with TestClient(app) as real:

            class HandlerClient:
                def __init__(self, url, ca, **kwargs):
                    http.target(url)
                    self.last = {}
                    self.connects = 0
                    self.connect_ns = 0
                    self.requests = 0

                def call(self, path, token=None, body=None, key=None, sample=True):
                    headers = {}
                    if token:
                        headers["Authorization"] = "Bearer " + token
                    if key:
                        headers["Idempotency-Key"] = key
                    response = real.request(
                        "GET" if body is None else "POST", path, headers=headers, json=body
                    )
                    value = response.json()
                    self.requests += 1
                    self.last = {
                        "status": response.status_code,
                        "wall_ns": 1,
                        "caller_thread_cpu_ns": 1,
                        "request_dispatch_attempted": True,
                    }
                    assert response.status_code in (200, 201, 202), value
                    assert value["meta"]["request_id"] == str(
                        UUID(response.headers["X-Request-ID"])
                    )
                    assert value["meta"]["replayed"] is False
                    return value["data"]

                def close(self):
                    pass

            original_client = http.Client
            monkeypatch.setattr(http, "Client", HandlerClient)
            s2_dir = tmp_path / "s2"
            assert (
                s2.main(
                    [
                        "--accounts",
                        str(account_path),
                        "--candidate",
                        str(candidate_path),
                        "--candidate-sha256",
                        candidate_sha,
                        "--output-dir",
                        str(s2_dir),
                        "--ca",
                        str(ca),
                        "--ca-sha256",
                        control["ca_sha256"],
                        "--url",
                        control["url"],
                        "--control",
                        str(control_path),
                        "--control-sha256",
                        control_sha,
                    ]
                )
                == 0
            )
            packet_path = s2_dir / "session.private.json"
            packet = http.private_json(packet_path)
            assert len(packet["slots"]) == 4 and packet["resumable"] is True
            initial = [slot["transition"]["version"] for slot in packet["slots"]]
            result = tmp_path / "run.public.jsonl"
            updated = tmp_path / "after.private.json"
            assert (
                http.main(
                    [
                        "--control",
                        str(control_path),
                        "--control-sha256",
                        control_sha,
                        "--packet",
                        str(packet_path),
                        "--packet-sha256",
                        hashlib.sha256(packet_path.read_bytes()).hexdigest(),
                        "--ca",
                        str(ca),
                        "--output",
                        str(result),
                        "--updated-packet",
                        str(updated),
                        "--clients",
                        "1",
                        "--cycles",
                        "2",
                        "--seconds",
                        "30",
                        "--slot-offset",
                        "1",
                    ]
                )
                == 0
            )
            final = http.private_json(updated)
            assert final["slots"][1]["transition"]["version"] == initial[1] + 2
            assert all(final["slots"][i]["transition"]["version"] == initial[i] for i in (0, 2, 3))
            report = json.loads(result.read_text().splitlines()[0])
            assert (
                report["diagnostic_complete"]
                and report["expected_requests"] == report["observed_requests"] == 8
            )

            def incomplete(index, slot, packet, ca, barrier, deadline, cycles, abort):
                barrier.wait(timeout=20)
                return {"client": index, "rows": [], "deadline_reached": True, "slot": slot}

            monkeypatch.setattr(http, "worker", incomplete)
            truncated = tmp_path / "truncated.public.jsonl"
            unusable = tmp_path / "unusable.private.json"
            assert (
                http.main(
                    [
                        "--control",
                        str(control_path),
                        "--control-sha256",
                        control_sha,
                        "--packet",
                        str(packet_path),
                        "--packet-sha256",
                        hashlib.sha256(packet_path.read_bytes()).hexdigest(),
                        "--ca",
                        str(ca),
                        "--output",
                        str(truncated),
                        "--updated-packet",
                        str(unusable),
                        "--clients",
                        "1",
                        "--cycles",
                        "2",
                        "--seconds",
                        "30",
                    ]
                )
                == 1
            )
            with pytest.raises(http.InvalidDiagnostic):
                http.check_packet(http.private_json(unusable))
            import ssl

            import certifi

            monkeypatch.setattr(http, "Client", original_client)
            strict = http.Client(control["url"], certifi.where())
            assert strict.context.check_hostname and strict.context.verify_mode == ssl.CERT_REQUIRED
            strict.close()
            for wrong in [
                "http://172.21.182.245:19445",
                "https://172.21.182.245:18445",
                "https://user:password@172.21.182.245:19445",
                "https://172.21.182.246:19445",
            ]:
                with pytest.raises(http.InvalidDiagnostic):
                    http.target(wrong)
    finally:
        engine.dispose()
