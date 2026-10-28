"""Synthetic no-network transport checks; never import/read cloud private packets."""

import argparse
import ast
import base64
import importlib.util
import json
import os
import stat
from datetime import datetime
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("transfer790", HERE / "790_transfer.py")
tool = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tool)


def namespace(**kwargs):
    return argparse.Namespace(**kwargs)


def put(path, raw):
    tool.write(path, raw)
    return tool.digest(raw)


@pytest.fixture(scope="module")
def prepared(tmp_path_factory):
    root = tmp_path_factory.mktemp("transport-synthetic")
    tool.keygen(namespace(output_dir=root / "key"))
    source = root / "app"
    source.mkdir(mode=0o700)
    ca = b"SYNTHETIC PUBLIC CA ONLY\n"
    binding = "e" * 64
    control = {
        "source_sha": tool.SOURCE,
        "binding_sha256": binding,
        "ca_sha256": tool.digest(ca),
        "stop_utc": "2026-10-28T16:00:00Z",
    }
    session = {
        "synthetic": True,
        "opaque_test_data": base64.b64encode(os.urandom(36000)).decode(),
    }
    hashes = {}
    for name, raw in {
        "control.private.json": tool.canonical(control),
        "session.private.json": tool.canonical(session),
        "ca.pem": ca,
        tool.MIRROR: b'{"synthetic_mirror":true}',
    }.items():
        hashes[name] = put(source / name, raw)
    args = namespace(
        public_key_file=root / "key/public.pem",
        public_key_sha256=tool.digest((root / "key/public.pem").read_bytes()),
        control=source / "control.private.json",
        session=source / "session.private.json",
        ca=source / "ca.pem",
        control_sha256=hashes["control.private.json"],
        packet_sha256=hashes["session.private.json"],
        ca_sha256=hashes["ca.pem"],
        binding_sha256=binding,
        output_dir=root / "sealed",
        mirror=source / tool.MIRROR,
        mirror_sha256=hashes[tool.MIRROR],
    )
    tool.seal(args)
    rows = [
        json.loads(line)
        for line in (root / "sealed/transfer.public.jsonl").read_bytes().splitlines()
    ]
    return root, args, rows


def open_args(root, rows, name="opened"):
    return namespace(
        private_key=root / "key/load-only-private.pem",
        transfer_file=root / "sealed/transfer.public.jsonl",
        output_dir=root / name,
        public_record_sha256=rows[0]["public_record_sha256"],
    )


def test_roundtrip_exact_three_plus_separate_mirror(prepared, capsys):
    root, _, rows = prepared
    tool.open_transfer(open_args(root, rows))
    assert {p.name for p in (root / "opened/inputs").iterdir()} == tool.NAMES
    for name in tool.NAMES:
        assert (root / "opened/inputs" / name).read_bytes() == (
            root / "app" / name
        ).read_bytes()
    assert (root / "opened/mirror" / tool.MIRROR).read_bytes() == (
        root / "app" / tool.MIRROR
    ).read_bytes()
    assert "opaque_test_data" not in capsys.readouterr().out


def test_chunks_bounded_and_multisegment(prepared):
    _, _, rows = prepared
    assert rows[0]["opaque_chars"] > 18000
    assert len(rows) > 2
    assert all(len(row["data"]) <= 16000 for row in rows[1:])


def test_private_modes(prepared):
    root, _, _ = prepared
    for path in (
        root / "key/load-only-private.pem",
        root / "opened/inputs/control.private.json",
        root / "opened/inputs/session.private.json",
        root / "opened/mirror" / tool.MIRROR,
    ):
        assert stat.S_IMODE(path.stat().st_mode) == 0o600
    for path in (
        root / "key",
        root / "opened",
        root / "opened/inputs",
        root / "opened/mirror",
    ):
        assert stat.S_IMODE(path.stat().st_mode) == 0o700


def test_existing_output_rejected(prepared):
    root, _, rows = prepared
    with pytest.raises(FileExistsError):
        tool.open_transfer(open_args(root, rows))


def test_wrong_public_pin_no_output(prepared):
    root, _, rows = prepared
    args = open_args(root, rows, "wrong-pin")
    args.public_record_sha256 = "0" * 64
    with pytest.raises(ValueError, match="HASH_DIFFERS"):
        tool.open_transfer(args)
    assert not args.output_dir.exists()


