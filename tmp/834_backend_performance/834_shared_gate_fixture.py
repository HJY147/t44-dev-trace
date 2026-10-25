"""Real sequential SQLite fixture smoke; no MySQL/concurrency assertion."""

from importlib import import_module
from types import SimpleNamespace

import pytest

gate = import_module("tmp.834_backend_performance.834_shared_gate_http")
profile = import_module("tmp.834_backend_performance.834_request_profile")


@pytest.mark.parametrize("writer", ["capacity", "role"])
def test_http_race_fixture_uses_valid_real_workflow_and_original_errors(writer):
    fixture = profile.fixture(SimpleNamespace(mode="sqlite"))
    try:
        client, _, factory, engine, users = next(fixture)
        env = SimpleNamespace(
            client=client,
            factory=factory,
            engine=engine,
            users=users,
            tokens={},
            report={"cases": [], "responses": []},
        )
        for role in users:
            env.tokens[role] = gate.send(
                env,
                "login",
                role=None,
                body={"username": role, "password": "synthetic-diagnostic-password"},
            )["data"]["access_token"]
        _, pid, iteration = gate.project.__wrapped__(env)
        row, assessment = gate.delivered(env, pid, gate.task(env, pid, iteration))
        row = gate.rollback(env, pid, row, assessment)
        assert row["state"] == 7
        if writer == "capacity":
            gate.send(
                env,
                "changeIteration",
                project_id=pid,
                iteration_id=iteration["id"],
                body={
                    "expected_version": iteration["version"],
                    "plan": {
                        **iteration["plan"],
                        "capacity": [{"user_id": env.users["reviewer"], "available_hours": 40}],
                    },
                    "reason": "Remove rolled-back owner capacity",
                    "evidence": gate.EVIDENCE,
                },
            )
        else:
            with factory() as uow:
                member = uow.gateway.rows(
                    "project_members", {"project_id": pid, "user_id": users["reviewer"]}
                )[0]
            gate.send(
                env,
                "changeProjectMember",
                project_id=pid,
                user_id=users["reviewer"],
                body={
                    "expected_version": member["version"],
                    "roles": [3],
                    "reason": "Remove manager",
                },
            )
        key = "synthetic-rework-" + writer
        result = gate.transition(
            env,
            pid,
            row,
            9,
            role="reviewer",
            expect=422 if writer == "capacity" else 403,
            key=key,
            new_plan=gate.PLAN,
            reason="Synthetic rework",
            evidence=gate.EVIDENCE,
        )
        assert result["code"] == (
            "CAPACITY_REFERENCE_INVALID" if writer == "capacity" else "ACTION_FORBIDDEN"
        )
        gate.rejection_effects(env, result, row, key=key, actor="reviewer")
    finally:
        fixture.close()
