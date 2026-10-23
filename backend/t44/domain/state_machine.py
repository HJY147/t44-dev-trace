"""Decide permitted domain changes without mutating a task or touching infrastructure."""

from typing import cast

from .commands import (
    AcceptReview,
    ApproveDelivery,
    AuthorizeRework,
    Command,
    RecordBlock,
    RecordRollback,
    ResolveBlock,
    ReturnForChanges,
    StartDevelopment,
    SubmitForReview,
)
from .models import (
    BLOCKABLE,
    Action,
    Decision,
    DomainViolation,
    Effect,
    GuardContext,
    ProjectRole,
    ReleaseGate,
    ResponsibilityStage,
    ReviewGate,
    ReviewOutcome,
    RollbackGate,
    TaskPosition,
    TaskState,
    Violation,
)


def _require(condition: bool, code: Violation) -> None:
    if not condition:
        raise DomainViolation(code)


def _present(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _evidence(values: tuple[str, ...]) -> None:
    _require(
        isinstance(values, tuple) and bool(values) and all(map(_present, values)),
        Violation.EVIDENCE_REQUIRED,
    )


def _stage_role(state: TaskState, context: GuardContext) -> None:
    if state is TaskState.DEVELOPING:
        _require(ProjectRole.DEVELOPER in context.roles, Violation.ROLE_FORBIDDEN)
        _require(context.actor_is_owner, Violation.OWNER_REQUIRED)
    elif state is TaskState.PENDING_REVIEW:
        _require(
            bool(context.roles & {ProjectRole.REVIEWER, ProjectRole.MANAGER}),
            Violation.ROLE_FORBIDDEN,
        )
    else:
        _require(ProjectRole.MANAGER in context.roles, Violation.ROLE_FORBIDDEN)


def _dependencies(context: GuardContext) -> None:
    _require(
        all(state is TaskState.DELIVERED for state in context.dependency_states),
        Violation.DEPENDENCIES_UNSATISFIED,
    )


def _review(reference: str, outcome: ReviewOutcome, context: GuardContext) -> ReviewGate:
    gate = context.review
    _require(gate is not None and _present(reference), Violation.REVIEW_REQUIRED)
    gate = cast(ReviewGate, gate)  # Runtime rejection above remains active under python -O.
    _require(
        reference == gate.reference == context.latest_review_reference
        and gate.cycle == context.cycle
        and _present(gate.artifact_reference)
        and gate.artifact_reference == context.artifact_reference,
        Violation.REVIEW_BASELINE_STALE,
    )
    _require(gate.outcome is outcome, Violation.REVIEW_OUTCOME_MISMATCH)
    if outcome is ReviewOutcome.ACCEPTED:
        _require(not gate.reviewer_is_owner, Violation.SELF_REVIEW_FORBIDDEN)
        _require(gate.evidence_complete, Violation.EVIDENCE_REQUIRED)
    return gate


def decide(position: TaskPosition, command: Command, context: GuardContext) -> Decision:
    """Return an immutable decision; never apply it or map errors to HTTP.

    Transaction/CAS, audit, idempotency, plan parsing and proof loading belong to a later
    facade. This function cannot be used as evidence that those concerns are implemented.
    """
    _require(context.project_member is True, Violation.PROJECT_ACCESS_REQUIRED)
    state = position.state
    effects: frozenset[Effect] = frozenset()

    if isinstance(command, StartDevelopment):
        _require(state is TaskState.PENDING, Violation.INVALID_TRANSITION)
        _stage_role(TaskState.DEVELOPING, context)
        _dependencies(context)
        action, target = Action.START, TaskPosition(TaskState.DEVELOPING)
    elif isinstance(command, RecordBlock):
        _require(state in BLOCKABLE, Violation.INVALID_TRANSITION)
        _stage_role(state, context)
        _require(_present(command.reason), Violation.BLOCK_REASON_REQUIRED)
        _require(
            isinstance(command.responsibility_stage, ResponsibilityStage),
            Violation.RESPONSIBILITY_STAGE_REQUIRED,
        )
        _evidence(command.evidence)
        action, target = Action.BLOCK, TaskPosition(TaskState.BLOCKED, state)
    elif isinstance(command, ResolveBlock):
        _require(state is TaskState.BLOCKED, Violation.INVALID_TRANSITION)
        previous = cast(TaskState, position.blocked_from)  # TaskPosition enforces this invariant.
        _stage_role(previous, context)
        _require(_present(command.basis), Violation.UNBLOCK_BASIS_REQUIRED)
        _evidence(command.evidence)
        if previous is TaskState.DEVELOPING:
            _dependencies(context)
        action, target = Action.UNBLOCK, TaskPosition(previous)
    elif isinstance(command, SubmitForReview):
        _require(state is TaskState.DEVELOPING, Violation.INVALID_TRANSITION)
        _stage_role(state, context)
        _require(_present(command.artifact_reference), Violation.ARTIFACT_REQUIRED)
        _evidence(command.evidence)
        action, target = Action.SUBMIT_REVIEW, TaskPosition(TaskState.PENDING_REVIEW)
    elif isinstance(command, AcceptReview):
        _require(state is TaskState.PENDING_REVIEW, Violation.INVALID_TRANSITION)
        _stage_role(state, context)
        _require(not context.actor_is_owner, Violation.SELF_REVIEW_FORBIDDEN)
        _review(command.review_reference, ReviewOutcome.ACCEPTED, context)
        action, target = Action.ACCEPT_REVIEW, TaskPosition(TaskState.PENDING_RELEASE)
    elif isinstance(command, ReturnForChanges):
        _require(state is TaskState.PENDING_REVIEW, Violation.INVALID_TRANSITION)
        _stage_role(state, context)
        _require(_present(command.reason), Violation.DECISION_DETAILS_REQUIRED)
        _review(command.review_reference, ReviewOutcome.REJECTED, context)
        effects = frozenset({Effect.ADVANCE_REVIEW_CYCLE, Effect.CLEAR_APPROVALS})
        action, target = Action.REJECT_REVIEW, TaskPosition(TaskState.DEVELOPING)
    elif isinstance(command, ApproveDelivery):
        _require(state is TaskState.PENDING_RELEASE, Violation.INVALID_TRANSITION)
        _stage_role(state, context)
        _require(
            _present(command.release_reference) and _present(command.reason),
            Violation.DECISION_DETAILS_REQUIRED,
        )
        _evidence(command.evidence)
        _require(_present(context.approved_review_reference), Violation.REVIEW_REQUIRED)
        _review(context.approved_review_reference or "", ReviewOutcome.ACCEPTED, context)
        release = context.release
        _require(release is not None, Violation.RELEASE_APPROVAL_REQUIRED)
        release = cast(ReleaseGate, release)
        _require(
            command.assessment_reference == release.reference
            and _present(command.assessment_reference)
            and release.delivery_cycle == context.cycle.delivery
            and release.schedule_version == context.schedule_version,
            Violation.RELEASE_BASELINE_STALE,
        )
        _require(
            release.approved and release.rollback_plan_reviewed, Violation.RELEASE_APPROVAL_REQUIRED
        )
        _require(not release.reviewer_is_creator, Violation.RELEASE_SELF_REVIEW_FORBIDDEN)
        _require(release.evidence_complete, Violation.EVIDENCE_REQUIRED)
        effects = frozenset({Effect.RECORD_DELIVERY_DECISION})
        action, target = Action.DELIVER, TaskPosition(TaskState.DELIVERED)
    elif isinstance(command, RecordRollback):
        _require(state is TaskState.DELIVERED, Violation.INVALID_TRANSITION)
        _stage_role(state, context)
        _require(
            all(map(_present, (command.reason, command.impact, command.target_reference))),
            Violation.DECISION_DETAILS_REQUIRED,
        )
        _evidence(command.evidence)
        rollback = context.rollback
        _require(
            rollback is not None and _present(command.rollback_plan_reference),
            Violation.ROLLBACK_PLAN_REQUIRED,
        )
        rollback = cast(RollbackGate, rollback)
        _require(
            command.rollback_plan_reference == rollback.reference
            and rollback.approved
            and rollback.used_for_delivery
            and rollback.delivery_cycle == context.cycle.delivery,
            Violation.ROLLBACK_PLAN_REQUIRED,
        )
        effects = frozenset({Effect.RECORD_ROLLBACK_DECISION})
        action, target = Action.ROLLBACK, TaskPosition(TaskState.ROLLED_BACK)
    elif isinstance(command, AuthorizeRework):
        _require(state is TaskState.ROLLED_BACK, Violation.INVALID_TRANSITION)
        _stage_role(state, context)
        _require(_present(command.reason), Violation.DECISION_DETAILS_REQUIRED)
        _evidence(command.evidence)
        _require(
            _present(command.new_plan_reference)
            and command.new_plan_reference == context.validated_rework_plan_reference,
            Violation.REWORK_PLAN_REQUIRED,
        )
        _dependencies(context)
        effects = frozenset(
            {
                Effect.ADVANCE_DELIVERY_CYCLE,
                Effect.RESET_REVIEW_CYCLE,
                Effect.ADVANCE_SCHEDULE,
                Effect.CLEAR_APPROVALS,
                Effect.RECORD_REWORK_DECISION,
            }
        )
        action, target = Action.REWORK, TaskPosition(TaskState.DEVELOPING)
    else:
        raise TypeError("unsupported internal transition command")

    return Decision(position, target, action, command, effects)
