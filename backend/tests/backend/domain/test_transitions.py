"""Business-path unit tests, without API, database, broker or scheduler substitutes."""

from dataclasses import FrozenInstanceError, replace

import pytest
from t44.domain import (
    AcceptReview,
    ApproveDelivery,
    AuthorizeRework,
    Cycle,
    DomainViolation,
    Effect,
    ProjectRole,
    RecordBlock,
    RecordRollback,
    ReleaseGate,
    ResolveBlock,
    ResponsibilityStage,
    ReturnForChanges,
    ReviewGate,
    ReviewOutcome,
    RollbackGate,
    StartDevelopment,
    SubmitForReview,
    TaskPosition,
    TaskState,
    TransitionContext,
    Violation,
    decide,
)

PROOF = ("fixed-evidence-reference",)
BLOCK = RecordBlock("external service unavailable", ResponsibilityStage.EXTERNAL_DEPENDENCY, PROOF)
UNBLOCK = ResolveBlock("external service verified available", PROOF)
SUBMIT = SubmitForReview("fixed-source-revision", PROOF)
ACCEPT = AcceptReview("review-A")
REJECT = ReturnForChanges("review-A", "required checks failed")
DELIVER = ApproveDelivery("assessment-A", "release-A", "approved for delivery", PROOF)
ROLLBACK = RecordRollback(
    "production fault", "affected orders recorded", "release-old", "plan-A", PROOF
)
REWORK = AuthorizeRework("new-plan-A", "manager authorizes rework", PROOF)


def context_for(state: TaskState) -> TransitionContext:
    role = {
        TaskState.PENDING: ProjectRole.MANAGER,
        TaskState.DEVELOPING: ProjectRole.DEVELOPER,
        TaskState.PENDING_REVIEW: ProjectRole.REVIEWER,
    }.get(state, ProjectRole.MANAGER)
    return TransitionContext(
        project_member=True,
        roles=frozenset({role}),
        actor_is_owner=role is ProjectRole.DEVELOPER,
        dependency_states=(TaskState.DELIVERED, TaskState.DELIVERED),
        artifact_reference="fixed-source-revision",
        latest_review_reference="review-A",
        approved_review_reference="review-A",
        review=ReviewGate(
            "review-A", Cycle(), "fixed-source-revision", ReviewOutcome.ACCEPTED, True
        ),
        release=ReleaseGate("assessment-A", 1, 1, True, True, True),
        rollback=RollbackGate("plan-A", 1, True, True),
        validated_rework_plan_reference="new-plan-A",
    )


def command_context(state: TaskState, command: object) -> TransitionContext:
    context = context_for(TaskState.DEVELOPING if isinstance(command, StartDevelopment) else state)
    if isinstance(command, ReturnForChanges):
        assert context.review is not None
        return replace(context, review=replace(context.review, outcome=ReviewOutcome.REJECTED))
    return context


@pytest.mark.parametrize(
    ("source", "command", "target"),
    [
        (TaskState.PENDING, StartDevelopment(), TaskState.DEVELOPING),
        (TaskState.DEVELOPING, SUBMIT, TaskState.PENDING_REVIEW),
        (TaskState.PENDING_REVIEW, ACCEPT, TaskState.PENDING_RELEASE),
        (TaskState.PENDING_REVIEW, REJECT, TaskState.DEVELOPING),
        (TaskState.PENDING_RELEASE, DELIVER, TaskState.DELIVERED),
        (TaskState.DELIVERED, ROLLBACK, TaskState.ROLLED_BACK),
        (TaskState.ROLLED_BACK, REWORK, TaskState.DEVELOPING),
    ],
)
def test_permitted_business_paths_return_decisions_without_applying_them(source, command, target):
    position = TaskPosition(source)
    context = command_context(source, command)
    decision = decide(position, command, context)
    assert decision.target == TaskPosition(target)
    assert decision.source is position
    assert decision.command is command
    assert position.state is source
    assert context.cycle == Cycle()
    with pytest.raises(FrozenInstanceError):
        decision.target.state = source


