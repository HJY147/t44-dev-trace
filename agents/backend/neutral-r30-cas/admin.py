"""Future APP admin entry, called only while root holds the new budget admission lock."""

import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

from admin_seed import seed_in_admitted_context
from guard import check_intent, check_plan, need, read_json, timestamp, validate_loaded_receipt
from http_primitives import save, stamp


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("seed", "counts", "service"))
    for key in ("plan", "intent", "budget-proof", "output", "import-receipt", "binding"):
        parser.add_argument("--" + key, type=Path, required=True)
    parser.add_argument("--root-budget-admitted", action="store_true")
    args = parser.parse_args()
    need(args.root_budget_admitted, "ROOT_MUST_HOLD_NEW_BUDGET_ADMISSION_LOCK")
    plan, intent, now = read_json(args.plan), read_json(args.intent), datetime.now(UTC)
    need(str(args.binding) == plan["gen_binding"]["path"], "SAME_MOUNTED_BINDING_PATH_REQUIRED")
    check_plan(plan, now, require_fixture_ready=False)
    validate_loaded_receipt(plan, args.import_receipt.read_bytes())
    need(
        hashlib.sha256(args.budget_proof.read_bytes()).hexdigest()
        == plan["budget"]["actual_admission_receipt_sha256"],
        "ACTUAL_NEW_BUDGET_PROOF_REQUIRED",
    )
    need(
        read_json(args.budget_proof)["kind"] == "actual-owned-mysql-budget-v4",
        "ORIGINAL_GEN_PROBE_SCHEMA_REQUIRED_NOT_LIVE_READMISSION",
    )
    need(not args.output.exists(), "EXCLUSIVE_NEW_ADMIN_OUTPUT_REQUIRED")
    from t44.persistence import SqlAlchemyUnitOfWorkFactory, create_mysql_engine
    from t44.services.common import wire
    from t44.settings import Settings

    settings = Settings.from_env()
    mysql = settings.mysql_settings()
    identity = {
        "database": mysql.database,
        "host": mysql.host,
        "port": mysql.port,
        "username": mysql.username,
    }
    target = plan["target"]
    need(
        identity
        == {
            "database": target["database"],
            "host": target["mysql_host"],
            "port": target["mysql_port"],
            "username": target["mysql_user"],
        },
        "EXACT_PROJECT_DATABASE_REQUIRED",
    )
    factory = SqlAlchemyUnitOfWorkFactory(create_mysql_engine(mysql))
    args.output.mkdir(mode=0o700)
    if args.mode == "seed":
        result = seed_in_admitted_context(plan, intent, factory, identity, now=now)
        save(args.output / "seed-result.json", wire(result))
    elif args.mode == "counts":
        need(
            intent["database"] == target["database"]
            and intent["namespace"] == plan["namespace"]
            and intent["run_id"] == plan["run_id"]
            and intent["binding_sha256"] == target["binding_sha256"],
            "EXACT_READONLY_SCOPE_REQUIRED",
        )
        with factory() as uow:
            g = uow.gateway
            raw = {
                table: g.count(table, {})
                for table in ("projects", "tasks", "task_dependencies", "reviews", "decisions")
            }
            snapshot = wire(g.rows("tasks", {}, order_by=("id",)))
            projects = [row["id"] for row in g.rows("projects", {}, order_by=("id",))]
        actual = {
            "projects": raw["projects"],
            "tasks": raw["tasks"],
            "dependencies": raw["task_dependencies"],
            "reviews_and_decisions": raw["reviews"] + raw["decisions"],
        }
        result = {
            "kind": "ACTUAL_NEUTRAL_COUNTS_NOT_ACCEPTANCE",
            "captured_at": stamp(datetime.now(UTC)),
            "run_id": plan["run_id"],
            "namespace": plan["namespace"],
            "database": target["database"],
            "binding_sha256": target["binding_sha256"],
            "actual_fixture_counts": actual,
            "raw_counts": raw,
            "project_ids": projects,
            "actual_fixture_sha256": hashlib.sha256(
                json.dumps(snapshot, sort_keys=True, separators=(",", ":")).encode()
            ).hexdigest(),
        }
        save(args.output / "counts.json", result)
    else:
        check_intent(plan, intent, now)
        need(
            intent["operation"] == "service-token"
            and plan["service_name"].startswith(plan["namespace"]),
            "EXACT_NEW_SERVICE_NAME_REQUIRED",
        )
        token_file = args.output / "original-service.json"
        command = [
            sys.executable,
            "-m",
            "t44.cli",
            "service-token",
            "--name",
            plan["service_name"],
            "--token-file",
            str(token_file),
        ]
        for pid in plan["authorized_project_ids"]:
            command.extend(("--project-id", str(pid)))
        # No -I: the official image deliberately exposes t44 through PYTHONPATH.
        process = subprocess.run(command, capture_output=True, timeout=40, check=False)
        (args.output / "cli.stdout.private").write_bytes(process.stdout)
        (args.output / "cli.stderr.private").write_bytes(process.stderr)
        need(process.returncode == 0, "ORIGINAL_SERVICE_CLI_FAILED_PREFIX_PRESERVED")
        original = read_json(token_file)
        with factory() as uow:
            row = uow.gateway.get("auth_sessions", original["session_id"])
        need(
            row["token_hash"] == hashlib.sha256(original["access_token"].encode()).digest()
            and row["revoked_at"] is None
            and sorted(row["project_ids"]) == sorted(plan["authorized_project_ids"])
            and row["scopes"] == ["escalation:write"],
            "ACTUAL_SERVICE_SESSION_READBACK_REQUIRED",
        )
        need(
            timestamp(wire(row["expires_at"]))
            > timestamp(plan["window"]["end_utc"])
            + timedelta(seconds=plan["session_expiry_reserve_seconds"]),
            "ACTUAL_SERVICE_TTL_INSUFFICIENT",
        )
        session = {
            "token": original["access_token"],
            "user_id": row["service_account_id"],
            "expires_at": wire(row["expires_at"]),
            "project_ids": row["project_ids"],
            "scopes": row["scopes"],
        }
        attestation = {key: value for key, value in session.items() if key != "token"}
        attestation.update(
            issued_at=wire(row["created_at"]),
            token_sha256=hashlib.sha256(original["access_token"].encode()).hexdigest(),
        )
        save(args.output / "service.json", {"session": session, "attestation": attestation})
    print(
        json.dumps(
            {
                "kind": "ROOT_ADMITTED_ADMIN_STEP_FINISHED_NOT_MEASUREMENT",
                "mode": args.mode,
                "output": str(args.output),
                "credentials_disclosed": False,
            }
        )
    )


if __name__ == "__main__":
    os.umask(0o077)
    main()
