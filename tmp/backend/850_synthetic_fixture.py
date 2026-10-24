"""Offline guards/crypto tests only; no DB, cloud, real account or service invocation."""

import hashlib
import importlib.util
import json
import os
import subprocess
import tempfile
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

ROOT = Path(__file__).resolve().parents[2]
PUBLIC = ROOT / "agents/backend/synthetic-fixture/public-inputs"


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


worker = load("synthetic_fixture_worker", ROOT / "deployment/synthetic-fixture.py")
envelope = load("published_envelope", PUBLIC / "852_public_envelope_v1.py")


@pytest.fixture
def private_dir():
    # Keep the synthetic tree under our checkout, not a world-writable /tmp ancestor.
    with tempfile.TemporaryDirectory(
        prefix=".850-unit-", dir=Path(__file__).parent
    ) as path:
        yield Path(path)


@pytest.fixture(scope="module")
def recipient():
    key = rsa.generate_private_key(public_exponent=65537, key_size=3072)
    subject = x509.Name(
        [x509.NameAttribute(NameOID.COMMON_NAME, "synthetic-local-unit-test")]
    )
    timestamp = datetime.now(UTC)
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(subject)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(timestamp - timedelta(days=1))
        .not_valid_after(timestamp + timedelta(days=1))
        .sign(key, hashes.SHA256())
    )
    return cert.public_bytes(serialization.Encoding.PEM), key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )


class SyntheticFactory:
    def __init__(self, populated=None):
        self.populated = populated or {}
        self.reads = []

    @contextmanager
    def __call__(self):
        def count(table, where=None):
            self.reads.append((table, where))
            return self.populated.get(table, 0)

        yield SimpleNamespace(gateway=SimpleNamespace(count=count))


def exercise(private_dir, monkeypatch, recipient, *, populated=None, replies=None):
    output = private_dir / "output"
    output.mkdir(mode=0o700)
    descriptor = worker._output_directory(output)
    observed = []
    passwords = iter([f"LOCAL-ONLY-KNOWN-TEST-VALUE-{i}" for i in range(3)])
    monkeypatch.setattr(worker.secrets, "token_urlsafe", lambda size: next(passwords))
    factory = SyntheticFactory(populated)

    def runner(command, **kwargs):
        assert (output / worker.PENDING).is_file()
        assert not (output / worker.FINAL).exists()
        assert kwargs.keys() == {"input", "capture_output", "check", "timeout"}
        assert command[:5] == [os.sys.executable, "-B", "-m", "t44.cli", "init-user"]
        assert command[-1] == "--password-stdin"
        assert not any("LOCAL-ONLY-KNOWN-TEST" in arg for arg in command)
        assert kwargs["input"].endswith(b"\n")
        observed.append(command)
        if replies is not None:
            return replies[len(observed) - 1]
        return subprocess.CompletedProcess(
            command, 0, json.dumps({"user_id": len(observed)}).encode(), b""
        )

    try:
        status = worker.provision(
            descriptor, envelope, recipient[0], factory, runner=runner
        )
    finally:
        os.close(descriptor)
    return output, observed, status, factory


def test_success_pending_precedes_stdin_and_only_ciphertext_persists(
    private_dir, monkeypatch, recipient
):
    output, calls, status, factory = exercise(private_dir, monkeypatch, recipient)
    assert status["success"] and len(calls) == 3
    assert not status["seeded"] and not status["sessions_created"]
    assert len(status["confirmed_users"]) == 3
    assert factory.reads[0] == (
        "users",
        {"username": [row[0] for row in worker.ACCOUNTS]},
    )
    for name, expected_state in (
        (worker.PENDING, "pending"),
        (worker.FINAL, "accounts-created-not-seeded"),
    ):
        raw = (output / name).read_bytes()
        assert b"LOCAL-ONLY-KNOWN-TEST" not in raw
        assert (output / name).stat().st_mode & 0o777 == 0o600
        content = envelope.strict_json(
            envelope.decrypt(json.loads(raw), *recipient, "neutral-environment")
        )
        assert (
            content["source"] == worker.SOURCE and content["status"] == expected_state
        )
        assert len({row["password"] for row in content["accounts"]}) == 3
        assert all(
            ("user_id" in row) == (name == worker.FINAL) for row in content["accounts"]
        )
    assert json.loads((output / worker.STATUS).read_bytes()) == status
    assert "LOCAL-ONLY-KNOWN-TEST" not in json.dumps(status)