@pytest.mark.parametrize(
    "source",
    [
        TaskState.PENDING,
        TaskState.DEVELOPING,
        TaskState.PENDING_REVIEW,
        TaskState.PENDING_RELEASE,
    ],
)
def test_block_round_trip_preserves_real_origin_and_does_not_reset_approval_cycles(source):
    context = context_for(source)
    original = TaskPosition(source)
    blocked = decide(original, BLOCK, context)
    assert blocked.target == TaskPosition(TaskState.BLOCKED, source)
    restored = decide(blocked.target, UNBLOCK, context)
    assert restored.target == original
    assert blocked.command.reason == "external service unavailable"
    assert restored.command.basis == "external service verified available"
    assert not blocked.effects and not restored.effects
    assert context.cycle == Cycle()


@pytest.mark.parametrize(
    ("source", "command"),
    [
        (TaskState.DEVELOPING, DELIVER),
        (TaskState.PENDING, ACCEPT),
        (TaskState.PENDING_REVIEW, ROLLBACK),
        (TaskState.PENDING_RELEASE, SUBMIT),
        (TaskState.ROLLED_BACK, StartDevelopment()),
        (TaskState.DELIVERED, REWORK),
        (TaskState.DEVELOPING, UNBLOCK),
        (TaskState.DELIVERED, BLOCK),
        (TaskState.ROLLED_BACK, BLOCK),
        (TaskState.BLOCKED, BLOCK),
    ],
)
def test_forbidden_skips_and_terminal_exits_leave_original_position_unchanged(source, command):
    position = TaskPosition(source, TaskState.DEVELOPING if source is TaskState.BLOCKED else None)
    with pytest.raises(DomainViolation) as error:
        decide(position, command, context_for(source))
    assert error.value.code is Violation.INVALID_TRANSITION
    assert position.state is source


@pytest.mark.parametrize(
    "dependency",
    [
        TaskState.PENDING,
        TaskState.DEVELOPING,
        TaskState.BLOCKED,
        TaskState.PENDING_REVIEW,
        TaskState.PENDING_RELEASE,
        TaskState.ROLLED_BACK,
    ],
)
@pytest.mark.parametrize("operation", ["start", "unblock-to-develop", "rework"])
def test_only_the_three_dependency_guarded_operations_refuse_undelivered_predecessors(
    dependency,
    operation,
):
    positions = {
        "start": TaskPosition(TaskState.PENDING),
        "unblock-to-develop": TaskPosition(TaskState.BLOCKED, TaskState.DEVELOPING),
        "rework": TaskPosition(TaskState.ROLLED_BACK),
    }
    commands = {"start": StartDevelopment(), "unblock-to-develop": UNBLOCK, "rework": REWORK}
    context = context_for(
        TaskState.PENDING_RELEASE if operation == "rework" else TaskState.DEVELOPING
    )
    context = replace(context, dependency_states=(TaskState.DELIVERED, dependency))
    with pytest.raises(DomainViolation) as error:
        decide(positions[operation], commands[operation], context)
    assert error.value.code is Violation.DEPENDENCIES_UNSATISFIED


def test_review_rejection_does_not_invent_a_dependency_guard_or_change_upstream_state():
    context = command_context(TaskState.PENDING_REVIEW, REJECT)
    context = replace(context, dependency_states=(TaskState.ROLLED_BACK,))
    result = decide(TaskPosition(TaskState.PENDING_REVIEW), REJECT, context)
    assert result.target.state is TaskState.DEVELOPING
    assert result.effects == frozenset({Effect.ADVANCE_REVIEW_CYCLE, Effect.CLEAR_APPROVALS})
    assert context.dependency_states == (TaskState.ROLLED_BACK,)
    assert context.cycle == Cycle()


@pytest.mark.parametrize(
    "roles",
    [
        frozenset({ProjectRole.MANAGER}),
        frozenset({ProjectRole.REVIEWER}),
    ],
)
@pytest.mark.parametrize(
    ("position", "command"),
    [
        (TaskPosition(TaskState.PENDING), StartDevelopment()),
        (TaskPosition(TaskState.DEVELOPING), SUBMIT),
    ],
)
def test_manager_or_reviewer_role_alone_cannot_advance_development(roles, position, command):
    context = replace(context_for(TaskState.DEVELOPING), roles=roles)
    with pytest.raises(DomainViolation) as error:
        decide(position, command, context)
    assert error.value.code is Violation.ROLE_FORBIDDEN


