"""Resolve persisted proofs, ask the pure state machine, and apply one CAS decision."""

from t44.domain.commands import (
    AcceptReview,
    ApproveDelivery,
    AuthorizeRework,
    RecordBlock,
    RecordRollback,
    ResolveBlock,
    ReturnForChanges,
    StartDevelopment,
    SubmitForReview,
)
from t44.domain.models import (
    Cycle,
    DomainViolation,
    Effect,
    ProjectRole,
    ReleaseGate,
    ResponsibilityStage,
    ReviewGate,
    ReviewOutcome,
    RollbackGate,
    TaskPosition,
    TaskState,
    TransitionContext,
    Violation,
)
from t44.domain.state_machine import decide

from .common import model, page, plan_values, roles, task_model
from .errors import Rejected, require

STATES = tuple(TaskState)
DOMAIN_ERRORS = {
    Violation.PROJECT_ACCESS_REQUIRED: "PROJECT_ACCESS_DENIED",
    Violation.INVALID_TRANSITION: "STATE_CONFLICT",
    Violation.DEPENDENCIES_UNSATISFIED: "DEPENDENCIES_UNSATISFIED",
    Violation.REVIEW_REQUIRED: "REVIEW_NOT_PASSED",
    Violation.REVIEW_OUTCOME_MISMATCH: "REVIEW_NOT_PASSED",
    Violation.REVIEW_BASELINE_STALE: "REVIEW_BASELINE_MISMATCH",
    Violation.RELEASE_APPROVAL_REQUIRED: "RELEASE_APPROVAL_REQUIRED",
    Violation.RELEASE_BASELINE_STALE: "ASSESSMENT_BASELINE_MISMATCH",
    Violation.ROLLBACK_PLAN_REQUIRED: "RELEASE_APPROVAL_REQUIRED",
    Violation.ROLE_FORBIDDEN: "ACTION_FORBIDDEN",
    Violation.OWNER_REQUIRED: "ACTION_FORBIDDEN",
    Violation.SELF_REVIEW_FORBIDDEN: "ACTION_FORBIDDEN",
    Violation.RELEASE_SELF_REVIEW_FORBIDDEN: "ACTION_FORBIDDEN",
}


def reference(identifier, version):
    return f"{identifier}:{version}"


