"""Owned offline bridge tests. No VM, network, independent private case or key reads."""

import base64
import copy
import hashlib
import hmac
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from cryptography.hazmat.primitives import hashes, padding, serialization
from cryptography.hazmat.primitives.asymmetric import padding as rsa_padding
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bridge_app
import bridge_common as common
import bridge_load
import bridge_protocol as protocol
import scope_crypto

UTC = timezone.utc  # noqa: UP017 -- host-compatible test data.


class Clock:
    def __init__(self, mono=10000):
        self.wall = datetime(2031, 1, 1, 12, tzinfo=UTC)
        self.value = mono

    def now(self):
        return self.wall

    def mono(self):
        return self.value

    def advance(self, seconds):
        self.wall += timedelta(seconds=seconds)
        self.value += seconds


class Observer:
    def __init__(self):
        self.alive, self.calls = True, 0

    def observe(self, owner, _grant):
        self.calls += 1
        common.require(self.alive, "OWNED_CONTAINER_NOT_LIVE")
        return {
            "alive": True,
            "operator_uid": owner["operator_uid"],
            "monotonic_namespace_same_as_load": True,
            "container_id": owner["container_id"],
            "supervisor_start_ticks": owner["supervisor_start_ticks"],
        }


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    import socket

    def forbidden(*_args, **_kwargs):
        raise AssertionError("NO_NETWORK_IN_OWNED_TEST")

    monkeypatch.setattr(socket.socket, "connect", forbidden)


@pytest.fixture(scope="module")
def key():
    private = rsa.generate_private_key(public_exponent=65537, key_size=3072)
    public = (
        private.public_key()
        .public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo)
        .decode()
    )
    return private, public


