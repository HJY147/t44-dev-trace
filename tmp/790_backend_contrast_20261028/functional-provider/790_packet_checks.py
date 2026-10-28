"""Own synthetic PUBLIC-interface codec checks, no independent cases/private key reads."""

import base64
import gzip
import hmac
import importlib
import json
import os
import struct
import sys
from pathlib import Path

import pytest
from cryptography.hazmat.primitives import hashes, padding, serialization
from cryptography.hazmat.primitives.asymmetric import padding as asymmetric_padding
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from jsonschema import Draft202012Validator, FormatChecker

sys.path.insert(0, str(Path(__file__).resolve().parent))
codec = importlib.import_module("790_provider_crypto")
worker = importlib.import_module("790_provider_worker")


@pytest.fixture(scope="module")
def own_key():
    key = rsa.generate_private_key(public_exponent=65537, key_size=3072)
    public = key.public_key().public_bytes(
        serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
    )
    return key, public


@pytest.fixture
def synthetic_packet(own_key):
    _, public = own_key
    schema_raw = Path(os.environ["T44_PROVIDER_PUBLIC_SCHEMA"]).read_bytes()
    assert codec.sha(schema_raw) == worker.SCHEMA_SHA
    descriptor = {
        "recipient_nonce": "a" * 48,
        "expired_subject": "x",
        "revocation_subject": "m",
        "sut_identity": {
            "source_sha": worker.SOURCE,
            "source_archive_sha256": "b" * 64,
            "image_digest": "sha256:" + "c" * 64,
            "runtime_identity": "synthetic-only-runtime",
            "base_url": "https://172.21.182.245:19443/api/v1",
            "pinned_ip": "172.21.182.245",
            "ca_sha256": worker.CA_SHA,
            "isolated_resource_ids": ["synthetic-only-resource"],
            "main_http_session_ttl_seconds": 3600,
            "worker_count": 4,
            "schema_name": worker.core.F_DATABASE,
        },
        "auth_store_resource_id": "synthetic-only/" + worker.core.F_DATABASE,
        "root_grant_sha256": None,
        "fixture_ownership": "synthetic own local test only",
        "provider_label": "synthetic provider",
    }
    accounts = {
        label: {
            "username": "synthetic-" + label,
            "password": "PASSWORD_MUST_NOT_BE_INCLUDED",
        }
        for label in worker.core.LABELS
    }
    sessions = {
        label: {
            "user_id": min(index + 1, 5),
            "session_id": index + 1,
            "access_token": "synthetic-private-" + label + "-" * 40,
            "issued_at": "2026-10-28T06:00:00Z",
            "expires_at": "2026-10-28T07:00:00Z",
            "ttl_seconds": 60 if label == "expired" else 3600,
        }
        for index, label in enumerate([*worker.core.LABELS, "expired", "revocation"])
    }
    # Actual worker sessions use source IDs; these deliberately synthetic codec values are not SUT evidence.
    packet = worker.build_packet(
        descriptor,
        accounts,
        sessions,
        b"SYNTHETIC PUBLIC CA",
        {"observed_utc": "2026-10-28T06:01:01Z"},
    )
    return packet, json.loads(schema_raw), public


