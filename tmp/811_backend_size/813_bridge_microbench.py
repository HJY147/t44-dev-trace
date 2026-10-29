"""Offline matched DTO/decision CPU comparison; excludes SQL/HTTP and formal latency."""

import ast
import gc
import importlib
import json
import statistics
import subprocess
import time
from pathlib import Path
from types import SimpleNamespace

from t44.domain.models import Action, State, Transition
from t44.domain.state_machine import decide
from t44.services.common import roles


def main():
    HERE = Path(__file__).resolve().parent
    ROOT = HERE.parents[1]
    fixture = importlib.import_module("tmp.811_backend_size.legacy_fixture")
    old = fixture.models
    source = subprocess.check_output(
        ["git", "show", fixture.BASE + ":backend/t44/services/workflow.py"], cwd=ROOT
    ).decode()
    tree = ast.parse(source)
    method = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == "transitionTask"
    )
    selected = []
    for node in method.body:
        if isinstance(node, ast.Assign):
            names = [target.id for target in node.targets if isinstance(target, ast.Name)]
            if set(names) & {"review_gate", "context", "commands", "position"} or any(
                isinstance(target, ast.Tuple)
                and [n.id for n in target.elts] == ["release_gate", "rollback_gate"]
                for target in node.targets
            ):
                selected.append(node)
        elif isinstance(node, ast.If) and isinstance(node.test, ast.BoolOp):
            for child in node.body:
                if isinstance(child, ast.Assign) and any(
                    isinstance(t, ast.Name) and t.id in ("release_gate", "rollback_gate")
                    for t in child.targets
                ):
                    selected.append(ast.If(test=node.test, body=[child], orelse=[]))
        elif isinstance(node, ast.Try):
            selected.extend(node.body)
    selected.append(ast.Return(ast.Name("decision", ast.Load())))
    fn = ast.FunctionDef(
        name="old_bridge",
        args=ast.parse(
            "def f(row, b, c, review, assessment, delivery, evidence, predecessors, action, new_plan=None): pass"
        )
        .body[0]
        .args,
        body=selected,
        decorator_list=[],
    )
    compiled = ast.fix_missing_locations(ast.Module(body=[fn], type_ignores=[]))
    namespace = {
        **vars(old),
        **vars(fixture.commands),
        "decide": fixture.original_machine.decide,
        "Action": Action,
        "State": State,
        "roles": roles,
        "STATE_TO_DOMAIN": {code: state for state, code in fixture.STATE_CODES.items()},
        "ROLE_TO_DOMAIN": {code: role for role, code in fixture.ROLE_CODES.items()},
        "STAGE_TO_DOMAIN": dict(enumerate(old.ResponsibilityStage, 1)),
        "reference": lambda identifier, version: f"{identifier}:{version}",
        "self": SimpleNamespace(review_complete=lambda review: True),
    }
    exec(compile(compiled, "<exact-base DTO bridge>", "exec"), namespace)
    old_bridge = namespace["old_bridge"]
    (HERE / "microbench-old-bridge.py").write_text(ast.unparse(compiled) + "\n")
    row = {
        "state": State.PENDING,
        "blocked_from_state": None,
        "delivery_cycle": 1,
        "review_cycle": 1,
        "schedule_version": 1,
        "owner_id": 1,
        "artifact_revision": "artifact",
        "latest_review_id": 1,
        "approved_review_id": 1,
    }
    review = {
        "id": 1,
        "version": 1,
        "delivery_cycle": 1,
        "review_cycle": 1,
        "artifact_revision": "artifact",
        "verdict": 1,
        "reviewer_id": 2,
    }
    assessment = {
        "id": 1,
        "version": 1,
        "delivery_cycle": 1,
        "schedule_version": 1,
        "status": 2,
        "review_evidence": ["proof"],
        "created_by": 1,
        "reviewed_by": 2,
    }
    delivery = {"assessment_id": 1, "rollback_plan_version": 1}
    c = SimpleNamespace(actor_id=1, membership={"roles_mask": 7})
    bodies = [
        (State.PENDING, {"action": Action.START}),
        (State.DEVELOPING, {"action": Action.SUBMIT_REVIEW, "artifact_revision": "artifact"}),
        (
            State.PENDING_REVIEW,
            {"action": Action.APPROVE_REVIEW, "review_id": 1, "review_version": 1},
        ),
        (
            State.PENDING_RELEASE,
            {
                "action": Action.DELIVER,
                "assessment_id": 1,
                "assessment_version": 1,
                "release_version": "release",
                "reason": "reason",
            },
        ),
        (
            State.DELIVERED,
            {
                "action": Action.ROLLBACK,
                "assessment_id": 1,
                "rollback_plan_version": 1,
                "target_version": "target",
                "reason": "reason",
                "impact": "impact",
            },
        ),
    ]
    receipts = []
    for state, body in bodies:
        task = {**row, "state": state}
        actor_owner = body["action"] != Action.APPROVE_REVIEW
        call = SimpleNamespace(actor_id=1 if actor_owner else 2, membership=c.membership)
        current_assessment = (
            assessment if body["action"] in (Action.DELIVER, Action.ROLLBACK) else None
        )
        previous = ({"state": State.DELIVERED},)

        def run_old(
            task=task,
            body=body,
            call=call,
            current_assessment=current_assessment,
            previous=previous,
        ):
            return old_bridge(
                task,
                body,
                call,
                review,
                current_assessment,
                [delivery],
                ("proof",),
                previous,
                body["action"],
            )

        def run_new(
            task=task, body=body, actor_owner=actor_owner, current_assessment=current_assessment
        ):
            return decide(
                Transition(
                    task,
                    body,
                    frozenset(roles(7)),
                    actor_owner,
                    ("proof",),
                    (State.DELIVERED,),
                    review,
                    current_assessment,
                    delivery if body["action"] == Action.ROLLBACK else None,
                    True,
                )
            )

        before, after = run_old(), run_new()
        assert fixture.STATE_CODES[before.target.state] == after.values["state"]
        samples = {"old": [], "v2": []}
        enabled = gc.isenabled()
        gc.disable()
        try:
            for repeat in range(9):
                for name, run in (
                    (("old", run_old), ("v2", run_new))
                    if repeat % 2
                    else (("v2", run_new), ("old", run_old))
                ):
                    started = time.process_time_ns()
                    for _ in range(4000):
                        run()
                    samples[name].append((time.process_time_ns() - started) / 4000)
        finally:
            if enabled:
                gc.enable()
        medians = {name: statistics.median(values) for name, values in samples.items()}
        receipts.append(
            {
                "action": body["action"],
                "target_equal": True,
                "samples_ns_per_call": samples,
                "median_cpu_ns": medians,
                "v2_over_old": medians["v2"] / medians["old"],
            }
        )
    (HERE / "microbench.json").write_text(
        json.dumps(
            {
                "base": fixture.BASE,
                "iterations_per_sample": 4000,
                "repeats": 9,
                "gc_during_timing": False,
                "scope": "pure DTO construction and decision only; no HTTP/SQL/formal performance",
                "cases": receipts,
            },
            indent=2,
        )
        + "\n"
    )
    print(
        json.dumps(
            [
                {key: item[key] for key in ("action", "median_cpu_ns", "v2_over_old")}
                for item in receipts
            ]
        )
    )


if __name__ == "__main__":
    main()