@pytest.fixture
def prepared(tmp_path, key):
    clock, observer = Clock(), Observer()
    phase = tmp_path / "unit-phase/f"
    phase.mkdir(parents=True)
    handoff = tmp_path / "PUBLIC/handoff"
    handoff.mkdir(parents=True)
    stop, source, image = "2031-01-01T12:30:00Z", "a" * 40, "sha256:" + "b" * 64
    binding = {
        "phase": "f",
        "entrypoint": "t44.api:app",
        "profiling": False,
        "source_sha": source,
        "source_archive_sha256": "c" * 64,
        "image_ids": {"backend": image},
        "config_ids": {"backend": image},
        "database": "unit_scope_f",
        "project": "unit-scope-f",
        "tls": {"ca_sha256": "d" * 64},
        "stop_utc": stop,
    }
    binding_raw = common.canonical(binding) + b"\n"
    identity = {
        "source_sha": source,
        "source_archive_sha256": "c" * 64,
        "image_digest": image,
        "runtime_identity": "unit-scope-f/api/unit-id",
        "prepared_binding_sha256": common.sha(binding_raw),
        "schema_name": binding["database"],
        "project_name": binding["project"],
        "phase_dir": str(phase),
        "ca_sha256": "d" * 64,
        "base_url": "https://192.0.2.1:24443/api/v1",
        "pinned_ip": "192.0.2.1",
        "runtime_receipt_sha256": "e" * 64,
        "prepared_receipt_sha256": "f" * 64,
        "lifecycle_status": "running",
        "isolated_resource_ids": ["unit:db", "unit:api"],
    }
    grant = {
        "admitted": True,
        "phase": "functional",
        "no_automatic_retry": True,
        "allowed_faults": [],
        "fixture_handoff": "nonce-sealed-project-scope",
        "tool_freeze_sha256": protocol.FREEZE,
        "tool_execution_build_sha256": protocol.EXECUTION,
        "build": {
            k: identity[k]
            for k in ("source_sha", "source_archive_sha256", "image_digest", "runtime_identity")
        },
        "base_url": identity["base_url"],
        "pinned_ip": identity["pinned_ip"],
        "isolated_resource_ids": identity["isolated_resource_ids"],
        "expires_at": "2031-01-01T12:20:00Z",
        "scope_provider_fixed_phase_dir": str(phase),
        "runtime_receipt_sha256": identity["runtime_receipt_sha256"],
        "network_name": "unit-operator-net",
    }
    launch = {
        "kind": "DETACHED_SUPERVISOR_LAUNCH_NOT_VERDICT",
        "phase": "functional",
        "no_automatic_retry": True,
        "supervisor_pid": 9,
        "owned_pgid": 9,
        "tool_freeze_sha256": protocol.FREEZE,
        "tool_execution_build_sha256": protocol.EXECUTION,
        "started_utc": "2031-01-01T11:59:59Z",
        "expires_at": grant["expires_at"],
    }
    sup = {
        "nonce": "b" * 48,
        "supervisor_pid": 9,
        "tool_freeze_sha256": protocol.FREEZE,
        "expires_at": grant["expires_at"],
        "hard_deadline_monotonic": clock.mono() + 1200,
    }
    context = {
        "tool_freeze_sha256": protocol.FREEZE,
        "source_sha": source,
        "native_runtime_identity": identity["runtime_identity"],
        "phase": "functional",
        "resource_ids": identity["isolated_resource_ids"],
        "supervisor_nonce": sup["nonce"],
    }
    request = {
        "kind": "SERVICE_SCOPE_REQUEST",
        "nonce": "a" * 48,
        "context": context,
        "project_ids": [2, 1],
        "iteration_ids": [],
        "scope": ["escalation:write"],
        "requested_utc": common.utc(clock.now()),
        "public_key_pem": key[1],
    }
    admission = {
        "kind": "ROOT_SINGLE_FUNCTIONAL_EXECUTION_RESERVED",
        "phase": "functional",
        "root_grant_sha256": common.sha(common.canonical(grant) + b"\n"),
        "tool_freeze_sha256": protocol.FREEZE,
        "tool_execution_build_sha256": protocol.EXECUTION,
        "no_automatic_retry": True,
    }
    originals = {}
    for name, obj in {
        "grant": grant,
        "launch": launch,
        "supervisor": sup,
        "binding": binding,
        "neutral": {"sut_identity": identity},
        "admission": admission,
    }.items():
        path = tmp_path / (name + ".PUBLIC.json")
        raw = common.canonical(obj) + b"\n"
        common.reserve(path, raw)
        originals[name] = {"path": str(path), "sha256": common.sha(raw)}
    request_path = handoff / (request["nonce"] + ".request.PUBLIC.json")
    raw = common.canonical(request) + b"\n"
    common.reserve(request_path, raw)
    config = {
        "originals": originals,
        "bridge_bundle_sha256": "9" * 64,
        "app_phase_dir": str(phase),
        "forbidden_key_shas": ["1" * 64, "2" * 64],
        "owner": {
            "container_id": "3" * 64,
            "init_host_pid": 1000,
            "init_start_ticks": "100",
            "supervisor_host_pid": 1009,
            "supervisor_start_ticks": "109",
            "supervisor_host_pgid": 1009,
            "supervisor_container_pid": 9,
            "supervisor_container_pgid": 9,
            "operator_uid": os.getuid(),
        },
    }
    result = bridge_load.prepare(
        config, request_path, common.sha(raw), tmp_path / "load-state", observer, clock
    )
    folder = Path(result["folder"])
    state = common.parse(common.read(folder / "reservation.PUBLIC.json"))
    authority = state["authority"]
    return tmp_path, clock, observer, authority, folder, result, config


