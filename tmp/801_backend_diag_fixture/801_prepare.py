"""Root-run fresh-P fixture preparation. No import-time database or credential access."""

import argparse
import hashlib
import importlib
import json
import os
import subprocess
import sys
from collections import defaultdict
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

http = importlib.import_module("801_http")


def guarded_settings(host, port, user):
    from t44.settings import Settings

    try:
        settings = Settings.from_env()
        mysql = settings.mysql_settings()
    except Exception:  # noqa: BLE001 - parsed DSN errors can contain credentials
        raise http.InvalidDiagnostic("Invalid database configuration") from None
    if (
        os.environ.get("T44_DIAG_ALLOW") != "source935-development-only"
        or os.environ.get("T44_DIAG_PRODUCT_SHA") != http.PRODUCT
        or os.environ.get("T44_DATABASE") != http.DATABASE
        or mysql.database != http.DATABASE
        or mysql.host != host
        or mysql.port != port
        or port != 3306
        or user == "root"
        or mysql.username != user
    ):
        raise http.InvalidDiagnostic("Fresh diagnostic target declarations differ")
    from t44 import api

    package = Path(api.__file__).parent
    checks = {
        "api.py": "2db431218d7c182dd114b7e616442478539396dcf86cccca42a537250356075e",
        "services/runtime.py": "9e0d770e4d5a646b406e1b1a3e328a7e369219d8821dbfcc008303547fe6825b",
    }
    if any(
        hashlib.sha256((package / path).read_bytes()).hexdigest() != digest
        for path, digest in checks.items()
    ):
        raise http.InvalidDiagnostic(
            "Source935 subset mismatch; full image attestation external"
        )
    return settings, mysql


def spread(rows, count):
    groups = defaultdict(list)
    for row in sorted(rows, key=lambda row: row["id"]):
        groups[row["project_id"]].append(row)
    result = []
    while len(result) < count:
        progressed = False
        for project in sorted(groups):
            if groups[project]:
                result.append(groups[project].pop(0))
                progressed = True
                if len(result) == count:
                    break
        if not progressed:
            raise http.InvalidDiagnostic("Insufficient real eligible disjoint tasks")
    return result


def candidates(g, accounts, count, clock):
    from t44.scheduling.rules import load_rules, select_window

    projects = g.rows("projects", {})
    project_ids = sorted(project["id"] for project in projects)
    if len(project_ids) != 40 or not g.rows(
        "audit_events", {"operation_id": "syntheticSeedV1"}, limit=1
    ):
        raise http.InvalidDiagnostic("Expected real seeded forty-project fresh fixture")
    for role, mask in (("manager", 1), ("developer", 2), ("reviewer", 4)):
        account = accounts[role]
        users = g.rows("users", {"username": account["username"], "active": 1})
        members = g.rows(
            "project_members", {"user_id": account["user_id"], "active": 1}
        )
        if (
            len(users) != 1
            or users[0]["id"] != account["user_id"]
            or {row["project_id"] for row in members if row["roles_mask"] & mask}
            != set(project_ids)
        ):
            raise http.InvalidDiagnostic(
                "Actual account/membership differs from explicit roles"
            )
    tasks = g.rows("tasks", {})
    by_id = {row["id"]: row for row in tasks}
    dependencies = defaultdict(list)
    for row in g.rows("task_dependencies", {}):
        dependencies[row["task_id"]].append(row["depends_on_task_id"])
    iterations = {row["id"]: row for row in g.rows("iterations", {})}
    uid = accounts["developer"]["user_id"]
    transitions = spread(
        [
            row
            for row in tasks
            if row["state"] == 2
            and row["owner_id"] == uid
            and any(
                entry["user_id"] == uid
                for entry in iterations[row["iteration_id"]]["capacity"]
            )
            and all(
                by_id[identifier]["state"] == 6
                for identifier in dependencies[row["id"]]
            )
        ],
        count,
    )
    used, rules = {row["id"] for row in transitions}, load_rules()
    escalations = []
    for row in tasks:
        if row["id"] in used or row["state"] not in (1, 2, 3, 4, 5):
            continue
        first = select_window(clock, row["planned_end"], rules)
        later = select_window(clock + timedelta(minutes=15), row["planned_end"], rules)
        if first is not None and later is not None and first.level == later.level:
            escalations.append(row)
    return project_ids, transitions, spread(escalations, count), rules.version


def login(client, accounts):
    sessions = {}
    for role in ("manager", "developer", "reviewer"):
        account = accounts[role]
        result = client.call(
            "/api/v1/auth/login",
            body={"username": account["username"], "password": account["password"]},
            sample=False,
        )
        if result["user"]["id"] != account["user_id"]:
            raise http.InvalidDiagnostic(
                "Authenticated user differs from explicit account"
            )
        sessions[role] = {key: result[key] for key in ("access_token", "expires_at")}
        sessions[role]["user_id"] = result["user"]["id"]
    return sessions


def snapshot(client, row, token):
    task = client.call(http.task_path(row), token, sample=False)
    if task["project_id"] != row["project_id"] or task["id"] != row["id"]:
        raise http.InvalidDiagnostic("HTTP task identity mismatch")
    return http.slim(task)


