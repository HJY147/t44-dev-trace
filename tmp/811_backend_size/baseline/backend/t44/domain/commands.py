"""Typed internal commands; callers cannot supply a target state.

References are opaque domain references. Their storage and HTTP formats are intentionally
not selected here. A transaction facade must resolve them into trusted guard context.
"""

from dataclasses import dataclass

from .models import ResponsibilityStage


@dataclass(frozen=True, slots=True)
class StartDevelopment:
    """Begin work with ownership and dependencies from the trusted context."""


@dataclass(frozen=True, slots=True)
class RecordBlock:
    reason: str
    responsibility_stage: ResponsibilityStage
    evidence: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ResolveBlock:
    basis: str
    evidence: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class SubmitForReview:
    artifact_reference: str
    evidence: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class AcceptReview:
    review_reference: str


@dataclass(frozen=True, slots=True)
class ReturnForChanges:
    review_reference: str
    reason: str


@dataclass(frozen=True, slots=True)
class ApproveDelivery:
    assessment_reference: str
    release_reference: str
    reason: str
    evidence: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class RecordRollback:
    reason: str
    impact: str
    target_reference: str
    rollback_plan_reference: str
    evidence: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class AuthorizeRework:
    new_plan_reference: str
    reason: str
    evidence: tuple[str, ...]


type Command = (
    StartDevelopment
    | RecordBlock
    | ResolveBlock
    | SubmitForReview
    | AcceptReview
    | ReturnForChanges
    | ApproveDelivery
    | RecordRollback
    | AuthorizeRework
)
