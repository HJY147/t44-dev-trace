"""New v2 trusted-input safety checks; developer tests, not independent acceptance."""

from dataclasses import FrozenInstanceError, replace

import pytest
from t44.domain.models import Action, DomainViolation, Role, State, Transition
from t44.domain.state_machine import decide


def context():
    return Transition(
        {
            "state": State.PENDING,
            "blocked_from_state": None,
            "delivery_cycle": 1,
            "review_cycle": 1,
            "schedule_version": 1,
            "owner_id": 1,
        },
        {"action": Action.START},
        frozenset({Role.DEVELOPER}),
        True,
        dependency_states=(State.DELIVERED,),
    )


@pytest.mark.parametrize("field", ["project_member", "actor_is_owner", "review_complete"])
@pytest.mark.parametrize("value", ["false", 1, None])
def test_flags_refuse_coerced_values(field, value):
    with pytest.raises(TypeError):
        replace(context(), **{field: value})


@pytest.mark.parametrize(
    "roles", [frozenset({"manager"}), {1}, [1], frozenset({True}), frozenset({4})]
)
def test_roles_require_immutable_known_actual_integer_codes(roles):
    with pytest.raises(TypeError):
        replace(context(), roles=roles)


@pytest.mark.parametrize("states", [[6], frozenset({6}), ("delivered",), (True,), (8,)])
def test_dependency_states_require_immutable_known_actual_integer_codes(states):
    with pytest.raises(TypeError):
        replace(context(), dependency_states=states)


@pytest.mark.parametrize(
    "field,value",
    [
        ("task", None),
        ("body", None),
        ("review", False),
        ("assessment", []),
        ("delivery", "row"),
        ("new_plan", "false"),
        ("new_plan", True),
        ("new_plan", []),
    ],
)
def test_row_views_refuse_non_mapping_inputs(field, value):
    with pytest.raises(TypeError):
        replace(context(), **{field: value})


@pytest.mark.parametrize(
    "state,previous",
    [
        (State.BLOCKED, None),
        (State.BLOCKED, State.DELIVERED),
        (State.DEVELOPING, State.PENDING),
        (State.BLOCKED, True),
    ],
)
def test_position_retains_exclusive_valid_block_origin(state, previous):
    with pytest.raises(ValueError):
        replace(context(), task={**context().task, "state": state, "blocked_from_state": previous})


@pytest.mark.parametrize("value", ["pending", True, 0, 8, None])
def test_state_refuses_non_internal_or_coerced_codes(value):
    with pytest.raises(TypeError):
        replace(context(), task={**context().task, "state": value})


@pytest.mark.parametrize("field", ["delivery_cycle", "review_cycle", "schedule_version"])
@pytest.mark.parametrize("value", [True, 0, -1, "1"])
def test_task_baselines_refuse_nonpositive_or_coerced_counters(field, value):
    with pytest.raises(ValueError):
        replace(context(), task={**context().task, field: value})


@pytest.mark.parametrize(
    "row_name,row,counter",
    [
        ("review", {"delivery_cycle": 1, "review_cycle": 1}, "review_cycle"),
        ("assessment", {"delivery_cycle": 1, "schedule_version": 1}, "schedule_version"),
    ],
)
@pytest.mark.parametrize("value", [True, 0, -1, "1"])
def test_proof_baselines_refuse_nonpositive_or_coerced_counters(row_name, row, counter, value):
    with pytest.raises(ValueError):
        replace(context(), **{row_name: {**row, counter: value}})


@pytest.mark.parametrize(
    "row_name,row",
    [
        ("review", {"delivery_cycle": 1, "review_cycle": 1, "reviewer_id": "false"}),
        ("assessment", {"delivery_cycle": 1, "schedule_version": 1, "status": "false"}),
        ("assessment", {"delivery_cycle": 1, "schedule_version": 1, "status": True}),
        ("assessment", {"delivery_cycle": 1, "schedule_version": 1, "review_evidence": "false"}),
        ("delivery", {"assessment_id": True}),
    ],
)
def test_truthy_strings_and_booleans_cannot_be_persisted_proof_codes(row_name, row):
    with pytest.raises(TypeError):
        replace(context(), **{row_name: row})


def test_snapshots_and_decisions_are_immutable_and_do_not_mutate_sources():
    original = context()
    task, body = dict(original.task), dict(original.body)
    view = replace(original, task=task, body=body)
    task["state"], body["action"] = State.DELIVERED, Action.ROLLBACK
    decision = decide(view)
    assert view.task["state"] == State.PENDING
    assert view.body["action"] == Action.START
    assert decision.values["state"] == State.DEVELOPING
    with pytest.raises(FrozenInstanceError):
        decision.values = {"state": State.DELIVERED}
    with pytest.raises(TypeError):
        view.task["state"] = State.DELIVERED
    with pytest.raises(TypeError):
        decision.values["state"] = State.DELIVERED


def test_type_safe_project_membership_and_stage_guards_keep_their_priority():
    with pytest.raises(DomainViolation) as error:
        decide(
            replace(
                context(),
                project_member=False,
                roles=frozenset(),
                task={**context().task, "state": State.DELIVERED},
            )
        )
    assert error.value.code == "PROJECT_ACCESS_REQUIRED"
    with pytest.raises(DomainViolation) as error:
        decide(
            replace(context(), roles=frozenset(), task={**context().task, "state": State.DELIVERED})
        )
    assert error.value.code == "INVALID_TRANSITION"


def delivery_context(review_evidence):
    return Transition(
        {
            "state": State.PENDING_RELEASE,
            "blocked_from_state": None,
            "delivery_cycle": 1,
            "review_cycle": 1,
            "schedule_version": 1,
            "owner_id": 1,
            "artifact_revision": "artifact",
            "latest_review_id": 1,
            "approved_review_id": 1,
        },
        {
            "action": Action.DELIVER,
            "assessment_id": 1,
            "assessment_version": 1,
            "release_version": "release",
            "reason": "reason",
        },
        frozenset({Role.MANAGER}),
        evidence=("decision-proof",),
        review={
            "id": 1,
            "version": 1,
            "delivery_cycle": 1,
            "review_cycle": 1,
            "artifact_revision": "artifact",
            "verdict": 1,
            "reviewer_id": 2,
        },
        assessment={
            "id": 1,
            "version": 1,
            "delivery_cycle": 1,
            "schedule_version": 1,
            "status": 2,
            "created_by": 1,
            "reviewed_by": 2,
            "review_evidence": review_evidence,
        },
        review_complete=True,
    )


def test_appending_caller_evidence_cannot_authorize_an_existing_delivery_snapshot():
    caller_evidence = []
    view = delivery_context(caller_evidence)
    with pytest.raises(DomainViolation) as before:
        decide(view)
    assert before.value.code == "EVIDENCE_REQUIRED"
    caller_evidence.append({"locator": "later-proof"})
    with pytest.raises(DomainViolation) as after:
        decide(view)
    assert after.value.code == before.value.code
    assert view.assessment["review_evidence"] == ()


def test_clearing_caller_evidence_cannot_revoke_an_existing_delivery_snapshot():
    caller_evidence = [{"locator": "original-proof"}]
    view = delivery_context(caller_evidence)
    before = decide(view)
    assert before.values["state"] == State.DELIVERED
    caller_evidence.clear()
    after = decide(view)
    assert after == before
    assert len(view.assessment["review_evidence"]) == 1