class Backend:
    def __init__(self, clock):
        self.clock, self.calls, self.existing, self.fail = clock, [], False, None

    def check_binding(self, _facts, _authority):
        self.calls.append("binding")

    def preflight(self, _facts, _authority, _folder, _deadline):
        self.calls.append("readonly")

    def scheduler_state(self, _facts):
        return {
            "absent": not self.existing,
            "credential_exists": self.existing,
            "healthy_owned": True,
        }

    def generation(self, action, facts, _folder, _deadline):
        self.calls.append(action)
        if self.fail == action:
            raise common.Refused("INFLIGHT_MAY_COMPLETE")
        return {"success": True, "action": action, "source_sha": facts["binding"]["source_sha"]}

    def confirm_scheduler(self, _facts, _folder):
        return {
            "container_id": "unit-scheduler",
            "same_file_mounted_readonly": True,
            "private_file_sha256": "4" * 64,
        }

    def seal(self, facts, _authority, _scheduler, _folder, _deadline):
        credential = {
            "project_ids": facts["request"]["project_ids"],
            "scope": ["escalation:write"],
            "token": "unit-private-" + "x" * 40,
            "applied_to": ["scheduler"],
        }
        return (
            common.canonical(
                scope_crypto.scope(
                    facts["request"],
                    credential,
                    facts["request"]["context"],
                    common.utc(self.clock.now()),
                )
            )
            + b"\n"
        )


def app_result(prepared, *, existing=False, mono=None):
    root, clock, _, authority, _, _, _ = prepared
    app_clock = clock if mono is None else Clock(mono)
    backend = Backend(app_clock)
    backend.existing = existing
    result = bridge_app.provision(authority, root / "app-state", backend, app_clock, "9" * 64)
    return result, backend


def test_three_stages_exact_context_empty_iterations_and_atomic_deliver(prepared):
    result, backend = app_result(prepared)
    assert backend.calls == [
        "binding",
        "readonly",
        "binding",
        "scheduler-token",
        "binding",
        "scheduler-start",
    ]
    root, clock, observer, authority, folder, _, _ = prepared
    delivered = bridge_load.deliver(folder / "reservation.PUBLIC.json", result, observer, clock)
    raw = Path(delivered["reply_path"]).read_bytes()
    reply = common.parse(raw)
    assert (
        reply["project_ids"] == [2, 1]
        and reply["context"] == common.decode_document(authority["documents"]["request"])["context"]
    )
    assert observer.calls == 2 and delivered["decrypted_by_root"] is False
    assert not list(Path(delivered["reply_path"]).parent.glob(".bridge-*.tmp"))


def test_existing_scheduler_uses_original_rotate_not_new_token(prepared):
    _, backend = app_result(prepared, existing=True)
    assert "scheduler-rotate" in backend.calls and "scheduler-token" not in backend.calls


def test_app_uses_own_monotonic_not_load_numeric_value(prepared):
    result, _ = app_result(prepared, mono=9_000_000_000)
    assert result["receipt"]["app_monotonic"] == 9_000_000_000
    assert result["receipt"]["load_observation_was_snapshot_only"] is True


def test_load_exit_while_app_works_refuses_delivery(prepared):
    result, _ = app_result(prepared)
    _, clock, observer, _, folder, _, _ = prepared
    observer.alive = False
    with pytest.raises(common.Refused, match="NOT_LIVE"):
        bridge_load.deliver(folder / "reservation.PUBLIC.json", result, observer, clock)
    assert not list((prepared[0] / "PUBLIC/handoff").glob("*.sealed.PUBLIC.json"))


def test_original120s_not_extended_and_late_reply_not_written(prepared):
    result, _ = app_result(prepared)
    _, clock, observer, _, folder, _, _ = prepared
    clock.advance(120)
    with pytest.raises(common.Refused):
        bridge_load.deliver(folder / "reservation.PUBLIC.json", result, observer, clock)
    assert not list((prepared[0] / "PUBLIC/handoff").glob("*.sealed.PUBLIC.json"))


