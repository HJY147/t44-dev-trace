"""One-time RSA-OAEP / AES-CBC + HMAC transport; stdout is public or ciphertext only."""

import argparse
import base64
import gzip
import hashlib
import hmac
import io
import json
import os
import re
import stat
import subprocess
from datetime import datetime, timezone
from pathlib import Path

UTC = timezone.utc  # noqa: UP017 -- Ubuntu host Python 3.10.
STOP = datetime(2026, 10, 28, 7, 30, tzinfo=UTC)
SOURCE = "a12e9e70b963bacafda3242bb6d82e53ee912ff1"
KIND = "t44-790-opaque-transfer-v1"
LIMIT = 2_000_000
CHUNK = 16000
NAMES = {"control.private.json", "session.private.json", "ca.pem"}
MIRROR = "private-mirror-handoff.json"


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def b64(raw):
    return base64.b64encode(raw).decode()


def unb64(value):
    return base64.b64decode(value, validate=True)


def budget():
    remaining = (STOP - datetime.now(UTC)).total_seconds()
    if remaining <= 0:
        raise ValueError("TRANSFER_HARDSTOP_EXPIRED")
    return min(60, remaining)


def read(path, private=True):
    path = Path(path)
    if not path.is_absolute() or path.resolve() != path:
        raise ValueError("CANONICAL_ABSOLUTE_INPUT_REQUIRED")
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_size > LIMIT:
            raise ValueError("BOUNDED_REGULAR_INPUT_REQUIRED")
        if private and stat.S_IMODE(info.st_mode) & 0o077:
            raise ValueError("PRIVATE_INPUT_MODE_REQUIRED")
        with os.fdopen(fd, "rb", closefd=False) as stream:
            return stream.read(LIMIT + 1)
    finally:
        os.close(fd)


def write(path, raw):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    try:
        with os.fdopen(fd, "wb", closefd=False) as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(fd)
    finally:
        os.close(fd)


def new_directory(path):
    path = Path(path)
    if not path.is_absolute() or path.parent.resolve() != path.parent:
        raise ValueError("NEW_CANONICAL_ABSOLUTE_DIRECTORY_REQUIRED")
    path.mkdir(mode=0o700)
    return path


def openssl(args, raw=b""):
    result = subprocess.run(
        ["openssl", *args],
        input=raw,
        capture_output=True,
        timeout=budget(),
        check=False,
    )
    if result.returncode:
        raise ValueError("OPENSSL_OPERATION_FAILED_PRIVATE_STDERR_SUPPRESSED")
    budget()
    return result.stdout


def check_hash(raw, wanted):
    if not re.fullmatch(r"[0-9a-f]{64}", wanted) or digest(raw) != wanted:
        raise ValueError("PINNED_INPUT_HASH_DIFFERS")


def emit(value):
    print(canonical(value).decode(), flush=True)


def keygen(args):
    budget()
    directory = new_directory(args.output_dir)
    private = directory / "load-only-private.pem"
    write(private, b"")
    openssl(
        [
            "genpkey",
            "-algorithm",
            "RSA",
            "-pkeyopt",
            "rsa_keygen_bits:3072",
            "-out",
            str(private),
        ]
    )
    public = openssl(["pkey", "-in", str(private), "-pubout"])
    write(directory / "public.pem", public)
    record = {
        "kind": "PUBLIC-790-KEY",
        "public_key_sha256": digest(public),
        "public_key_b64": b64(public),
    }
    write(directory / "public-key.json", canonical(record) + b"\n")
    emit(record)


def validate_files(files, binding):
    if set(files) not in (NAMES, NAMES | {MIRROR}):
        raise ValueError("EXACT_THREE_INPUTS_OPTIONAL_SEPARATE_MIRROR_REQUIRED")
    control = json.loads(files["control.private.json"])
    if control.get("source_sha") != SOURCE or control.get("binding_sha256") != binding:
        raise ValueError("SOURCE_OR_ACTUAL_BINDING_DIFFERS")
    if control.get("ca_sha256") != digest(files["ca.pem"]):
        raise ValueError("CONTROL_CA_HASH_DIFFERS")
    stamp = datetime.fromisoformat(
        control["stop_utc"].replace("Z", "+00:00")  # noqa: FURB162 -- Python 3.10 host.
    )
    if stamp != STOP:
        raise ValueError("EXACT_CONTROL_HARDSTOP_REQUIRED")
    # Packet semantics, session expiry and resource handoff are separately validated by consumers.
    json.loads(files["session.private.json"])
    if MIRROR in files:
        json.loads(files[MIRROR])


