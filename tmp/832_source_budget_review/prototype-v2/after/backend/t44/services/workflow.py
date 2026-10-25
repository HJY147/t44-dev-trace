"""Resolve persisted proofs, ask the pure state machine, and apply one CAS decision."""

from t44.domain import commands as domain_commands
from t44.domain import models as domain_models
from t44.domain.state_machine import decide

from . import codes
from .common import model, plan_values, roles, task_model
from .errors import Rejected, require

DOMAIN_ERRORS = {
    domain_models.Violation.PROJECT_ACCESS_REQUIRED: "PROJECT_ACCESS_DENIED",
    domain_models.Violation.INVALID_TRANSITION: "STATE_CONFLICT",
    domain_models.Violation.DEPENDENCIES_UNSATISFIED: "DEPENDENCIES_UNSATISFIED",
    domain_models.Violation.REVIEW_REQUIRED: "REVIEW_NOT_PASSED",
    domain_models.Violation.REVIEW_OUTCOME_MISMATCH: "REVIEW_NOT_PASSED",
    domain_models.Violation.REVIEW_BASELINE_STALE: "REVIEW_BASELINE_MISMATCH",
    domain_models.Violation.RELEASE_APPROVAL_REQUIRED: "RELEASE_APPROVAL_REQUIRED",
    domain_models.Violation.RELEASE_BASELINE_STALE: "ASSESSMENT_BASELINE_MISMATCH",
    domain_models.Violation.ROLLBACK_PLAN_REQUIRED: "RELEASE_APPROVAL_REQUIRED",
    domain_models.Violation.ROLE_FORBIDDEN: "ACTION_FORBIDDEN",
    domain_models.Violation.OWNER_REQUIRED: "ACTION_FORBIDDEN",
    domain_models.Violation.SELF_REVIEW_FORBIDDEN: "ACTION_FORBIDDEN",
    domain_models.Violation.RELEASE_SELF_REVIEW_FORBIDDEN: "ACTION_FORBIDDEN",
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
        predecessors = []
        if action in (codes.Action.START, codes.Action.REWORK) or (
            action == codes.Action.UNBLOCK and row["blocked_from_state"] == codes.State.DEVELOPING
        ):
            deps = g.rows("task_dependencies", {"project_id": c.project_id, "task_id": row["id"]})
            predecessor_ids = [d["depends_on_task_id"] for d in deps]
            if predecessor_ids:
                predecessors = g.rows("tasks", {"project_id": c.project_id, "id": predecessor_ids})
        review_id = (
            b.get("review_id")
            if action in (codes.Action.APPROVE_REVIEW, codes.Action.REJECT_REVIEW)
            else row["approved_review_id"]
        )
        review = g.get("reviews", review_id) if review_id else None
        if review:
            require(review["task_id"] == row["id"], "RESOURCE_NOT_FOUND")
            if action in (codes.Action.APPROVE_REVIEW, codes.Action.REJECT_REVIEW):
                require(review["version"] == b["review_version"], "REVIEW_BASELINE_MISMATCH")
        assessment = (
            g.get("release_assessments", b["assessment_id"]) if "assessment_id" in b else None
        )
        if assessment:
            require(assessment["task_id"] == row["id"], "RESOURCE_NOT_FOUND")
        review_gate = (
            domain_models.ReviewGate(
                reference(review["id"], review["version"]),
                domain_models.Cycle(review["delivery_cycle"], review["review_cycle"]),
                review["artifact_revision"],
                domain_models.ReviewOutcome.ACCEPTED
                if review["verdict"] == 1
                else domain_models.ReviewOutcome.REJECTED,
                self.review_complete(review),
                review["reviewer_id"] == row["owner_id"],
            )
            if review
            else None
        )
        release_gate, rollback_gate = None, None
        if action == codes.Action.DELIVER and assessment:
            require(
                b["assessment_version"] == assessment["version"], "ASSESSMENT_BASELINE_MISMATCH"
            )
            require(
                row["approved_assessment_id"] == assessment["id"]
                and row["approved_assessment_version"] == assessment["version"],
                "RELEASE_APPROVAL_REQUIRED"
                if assessment["delivery_cycle"] == row["delivery_cycle"]
                and assessment["schedule_version"] == row["schedule_version"]
                else "ASSESSMENT_BASELINE_MISMATCH",
            )
            release_gate = domain_models.ReleaseGate(
                reference(assessment["id"], assessment["version"]),
                assessment["delivery_cycle"],
                assessment["schedule_version"],
                assessment["status"] == 2,
                bool(assessment["review_evidence"]),
                assessment["status"] == 2,
                assessment["created_by"] == assessment["reviewed_by"],
            )
        if action == codes.Action.ROLLBACK and assessment:
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
            rollback_gate = domain_models.RollbackGate(
                reference(assessment["id"], b["rollback_plan_version"]),
                assessment["delivery_cycle"],
                assessment["status"] == 2,
                bool(
                    delivery
                    and delivery[0]["assessment_id"] == assessment["id"]
                    and delivery[0]["rollback_plan_version"] == b["rollback_plan_version"]
                ),
            )
        new_plan = plan_values(b["new_plan"]) if action == codes.Action.REWORK else None
        context = domain_models.TransitionContext(
            True,
            frozenset(codes.ROLE_TO_DOMAIN[r] for r in roles(c.membership["roles_mask"])),
            c.actor_id == row["owner_id"],
            tuple(codes.STATE_TO_DOMAIN[t["state"]] for t in predecessors),
            domain_models.Cycle(row["delivery_cycle"], row["review_cycle"]),
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
            codes.Action.START: lambda: domain_commands.StartDevelopment(),
            codes.Action.BLOCK: lambda: domain_commands.RecordBlock(
                b["reason"], codes.STAGE_TO_DOMAIN[b["responsibility_stage"]], evidence
            ),
            codes.Action.UNBLOCK: lambda: domain_commands.ResolveBlock(b["basis"], evidence),
            codes.Action.SUBMIT_REVIEW: lambda: domain_commands.SubmitForReview(
                b["artifact_revision"], evidence
            ),
            codes.Action.APPROVE_REVIEW: lambda: domain_commands.AcceptReview(
                reference(b["review_id"], b["review_version"])
            ),
            codes.Action.REJECT_REVIEW: lambda: domain_commands.ReturnForChanges(
                reference(b["review_id"], b["review_version"]), b["reason"]
            ),
            codes.Action.DELIVER: lambda: domain_commands.ApproveDelivery(
                reference(b["assessment_id"], b["assessment_version"]),
                b["release_version"],
                b["reason"],
                evidence,
            ),
            codes.Action.ROLLBACK: lambda: domain_commands.RecordRollback(
                b["reason"],
                b["impact"],
                b["target_version"],
                reference(b["assessment_id"], b["rollback_plan_version"]),
                evidence,
            ),
            codes.Action.REWORK: lambda: domain_commands.AuthorizeRework(
                "new-plan", b["reason"], evidence
            ),
        }
        position = domain_models.TaskPosition(
            codes.STATE_TO_DOMAIN[row["state"]],
            codes.STATE_TO_DOMAIN[row["blocked_from_state"]] if row["blocked_from_state"] else None,
        )
        try:
            decision = decide(position, commands[action](), context)
        except domain_models.DomainViolation as error:
            raise Rejected(
                DOMAIN_ERRORS.get(error.code, "EVIDENCE_REQUIRED"), current_state=row["state"]
            ) from None
        if action == codes.Action.REWORK:
            c.check_version(row)
            self.owner(g, c, row["owner_id"], code="CAPACITY_REFERENCE_INVALID")
            self.capacity_owner(g, c, row["owner_id"], row["iteration_id"])
        values = {
            "state": codes.DOMAIN_TO_STATE[decision.target.state],
            "blocked_from_state": codes.DOMAIN_TO_STATE[decision.target.blocked_from]
            if decision.target.blocked_from
            else None,
            "block_reason": b["reason"] if action == codes.Action.BLOCK else None,
            "responsibility_stage": b["responsibility_stage"]
            if action == codes.Action.BLOCK
            else None,
        }
        if action == codes.Action.SUBMIT_REVIEW:
            values["artifact_revision"] = b["artifact_revision"]
        if action == codes.Action.APPROVE_REVIEW:
            values["approved_review_id"] = b["review_id"]
        if domain_models.Effect.CLEAR_APPROVALS in decision.effects:
            values.update(
                latest_review_id=None,
                approved_review_id=None,
                approved_assessment_id=None,
                approved_assessment_version=None,
                artifact_revision=None,
            )
        if domain_models.Effect.ADVANCE_REVIEW_CYCLE in decision.effects:
            values["review_cycle"] = row["review_cycle"] + 1
        if domain_models.Effect.ADVANCE_DELIVERY_CYCLE in decision.effects:
            values.update(
                delivery_cycle=row["delivery_cycle"] + 1,
                review_cycle=1,
                schedule_version=row["schedule_version"] + 1,
                **new_plan,
            )
        changed = c.cas(g, "tasks", row, values)
        if action == codes.Action.REWORK:
            self.schedule_diff(g, c, row, changed)
        saved_decision = None
        if action in codes.DECISION_TYPE:
            identifier = g.insert(
                "decisions",
                {
                    "project_id": c.project_id,
                    "task_id": row["id"],
                    "type": codes.DECISION_TYPE[action],
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