def test_manager_who_also_is_the_assigned_developer_can_start():
    context = replace(
        context_for(TaskState.DEVELOPING),
        roles=frozenset({ProjectRole.MANAGER, ProjectRole.DEVELOPER}),
    )
    assert (
        decide(TaskPosition(TaskState.PENDING), StartDevelopment(), context).target.state
        is TaskState.DEVELOPING
    )


@pytest.mark.parametrize(
    ("change", "code"),
    [
        ({"project_member": False}, Violation.PROJECT_ACCESS_REQUIRED),
        ({"actor_is_owner": False}, Violation.OWNER_REQUIRED),
    ],
)
def test_current_project_membership_and_task_ownership_are_required(change, code):
    with pytest.raises(DomainViolation) as error:
        decide(
            TaskPosition(TaskState.PENDING),
            StartDevelopment(),
            replace(context_for(TaskState.DEVELOPING), **change),
        )
    assert error.value.code is code


@pytest.mark.parametrize(
    ("command", "code"),
    [
        (replace(BLOCK, reason=" \n"), Violation.BLOCK_REASON_REQUIRED),
        (replace(BLOCK, responsibility_stage=None), Violation.RESPONSIBILITY_STAGE_REQUIRED),
        (replace(BLOCK, evidence=()), Violation.EVIDENCE_REQUIRED),
        (replace(BLOCK, evidence=(" ",)), Violation.EVIDENCE_REQUIRED),
    ],
)
def test_block_requires_reason_actual_responsibility_stage_and_evidence(command, code):
    with pytest.raises(DomainViolation) as error:
        decide(TaskPosition(TaskState.DEVELOPING), command, context_for(TaskState.DEVELOPING))
    assert error.value.code is code


def test_claiming_external_or_review_responsibility_does_not_bypass_stage_authorization():
    with pytest.raises(DomainViolation) as error:
        decide(TaskPosition(TaskState.DEVELOPING), BLOCK, context_for(TaskState.PENDING_REVIEW))
    assert error.value.code is Violation.ROLE_FORBIDDEN


@pytest.mark.parametrize(
    ("command", "code"),
    [
        (replace(UNBLOCK, basis=" "), Violation.UNBLOCK_BASIS_REQUIRED),
        (replace(UNBLOCK, evidence=()), Violation.EVIDENCE_REQUIRED),
    ],
)
def test_unblock_requires_actual_basis_and_evidence(command, code):
    with pytest.raises(DomainViolation) as error:
        decide(
            TaskPosition(TaskState.BLOCKED, TaskState.DEVELOPING),
            command,
            context_for(TaskState.DEVELOPING),
        )
    assert error.value.code is code


@pytest.mark.parametrize(
    ("change", "code"),
    [
        ({"review": None}, Violation.REVIEW_REQUIRED),
        ({"latest_review_reference": "old-review"}, Violation.REVIEW_BASELINE_STALE),
        ({"artifact_reference": "changed-source"}, Violation.REVIEW_BASELINE_STALE),
        ({"cycle": Cycle(2, 1)}, Violation.REVIEW_BASELINE_STALE),
        ({"cycle": Cycle(1, 2)}, Violation.REVIEW_BASELINE_STALE),
        ({"actor_is_owner": True}, Violation.SELF_REVIEW_FORBIDDEN),
    ],
)
def test_code_review_cannot_reuse_stale_proof_or_be_approved_by_owner(change, code):
    with pytest.raises(DomainViolation) as error:
        decide(
            TaskPosition(TaskState.PENDING_REVIEW),
            ACCEPT,
            replace(context_for(TaskState.PENDING_REVIEW), **change),
        )
    assert error.value.code is code


@pytest.mark.parametrize(
    ("change", "code"),
    [
        ({"evidence_complete": False}, Violation.EVIDENCE_REQUIRED),
        ({"reviewer_is_owner": True}, Violation.SELF_REVIEW_FORBIDDEN),
        ({"outcome": ReviewOutcome.REJECTED}, Violation.REVIEW_OUTCOME_MISMATCH),
    ],
)
def test_review_acceptance_checks_the_underlying_proof_not_only_the_approver(change, code):
    context = context_for(TaskState.PENDING_REVIEW)
    assert context.review is not None
    with pytest.raises(DomainViolation) as error:
        decide(
            TaskPosition(TaskState.PENDING_REVIEW),
            ACCEPT,
            replace(context, review=replace(context.review, **change)),
        )
    assert error.value.code is code


