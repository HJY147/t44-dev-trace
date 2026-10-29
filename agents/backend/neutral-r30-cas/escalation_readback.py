"""Keep the POST CAS intact; adopt only a schema-checked, stable existing GET event."""

import uuid

from guard import need, timestamp
from http_primitives import HttpRejected, all_pages, save
from t44.contracts import violations
from t44.scheduling.rules import load_rules, select_window


def valid_task(task, selected, pid, observed_at):
    need(
        not violations({"$ref": "#/components/schemas/Task"}, task),
        "COMPLETE_ESCALATION_TASK_READBACK_REQUIRED",
    )
    need(
        task["id"] == selected["id"]
        and task["project_id"] == pid
        and task["schedule_version"] == selected["schedule_version"]
        and task["plan"] == selected["plan"]
        and task["state"] in (1, 2, 3, 4, 5)
        and task["version"] >= selected["version"]
        and timestamp(task["updated_at"]) <= observed_at,
        "ORIGINAL_ESCALATION_SCOPE_AND_SCHEDULE_REQUIRED",
    )


def create_or_read_existing(
    api, pid, selected, rules_snapshot, manager, service, window, clock, output
):
    rules = load_rules()
    need(rules_snapshot == rules.snapshot(), "EXACT_CURRENT_FROZEN_RULES_REQUIRED")
    valid_task(selected, selected, pid, clock())
    conflict, posted = None, None
    try:
        posted = api.request(
            f"/internal/projects/{pid}/tasks/{selected['id']}/escalations",
            service,
            {
                "expected_version": selected["version"],
                "schedule_version": selected["schedule_version"],
                "rule_version": rules.version,
                "scan_run_id": str(uuid.uuid4()),
            },
        )["event"]
    except HttpRejected as error:
        if (
            error.status != 409
            or not isinstance(error.envelope, dict)
            or error.envelope.get("code") != "VERSION_CONFLICT"
        ):
            raise
        need(
            not violations({"$ref": "#/components/schemas/Error"}, error.envelope),
            "COMPLETE_ORIGINAL_VERSION_CONFLICT_ENVELOPE_REQUIRED",
        )
        conflict = error
        current_rules = api.request(f"/projects/{pid}/escalation-rules", manager)
        need(current_rules == rules_snapshot, "RULES_CHANGED_DURING_ESCALATION_PREPARATION")

    path = f"/projects/{pid}/tasks/{selected['id']}"
    before = api.request(path, manager)
    valid_task(before, selected, pid, clock())
    if conflict is not None:
        need(
            before["version"] > selected["version"],
            "VERSION_CONFLICT_WITHOUT_OBSERVED_TASK_ADVANCE",
        )
    matches = [
        select_window(at, before["plan"]["planned_end"], rules)
        for at in (clock(), timestamp(window["start_utc"]), timestamp(window["end_utc"]))
    ]
    need(
        all(match is not None for match in matches)
        and len({match.level for match in matches}) == 1,
        "SAME_RULE_SELECTED_LEVEL_FOR_PREPARATION_AND_WHOLE_WINDOW_REQUIRED",
    )
    level = matches[0].level
    events = all_pages(
        api, f"/projects/{pid}/escalations?task_id={selected['id']}&level={level}", manager
    )
    need(
        all(
            not violations({"$ref": "#/components/schemas/EscalationEvent"}, event)
            and event["project_id"] == pid
            and event["task_id"] == selected["id"]
            and event["level"] == level
            and timestamp(event["created_at"]) <= clock()
            for event in events
        ),
        "COMPLETE_SAME_OBJECT_EVENT_READBACK_REQUIRED",
    )
    current = [event for event in events if event["schedule_version"] == before["schedule_version"]]
    need(
        len(current) == 1 and current[0]["rule_version"] == rules.version,
        "ONE_EXISTING_EVENT_FOR_CURRENT_SCHEDULE_RULE_AND_LEVEL_REQUIRED",
    )
    event = current[0]
    if posted is not None:
        need(
            not violations({"$ref": "#/components/schemas/EscalationEvent"}, posted)
            and all(
                posted[key] == event[key]
                for key in (
                    "id",
                    "project_id",
                    "task_id",
                    "schedule_version",
                    "rule_version",
                    "level",
                    "recipient_ids",
                    "scan_run_id",
                    "created_at",
                )
            ),
            "POSTED_EVENT_MUST_BE_THE_ACTUAL_EXISTING_GET_EVENT",
        )
    after = api.request(path, manager)
    valid_task(after, selected, pid, clock())
    need(
        all(
            before[key] == after[key]
            for key in ("id", "project_id", "schedule_version", "plan", "state", "owner_id")
        )
        and after["version"] >= before["version"],
        "ESCALATION_TASK_CHANGED_DURING_EVENT_READBACK",
    )
    save(
        output / f"{pid}-{selected['id']}.json",
        {
            "kind": "ACTUAL_GET_EVENT_READBACK_NOT_POST_RETRY",
            "post_outcome": "http_409_VERSION_CONFLICT"
            if conflict is not None
            else "successful_response",
            "conflicting_post_request_id": None if conflict is None else conflict.request_id,
            "selected_expected_version": selected["version"],
            "first_read_task_version": before["version"],
            "task": after,
            "event": event,
        },
    )
    return after, event