def seal(args):
    budget()
    public = read(args.public_key_file, False)
    check_hash(public, args.public_key_sha256)
    files = {}
    for name, path, wanted in (
        ("control.private.json", args.control, args.control_sha256),
        ("session.private.json", args.session, args.packet_sha256),
        ("ca.pem", args.ca, args.ca_sha256),
    ):
        files[name] = read(path, name != "ca.pem")
        check_hash(files[name], wanted)
    if bool(args.mirror) != bool(args.mirror_sha256):
        raise ValueError("MIRROR_PATH_AND_PIN_BOTH_REQUIRED")
    if args.mirror:
        files[MIRROR] = read(args.mirror)
        check_hash(files[MIRROR], args.mirror_sha256)
    validate_files(files, args.binding_sha256)
    plaintext = canonical({name: b64(raw) for name, raw in files.items()})
    if len(plaintext) > LIMIT:
        raise ValueError("TRANSFER_INPUT_TOO_LARGE")
    compressed = gzip.compress(plaintext, mtime=0)
    keys, iv = os.urandom(64), os.urandom(16)
    wrapped = openssl(
        [
            "pkeyutl",
            "-encrypt",
            "-pubin",
            "-inkey",
            str(args.public_key_file),
            "-pkeyopt",
            "rsa_padding_mode:oaep",
            "-pkeyopt",
            "rsa_oaep_md:sha256",
            "-pkeyopt",
            "rsa_mgf1_md:sha256",
        ],
        keys,
    )
    cipher = openssl(
        ["enc", "-aes-256-cbc", "-nosalt", "-K", keys[:32].hex(), "-iv", iv.hex()],
        compressed,
    )
    envelope = {
        "kind": KIND,
        "key_sha256": digest(public),
        "wrapped": b64(wrapped),
        "iv": b64(iv),
        "cipher": b64(cipher),
    }
    envelope["hmac"] = hmac.new(
        keys[32:], canonical(envelope), hashlib.sha256
    ).hexdigest()
    opaque = b64(canonical(envelope))
    chunks = [opaque[index : index + CHUNK] for index in range(0, len(opaque), CHUNK)]
    info = {
        "kind": "PUBLIC-790-TRANSFER",
        "key_sha256": digest(public),
        "binding_sha256": args.binding_sha256,
        "files": {
            name: {"bytes": len(raw), "sha256": digest(raw)}
            for name, raw in files.items()
        },
        "opaque_sha256": digest(opaque.encode()),
        "opaque_chars": len(opaque),
        "chunks": len(chunks),
        "gzip_bytes": len(compressed),
    }
    public_record = {**info, "public_record_sha256": digest(canonical(info))}
    records = [public_record] + [
        {"kind": "OPAQUE", "part": index + 1, "total": len(chunks), "data": value}
        for index, value in enumerate(chunks)
    ]
    budget()
    directory = new_directory(args.output_dir)
    raw = b"".join(canonical(record) + b"\n" for record in records)
    write(directory / "transfer.public.jsonl", raw)
    for record in records:
        emit(record)


