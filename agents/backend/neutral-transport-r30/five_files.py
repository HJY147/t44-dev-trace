"""Bound exactly five original neutral files into a JSON mirror; extract only as operator."""

import argparse
import base64
import gzip
import hashlib
import io
import json
import os
import re
import stat
import tarfile
from datetime import datetime, timezone
from pathlib import Path

SOURCE = "0bffe0c535e5897890aebf30879fdd3839dc52d6"
CAP = 4 * 1024 * 1024
NAMES = {
    "session.private.json",
    "ca.pem",
    "source-manifest.json",
    "backend-bundle-manifest.json",
    "backend-import-receipt.json",
}


def need(value, code):
    if not value:
        raise ValueError(code)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def bounded(path, cap=CAP):
    path = Path(path)
    need(path.is_absolute() and path.resolve() == path, "CANONICAL_FILE_REQUIRED")
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(descriptor, "rb") as stream:
        before = os.fstat(stream.fileno())
        need(
            stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and before.st_size <= cap,
            "BOUNDED_REGULAR_FILE_REQUIRED",
        )
        raw = stream.read(cap + 1)
        after = os.fstat(stream.fileno())
    need(
        (before.st_ino, before.st_size, before.st_mtime_ns)
        == (after.st_ino, after.st_size, after.st_mtime_ns)
        and len(raw) == before.st_size,
        "STABLE_COMPLETE_FILE_REQUIRED",
    )
    return raw


def write(path, raw):
    path = Path(path)
    need(
        path.is_absolute() and path.parent.resolve() == path.parent,
        "CANONICAL_ABSOLUTE_OUTPUT_REQUIRED",
    )
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())


def stamp(value):
    need(isinstance(value, str) and value.endswith("Z"), "EXPLICIT_UTC_Z_REQUIRED")
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def remaining(stop):
    left = (stamp(stop) - datetime.now(timezone.utc)).total_seconds()
    need(0 < left <= 3600, "ABSOLUTE_C_EXPIRED_OR_UNBOUNDED")
    return left