class Workflow:
    def transitionTask(self, g, c):
        row, b = c.task(g), c.body
        action = b["action"]
        # Optimistic version is checked after authorization/replay and before proof resolution.
        require(
            row["version"] == b["expected_version"],
            "VERSION_CONFLICT",
            current_version=row["version"],
            current_state=row["state"],
        )
        evidence = tuple(e["locator"] for e in b.get("evidence", ()))
        deps = g.rows("task_dependencies", {"task_id": row["id"]})
        predecessor_ids = [d["depends_on_task_id"] for d in deps]
        predecessors = g.rows("tasks", {"project_id": c.project_id, "id": predecessor_ids})
        review_id = b.get("review_id") if action in (5, 6) else row["approved_review_id"]
        review = g.get("reviews", review_id) if review_id else None
        if review:
            require(review["task_id"] == row["id"], "RESOURCE_NOT_FOUND")
            if action in (5, 6):
                require(review["version"] == b["review_version"], "REVIEW_BASELINE_MISMATCH")
        assessment = (
            g.get("release_assessments", b["assessment_id"]) if "assessment_id" in b else None
        )
        if assessment:
            require(assessment["task_id"] == row["id"], "RESOURCE_NOT_FOUND")
        review_gate = (
            ReviewGate(
                reference(review["id"], review["version"]),
                Cycle(review["delivery_cycle"], review["review_cycle"]),
                review["artifact_revision"],
                ReviewOutcome.ACCEPTED if review["verdict"] == 1 else ReviewOutcome.REJECTED,
                self.review_complete(review),
                review["reviewer_id"] == row["owner_id"],
            )
            if review
            else None
        )
        release_gate, rollback_gate = None, None
        if action == 7 and assessment:
            require(
                b["assessment_version"] == assessment["version"], "ASSESSMENT_BASELINE_MISMATCH"
            )
            require(
                row["approved_assessment_id"] == assessment["id"]
                and row["approved_assessment_version"] == assessment["version"],
                "RELEASE_APPROVAL_REQUIRED",
            )
            release_gate = ReleaseGate(
                reference(assessment["id"], assessment["version"]),
                assessment["delivery_cycle"],
                assessment["schedule_version"],
                assessment["status"] == 2,
                bool(assessment["review_evidence"]),
                assessment["status"] == 2,
                assessment["created_by"] == assessment["reviewed_by"],
            )
        if action == 8 and assessment:
            delivery = g.rows(
                "decisions",
                {"task_id": row["id"], "delivery_cycle": row["delivery_cycle"], "type": 1},
                limit=1,
            )
            require(
                assessment["rollback_plan_version"] == b["rollback_plan_version"]
                and assessment["rollback_plan"]["target_version"] == b["target_version"],
                "RELEASE_APPROVAL_REQUIRED",
            )
            rollback_gate = RollbackGate(
                reference(assessment["id"], b["rollback_plan_version"]),
                assessment["delivery_cycle"],
                assessment["status"] == 2,
                bool(
                    delivery
                    and delivery[0]["assessment_id"] == assessment["id"]
                    and delivery[0]["rollback_plan_version"] == b["rollback_plan_version"]
                ),
            )
        new_plan = plan_values(b["new_plan"]) if action == 9 else None
        context = TransitionContext(
            True,
            frozenset(tuple(ProjectRole)[r - 1] for r in roles(c.membership["roles_mask"])),
            c.actor_id == row["owner_id"],
            tuple(STATES[t["state"] - 1] for t in predecessors),
            Cycle(row["delivery_cycle"], row["review_cycle"]),
            row["schedule_version"],
            row["artifact_revision"],
            reference(row["latest_review_id"], 1) if row["latest_review_id"] else None,
            reference(row["approved_review_id"], 1) if row["approved_review_id"] else None,
            review_gate,
            release_gate,
            rollback_gate,
            "new-plan" if new_plan else None,
        )
        commands = {
            1: lambda: StartDevelopment(),
            2: lambda: RecordBlock(
                b["reason"], tuple(ResponsibilityStage)[b["responsibility_stage"] - 1], evidence
            ),
            3: lambda: ResolveBlock(b["basis"], evidence),
            4: lambda: SubmitForReview(b["artifact_revision"], evidence),
            5: lambda: AcceptReview(reference(b["review_id"], b["review_version"])),
            6: lambda: ReturnForChanges(
                reference(b["review_id"], b["review_version"]), b["reason"]
            ),
            7: lambda: ApproveDelivery(
                reference(b["assessment_id"], b["assessment_version"]),
                b["release_version"],
                b["reason"],
                evidence,
            ),
            8: lambda: RecordRollback(
                b["reason"],
                b["impact"],
                b["target_version"],
                reference(b["assessment_id"], b["rollback_plan_version"]),
                evidence,
            ),
            9: lambda: AuthorizeRework("new-plan", b["reason"], evidence),
        }
        position = TaskPosition(
            STATES[row["state"] - 1],
            STATES[row["blocked_from_state"] - 1] if row["blocked_from_state"] else None,
        )
        try:
            decision = decide(position, commands[action](), context)
        except DomainViolation as error:
            raise Rejected(
                DOMAIN_ERRORS.get(error.code, "EVIDENCE_REQUIRED"), current_state=row["state"]
            ) from None
        values = {
            "state": STATES.index(decision.target.state) + 1,
            "blocked_from_state": STATES.index(decision.target.blocked_from) + 1
            if decision.target.blocked_from
            else None,
            "block_reason": b["reason"] if action == 2 else None,
            "responsibility_stage": b["responsibility_stage"] if action == 2 else None,
        }
        if action == 4:
            values["artifact_revision"] = b["artifact_revision"]
        if action == 5:
            values["approved_review_id"] = b["review_id"]
        if Effect.CLEAR_APPROVALS in decision.effects:
            values.update(
                latest_review_id=None,
                approved_review_id=None,
                approved_assessment_id=None,
                approved_assessment_version=None,
                artifact_revision=None,
            )
        if Effect.ADVANCE_REVIEW_CYCLE in decision.effects:
            values["review_cycle"] = row["review_cycle"] + 1
        if Effect.ADVANCE_DELIVERY_CYCLE in decision.effects:
            values.update(
                delivery_cycle=row["delivery_cycle"] + 1,
                review_cycle=1,
                schedule_version=row["schedule_version"] + 1,
                **new_plan,
            )
        changed = c.cas(g, "tasks", row, values)
        if action == 9:
            self.schedule_diff(g, c, row, changed)
        saved_decision = None
        if action >= 7:
            identifier = g.insert(
                "decisions",
                {
                    "project_id": c.project_id,
                    "task_id": row["id"],
                    "type": action - 6,
                    "decided_by": c.actor_id,
                    "delivery_cycle": changed["delivery_cycle"],
                    "reason": b["reason"],
                    "impact": b.get("impact"),
                    "target_version": b.get("target_version", b.get("release_version")),
                    "assessment_id": b.get("assessment_id"),
                    "rollback_plan_version": assessment["rollback_plan_version"]
                    if assessment
                    else None,
                    "evidence": b["evidence"],
                    "decided_at": c.clock,
                },
            )
            saved_decision = model("Decision", g.get("decisions", identifier))
        c.before.append({"field": "state", "value": str(row["state"])})
        c.after.append({"field": "state", "value": str(changed["state"])})
        return {"task": task_model(changed), "decision": saved_decision}

    def listTaskDecisions(self, g, c):
        c.task(g)
        return page(
            g,
            "decisions",
            {"project_id": c.project_id, "task_id": c.path["task_id"]},
            c.query,
            lambda r: model("Decision", r),
        )
