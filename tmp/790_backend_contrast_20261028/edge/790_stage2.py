"""S2: source-free stdlib edge-only TLS client. No T44, SQL, DB settings or credentials."""

import argparse
import hashlib
import importlib
import json
import os
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

http = importlib.import_module("790_http")


def validate(candidate, accounts, wanted_sha, actual_sha):
    http.require_context(candidate)
    if wanted_sha != actual_sha or candidate.get("kind") != "contrast790-stage1-candidates":
        raise http.InvalidDiagnostic("Explicit S1 candidate hash/kind mismatch")
    if candidate.get("product") != http.PRODUCT or candidate.get("database") != http.DATABASE:
        raise http.InvalidDiagnostic("Wrong S1 source/schema")
    if datetime.fromisoformat(candidate["created_at"]) + timedelta(minutes=15) <= datetime.now(UTC):
        raise http.InvalidDiagnostic("S1 candidate expired")
    if datetime.fromisoformat(candidate["service"]["expires_at"]) <= datetime.now(UTC):
        raise http.InvalidDiagnostic("Actual service session expired")
    if (
        candidate["service"].get("project_ids") != candidate["project_ids"]
        or candidate["service"].get("scopes") != ["escalation:write"]
        or candidate["service"].get("actor_kind") != 2
    ):
        raise http.InvalidDiagnostic("Actual scoped service binding differs")
    if set(accounts) != {"manager", "developer", "reviewer"} or any(
        set(value) != {"username", "password", "user_id"} for value in accounts.values()
    ):
        raise http.InvalidDiagnostic("Explicit three-role private accounts required")
    if {
        role: {key: value[key] for key in ("username", "user_id")}
        for role, value in accounts.items()
    } != candidate["identities"]:
        raise http.InvalidDiagnostic("Private accounts differ from S1 actual identities")
    ids = [slot[key]["id"] for slot in candidate["slots"] for key in ("transition", "escalation")]
    if (
        not 1 <= len(candidate["slots"]) <= 500
        or len(ids) != len(set(ids))
        or len(set(candidate["project_ids"])) != 40
    ):
        raise http.InvalidDiagnostic("S1 slots/scope must be actual and disjoint")
    for slot in candidate["slots"]:
        if (
            slot["transition"]["state"] != 2
            or slot["transition"]["owner_id"] != accounts["developer"]["user_id"]
        ):
            raise http.InvalidDiagnostic("S1 transition state/owner invalid")
        if any(
            slot[key]["project_id"] not in candidate["project_ids"]
            for key in ("transition", "escalation")
        ):
            raise http.InvalidDiagnostic("Candidate outside actual service scope")


