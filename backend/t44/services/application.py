"""Application facade. Component owners are injected; no alternate storage is created."""

from t44.contracts import OPERATIONS, violations

from .codes import ERROR_CODES, Action, State
from .common import SCHEMAS, model, page, plan, plan_values, roles
from .errors import require
from .history import project_reasons
from .projects import Projects
from .reviews import Reviews
from .tasks import Tasks
from .workflow import Workflow

_COMPONENT_OPERATIONS = {
    "listMyNotifications": ("notifications", "list"),
    "markNotificationRead": ("notifications", "mark_read"),
    "handleNotification": ("notifications", "handle"),
    "getEscalationRules": ("escalations", "rules"),
    "listEscalations": ("escalations", "list"),
    "createEscalation": ("escalations", "create"),
}

_COLLECTIONS = {
    "listProjects": ("projects", "Project"),
    "listProjectMembers": ("project_members", "Member"),
    "listIterations": ("iterations", "Iteration"),
    "listTasks": ("tasks", "Task"),
    "listTaskDependencies": ("task_dependencies", "Dependency"),
    "listTaskReviews": ("reviews", "Review"),
    "listReleaseAssessments": ("release_assessments", "ReleaseAssessment"),
    "listTaskDecisions": ("decisions", "Decision"),
    "listProjectAuditEvents": ("audit_events", "AuditEvent"),
}
_FILTERS = {"Task": ("state", "owner_id", "iteration_id"), "AuditEvent": ("task_id", "outcome")}
_RELATED = {"Member": ("users", "user_id"), "Dependency": ("tasks", "depends_on_task_id")}

_DICTIONARIES = {
    "task_states": "TaskState",
    "project_roles": "ProjectRole",
    "transition_actions": "TransitionAction",
    "responsibility_stages": "ResponsibilityStage",
    "review_judgments": "ReviewItemJudgment",
    "risk_perspectives": "RiskPerspective",
    "risk_severities": "RiskSeverity",
    "delivery_dispositions": "DeliveryDisposition",
    "evidence_kinds": "EvidenceRef",
    "review_verdicts": "ReviewVerdict",
    "assessment_statuses": "AssessmentStatus",
    "decision_types": "DecisionType",
    "audit_outcomes": "AuditOutcome",
    "escalation_recipient_kinds": "EscalationRecipientKind",
}


class Business(Projects, Tasks, Reviews, Workflow):
    def __init__(self, *, notifications=None, escalations=None):
        self.notifications, self.escalations = notifications, escalations

    def status(self, operation):
        return OPERATIONS[operation]["success_status"]

    def row_model(self, g, schema, row, related=None):
        if schema == "Member":
            user = (
                g.get("users", row["user_id"]) if related is None else related.get(row["user_id"])
            )
            return model(
                "Member",
                row,
                user=model("User", user),
                roles=roles(row["roles_mask"]),
                active=bool(row["active"]),
            )
        if schema == "Dependency":
            predecessor = (
                g.get("tasks", row["depends_on_task_id"])
                if related is None
                else related.get(row["depends_on_task_id"])
            )
            return model("Dependency", row, satisfied=predecessor["state"] == State.DELIVERED)
        if schema in ("Task", "Iteration"):
            return model(schema, row, plan=plan(row, iteration=schema == "Iteration"))
        if schema == "AuditEvent":
            return model(
                schema,
                row,
                before=row["before_values"],
                after=row["after_values"],
                reason_code=ERROR_CODES[row["reason_code"]] if row["reason_code"] else None,
            )
        return model(schema, row)

    def dispatch(self, g, call, *, locked_task=None):
        if locked_task is not None:
            gateway, row = locked_task
            require(gateway is g and call.operation == "transitionTask", "INTERNAL_ERROR")
            return self.transitionTask(g, call, locked_task=row)
        if call.operation in _COLLECTIONS:
            table, schema = _COLLECTIONS[call.operation]
            if "task_id" in call.path:
                call.task(g)
            where = {
                **call.path,
                **{
                    key: value
                    for key, value in call.query.items()
                    if key in _FILTERS.get(schema, ())
                },
            }

            def serialize(row):
                return self.row_model(g, schema, row)

            if schema == "Project":
                memberships = g.rows("project_members", {"user_id": call.actor_id, "active": 1})
                by_project = {row["project_id"]: row for row in memberships}
                where = {"id": list(by_project)}

                def serialize(row):
                    return self.project_model(row, by_project[row["id"]])

            if schema == "Member":
                where["active"] = 1

            def prepare(rows):
                if schema not in _RELATED:
                    return serialize
                target, key = _RELATED[schema]
                related = (
                    {
                        row["id"]: row
                        for row in g.rows(target, {"id": sorted({row[key] for row in rows})})
                    }
                    if rows
                    else {}
                )
                return lambda row: self.row_model(g, schema, row, related)

            result = page(g, table, where, call.query, serialize, prepare=prepare)
            return project_reasons(g, call.project_id, result) if schema == "AuditEvent" else result
        target = _COMPONENT_OPERATIONS.get(call.operation)
        if target:
            component, method = target
            owner = getattr(self, component)
            require(owner is not None, "DEPENDENCY_UNAVAILABLE")
            return getattr(owner, method)(g, call)
        return getattr(self, call.operation)(g, call)

    def finalize(self, result, call):
        fields = OPERATIONS[call.operation]["data_fields"]
        if "audit_id" in fields:
            result["audit_id"] = call.audit_id
        return result

    def validate_data(self, operation, result):
        require(not violations(OPERATIONS[operation]["data_schema"], result), "INTERNAL_ERROR")

    def outbox(self, c, project):
        return {
            "event_type": 1,
            "project_id": project,
            "task_id": c.path.get("task_id"),
            "payload": {"operation_id": c.operation, "request_id": c.request_id},
            "recipients": [],
            "next_attempt_at": c.clock,
            "created_at": c.clock,
            "updated_at": c.clock,
        }

    def getMe(self, g, c):
        return model("User", c.actor["identity"])

    def getDictionaries(self, g, c):
        result = {"version": 1, "error_codes": SCHEMAS["ErrorCode"]["enum"]}
        for key, schema in _DICTIONARIES.items():
            definition = SCHEMAS[schema]
            if schema == "EvidenceRef":
                definition = definition["properties"]["kind"]
            names = definition["x-enum-names"]
            result[key] = [
                {"value": value, "name": name, "label": name}
                for value, name in zip(definition["enum"], names, strict=True)
            ]
        result["escalation_levels"] = [
            {"value": value, "name": name, "label": name}
            for value, name in zip(
                SCHEMAS["EscalationLevel"]["x-v1-values"],
                SCHEMAS["EscalationLevel"]["x-v1-names"],
                strict=True,
            )
        ]
        return result

    def validateContractPayload(self, g, c):
        """Report the candidate Schema version independently from the envelope version."""
        category, payload = c.body["category"], c.body["payload"]
        if "task_id" in c.body:
            c.resource(g, "tasks", c.body["task_id"])
        if category == 1:
            plan_values(payload["plan"])
        elif category == 2 and payload["action"] == Action.REWORK:
            plan_values(payload["new_plan"])
        return {
            "valid": True,
            "category": category,
            "validated_operation_id": {
                1: "createTask",
                2: "transitionTask",
                3: "createReleaseAssessment",
            }[category],
            "schema_version": SCHEMAS["ContractValidationResult"]["properties"]["schema_version"][
                "const"
            ],
            "business_guards_executed": False,
        }