@pytest.mark.parametrize(
    "field",
    ["source", "nonce", "scope", "context_extra", "resources", "binding_phase", "key_domain"],
)
def test_bad_context_has_zero_provision_before_mutation(prepared, field):
    root, clock, _, authority, _, _, _ = prepared
    authority = copy.deepcopy(authority)
    name = "binding" if field == "binding_phase" else "request"
    doc = common.decode_document(authority["documents"][name])
    if field == "source":
        doc["context"]["source_sha"] = "0" * 40
    elif field == "nonce":
        doc["context"]["supervisor_nonce"] = "0" * 48
    elif field == "scope":
        doc["scope"] = ["anything"]
    elif field == "context_extra":
        doc["context"]["tool_execution_build_sha256"] = protocol.EXECUTION
    elif field == "resources":
        doc["context"]["resource_ids"] += ["outside-resource"]
    elif field == "binding_phase":
        doc["phase"] = "p"
    else:
        authority["forbidden_key_shas"][0] = common.sha(doc["public_key_pem"].encode())
    authority["documents"][name] = common.document(common.canonical(doc))
    backend = Backend(clock)
    with pytest.raises(common.Refused):
        bridge_app.provision(authority, root / "bad-app", backend, clock, "9" * 64)
    assert backend.calls == []


def test_stale_snapshot_refuses_before_readonly_or_gen(prepared):
    root, clock, _, authority, *_ = prepared
    clock.advance(31)
    backend = Backend(clock)
    with pytest.raises(common.Refused, match="SNAPSHOT"):
        bridge_app.provision(authority, root / "stale", backend, clock, "9" * 64)
    assert backend.calls == []


def test_duplicate_nonce_no_second_provision(prepared):
    app_result(prepared)
    with pytest.raises(FileExistsError):
        app_result(prepared)


def test_mutation_failure_stops_no_retry_and_keeps_dirty_phase(prepared):
    root, clock, _, authority, *_ = prepared
    backend = Backend(clock)
    backend.fail = "scheduler-token"
    with pytest.raises(common.Refused):
        bridge_app.provision(authority, root / "failed-app", backend, clock, "9" * 64)
    assert backend.calls.count("scheduler-token") == 1 and "scheduler-start" not in backend.calls
    assert list((root / "failed-app").glob("*.inflight-or-quarantined"))
    assert list((root / "failed-app").glob("*/failed.PUBLIC.json"))


def test_pending_request_changed_or_reply_exists_refuses(prepared):
    result, _ = app_result(prepared)
    root, clock, observer, authority, folder, *_ = prepared
    request = common.decode_document(authority["documents"]["request"])
    common.reserve(
        root / "PUBLIC/handoff" / (request["nonce"] + ".sealed.PUBLIC.json"), b"old opaque"
    )
    with pytest.raises(common.Refused, match="ALREADY_DELIVERED"):
        bridge_load.deliver(folder / "reservation.PUBLIC.json", result, observer, clock)
    assert (
        root / "PUBLIC/handoff" / (request["nonce"] + ".sealed.PUBLIC.json")
    ).read_bytes() == b"old opaque"


def test_monotonic_expiry_even_when_wall_moves_back():
    clock = Clock()
    deadline = common.Deadline(clock, clock.now() + timedelta(seconds=10))
    clock.value += 11
    clock.wall -= timedelta(seconds=100)
    with pytest.raises(common.Refused):
        deadline.remaining()


def test_opaque_context_tamper_is_refused_before_final_publish(prepared):
    result, _ = app_result(prepared)
    opaque = common.parse(base64.b64decode(result["opaque_b64"]))
    opaque["context"]["phase"] = "performance"
    raw = common.canonical(opaque)
    result["opaque_b64"] = base64.b64encode(raw).decode()
    result["receipt"]["opaque_sha256"] = common.sha(raw)
    _, clock, observer, _, folder, *_ = prepared
    with pytest.raises(common.Refused, match="CONTEXT_CHANGED"):
        bridge_load.deliver(folder / "reservation.PUBLIC.json", result, observer, clock)


