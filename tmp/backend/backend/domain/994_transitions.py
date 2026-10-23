"""Business-path unit tests, without API, database, broker or scheduler substitutes."""

from dataclasses import FrozenInstanceError, replace

import pytest
from t44.domain import commands, models as domain
from t44.domain.state_machine import decide

PROOF = ("fixed-evidence-reference",)
BLOCK = commands.RecordBlock("external service unavailable", domain.ResponsibilityStage.EXTERNAL_DEPENDENCY, PROOF)
UNBLOCK = commands.ResolveBlock("external service verified available", PROOF)
SUBMIT = commands.SubmitForReview("fixed-source-revision", PROOF)
ACCEPT = commands.AcceptReview("review-A")
REJECT = commands.ReturnForChanges("review-A", "required checks failed")
DELIVER = commands.ApproveDelivery("assessment-A", "release-A", "approved for delivery", PROOF)
ROLLBACK = commands.RecordRollback(
    "production fault", "affected orders recorded", "release-old", "plan-A", PROOF
)
REWORK = commands.AuthorizeRework("new-plan-A", "manager authorizes rework", PROOF)


def context_for(state: domain.TaskState) -> domain.TransitionContext:
    role = {
        domain.TaskState.PENDING: domain.ProjectRole.MANAGER,
        domain.TaskState.DEVELOPING: domain.ProjectRole.DEVELOPER,
        domain.TaskState.PENDING_REVIEW: domain.ProjectRole.REVIEWER,
    }.get(state, domain.ProjectRole.MANAGER)
    return domain.TransitionContext(
        project_member=True,
        roles=frozenset({role}),
        actor_is_owner=role is domain.ProjectRole.DEVELOPER,
        dependency_states=(domain.TaskState.DELIVERED, domain.TaskState.DELIVERED),
        artifact_reference="fixed-source-revision",
        latest_review_reference="review-A",
        approved_review_reference="review-A",
        review=domain.ReviewGate(
            "review-A", domain.Cycle(), "fixed-source-revision", domain.ReviewOutcome.ACCEPTED, True
        ),
        release=domain.ReleaseGate("assessment-A", 1, 1, True, True, True),
        rollback=domain.RollbackGate("plan-A", 1, True, True),
        validated_rework_plan_reference="new-plan-A",
    )


def command_context(state: domain.TaskState, command: object) -> domain.TransitionContext:
    context = context_for(domain.TaskState.DEVELOPING if isinstance(command, commands.StartDevelopment) else state)
    if isinstance(command, commands.ReturnForChanges):
        assert context.review is not None
        return replace(context, review=replace(context.review, outcome=domain.ReviewOutcome.REJECTED))
    return context


@pytest.mark.parametrize(
    ("source", "command", "target"),
    [
        (domain.TaskState.PENDING, commands.StartDevelopment(), domain.TaskState.DEVELOPING),
        (domain.TaskState.DEVELOPING, SUBMIT, domain.TaskState.PENDING_REVIEW),
        (domain.TaskState.PENDING_REVIEW, ACCEPT, domain.TaskState.PENDING_RELEASE),
        (domain.TaskState.PENDING_REVIEW, REJECT, domain.TaskState.DEVELOPING),
        (domain.TaskState.PENDING_RELEASE, DELIVER, domain.TaskState.DELIVERED),
        (domain.TaskState.DELIVERED, ROLLBACK, domain.TaskState.ROLLED_BACK),
        (domain.TaskState.ROLLED_BACK, REWORK, domain.TaskState.DEVELOPING),
    ],
)
def test_permitted_business_paths_return_decisions_without_applying_them(source, command, target):
    position = domain.TaskPosition(source)
    context = command_context(source, command)
    decision = decide(position, command, context)
    assert decision.target == domain.TaskPosition(target)
    assert decision.source is position
    assert decision.command is command
    assert position.state is source
    assert context.cycle == domain.Cycle()
    with pytest.raises(FrozenInstanceError):
        decision.target.state = source


@pytest.mark.parametrize(
    "source",
    [
        domain.TaskState.PENDING,
        domain.TaskState.DEVELOPING,
        domain.TaskState.PENDING_REVIEW,
        domain.TaskState.PENDING_RELEASE,
    ],
)
def test_block_round_trip_preserves_real_origin_and_does_not_reset_approval_cycles(source):
    context = context_for(source)
    original = domain.TaskPosition(source)
    blocked = decide(original, BLOCK, context)
    assert blocked.target == domain.TaskPosition(domain.TaskState.BLOCKED, source)
    restored = decide(blocked.target, UNBLOCK, context)
    assert restored.target == original
    assert blocked.command.reason == "external service unavailable"
    assert restored.command.basis == "external service verified available"
    assert not blocked.effects and not restored.effects
    assert context.cycle == domain.Cycle()


