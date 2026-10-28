"""T12 PUBLIC v2 wire encoders. No secret argv/env/subprocess or recipient private keys."""

import base64
import gzip
import hashlib
import hmac
import json
import os
import struct

from cryptography.hazmat.primitives import hashes, padding, serialization
from cryptography.hazmat.primitives.asymmetric import padding as asymmetric_padding
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicKey
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

FREEZE = "33dd522d382bb166d331489e46166a8a59c1b985e065b4849acbf7674ad5309e"
EXECUTION_BUILD = "e8ac37bb41c474681f2ea36598806cb7ba0605ee26b82cfdc4fe462c7a2d16ae"


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def b64(raw):
    return base64.b64encode(raw).decode()


def public_key(pem, expected_sha=None):
    raw = pem.encode() if isinstance(pem, str) else pem
    if expected_sha is not None and sha(raw) != expected_sha:
        raise ValueError("RECIPIENT_PUBLIC_KEY_PIN_DIFFERS")
    key = serialization.load_pem_public_key(raw)
    if not isinstance(key, RSAPublicKey) or key.key_size != 3072:
        raise ValueError("EXACT_RECIPIENT_RSA3072_REQUIRED")
    return key, sha(raw)


def encrypt(raw, pem, expected_sha=None):
    key, fingerprint = public_key(pem, expected_sha)
    material, iv = os.urandom(64), os.urandom(16)
    padder = padding.PKCS7(128).padder()
    padded = padder.update(raw) + padder.finalize()
    encryptor = Cipher(algorithms.AES(material[:32]), modes.CBC(iv)).encryptor()
    ciphertext = encryptor.update(padded) + encryptor.finalize()
    wrapped = key.encrypt(
        material,
        asymmetric_padding.OAEP(
            mgf=asymmetric_padding.MGF1(hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )
    return material, iv, ciphertext, wrapped, fingerprint


def functional(payload, pem, expected_sha):
    if (
        payload["tool_freeze_sha256"] != FREEZE
        or payload["tool_execution_build_sha256"] != EXECUTION_BUILD
    ):
        raise ValueError("EXACT_T12_TOOLS_REQUIRED")
    plain = canonical(payload) + b"\n"
    zipped = gzip.compress(plain, mtime=0)
    if len(plain) > 4 * 1024 * 1024 or len(zipped) > 1024 * 1024:
        raise ValueError("FUNCTIONAL_PACKET_SIZE_LIMIT")
    key, iv, ciphertext, wrapped, fingerprint = encrypt(zipped, pem, expected_sha)
    header = {
        "kind": "FUNCTIONAL_MATERIAL_PACKET_V1",
        "recipient_nonce": payload["recipient_nonce"],
        "recipient_public_key_sha256": fingerprint,
        "tool_freeze_sha256": FREEZE,
        "tool_execution_build_sha256": EXECUTION_BUILD,
        "root_grant_sha256": payload["root_grant_sha256"],
        "wrapped_key_b64": b64(wrapped),
        "iv_b64": b64(iv),
        "plaintext_bytes": len(plain),
        "plaintext_sha256": sha(plain),
        "gzip_bytes": len(zipped),
        "gzip_sha256": sha(zipped),
    }
    header_raw = canonical(header)
    if len(header_raw) > 16384:
        raise ValueError("FUNCTIONAL_HEADER_LIMIT")
    prefix = b"T44FENV1" + struct.pack(">I", len(header_raw)) + header_raw + ciphertext
    return prefix + hmac.digest(key[32:], prefix, "sha256")


def scope(request, credential, expected_context, sealed_utc):
    if (
        request.get("kind") != "SERVICE_SCOPE_REQUEST"
        or request.get("scope") != ["escalation:write"]
        or request.get("context") != expected_context
        or credential.get("project_ids") != request.get("project_ids")
        or credential.get("scope") != ["escalation:write"]
        or "scheduler" not in credential.get("applied_to", [])
        or len(credential.get("token", "")) < 32
    ):
        raise ValueError("ACTUAL_SCOPE_REQUEST_CONTEXT_AND_APPLIED_CREDENTIAL_REQUIRED")
    nonce, ids, context = request["nonce"], request["project_ids"], request["context"]
    if (
        not isinstance(ids, list)
        or not ids
        or len(set(ids)) != len(ids)
        or any(type(value) is not int or value < 1 for value in ids)
    ):
        raise ValueError("EXACT_ORDERED_POSITIVE_PROJECT_IDS_REQUIRED")
    plain = canonical({"nonce": nonce, "project_ids": ids, "credential": credential})
    key, iv, ciphertext, wrapped, _ = encrypt(plain, request["public_key_pem"])
    authenticated = (
        canonical({"nonce": nonce, "project_ids": ids, "context": context}) + iv + ciphertext
    )
    return {
        "kind": "SEALED_SERVICE_SCOPE",
        "nonce": nonce,
        "project_ids": ids,
        "context": context,
        "wrapped_key_b64": b64(wrapped),
        "iv_b64": b64(iv),
        "ciphertext_b64": b64(ciphertext),
        "hmac_sha256": hmac.digest(key[32:], authenticated, "sha256").hex(),
        "sealed_utc": sealed_utc,
    }
