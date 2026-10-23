"""Real MySQL module/API/CLI checks, with scoped synthetic identities and no table clearing."""

import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from t44.api import create_app
from t44.contracts import OPERATIONS, violations
from t44.persistence.delivery import OutboxStore
from t44.persistence.rows import RowsGateway
from t44.scheduling.__main__ import read_token
from t44.scheduling.scanner import Scanner, validate_call
from t44.services.common import Call, now
from t44.services.errors import Rejected

pytestmark = pytest.mark.integration


def create(team, tid, *, key=None, run=None, expected=None, **body):
    with team["factory"]() as uow:
        task = uow.gateway.get("tasks", tid)
    payload = dict(
        expected_version=task["version"] if expected is None else expected,
        schedule_version=task["schedule_version"],
        rule_version=team["rules"].version,
        scan_run_id=str(run or uuid4()),
    )
    payload.update(body)
    call = Call(
        "createEscalation",
        str(uuid4()),
        team["token"],
        path={"project_id": team["project"], "task_id": tid},
        body=payload,
        key=key or uuid4().hex,
    )
    return call, team["runtime"].execute(call, validate_call)


def scanner(team, **kwargs):
    return Scanner(team["runtime"], lambda: read_token(team["token_file"]), page_size=7, **kwargs)


def test_twenty_overdue_repeated_scan_and_durable_restart(team):
    tids = [team["task"](state=3 if index == 0 else 2) for index in range(20)]
    delivered, rolled_back = team["task"](state=6), team["task"](state=7)
    worker, run_id = scanner(team), str(uuid4())
    run = worker.run(run_id)
    assert run["status"] == 2 and run["created_count"] == 20
    again = scanner(team).run()
    assert again["created_count"] == 0 and again["duplicate_count"] == 20
    resumed = scanner(team).run(run_id)
    assert resumed["id"] == run["id"] and resumed["created_count"] == 20
    with team["factory"]() as uow:
        g = uow.gateway
        events = g.rows("escalation_events", {"project_id": team["project"]})
        assert {row["task_id"] for row in events} == set(tids)
        assert {row["level"] for row in events} == {3}
        assert all(row["rule_hash"] == team["rules"].raw_hash for row in events)
        assert all(row["rule_snapshot"] == team["rules"].snapshot() for row in events)
        assert g.count("outbox_events", {"project_id": team["project"]}) == 20
        assert (
            g.count(
                "audit_events",
                {"project_id": team["project"], "operation_id": "createEscalation", "outcome": 1},
            )
            == 40
        )
        for tid in tids:
            task = g.get("tasks", tid)
            assert (task["version"], task["escalation_count"]) == (2, 1)
        for tid in (delivered, rolled_back):
            assert g.get("tasks", tid)["version"] == 1
        assert run["rule_hash"] == team["rules"].raw_hash and run["heartbeat_at"] is not None


def test_crash_after_event_commit_before_checkpoint_resumes_without_repeat(team, monkeypatch):
    tids = [team["task"]() for _ in range(20)]
    worker, run_id = scanner(team), str(uuid4())
    checkpoint = worker.store.checkpoint

    def crash_once(*args, **kwargs):
        if kwargs["last_task_id"] == tids[0]:
            raise RuntimeError("injected crash after committed upgrade before checkpoint")
        return checkpoint(*args, **kwargs)

    monkeypatch.setattr(worker.store, "checkpoint", crash_once)
    with pytest.raises(RuntimeError, match="injected crash"):
        worker.run(run_id)
    with team["factory"]() as uow:
        assert uow.gateway.count("escalation_events", {"project_id": team["project"]}) == 1
    durable = worker.store.get(run_id)
    assert durable["status"] == 1 and durable["last_task_id"] < tids[0]
    # A separate Scanner object and fresh sessions load persisted cursor/snapshot/UUID.
    final = scanner(team).run(run_id)
    assert final["status"] == 2 and final["created_count"] == 20 and final["duplicate_count"] == 0
    with team["factory"]() as uow:
        assert uow.gateway.count("escalation_events", {"project_id": team["project"]}) == 20
        assert uow.gateway.count("outbox_events", {"project_id": team["project"]}) == 20


