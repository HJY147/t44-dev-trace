"""PUBLIC two-stage root grant; stdlib only, no import-time IO or networking."""

import base64
import hashlib
import json
import re
from datetime import datetime, timezone

SOURCE = "f7cdb5fa3b19f84d8ab0d0b042bf51a5b8484e8f"
ANCHOR = "2026-10-28T04:00:00Z"
STOP = "2026-10-28T20:00:00Z"
COHORTS = [["baseline1", 1, 20, 0], ["warmup40", 40, 5, 1], ["measure400", 400, 5, 41]]
ROLES = {"mysql", "rabbitmq", "api", "consumer", "web", "tls-gateway"}
UTC = timezone.utc  # noqa: UP017 -- host3.10.


def require(value, code):
    if not value:
        raise ValueError(code)


def stamp(value):
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    require(parsed.tzinfo is not None and parsed.utcoffset().total_seconds() == 0, "UTC_REQUIRED")
    return parsed


def check_control(control, mode, now):
    raw = base64.b64decode(control["root_grant_b64"], validate=True)
    require(
        hashlib.sha256(raw).hexdigest() == control["root_grant_sha256"], "ROOT_GRANT_SHA_CHANGED"
    )
    grant = json.loads(raw)
    require(mode in {"prep", "pressure"}, "EXPLICIT_GRANT_MODE")
    require(grant["kind"] == "ROOT_P_" + mode.upper() + "_GRANT_V4", "WRONG_ROOT_GRANT_STAGE")
    require(
        grant["admitted"] is True and grant["no_automatic_retry"] is True, "ROOT_ADMISSION_REQUIRED"
    )
    require(grant["HTTP_authorized"] is (mode == "pressure"), "PREP_IS_NOT_HTTP_AUTHORIZATION")
    for key in (
        "source_sha",
        "run_id",
        "binding_sha256",
        "namespace",
        "database",
        "api_workers",
        "backend_image_id",
        "source_proof_sha256",
        "source_file_count",
        "seed",
        "anchor_at",
        "stop_utc",
    ):
        require(grant[key] == control[key], "ROOT_GRANT_EXACT_IDENTITY_" + key.upper())
    require(
        control["source_sha"] == SOURCE and control["source_file_count"] == 53, "EXACT_F7_SOURCE53"
    )
    require(control["seed"] == 44 and control["anchor_at"] == ANCHOR, "EXACT_SEED_ANCHOR")
    require(stamp(control["stop_utc"]) == stamp(STOP), "EXACT_20Z_WINDOW")
    require(
        stamp(grant["issued_at"]) <= now < stamp(grant["expires_at"]) == stamp(STOP),
        "FINITE_ROOT_GRANT",
    )
    require(re.fullmatch(r"[0-9a-f]{48,64}", grant["session_nonce"]), "NEW_EXPLICIT_SESSION_NONCE")
    require(
        grant["session_ttl_seconds"] == 600 and grant["cohorts"] == COHORTS,
        "ORIGINAL_SHORT_MATRIX_REQUIRED",
    )
    require(grant["formal_performance_authorized"] is False, "SHORT_DIAGNOSTIC_ONLY")
    roles = grant["roles"]
    required = ROLES if mode == "pressure" else {"mysql", "rabbitmq"}
    require(required <= set(roles), "EXPLICIT_ACTUAL_ROLE_METADATA_REQUIRED")
    for name in required:
        row = roles[name]
        require(
            set(row) == {"container_id", "image_id", "running", "restart_count"},
            "LIMITED_PUBLIC_ROLE_FIELDS",
        )
        require(
            re.fullmatch(r"[0-9a-f]{64}", row["container_id"])
            and re.fullmatch(r"sha256:[0-9a-f]{64}", row["image_id"])
            and row["running"] is True
            and row["restart_count"] == 0,
            "ACTUAL_RUNNING_ROLE_REQUIRED",
        )
    if mode == "pressure":
        require(
            set(roles) == ROLES | {"scheduler"} and roles["scheduler"] == {"absent": True},
            "DEVELOPER_SIX_ROLES_SCHEDULER_ABSENT",
        )
    return grant


def attach(control, raw, wanted, mode, now):
    result = dict(control)
    result["root_grant_b64"] = base64.b64encode(raw).decode()
    result["root_grant_sha256"] = wanted
    check_control(result, mode, now)
    return result