def test_wrong_app_file_pin(prepared):
    _, args, _ = prepared
    changed = namespace(**vars(args))
    changed.packet_sha256 = "0" * 64
    with pytest.raises(ValueError, match="HASH_DIFFERS"):
        tool.seal(changed)


def test_hmac_tamper_before_plaintext_decrypt(prepared, monkeypatch):
    root, _, rows = prepared
    altered = json.loads(json.dumps(rows))
    envelope = json.loads(tool.unb64("".join(row["data"] for row in altered[1:])))
    cipher = bytearray(tool.unb64(envelope["cipher"]))
    cipher[0] ^= 1
    envelope["cipher"] = tool.b64(cipher)
    opaque = tool.b64(tool.canonical(envelope))
    parts = [
        opaque[index : index + tool.CHUNK]
        for index in range(0, len(opaque), tool.CHUNK)
    ]
    public = altered[0]
    public.pop("public_record_sha256")
    public.update(
        opaque_sha256=tool.digest(opaque.encode()),
        opaque_chars=len(opaque),
        chunks=len(parts),
    )
    public["public_record_sha256"] = tool.digest(tool.canonical(public))
    record_path = root / "tampered.public.jsonl"
    put(
        record_path,
        b"\n".join(
            tool.canonical(row)
            for row in [public]
            + [
                {"kind": "OPAQUE", "part": i + 1, "total": len(parts), "data": part}
                for i, part in enumerate(parts)
            ]
        ),
    )
    args = open_args(root, [public], "tampered-open")
    args.transfer_file = record_path
    original, calls = tool.openssl, []

    def watched(argv, raw=b""):
        calls.append(argv)
        return original(argv, raw)

    monkeypatch.setattr(tool, "openssl", watched)
    with pytest.raises(ValueError, match="HMAC_INVALID"):
        tool.open_transfer(args)
    assert not any(argv[:2] == ["enc", "-d"] for argv in calls)
    assert not args.output_dir.exists()


def test_missing_chunk_rejected(prepared):
    root, _, rows = prepared
    path = root / "incomplete.public.jsonl"
    put(path, b"\n".join(tool.canonical(row) for row in rows[:-1]))
    args = open_args(root, rows, "missing-open")
    args.transfer_file = path
    with pytest.raises(ValueError, match="COMPLETE"):
        tool.open_transfer(args)
    assert not args.output_dir.exists()


def test_symlink_and_insecure_private_rejected(prepared):
    root, _, _ = prepared
    insecure = root / "insecure"
    put(insecure, b"synthetic")
    insecure.chmod(0o644)
    with pytest.raises(ValueError, match="PRIVATE_INPUT_MODE"):
        tool.read(insecure)
    link = root / "symlink"
    link.symlink_to(insecure)
    with pytest.raises(ValueError, match="CANONICAL"):
        tool.read(link)


def test_deadline_prevents_any_openssl(monkeypatch, tmp_path):
    monkeypatch.setattr(tool, "STOP", datetime(2000, 1, 1, tzinfo=tool.UTC))
    with pytest.raises(ValueError, match="HARDSTOP"):
        tool.keygen(namespace(output_dir=tmp_path / "expired"))
    assert not (tmp_path / "expired").exists()


def test_host_python310_syntax():
    ast.parse((HERE / "790_transfer.py").read_text(), feature_version=(3, 10))
    assert "from datetime import UTC" not in (HERE / "790_transfer.py").read_text()


def test_exact_three_without_mirror(prepared):
    root, args, _ = prepared
    changed = namespace(**vars(args))
    changed.output_dir = root / "sealed-three"
    changed.mirror = changed.mirror_sha256 = None
    tool.seal(changed)
    rows = [
        json.loads(line)
        for line in (changed.output_dir / "transfer.public.jsonl")
        .read_bytes()
        .splitlines()
    ]
    opened = open_args(root, rows, "opened-three")
    opened.transfer_file = changed.output_dir / "transfer.public.jsonl"
    tool.open_transfer(opened)
    assert not (opened.output_dir / "mirror").exists()
    assert set(rows[0]["files"]) == tool.NAMES


def test_binding_and_ca_validation_rejects(prepared):
    root, _, _ = prepared
    files = {name: (root / "app" / name).read_bytes() for name in tool.NAMES}
    with pytest.raises(ValueError, match="BINDING"):
        tool.validate_files(files, "0" * 64)
    files["ca.pem"] = b"different"
    with pytest.raises(ValueError, match="CA_HASH"):
        tool.validate_files(files, "e" * 64)
