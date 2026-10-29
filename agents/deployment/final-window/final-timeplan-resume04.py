"""Freeze a new run only after actual transport/readiness; no VM or grant operations."""
import argparse
import hashlib
import json
import math
import os
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path


def read(path, expected):
    raw = path.read_bytes()
    if path.is_symlink() or hashlib.sha256(raw).hexdigest() != expected:
        raise ValueError("ROOT_PINNED_ORIGINAL_REQUIRED")
    return json.loads(raw)


def utc(text):
    if not re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ", text or ""):
        raise ValueError("EXPLICIT_UTC_REQUIRED")
    return datetime.fromisoformat(text.replace("Z", "+00:00"))  # noqa: FURB162 -- APP Python3.10


def text(value):
    return value.strftime("%Y-%m-%dT%H:%M:%SZ")


def save(path, value):
    if not path.is_absolute() or path.parent.resolve() != path.parent:
        raise ValueError("NEW_CANONICAL_OUTPUT_REQUIRED")
    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "w") as stream:
        json.dump(value, stream, sort_keys=True, indent=2)
        stream.write("\n")


def freeze(args):
    source = read(args.source_profile, args.source_profile_sha256)
    loaded = read(args.import_receipt, args.import_receipt_sha256)
    now = datetime.now(timezone.utc).replace(microsecond=0)  # noqa: UP017 -- APP Python3.10
    boot = utc(args.actual_first_boot_utc)
    approval = read(args.cost_approval, args.cost_approval_sha256)
    outer = utc(approval["absolute_cost_cutoff_utc"])
    observed = utc(approval["resume_observed_utc"])
    remaining = approval["remaining_budget_CNY"]
    if (approval.get("root_approved") is not True
            or approval["historical_APP_first_boot_utc"] != args.actual_first_boot_utc
            or remaining != 40 or not boot <= observed <= now
            or not observed <= utc(approval["actual_APP_resume_boot_utc"]) <= now
            or not observed <= utc(approval["actual_LOAD_resume_boot_utc"]) <= now
            or outer <= now or (outer-observed).total_seconds()/3600*15.5765 > remaining-3):
        raise ValueError("FRESH_RESUME_ACTUAL_BOOTS_ROOT_REMAINING40_AND_THREE_YUAN_RESERVE_REQUIRED")
    if (not re.fullmatch(r"r30[a-z0-9]{5,12}", args.run_id) or args.run_id == "r30window01"
            or source.get("root_approved") is not True or source["source_sha"] != loaded["source_sha"]
            or loaded["identity"]["config_id"] != source["backend_config_id"]
            or loaded["source_manifest_sha256"] != source["source_manifest_sha256"]
            or loaded["bundle_manifest_sha256"] != source["backend_bundle_manifest_sha256"]
            or loaded.get("kind") != "final-backend-web-import-v1"
            or not boot <= now or now + timedelta(minutes=45) > outer):
        raise ValueError("NEW_APPROVED_LOADED_SOURCE_RUN_AND_OUTER_RESERVE_REQUIRED")
    value = {"kind": "final-immutable-timeplan-v1", "source_sha": source["source_sha"], "phase": args.phase,
        "run_id": args.run_id, "actual_first_boot_utc": args.actual_first_boot_utc,
        "absolute_cost_cutoff_utc": text(outer), "t0_utc": text(now), "stop_utc": text(now + timedelta(minutes=35)),
        "cost_stop_utc": text(now + timedelta(minutes=40)), "root_transport_ready_import_sha256": args.import_receipt_sha256,
        "source_profile_sha256": args.source_profile_sha256,
        "quote_root_reported_CNY_per_hour": {"APP": 12.436, "LOAD": 3.1405, "sum": 15.5765},
        "cost_approval_sha256": args.cost_approval_sha256,
        "cost_approval_resume_observed_utc": approval["resume_observed_utc"],
        "historical_expense_not_reused": True,
        "approved_remaining_CNY": remaining,
        "actual_APP_resume_boot_utc":approval["actual_APP_resume_boot_utc"],
        "actual_LOAD_resume_boot_utc":approval["actual_LOAD_resume_boot_utc"],
        "variance_reserve_CNY": 3,
        "actual_bill_guarantee": False, "cloud_or_sessions_or_grant_executed": False}
    if args.phase == "p":
        value.update(start_utc=text(now + timedelta(minutes=20)), end_utc=text(now + timedelta(minutes=33)),
            packet_cutoff_utc=text(now + timedelta(minutes=17, seconds=30)), measurement_seconds=780,
            minimum_actual_steady_seconds=660, packet_age_at_execute_max_seconds=300,
            workload_post_E_reserve_seconds=120, export_post_G_reserve_seconds=300)
    save(args.output, value)
    return value


def f_start(args):
    value = read(args.timeplan, args.timeplan_sha256)
    now = datetime.now(timezone.utc).replace(microsecond=0)  # noqa: UP017 -- APP Python3.10
    seconds = math.floor((utc(value["stop_utc"]) - now).total_seconds()) - 120
    if value["phase"] != "f" or seconds < 60 or now < utc(value["t0_utc"]):
        raise ValueError("F_TIMEPLAN_ACTUAL_REMAINING_TIME_REQUIRED")
    result = {"run_id": value["run_id"], "f_started_utc": text(now), "max_seconds": min(2400, 1500, seconds),
              "stop_utc": value["stop_utc"], "cost_stop_utc": value["cost_stop_utc"],
              "absolute_cost_cutoff_utc": value["absolute_cost_cutoff_utc"], "cleanup_reserve_seconds": 120,
              "timeplan_sha256": args.timeplan_sha256, "QA_started": False}
    save(args.output, result)
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("action", choices=("freeze", "f-start"))
    p.add_argument("--phase", choices=("f", "p"))
    for name in ("source-profile", "import-receipt", "timeplan", "output", "cost-approval"):
        p.add_argument("--" + name, type=Path)
    for name in ("source-profile-sha256", "import-receipt-sha256", "timeplan-sha256", "actual-first-boot-utc", "run-id", "cost-approval-sha256"):
        p.add_argument("--" + name)
    args = p.parse_args()
    os.umask(0o077)
    print(json.dumps(freeze(args) if args.action == "freeze" else f_start(args)))


if __name__ == "__main__":
    main()
