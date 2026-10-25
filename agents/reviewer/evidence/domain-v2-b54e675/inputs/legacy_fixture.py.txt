"""Test-only v1 construction adapter for unchanged behavioral assertions against v2.

Old constructor validation belongs to the historical fixture. Actual v2 row/flag/collection
validation is covered separately in 812_v2_boundary.py. No product compatibility shim exists.
"""

import hashlib
import importlib
import json
import sys
import types
import zlib
from pathlib import Path

from t44.domain import models as v2
from t44.domain.state_machine import decide as decide_v2

ROOT = Path(__file__).resolve().parents[2]
BASE = "e45a2b980c6ba8c61761f897414d54a10000409d"
DIRECTORY = Path(__file__).resolve().parent / "baseline/backend/t44/domain"
manifest = json.loads((Path(__file__).resolve().parent / "legacy-reference.json").read_text())
for name, expected in manifest["files"].items():
    if hashlib.sha256((DIRECTORY / (name + ".py")).read_bytes()).hexdigest() != expected:
        raise RuntimeError("Historical test reference changed")
PACKAGE = "_size_legacy_fixture"
package = types.ModuleType(PACKAGE)
package.__path__ = [str(DIRECTORY)]
sys.modules[PACKAGE] = package
models = importlib.import_module(PACKAGE + ".models")
commands = importlib.import_module(PACKAGE + ".commands")
original_machine = importlib.import_module(PACKAGE + ".state_machine")

STATE_CODES = {state: index for index, state in enumerate(models.TaskState, 1)}
ROLE_CODES = {role: index for index, role in enumerate(models.ProjectRole, 1)}
COMMANDS = (
    commands.StartDevelopment,
    commands.RecordBlock,
    commands.ResolveBlock,
    commands.SubmitForReview,
    commands.AcceptReview,
    commands.ReturnForChanges,
    commands.ApproveDelivery,
    commands.RecordRollback,
    commands.AuthorizeRework,
)


def identifier(reference):
    return (
        zlib.crc32(reference.encode()) + 1
        if isinstance(reference, str) and reference.strip()
        else None
    )


def input_for(position, command, context):
    action = next(
        (index for index, kind in enumerate(COMMANDS, 1) if isinstance(command, kind)), None
    )
    if action is None:
        # Match the v1 membership-before-unsupported-command priority in this call adapter.
        if not context.project_member:
            raise models.DomainViolation(models.Violation.PROJECT_ACCESS_REQUIRED)
        raise TypeError("unsupported internal transition command")
    task = {
        "state": STATE_CODES[position.state],
        "blocked_from_state": STATE_CODES.get(position.blocked_from),
        "delivery_cycle": context.cycle.delivery,
        "review_cycle": context.cycle.review,
        "schedule_version": context.schedule_version,
        "owner_id": 1,
        "artifact_revision": context.artifact_reference,
        "latest_review_id": identifier(context.latest_review_reference),
        "approved_review_id": identifier(context.approved_review_reference),
    }
    body = {"action": action}
    names = {
        "artifact_reference": "artifact_revision",
        "release_reference": "release_version",
        "target_reference": "target_version",
    }
    import dataclasses

    for field in dataclasses.fields(command):
        value = getattr(command, field.name)
        if field.name == "responsibility_stage":
            value = (
                list(models.ResponsibilityStage).index(value) + 1
                if isinstance(value, models.ResponsibilityStage)
                else value
            )
        body[names.get(field.name, field.name)] = value
    body.update(
        review_id=identifier(getattr(command, "review_reference", None)),
        review_version=1,
        assessment_id=identifier(getattr(command, "assessment_reference", None)),
        assessment_version=1,
    )
    review = None
    if context.review:
        gate = context.review
        review = {
            "id": identifier(gate.reference),
            "version": 1,
            "delivery_cycle": gate.cycle.delivery,
            "review_cycle": gate.cycle.review,
            "artifact_revision": gate.artifact_reference,
            "verdict": 1 if gate.outcome is models.ReviewOutcome.ACCEPTED else 2,
            "reviewer_id": 1 if gate.reviewer_is_owner else 2,
        }
    assessment, delivery = None, None
    if action == v2.Action.DELIVER and context.release:
        gate = context.release
        assessment = {
            "id": identifier(gate.reference),
            "version": 1,
            "delivery_cycle": gate.delivery_cycle,
            "schedule_version": gate.schedule_version,
            "status": 2 if gate.approved and gate.rollback_plan_reviewed else 1,
            "created_by": 1,
            "reviewed_by": 1 if gate.reviewer_is_creator else 2,
            "review_evidence": ["proof"] if gate.evidence_complete else [],
        }
    if action == v2.Action.ROLLBACK:
        body.update(
            assessment_id=identifier(command.rollback_plan_reference), rollback_plan_version=1
        )
        if context.rollback:
            gate = context.rollback
            assessment = {
                "id": identifier(gate.reference),
                "delivery_cycle": gate.delivery_cycle,
                "schedule_version": context.schedule_version,
                "status": 2 if gate.approved else 1,
            }
            if gate.used_for_delivery:
                delivery = {"assessment_id": assessment["id"], "rollback_plan_version": 1}
    return v2.Transition(
        task,
        body,
        frozenset(ROLE_CODES[role] for role in context.roles),
        context.actor_is_owner,
        getattr(command, "evidence", ()),
        tuple(STATE_CODES[state] for state in context.dependency_states),
        review,
        assessment,
        delivery,
        context.review.evidence_complete if context.review else False,
        context.project_member,
        {"fixture_plan": "validated"}
        if (
            isinstance(command, commands.AuthorizeRework)
            and isinstance(command.new_plan_reference, str)
            and command.new_plan_reference.strip()
            and command.new_plan_reference == context.validated_rework_plan_reference
        )
        else None,
    )


CALLS = 0


def decide(position, command, context):
    global CALLS
    CALLS += 1
    try:
        result = decide_v2(input_for(position, command, context))
    except v2.DomainViolation as error:
        raise models.DomainViolation(models.Violation[error.code]) from None
    states = {code: state for state, code in STATE_CODES.items()}
    action = next(index for index, kind in enumerate(COMMANDS, 1) if isinstance(command, kind))
    values, effects = result.values, set()
    clears = (
        "latest_review_id",
        "approved_review_id",
        "approved_assessment_id",
        "approved_assessment_version",
        "artifact_revision",
    )
    if all(key in values and values[key] is None for key in clears):
        effects.add(models.Effect.CLEAR_APPROVALS)
    if values.get("review_cycle") == context.cycle.review + 1:
        effects.add(models.Effect.ADVANCE_REVIEW_CYCLE)
    if values.get("delivery_cycle") == context.cycle.delivery + 1:
        effects.add(models.Effect.ADVANCE_DELIVERY_CYCLE)
        if values.get("review_cycle") == 1:
            effects.add(models.Effect.RESET_REVIEW_CYCLE)
    if values.get("schedule_version") == context.schedule_version + 1:
        effects.add(models.Effect.ADVANCE_SCHEDULE)
    records = {
        1: models.Effect.RECORD_DELIVERY_DECISION,
        2: models.Effect.RECORD_ROLLBACK_DECISION,
        3: models.Effect.RECORD_REWORK_DECISION,
    }
    if result.record_type:
        effects.add(records[result.record_type])
    return models.Decision(
        position,
        models.TaskPosition(states[values["state"]], states.get(values["blocked_from_state"])),
        list(models.Action)[action - 1],
        command,
        frozenset(effects),
    )