def test_concurrent_same_level_only_one_event_and_same_key_replays(team):
    tid = team["task"]()
    barrier = Barrier(2)

    def compete(_):
        barrier.wait()
        return create(team, tid, expected=1)

    with ThreadPoolExecutor(max_workers=2) as executor:
        outcomes = list(executor.map(compete, range(2)))
    assert sorted(outcome[1][0] for outcome in outcomes) == [202, 409]
    successful = next(c for c, r in outcomes if r[0] == 202)
    original = next(r for c, r in outcomes if r[0] == 202)
    replay = Call(
        "createEscalation",
        str(uuid4()),
        team["token"],
        path=successful.path,
        body=successful.body,
        key=successful.key,
    )
    result = team["runtime"].execute(replay, validate_call)
    assert result[0] == 202 and result[1] == original[1] and result[2] is True
    assert result[3] == successful.request_id
    with team["factory"]() as uow:
        g = uow.gateway
        assert g.count("escalation_events", {"task_id": tid}) == 1
        assert g.count("outbox_events", {"task_id": tid}) == 1
        assert g.get("tasks", tid)["escalation_count"] == 1


def test_valid_business_duplicate_and_new_schedule_version(team):
    tid = team["task"]()
    _, first = create(team, tid)
    assert first[0] == 202 and first[1]["created"] is True
    _, second = create(team, tid)
    assert second[0] == 202 and second[1]["created"] is False
    assert second[1]["task_version"] == 2
    with team["factory"]() as uow:
        # Synthetic schedule boundary fixture; normal plan changes remain the backend's API.
        uow.gateway.update("tasks", {"id": tid}, {"version": 3, "schedule_version": 2})
    _, third = create(team, tid)
    assert third[0] == 202 and third[1]["created"] is True and third[1]["task_version"] == 4
    with team["factory"]() as uow:
        g = uow.gateway
        assert g.count("escalation_events", {"task_id": tid}) == 2
        assert g.get("tasks", tid)["escalation_count"] == 2


def test_unique_constraint_savepoint_discards_temporary_outbox(team, monkeypatch):
    tid = team["task"]()
    assert create(team, tid)[1][0] == 202
    original, hidden = RowsGateway.rows, []

    def hide_first(self, table, where=None, **kwargs):
        if table == "escalation_events" and where and where.get("task_id") == tid and not hidden:
            hidden.append(True)
            return []
        return original(self, table, where, **kwargs)

    monkeypatch.setattr(RowsGateway, "rows", hide_first)
    _, result = create(team, tid)
    assert result[0] == 202 and result[1]["created"] is False
    with team["factory"]() as uow:
        g = uow.gateway
        assert g.count("outbox_events", {"task_id": tid}) == 1
        assert g.count("escalation_events", {"task_id": tid}) == 1
        assert (g.get("tasks", tid)["version"], g.get("tasks", tid)["escalation_count"]) == (2, 1)


@pytest.mark.parametrize(
    ("change", "code"),
    [
        ({"expected_version": 9}, "VERSION_CONFLICT"),
        ({"schedule_version": 9}, "SCHEDULE_VERSION_CONFLICT"),
        ({"rule_version": 9}, "RULE_VERSION_CONFLICT"),
    ],
)
def test_locked_versions_rejected_without_business_changes(team, change, code):
    tid = team["task"]()
    _, result = create(team, tid, **change)
    assert result[0] == 409 and result[1]["code"] == code
    with team["factory"]() as uow:
        g = uow.gateway
        assert g.count("outbox_events", {"task_id": tid}) == 0
        assert g.get("tasks", tid)["version"] == 1
        assert g.count("audit_events", {"task_id": tid, "outcome": 2}) == 1


@pytest.mark.parametrize("state", [6, 7])
def test_terminal_state_rejected_and_blocked_timer_continues(team, state):
    terminal = team["task"](state=state)
    _, denied = create(team, terminal)
    assert denied[0] == 409 and denied[1]["code"] == "NOT_ELIGIBLE_FOR_ESCALATION"
    blocked = team["task"](state=3)
    assert create(team, blocked)[1][1]["event"]["level"] == 3


