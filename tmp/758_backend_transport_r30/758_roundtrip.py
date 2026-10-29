"""Real local OpenSSL/TLS with synthetic packets; no cloud, QA private data or real session."""

import contextlib
import hashlib
import importlib
import io
import json
import signal
import socket
import ssl
import subprocess
import sys
import threading
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

CODE = Path(__file__).resolve().parents[2] / "agents/backend/neutral-transport-r30"
sys.path.insert(0, str(CODE))
five = importlib.import_module("five_files")
policy = importlib.import_module("policy_790")
relay = importlib.import_module("opaque_tls")


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


@pytest.fixture(scope="module")
def material(tmp_path_factory):
    root = tmp_path_factory.mktemp("synthetic-neutral-transport").resolve()
    stop = (datetime.now(timezone.utc) + timedelta(seconds=180)).isoformat().replace("+00:00", "Z")
    inputs = root / "original-five"
    inputs.mkdir(mode=0o700)
    files = {
        "ca.pem": b"SYNTHETIC-CA-NOT-A-REAL-SUT-CA",
        "source-manifest.json": b'{"synthetic": "source"}',
        "backend-bundle-manifest.json": b'{"synthetic": "bundle"}',
        "backend-import-receipt.json": b'{"synthetic": "NOT_ACTUAL_IMPORT"}',
    }
    packet = {
        "schema": "NEUTRAL_772_INPUTS_V2_0B_V24",
        "run_id": "r30window01",
        "window": {"cost_stop_utc": stop},
        "identity": {
            "git_commit": five.SOURCE,
            "source_manifest_sha256": digest(files["source-manifest.json"]),
            "backend_bundle_manifest_sha256": digest(files["backend-bundle-manifest.json"]),
        },
        "environment": {"ca_sha256": digest(files["ca.pem"])},
        "loaded_receipt_sha256": digest(files["backend-import-receipt.json"]),
        "sessions": {
            role: {"token": "SYNTHETIC_NOT_REAL_" + role}
            for role in ("manager", "developer", "reviewer", "service")
        },
        "inventory": {"clients": [{"client_id": index, "synthetic": True} for index in range(400)]},
    }
    packet["binding_sha256"] = digest(five.canonical(packet))
    files["session.private.json"] = five.canonical(packet)
    for name, raw in files.items():
        five.write(inputs / name, raw)
    packed = root / "packed"
    gen_binding = digest(b"synthetic-gen-binding")
    reference = five.pack(inputs, packed, stop, gen_binding)
    module = policy.load_policy(stop)
    keys = root / "new-load-key"
    with contextlib.redirect_stdout(io.StringIO()):
        module.keygen(SimpleNamespace(output_dir=keys))
        module.seal(
            SimpleNamespace(
                public_key_file=keys / "public.pem",
                public_key_sha256=digest((keys / "public.pem").read_bytes()),
                binding_sha256=gen_binding,
                control=packed / "control.json",
                control_sha256=digest((packed / "control.json").read_bytes()),
                session=packed / "session-reference.json",
                packet_sha256=digest((packed / "session-reference.json").read_bytes()),
                ca=packed / "ca.pem",
                ca_sha256=digest((packed / "ca.pem").read_bytes()),
                mirror=packed / "mirror.json",
                mirror_sha256=digest((packed / "mirror.json").read_bytes()),
                output_dir=root / "sealed",
            )
        )
    transfer = root / "sealed/transfer.public.jsonl"
    first = json.loads(transfer.read_bytes().splitlines()[0])
    return SimpleNamespace(
        root=root,
        stop=stop,
        files=files,
        packed=packed,
        module=module,
        keys=keys,
        transfer=transfer,
        public=first,
        gen_binding=gen_binding,
        neutral=packet["binding_sha256"],
        reference=reference,
    )