def open_transfer(args):
    budget()
    records = [
        json.loads(line) for line in read(args.transfer_file, False).splitlines()
    ]
    public = records[0]
    if public.get("kind") != "PUBLIC-790-TRANSFER":
        raise ValueError("PUBLIC_TRANSFER_RECORD_REQUIRED")
    wanted = public.pop("public_record_sha256")
    check_hash(canonical(public), args.public_record_sha256)
    if wanted != args.public_record_sha256 or public["chunks"] != len(records) - 1:
        raise ValueError("COMPLETE_PINNED_TRANSFER_RECORD_REQUIRED")
    chunks = []
    for index, row in enumerate(records[1:], 1):
        if (
            row.get("kind") != "OPAQUE"
            or row.get("part") != index
            or row.get("total") != public["chunks"]
        ):
            raise ValueError("ORDERED_UNIQUE_COMPLETE_OPAQUE_PARTS_REQUIRED")
        if not isinstance(row.get("data"), str) or len(row["data"]) > CHUNK:
            raise ValueError("BOUNDED_OPAQUE_PART_REQUIRED")
        chunks.append(row["data"])
    opaque = "".join(chunks).encode()
    check_hash(opaque, public["opaque_sha256"])
    if len(opaque) != public["opaque_chars"]:
        raise ValueError("OPAQUE_LENGTH_DIFFERS")
    envelope = json.loads(unb64(opaque))
    if (
        set(envelope) != {"kind", "key_sha256", "wrapped", "iv", "cipher", "hmac"}
        or envelope["kind"] != KIND
    ):
        raise ValueError("EXACT_ENVELOPE_REQUIRED")
    private = read(args.private_key)
    if not private:
        raise ValueError("LOAD_PRIVATE_KEY_REQUIRED")
    actual_public = openssl(["pkey", "-in", str(args.private_key), "-pubout"])
    if (
        digest(actual_public) != envelope["key_sha256"]
        or envelope["key_sha256"] != public["key_sha256"]
    ):
        raise ValueError("LOAD_KEY_FINGERPRINT_DIFFERS")
    keys = openssl(
        [
            "pkeyutl",
            "-decrypt",
            "-inkey",
            str(args.private_key),
            "-pkeyopt",
            "rsa_padding_mode:oaep",
            "-pkeyopt",
            "rsa_oaep_md:sha256",
            "-pkeyopt",
            "rsa_mgf1_md:sha256",
        ],
        unb64(envelope["wrapped"]),
    )
    mac = envelope.pop("hmac")
    if len(keys) != 64 or not hmac.compare_digest(
        mac, hmac.new(keys[32:], canonical(envelope), hashlib.sha256).hexdigest()
    ):
        raise ValueError("HMAC_INVALID_NO_PLAINTEXT_DECRYPTION")
    iv = unb64(envelope["iv"])
    if len(iv) != 16:
        raise ValueError("AES_IV_INVALID")
    compressed = openssl(
        [
            "enc",
            "-d",
            "-aes-256-cbc",
            "-nosalt",
            "-K",
            keys[:32].hex(),
            "-iv",
            iv.hex(),
        ],
        unb64(envelope["cipher"]),
    )
    with gzip.GzipFile(fileobj=io.BytesIO(compressed)) as stream:
        raw = stream.read(LIMIT + 1)
    if len(raw) > LIMIT:
        raise ValueError("DECOMPRESSED_INPUT_TOO_LARGE")
    files = {name: unb64(value) for name, value in json.loads(raw).items()}
    validate_files(files, public["binding_sha256"])
    actual = {
        name: {"bytes": len(value), "sha256": digest(value)}
        for name, value in files.items()
    }
    if actual != public["files"]:
        raise ValueError("APP_PINNED_FILE_HASHES_DIFFER")
    budget()
    directory = new_directory(args.output_dir)
    inputs = directory / "inputs"
    inputs.mkdir(mode=0o700)
    for name in sorted(NAMES):
        budget()
        write(inputs / name, files[name])
    if MIRROR in files:
        mirror = directory / "mirror"
        mirror.mkdir(mode=0o700)
        write(mirror / MIRROR, files[MIRROR])
    receipt = {
        "kind": "PUBLIC-790-OPENED",
        "inputs_dir": str(inputs),
        "files": actual,
        "public_record_sha256": args.public_record_sha256,
        "binding_sha256": public["binding_sha256"],
    }
    write(directory / "receipt.public.json", canonical(receipt) + b"\n")
    emit(receipt)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_subparsers(dest="action", required=True)
    key = actions.add_parser("keygen")
    key.add_argument("--output-dir", type=Path, required=True)
    encrypt = actions.add_parser("seal")
    for name in ("public-key-file", "control", "session", "ca", "output-dir"):
        encrypt.add_argument("--" + name, type=Path, required=True)
    for name in (
        "public-key-sha256",
        "binding-sha256",
        "control-sha256",
        "packet-sha256",
        "ca-sha256",
    ):
        encrypt.add_argument("--" + name, required=True)
    encrypt.add_argument("--mirror", type=Path)
    encrypt.add_argument("--mirror-sha256")
    decrypt = actions.add_parser("open")
    for name in ("private-key", "transfer-file", "output-dir"):
        decrypt.add_argument("--" + name, type=Path, required=True)
    decrypt.add_argument("--public-record-sha256", required=True)
    args = parser.parse_args(argv)
    {"keygen": keygen, "seal": seal, "open": open_transfer}[args.action](args)


if __name__ == "__main__":
    os.umask(0o077)
    try:
        main()
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError):
        emit({"kind": "PUBLIC-790-TRANSFER-FAILED", "private_output_printed": False})
        raise SystemExit(1) from None