def test_second_cli_failure_stops_and_retains_recovery_without_final(
    private_dir, monkeypatch, recipient
):
    replies = [
        subprocess.CompletedProcess([], 0, b'{"user_id":17}', b""),
        subprocess.CompletedProcess([], 1, b"", b"PRIVATE ERROR MUST NOT BE COPIED"),
    ]
    output, calls, status, _ = exercise(
        private_dir, monkeypatch, recipient, replies=replies
    )
    assert len(calls) == 2 and not status["success"]
    assert status["confirmed_users"] == [
        {"username": "synthetic-manager", "user_id": 17}
    ]
    assert status["error"] == "ACCOUNT_CLI_FAILED" and status["cli_exit_code"] == 1
    assert status["creation_outcome_may_be_committed"]
    assert (output / worker.PENDING).is_file() and not (output / worker.FINAL).exists()
    assert "PRIVATE ERROR" not in (output / worker.STATUS).read_text()


@pytest.mark.parametrize(
    "stdout",
    [
        b"{}",
        b'{"user_id":true}',
        b'{"user_id":0}',
        b'{"user_id":4294967296}',
        b'{"user_id":1,"password":"UNTRUSTED"}',
        b"not-json",
    ],
)
def test_malformed_success_is_unknown_never_retried(
    private_dir, monkeypatch, recipient, stdout
):
    output, calls, status, _ = exercise(
        private_dir,
        monkeypatch,
        recipient,
        replies=[subprocess.CompletedProcess([], 0, stdout, b"")],
    )
    assert len(calls) == 1 and status["error"] == "ACCOUNT_OUTCOME_UNKNOWN"
    assert status["creation_outcome_may_be_committed"] and not status["confirmed_users"]
    assert (output / worker.PENDING).exists() and not (output / worker.FINAL).exists()
    assert "UNTRUSTED" not in json.dumps(status)


@pytest.mark.parametrize(
    "table,code",
    [
        ("users", "SYNTHETIC_USER_ALREADY_EXISTS"),
        ("tasks", "BUSINESS_DATA_NOT_EMPTY"),
        ("audit_events", "BUSINESS_DATA_NOT_EMPTY"),
    ],
)
def test_preflight_blocks_any_existing_target_or_business_before_passwords_or_cli(
    private_dir, monkeypatch, recipient, table, code
):
    output, calls, status, _ = exercise(
        private_dir, monkeypatch, recipient, populated={table: 1}
    )
    assert status["error"] == code and not calls
    assert (
        not (output / worker.PENDING).exists() and not (output / worker.FINAL).exists()
    )


def test_final_output_failure_keeps_pending_and_confirmed_users(
    private_dir, monkeypatch, recipient
):
    original = worker._write_json

    def failed_final(directory, name, content):
        if name == worker.FINAL:
            raise OSError("LOCAL-SYNTHETIC-FAILURE")
        return original(directory, name, content)

    monkeypatch.setattr(worker, "_write_json", failed_final)
    output, calls, status, _ = exercise(private_dir, monkeypatch, recipient)
    assert len(calls) == len(status["confirmed_users"]) == 3
    assert not status["success"] and status["error"] == "FIXTURE_FAILED"
    assert (output / worker.PENDING).exists() and not (output / worker.FINAL).exists()


def test_output_requires_private_owner_and_exclusive_non_symlink_files(private_dir):
    output = private_dir / "output"
    output.mkdir(mode=0o755)
    with pytest.raises(worker.FixtureFailure, match="OUTPUT_DIRECTORY_REJECTED"):
        worker._output_directory(output)
    output.chmod(0o700)
    descriptor = worker._output_directory(output)
    try:
        with pytest.raises(worker.FixtureFailure, match="OUTPUT_IN_USE"):
            worker._output_directory(output)
        worker._write_json(
            descriptor, worker.PENDING, {"known": "ciphertext-placeholder"}
        )
        with pytest.raises(FileExistsError):
            worker._write_json(descriptor, worker.PENDING, {})
        with pytest.raises(worker.FixtureFailure, match="OUTPUT_NAME_REJECTED"):
            worker._write_json(descriptor, "../escape", {})
    finally:
        os.close(descriptor)
    with pytest.raises(worker.FixtureFailure, match="OUTPUT_ALREADY_EXISTS"):
        worker._output_directory(output)
    alias = private_dir / "alias"
    alias.symlink_to(output, target_is_directory=True)
    with pytest.raises(worker.FixtureFailure, match="SYMLINK_REJECTED"):
        worker._output_directory(alias)