def test_seal_exact_original_protocol_roundtrip_and_no_plaintext(prepared, key):
    result, _ = app_result(prepared)
    raw = base64.b64decode(result["opaque_b64"])
    sealed = common.parse(raw)
    material = key[0].decrypt(
        base64.b64decode(sealed["wrapped_key_b64"]),
        rsa_padding.OAEP(
            mgf=rsa_padding.MGF1(hashes.SHA256()), algorithm=hashes.SHA256(), label=None
        ),
    )
    iv, ciphertext = base64.b64decode(sealed["iv_b64"]), base64.b64decode(sealed["ciphertext_b64"])
    authenticated = (
        common.canonical(
            {
                "nonce": sealed["nonce"],
                "project_ids": sealed["project_ids"],
                "context": sealed["context"],
            }
        )
        + iv
        + ciphertext
    )
    assert hmac.compare_digest(
        sealed["hmac_sha256"], hmac.digest(material[32:], authenticated, "sha256").hex()
    )
    decryptor = Cipher(algorithms.AES(material[:32]), modes.CBC(iv)).decryptor()
    padded = decryptor.update(ciphertext) + decryptor.finalize()
    unpadder = padding.PKCS7(128).unpadder()
    plain = common.parse(unpadder.update(padded) + unpadder.finalize())
    assert plain["project_ids"] == [2, 1] and plain["credential"]["applied_to"] == ["scheduler"]
    assert (
        hashlib.sha256(plain["credential"]["token"].encode()).digest()
        == hashlib.sha256(("unit-private-" + "x" * 40).encode()).digest()
    )
    assert b"unit-private-" not in raw and b"unit-private-" not in common.canonical(result)


def test_original_cli_and_readonly_data_guard_seal_roundtrip(tmp_path, monkeypatch, key):
    import contextlib
    import io

    import bridge_data
    from sqlalchemy import create_engine
    from t44 import cli, persistence
    from t44.persistence.schema import metadata

    assert "product-source" in cli.__file__
    engine = create_engine("sqlite:///" + str(tmp_path / "original-path.sqlite"))
    metadata.create_all(engine)
    factory = persistence.SqlAlchemyUnitOfWorkFactory(engine)
    monkeypatch.setenv("DATABASE_URL", "mysql+pymysql://unit:synthetic@mysql:3306/unit_scope_f")
    monkeypatch.setenv("T44_DATABASE", "unit_scope_f")
    monkeypatch.setenv("T44_SESSION_TTL_SECONDS", "3600")
    monkeypatch.setattr(cli, "create_mysql_engine", lambda _settings: engine)

    def call(arguments, secret=b""):
        monkeypatch.setattr(sys, "stdin", io.StringIO(secret.decode()))
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            assert cli.main(arguments) == 0
        return common.parse(output.getvalue())

    try:
        user = call(
            [
                "init-user",
                "--username",
                "scope-unit",
                "--display-name",
                "[synthetic] scope",
                "--password-stdin",
            ],
            b"unit-only-password\n",
        )["user_id"]
        now = datetime.now(UTC)
        with factory() as uow:
            ids = [
                uow.gateway.insert(
                    "projects",
                    {
                        "name": "unit" + str(i),
                        "description": "local only",
                        "created_by": user,
                        "created_at": now,
                        "updated_at": now,
                    },
                )
                for i in range(2)
            ]
            iteration = uow.gateway.insert(
                "iterations",
                {
                    "project_id": ids[0],
                    "name": "unit",
                    "planned_start": now,
                    "planned_end": now + timedelta(days=1),
                    "capacity": [{"user_id": user, "available_hours": 8}],
                    "buffer_quarters": 0,
                    "delay_contingency": "unit",
                    "created_at": now,
                    "updated_at": now,
                },
            )
        path = tmp_path / "service.private.json"
        call(
            [
                "service-token",
                "--name",
                "unit-scheduler",
                "--project-id",
                str(ids[0]),
                "--project-id",
                str(ids[1]),
                "--token-file",
                str(path),
            ]
        )
        request = {
            "kind": "SERVICE_SCOPE_REQUEST",
            "nonce": "new-unit-scope",
            "project_ids": list(reversed(ids)),
            "iteration_ids": [],
            "scope": ["escalation:write"],
            "public_key_pem": key[1],
            "context": {"unit": "original-cli"},
        }
        bridge_data.preflight(factory, request)
        bridge_data.preflight(factory, {**request, "iteration_ids": [iteration]})
        with pytest.raises(common.Refused, match="ITERATION_OWNERSHIP"):
            bridge_data.preflight(
                factory, {**request, "project_ids": [ids[1]], "iteration_ids": [iteration]}
            )
        with pytest.raises(common.Refused, match="ACTUAL_PROJECTS"):
            bridge_data.preflight(factory, {**request, "project_ids": [9999]})
        before = path.read_bytes()
        credential = bridge_data.service_credential(
            factory, request, before, lambda: datetime.now(UTC)
        )
        assert credential["project_ids"] == request["project_ids"]
        sealed = scope_crypto.scope(
            request, credential, request["context"], common.utc(datetime.now(UTC))
        )
        assert "token" not in sealed and path.read_bytes() == before
        with pytest.raises(common.Refused, match="SERVICE_SCOPE"):
            bridge_data.service_credential(
                factory, {**request, "project_ids": [ids[0]]}, before, lambda: datetime.now(UTC)
            )
        with pytest.raises(common.Refused, match="ACTIVE_ORIGINAL"):
            bridge_data.service_credential(
                factory, request, before, lambda: datetime.now(UTC) + timedelta(days=2)
            )
        with factory() as uow:
            assert (
                uow.gateway.count("auth_sessions") == 1
                and uow.gateway.count("service_accounts") == 1
            )
            rows = uow.gateway.rows("audit_events", {"operation_id": "service-token"})
            assert len(rows) == 1
        # Rotation is delegated to GEN/credential-admin, never implemented by SQL UPDATE here.
        assert not any(
            isinstance(node, __import__("ast").Attribute)
            and node.attr in {"insert", "update", "delete"}
            for node in __import__("ast").walk(
                __import__("ast").parse(Path(bridge_data.__file__).read_text())
            )
        )
    finally:
        engine.dispose()


