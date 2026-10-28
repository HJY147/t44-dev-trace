"""Root-run fresh-P fixture preparation. No import-time database or credential access."""

import hashlib
import importlib
import os
from collections import defaultdict
from pathlib import Path

http = importlib.import_module("790_http")


def guarded_settings(host, port, user):
    from t44.settings import Settings

    try:
        settings = Settings.from_env()
        mysql = settings.mysql_settings()
    except Exception:  # noqa: BLE001 - parsed DSN errors can contain credentials
        raise http.InvalidDiagnostic("Invalid database configuration") from None
    if (
        os.environ.get("T44_CONTRAST_ALLOW") != http.KIND
        or os.environ.get("T44_CONTRAST_SOURCE") != http.PRODUCT
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
        "services/runtime.py": "a8b6a6711f2a88249f760e05badd80c911ead6e25824e9d4400d8b3b1844a239",
        "persistence/migrations.py": "cf2e6b30c6284148afc24b039ee483f744e9fa8af0fbe5f0982f67fb42371ca5",
        "persistence/seed.py": "7fe5f623d56c0e16ea8395edd67fdd961563a04a8d73661d78133fe4f80ac141",
        "contracts/openapi.json": "6f07cb53a7d9314240ba93ec490325d3c63dca7e4d077021047e216e7b26f478",
    }
    if any(
        hashlib.sha256((package / path).read_bytes()).hexdigest() != digest
        for path, digest in checks.items()
    ):
        raise http.InvalidDiagnostic(
            "Target-source subset mismatch; full image attestation external"
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


def candidates(g, accounts, count, clock, emit_profile, inspect_only=False):
    from t44.scheduling.rules import load_rules, select_window

    projects = g.rows("projects", {})
    project_ids = sorted(project["id"] for project in projects)
    if len(project_ids) != 40 or not g.rows(
        "audit_events", {"operation_id": "syntheticSeedV2"}, limit=1
    ):
        raise http.InvalidDiagnostic("Expected real seeded forty-project fresh fixture")
    for role, mask in (("manager", 1), ("developer", 2), ("reviewer", 4)):
        account = accounts[role]
        users = g.rows("users", {"username": account["username"], "active": 1})
        members = g.rows("project_members", {"user_id": account["user_id"], "active": 1})
        if (
            len(users) != 1
            or users[0]["id"] != account["user_id"]
            or {row["project_id"] for row in members if row["roles_mask"] & mask}
            != set(project_ids)
        ):
            raise http.InvalidDiagnostic("Actual account/membership differs from explicit roles")
    tasks = g.rows("tasks", {})
    by_id = {row["id"]: row for row in tasks}
    dependencies = defaultdict(list)
    edge_rows = g.rows("task_dependencies", {})
    for row in edge_rows:
        dependencies[row["task_id"]].append(row["depends_on_task_id"])
    iterations = {row["id"]: row for row in g.rows("iterations", {})}
    uid = accounts["developer"]["user_id"]
    transitions = [
        row
        for row in tasks
        if row["state"] == 2
        and row["owner_id"] == uid
        and any(entry["user_id"] == uid for entry in iterations[row["iteration_id"]]["capacity"])
        and all(by_id[identifier]["state"] == 6 for identifier in dependencies[row["id"]])
    ]
    used, rules = {row["id"] for row in transitions}, load_rules()
    escalations = []
    for row in tasks:
        if row["id"] in used or row["state"] not in (1, 2, 3, 4, 5):
            continue
        first = select_window(clock, row["planned_end"], rules)
        later = select_window(http.parse_utc(http.CONTROL["stop_utc"]), row["planned_end"], rules)
        if first is not None and later is not None and first.level == later.level:
            escalations.append(row)
    emit_profile(
        {
            "kind": "actual-readonly-candidate-profile",
            "utc": http.utc(),
            "projects_observed": len(projects),
            "tasks_observed": len(tasks),
            "dependencies_observed": len(edge_rows),
            "eligible_transition_tasks": len(transitions),
            "eligible_disjoint_escalation_tasks": len(escalations),
            "requested_slots": count,
            "sufficient_observed": min(len(transitions), len(escalations)) >= count,
            "selection_scope": "DEVELOPING developer owner, valid capacity, all actual predecessors DELIVERED; escalation excludes every eligible transition",
            "not_a_business_defect_if_insufficient": True,
        }
    )
    if inspect_only:
        return project_ids, [], [], rules.version
    return (
        project_ids,
        spread(transitions, count),
        spread(escalations, count),
        rules.version,
    )
