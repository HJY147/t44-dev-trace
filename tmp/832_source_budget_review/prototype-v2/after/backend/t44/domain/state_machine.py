"""Decide permitted domain changes without mutating a task or touching infrastructure."""

from typing import cast

from . import commands as domain_commands
from . import models as domain_models


def _require(condition: bool, code: domain_models.Violation) -> None:
    if not condition:
        raise domain_models.DomainViolation(code)


def _present(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _evidence(values: tuple[str, ...]) -> None:
    _require(
        isinstance(values, tuple) and bool(values) and all(map(_present, values)),
        domain_models.Violation.EVIDENCE_REQUIRED,
    )


def _stage_role(state: domain_models.TaskState, context: domain_models.TransitionContext) -> None:
    if state is domain_models.TaskState.DEVELOPING:
        _require(
            domain_models.ProjectRole.DEVELOPER in context.roles,
            domain_models.Violation.ROLE_FORBIDDEN,
        )
        _require(context.actor_is_owner, domain_models.Violation.OWNER_REQUIRED)
    elif state is domain_models.TaskState.PENDING_REVIEW:
        _require(
            bool(
                context.roles
                & {domain_models.ProjectRole.REVIEWER, domain_models.ProjectRole.MANAGER}
            ),
            domain_models.Violation.ROLE_FORBIDDEN,
        )
    else:
        _require(
            domain_models.ProjectRole.MANAGER in context.roles,
            domain_models.Violation.ROLE_FORBIDDEN,
        )


def _dependencies(context: domain_models.TransitionContext) -> None:
    _require(
        all(state is domain_models.TaskState.DELIVERED for state in context.dependency_states),
        domain_models.Violation.DEPENDENCIES_UNSATISFIED,
    )


def _review(
    reference: str, outcome: domain_models.ReviewOutcome, context: domain_models.TransitionContext
) -> domain_models.ReviewGate:
    gate = context.review
    _require(gate is not None and _present(reference), domain_models.Violation.REVIEW_REQUIRED)
    gate = cast(
        domain_models.ReviewGate, gate
    )  # Runtime rejection above remains active under python -O.
    _require(
        reference == gate.reference == context.latest_review_reference
        and gate.cycle == context.cycle
        and _present(gate.artifact_reference)
        and gate.artifact_reference == context.artifact_reference,
        domain_models.Violation.REVIEW_BASELINE_STALE,
    )
    _require(gate.outcome is outcome, domain_models.Violation.REVIEW_OUTCOME_MISMATCH)
    if outcome is domain_models.ReviewOutcome.ACCEPTED:
        _require(not gate.reviewer_is_owner, domain_models.Violation.SELF_REVIEW_FORBIDDEN)
        _require(gate.evidence_complete, domain_models.Violation.EVIDENCE_REQUIRED)
    return gate


def decide(
    position: domain_models.TaskPosition,
    command: domain_commands.Command,
    context: domain_models.TransitionContext,
) -> domain_models.Decision:
    """Return an immutable decision; never apply it or map errors to HTTP.

    Transaction/CAS, audit, idempotency, plan parsing and proof loading belong to a later
    facade. This function cannot be used as evidence that those concerns are implemented.
    """
    _require(context.project_member is True, domain_models.Violation.PROJECT_ACCESS_REQUIRED)
    state = position.state
    effects: frozenset[domain_models.Effect] = frozenset()

    if isinstance(command, domain_commands.StartDevelopment):
        _require(
            state is domain_models.TaskState.PENDING, domain_models.Violation.INVALID_TRANSITION
        )
        _stage_role(domain_models.TaskState.DEVELOPING, context)
        _dependencies(context)
        action, target = (
            domain_models.Action.START,
            domain_models.TaskPosition(domain_models.TaskState.DEVELOPING),
        )
    elif isinstance(command, domain_commands.RecordBlock):
        _require(state in domain_models.BLOCKABLE, domain_models.Violation.INVALID_TRANSITION)
        _stage_role(state, context)
        _require(_present(command.reason), domain_models.Violation.BLOCK_REASON_REQUIRED)
        _require(
            isinstance(command.responsibility_stage, domain_models.ResponsibilityStage),
            domain_models.Violation.RESPONSIBILITY_STAGE_REQUIRED,
        )
        _evidence(command.evidence)
        action, target = (
            domain_models.Action.BLOCK,
            domain_models.TaskPosition(domain_models.TaskState.BLOCKED, state),
        )
    elif isinstance(command, domain_commands.ResolveBlock):
        _require(
            state is domain_models.TaskState.BLOCKED, domain_models.Violation.INVALID_TRANSITION
        )
        previous = cast(
            domain_models.TaskState, position.blocked_from
        )  # TaskPosition enforces this invariant.
        _stage_role(previous, context)
        _require(_present(command.basis), domain_models.Violation.UNBLOCK_BASIS_REQUIRED)
        _evidence(command.evidence)
        if previous is domain_models.TaskState.DEVELOPING:
            _dependencies(context)
        action, target = domain_models.Action.UNBLOCK, domain_models.TaskPosition(previous)
    elif isinstance(command, domain_commands.SubmitForReview):
        _require(
            state is domain_models.TaskState.DEVELOPING, domain_models.Violation.INVALID_TRANSITION
        )
        _stage_role(state, context)
        _require(_present(command.artifact_reference), domain_models.Violation.ARTIFACT_REQUIRED)
        _evidence(command.evidence)
        action, target = (
            domain_models.Action.SUBMIT_REVIEW,
            domain_models.TaskPosition(domain_models.TaskState.PENDING_REVIEW),
        )
    elif isinstance(command, domain_commands.AcceptReview):
        _require(
            state is domain_models.TaskState.PENDING_REVIEW,
            domain_models.Violation.INVALID_TRANSITION,
        )
        _stage_role(state, context)
        _require(not context.actor_is_owner, domain_models.Violation.SELF_REVIEW_FORBIDDEN)
        _review(command.review_reference, domain_models.ReviewOutcome.ACCEPTED, context)
        action, target = (
            domain_models.Action.ACCEPT_REVIEW,
            domain_models.TaskPosition(domain_models.TaskState.PENDING_RELEASE),
        )
    elif isinstance(command, domain_commands.ReturnForChanges):
        _require(
            state is domain_models.TaskState.PENDING_REVIEW,
            domain_models.Violation.INVALID_TRANSITION,
        )
        _stage_role(state, context)
        _require(_present(command.reason), domain_models.Violation.DECISION_DETAILS_REQUIRED)
        _review(command.review_reference, domain_models.ReviewOutcome.REJECTED, context)
        effects = frozenset(
            {domain_models.Effect.ADVANCE_REVIEW_CYCLE, domain_models.Effect.CLEAR_APPROVALS}
        )
        action, target = (
            domain_models.Action.REJECT_REVIEW,
            domain_models.TaskPosition(domain_models.TaskState.DEVELOPING),
        )
    elif isinstance(command, domain_commands.ApproveDelivery):
        _require(
            state is domain_models.TaskState.PENDING_RELEASE,
            domain_models.Violation.INVALID_TRANSITION,
        )
        _stage_role(state, context)
        _require(
            _present(command.release_reference) and _present(command.reason),
            domain_models.Violation.DECISION_DETAILS_REQUIRED,
        )
        _evidence(command.evidence)
        _require(
            _present(context.approved_review_reference), domain_models.Violation.REVIEW_REQUIRED
        )
        _review(
            context.approved_review_reference or "", domain_models.ReviewOutcome.ACCEPTED, context
        )
        release = context.release
        _require(release is not None, domain_models.Violation.RELEASE_APPROVAL_REQUIRED)
        release = cast(domain_models.ReleaseGate, release)
        _require(
            command.assessment_reference == release.reference
            and _present(command.assessment_reference)
            and release.delivery_cycle == context.cycle.delivery
            and release.schedule_version == context.schedule_version,
            domain_models.Violation.RELEASE_BASELINE_STALE,
        )
        _require(
            release.approved and release.rollback_plan_reviewed,
            domain_models.Violation.RELEASE_APPROVAL_REQUIRED,
        )
        _require(
            not release.reviewer_is_creator, domain_models.Violation.RELEASE_SELF_REVIEW_FORBIDDEN
        )
        _require(release.evidence_complete, domain_models.Violation.EVIDENCE_REQUIRED)
        effects = frozenset({domain_models.Effect.RECORD_DELIVERY_DECISION})
        action, target = (
            domain_models.Action.DELIVER,
            domain_models.TaskPosition(domain_models.TaskState.DELIVERED),
        )
    elif isinstance(command, domain_commands.RecordRollback):
        _require(
            state is domain_models.TaskState.DELIVERED, domain_models.Violation.INVALID_TRANSITION
        )
        _stage_role(state, context)
        _require(
            all(map(_present, (command.reason, command.impact, command.target_reference))),
            domain_models.Violation.DECISION_DETAILS_REQUIRED,
        )
        _evidence(command.evidence)
        rollback = context.rollback
        _require(
            rollback is not None and _present(command.rollback_plan_reference),
            domain_models.Violation.ROLLBACK_PLAN_REQUIRED,
        )
        rollback = cast(domain_models.RollbackGate, rollback)
        _require(
            command.rollback_plan_reference == rollback.reference
            and rollback.approved
            and rollback.used_for_delivery
            and rollback.delivery_cycle == context.cycle.delivery,
            domain_models.Violation.ROLLBACK_PLAN_REQUIRED,
        )
        effects = frozenset({domain_models.Effect.RECORD_ROLLBACK_DECISION})
        action, target = (
            domain_models.Action.ROLLBACK,
            domain_models.TaskPosition(domain_models.TaskState.ROLLED_BACK),
        )
    elif isinstance(command, domain_commands.AuthorizeRework):
        _require(
            state is domain_models.TaskState.ROLLED_BACK, domain_models.Violation.INVALID_TRANSITION
        )
        _stage_role(state, context)
        _require(_present(command.reason), domain_models.Violation.DECISION_DETAILS_REQUIRED)
        _evidence(command.evidence)
        _require(
            _present(command.new_plan_reference)
            and command.new_plan_reference == context.validated_rework_plan_reference,
            domain_models.Violation.REWORK_PLAN_REQUIRED,
        )
        _dependencies(context)
        effects = frozenset(
            {
                domain_models.Effect.ADVANCE_DELIVERY_CYCLE,
                domain_models.Effect.RESET_REVIEW_CYCLE,
                domain_models.Effect.ADVANCE_SCHEDULE,
                domain_models.Effect.CLEAR_APPROVALS,
                domain_models.Effect.RECORD_REWORK_DECISION,
            }
        )
        action, target = (
            domain_models.Action.REWORK,
            domain_models.TaskPosition(domain_models.TaskState.DEVELOPING),
        )
    else:
        raise TypeError("unsupported internal transition command")

    return domain_models.Decision(position, target, action, command, effects)