@pytest.mark.parametrize(
    ("source", "command"),
    [
        (domain.TaskState.DEVELOPING, DELIVER),
        (domain.TaskState.PENDING, ACCEPT),
        (domain.TaskState.PENDING_REVIEW, ROLLBACK),
        (domain.TaskState.PENDING_RELEASE, SUBMIT),
        (domain.TaskState.ROLLED_BACK, commands.StartDevelopment()),
        (domain.TaskState.DELIVERED, REWORK),
        (domain.TaskState.DEVELOPING, UNBLOCK),
        (domain.TaskState.DELIVERED, BLOCK),
        (domain.TaskState.ROLLED_BACK, BLOCK),
        (domain.TaskState.BLOCKED, BLOCK),
    ],
)
def test_forbidden_skips_and_terminal_exits_leave_original_position_unchanged(source, command):
    position = domain.TaskPosition(source, domain.TaskState.DEVELOPING if source is domain.TaskState.BLOCKED else None)
    with pytest.raises(domain.DomainViolation) as error:
        decide(position, command, context_for(source))
    assert error.value.code is domain.Violation.INVALID_TRANSITION
    assert position.state is source


@pytest.mark.parametrize(
    "dependency",
    [
        domain.TaskState.PENDING,
        domain.TaskState.DEVELOPING,
        domain.TaskState.BLOCKED,
        domain.TaskState.PENDING_REVIEW,
        domain.TaskState.PENDING_RELEASE,
        domain.TaskState.ROLLED_BACK,
    ],
)
@pytest.mark.parametrize("operation", ["start", "unblock-to-develop", "rework"])
def test_only_the_three_dependency_guarded_operations_refuse_undelivered_predecessors(
    dependency,
    operation,
):
    positions = {
        "start": domain.TaskPosition(domain.TaskState.PENDING),
        "unblock-to-develop": domain.TaskPosition(domain.TaskState.BLOCKED, domain.TaskState.DEVELOPING),
        "rework": domain.TaskPosition(domain.TaskState.ROLLED_BACK),
    }
    commands = {"start": commands.StartDevelopment(), "unblock-to-develop": UNBLOCK, "rework": REWORK}
    context = context_for(
        domain.TaskState.PENDING_RELEASE if operation == "rework" else domain.TaskState.DEVELOPING
    )
    context = replace(context, dependency_states=(domain.TaskState.DELIVERED, dependency))
    with pytest.raises(domain.DomainViolation) as error:
        decide(positions[operation], commands[operation], context)
    assert error.value.code is domain.Violation.DEPENDENCIES_UNSATISFIED


def test_review_rejection_does_not_invent_a_dependency_guard_or_change_upstream_state():
    context = command_context(domain.TaskState.PENDING_REVIEW, REJECT)
    context = replace(context, dependency_states=(domain.TaskState.ROLLED_BACK,))
    result = decide(domain.TaskPosition(domain.TaskState.PENDING_REVIEW), REJECT, context)
    assert result.target.state is domain.TaskState.DEVELOPING
    assert result.effects == frozenset({domain.Effect.ADVANCE_REVIEW_CYCLE, domain.Effect.CLEAR_APPROVALS})
    assert context.dependency_states == (domain.TaskState.ROLLED_BACK,)
    assert context.cycle == domain.Cycle()


@pytest.mark.parametrize(
    "roles",
    [
        frozenset({domain.ProjectRole.MANAGER}),
        frozenset({domain.ProjectRole.REVIEWER}),
    ],
)
@pytest.mark.parametrize(
    ("position", "command"),
    [
        (domain.TaskPosition(domain.TaskState.PENDING), commands.StartDevelopment()),
        (domain.TaskPosition(domain.TaskState.DEVELOPING), SUBMIT),
    ],
)
def test_manager_or_reviewer_role_alone_cannot_advance_development(roles, position, command):
    context = replace(context_for(domain.TaskState.DEVELOPING), roles=roles)
    with pytest.raises(domain.DomainViolation) as error:
        decide(position, command, context)
    assert error.value.code is domain.Violation.ROLE_FORBIDDEN


