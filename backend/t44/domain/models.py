"""Internal semantic types, without HTTP codes or persistence representations."""

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

from t44.contracts import SPEC

if TYPE_CHECKING:
    from .commands import Command


def _semantic_enum(name, schema, *, aliases=None):
    """Adapt frozen dictionary values once while keeping the semantic Enum facade."""
    definition = SPEC["components"]["schemas"][schema]
    aliases = aliases or {}
    values = {
        aliases.get(value, value).upper(): aliases.get(value, value)
        for value in definition["x-enum-names"]
    }
    result = Enum(name, values, module=__name__)
    for value, code in zip(values.values(), definition["enum"], strict=True):
        result(value).code = code
    return result


TaskState = _semantic_enum("TaskState", "TaskState")
Action = _semantic_enum("Action", "TransitionAction", aliases={"approve_review": "accept_review"})
ProjectRole = _semantic_enum("ProjectRole", "ProjectRole")
ResponsibilityStage = _semantic_enum("ResponsibilityStage", "ResponsibilityStage")


class ReviewOutcome(Enum):
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class Effect(Enum):
    CLEAR_APPROVALS = "clear_approvals"
    ADVANCE_REVIEW_CYCLE = "advance_review_cycle"
    ADVANCE_DELIVERY_CYCLE = "advance_delivery_cycle"
    RESET_REVIEW_CYCLE = "reset_review_cycle"
    ADVANCE_SCHEDULE = "advance_schedule"
    RECORD_DELIVERY_DECISION = "record_delivery_decision"
    RECORD_ROLLBACK_DECISION = "record_rollback_decision"
    RECORD_REWORK_DECISION = "record_rework_decision"


class Violation(Enum):
    PROJECT_ACCESS_REQUIRED = "project_access_required"
    INVALID_TRANSITION = "invalid_transition"
    ROLE_FORBIDDEN = "role_forbidden"
    OWNER_REQUIRED = "owner_required"
    SELF_REVIEW_FORBIDDEN = "self_review_forbidden"
    BLOCK_REASON_REQUIRED = "block_reason_required"
    RESPONSIBILITY_STAGE_REQUIRED = "responsibility_stage_required"
    UNBLOCK_BASIS_REQUIRED = "unblock_basis_required"
    EVIDENCE_REQUIRED = "evidence_required"
    DEPENDENCIES_UNSATISFIED = "dependencies_unsatisfied"
    ARTIFACT_REQUIRED = "artifact_required"
    REVIEW_REQUIRED = "review_required"
    REVIEW_OUTCOME_MISMATCH = "review_outcome_mismatch"
    REVIEW_BASELINE_STALE = "review_baseline_stale"
    RELEASE_APPROVAL_REQUIRED = "release_approval_required"
    RELEASE_BASELINE_STALE = "release_baseline_stale"
    RELEASE_SELF_REVIEW_FORBIDDEN = "release_self_review_forbidden"
    DECISION_DETAILS_REQUIRED = "decision_details_required"
    ROLLBACK_PLAN_REQUIRED = "rollback_plan_required"
    REWORK_PLAN_REQUIRED = "rework_plan_required"


class DomainViolation(ValueError):
    """Internal rejection. A later API adapter chooses its approved HTTP mapping."""

    def __init__(self, code: Violation):
        self.code = code
        super().__init__(code.value)


def _positive_counter(value: int) -> None:
    if type(value) is not int or value < 1:
        raise ValueError("domain counters must be positive integers")


def _boolean_flags(*values: bool) -> None:
    if any(type(value) is not bool for value in values):
        raise TypeError("guard flags must be actual booleans")


BLOCKABLE = frozenset(
    {
        TaskState.PENDING,
        TaskState.DEVELOPING,
        TaskState.PENDING_REVIEW,
        TaskState.PENDING_RELEASE,
    }
)


@dataclass(frozen=True, slots=True)
class TaskPosition:
    state: TaskState
    blocked_from: TaskState | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.state, TaskState):
            raise TypeError("state must be an internal TaskState")
        if self.state is TaskState.BLOCKED:
            if self.blocked_from not in BLOCKABLE:
                raise ValueError("blocked position requires a valid previous state")
        elif self.blocked_from is not None:
            raise ValueError("only blocked positions carry a previous state")


@dataclass(frozen=True, slots=True)
class Cycle:
    delivery: int = 1
    review: int = 1

    def __post_init__(self) -> None:
        _positive_counter(self.delivery)
        _positive_counter(self.review)


@dataclass(frozen=True, slots=True)
class ReviewGate:
    reference: str
    cycle: Cycle
    artifact_reference: str
    outcome: ReviewOutcome
    evidence_complete: bool
    reviewer_is_owner: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.cycle, Cycle) or not isinstance(self.outcome, ReviewOutcome):
            raise TypeError("review proof requires internal cycle and outcome types")
        _boolean_flags(self.evidence_complete, self.reviewer_is_owner)


@dataclass(frozen=True, slots=True)
class ReleaseGate:
    reference: str
    delivery_cycle: int
    schedule_version: int
    approved: bool
    evidence_complete: bool
    rollback_plan_reviewed: bool
    reviewer_is_creator: bool = False

    def __post_init__(self) -> None:
        _positive_counter(self.delivery_cycle)
        _positive_counter(self.schedule_version)
        _boolean_flags(
            self.approved,
            self.evidence_complete,
            self.rollback_plan_reviewed,
            self.reviewer_is_creator,
        )


@dataclass(frozen=True, slots=True)
class RollbackGate:
    reference: str
    delivery_cycle: int
    approved: bool
    used_for_delivery: bool

    def __post_init__(self) -> None:
        _positive_counter(self.delivery_cycle)
        _boolean_flags(self.approved, self.used_for_delivery)


@dataclass(frozen=True, slots=True)
class TransitionContext:
    project_member: bool
    roles: frozenset[ProjectRole]
    actor_is_owner: bool = False
    dependency_states: tuple[TaskState, ...] = ()
    cycle: Cycle = field(default_factory=Cycle)
    schedule_version: int = 1
    artifact_reference: str | None = None
    latest_review_reference: str | None = None
    approved_review_reference: str | None = None
    review: ReviewGate | None = None
    release: ReleaseGate | None = None
    rollback: RollbackGate | None = None
    validated_rework_plan_reference: str | None = None

    def __post_init__(self) -> None:
        _boolean_flags(self.project_member, self.actor_is_owner)
        _positive_counter(self.schedule_version)
        if not isinstance(self.cycle, Cycle):
            raise TypeError("context requires an internal Cycle")
        if not isinstance(self.roles, frozenset) or any(
            not isinstance(role, ProjectRole) for role in self.roles
        ):
            raise TypeError("roles must be a frozen set of internal ProjectRole values")
        if not isinstance(self.dependency_states, tuple) or any(
            not isinstance(state, TaskState) for state in self.dependency_states
        ):
            raise TypeError("dependency states must be an immutable tuple of TaskState")


@dataclass(frozen=True, slots=True)
class Decision:
    source: TaskPosition
    target: TaskPosition
    action: Action
    command: "Command"
    effects: frozenset[Effect] = frozenset()
