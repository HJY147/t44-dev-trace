"""Future root-admitted real API preparation, distinct from any benchmark cohort."""

import argparse
import concurrent.futures
import hashlib
import os
import time
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

from guard import check_intent, check_plan, need, read_json, timestamp, validate_loaded_receipt
from http_primitives import Client, all_pages, choose_escalations, save, stamp


def prepare(
    plan,
    accounts,
    service,
    ca,
    output,
    *,
    clock=lambda: datetime.now(UTC),
    client_type=Client,
    import_receipt_raw=None,
):
    now = clock()
    check_plan(plan, now, require_fixture_ready=False)
    validate_loaded_receipt(plan, import_receipt_raw)
    need(plan["authorized_count_delta"]["tasks"] == 400, "EXPLICIT_400_API_TASK_DELTA_REQUIRED")
    need(not output.exists(), "EXCLUSIVE_NEW_PREPARATION_OUTPUT_REQUIRED")
    need(
        hashlib.sha256(ca.read_bytes()).hexdigest() == plan["target"]["ca_sha256"],
        "ACTUAL_CA_PIN_REQUIRED",
    )
    existing, attestation = service["session"], service["attestation"]
    need(
        hashlib.sha256(existing["token"].encode()).hexdigest() == attestation["token_sha256"]
        and existing["expires_at"] == attestation["expires_at"]
        and timestamp(existing["expires_at"])
        > timestamp(plan["window"]["end_utc"])
        + timedelta(seconds=plan["session_expiry_reserve_seconds"])
        and timestamp(plan["readiness"]["all_ready_at"])
        <= timestamp(attestation["issued_at"])
        <= now
        and sorted(existing["project_ids"]) == sorted(plan["authorized_project_ids"])
        and existing["scopes"] == ["escalation:write"],
        "ACTUAL_FRESH_SERVICE_MUST_PRECEDE_ANY_HUMAN_LOGIN",
    )
    output.mkdir(mode=0o700)
    records = output / "requests"
    records.mkdir(mode=0o700)
    prefix = output / "session-prefix"
    prefix.mkdir(mode=0o700)
    deadline = time.monotonic() + min(
        300, (timestamp(plan["window"]["start_utc"]) - now).total_seconds() - 30
    )
    need(deadline > time.monotonic(), "FINITE_PREPARATION_BEFORE_UNCHANGED_WINDOW_REQUIRED")

    def intent(operation, projects):
        value = {
            "run_id": plan["run_id"],
            "namespace": plan["namespace"],
            "database": plan["target"]["database"],
            "binding_sha256": plan["target"]["binding_sha256"],
            "operation": operation,
            "project_ids": projects,
            "purpose": "material_preparation",
        }
        check_intent(plan, value, clock())

    origin = plan["target"]["origin"]
    api = client_type(origin, ca, records, deadline)
    sessions, issued = {"service": service["session"]}, {"service": service["attestation"]}
    try:
        for role in ("manager", "developer", "reviewer"):
            intent("login", [])
            before = clock()
            response = api.request(
                "/auth/login",
                body={
                    "username": accounts[role]["username"],
                    "password": accounts[role]["password"],
                },
            )
            observed = clock()
            metadata = getattr(api, "last_meta", None)
            save(
                prefix / (role + ".json"),
                {
                    "original_login_data": response,
                    "response_meta": metadata,
                    "login_request_started_at": stamp(before),
                    "response_observed_at": stamp(observed),
                },
            )
            need(
                isinstance(metadata, dict) and "server_time" in metadata,
                "ORIGINAL_LOGIN_RESPONSE_META_REQUIRED_PREFIX_PRESERVED",
            )
            need(
                response["user"]["id"] == accounts[role]["user_id"], "ACTUAL_ROLE_USER_ID_REQUIRED"
            )
            session = {
                "token": response["access_token"],
                "user_id": response["user"]["id"],
                "expires_at": response["expires_at"],
                "project_ids": [],
                "scopes": [],
            }
            sessions[role] = session
            issued[role] = {
                "login_request_started_at": stamp(before),
                "response_observed_at": stamp(observed),
                "response_meta": metadata,
                "expires_at": response["expires_at"],
                "token_sha256": hashlib.sha256(response["access_token"].encode()).hexdigest(),
                "user_id": session["user_id"],
                "project_ids": [],
                "scopes": [],
            }
        projects = all_pages(api, "/projects", sessions["manager"]["token"])
        ids = sorted(project["id"] for project in projects)
        need(
            len(ids) == 40 and ids == sorted(plan["authorized_project_ids"]),
            "EXACT_ACTUAL_PROJECT_SCOPE_REQUIRED",
        )
        need(
            sorted(sessions["service"]["project_ids"]) == ids,
            "EXACT_SERVICE_PROJECT_SCOPE_REQUIRED",
        )
        for role in ("manager", "developer", "reviewer"):
            sessions[role]["project_ids"] = ids
            issued[role]["project_ids"] = ids
        expiry_minimum = timestamp(plan["window"]["end_utc"]) + timedelta(
            seconds=plan["session_expiry_reserve_seconds"]
        )
        need(
            all(timestamp(value["expires_at"]) > expiry_minimum for value in sessions.values()),
            "ACTUAL_SESSION_LIFETIME_INSUFFICIENT_NO_EXTENSION",
        )
    finally:
        api.close()
    # Preserve actual original issue times and tokens even if a later setup operation fails.
    save(output / "sessions.json", sessions)
    save(output / "session-attestations.json", issued)

    def project_setup(pid):
        api = client_type(origin, ca, records, deadline)
        manager, developer = sessions["manager"]["token"], sessions["developer"]["token"]
        try:
            members = all_pages(api, f"/projects/{pid}/members", manager)
            iterations = all_pages(api, f"/projects/{pid}/iterations", manager)
            due = timestamp(plan["window"]["end_utc"]) + timedelta(days=2)
            choices = [
                row
                for row in iterations
                if timestamp(row["plan"]["planned_end"]) >= due
                and any(
                    item["user_id"] == sessions["developer"]["user_id"]
                    for item in row["plan"]["capacity"]
                )
            ]
            need(choices, "ACTUAL_ITERATION_CAPACITY_AND_HORIZON_REQUIRED")
            iteration = min(choices, key=lambda row: row["id"])
            tasks = all_pages(api, f"/projects/{pid}/tasks", manager)
            selected = choose_escalations(tasks, set(), now, 10)
            rules = api.request(f"/projects/{pid}/escalation-rules", manager)
            managers = sorted(
                member["user"]["id"]
                for member in members
                if member["active"] and 1 in member["roles"]
            )
            clients, dependencies = [], {}
            for index, escalation in enumerate(selected):
                intent("createTask", [pid])
                created = api.request(
                    f"/projects/{pid}/tasks",
                    manager,
                    {
                        "title": f"[synthetic r30] {plan['run_id']} {pid}-{index}",
                        "description": "[synthetic] API-created neutral preparation, not human delivery",
                        "iteration_id": iteration["id"],
                        "owner_id": sessions["developer"]["user_id"],
                        "dependency_task_ids": [],
                        "plan": {
                            "planned_start": stamp(now),
                            "planned_end": stamp(due),
                            "estimated_hours": 1,
                            "buffer_hours": 0.25,
                            "delay_contingency": "[synthetic] manager replans with evidence",
                        },
                    },
                )["task"]
                intent("transitionTask", [pid])
                task = api.request(
                    f"/projects/{pid}/tasks/{created['id']}/transitions",
                    developer,
                    {"expected_version": created["version"], "action": 1},
                )["task"]
                intent("createEscalation", [pid])
                event = api.request(
                    f"/internal/projects/{pid}/tasks/{escalation['id']}/escalations",
                    sessions["service"]["token"],
                    {
                        "expected_version": escalation["version"],
                        "schedule_version": escalation["schedule_version"],
                        "rule_version": rules["version"],
                        "scan_run_id": str(uuid.uuid4()),
                    },
                )["event"]
                actual_task = api.request(f"/projects/{pid}/tasks/{task['id']}", developer)
                actual_escalation = api.request(
                    f"/projects/{pid}/tasks/{escalation['id']}", manager
                )
                existing = all_pages(
                    api,
                    f"/projects/{pid}/escalations?task_id={escalation['id']}&level={event['level']}",
                    manager,
                )
                actual_event = next((row for row in existing if row["id"] == event["id"]), None)
                need(actual_event is not None, "ACTUAL_EXISTING_EVENT_READBACK_REQUIRED")
                edges = all_pages(api, f"/projects/{pid}/tasks/{task['id']}/dependencies", manager)
                need(not edges, "NEW_TASK_ACTUAL_DEPENDENCY_READBACK_REQUIRED")
                dependencies[str(task["id"])] = {
                    "project_id": pid,
                    "task_id": task["id"],
                    "predecessor_ids": [],
                    "predecessor_states": [],
                }
                clients.append(
                    {
                        "project_id": pid,
                        "transition_task": actual_task,
                        "escalation_task": actual_escalation,
                        "escalation_event": actual_event,
                        "project_manager_ids": managers,
                    }
                )
            return clients, members, iteration, dependencies, rules["version"]
        finally:
            api.close()

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(project_setup, ids))
    clients = [item for result in results for item in result[0]]
    for index, item in enumerate(clients):
        item["client_id"] = index
    need(
        len(clients) == 400 and len({result[4] for result in results}) == 1,
        "ACTUAL_400_CURRENT_INVENTORY_REQUIRED",
    )
    completed = stamp(clock())
    value = {
        "run_id": plan["run_id"],
        "namespace": plan["namespace"],
        "database": plan["target"]["database"],
        "binding_sha256": plan["target"]["binding_sha256"],
        "session_time_evidence": issued,
        "generated_complete_utc": completed,
        "inventory": {
            "schema": "772-inventory-v1",
            "captured_at": completed,
            "rule_version": results[0][4],
            "clients": clients,
        },
        "memberships": {str(pid): result[1] for pid, result in zip(ids, results, strict=True)},
        "iterations": {str(result[2]["id"]): result[2] for result in results},
        "transition_dependency_facts": {
            key: facts for result in results for key, facts in result[3].items()
        },
        "session_attestations": issued,
    }
    save(output / "factual-snapshots.json", value)
    save(
        output / "complete.PUBLIC.json",
        {
            "kind": "NEUTRAL_API_PREPARATION_NOT_MEASUREMENT",
            "new_tasks": 400,
            "clients": 400,
            "actual_generated_complete_utc": completed,
            "actual_database_counts_verified": False,
        },
    )
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("plan", "accounts", "service", "ca", "output", "import-receipt"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--root-admit-http-preparation", action="store_true")
    args = parser.parse_args()
    need(args.root_admit_http_preparation, "EXPLICIT_ROOT_HTTP_PREPARATION_REQUIRED")
    os.umask(0o077)
    prepare(
        read_json(args.plan),
        read_json(args.accounts),
        read_json(args.service),
        args.ca,
        args.output,
        import_receipt_raw=args.import_receipt.read_bytes(),
    )


if __name__ == "__main__":
    main()
