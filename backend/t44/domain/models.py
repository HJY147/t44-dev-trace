"""Internal v2: validated trusted row views and immutable pure transition decisions."""

from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType

from t44.contracts import SPEC


def _dictionary(name):
    schema = SPEC["components"]["schemas"][name]
    pairs = tuple(zip(schema["x-enum-names"], schema["enum"], strict=True))
    # Semantic enum views remain available for display; storage constants never depend on iteration.
    semantic = Enum(name, {label.upper(): label for label, _ in pairs}, module=__name__)
    codes = type(name, (), {label.upper(): code for label, code in pairs})
    return semantic, codes


TaskState, State = _dictionary("TaskState")
_TransitionAction, Action = _dictionary("TransitionAction")
ProjectRole, Role = _dictionary("ProjectRole")
ResponsibilityStage, Stage = _dictionary("ResponsibilityStage")
BLOCKABLE = frozenset(
    {State.PENDING, State.DEVELOPING, State.PENDING_REVIEW, State.PENDING_RELEASE}
)


class DomainViolation(ValueError):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


def _counter(value):
    if type(value) is not int or value < 1:
        raise ValueError("domain counters must be positive integers")


@dataclass(frozen=True, slots=True)
class Transition:
    task: Mapping
    body: Mapping
    roles: frozenset[int]
    actor_is_owner: bool = False
    evidence: tuple[str, ...] = ()
    dependency_states: tuple[int, ...] = ()
    review: Mapping | None = None
    assessment: Mapping | None = None
    delivery: Mapping | None = None
    review_complete: bool = False
    project_member: bool = True
    new_plan: Mapping | None = None

    def __post_init__(self):
        if any(
            type(value) is not bool
            for value in (
                self.actor_is_owner,
                self.review_complete,
                self.project_member,
            )
        ):
            raise TypeError("guard flags must be actual booleans")
        if not isinstance(self.roles, frozenset) or any(
            type(role) is not int or role not in (Role.MANAGER, Role.DEVELOPER, Role.REVIEWER)
            for role in self.roles
        ):
            raise TypeError("roles must be a frozen set of internal role codes")
        if not isinstance(self.dependency_states, tuple) or any(
            type(state) is not int or state not in range(1, 8) for state in self.dependency_states
        ):
            raise TypeError("dependency states must be an immutable tuple of state codes")
        for field in ("task", "body", "review", "assessment", "delivery", "new_plan"):
            row = getattr(self, field)
            if row is None and field not in ("task", "body"):
                continue
            if not isinstance(row, Mapping):
                raise TypeError("trusted rows must be mappings")
            object.__setattr__(self, field, MappingProxyType(dict(row)))
        state, previous = self.task["state"], self.task["blocked_from_state"]
        if type(state) is not int or state not in range(1, 8):
            raise TypeError("state must be an internal state code")
        if (
            state == State.BLOCKED and (type(previous) is not int or previous not in BLOCKABLE)
        ) or (state != State.BLOCKED and previous is not None):
            raise ValueError("blocked position requires its valid previous state exclusively")
        if type(self.body["action"]) is not int or self.body["action"] not in range(1, 10):
            raise TypeError("unsupported internal transition action")
        for row, counters in (
            (self.task, ("delivery_cycle", "review_cycle", "schedule_version")),
            (self.review, ("delivery_cycle", "review_cycle")),
            (self.assessment, ("delivery_cycle", "schedule_version")),
        ):
            if row is not None:
                for counter in counters:
                    _counter(row[counter])
        for row, fields in (
            (self.task, ("id", "owner_id")),
            (self.review, ("id", "version", "reviewer_id", "verdict")),
            (self.assessment, ("id", "version", "status", "created_by", "reviewed_by")),
            (self.delivery, ("assessment_id", "rollback_plan_version")),
        ):
            if row is not None and any(
                field in row and row[field] is not None and type(row[field]) is not int
                for field in fields
            ):
                raise TypeError("trusted row identities and statuses must be integer codes")
        if (
            self.assessment is not None
            and "review_evidence" in self.assessment
            and not isinstance(self.assessment["review_evidence"], (list, tuple))
        ):
            raise TypeError("assessment evidence must be a collection")
        if self.assessment is not None and "review_evidence" in self.assessment:
            values = {
                **self.assessment,
                "review_evidence": tuple(self.assessment["review_evidence"]),
            }
            object.__setattr__(self, "assessment", MappingProxyType(values))


@dataclass(frozen=True, slots=True)
class Decision:
    values: Mapping
    record_type: int | None = None

    def __post_init__(self):
        object.__setattr__(self, "values", MappingProxyType(dict(self.values)))
