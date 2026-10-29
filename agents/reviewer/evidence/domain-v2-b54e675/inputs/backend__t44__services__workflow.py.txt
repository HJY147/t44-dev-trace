"""Resolve persisted proofs, ask the pure state machine, and apply one CAS decision."""

from t44.domain import models as domain
from t44.domain.state_machine import decide

from .codes import Action, State
from .common import model, plan_values, roles, task_model
from .errors import Rejected, require

DOMAIN_ERRORS = {
    "PROJECT_ACCESS_REQUIRED": "PROJECT_ACCESS_DENIED",
    "INVALID_TRANSITION": "STATE_CONFLICT",
    "DEPENDENCIES_UNSATISFIED": "DEPENDENCIES_UNSATISFIED",
    "REVIEW_REQUIRED": "REVIEW_NOT_PASSED",
    "REVIEW_OUTCOME_MISMATCH": "REVIEW_NOT_PASSED",
    "REVIEW_BASELINE_STALE": "REVIEW_BASELINE_MISMATCH",
    "RELEASE_APPROVAL_REQUIRED": "RELEASE_APPROVAL_REQUIRED",
    "RELEASE_BASELINE_STALE": "ASSESSMENT_BASELINE_MISMATCH",
    "ROLLBACK_PLAN_REQUIRED": "RELEASE_APPROVAL_REQUIRED",
    "ROLE_FORBIDDEN": "ACTION_FORBIDDEN",
    "OWNER_REQUIRED": "ACTION_FORBIDDEN",
    "SELF_REVIEW_FORBIDDEN": "ACTION_FORBIDDEN",
    "RELEASE_SELF_REVIEW_FORBIDDEN": "ACTION_FORBIDDEN",
}


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
        if action in (Action.START, Action.REWORK) or (
            action == Action.UNBLOCK and row["blocked_from_state"] == State.DEVELOPING
        ):
            deps = g.rows("task_dependencies", {"project_id": c.project_id, "task_id": row["id"]})
            predecessor_ids = [d["depends_on_task_id"] for d in deps]
            if predecessor_ids:
                predecessors = g.rows("tasks", {"project_id": c.project_id, "id": predecessor_ids})
        review_id = (
            b.get("review_id")
            if action in (Action.APPROVE_REVIEW, Action.REJECT_REVIEW)
            else row["approved_review_id"]
        )
        review = g.get("reviews", review_id) if review_id else None
        if review:
            require(review["task_id"] == row["id"], "RESOURCE_NOT_FOUND")
            if action in (Action.APPROVE_REVIEW, Action.REJECT_REVIEW):
                require(review["version"] == b["review_version"], "REVIEW_BASELINE_MISMATCH")
        assessment = (
            g.get("release_assessments", b["assessment_id"]) if "assessment_id" in b else None
        )
        if assessment:
            require(assessment["task_id"] == row["id"], "RESOURCE_NOT_FOUND")
        delivery = None
        if action == Action.DELIVER and assessment:
            require(
                b["assessment_version"] == assessment["version"], "ASSESSMENT_BASELINE_MISMATCH"
            )
            if not (
                row["approved_assessment_id"] == assessment["id"]
                and row["approved_assessment_version"] == assessment["version"]
            ):
                # The failed approval slot must not hide the existing state/manager guards.
                require(
                    row["state"] == State.PENDING_RELEASE,
                    "STATE_CONFLICT",
                    current_state=row["state"],
                )
                c.manager()
                require(
                    False,
                    "RELEASE_APPROVAL_REQUIRED"
                    if assessment["delivery_cycle"] == row["delivery_cycle"]
                    and assessment["schedule_version"] == row["schedule_version"]
                    else "ASSESSMENT_BASELINE_MISMATCH",
                )
        if action == Action.ROLLBACK and assessment:
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
            delivery = delivery[0] if delivery else None
        new_plan = plan_values(b["new_plan"]) if action == Action.REWORK else None
        context = domain.Transition(
            row,
            b,
            frozenset(roles(c.membership["roles_mask"])),
            c.actor_id == row["owner_id"],
            evidence,
            tuple(t["state"] for t in predecessors),
            review,
            assessment if action in (Action.DELIVER, Action.ROLLBACK) else None,
            delivery,
            self.review_complete(review) if review else False,
            new_plan=new_plan,
        )
        try:
            decision = decide(context)
        except domain.DomainViolation as error:
            raise Rejected(
                DOMAIN_ERRORS.get(error.code, "EVIDENCE_REQUIRED"), current_state=row["state"]
            ) from None
        if action == Action.REWORK:
            c.check_version(row)
            self.owner(g, c, row["owner_id"], code="CAPACITY_REFERENCE_INVALID")
            self.capacity_owner(g, c, row["owner_id"], row["iteration_id"])
        changed = c.cas(g, "tasks", row, decision.values)
        if action == Action.REWORK:
            self.schedule_diff(g, c, row, changed)
        saved_decision = None
        if decision.record_type:
            identifier = g.insert(
                "decisions",
                {
                    "project_id": c.project_id,
                    "task_id": row["id"],
                    "type": decision.record_type,
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