def canonical(value):
    return (
        json.dumps(
            value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode()
        + b"\n"
    )


def validate_five(files, stop, neutral_binding):
    need(
        set(files) == NAMES and sum(map(len, files.values())) <= CAP,
        "EXACT_FIVE_WITHIN_4M_REQUIRED",
    )
    packet = json.loads(files["session.private.json"])
    need(
        packet["schema"] == "NEUTRAL_772_INPUTS_V2_0B_V24"
        and packet["identity"]["git_commit"] == SOURCE
        and packet["window"]["cost_stop_utc"] == stop,
        "EXACT_NEW_0B_PACKET_AND_C_REQUIRED",
    )
    binding = packet.pop("binding_sha256")
    need(binding == neutral_binding == sha(canonical(packet)), "ORIGINAL_NEUTRAL_BINDING_REQUIRED")
    need(
        sha(files["source-manifest.json"]) == packet["identity"]["source_manifest_sha256"]
        and sha(files["backend-bundle-manifest.json"])
        == packet["identity"]["backend_bundle_manifest_sha256"]
        and sha(files["backend-import-receipt.json"]) == packet["loaded_receipt_sha256"]
        and sha(files["ca.pem"]) == packet["environment"]["ca_sha256"],
        "EXACT_FIVE_ORIGINAL_RAW_HASHES_REQUIRED",
    )
    return packet


def pack(inputs, output, stop, gen_binding):
    remaining(stop)
    need(re.fullmatch(r"[0-9a-f]{64}", gen_binding or ""), "EXACT_GEN_BINDING_SHA_REQUIRED")
    need(set(path.name for path in inputs.iterdir()) == NAMES, "ONLY_ORIGINAL_FIVE_FILES_ALLOWED")
    files = {name: bounded(inputs / name) for name in NAMES}
    neutral = json.loads(files["session.private.json"])["binding_sha256"]
    packet = validate_five(files, stop, neutral)
    archive_stream = io.BytesIO()
    with tarfile.open(fileobj=archive_stream, mode="w", format=tarfile.USTAR_FORMAT) as archive:
        for name in sorted(files):
            member = tarfile.TarInfo(name)
            member.size, member.mode, member.mtime = len(files[name]), 0o600, 0
            archive.addfile(member, io.BytesIO(files[name]))
    plain = archive_stream.getvalue()
    need(len(plain) <= CAP, "TAR_PLAINTEXT_CAP")
    compressed = gzip.compress(plain, mtime=0)
    need(len(compressed) <= CAP, "COMPRESSED_ARCHIVE_CAP")
    index = {name: {"bytes": len(raw), "sha256": sha(raw)} for name, raw in files.items()}
    reference = {
        "schema": "R30-NEUTRAL-FIVE-ARCHIVE-REFERENCE-v1",
        "source_sha": SOURCE,
        "cost_stop_utc": stop,
        "gen_binding_sha256": gen_binding,
        "neutral_binding_sha256": neutral,
        "archive_sha256": sha(compressed),
        "archive_bytes": len(compressed),
        "files": index,
    }
    mirror = {
        "schema": "R30-NEUTRAL-FIVE-MIRROR-v1",
        "archive_b64": base64.b64encode(compressed).decode(),
    }
    control = {
        "source_sha": SOURCE,
        "binding_sha256": gen_binding,
        "ca_sha256": sha(files["ca.pem"]),
        "stop_utc": stop,
    }
    need(
        output.parent.resolve() == output.parent and not output.exists(),
        "NEW_CANONICAL_OUTPUT_REQUIRED",
    )
    output.mkdir(mode=0o700)
    for name, raw in (
        ("control.json", canonical(control)),
        ("session-reference.json", canonical(reference)),
        ("mirror.json", canonical(mirror)),
        ("ca.pem", files["ca.pem"]),
    ):
        write(output / name, raw)
    receipt = {
        "kind": "R30_FIVE_PACKED_NOT_A_GRANT",
        "run_id": packet["run_id"],
        **reference,
        "inputs": {
            name: {"sha256": sha(bounded(output / name)), "bytes": (output / name).stat().st_size}
            for name in ("control.json", "session-reference.json", "mirror.json", "ca.pem")
        },
    }
    write(output / "pack.PUBLIC.json", canonical(receipt))
    return receipt


def extract(opened, output, stop, gen_binding, neutral_binding):
    remaining(stop)
    need(
        re.fullmatch(r"[0-9a-f]{64}", gen_binding or "")
        and re.fullmatch(r"[0-9a-f]{64}", neutral_binding or ""),
        "EXACT_GEN_AND_NEUTRAL_BINDING_SHAS_REQUIRED",
    )
    reference = json.loads(bounded(opened / "inputs/session.private.json"))
    control = json.loads(bounded(opened / "inputs/control.private.json"))
    mirror = json.loads(bounded(opened / "mirror/private-mirror-handoff.json"))
    need(
        reference["schema"] == "R30-NEUTRAL-FIVE-ARCHIVE-REFERENCE-v1"
        and reference["source_sha"] == SOURCE
        and reference["cost_stop_utc"] == stop
        and reference["gen_binding_sha256"] == gen_binding
        and reference["neutral_binding_sha256"] == neutral_binding
        and control["binding_sha256"] == gen_binding
        and control["stop_utc"] == stop
        and mirror["schema"] == "R30-NEUTRAL-FIVE-MIRROR-v1",
        "EXACT_REFERENCE_AND_BINDINGS_REQUIRED",
    )
    compressed = base64.b64decode(mirror["archive_b64"], validate=True)
    need(
        len(compressed) == reference["archive_bytes"] <= CAP
        and sha(compressed) == reference["archive_sha256"],
        "ARCHIVE_SIZE_SHA_REQUIRED",
    )
    with gzip.GzipFile(fileobj=io.BytesIO(compressed)) as stream:
        raw = stream.read(CAP + 1)
    need(len(raw) <= CAP, "DECOMPRESSED_TAR_CAP")
    files = {}
    with tarfile.open(fileobj=io.BytesIO(raw), mode="r:") as archive:
        for member in archive:
            need(
                member.name in NAMES
                and member.name not in files
                and member.isfile()
                and not member.pax_headers
                and not member.sparse
                and 0 <= member.size <= CAP,
                "EXACT_UNIQUE_REGULAR_FIVE_MEMBERS_ONLY",
            )
            files[member.name] = archive.extractfile(member).read(CAP + 1)
    need(
        {name: {"bytes": len(value), "sha256": sha(value)} for name, value in files.items()}
        == reference["files"],
        "ALL_FIVE_MEMBER_HASHES_REQUIRED",
    )
    validate_five(files, stop, neutral_binding)
    need(files["ca.pem"] == bounded(opened / "inputs/ca.pem"), "SAME_ORIGINAL_CA_REQUIRED")
    remaining(stop)
    need(
        output.parent.resolve() == output.parent and not output.exists(),
        "NEW_OPERATOR_EXTRACTION_ONLY",
    )
    output.mkdir(mode=0o700)
    inputs = output / "inputs"
    inputs.mkdir(mode=0o700)
    for name, value in files.items():
        write(inputs / name, value)
    receipt = {
        "kind": "R30_OPERATOR_FIVE_EXTRACTED_NOT_AUTHORIZED",
        "gen_binding_sha256": gen_binding,
        "neutral_binding_sha256": neutral_binding,
        "files": reference["files"],
        "cost_stop_utc": stop,
    }
    write(output / "extraction.PUBLIC.json", canonical(receipt))
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("pack", "extract"))
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--cost-stop-utc", required=True)
    parser.add_argument("--gen-binding-sha256", required=True)
    parser.add_argument("--neutral-binding-sha256")
    args = parser.parse_args()
    os.umask(0o077)
    function = pack if args.mode == "pack" else extract
    parameters = [args.input_dir, args.output_dir, args.cost_stop_utc, args.gen_binding_sha256]
    if args.mode == "extract":
        parameters.append(args.neutral_binding_sha256)
    print(json.dumps(function(*parameters), sort_keys=True))


if __name__ == "__main__":
    main()