def test_public_input_content_owner_mode_and_symlink_guards(private_dir):
    source = private_dir / "known-public.txt"
    source.write_bytes(b"known public data")
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    with pytest.raises(worker.FixtureFailure, match="PUBLIC_FILE_REJECTED"):
        worker._public_file(source, digest, owner=os.geteuid())
    source.chmod(0o444)
    assert (
        worker._public_file(source, digest, owner=os.geteuid()) == b"known public data"
    )
    with pytest.raises(worker.FixtureFailure, match="PUBLIC_HASH_MISMATCH"):
        worker._public_file(source, "0" * 64, owner=os.geteuid())
    with pytest.raises(
        worker.FixtureFailure, match="PUBLIC_FILE_REJECTED|PUBLIC_PARENT_REJECTED"
    ):
        worker._public_file(source, digest, owner=os.geteuid() + 1)
    link = private_dir / "public-link"
    link.symlink_to(source)
    with pytest.raises(worker.FixtureFailure, match="SYMLINK_REJECTED"):
        worker._public_file(link, digest, owner=os.geteuid())


def test_published_input_hashes_and_recipient_fingerprint_are_pinned():
    spec = json.loads((PUBLIC / "852_public_envelope_spec_v1.json").read_bytes())
    helper_raw = (PUBLIC / "852_public_envelope_v1.py").read_bytes()
    certificate = (PUBLIC / "852_public_env_recipient_v1.cert.pem").read_bytes()
    assert (
        hashlib.sha256(helper_raw).hexdigest()
        == worker.HELPER_SHA256
        == spec["public_helper_sha256"]
    )
    assert (
        hashlib.sha256(certificate).hexdigest()
        == worker.CERT_SHA256
        == spec["public_certificate_pem_sha256"]
    )
    assert (
        envelope.recipient(certificate)[1]
        == worker.CERT_FINGERPRINT
        == spec["public_certificate_der_sha256_fingerprint"]
    )


@pytest.mark.parametrize(
    "database,declared,source",
    [
        ("other", "other", worker.SOURCE),
        ("t44", "other", worker.SOURCE),
        ("t44", "t44", "wrong"),
    ],
)
def test_database_and_source_are_explicit_before_engine_creation(
    monkeypatch, database, declared, source
):
    monkeypatch.setenv("T44_DATABASE", declared)
    with pytest.raises(worker.FixtureFailure, match="TARGET_REJECTED"):
        worker._database_settings(database, source)


def test_settings_parse_and_cli_digest_without_connecting(monkeypatch):
    monkeypatch.setenv("T44_DATABASE", "t44")
    monkeypatch.setenv(
        "DATABASE_URL", "mysql+pymysql://synthetic:unit-only@mysql:3306/t44"
    )
    assert worker._database_settings("t44", worker.SOURCE).database == "t44"


def test_root_execution_rejected_before_inputs_or_database(monkeypatch, capsys):
    monkeypatch.setattr(worker.os, "getuid", lambda: 0)
    assert (
        worker.main(
            [
                "--database",
                "t44",
                "--expected-source",
                worker.SOURCE,
                "--certificate",
                "/unused",
                "--envelope-helper",
                "/unused",
                "--output-dir",
                "/unused",
            ]
        )
        == 1
    )
    assert json.loads(capsys.readouterr().out) == {
        "success": False,
        "error": "WORKER_UID_REJECTED",
    }


def test_cloud_launcher_constructs_exact_two_file_admin_call_without_secrets():
    launcher = load(
        "fixture_launcher_static", ROOT / "deployment/fixture-launcher-cloud.py"
    )
    values = {
        "MYSQL_DATABASE": "t44",
        "T44_DOCKER_CONTEXT": "default",
        "COMPOSE_PROJECT_NAME": "t44",
        "MYSQL_PASSWORD": "STATIC-TEST-NOT-A-CREDENTIAL",
    }
    command = launcher.command(values)
    assert [command[i + 1] for i, value in enumerate(command) if value == "-f"] == [
        "/opt/t44-c-0dfb55c/compose.yaml",
        "/run/t44-delivery/tls-C/overlay.json",
    ]
    assert command[
        command.index("--profile") + 1 : command.index("--entrypoint") + 2
    ] == [
        "operations",
        "run",
        "--rm",
        "-T",
        "--pull",
        "never",
        "--no-deps",
        "--entrypoint",
        "python",
    ]
    mounts = [command[i + 1] for i, value in enumerate(command) if value == "--volume"]
    assert len(mounts) == 4 and sum(value.endswith(":ro") for value in mounts) == 3
    assert mounts[-1] == "/run/t44-delivery/fixture-output:/run/t44-fixture-output:rw"
    assert command[command.index("admin") + 1] == "/run/t44-fixture/worker.py"
    assert command[-2:] == ["--output-dir", "/run/t44-fixture-output"]
    assert not {"--user", "--privileged", "--cap-add", "seed-demo"}.intersection(
        command
    )
    assert values["MYSQL_PASSWORD"] not in command