def test_manager_who_also_is_the_assigned_developer_can_start():
    context = replace(
        context_for(domain.TaskState.DEVELOPING),
        roles=frozenset({domain.ProjectRole.MANAGER, domain.ProjectRole.DEVELOPER}),
    )
    assert (
        decide(domain.TaskPosition(domain.TaskState.PENDING), commands.StartDevelopment(), context).target.state
        is domain.TaskState.DEVELOPING
    )


@pytest.mark.parametrize(
    ("change", "code"),
    [
        ({"project_member": False}, domain.Violation.PROJECT_ACCESS_REQUIRED),
        ({"actor_is_owner": False}, domain.Violation.OWNER_REQUIRED),
    ],
)
def test_current_project_membership_and_task_ownership_are_required(change, code):
    with pytest.raises(domain.DomainViolation) as error:
        decide(
            domain.TaskPosition(domain.TaskState.PENDING),
            commands.StartDevelopment(),
            replace(context_for(domain.TaskState.DEVELOPING), **change),
        )
    assert error.value.code is code


@pytest.mark.parametrize(
    ("command", "code"),
    [
        (replace(BLOCK, reason=" \n"), domain.Violation.BLOCK_REASON_REQUIRED),
        (replace(BLOCK, responsibility_stage=None), domain.Violation.RESPONSIBILITY_STAGE_REQUIRED),
        (replace(BLOCK, evidence=()), domain.Violation.EVIDENCE_REQUIRED),
        (replace(BLOCK, evidence=(" ",)), domain.Violation.EVIDENCE_REQUIRED),
    ],
)
def test_block_requires_reason_actual_responsibility_stage_and_evidence(command, code):
    with pytest.raises(domain.DomainViolation) as error:
        decide(domain.TaskPosition(domain.TaskState.DEVELOPING), command, context_for(domain.TaskState.DEVELOPING))
    assert error.value.code is code


def test_claiming_external_or_review_responsibility_does_not_bypass_stage_authorization():
    with pytest.raises(domain.DomainViolation) as error:
        decide(domain.TaskPosition(domain.TaskState.DEVELOPING), BLOCK, context_for(domain.TaskState.PENDING_REVIEW))
    assert error.value.code is domain.Violation.ROLE_FORBIDDEN


@pytest.mark.parametrize(
    ("command", "code"),
    [
        (replace(UNBLOCK, basis=" "), domain.Violation.UNBLOCK_BASIS_REQUIRED),
        (replace(UNBLOCK, evidence=()), domain.Violation.EVIDENCE_REQUIRED),
    ],
)
def test_unblock_requires_actual_basis_and_evidence(command, code):
    with pytest.raises(domain.DomainViolation) as error:
        decide(
            domain.TaskPosition(domain.TaskState.BLOCKED, domain.TaskState.DEVELOPING),
            command,
            context_for(domain.TaskState.DEVELOPING),
        )
    assert error.value.code is code


@pytest.mark.parametrize(
    ("change", "code"),
    [
        ({"review": None}, domain.Violation.REVIEW_REQUIRED),
        ({"latest_review_reference": "old-review"}, domain.Violation.REVIEW_BASELINE_STALE),
        ({"artifact_reference": "changed-source"}, domain.Violation.REVIEW_BASELINE_STALE),
        ({"cycle": domain.Cycle(2, 1)}, domain.Violation.REVIEW_BASELINE_STALE),
        ({"cycle": domain.Cycle(1, 2)}, domain.Violation.REVIEW_BASELINE_STALE),
        ({"actor_is_owner": True}, domain.Violation.SELF_REVIEW_FORBIDDEN),
    ],
)
def test_code_review_cannot_reuse_stale_proof_or_be_approved_by_owner(change, code):
    with pytest.raises(domain.DomainViolation) as error:
        decide(
            domain.TaskPosition(domain.TaskState.PENDING_REVIEW),
            ACCEPT,
            replace(context_for(domain.TaskState.PENDING_REVIEW), **change),
        )
    assert error.value.code is code


@pytest.mark.parametrize(
    ("change", "code"),
    [
        ({"evidence_complete": False}, domain.Violation.EVIDENCE_REQUIRED),
        ({"reviewer_is_owner": True}, domain.Violation.SELF_REVIEW_FORBIDDEN),
        ({"outcome": domain.ReviewOutcome.REJECTED}, domain.Violation.REVIEW_OUTCOME_MISMATCH),
    ],
)
def test_review_acceptance_checks_the_underlying_proof_not_only_the_approver(change, code):
    context = context_for(domain.TaskState.PENDING_REVIEW)
    assert context.review is not None
    with pytest.raises(domain.DomainViolation) as error:
        decide(
            domain.TaskPosition(domain.TaskState.PENDING_REVIEW),
            ACCEPT,
            replace(context, review=replace(context.review, **change)),
        )
    assert error.value.code is code