@pytest.mark.parametrize(
    ("change", "code"),
    [
        ({"schedule_version": 2}, Violation.RELEASE_BASELINE_STALE),
        ({"delivery_cycle": 2}, Violation.RELEASE_BASELINE_STALE),
        ({"approved": False}, Violation.RELEASE_APPROVAL_REQUIRED),
        ({"rollback_plan_reviewed": False}, Violation.RELEASE_APPROVAL_REQUIRED),
        ({"evidence_complete": False}, Violation.EVIDENCE_REQUIRED),
        ({"reviewer_is_creator": True}, Violation.RELEASE_SELF_REVIEW_FORBIDDEN),
    ],
)
def test_delivery_needs_current_independently_reviewed_assessment_and_plan(change, code):
    context = context_for(TaskState.PENDING_RELEASE)
    assert context.release is not None
    with pytest.raises(DomainViolation) as error:
        decide(
            TaskPosition(TaskState.PENDING_RELEASE),
            DELIVER,
            replace(context, release=replace(context.release, **change)),
        )
    assert error.value.code is code


def test_reschedule_needs_new_assessment_but_keeps_current_code_review():
    context = context_for(TaskState.PENDING_RELEASE)
    updated = replace(context, schedule_version=2)
    with pytest.raises(DomainViolation) as error:
        decide(TaskPosition(TaskState.PENDING_RELEASE), DELIVER, updated)
    assert error.value.code is Violation.RELEASE_BASELINE_STALE
    assert updated.review is context.review
    assert updated.release is not None
    updated = replace(updated, release=replace(updated.release, schedule_version=2))
    assert (
        decide(TaskPosition(TaskState.PENDING_RELEASE), DELIVER, updated).target.state
        is TaskState.DELIVERED
    )


@pytest.mark.parametrize(
    "change",
    [
        {"approved": False},
        {"used_for_delivery": False},
        {"delivery_cycle": 2},
        {"reference": "other-plan"},
    ],
)
def test_rollback_requires_the_reviewed_plan_used_for_this_delivery(change):
    context = context_for(TaskState.DELIVERED)
    assert context.rollback is not None
    with pytest.raises(DomainViolation) as error:
        decide(
            TaskPosition(TaskState.DELIVERED),
            ROLLBACK,
            replace(context, rollback=replace(context.rollback, **change)),
        )
    assert error.value.code is Violation.ROLLBACK_PLAN_REQUIRED


@pytest.mark.parametrize(
    "state,command",
    [
        (TaskState.PENDING_RELEASE, DELIVER),
        (TaskState.DELIVERED, ROLLBACK),
        (TaskState.ROLLED_BACK, REWORK),
    ],
)
def test_delivery_rollback_and_rework_require_manager(state, command):
    with pytest.raises(DomainViolation) as error:
        decide(
            TaskPosition(state),
            command,
            replace(context_for(state), roles=frozenset({ProjectRole.DEVELOPER})),
        )
    assert error.value.code is Violation.ROLE_FORBIDDEN


def test_rework_needs_validated_new_plan_and_returns_cycle_reset_effects_without_applying_them():
    context = context_for(TaskState.ROLLED_BACK)
    with pytest.raises(DomainViolation) as error:
        decide(
            TaskPosition(TaskState.ROLLED_BACK),
            REWORK,
            replace(context, validated_rework_plan_reference=None),
        )
    assert error.value.code is Violation.REWORK_PLAN_REQUIRED
    result = decide(TaskPosition(TaskState.ROLLED_BACK), REWORK, context)
    assert {
        Effect.ADVANCE_DELIVERY_CYCLE,
        Effect.RESET_REVIEW_CYCLE,
        Effect.ADVANCE_SCHEDULE,
        Effect.CLEAR_APPROVALS,
    } <= result.effects
    assert context.cycle == Cycle() and context.schedule_version == 1


@pytest.mark.parametrize(
    "position",
    [
        (TaskState.BLOCKED, None),
        (TaskState.BLOCKED, TaskState.DELIVERED),
        (TaskState.DEVELOPING, TaskState.PENDING),
    ],
)
def test_inconsistent_block_origin_is_rejected_before_any_decision(position):
    with pytest.raises(ValueError):
        TaskPosition(*position)