def test_cloud_launcher_filters_inherited_docker_compose_environment(monkeypatch):
    launcher = load(
        "fixture_launcher_env_static", ROOT / "deployment/fixture-launcher-cloud.py"
    )
    monkeypatch.setenv("DOCKER_HOST", "tcp://untrusted.invalid")
    monkeypatch.setenv("COMPOSE_FILE", "untrusted.yml")
    environment = launcher.environment(
        {"COMPOSE_PROJECT_NAME": "t44", "MYSQL_DATABASE": "t44"}
    )
    assert "DOCKER_HOST" not in environment and "COMPOSE_FILE" not in environment
    assert environment["COMPOSE_PROJECT_NAME"] == environment["MYSQL_DATABASE"] == "t44"


@pytest.mark.parametrize(
    "invalid",
    [
        {"success": False, "password": "STATIC-KNOWN-TAMPER"},
        {"success": False, "error": "UNTRUSTED_DRIVER_MESSAGE"},
    ],
)
def test_cloud_launcher_receipt_rejects_non_allowlisted_values(invalid):
    launcher = load(
        "fixture_launcher_receipt_static", ROOT / "deployment/fixture-launcher-cloud.py"
    )
    assert launcher.safe_receipt(b'{"success":false,"error":"ACCOUNT_CLI_FAILED"}') == {
        "success": False,
        "error": "ACCOUNT_CLI_FAILED",
    }
    with pytest.raises(ValueError):
        launcher.safe_receipt(json.dumps(invalid).encode())


def service_fixture_rows():
    issued = datetime(2026, 10, 24, 9, tzinfo=UTC)
    token = "SYNTHETIC-UNIT-NOT-AN-AUTH-TOKEN-000000"
    session = {
        "actor_kind": 2,
        "service_account_id": 77,
        "user_id": None,
        "created_at": issued,
        "expires_at": issued + timedelta(seconds=5400),
        "revoked_at": None,
        "token_hash": hashlib.sha256(token.encode()).digest(),
        "scopes": ["escalation:write"],
        "project_ids": list(range(1, 41)),
    }
    subject = {"name": "notification-cohort", "active": 1, "created_at": issued}
    credential = {
        "session_id": 55,
        "access_token": token,
        "expires_at": "2026-10-24T10:30:00.000000Z",
    }

    @contextmanager
    def factory():
        def get(table, identifier):
            assert (table, identifier) in {
                ("auth_sessions", 55),
                ("service_accounts", 77),
            }
            return session if table == "auth_sessions" else subject

        yield SimpleNamespace(gateway=SimpleNamespace(get=get))

    return factory, session, subject, credential


def test_service_fixture_actual_metadata_and_known_data_envelope(recipient):
    service = load(
        "service_fixture_package", ROOT / "deployment/encrypted-service-fixture.py"
    )
    factory, _, _, credential = service_fixture_rows()
    # Synthetic RFC1918 value only; never read the actual deployment private IP.
    approved = service.origin(
        json.dumps({"approved_origin": "https://10.255.255.254:8443"}).encode()
    )
    body = service.package(
        factory, credential, approved, datetime(2026, 10, 24, 9, tzinfo=UTC)
    )
    assert set(body) == {
        "format",
        "synthetic",
        "source_commit",
        "approved_origin",
        "service",
    }
    assert (
        body["format"] == "852-neutral-service-credential-v1"
        and body["service"]["subject_id"] == 77
    )
    assert body["service"]["issued_at"] == "2026-10-24T09:00:00.000000Z"
    assert body["service"]["expires_at"] == credential["expires_at"]
    assert body["service"]["allowed_project_ids"] == list(range(1, 41))
    encrypted = envelope.encrypt(
        envelope.canonical(body), recipient[0], "neutral-environment"
    )
    assert (
        json.loads(envelope.decrypt(encrypted, *recipient, "neutral-environment"))
        == body
    )
    assert credential["access_token"] not in json.dumps(
        encrypted
    ) and approved not in json.dumps(encrypted)


