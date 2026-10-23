"""API and scanner share a transaction-local escalation service, never a private commit."""

from uuid import UUID

from t44.persistence import PersistenceIntegrityError
from t44.services.common import page, uuid_text, wire
from t44.services.errors import require

from .rules import load_rules, select_window


class EscalationFacade:
    def __init__(self, rules=None):
        self._configured = rules

    def current(self):
        return self._configured if self._configured is not None else load_rules()

    def rules(self, g, c):
        current = self.current()
        version = c.query.get("version", current.version)
        if version == current.version:
            return current.snapshot()
        history = g.rows("scan_runs", {"rule_version": version}, limit=1)
        require(history, "RESOURCE_NOT_FOUND")
        return history[0]["rule_snapshot"]

    def event(self, g, row):
        outbox = g.get("outbox_events", row["event_id"])
        notices = g.rows("notifications", {"event_id": row["event_id"]})
        disposition = (
            4
            if outbox["status"] == 4
            else (
                3
                if set(outbox["recipients"]) <= {n["recipient_id"] for n in notices}
                else 2
                if outbox["status"] == 3
                else 1
            )
        )
        return wire(
            {
                "id": row["event_id"],
                "task_id": row["task_id"],
                "project_id": row["project_id"],
                "schedule_version": row["schedule_version"],
                "rule_version": row["rule_version"],
                "level": row["level"],
                "recipient_ids": outbox["recipients"],
                "disposition": disposition,
                "scan_run_id": uuid_text(g.get("scan_runs", row["scan_run_id"])["run_key"]),
                "created_at": row["observed_at"],
                "handled_count": sum(n["handled_at"] is not None for n in notices),
            }
        )

    def list(self, g, c):
        return page(
            g,
            "escalation_events",
            {
                "project_id": c.project_id,
                **{k: v for k, v in c.query.items() if k in ("task_id", "level")},
            },
            c.query,
            lambda row: self.event(g, row),
        )

    def _run(self, g, c, rules):
        key = UUID(c.body["scan_run_id"]).bytes
        rows = g.rows("scan_runs", {"run_key": key}, limit=1)
        if not rows:
            try:
                with g.savepoint():
                    identifier = g.insert(
                        "scan_runs",
                        dict(
                            run_key=key,
                            rule_version=rules.version,
                            rule_snapshot=rules.snapshot(),
                            rule_hash=rules.raw_hash,
                            cutoff_at=c.clock,
                            status=1,
                            last_task_id=0,
                            scanned_count=0,
                            created_count=0,
                            duplicate_count=0,
                            started_at=c.clock,
                            heartbeat_at=c.clock,
                            finished_at=None,
                            error_code=None,
                        ),
                    )
                return identifier
            except PersistenceIntegrityError as error:
                if error.kind != "duplicate":
                    raise
            rows = g.rows("scan_runs", {"run_key": key}, limit=1)
        require(
            rows[0]["rule_hash"] == rules.raw_hash and rows[0]["rule_version"] == rules.version,
            "RULE_VERSION_CONFLICT",
        )
        return rows[0]["id"]

    def create(self, g, c):
        require(
            c.actor
            and c.actor["actor_kind"] == 2
            and "escalation:write" in c.actor["scopes"]
            and c.project_id in c.actor["project_ids"],
            "SERVICE_SCOPE_REQUIRED",
        )
        task, rules = c.task(g, lock="update"), self.current()
        require(
            task["version"] == c.body["expected_version"],
            "VERSION_CONFLICT",
            current_version=task["version"],
            current_state=task["state"],
        )
        require(task["schedule_version"] == c.body["schedule_version"], "SCHEDULE_VERSION_CONFLICT")
        require(
            rules.version == c.body["rule_version"] and c.clock >= rules.effective_at,
            "RULE_VERSION_CONFLICT",
        )
        match = select_window(c.clock, task["planned_end"], rules)
        require(
            task["state"] in (1, 2, 3, 4, 5) and match is not None, "NOT_ELIGIBLE_FOR_ESCALATION"
        )
        key = dict(task_id=task["id"], schedule_version=task["schedule_version"], level=match.level)
        existing = g.rows("escalation_events", key, limit=1)
        if existing:
            return {
                "event": self.event(g, existing[0]),
                "created": False,
                "task_version": task["version"],
            }
        require(
            task["escalation_count"] < 2147483647,
            "VERSION_CONFLICT",
            current_version=task["version"],
            current_state=task["state"],
        )
        members = g.rows("project_members", {"project_id": c.project_id, "active": 1})
        recipients = {task["owner_id"]} if 1 in match.recipient_kinds else set()
        if 2 in match.recipient_kinds:
            recipients.update(
                m["user_id"]
                for m in members
                if m["roles_mask"] & 1 and g.get("users", m["user_id"])["active"]
            )
        require(recipients, "DEPENDENCY_UNAVAILABLE")
        try:
            with g.savepoint():
                run_id = self._run(g, c, rules)
                event_id = g.insert(
                    "outbox_events",
                    dict(
                        event_type=2,
                        schema_version=1,
                        project_id=c.project_id,
                        task_id=task["id"],
                        payload=wire(
                            {
                                **key,
                                "rule_version": rules.version,
                                "planned_end": task["planned_end"],
                                "observed_at": c.clock,
                                "title": f"{match.label}：{task['title']}"[:200],
                                "message": f"任务 {task['id']} 触发{match.label}，请处理并记录依据",
                            }
                        ),
                        recipients=sorted(recipients),
                        status=1,
                        attempts=0,
                        next_attempt_at=c.clock,
                        lease_token=None,
                        lease_until=None,
                        confirmed_at=None,
                        fallback_at=None,
                        last_error_code=None,
                        created_at=c.clock,
                        updated_at=c.clock,
                    ),
                )
                identifier = g.insert(
                    "escalation_events",
                    dict(
                        **key,
                        project_id=c.project_id,
                        rule_version=rules.version,
                        rule_snapshot=rules.snapshot(),
                        rule_hash=rules.raw_hash,
                        scan_run_id=run_id,
                        planned_end=task["planned_end"],
                        observed_at=c.clock,
                        event_id=event_id,
                    ),
                )
        except PersistenceIntegrityError as error:
            if error.kind != "duplicate":
                raise
            rows = g.rows("escalation_events", key, limit=1)
            require(rows, "DEPENDENCY_UNAVAILABLE")
            return {
                "event": self.event(g, rows[0]),
                "created": False,
                "task_version": task["version"],
            }
        updated = c.cas(g, "tasks", task, {"escalation_count": task["escalation_count"] + 1})
        c.before.append({"field": "escalation_count", "value": str(task["escalation_count"])})
        c.after.append({"field": "escalation_count", "value": str(updated["escalation_count"])})
        return {
            "event": self.event(g, g.get("escalation_events", identifier)),
            "created": True,
            "task_version": updated["version"],
        }
