"""Developer-owned semantic differential checks against the exact admitted source."""

import dataclasses
import hashlib
import importlib
import itertools
import json
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = "e45a2b980c6ba8c61761f897414d54a10000409d"
HERE = Path(__file__).resolve().parent
BASE_DOMAIN = HERE / "baseline" / "backend/t44/domain"
manifest = json.loads((HERE / "legacy-reference.json").read_text())
for name, expected in manifest["files"].items():
    if hashlib.sha256((BASE_DOMAIN / (name + ".py")).read_bytes()).hexdigest() != expected:
        raise RuntimeError("Historical test reference changed")
package = types.ModuleType("_size_baseline_domain")
package.__path__ = [str(BASE_DOMAIN)]
sys.modules[package.__name__] = package
baseline = tuple(
    importlib.import_module(package.__name__ + "." + name)
    for name in ("models", "commands", "state_machine")
)
fixture = importlib.import_module("tmp.811_backend_size.legacy_fixture")
current = (fixture.models, fixture.commands, types.SimpleNamespace(decide=fixture.decide))


def cases(modules):
    domain, cmd, _ = modules
    proof = ("evidence",)
    commands = [
        cmd.StartDevelopment(),
        cmd.RecordBlock("reason", domain.ResponsibilityStage.INTAKE, proof),
        cmd.ResolveBlock("basis", proof),
        cmd.SubmitForReview("artifact", proof),
        cmd.AcceptReview("review"),
        cmd.ReturnForChanges("review", "reason"),
        cmd.ApproveDelivery("assessment", "release", "reason", proof),
        cmd.RecordRollback("reason", "impact", "target", "rollback", proof),
        cmd.AuthorizeRework("plan", "reason", proof),
    ]
    malformed = []
    for command in commands:
        for field in dataclasses.fields(command):
            original = getattr(command, field.name)
            values = ((), ["evidence"], (" ",), (1,)) if field.name == "evidence" else ("", None)
            if isinstance(original, domain.ResponsibilityStage):
                values = (None, "intake")
            malformed.extend(
                dataclasses.replace(command, **{field.name: value}) for value in values
            )
    derived = type("DerivedStart", (cmd.StartDevelopment,), {"evidence": ()})()
    ambiguous = type("AmbiguousStart", (cmd.StartDevelopment, cmd.RecordBlock), {})()
    commands.extend([*malformed, derived, ambiguous, object()])
    positions = [
        domain.TaskPosition(state)
        for state in domain.TaskState
        if state is not domain.TaskState.BLOCKED
    ]
    positions.extend(
        domain.TaskPosition(domain.TaskState.BLOCKED, state) for state in domain.BLOCKABLE
    )
    # Deterministic order is required because baseline/current Enum hash identities differ.
    positions.sort(key=lambda p: (p.state.value, p.blocked_from.value if p.blocked_from else ""))
    base = domain.TransitionContext(
        True,
        frozenset(domain.ProjectRole),
        True,
        (domain.TaskState.DELIVERED,),
        artifact_reference="artifact",
        latest_review_reference="review",
        approved_review_reference="review",
        review=domain.ReviewGate(
            "review", domain.Cycle(), "artifact", domain.ReviewOutcome.ACCEPTED, True
        ),
        release=domain.ReleaseGate("assessment", 1, 1, True, True, True),
        rollback=domain.RollbackGate("rollback", 1, True, True),
        validated_rework_plan_reference="plan",
    )
    contexts = []
    for member, owner, mask, dependency in itertools.product(
        (False, True), (False, True), range(8), (False, True)
    ):
        roles = frozenset(
            role for index, role in enumerate(domain.ProjectRole) if mask & (1 << index)
        )
        contexts.append(
            dataclasses.replace(
                base,
                project_member=member,
                actor_is_owner=owner,
                roles=roles,
                dependency_states=(
                    domain.TaskState.DELIVERED if dependency else domain.TaskState.PENDING,
                ),
            )
        )
    changes = [
        {"review": None},
        {"release": None},
        {"rollback": None},
        {"schedule_version": 2},
        {"cycle": domain.Cycle(2, 2)},
        {"artifact_reference": "stale"},
        {"latest_review_reference": "stale"},
        {"approved_review_reference": None},
        {"validated_rework_plan_reference": None},
    ]
    for field in ("evidence_complete", "reviewer_is_owner"):
        changes.append(
            {"review": dataclasses.replace(base.review, **{field: field == "reviewer_is_owner"})}
        )
    changes.append(
        {"review": dataclasses.replace(base.review, outcome=domain.ReviewOutcome.REJECTED)}
    )
    for field in ("approved", "evidence_complete", "rollback_plan_reviewed", "reviewer_is_creator"):
        changes.append(
            {
                "release": dataclasses.replace(
                    base.release, **{field: field == "reviewer_is_creator"}
                )
            }
        )
    for field, value in (
        ("approved", False),
        ("used_for_delivery", False),
        ("delivery_cycle", 2),
        ("reference", "stale"),
    ):
        changes.append({"rollback": dataclasses.replace(base.rollback, **{field: value})})
    contexts.extend(dataclasses.replace(base, **change) for change in changes)
    return positions, commands, contexts


def outcome(modules, position, command, context):
    domain, _, machine = modules
    try:
        result = machine.decide(position, command, context)
    except domain.DomainViolation as error:
        return ("violation", error.code.value)
    except Exception as error:
        return ("exception", type(error).__name__, str(error))
    return (
        "decision",
        result.action.value,
        result.target.state.value,
        result.target.blocked_from.value if result.target.blocked_from else None,
        tuple(sorted(effect.value for effect in result.effects)),
    )


def test_decisions_match_exact_base_across_ordered_guards_and_malformed_commands():
    old, new = cases(baseline), cases(current)
    count = 0
    for old_case, new_case in zip(itertools.product(*old), itertools.product(*new), strict=True):
        assert outcome(baseline, *old_case) == outcome(current, *new_case), (old_case, new_case)
        count += 1
    (HERE / "differential-receipt.json").write_text(
        json.dumps(
            {
                "base": BASE,
                "comparisons": count,
                "scope": "pure domain decisions/violations; not MySQL locks, HTTP or independent acceptance",
            },
            indent=2,
        )
        + "\n"
    )
