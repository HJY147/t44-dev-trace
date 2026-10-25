"""Pure v2 rules over trusted row snapshots; no SQL, mutation or HTTP decisions."""

from .models import (
    BLOCKABLE,
    Action,
    Decision,
    DomainViolation,
    Role,
    Stage,
    State,
    Transition,
)

_RULES = {
    Action.START: ((State.PENDING,), State.DEVELOPING, None),
    Action.BLOCK: (BLOCKABLE, State.BLOCKED, None),
    Action.UNBLOCK: ((State.BLOCKED,), None, None),
    Action.SUBMIT_REVIEW: ((State.DEVELOPING,), State.PENDING_REVIEW, None),
    Action.APPROVE_REVIEW: ((State.PENDING_REVIEW,), State.PENDING_RELEASE, None),
    Action.REJECT_REVIEW: ((State.PENDING_REVIEW,), State.DEVELOPING, None),
    Action.DELIVER: ((State.PENDING_RELEASE,), State.DELIVERED, 1),
    Action.ROLLBACK: ((State.DELIVERED,), State.ROLLED_BACK, 2),
    Action.REWORK: ((State.ROLLED_BACK,), State.DEVELOPING, 3),
}
_DETAILS = {
    Action.BLOCK: ("BLOCK_REASON_REQUIRED", ("reason",)),
    Action.UNBLOCK: ("UNBLOCK_BASIS_REQUIRED", ("basis",)),
    Action.SUBMIT_REVIEW: ("ARTIFACT_REQUIRED", ("artifact_revision",)),
    Action.REJECT_REVIEW: ("DECISION_DETAILS_REQUIRED", ("reason",)),
    Action.DELIVER: ("DECISION_DETAILS_REQUIRED", ("release_version", "reason")),
    Action.ROLLBACK: ("DECISION_DETAILS_REQUIRED", ("reason", "impact", "target_version")),
    Action.REWORK: ("DECISION_DETAILS_REQUIRED", ("reason",)),
}


def _require(condition, code):
    if not condition:
        raise DomainViolation(code)


def _present(value):
    return isinstance(value, str) and bool(value.strip())


def _stage_role(state, context):
    if state == State.DEVELOPING:
        _require(Role.DEVELOPER in context.roles, "ROLE_FORBIDDEN")
        _require(context.actor_is_owner, "OWNER_REQUIRED")
    elif state == State.PENDING_REVIEW:
        _require(bool(context.roles & {Role.REVIEWER, Role.MANAGER}), "ROLE_FORBIDDEN")
    else:
        _require(Role.MANAGER in context.roles, "ROLE_FORBIDDEN")


def _review(identifier, version, accepted, context):
    review, task = context.review, context.task
    _require(review is not None and identifier, "REVIEW_REQUIRED")
    _require(
        identifier == review["id"] == task["latest_review_id"]
        and version == review["version"] == 1
        and (review["delivery_cycle"], review["review_cycle"])
        == (task["delivery_cycle"], task["review_cycle"])
        and _present(review["artifact_revision"])
        and review["artifact_revision"] == task["artifact_revision"],
        "REVIEW_BASELINE_STALE",
    )
    _require((review["verdict"] == 1) is accepted, "REVIEW_OUTCOME_MISMATCH")
    if accepted:
        _require(review["reviewer_id"] != task["owner_id"], "SELF_REVIEW_FORBIDDEN")
        _require(context.review_complete, "EVIDENCE_REQUIRED")


