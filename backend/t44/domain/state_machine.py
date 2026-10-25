"""Decide permitted domain changes without mutating a task or touching infrastructure."""

from typing import cast

from t44.domain import commands as cmd
from t44.domain import models as domain


def _require(condition: bool, code: domain.Violation) -> None:
    if not condition:
        raise domain.DomainViolation(code)


def _present(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _evidence(values: tuple[str, ...]) -> None:
    _require(
        isinstance(values, tuple) and bool(values) and all(map(_present, values)),
        domain.Violation.EVIDENCE_REQUIRED,
    )


def _stage_role(state: domain.TaskState, context: domain.TransitionContext) -> None:
    if state is domain.TaskState.DEVELOPING:
        _require(domain.ProjectRole.DEVELOPER in context.roles, domain.Violation.ROLE_FORBIDDEN)
        _require(context.actor_is_owner, domain.Violation.OWNER_REQUIRED)
    elif state is domain.TaskState.PENDING_REVIEW:
        _require(
            bool(context.roles & {domain.ProjectRole.REVIEWER, domain.ProjectRole.MANAGER}),
            domain.Violation.ROLE_FORBIDDEN,
        )
    else:
        _require(domain.ProjectRole.MANAGER in context.roles, domain.Violation.ROLE_FORBIDDEN)


def _dependencies(context: domain.TransitionContext) -> None:
    _require(
        all(state is domain.TaskState.DELIVERED for state in context.dependency_states),
        domain.Violation.DEPENDENCIES_UNSATISFIED,
    )


def _review(
    reference: str, outcome: domain.ReviewOutcome, context: domain.TransitionContext
) -> domain.ReviewGate:
    gate = context.review
    _require(gate is not None and _present(reference), domain.Violation.REVIEW_REQUIRED)
    gate = cast(domain.ReviewGate, gate)  # Runtime rejection above remains active under python -O.
    _require(
        reference == gate.reference == context.latest_review_reference
        and gate.cycle == context.cycle
        and _present(gate.artifact_reference)
        and gate.artifact_reference == context.artifact_reference,
        domain.Violation.REVIEW_BASELINE_STALE,
    )
    _require(gate.outcome is outcome, domain.Violation.REVIEW_OUTCOME_MISMATCH)
    if outcome is domain.ReviewOutcome.ACCEPTED:
        _require(not gate.reviewer_is_owner, domain.Violation.SELF_REVIEW_FORBIDDEN)
        _require(gate.evidence_complete, domain.Violation.EVIDENCE_REQUIRED)
    return gate


# One transition definition owns the fixed source, action and target. Blocking keeps its origin.
_RULES = {
    cmd.StartDevelopment: (
        (domain.TaskState.PENDING,),
        domain.Action.START,
        domain.TaskState.DEVELOPING,
    ),
    cmd.RecordBlock: (domain.BLOCKABLE, domain.Action.BLOCK, domain.TaskState.BLOCKED),
    cmd.ResolveBlock: ((domain.TaskState.BLOCKED,), domain.Action.UNBLOCK, None),
    cmd.SubmitForReview: (
        (domain.TaskState.DEVELOPING,),
        domain.Action.SUBMIT_REVIEW,
        domain.TaskState.PENDING_REVIEW,
    ),
    cmd.AcceptReview: (
        (domain.TaskState.PENDING_REVIEW,),
        domain.Action.ACCEPT_REVIEW,
        domain.TaskState.PENDING_RELEASE,
    ),
    cmd.ReturnForChanges: (
        (domain.TaskState.PENDING_REVIEW,),
        domain.Action.REJECT_REVIEW,
        domain.TaskState.DEVELOPING,
    ),
    cmd.ApproveDelivery: (
        (domain.TaskState.PENDING_RELEASE,),
        domain.Action.DELIVER,
        domain.TaskState.DELIVERED,
    ),
    cmd.RecordRollback: (
        (domain.TaskState.DELIVERED,),
        domain.Action.ROLLBACK,
        domain.TaskState.ROLLED_BACK,
    ),
    cmd.AuthorizeRework: (
        (domain.TaskState.ROLLED_BACK,),
        domain.Action.REWORK,
        domain.TaskState.DEVELOPING,
    ),
}


# Ordered command prerequisites precede evidence, then proof/dependency validation.
_DETAILS = {
    cmd.RecordBlock: (domain.Violation.BLOCK_REASON_REQUIRED, ("reason",)),
    cmd.ResolveBlock: (domain.Violation.UNBLOCK_BASIS_REQUIRED, ("basis",)),
    cmd.SubmitForReview: (domain.Violation.ARTIFACT_REQUIRED, ("artifact_reference",)),
    cmd.ReturnForChanges: (domain.Violation.DECISION_DETAILS_REQUIRED, ("reason",)),
    cmd.ApproveDelivery: (
        domain.Violation.DECISION_DETAILS_REQUIRED,
        ("release_reference", "reason"),
    ),
    cmd.RecordRollback: (
        domain.Violation.DECISION_DETAILS_REQUIRED,
        ("reason", "impact", "target_reference"),
    ),
    cmd.AuthorizeRework: (domain.Violation.DECISION_DETAILS_REQUIRED, ("reason",)),
}


def decide(
    position: domain.TaskPosition, command: cmd.Command, context: domain.TransitionContext
) -> domain.Decision:
    """Return an immutable decision; never apply it or map errors to HTTP.

    Transaction/CAS, audit, idempotency, plan parsing and proof loading belong to a later
    facade. This function cannot be used as evidence that those concerns are implemented.
    """
    _require(context.project_member is True, domain.Violation.PROJECT_ACCESS_REQUIRED)
    selected = next(
        ((kind, rule) for kind, rule in _RULES.items() if isinstance(command, kind)), None
    )
    if selected is None:
        raise TypeError("unsupported internal transition command")
    kind, (sources, action, target) = selected
    state = position.state
    _require(state in sources, domain.Violation.INVALID_TRANSITION)
    stage = (
        domain.TaskState.DEVELOPING
        if isinstance(command, cmd.StartDevelopment)
        else cast(domain.TaskState, position.blocked_from)
        if isinstance(command, cmd.ResolveBlock)
        else state
    )
    _stage_role(stage, context)
    effects: frozenset[domain.Effect] = frozenset()

    details = _DETAILS.get(kind)
    if details:
        code, names = details
        _require(all(_present(getattr(command, name)) for name in names), code)
    if kind is cmd.RecordBlock:
        _require(
            isinstance(command.responsibility_stage, domain.ResponsibilityStage),
            domain.Violation.RESPONSIBILITY_STAGE_REQUIRED,
        )
    if kind in _DETAILS and kind is not cmd.ReturnForChanges:
        _evidence(command.evidence)

    if isinstance(command, cmd.StartDevelopment):
        _dependencies(context)
    elif isinstance(command, cmd.ResolveBlock):
        if stage is domain.TaskState.DEVELOPING:
            _dependencies(context)
    elif isinstance(command, cmd.AcceptReview):
        _require(not context.actor_is_owner, domain.Violation.SELF_REVIEW_FORBIDDEN)
        _review(command.review_reference, domain.ReviewOutcome.ACCEPTED, context)
    elif isinstance(command, cmd.ReturnForChanges):
        _review(command.review_reference, domain.ReviewOutcome.REJECTED, context)
        effects = frozenset({domain.Effect.ADVANCE_REVIEW_CYCLE, domain.Effect.CLEAR_APPROVALS})
    elif isinstance(command, cmd.ApproveDelivery):
        _require(_present(context.approved_review_reference), domain.Violation.REVIEW_REQUIRED)
        _review(context.approved_review_reference or "", domain.ReviewOutcome.ACCEPTED, context)
        release = context.release
        _require(release is not None, domain.Violation.RELEASE_APPROVAL_REQUIRED)
        release = cast(domain.ReleaseGate, release)
        _require(
            command.assessment_reference == release.reference
            and _present(command.assessment_reference)
            and release.delivery_cycle == context.cycle.delivery
            and release.schedule_version == context.schedule_version,
            domain.Violation.RELEASE_BASELINE_STALE,
        )
        _require(
            release.approved and release.rollback_plan_reviewed,
            domain.Violation.RELEASE_APPROVAL_REQUIRED,
        )
        _require(not release.reviewer_is_creator, domain.Violation.RELEASE_SELF_REVIEW_FORBIDDEN)
        _require(release.evidence_complete, domain.Violation.EVIDENCE_REQUIRED)
        effects = frozenset({domain.Effect.RECORD_DELIVERY_DECISION})
    elif isinstance(command, cmd.RecordRollback):
        rollback = context.rollback
        _require(
            rollback is not None and _present(command.rollback_plan_reference),
            domain.Violation.ROLLBACK_PLAN_REQUIRED,
        )
        rollback = cast(domain.RollbackGate, rollback)
        _require(
            command.rollback_plan_reference == rollback.reference
            and rollback.approved
            and rollback.used_for_delivery
            and rollback.delivery_cycle == context.cycle.delivery,
            domain.Violation.ROLLBACK_PLAN_REQUIRED,
        )
        effects = frozenset({domain.Effect.RECORD_ROLLBACK_DECISION})
    elif isinstance(command, cmd.AuthorizeRework):
        _require(
            _present(command.new_plan_reference)
            and command.new_plan_reference == context.validated_rework_plan_reference,
            domain.Violation.REWORK_PLAN_REQUIRED,
        )
        _dependencies(context)
        effects = frozenset(
            {
                domain.Effect.ADVANCE_DELIVERY_CYCLE,
                domain.Effect.RESET_REVIEW_CYCLE,
                domain.Effect.ADVANCE_SCHEDULE,
                domain.Effect.CLEAR_APPROVALS,
                domain.Effect.RECORD_REWORK_DECISION,
            }
        )
    target = (
        domain.TaskPosition(target, state)
        if action is domain.Action.BLOCK
        else domain.TaskPosition(target or stage)
    )
    return domain.Decision(position, target, action, command, effects)
