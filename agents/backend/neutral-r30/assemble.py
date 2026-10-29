"""Create one fresh private 0b neutral packet; never authorize, encrypt or run the benchmark."""

import argparse
import hashlib
import json
import os
import secrets
from datetime import UTC, datetime, timedelta
from pathlib import Path

from guard import (
    BUNDLE_MANIFEST,
    SOURCE,
    SOURCE_MANIFEST,
    check_evidence,
    need,
    read_json,
    timestamp,
)
from http_primitives import save, stamp


def canonical(value):
    return (
        json.dumps(
            value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode()
        + b"\n"
    )


def assemble(
    plan,
    evidence,
    sessions,
    counts,
    ca_raw,
    source_raw,
    bundle_raw,
    receipt_raw,
    output,
    *,
    now=None,
):
    now = now or datetime.now(UTC)
    need(not output.exists(), "NEW_PACKET_DIRECTORY_REQUIRED_NO_RETIME")
    check_evidence(plan, evidence, now)
    need(
        hashlib.sha256(source_raw).hexdigest() == SOURCE_MANIFEST
        and hashlib.sha256(bundle_raw).hexdigest() == BUNDLE_MANIFEST,
        "EXACT_RAW_MANIFEST_BYTES_REQUIRED",
    )
    need(
        hashlib.sha256(ca_raw).hexdigest() == plan["target"]["ca_sha256"],
        "ACTUAL_CA_BYTES_REQUIRED",
    )
    receipt = json.loads(receipt_raw)
    proof = plan["source"]
    receipt_sha = hashlib.sha256(receipt_raw).hexdigest()
    need(
        receipt_sha == proof["actual_loaded_receipt_sha256"],
        "ORIGINAL_ACTUAL_IMPORT_BYTES_REQUIRED",
    )
    need(
        receipt["kind"] == "r30-backend-import-receipt-v1"
        and receipt["source_sha"] == SOURCE
        and receipt["bundle_manifest_sha256"] == BUNDLE_MANIFEST
        and receipt["source_manifest_sha256"] == SOURCE_MANIFEST
        and type(receipt["full_runtime_files"]) is int
        and receipt["full_runtime_files"] == 60
        and bool(receipt["identity"])
        and bool(receipt["package_resolution"])
        and plan["images"]["backend"] in json.dumps(receipt["identity"])
        and receipt["business_services_started"] is False
        and receipt["volumes_modified"] is False,
        "ACTUAL_APP_IMPORT_RECEIPT_REQUIRED_NOT_CI_OR_TEMPLATE",
    )
    need(
        proof["actual_loaded_full_chain_reviewed_by_root"] is True,
        "ROOT_MUST_REVIEW_SAME_ACTUAL_IMPORT_CHAIN",
    )
    need(
        set(sessions) == set(evidence["session_attestations"]),
        "EXACT_ORIGINAL_FOUR_SESSIONS_REQUIRED",
    )
    for role, session in sessions.items():
        actual = evidence["session_attestations"][role]
        need(
            hashlib.sha256(session["token"].encode()).hexdigest() == actual["token_sha256"]
            and all(
                session[key] == actual[key]
                for key in ("user_id", "expires_at", "project_ids", "scopes")
            ),
            "ORIGINAL_SESSION_BYTES_AND_METADATA_UNCHANGED",
        )
    need(
        counts["actual_fixture_counts"] == evidence["actual_fixture_counts"]
        and counts["actual_fixture_sha256"] == evidence["actual_fixture_sha256"],
        "SAME_ACTUAL_COUNT_ATTESTATION_REQUIRED",
    )
    need(
        now < timestamp(plan["window"]["start_utc"]) <= now + timedelta(seconds=600),
        "PACKET_START_WITHIN_600_SECONDS_REQUIRED",
    )
    template = read_json(Path(__file__).with_name("NEUTRAL_0B_V24.template.json"))
    packet = {
        **template,
        "run_id": plan["run_id"],
        "packet_nonce": secrets.token_hex(32),
        "created_at": stamp(now),
        "window": {
            "start_utc": plan["window"]["start_utc"],
            "end_utc": plan["window"]["end_utc"],
            "cost_stop_utc": plan["lifecycle"]["cost_stop_utc"],
        },
        "environment": {
            "origin": plan["target"]["origin"],
            "connect_ip": plan["target"]["connect_ip"],
            "ca_sha256": plan["target"]["ca_sha256"],
        },
        "sessions": sessions,
        "inventory": evidence["inventory"],
        "counts": {
            key: counts["raw_counts"][key] for key in ("projects", "tasks", "reviews", "decisions")
        },
        "fixture_sha256": evidence["actual_fixture_sha256"],
        "additional_neutral_snapshots": evidence,
        "loaded_receipt_sha256": receipt_sha,
        "loaded_receipt_reference": {
            "original_path": proof["actual_loaded_receipt_path"],
            "observed_at": proof["actual_loaded_observed_at"],
            "sha256": receipt_sha,
        },
    }
    packet["counts"]["dependencies"] = counts["raw_counts"]["task_dependencies"]
    packet.pop("binding_sha256", None)
    packet["binding_sha256"] = hashlib.sha256(canonical(packet)).hexdigest()
    output.mkdir(mode=0o700)
    inputs = output / "inputs"
    inputs.mkdir(mode=0o700)
    for name, raw in (
        ("ca.pem", ca_raw),
        ("source-manifest.json", source_raw),
        ("backend-bundle-manifest.json", bundle_raw),
        ("backend-import-receipt.json", receipt_raw),
    ):
        descriptor = os.open(inputs / name, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(raw)
    save(inputs / "session.private.json", packet)
    save(
        output / "complete.PUBLIC.json",
        {
            "kind": "FRESH_NEUTRAL_PACKET_NOT_AUTHORIZATION",
            "run_id": packet["run_id"],
            "created_at": packet["created_at"],
            "counts": packet["counts"],
            "binding_sha256": packet["binding_sha256"],
            "grant_allow": False,
            "actual_sessions_extended": False,
        },
    )
    return packet


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for key in (
        "plan",
        "evidence",
        "sessions",
        "counts",
        "ca",
        "source-manifest",
        "bundle-manifest",
        "import-receipt",
        "output",
    ):
        parser.add_argument("--" + key, type=Path, required=True)
    parser.add_argument("--root-admit-new-packet", action="store_true")
    args = parser.parse_args()
    need(args.root_admit_new_packet, "EXPLICIT_ROOT_NEW_PACKET_PREPARATION_REQUIRED")
    os.umask(0o077)
    packet = assemble(
        read_json(args.plan),
        read_json(args.evidence),
        read_json(args.sessions),
        read_json(args.counts),
        args.ca.read_bytes(),
        args.source_manifest.read_bytes(),
        args.bundle_manifest.read_bytes(),
        args.import_receipt.read_bytes(),
        args.output,
    )
    print(
        json.dumps(
            {
                "status": "NEW_PACKET_WRITTEN_NOT_A_GRANT",
                "created_at": packet["created_at"],
                "grant_allow": False,
            }
        )
    )


if __name__ == "__main__":
    main()