def main(argv=None):
    parser = argparse.ArgumentParser()
    for name in (
        "accounts",
        "candidate",
        "candidate-sha256",
        "output-dir",
        "ca",
        "ca-sha256",
        "url",
    ):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--control", required=True)
    parser.add_argument("--control-sha256", required=True)
    args = parser.parse_args(argv)
    http.configure(args.control, args.control_sha256)
    http.target(args.url)
    candidate = http.private_json(args.candidate)
    accounts = http.private_json(args.accounts)
    validate(
        candidate,
        accounts,
        args.candidate_sha256,
        hashlib.sha256(Path(args.candidate).read_bytes()).hexdigest(),
    )
    directory = Path(args.output_dir)
    if not directory.is_absolute():
        raise http.InvalidDiagnostic("New absolute output directory required")
    directory.mkdir(mode=0o700)
    status_fd, packet_fd = http.reserve(directory / "status.public.jsonl"), None
    client, phase, writes_started = None, "public_ca_verification", False
    try:
        if (
            args.ca_sha256 != http.CONTROL["ca_sha256"]
            or hashlib.sha256(Path(args.ca).read_bytes()).hexdigest() != args.ca_sha256
        ):
            raise http.InvalidDiagnostic("Original public CA hash mismatch")
        packet_fd = http.reserve(directory / "session.private.json")
        phase = "first_tls_client_configuration"
        http.write_fd(
            status_fd,
            {"kind": phase, "utc": http.utc(), "no_http_request_sent_yet": True},
        )
        client = http.Client(args.url, args.ca)
        http.write_fd(status_fd, {"kind": "tls_client_configuration_ready", "utc": http.utc()})
        phase, sessions = "three_real_tls_logins", {}
        for role in ("manager", "developer", "reviewer"):
            value = accounts[role]
            result = client.call(
                "/api/v1/auth/login",
                body={"username": value["username"], "password": value["password"]},
                sample=False,
            )
            if result["user"]["id"] != value["user_id"]:
                raise http.InvalidDiagnostic("Authenticated identity differs")
            sessions[role] = {key: result[key] for key in ("access_token", "expires_at")}
            sessions[role]["user_id"] = result["user"]["id"]
        sessions["service"] = {
            key: candidate["service"][key] for key in ("access_token", "expires_at")
        }
        del accounts
        slots = []
        for slot in candidate["slots"]:
            phase = "real_http_snapshot_and_contract"
            actual = {}
            for key, role in (("transition", "developer"), ("escalation", "manager")):
                observed = client.call(
                    http.task_path(slot[key]),
                    sessions[role]["access_token"],
                    sample=False,
                )
                if observed != slot[key]:
                    raise http.InvalidDiagnostic(
                        "Real HTTP task snapshot differs from S1; preserve and review"
                    )
                actual[key] = http.slim(observed)
            transition, escalation = actual["transition"], actual["escalation"]
            result = client.call(
                f"/api/v1/projects/{transition['project_id']}/contract-validations",
                sessions["developer"]["access_token"],
                {
                    "category": 2,
                    "task_id": transition["id"],
                    "payload": http.block_body(transition),
                },
                sample=False,
            )
            if result.get("valid") is not True:
                raise http.InvalidDiagnostic("Real contract input rejected")
            scan_run_id = str(uuid4())
            body = {
                "expected_version": escalation["version"],
                "schedule_version": escalation["schedule_version"],
                "rule_version": candidate["rule_version"],
                "scan_run_id": scan_run_id,
            }
            path = (
                "/api/v1/internal"
                + http.task_path(escalation).removeprefix("/api/v1")
                + "/escalations"
            )
            phase, writes_started = "real_escalation_create", True
            created = client.call(
                path,
                sessions["service"]["access_token"],
                body,
                str(uuid4()),
                sample=False,
            )
            if (
                created.get("created") is not True
                or created["task_version"] != escalation["version"] + 1
            ):
                raise http.InvalidDiagnostic("Actual fresh event creation not observed")
            escalation["version"] = body["expected_version"] = created["task_version"]
            phase = "real_existing_event_dedup"
            duplicate = client.call(
                path,
                sessions["service"]["access_token"],
                body,
                str(uuid4()),
                sample=False,
            )
            if (
                duplicate.get("created") is not False
                or duplicate["task_version"] != escalation["version"]
                or duplicate["event"]["id"] != created["event"]["id"]
            ):
                raise http.InvalidDiagnostic("Actual existing-event dedup not observed")
            slots.append(
                {
                    "transition": transition,
                    "transition_role": "developer",
                    "escalation": escalation,
                    "rule_version": candidate["rule_version"],
                    "scan_run_id": scan_run_id,
                    "event_id": created["event"]["id"],
                }
            )
            if len(slots) % 20 == 0:
                http.write_fd(
                    status_fd,
                    {
                        "kind": "stage2_progress",
                        "utc": http.utc(),
                        "prepared_slots": len(slots),
                    },
                )
        packet = {
            "kind": http.KIND,
            "product": http.PRODUCT,
            "database": http.DATABASE,
            **http.context_fields(),
            "url": args.url,
            "created_at": http.utc(),
            "sessions": sessions,
            "slots": slots,
            "resumable": True,
            "stage1_candidate_sha256": args.candidate_sha256,
        }
        http.check_packet(packet)
        phase = "write_driver_session"
        http.write_fd(packet_fd, packet)
        os.fsync(packet_fd)
        http.write_fd(
            status_fd,
            {
                "kind": "stage2-complete-not-acceptance",
                "utc": http.utc(),
                "slots": len(slots),
                "three_real_http_logins": True,
                "real_creation_and_dedup_pairs": len(slots),
                "diagnostic_valid": True,
                "no_product_or_sql_import": True,
            },
        )
        os.fsync(status_fd)
        return 0
    except BaseException as error:
        http.write_fd(
            status_fd,
            {
                "diagnostic_valid": False,
                "utc": http.utc(),
                "phase": phase,
                "failure": type(error).__name__,
                "errno": getattr(error, "errno", None),
                "partial_event_commits_may_exist": writes_started,
                "resumable": False,
            },
        )
        raise
    finally:
        if client is not None:
            client.close()
        os.close(status_fd)
        if packet_fd is not None:
            os.close(packet_fd)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as error:  # noqa: BLE001 - private failure details must not be printed
        print(json.dumps({"stage2_failed": type(error).__name__}), file=sys.stderr)
        sys.exit(1)