def test_owner_and_all_active_managers_snapshot_and_notification_disposition(team):
    near = team["task"](end=now() + timedelta(hours=2))
    event = create(team, near)[1][1]["event"]
    assert event["level"] == 1 and event["recipient_ids"] == [team["users"][0]]
    overdue = team["task"](end=now() - timedelta(hours=2))
    event = create(team, overdue)[1][1]["event"]
    assert event["level"] == 2 and event["recipient_ids"] == sorted(team["users"][:3])
    store = OutboxStore(team["factory"])
    assert store.consume(event["id"])["created"] == 3
    with team["factory"]() as uow:
        g = uow.gateway
        notice = g.rows("notifications", {"event_id": event["id"]}, limit=1)[0]
        g.update(
            "notifications",
            {"id": notice["id"]},
            {
                "handled_at": now(),
                "handling_note": "Synthetic handling",
                "handling_evidence": [{"kind": 1, "ref": "synthetic module evidence"}],
            },
        )
        row = g.rows("escalation_events", {"event_id": event["id"]}, limit=1)[0]
        wire = team["runtime"].business.escalations.event(g, row)
        assert wire["disposition"] == 3 and wire["handled_count"] == 1
        assert not violations({"$ref": "#/components/schemas/EscalationEvent"}, wire)
    assert store.fallback(event["id"])["created"] == 0
    assert store.consume(event["id"])["created"] == 0


def test_failure_after_writes_rolls_back_event_task_and_outbox_but_records_rejection(
    team, monkeypatch
):
    tid = team["task"]()

    def fail_after_finalize(operation, result):
        assert "audit_id" in result
        raise Rejected("INTERNAL_ERROR")

    monkeypatch.setattr(team["runtime"].business, "validate_data", fail_after_finalize)
    _, result = create(team, tid)
    assert result[0] == 500 and result[1]["code"] == "INTERNAL_ERROR"
    with team["factory"]() as uow:
        g = uow.gateway
        assert g.count("outbox_events", {"task_id": tid}) == 0
        assert g.count("escalation_events", {"task_id": tid}) == 0
        assert g.get("tasks", tid)["version"] == 1
        assert g.count("audit_events", {"task_id": tid, "outcome": 2}) == 1


def test_real_cli_once_and_resume_new_process(team):
    tids = [team["task"]() for _ in range(20)]
    command = [
        sys.executable,
        "-m",
        "t44.scheduling",
        "--once",
        "--page-size",
        "6",
        "--token-file",
        str(team["token_file"]),
        "--rules",
        str(team["rule_file"]),
    ]
    env = dict(team["env"], T44_SCHEDULER_LOCK_FILE=str(team["token_file"].with_suffix(".lock")))
    result = subprocess.run(command, env=env, text=True, capture_output=True, timeout=30)
    assert result.returncode == 0, result.stderr
    first = json.loads(result.stdout)
    assert first["status"] == 2 and first["created_count"] == 20
    result = subprocess.run(command, env=env, text=True, capture_output=True, timeout=30)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["duplicate_count"] == 20
    with team["factory"]() as uow:
        assert uow.gateway.count("escalation_events", {"task_id": tids}) == 20


def test_api_default_zero_arg_component_and_frozen_response_after_finalize(team):
    app = create_app(factory=team["factory"], settings=team["runtime"].settings)
    assert app.state.runtime.business.escalations.__class__.__name__ == "EscalationFacade"
    tid = team["task"]()
    with TestClient(app) as client:
        payload = dict(
            expected_version=1, schedule_version=1, rule_version=1, scan_run_id=str(uuid4())
        )
        response = client.post(
            f"/api/v1/internal/projects/{team['project']}/tasks/{tid}/escalations",
            headers={"Authorization": "Bearer " + team["token"], "Idempotency-Key": uuid4().hex},
            json=payload,
        )
        assert response.status_code == 202, response.text
        assert response.json()["data"]["audit_id"] > 0
        assert not violations({"$ref": "#/components/schemas/EscalationEnvelope"}, response.json())