def unwrap(private, wrapped):
    return private.decrypt(
        base64.b64decode(wrapped),
        asymmetric_padding.OAEP(
            mgf=asymmetric_padding.MGF1(hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )


def decrypt(key, iv, ciphertext):
    decryptor = Cipher(algorithms.AES(key[:32]), modes.CBC(iv)).decryptor()
    padded = decryptor.update(ciphertext) + decryptor.finalize()
    unpadder = padding.PKCS7(128).unpadder()
    return unpadder.update(padded) + unpadder.finalize()


def test_strict_public_v2_schema_and_no_password(synthetic_packet):
    packet, schema, _ = synthetic_packet
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(packet)
    assert b"PASSWORD_MUST_NOT_BE_INCLUDED" not in codec.canonical(packet)
    assert packet["root_grant_sha256"] is None
    assert packet["session_provenance"]["revocation"]["state_at_delivery"] == "active"
    assert (
        packet["session_provenance"]["expired"]["state_at_delivery"]
        == "naturally_expired"
    )


def test_t44fenv1_exact_roundtrip_prefix_hmac_and_header(synthetic_packet, own_key):
    packet, _, public = synthetic_packet
    private, _ = own_key
    raw = codec.functional(packet, public, codec.sha(public))
    assert raw[:8] == b"T44FENV1"
    size = struct.unpack(">I", raw[8:12])[0]
    header = json.loads(raw[12 : 12 + size])
    assert set(header) == {
        "kind",
        "recipient_nonce",
        "recipient_public_key_sha256",
        "tool_freeze_sha256",
        "tool_execution_build_sha256",
        "root_grant_sha256",
        "wrapped_key_b64",
        "iv_b64",
        "plaintext_bytes",
        "plaintext_sha256",
        "gzip_bytes",
        "gzip_sha256",
    }
    key = unwrap(private, header["wrapped_key_b64"])
    assert hmac.compare_digest(raw[-32:], hmac.digest(key[32:], raw[:-32], "sha256"))
    zipped = decrypt(key, base64.b64decode(header["iv_b64"]), raw[12 + size : -32])
    plain = gzip.decompress(zipped)
    assert plain == codec.canonical(packet) + b"\n"
    assert (
        codec.sha(plain) == header["plaintext_sha256"]
        and len(plain) == header["plaintext_bytes"]
    )
    assert (
        codec.sha(zipped) == header["gzip_sha256"]
        and len(zipped) == header["gzip_bytes"]
    )
    changed = bytearray(raw[:-32])
    changed[12] ^= 1
    assert not hmac.compare_digest(raw[-32:], hmac.digest(key[32:], changed, "sha256"))


def test_wrong_recipient_pin_rejected(synthetic_packet):
    packet, _, public = synthetic_packet
    with pytest.raises(ValueError, match="PIN_DIFFERS"):
        codec.functional(packet, public, "0" * 64)


def test_scope_uses_its_own_request_key_context_and_empty_iterations(own_key):
    private, public = own_key
    context = {
        "tool_freeze_sha256": codec.FREEZE,
        "source_sha": worker.SOURCE,
        "phase": "functional",
        "resource_ids": ["synthetic-resource"],
        "native_runtime_identity": "synthetic-runtime",
        "supervisor_nonce": "synthetic-supervisor",
    }
    request = {
        "kind": "SERVICE_SCOPE_REQUEST",
        "nonce": "synthetic-scope-nonce",
        "project_ids": [9, 12],
        "iteration_ids": [],
        "scope": ["escalation:write"],
        "public_key_pem": public.decode(),
        "context": context,
    }
    credential = {
        "project_ids": [9, 12],
        "scope": ["escalation:write"],
        "token": "synthetic-private-token-" + "x" * 40,
        "applied_to": ["scheduler"],
    }
    sealed = codec.scope(request, credential, context, "2026-10-28T06:00:00Z")
    assert (
        sealed["context"] == context
        and "tool_execution_build_sha256" not in sealed["context"]
    )
    key = unwrap(private, sealed["wrapped_key_b64"])
    iv, cipher = (
        base64.b64decode(sealed["iv_b64"]),
        base64.b64decode(sealed["ciphertext_b64"]),
    )
    authenticated = (
        codec.canonical(
            {
                "nonce": request["nonce"],
                "project_ids": request["project_ids"],
                "context": context,
            }
        )
        + iv
        + cipher
    )
    assert sealed["hmac_sha256"] == hmac.digest(key[32:], authenticated, "sha256").hex()
    plain = json.loads(decrypt(key, iv, cipher))
    assert plain == {
        "nonce": request["nonce"],
        "project_ids": [9, 12],
        "credential": credential,
    }
    with pytest.raises(ValueError):
        codec.scope(
            request, credential, {**context, "supervisor_nonce": "different"}, "now"
        )
    with pytest.raises(ValueError):
        codec.scope(request, {**credential, "project_ids": [12, 9]}, context, "now")
    with pytest.raises(ValueError):
        codec.scope(request, {**credential, "applied_to": []}, context, "now")


def test_crypto_contains_no_subprocess_or_environment_secret_channel():
    import ast

    tree = ast.parse(Path(codec.__file__).read_text(), feature_version=(3, 10))
    assert not any(
        isinstance(node, ast.Import)
        and any(name.name in {"subprocess", "sys"} for name in node.names)
        for node in ast.walk(tree)
    )
    assert not any(
        isinstance(node, ast.Attribute)
        and node.attr in {"environ", "putenv", "system", "popen"}
        for node in ast.walk(tree)
    )