@pytest.mark.parametrize(
    "change", ["bool_project", "digest", "old_subject", "revoked", "ttl"]
)
def test_service_fixture_rejects_inconsistent_live_metadata(change):
    service = load(
        "service_fixture_metadata_guard",
        ROOT / "deployment/encrypted-service-fixture.py",
    )
    factory, session, subject, credential = service_fixture_rows()
    if change == "bool_project":
        session["project_ids"][0] = True
    elif change == "digest":
        session["token_hash"] = b"wrong"
    elif change == "old_subject":
        subject["created_at"] -= timedelta(seconds=1)
    elif change == "revoked":
        session["revoked_at"] = session["created_at"]
    else:
        session["expires_at"] -= timedelta(seconds=1)
    with pytest.raises(ValueError):
        service.package(
            factory,
            credential,
            "synthetic-origin-not-transported",
            datetime(2026, 10, 24, 9, tzinfo=UTC),
        )


def test_service_fixture_too_early_issues_nothing():
    service = load(
        "service_fixture_time_guard", ROOT / "deployment/encrypted-service-fixture.py"
    )

    def forbidden_factory():
        raise AssertionError("No DB work allowed for a too-early issuance")

    with pytest.raises(ValueError, match="issuance_too_early"):
        service.preflight(forbidden_factory, datetime(2026, 10, 24, 8, 40, tzinfo=UTC))


@pytest.mark.parametrize("existing,projects", [(True, 40), (False, 39)])
def test_service_fixture_preflight_blocks_existing_or_incomplete_scope(
    existing, projects
):
    service = load(
        "service_fixture_preflight", ROOT / "deployment/encrypted-service-fixture.py"
    )

    @contextmanager
    def factory():
        yield SimpleNamespace(
            gateway=SimpleNamespace(
                rows=lambda *a, **k: [1] if existing else [],
                count=lambda *a, **k: projects,
            )
        )

    with pytest.raises(
        ValueError, match="subject_already_exists|project_scope_missing"
    ):
        service.preflight(factory, datetime(2026, 10, 24, 9, tzinfo=UTC))


def test_service_fixture_host_command_scope_and_source_pins():
    service = load(
        "service_fixture_argv", ROOT / "deployment/encrypted-service-fixture.py"
    )
    host = load(
        "service_fixture_host_argv",
        ROOT / "deployment/service-fixture-launcher-cloud.py",
    )
    argv = host.command(
        {
            "MYSQL_DATABASE": "t44",
            "T44_DOCKER_CONTEXT": "default",
            "COMPOSE_PROJECT_NAME": "t44",
        }
    )
    assert (
        hashlib.sha256(
            (ROOT / "deployment/encrypted-service-fixture.py").read_bytes()
        ).hexdigest()
        == host.WORKER_SHA
    )
    mounts = [argv[i + 1] for i, value in enumerate(argv) if value == "--volume"]
    assert len(mounts) == 5 and sum(value.endswith(":ro") for value in mounts) == 4
    assert mounts[-1] == "/run/t44-delivery/cohort-secrets:/run/t44-secrets:rw"
    assert "admin" in argv and "credential-admin" not in argv and "--rotate" not in argv
    assert argv.count("-f") == 2 and "T44_SESSION_TTL_SECONDS=5400" in argv
    assert not any("approved_origin" in value for value in argv)
    issue = service.issue_command(Path("/app/deployment/credential_admin.py"))
    assert issue[3:5] == ["--name", "notification-cohort"]
    assert [
        int(issue[i + 1]) for i, value in enumerate(issue) if value == "--project-id"
    ] == list(range(1, 41))
    assert "--rotate" not in issue
    assert str(host.TLS_HELPER) == "/run/t44-delivery/tls-delivery-extended.py"
    assert (
        host.TLS_SHA
        == "ea1b5873efb359e2e4e4adb8f020bfeab3da8f20e7661ae7bb7a5d883ac121d9"
    )


def test_service_fixture_public_receipt_cannot_disclose_token_or_origin():
    host = load(
        "service_fixture_receipt", ROOT / "deployment/service-fixture-launcher-cloud.py"
    )
    valid = {
        "success": True,
        "subject_id": 77,
        "session_id": 55,
        "expires_at": "2026-10-24T10:30:00.000000Z",
        "envelope_sha256": "a" * 64,
    }
    assert host.safe_receipt(json.dumps(valid)) == valid
    for extra in ({"token": "SYNTHETIC-ONLY"}, {"approved_origin": "SYNTHETIC-ONLY"}):
        with pytest.raises(ValueError):
            host.safe_receipt(json.dumps({**valid, **extra}))
    with pytest.raises(ValueError):
        host.safe_receipt('{"success":0,"error":"COHORT_FIXTURE_FAILED"}')