def test_frozen_rules_and_list_queries_use_human_authentication(team):
    tid = team["task"]()
    created = create(team, tid)[1][1]
    app = create_app(
        factory=team["factory"],
        settings=team["runtime"].settings,
        escalations=team["runtime"].business.escalations,
    )
    with team["factory"]() as uow:
        username = uow.gateway.get("users", team["users"][1])["username"]
    with TestClient(app) as client:
        login = client.post(
            "/api/v1" + OPERATIONS["login"]["path"],
            json={"username": username, "password": team["password"]},
        )
        assert login.status_code == 200
        headers = {"Authorization": "Bearer " + login.json()["data"]["access_token"]}
        response = client.get(
            f"/api/v1/projects/{team['project']}/escalation-rules", headers=headers
        )
        assert response.status_code == 200, response.text
        assert response.json()["data"] == team["rules"].snapshot()
        assert not violations(
            {"$ref": "#/components/schemas/EscalationRuleEnvelope"}, response.json()
        )
        response = client.get(
            f"/api/v1/projects/{team['project']}/escalations",
            headers=headers,
            params={"task_id": tid, "level": 3, "page_size": 1},
        )
        assert response.status_code == 200, response.text
        assert response.json()["data"]["total"] == 1
        assert response.json()["data"]["items"][0]["id"] == created["event"]["id"]
        assert not violations(
            {"$ref": "#/components/schemas/EscalationPageEnvelope"}, response.json()
        )
        denied = client.get(
            f"/api/v1/projects/{team['project']}/escalation-rules",
            headers={"Authorization": "Bearer " + team["token"]},
        )
        assert denied.status_code == 403


def test_service_scope_and_session_revocation_are_rechecked(team):
    tid = team["task"]()
    call, _ = create(team, tid)
    with team["factory"]() as uow:
        g = uow.gateway
        session = g.rows("auth_sessions", {"service_account_id": call.actor_id}, limit=1)[0]
        g.update("auth_sessions", {"id": session["id"]}, {"scopes": []})
    _, denied = create(team, tid)
    assert denied[0] == 403 and denied[1]["code"] == "SERVICE_SCOPE_REQUIRED"
    with team["factory"]() as uow:
        uow.gateway.update("auth_sessions", {"id": session["id"]}, {"revoked_at": now()})
    _, revoked = create(team, tid)
    assert revoked[0] == 401 and revoked[1]["code"] == "TOKEN_REVOKED"
    with team["factory"]() as uow:
        assert uow.gateway.get("tasks", tid)["escalation_count"] == 1


def test_future_window_does_not_create_event(team):
    tid = team["task"](end=now() + timedelta(days=2))
    _, result = create(team, tid)
    assert result[0] == 409 and result[1]["code"] == "NOT_ELIGIBLE_FOR_ESCALATION"
    with team["factory"]() as uow:
        assert uow.gateway.count("escalation_events", {"task_id": tid}) == 0


def test_real_process_death_after_commit_and_cli_resume(team):
    from t44.persistence.scans import ScanStore

    tids = [team["task"]() for _ in range(20)]
    run_id = str(uuid4())
    store = ScanStore(team["factory"])
    store.start(
        run_id,
        rule_version=team["rules"].version,
        rule_snapshot=team["rules"].snapshot(),
        rule_hash=team["rules"].raw_hash,
    )
    # Actual process termination at the real post-commit checkpoint boundary, not an in-memory DB.
    script = """
import os,sys
from t44.persistence.scans import ScanStore
from t44.scheduling.__main__ import main
checkpoint=ScanStore.checkpoint
stop=int(sys.argv[1])
def crash(self,*args,**kwargs):
    if kwargs["last_task_id"]==stop:
        os._exit(73)
    return checkpoint(self,*args,**kwargs)
ScanStore.checkpoint=crash
raise SystemExit(main(sys.argv[2:]))
"""
    options = [
        "--once",
        "--resume-run",
        run_id,
        "--token-file",
        str(team["token_file"]),
        "--rules",
        str(team["rule_file"]),
        "--page-size",
        "5",
    ]
    env = dict(team["env"], T44_SCHEDULER_LOCK_FILE=str(team["token_file"].with_suffix(".lock")))
    died = subprocess.run(
        [sys.executable, "-c", script, str(tids[0]), *options],
        env=env,
        text=True,
        capture_output=True,
        timeout=30,
    )
    assert died.returncode == 73
    assert store.get(run_id)["status"] == 1
    with team["factory"]() as uow:
        assert uow.gateway.count("escalation_events", {"task_id": tids}) == 1
    resumed = subprocess.run(
        [sys.executable, "-m", "t44.scheduling", *options],
        env=env,
        text=True,
        capture_output=True,
        timeout=30,
    )
    assert resumed.returncode == 0, resumed.stderr
    final = json.loads(resumed.stdout)
    assert final["status"] == 2 and final["created_count"] == 20 and final["duplicate_count"] == 0
    with team["factory"]() as uow:
        assert uow.gateway.count("escalation_events", {"task_id": tids}) == 20
        assert uow.gateway.count("outbox_events", {"task_id": tids}) == 20