def test_real_metadata_observer_refuses_pid_reuse_and_dead_container(tmp_path):
    owner = {
        "container_id": "c" * 64,
        "init_host_pid": 1000,
        "init_start_ticks": "100",
        "supervisor_host_pid": 1009,
        "supervisor_start_ticks": "109",
        "supervisor_host_pgid": 1009,
        "supervisor_container_pid": 9,
        "supervisor_container_pgid": 9,
    }

    def stat_line(pid, ppid, pgid, ticks):
        fields = ["S", str(ppid), str(pgid)] + ["0"] * 16 + [str(ticks)]
        return str(pid) + " (unit process) " + " ".join(fields)

    for pid, ppid, pgid, ticks in [(1000, 1, 1000, 100), (1009, 1000, 1009, 109)]:
        folder = tmp_path / str(pid)
        folder.mkdir()
        (folder / "stat").write_text(stat_line(pid, ppid, pgid, ticks))
    sup = tmp_path / "1009"
    (sup / "status").write_text(
        "NSpid:\t1009\t9\nNSpgid:\t1009\t9\nUid:\t10001\t10001\t10001\t10001\n"
    )
    (sup / "ns").mkdir()
    (sup / "ns/time").symlink_to("time:[42]")
    (tmp_path / "self/ns").mkdir(parents=True)
    (tmp_path / "self/ns/time").symlink_to("time:[42]")
    info = {
        "Id": owner["container_id"],
        "State": {"Running": True, "Pid": 1000, "OOMKilled": False},
        "Config": {"User": "10001:10001"},
        "HostConfig": {"ReadonlyRootfs": True, "NetworkMode": "unit-net"},
    }
    observer = bridge_load.DockerProcObserver(
        lambda *_a, **_k: common.canonical(info), proc_root=tmp_path
    )
    assert observer.observe(owner, {"network_name": "unit-net"})["alive"] is True
    with pytest.raises(common.Refused, match="PID_REUSED"):
        observer.observe({**owner, "supervisor_start_ticks": "old"}, {"network_name": "unit-net"})
    info["State"]["Running"] = False
    with pytest.raises(common.Refused, match="NOT_LIVE"):
        observer.observe(owner, {"network_name": "unit-net"})


