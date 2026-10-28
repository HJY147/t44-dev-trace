"""Strict PUBLIC document links. No cloud operations and no credentials in this module."""

import re
from datetime import timedelta
from pathlib import Path

from bridge_common import HANDOFF_SECONDS, decode_document, require, stamp

FREEZE = "33dd522d382bb166d331489e46166a8a59c1b985e065b4849acbf7674ad5309e"
EXECUTION = "e8ac37bb41c474681f2ea36598806cb7ba0605ee26b82cfdc4fe462c7a2d16ae"
CONTEXT_KEYS = {
    "tool_freeze_sha256",
    "native_runtime_identity",
    "source_sha",
    "phase",
    "resource_ids",
    "supervisor_nonce",
}


def positive_ids(values, empty=False):
    require(isinstance(values, list) and (empty or bool(values)), "EXPLICIT_ID_LIST_REQUIRED")
    require(
        all(type(v) is int and 1 <= v <= 4294967295 for v in values),
        "POSITIVE_STORAGE_IDS_REQUIRED",
    )
    require(len(set(values)) == len(values), "UNIQUE_IDS_REQUIRED")


def validate(authority, clock):
    require(authority["kind"] == "PUBLIC_SCOPE_AUTHORITY_V1", "AUTHORITY_KIND")
    docs = authority["documents"]
    require(
        set(docs)
        == {"grant", "launch", "supervisor", "binding", "neutral", "admission", "request"},
        "EXACT_DOCUMENT_SET",
    )
    g, launch, sup, b, neutral, r = (
        decode_document(docs[name])
        for name in ("grant", "launch", "supervisor", "binding", "neutral", "request")
    )
    n = neutral["sut_identity"]
    admission = decode_document(docs["admission"])
    require(
        admission["kind"] == "ROOT_SINGLE_FUNCTIONAL_EXECUTION_RESERVED"
        and admission["phase"] == "functional"
        and admission["root_grant_sha256"] == docs["grant"]["sha256"]
        and admission["tool_freeze_sha256"] == FREEZE
        and admission["tool_execution_build_sha256"] == EXECUTION
        and admission["no_automatic_retry"] is True,
        "ACTUAL_ADMISSION_GRANT_HASH_BINDING",
    )
    require(
        re.fullmatch(r"[0-9a-f]{40}", b["source_sha"])
        and re.fullmatch(r"[0-9a-f]{64}", b["source_archive_sha256"]),
        "FULL_SOURCE_IDENTIFIERS_REQUIRED",
    )
    require(
        g["admitted"] is True and g["phase"] == "functional" and g["no_automatic_retry"] is True,
        "ROOT_SINGLE_FUNCTIONAL_GRANT_REQUIRED",
    )
    require(
        g["allowed_faults"] == [] and g["fixture_handoff"] == "nonce-sealed-project-scope",
        "ONLY_FUNCTIONAL_SCOPE_ALLOWED",
    )
    require(
        g["tool_freeze_sha256"]
        == launch["tool_freeze_sha256"]
        == sup["tool_freeze_sha256"]
        == FREEZE,
        "FREEZE_MISMATCH",
    )
    require(
        g["tool_execution_build_sha256"] == launch["tool_execution_build_sha256"] == EXECUTION,
        "EXECUTION_BUILD_MISMATCH",
    )
    require(
        launch["kind"] == "DETACHED_SUPERVISOR_LAUNCH_NOT_VERDICT"
        and launch["phase"] == "functional"
        and launch["no_automatic_retry"] is True,
        "LAUNCH_MISMATCH",
    )
    require(
        launch["supervisor_pid"]
        == sup["supervisor_pid"]
        == authority["owner"]["supervisor_container_pid"],
        "SUPERVISOR_PID_BINDING",
    )
    require(
        b["phase"] == "f" and b["entrypoint"] == "t44.api:app" and b["profiling"] is False,
        "PRODUCTION_F_ONLY",
    )
    require(b["source_sha"] == n["source_sha"] == g["build"]["source_sha"], "SOURCE_MISMATCH")
    require(
        b["source_archive_sha256"]
        == n["source_archive_sha256"]
        == g["build"]["source_archive_sha256"],
        "SOURCE_ARCHIVE_MISMATCH",
    )
    require(
        n["image_digest"] == g["build"]["image_digest"]
        and n["image_digest"] in {b["image_ids"]["backend"], b["config_ids"]["backend"]},
        "IMAGE_MISMATCH",
    )
    require(
        n["runtime_identity"] == g["build"]["runtime_identity"]
        and n["lifecycle_status"] == "running",
        "RUNTIME_IDENTITY_MISMATCH",
    )
    require(
        n["prepared_binding_sha256"] == docs["binding"]["sha256"]
        and n["schema_name"] == b["database"]
        and n["project_name"] == b["project"],
        "DATABASE_NAMESPACE_BINDING",
    )
    require(
        n["phase_dir"] == g["scope_provider_fixed_phase_dir"] == authority["app_phase_dir"],
        "PHASE_DIRECTORY_MISMATCH",
    )
    require(Path(authority["app_phase_dir"]).is_absolute(), "EXPLICIT_PHASE_PATH")
    require(
        n["ca_sha256"] == b["tls"]["ca_sha256"]
        and n["base_url"] == g["base_url"]
        and n["pinned_ip"] == g["pinned_ip"],
        "TLS_TARGET_MISMATCH",
    )
    require(
        n["runtime_receipt_sha256"] == g["runtime_receipt_sha256"]
        and n["runtime_receipt_sha256"] != n["prepared_receipt_sha256"],
        "ACTUAL_RUNTIME_RECEIPT_REQUIRED",
    )
    require(
        len(set(n["isolated_resource_ids"])) == len(n["isolated_resource_ids"])
        and set(n["isolated_resource_ids"]) == set(g["isolated_resource_ids"]),
        "RESOURCE_SET_MISMATCH",
    )
    require(
        r["kind"] == "SERVICE_SCOPE_REQUEST" and r["scope"] == ["escalation:write"],
        "SCOPE_REQUEST_ONLY_NO_REVOCATION_ACK",
    )
    positive_ids(r["project_ids"])
    positive_ids(r["iteration_ids"], empty=True)
    require(
        isinstance(r["nonce"], str)
        and 1 <= len(r["nonce"]) <= 128
        and Path(r["nonce"]).name == r["nonce"]
        and r["nonce"] not in {".", ".."},
        "SAFE_NONCE_COMPONENT",
    )
    c = r["context"]
    require(set(c) == CONTEXT_KEYS, "EXACT_FROZEN_CONTEXT_KEYS")
    require(
        c["tool_freeze_sha256"] == FREEZE
        and c["source_sha"] == b["source_sha"]
        and c["phase"] == "functional",
        "REQUEST_BUILD_CONTEXT",
    )
    require(
        c["native_runtime_identity"] == n["runtime_identity"]
        and set(c["resource_ids"]) == set(n["isolated_resource_ids"])
        and len(c["resource_ids"]) == len(n["isolated_resource_ids"]),
        "REQUEST_RESOURCE_CONTEXT",
    )
    require(
        c["supervisor_nonce"] == sup["nonce"] == authority["supervisor_nonce"],
        "REQUEST_SUPERVISOR_NONCE",
    )
    require(
        r["public_key_pem"].startswith("-----BEGIN PUBLIC KEY-----\n"), "PUBLIC_SCOPE_KEY_REQUIRED"
    )
    key_sha = __import__("hashlib").sha256(r["public_key_pem"].encode()).hexdigest()
    require(
        len(authority["forbidden_key_shas"]) >= 2
        and len(set(authority["forbidden_key_shas"])) == len(authority["forbidden_key_shas"])
        and all(re.fullmatch(r"[0-9a-f]{64}", s) for s in authority["forbidden_key_shas"]),
        "INPUT_AND_EVIDENCE_KEY_DOMAINS_REQUIRED",
    )
    require(key_sha not in authority["forbidden_key_shas"], "KEY_DOMAIN_REUSE")
    request_at = stamp(r["requested_utc"])
    require(stamp(launch["started_utc"]) <= request_at <= clock.now(), "REQUEST_TIME_BINDING")
    end = min(
        request_at + timedelta(seconds=HANDOFF_SECONDS),
        *(
            stamp(x)
            for x in (g["expires_at"], launch["expires_at"], sup["expires_at"], b["stop_utc"])
        ),
    )
    require(end > clock.now(), "ORIGINAL_HANDOFF_OR_GRANT_EXPIRED")
    require(stamp(authority["callback_deadline_utc"]) == end, "CALLBACK_DEADLINE_NOT_EXTENDABLE")
    if "load_observation" in authority:
        observed = stamp(authority["load_observation"]["utc"])
        require(
            stamp(authority["app_lease_end_utc"])
            <= min(observed + timedelta(seconds=80), end - timedelta(seconds=10)),
            "APP_LEASE_NOT_EXTENDABLE",
        )
    return {
        "grant": g,
        "launch": launch,
        "supervisor": sup,
        "binding": b,
        "neutral": neutral,
        "request": r,
        "end": end,
    }