@pytest.mark.parametrize(
    ("change", "code"),
    [
        ({"schedule_version": 2}, domain.Violation.RELEASE_BASELINE_STALE),
        ({"delivery_cycle": 2}, domain.Violation.RELEASE_BASELINE_STALE),
        ({"approved": False}, domain.Violation.RELEASE_APPROVAL_REQUIRED),
        ({"rollback_plan_reviewed": False}, domain.Violation.RELEASE_APPROVAL_REQUIRED),
        ({"evidence_complete": False}, domain.Violation.EVIDENCE_REQUIRED),
        ({"reviewer_is_creator": True}, domain.Violation.RELEASE_SELF_REVIEW_FORBIDDEN),
    ],
)
def test_delivery_needs_current_independently_reviewed_assessment_and_plan(change, code):
    context = context_for(domain.TaskState.PENDING_RELEASE)
    assert context.release is not None
    with pytest.raises(domain.DomainViolation) as error:
        decide(
            domain.TaskPosition(domain.TaskState.PENDING_RELEASE),
            DELIVER,
            replace(context, release=replace(context.release, **change)),
        )
    assert error.value.code is code


def test_reschedule_needs_new_assessment_but_keeps_current_code_review():
    context = context_for(domain.TaskState.PENDING_RELEASE)
    updated = replace(context, schedule_version=2)
    with pytest.raises(domain.DomainViolation) as error:
        decide(domain.TaskPosition(domain.TaskState.PENDING_RELEASE), DELIVER, updated)
    assert error.value.code is domain.Violation.RELEASE_BASELINE_STALE
    assert updated.review is context.review
    assert updated.release is not None
    updated = replace(updated, release=replace(updated.release, schedule_version=2))
    assert (
        decide(domain.TaskPosition(domain.TaskState.PENDING_RELEASE), DELIVER, updated).target.state
        is domain.TaskState.DELIVERED
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
    context = context_for(domain.TaskState.DELIVERED)
    assert context.rollback is not None
    with pytest.raises(domain.DomainViolation) as error:
        decide(
            domain.TaskPosition(domain.TaskState.DELIVERED),
            ROLLBACK,
            replace(context, rollback=replace(context.rollback, **change)),
        )
    assert error.value.code is domain.Violation.ROLLBACK_PLAN_REQUIRED


@pytest.mark.parametrize(
    "state,command",
    [
        (domain.TaskState.PENDING_RELEASE, DELIVER),
        (domain.TaskState.DELIVERED, ROLLBACK),
        (domain.TaskState.ROLLED_BACK, REWORK),
    ],
)
def test_delivery_rollback_and_rework_require_manager(state, command):
    with pytest.raises(domain.DomainViolation) as error:
        decide(
            domain.TaskPosition(state),
            command,
            replace(context_for(state), roles=frozenset({domain.ProjectRole.DEVELOPER})),
        )
    assert error.value.code is domain.Violation.ROLE_FORBIDDEN


def test_rework_needs_validated_new_plan_and_returns_cycle_reset_effects_without_applying_them():
    context = context_for(domain.TaskState.ROLLED_BACK)
    with pytest.raises(domain.DomainViolation) as error:
        decide(
            domain.TaskPosition(domain.TaskState.ROLLED_BACK),
            REWORK,
            replace(context, validated_rework_plan_reference=None),
        )
    assert error.value.code is domain.Violation.REWORK_PLAN_REQUIRED
    result = decide(domain.TaskPosition(domain.TaskState.ROLLED_BACK), REWORK, context)
    assert {
        domain.Effect.ADVANCE_DELIVERY_CYCLE,
        domain.Effect.RESET_REVIEW_CYCLE,
        domain.Effect.ADVANCE_SCHEDULE,
        domain.Effect.CLEAR_APPROVALS,
    } <= result.effects
    assert context.cycle == domain.Cycle() and context.schedule_version == 1


@pytest.mark.parametrize(
    "position",
    [
        (domain.TaskState.BLOCKED, None),
        (domain.TaskState.BLOCKED, domain.TaskState.DELIVERED),
        (domain.TaskState.DEVELOPING, domain.TaskState.PENDING),
    ],
)
def test_inconsistent_block_origin_is_rejected_before_any_decision(position):
    with pytest.raises(ValueError):
        domain.TaskPosition(*position)


@pytest.mark.parametrize(
    ("state", "command", "code"),
    [
        (domain.TaskState.DEVELOPING, replace(SUBMIT, artifact_reference=""), domain.Violation.ARTIFACT_REQUIRED),
        (domain.TaskState.DEVELOPING, replace(SUBMIT, evidence=()), domain.Violation.EVIDENCE_REQUIRED),
        (domain.TaskState.PENDING_REVIEW, replace(REJECT, reason=""), domain.Violation.DECISION_DETAILS_REQUIRED),
        (
            domain.TaskState.PENDING_RELEASE,
            replace(DELIVER, reason=""),
            domain.Violation.DECISION_DETAILS_REQUIRED,
        ),
        (domain.TaskState.PENDING_RELEASE, replace(DELIVER, evidence=()), domain.Violation.EVIDENCE_REQUIRED),
        (domain.TaskState.DELIVERED, replace(ROLLBACK, impact=""), domain.Violation.DECISION_DETAILS_REQUIRED),
        (domain.TaskState.DELIVERED, replace(ROLLBACK, evidence=()), domain.Violation.EVIDENCE_REQUIRED),
        (domain.TaskState.ROLLED_BACK, replace(REWORK, reason=""), domain.Violation.DECISION_DETAILS_REQUIRED),
        (domain.TaskState.ROLLED_BACK, replace(REWORK, evidence=()), domain.Violation.EVIDENCE_REQUIRED),
    ],
)
def test_missing_artifact_decision_details_and_evidence_reject_without_mutation(
    state, command, code
):
    position = domain.TaskPosition(state)
    with pytest.raises(domain.DomainViolation) as error:
        decide(position, command, command_context(state, command))
    assert error.value.code is code
    assert position.state is state


@pytest.mark.parametrize(
    ("change", "code"),
    [
        ({"approved_review_reference": None}, domain.Violation.REVIEW_REQUIRED),
        ({"release": None}, domain.Violation.RELEASE_APPROVAL_REQUIRED),
    ],
)
def test_delivery_cannot_bypass_either_code_or_release_approval(change, code):
    with pytest.raises(domain.DomainViolation) as error:
        decide(
            domain.TaskPosition(domain.TaskState.PENDING_RELEASE),
            DELIVER,
            replace(context_for(domain.TaskState.PENDING_RELEASE), **change),
        )
    assert error.value.code is code


def test_rollback_cannot_bypass_missing_plan():
    with pytest.raises(domain.DomainViolation) as error:
        decide(
            domain.TaskPosition(domain.TaskState.DELIVERED),
            ROLLBACK,
            replace(context_for(domain.TaskState.DELIVERED), rollback=None),
        )
    assert error.value.code is domain.Violation.ROLLBACK_PLAN_REQUIRED


def test_no_dependencies_is_a_valid_start_and_no_direct_target_override_exists():
    context = replace(context_for(domain.TaskState.DEVELOPING), dependency_states=())
    result = decide(domain.TaskPosition(domain.TaskState.PENDING), commands.StartDevelopment(), context)
    assert result.target.state is domain.TaskState.DEVELOPING
    with pytest.raises(TypeError):
        commands.ResolveBlock(basis="verified", evidence=PROOF, target_state=domain.TaskState.DELIVERED)


@pytest.mark.parametrize(
    "change",
    [
        {"project_member": "false"},
        {"actor_is_owner": 1},
        {"roles": frozenset({"manager"})},
        {"roles": {domain.ProjectRole.MANAGER}},
        {"dependency_states": ("delivered",)},
        {"dependency_states": [domain.TaskState.DELIVERED]},
        {"cycle": None},
    ],
)
def test_trusted_context_still_refuses_truthy_strings_and_mutable_or_external_types(change):
    with pytest.raises(TypeError):
        replace(context_for(domain.TaskState.DEVELOPING), **change)


@pytest.mark.parametrize("counter", [True, 0, -1, "1"])
def test_round_baselines_refuse_nonpositive_or_coerced_counters(counter):
    with pytest.raises(ValueError):
        domain.Cycle(delivery=counter)


def test_proof_flags_are_not_treated_as_truthy_client_strings():
    context = context_for(domain.TaskState.PENDING_RELEASE)
    assert context.review and context.release and context.rollback
    with pytest.raises(TypeError):
        replace(context.review, evidence_complete="false")
    with pytest.raises(TypeError):
        replace(context.release, approved="false")
    with pytest.raises(TypeError):
        replace(context.rollback, approved="false")