def test_original_crypto_mirror_operator_extract_real_roundtrip(material):
    m = material
    with contextlib.redirect_stdout(io.StringIO()):
        m.module.open_transfer(
            SimpleNamespace(
                private_key=m.keys / "load-only-private.pem",
                transfer_file=m.transfer,
                public_record_sha256=m.public["public_record_sha256"],
                output_dir=m.root / "opened790",
            )
        )
    output = m.root / "operator-five"
    result = five.extract(m.root / "opened790", output, m.stop, m.gen_binding, m.neutral)
    assert set(path.name for path in (output / "inputs").iterdir()) == five.NAMES
    assert all((output / "inputs" / name).read_bytes() == raw for name, raw in m.files.items())
    assert all((output / "inputs" / name).stat().st_mode & 0o777 == 0o600 for name in five.NAMES)
    assert m.transfer.stat().st_size <= five.CAP
    assert set(result["files"]) == five.NAMES
    assert digest((CODE / "790_transfer.original.py").read_bytes()) == policy.ORIGINAL_SHA
    with pytest.raises((ValueError, FileExistsError)):
        five.extract(m.root / "opened790", output, m.stop, m.gen_binding, m.neutral)


def test_opaque_tampering_refused_before_open_output(material):
    m = material
    records = [json.loads(line) for line in m.transfer.read_bytes().splitlines()]
    records[1]["data"] = ("A" if records[1]["data"][0] != "A" else "B") + records[1]["data"][1:]
    path = m.root / "tampered.jsonl"
    five.write(path, b"".join(five.canonical(record) for record in records))
    with pytest.raises(ValueError):
        m.module.open_transfer(
            SimpleNamespace(
                private_key=m.keys / "load-only-private.pem",
                transfer_file=path,
                public_record_sha256=m.public["public_record_sha256"],
                output_dir=m.root / "must-not-open",
            )
        )
    assert not (m.root / "must-not-open").exists()


@pytest.fixture(scope="module")
def certificates(material):
    root = material.root
    for name in ("leaf", "untrusted"):
        result = subprocess.run(
            [
                "openssl",
                "req",
                "-x509",
                "-newkey",
                "rsa:2048",
                "-nodes",
                "-keyout",
                str(root / (name + ".key")),
                "-out",
                str(root / (name + ".pem")),
                "-days",
                "1",
                "-subj",
                "/CN=127.0.0.1",
                "-addext",
                "subjectAltName=IP:127.0.0.1",
            ],
            capture_output=True,
            check=False,
        )
        assert result.returncode == 0
        (root / (name + ".key")).chmod(0o600)
    return root


def configs(material, certificates, name):
    m = material
    with socket.socket() as candidate:
        candidate.bind(("127.0.0.1", 0))
        port = candidate.getsockname()[1]
    base = {
        "app_ip": "127.0.0.1",
        "load_ip": "127.0.0.1",
        "port": port,
        "cost_stop_utc": m.stop,
        "bytes": m.transfer.stat().st_size,
        "sha256": digest(m.transfer.read_bytes()),
        "source_file": str(m.transfer),
        "certificate_file": str(certificates / "leaf.pem"),
        "private_key_file": str(certificates / "leaf.key"),
        "ca_file": str(certificates / "leaf.pem"),
        "output_file": str(m.root / (name + ".received")),
    }
    return {**base, "attempt_marker": str(m.root / (name + ".serve.once"))}, {
        **base,
        "attempt_marker": str(m.root / (name + ".fetch.once")),
    }


def launch_server(config, monkeypatch):
    ready, results = threading.Event(), []

    def report(value, **kwargs):
        if "R30_OPAQUE_LISTENING" in value:
            ready.set()

    monkeypatch.setattr(relay, "print", report, raising=False)

    def target():
        try:
            results.append(relay.serve(config))
        except Exception as error:
            results.append(error)

    thread = threading.Thread(target=target, daemon=True)
    thread.start()
    assert ready.wait(5)
    return thread, results