@pytest.mark.parametrize(
    ("state", "command", "code"),
    [
        (TaskState.DEVELOPING, replace(SUBMIT, artifact_reference=""), Violation.ARTIFACT_REQUIRED),
        (TaskState.DEVELOPING, replace(SUBMIT, evidence=()), Violation.EVIDENCE_REQUIRED),
        (TaskState.PENDING_REVIEW, replace(REJECT, reason=""), Violation.DECISION_DETAILS_REQUIRED),
        (
            TaskState.PENDING_RELEASE,
            replace(DELIVER, reason=""),
            Violation.DECISION_DETAILS_REQUIRED,
        ),
        (TaskState.PENDING_RELEASE, replace(DELIVER, evidence=()), Violation.EVIDENCE_REQUIRED),
        (TaskState.DELIVERED, replace(ROLLBACK, impact=""), Violation.DECISION_DETAILS_REQUIRED),
        (TaskState.DELIVERED, replace(ROLLBACK, evidence=()), Violation.EVIDENCE_REQUIRED),
        (TaskState.ROLLED_BACK, replace(REWORK, reason=""), Violation.DECISION_DETAILS_REQUIRED),
        (TaskState.ROLLED_BACK, replace(REWORK, evidence=()), Violation.EVIDENCE_REQUIRED),
    ],
)
def test_missing_artifact_decision_details_and_evidence_reject_without_mutation(
    state, command, code
):
    position = TaskPosition(state)
    with pytest.raises(DomainViolation) as error:
        decide(position, command, command_context(state, command))
    assert error.value.code is code
    assert position.state is state


@pytest.mark.parametrize(
    ("change", "code"),
    [
        ({"approved_review_reference": None}, Violation.REVIEW_REQUIRED),
        ({"release": None}, Violation.RELEASE_APPROVAL_REQUIRED),
    ],
)
def test_delivery_cannot_bypass_either_code_or_release_approval(change, code):
    with pytest.raises(DomainViolation) as error:
        decide(
            TaskPosition(TaskState.PENDING_RELEASE),
            DELIVER,
            replace(context_for(TaskState.PENDING_RELEASE), **change),
        )
    assert error.value.code is code


def test_rollback_cannot_bypass_missing_plan():
    with pytest.raises(DomainViolation) as error:
        decide(
            TaskPosition(TaskState.DELIVERED),
            ROLLBACK,
            replace(context_for(TaskState.DELIVERED), rollback=None),
        )
    assert error.value.code is Violation.ROLLBACK_PLAN_REQUIRED


def test_no_dependencies_is_a_valid_start_and_no_direct_target_override_exists():
    context = replace(context_for(TaskState.DEVELOPING), dependency_states=())
    result = decide(TaskPosition(TaskState.PENDING), StartDevelopment(), context)
    assert result.target.state is TaskState.DEVELOPING
    with pytest.raises(TypeError):
        ResolveBlock(basis="verified", evidence=PROOF, target_state=TaskState.DELIVERED)


@pytest.mark.parametrize(
    "change",
    [
        {"project_member": "false"},
        {"actor_is_owner": 1},
        {"roles": frozenset({"manager"})},
        {"roles": {ProjectRole.MANAGER}},
        {"dependency_states": ("delivered",)},
        {"dependency_states": [TaskState.DELIVERED]},
        {"cycle": None},
    ],
)
def test_trusted_context_still_refuses_truthy_strings_and_mutable_or_external_types(change):
    with pytest.raises(TypeError):
        replace(context_for(TaskState.DEVELOPING), **change)


@pytest.mark.parametrize("counter", [True, 0, -1, "1"])
def test_round_baselines_refuse_nonpositive_or_coerced_counters(counter):
    with pytest.raises(ValueError):
        Cycle(delivery=counter)


def test_proof_flags_are_not_treated_as_truthy_client_strings():
    context = context_for(TaskState.PENDING_RELEASE)
    assert context.review and context.release and context.rollback
    with pytest.raises(TypeError):
        replace(context.review, evidence_complete="false")
    with pytest.raises(TypeError):
        replace(context.release, approved="false")
    with pytest.raises(TypeError):
        replace(context.rollback, approved="false")
