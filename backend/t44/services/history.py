"""Conservative, response-only linkage of immutable task schedule history."""

from t44.contracts import violations

from .codes import State
from .common import SCHEMAS, time, wire


def _snapshot(audit):
    if (
        audit["outcome"] != 1
        or audit["actor_kind"] != 1
        or audit["actor_id"] is None
        or audit["task_id"] is None
        or len(audit["after"]) >= 50
        or any(item["field"] == "reason" for item in audit["after"])
    ):
        return None
    before, after = (
        {item["field"]: item["value"] for item in audit[side]} for side in ("before", "after")
    )
    related = {"version", "schedule_version", *SCHEMAS["Plan"]["required"]}
    if audit["operation_id"] == "transitionTask":
        related.add("state")
    for side in ("before", "after"):
        fields = [item["field"] for item in audit[side] if item["field"] in related]
        if len(fields) != len(set(fields)):
            return None
    if audit["operation_id"] != "changeTaskPlan" and not (
        audit["operation_id"] == "transitionTask"
        and before.get("state") == str(State.ROLLED_BACK)
        and after.get("state") == str(State.DEVELOPING)
    ):
        return None
    numbers = []
    for side in (before, after):
        for field in ("version", "schedule_version"):
            value = side.get(field, "")
            if not (
                isinstance(value, str)
                and value.isascii()
                and value.isdecimal()
                and len(value) <= 10
                and 1 <= int(value) <= 2147483647
                and str(int(value)) == value
            ):
                return None
            numbers.append(int(value))
    old, old_schedule, new, new_schedule = numbers
    if old != audit["expected_version"] or new != old + 1 or new_schedule != old_schedule + 1:
        return None
    return before, after, old_schedule, new_schedule


def _matches(audit, snapshot, change, project_id):
    before, after, old_schedule, new_schedule = snapshot
    reason = change["reason"]
    if not (
        audit["project_id"] == change["project_id"] == project_id
        and audit["task_id"] == change["task_id"]
        and change["iteration_id"] is None
        and change["from_version"] == old_schedule
        and change["to_version"] == new_schedule
        and audit["actor_id"] == change["changed_by"]
        and audit["created_at"] == wire(change["changed_at"])
        and audit["evidence"] == change["evidence"]
        and isinstance(reason, str)
        and reason.strip()
        and len(reason) <= 2000
    ):
        return False
    for diff, plan in ((before, change["before_plan"]), (after, change["after_plan"])):
        if violations(SCHEMAS["Plan"], plan):
            return False
        # Require the original plan() producer spelling, even for equivalent JSON numbers.
        if (
            any(type(plan[field]) is not float for field in ("estimated_hours", "buffer_hours"))
            or any(
                wire(time(plan[field])) != plan[field] for field in ("planned_start", "planned_end")
            )
            or not time(plan["planned_start"]) < time(plan["planned_end"])
            or not all(diff.get(field) == str(value) for field, value in plan.items())
        ):
            return False
    return True


def project_reasons(g, project_id, result):
    """Enrich only this authorized page; no row, replay snapshot, or page order changes."""
    eligible = [
        (audit, snapshot) for audit in result["items"] if (snapshot := _snapshot(audit)) is not None
    ]
    if eligible:
        pairs = tuple(dict.fromkeys((a["task_id"], s[3]) for a, s in eligible))
        changes = {
            (row["task_id"], row["to_version"]): row
            for row in g.task_schedule_changes(project_id, pairs)
        }
        for audit, snapshot in eligible:
            change = changes.get((audit["task_id"], snapshot[3]))
            if change and _matches(audit, snapshot, change, project_id):
                audit["after"] = [*audit["after"], {"field": "reason", "value": change["reason"]}]
    return result