def test_real_tls_one_get_exact_ciphertext_no_plaintext(material, certificates, monkeypatch):
    # Low-level loopback harness only. Production main separately rejects loopback/non-RFC1918.
    server, client = configs(material, certificates, "success")
    thread, results = launch_server(server, monkeypatch)
    result = relay.fetch(client)
    thread.join(5)
    assert not thread.is_alive() and isinstance(results[0], dict)
    assert result["kind"] == "R30_OPAQUE_FETCHED_ONCE"
    assert Path(client["output_file"]).read_bytes() == material.transfer.read_bytes()
    with contextlib.redirect_stdout(io.StringIO()):
        material.module.open_transfer(
            SimpleNamespace(
                private_key=material.keys / "load-only-private.pem",
                transfer_file=Path(client["output_file"]),
                public_record_sha256=material.public["public_record_sha256"],
                output_dir=material.root / "tls-received-opened",
            )
        )
    final = material.root / "tls-received-five"
    five.extract(
        material.root / "tls-received-opened",
        final,
        material.stop,
        material.gen_binding,
        material.neutral,
    )
    assert all(
        (final / "inputs" / name).read_bytes() == raw for name, raw in material.files.items()
    )
    with pytest.raises((ValueError, FileExistsError)):
        relay.fetch(client)


def test_real_wrong_ca_fails_no_output_or_retry(material, certificates, monkeypatch):
    server, client = configs(material, certificates, "wrongca")
    client["ca_file"] = str(certificates / "untrusted.pem")
    thread, results = launch_server(server, monkeypatch)
    with pytest.raises(ssl.SSLCertVerificationError):
        relay.fetch(client)
    thread.join(5)
    assert not thread.is_alive() and isinstance(results[0], ValueError)
    assert not Path(client["output_file"]).exists()
    assert Path(client["attempt_marker"]).exists()
    with pytest.raises(FileExistsError):
        relay.fetch(client)


def test_production_closed_cap_c_and_private_ip(material, certificates):
    server, client = configs(material, certificates, "negative")
    client.update(
        root_admit_transport=True,
        schema="r30-neutral-opaque-relay-v1",
        source_sha=five.SOURCE,
        ca_sha256=digest((certificates / "leaf.pem").read_bytes()),
    )
    with pytest.raises(ValueError):
        relay.validate(client, "fetch")
    client.update(app_ip="10.0.0.1", load_ip="10.0.0.2", bytes=five.CAP + 1)
    with pytest.raises(ValueError):
        relay.validate(client, "fetch")
    with pytest.raises(ValueError):
        policy.load_policy("2026-10-29T00:00:00Z")


def test_real_wrong_peer_is_rejected_before_tls_body(material, certificates, monkeypatch):
    server, client = configs(material, certificates, "wrongpeer")
    server["load_ip"] = "127.0.0.2"
    thread, results = launch_server(server, monkeypatch)
    with pytest.raises(OSError):
        relay.fetch(client)
    thread.join(5)
    assert not thread.is_alive() and isinstance(results[0], ValueError)
    assert not Path(client["output_file"]).exists()


def test_cli_absolute_c_alarm_is_real_not_a_deadline_relabel(tmp_path, monkeypatch):
    path = tmp_path / "deadline.json"
    path.write_text(
        json.dumps(
            {
                "cost_stop_utc": (datetime.now(timezone.utc) + timedelta(seconds=0.15))
                .isoformat()
                .replace("+00:00", "Z")
            }
        )
    )
    monkeypatch.setattr(sys, "argv", ["opaque_tls.py", "serve", "--config", str(path)])
    monkeypatch.setattr(relay, "validate", lambda *args: None)
    monkeypatch.setattr(relay, "serve", lambda *args: time.sleep(5))
    previous = signal.getsignal(signal.SIGALRM)
    started = time.monotonic()
    try:
        with pytest.raises(TimeoutError, match="ABSOLUTE_C_HARD_STOP"):
            relay.main()
    finally:
        signal.signal(signal.SIGALRM, previous)
    assert time.monotonic() - started < 1