def prepare(args):
    http.target(args.url)
    if not 1 <= args.slots <= 400:
        raise http.InvalidDiagnostic("Slots must be 1..400")
    _settings, mysql = guarded_settings(args.host, args.port, args.user)
    accounts = http.private_json(args.accounts)
    if set(accounts) != {"manager", "developer", "reviewer"}:
        raise http.InvalidDiagnostic("Explicit three-role account mapping required")
    for account in accounts.values():
        if (
            set(account) != {"username", "password", "user_id"}
            or type(account["user_id"]) is not int
        ):
            raise http.InvalidDiagnostic("Account shape invalid")
    directory = Path(args.output_dir)
    if not directory.is_absolute():
        raise http.InvalidDiagnostic("Absolute new owned output directory required")
    directory.mkdir(mode=0o700)
    status_fd, packet_fd = http.reserve(directory / "status.public.jsonl"), None
    engine = client = None
    try:
        packet_fd = http.reserve(directory / "session.private.json")
        from t44.persistence import SqlAlchemyUnitOfWorkFactory, create_mysql_engine

        engine = create_mysql_engine(mysql)
        with SqlAlchemyUnitOfWorkFactory(engine)() as uow:
            projects, transition_rows, escalation_rows, rule_version = candidates(
                uow.gateway, accounts, args.slots, datetime.now(UTC)
            )
        service_path = directory / "service.private.json"
        command = [
            sys.executable,
            "-m",
            "t44.cli",
            "service-token",
            "--name",
            "diag801-" + uuid4().hex,
            "--token-file",
            str(service_path),
        ]
        for identifier in projects:
            command.extend(("--project-id", str(identifier)))
        result = subprocess.run(
            command,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            check=False,
            timeout=60,
        )
        if result.returncode != 0:
            raise http.InvalidDiagnostic("Original service-token CLI failed")
        service = http.private_json(service_path)
        client = http.Client(args.url, args.ca)
        sessions = login(client, accounts)
        sessions["service"] = {
            key: service[key] for key in ("access_token", "expires_at")
        }
        del accounts
        slots = []
        for transition_row, escalation_row in zip(
            transition_rows, escalation_rows, strict=True
        ):
            transition = snapshot(
                client, transition_row, sessions["developer"]["access_token"]
            )
            if transition["state"] != 2:
                raise http.InvalidDiagnostic(
                    "Transition fixture changed during preparation"
                )
            escalation = snapshot(
                client, escalation_row, sessions["manager"]["access_token"]
            )
            scan_run_id = str(uuid4())
            path = (
                "/api/v1/internal"
                + http.task_path(escalation).removeprefix("/api/v1")
                + "/escalations"
            )
            body = {
                "expected_version": escalation["version"],
                "schedule_version": escalation["schedule_version"],
                "rule_version": rule_version,
                "scan_run_id": scan_run_id,
            }
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
                raise http.InvalidDiagnostic(
                    "Fresh fixture escalation was not newly created"
                )
            escalation["version"] = created["task_version"]
            body["expected_version"] = escalation["version"]
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
                raise http.InvalidDiagnostic(
                    "Real existing-event deduplication not established"
                )
            validated = client.call(
                f"/api/v1/projects/{transition['project_id']}/contract-validations",
                sessions["developer"]["access_token"],
                {
                    "category": 2,
                    "task_id": transition["id"],
                    "payload": http.block_body(transition),
                },
                sample=False,
            )
            if validated.get("valid") is not True:
                raise http.InvalidDiagnostic("Real contract input invalid")
            slots.append(
                {
                    "transition": transition,
                    "transition_role": "developer",
                    "escalation": escalation,
                    "scan_run_id": scan_run_id,
                    "event_id": created["event"]["id"],
                    "rule_version": rule_version,
                }
            )
            if len(slots) % 20 == 0:
                http.write_fd(
                    status_fd,
                    {
                        "kind": "preparation_progress",
                        "utc": http.utc(),
                        "prepared_slots": len(slots),
                    },
                )
        packet = {
            "kind": "source935-development-only",
            "product": http.PRODUCT,
            "database": http.DATABASE,
            "url": args.url,
            "created_at": http.utc(),
            "sessions": sessions,
            "slots": slots,
            "resumable": True,
            "valid_for_seconds_from_prepare": 600,
        }
        http.check_packet(packet)
        http.write_fd(packet_fd, packet)
        os.fsync(packet_fd)
        http.write_fd(
            status_fd,
            {
                "kind": "prepared-not-acceptance",
                "product": http.PRODUCT,
                "database": http.DATABASE,
                "utc": http.utc(),
                "projects": len(projects),
                "slots": len(slots),
                "original_cli_service_token": True,
                "three_real_http_logins": True,
                "real_creation_and_dedup_pairs": len(slots),
                "passwords_in_packet": False,
                "diagnostic_valid": True,
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
                "failure": type(error).__name__,
                "partial_business_commits_may_exist": True,
                "retry_requires_new_fixture_review": True,
            },
        )
        raise
    finally:
        if client:
            client.close()
        if engine:
            engine.dispose()
        os.close(status_fd)
        if packet_fd is not None:
            os.close(packet_fd)


def main(argv=None):
    parser = argparse.ArgumentParser()
    for name in ("accounts", "output-dir", "url", "ca", "host", "user"):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--slots", type=int, default=400)
    return prepare(parser.parse_args(argv))


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as error:  # noqa: BLE001 - never print private exception details
        print(json.dumps({"preparation_failed": type(error).__name__}), file=sys.stderr)
        sys.exit(1)
