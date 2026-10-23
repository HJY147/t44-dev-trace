"""Application facade. Component owners are injected; no alternate storage is created."""

from t44.contracts import OPERATIONS, violations

from .codes import ERROR_CODES, Action
from .common import SCHEMAS, model, page, plan_values
from .errors import require
from .projects import Projects
from .reviews import Reviews
from .tasks import Tasks
from .workflow import Workflow

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

    def dispatch(self, g, call):
        collections = {
            "listTaskDependencies": ("task_dependencies", "Dependency"),
            "listTaskReviews": ("reviews", "Review"),
            "listReleaseAssessments": ("release_assessments", "ReleaseAssessment"),
            "listTaskDecisions": ("decisions", "Decision"),
        }
        if call.operation in collections:
            call.task(g)
            table, schema = collections[call.operation]
            serialize = (
                (lambda row: self.dependency_model(g, row))
                if schema == "Dependency"
                else (lambda row: model(schema, row))
            )
            return page(
                g,
                table,
                {"project_id": call.project_id, "task_id": call.path["task_id"]},
                call.query,
                serialize,
            )
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
            task = g.get("tasks", c.body["task_id"])
            require(task and task["project_id"] == c.project_id, "RESOURCE_NOT_FOUND")
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

    def listProjectAuditEvents(self, g, c):
        where = {
            "project_id": c.project_id,
            **{k: v for k, v in c.query.items() if k in ("task_id", "outcome")},
        }
        return page(
            g,
            "audit_events",
            where,
            c.query,
            lambda row: model(
                "AuditEvent",
                row,
                before=row["before_values"],
                after=row["after_values"],
                reason_code=ERROR_CODES[row["reason_code"]] if row["reason_code"] else None,
            ),
        )

    def listMyNotifications(self, g, c):
        require(self.notifications is not None, "DEPENDENCY_UNAVAILABLE")
        return self.notifications.list(g, actor_id=c.actor_id, query=c.query)

    def markNotificationRead(self, g, c):
        require(self.notifications is not None, "DEPENDENCY_UNAVAILABLE")
        return self.notifications.mark_read(
            g,
            actor_id=c.actor_id,
            project_id=c.project_id,
            notification_id=c.path["notification_id"],
            version=c.body["expected_version"],
            now=c.clock,
        )

    def handleNotification(self, g, c):
        require(self.notifications is not None, "DEPENDENCY_UNAVAILABLE")
        return self.notifications.handle(
            g,
            actor_id=c.actor_id,
            project_id=c.project_id,
            notification_id=c.path["notification_id"],
            version=c.body["expected_version"],
            note=c.body["note"],
            evidence=c.body["evidence"],
            now=c.clock,
        )

    def _escalation(self, method, g, c):
        require(self.escalations is not None, "DEPENDENCY_UNAVAILABLE")
        return getattr(self.escalations, method)(g, c)

    def getEscalationRules(self, g, c):
        return self._escalation("rules", g, c)

    def listEscalations(self, g, c):
        return self._escalation("list", g, c)

    def createEscalation(self, g, c):
        return self._escalation("create", g, c)