def test_timeout_after_gen_retains_owned_failure_no_retry(prepared):
    root, clock, _, authority, *_ = prepared
    backend = Backend(clock)
    original = backend.generation

    def late(stage, facts, folder, deadline):
        result = original(stage, facts, folder, deadline)
        clock.advance(61)
        return result

    backend.generation = late
    with pytest.raises(common.Refused, match="DEADLINE"):
        bridge_app.provision(authority, root / "timeout-app", backend, clock, "9" * 64)
    assert backend.calls.count("scheduler-token") == 1 and "scheduler-start" not in backend.calls


def test_explicit_root_admission_sha_cannot_be_mixed(prepared):
    root, clock, _, authority, *_ = prepared
    authority = copy.deepcopy(authority)
    admission = common.decode_document(authority["documents"]["admission"])
    admission["root_grant_sha256"] = "0" * 64
    authority["documents"]["admission"] = common.document(common.canonical(admission))
    backend = Backend(clock)
    with pytest.raises(common.Refused, match="ADMISSION"):
        bridge_app.provision(authority, root / "wrong-admission", backend, clock, "9" * 64)
    assert backend.calls == []


def test_host_python310_and_cli_has_no_root_ack_or_cloud_permissions():
    import ast

    here = Path(__file__).resolve().parent
    for name in (
        "bridge_common.py",
        "bridge_protocol.py",
        "bridge_load.py",
        "bridge_app.py",
        "bridge_backend.py",
        "bridge_cli.py",
    ):
        tree = ast.parse((here / name).read_text(), feature_version=(3, 10))
        assert not any(
            isinstance(n, ast.ImportFrom)
            and n.module == "datetime"
            and any(a.name == "UTC" for a in n.names)
            for n in ast.walk(tree)
        )
    source = (here / "bridge_cli.py").read_text()
    assert 'choices=("prepare", "provision", "deliver")' in source
    assert '"revoke"' not in source and '"ROOT_ACK"' not in source


def test_fresh_cli_help_parses_without_duplicate_arguments():
    import subprocess

    path = Path(__file__).resolve().parent / "bridge_cli.py"
    result = subprocess.run([sys.executable, str(path), "--help"], capture_output=True, check=False)
    assert result.returncode == 0
    assert b"{prepare,provision,deliver}" in result.stdout


def test_owned_command_timeout_preserves_prefix_if_process_disappears(tmp_path, monkeypatch):
    import subprocess

    import bridge_backend

    clock = Clock()

    class Process:
        pid = 424242
        count = 0

        def communicate(self, **_kwargs):
            self.count += 1
            if self.count == 1:
                raise subprocess.TimeoutExpired(
                    "unit", 1, output=b"public-prefix", stderr=b"error-prefix"
                )
            return b"public-prefix", b"error-prefix"

        def poll(self):
            return None

    monkeypatch.setattr(bridge_backend.subprocess, "Popen", lambda *_a, **_k: Process())

    def gone(_pid):
        raise ProcessLookupError()

    monkeypatch.setattr(bridge_backend.os, "getpgid", gone)
    with pytest.raises(common.Refused, match="TIMEOUT"):
        bridge_backend.Runner().run(
            ["unit-no-real-command"],
            common.Deadline(clock, clock.now() + timedelta(seconds=10)),
            tmp_path / "owned",
        )
    assert (tmp_path / "owned.stdout.private").read_bytes() == b"public-prefix"
    assert (tmp_path / "owned.stderr.private").read_bytes() == b"error-prefix"