def test_snapshot_keeps_more_than_one_hundred_active_managers(team):
    from t44.services.identity import HASHER

    stamp = now()
    hashed = HASHER.hash(uuid4().hex)
    managers = []
    with team["factory"]() as uow:
        g = uow.gateway
        for _ in range(101):
            user = g.insert(
                "users",
                dict(
                    username="sch-bulk-" + uuid4().hex,
                    display_name="Synthetic manager scale fixture",
                    password_hash=hashed,
                    active=1,
                    created_at=stamp,
                    updated_at=stamp,
                ),
            )
            managers.append(user)
            g.insert(
                "project_members",
                dict(
                    project_id=team["project"],
                    user_id=user,
                    roles_mask=1,
                    created_at=stamp,
                    updated_at=stamp,
                ),
            )
    tid = team["task"]()
    _, result = create(team, tid)
    assert result[0] == 202
    assert result[1]["event"]["recipient_ids"] == sorted(team["users"][:3] + managers)
    assert OutboxStore(team["factory"]).fallback(result[1]["event"]["id"])["created"] == 104


def test_stale_matching_run_recovered_without_touching_other_rule_artifacts(team):
    from t44.persistence.scans import ScanStore

    run_id = str(uuid4())
    team["task"]()
    store = ScanStore(team["factory"])
    run = store.start(
        run_id,
        rule_version=team["rules"].version,
        rule_snapshot=team["rules"].snapshot(),
        rule_hash=team["rules"].raw_hash,
    )
    with team["factory"]() as uow:
        uow.gateway.update(
            "scan_runs", {"id": run["id"]}, {"heartbeat_at": now() - timedelta(minutes=3)}
        )
    result = scanner(team).tick()
    assert store.get(run_id)["status"] == 2 and store.get(run_id)["created_count"] == 1
    assert result["created_count"] == 0 and result["duplicate_count"] == 1


def test_rule_version_change_cannot_bypass_business_unique_key(team, tmp_path):
    from t44.scheduling.facade import EscalationFacade
    from t44.scheduling.rules import load_rules

    tid = team["task"]()
    _, first = create(team, tid)
    before = team["rules"]
    changed = before.snapshot()
    changed["version"] += 1
    path = tmp_path / "synthetic-rule-change.json"
    path.write_text(json.dumps(changed, ensure_ascii=False, indent=2) + "\n")
    after = load_rules(path)
    team["rules"] = after
    team["runtime"].business.escalations = EscalationFacade(after)
    _, again = create(team, tid)
    assert again[0] == 202 and again[1]["created"] is False
    assert again[1]["event"]["id"] == first[1]["event"]["id"]
    assert again[1]["event"]["rule_version"] == before.version
    with team["factory"]() as uow:
        g = uow.gateway
        assert g.get("tasks", tid)["escalation_count"] == 1
        assert g.count("outbox_events", {"task_id": tid}) == 1
        context = Call("getEscalationRules", str(uuid4()), None, query={"version": before.version})
        assert team["runtime"].business.escalations.rules(g, context) == before.snapshot()


def test_uuid_case_is_canonical_before_counting_owned_creations(team):
    team["task"]()
    run_id = str(uuid4())
    result = scanner(team).run(run_id.upper())
    assert result["created_count"] == 1 and result["duplicate_count"] == 0
    resumed = scanner(team).run(run_id)
    assert resumed["id"] == result["id"] and resumed["created_count"] == 1