def decide(context: Transition) -> Decision:
    """Check membership, state, stage authorization, details, evidence, then proof rules."""
    row, body = context.task, context.body
    action, state = body["action"], row["state"]
    _require(context.project_member, "PROJECT_ACCESS_REQUIRED")
    sources, target, record_type = _RULES[action]
    _require(state in sources, "INVALID_TRANSITION")
    stage = (
        State.DEVELOPING
        if action == Action.START
        else row["blocked_from_state"]
        if action == Action.UNBLOCK
        else state
    )
    _stage_role(stage, context)
    if action in _DETAILS:
        code, names = _DETAILS[action]
        _require(all(_present(body.get(name)) for name in names), code)
    if action == Action.BLOCK:
        value = body.get("responsibility_stage")
        _require(
            type(value) is int and value in vars(Stage).values(), "RESPONSIBILITY_STAGE_REQUIRED"
        )
    if action in _DETAILS and action != Action.REJECT_REVIEW:
        _require(
            isinstance(context.evidence, tuple)
            and bool(context.evidence)
            and all(map(_present, context.evidence)),
            "EVIDENCE_REQUIRED",
        )
    if action == Action.APPROVE_REVIEW:
        _require(not context.actor_is_owner, "SELF_REVIEW_FORBIDDEN")
        _review(body.get("review_id"), body.get("review_version"), True, context)
    elif action == Action.REJECT_REVIEW:
        _review(body.get("review_id"), body.get("review_version"), False, context)
    elif action == Action.DELIVER:
        _require(row["approved_review_id"], "REVIEW_REQUIRED")
        _review(row["approved_review_id"], 1, True, context)
        assessment = context.assessment
        _require(assessment is not None, "RELEASE_APPROVAL_REQUIRED")
        _require(
            body.get("assessment_id") == assessment["id"]
            and body.get("assessment_version") == assessment["version"]
            and assessment["delivery_cycle"] == row["delivery_cycle"]
            and assessment["schedule_version"] == row["schedule_version"],
            "RELEASE_BASELINE_STALE",
        )
        _require(assessment["status"] == 2, "RELEASE_APPROVAL_REQUIRED")
        _require(
            assessment["created_by"] != assessment["reviewed_by"], "RELEASE_SELF_REVIEW_FORBIDDEN"
        )
        _require(bool(assessment["review_evidence"]), "EVIDENCE_REQUIRED")
    elif action == Action.ROLLBACK:
        assessment, delivery = context.assessment, context.delivery
        _require(
            assessment is not None
            and body.get("assessment_id")
            and body.get("rollback_plan_version"),
            "ROLLBACK_PLAN_REQUIRED",
        )
        _require(
            body["assessment_id"] == assessment["id"]
            and assessment["status"] == 2
            and delivery
            and delivery["assessment_id"] == assessment["id"]
            and delivery["rollback_plan_version"] == body["rollback_plan_version"]
            and assessment["delivery_cycle"] == row["delivery_cycle"],
            "ROLLBACK_PLAN_REQUIRED",
        )
    elif action == Action.REWORK:
        _require(context.new_plan, "REWORK_PLAN_REQUIRED")
    if action in (Action.START, Action.REWORK) or (
        action == Action.UNBLOCK and stage == State.DEVELOPING
    ):
        _require(
            all(state == State.DELIVERED for state in context.dependency_states),
            "DEPENDENCIES_UNSATISFIED",
        )
    values = {
        "state": target or stage,
        "blocked_from_state": state if action == Action.BLOCK else None,
        "block_reason": body["reason"] if action == Action.BLOCK else None,
        "responsibility_stage": body["responsibility_stage"] if action == Action.BLOCK else None,
    }
    if action == Action.SUBMIT_REVIEW:
        values["artifact_revision"] = body["artifact_revision"]
    if action == Action.APPROVE_REVIEW:
        values["approved_review_id"] = body["review_id"]
    if action in (Action.REJECT_REVIEW, Action.REWORK):
        values.update(
            latest_review_id=None,
            approved_review_id=None,
            approved_assessment_id=None,
            approved_assessment_version=None,
            artifact_revision=None,
        )
    if action == Action.REJECT_REVIEW:
        values["review_cycle"] = row["review_cycle"] + 1
    if action == Action.REWORK:
        values.update(
            delivery_cycle=row["delivery_cycle"] + 1,
            review_cycle=1,
            schedule_version=row["schedule_version"] + 1,
            **context.new_plan,
        )
    return Decision(values, record_type)
