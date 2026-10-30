"""Author self-tests through real FastAPI/schema/business/SQLite. Not cloud/MySQL acceptance."""

import importlib.util
import re
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pytest
from t44.contracts import OPERATIONS, violations
from t44.services.common import task_model

HERE = Path(__file__).resolve().parents[3] / "agents/backend/manual11-maintenance/v2"
spec = importlib.util.spec_from_file_location(
    "maintenance_http_subject", HERE / "cohort_maintenance.py"
)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def fixture(application):
    _client, factory = application
    stamp = datetime.now(UTC)
    start, end = datetime(2098, 1, 1, tzinfo=UTC), datetime(2099, 1, 1, tzinfo=UTC)
    clients = []
    with factory() as uow:
        g = uow.gateway
        for pid in range(1, 41):
            g.insert(
                "projects",
                dict(
                    id=pid,
                    name=f"Synthetic {pid}",
                    description="",
                    created_by=1,
                    created_at=stamp,
                    updated_at=stamp,
                ),
            )
            for uid, mask in ((1, 1), (2, 2), (3, 4)):
                g.insert(
                    "project_members",
                    dict(
                        project_id=pid,
                        user_id=uid,
                        roles_mask=mask,
                        created_at=stamp,
                        updated_at=stamp,
                    ),
                )
            iid = g.insert(
                "iterations",
                dict(
                    project_id=pid,
                    name="Synthetic",
                    planned_start=start,
                    planned_end=end,
                    capacity=[{"user_id": 2, "available_hours": 1000}],
                    buffer_quarters=4,
                    delay_contingency="Synthetic",
                    created_at=stamp,
                    updated_at=stamp,
                ),
            )
            for i in range((pid - 1) * 10, pid * 10):
                tasks = []
                for tid, blocked in ((i + 1, i < 138), (i + 401, False)):
                    g.insert(
                        "tasks",
                        dict(
                            id=tid,
                            project_id=pid,
                            iteration_id=iid,
                            title="Synthetic task",
                            description="",
                            owner_id=2,
                            state=3 if blocked else 2,
                            blocked_from_state=2 if blocked else None,
                            block_reason="Synthetic old cycle" if blocked else None,
                            responsibility_stage=5 if blocked else None,
                            planned_start=start,
                            planned_end=end
                            if tid <= 400
                            else stamp - timedelta(days=3),
                            estimated_quarters=32,
                            buffer_quarters=4,
                            delay_contingency="Synthetic",
                            created_at=stamp,
                            updated_at=stamp,
                        ),
                    )
                    tasks.append(task_model(g.get("tasks", tid)))
                scan = g.insert(
                    "scan_runs",
                    dict(
                        run_key=uuid4().bytes,
                        rule_version=1,
                        rule_snapshot=m.FROZEN_RULES,
                        rule_hash=b"0" * 32,
                        cutoff_at=stamp,
                        status=2,
                        started_at=stamp,
                        heartbeat_at=stamp,
                        finished_at=stamp,
                    ),
                )
                event = g.insert(
                    "outbox_events",
                    dict(
                        event_type=2,
                        project_id=pid,
                        task_id=i + 401,
                        payload={},
                        recipients=[1, 2],
                        next_attempt_at=stamp,
                        created_at=stamp,
                        updated_at=stamp,
                    ),
                )
                g.insert(
                    "escalation_events",
                    dict(
                        project_id=pid,
                        task_id=i + 401,
                        schedule_version=1,
                        level=3,
                        rule_version=1,
                        rule_snapshot=m.FROZEN_RULES,
                        rule_hash=b"0" * 32,
                        scan_run_id=scan,
                        planned_end=stamp - timedelta(days=3),
                        observed_at=stamp,
                        event_id=event,
                    ),
                )
                clients.append(
                    dict(
                        client_id=i,
                        project_id=pid,
                        transition_task=tasks[0],
                        escalation_task=tasks[1],
                        escalation_event={"id": event},
                    )
                )
    accounts = {
        r: dict(username=r, password="test-only-password", user_id=i)
        for i, r in enumerate(("manager", "developer", "reviewer"), 1)
    }
    old = dict(
        identity={"git_commit": m.SOURCE},
        run_id="synthetic-original",
        environment={"origin": "https://synthetic.invalid"},
        sessions={r: {"user_id": a["user_id"]} for r, a in accounts.items()},
        inventory={"clients": clients},
    )
    old["binding_sha256"] = m.sha(m.canonical(old))
    return old, accounts


def bridge(client, old, ev):
    class Connection:
        sock = None

        def __init__(self, *args, **kwargs):
            self.requests = []

        def connect(self):
            pass

        def request(self, method, path, body, headers):
            response = client.request(method, path, content=body, headers=headers)
            # Check actual response against frozen envelope for every request.
            operation = next(
                op
                for op in OPERATIONS.values()
                if op["method"].upper() == method
                and re.fullmatch(
                    re.sub(r"\{[^}]+\}", r"[0-9]+", "/api/v1" + op["path"]),
                    path.split("?")[0],
                )
            )
            schema = operation["responses"][str(response.status_code)]["content"][
                "application/json"
            ]["schema"]
            assert not violations(schema, response.json()), response.text
            self.requests.append((method, path, response.status_code))
            self.response = response

        def getresponse(self):
            response = self.response
            return SimpleNamespace(
                status=response.status_code, read=lambda limit: response.content[:limit]
            )

        def close(self):
            pass

    return m.API(
        SimpleNamespace(PinnedHTTPSConnection=Connection),
        old,
        Path("unused-ca"),
        {"connect_ip": "127.0.0.1", "connect_port": 443},
        ev,
        time.monotonic() + 120,
    )


def run_subject(application, tmp_path):
    old, accounts = fixture(application)
    items, _ids = m.inventory(old, accounts)
    ev = m.Evidence(tmp_path / "operation", "synthetic-restore")
    api = bridge(application[0], old, ev)
    summary = dict(
        operation_id="synthetic-restore",
        old_packet_sha256=m.sha(m.canonical(old)),
        unblocked=0,
        skipped_state2=0,
        preflight400=0,
        final400_state2=0,
    )
    return old, accounts, items, api, ev, summary


def test_real_http_138_unblock_full_400_readback_and_800_preserved(
    application, tmp_path
):
    old, accounts, items, api, ev, summary = run_subject(application, tmp_path)
    m.restore(api, old, items, accounts, ev, summary)
    assert summary["status"] == "COMPLETE_EXISTING400_STATE2_ORIGINAL800_PRESERVED"
    assert summary["unblocked"] == 138 and summary["skipped_state2"] == 262
    assert summary["final400_state2"] == 400
    assert summary["original800_before"] == summary["original800_after"] == 800
    posts = [
        r
        for r in api.connection.requests
        if r[0] == "POST" and r[1] != "/api/v1/auth/login"
    ]
    assert len(posts) == 138 and all(status == 200 for _, _, status in posts)
    with application[1]() as uow:
        audits = uow.gateway.rows(
            "audit_events", {"operation_id": "transitionTask", "outcome": 1}
        )
        assert len(audits) == 138
        assert {r["task_id"] for r in audits} == set(range(1, 139))
        assert all(r["actor_id"] == 2 and r["expected_version"] == 1 for r in audits)
        assert all(
            r["evidence"][0]["locator"]
            == f"maintenance/synthetic-restore/{r['task_id']}"
            for r in audits
        )
    assert all(
        b"test-only-password" not in p.read_bytes() and b"Bearer " not in p.read_bytes()
        for p in ev.root.rglob("*")
        if p.is_file()
    )


def test_real_http_unknown_post_commit_inspection_never_reposts(application, tmp_path):
    old, accounts, items, api, ev, summary = run_subject(application, tmp_path)
    developer = m.login(api, "developer", accounts["developer"], ev)
    marker = "maintenance/synthetic-restore/1"
    ev.event(
        "UNBLOCK_ACTION_PLANNED",
        dict(
            task_id=1,
            project_id=1,
            before_version=1,
            idempotency_key="synthetic-lost-reply",
            marker=marker,
        ),
    )
    value = api.request(
        "/projects/1/tasks/1/transitions",
        developer,
        dict(
            expected_version=1,
            action=3,
            basis=m.BASIS,
            evidence=[
                dict(kind=2, locator=marker, description="Synthetic uncertain response")
            ],
        ),
        key="synthetic-lost-reply",
    )
    assert value["task"]["state"] == 2
    m.put(
        ev.root / "guard.PUBLIC.json",
        m.canonical({"old_packet_sha256": summary["old_packet_sha256"]}),
    )
    inspect_ev = m.Evidence(tmp_path / "inspection", "synthetic-inspect")
    after = len(api.connection.requests)
    m.inspect_previous(api, old, items, accounts, inspect_ev, summary, ev.root)
    assert (
        summary["recovery_findings"][0]["classification"]
        == "UNKNOWN_POST_COMMIT_PROVEN_BY_AUDIT_AND_READBACK"
    )
    assert not summary["automatic_resume"]
    assert all(
        method == "GET" or path == "/api/v1/auth/login"
        for method, path, _ in api.connection.requests[after:]
    )


def test_real_http_last_task_due_horizon_refuses_before_first_mutation(
    application, tmp_path
):
    old, accounts, items, api, ev, summary = run_subject(application, tmp_path)
    with application[1]() as uow:
        uow.gateway.update(
            "tasks", {"id": 400}, {"planned_end": datetime(2026, 1, 1, tzinfo=UTC)}
        )
    with pytest.raises(m.Stop, match="EXISTING_TRANSITION_TASK_NOT_ELIGIBLE"):
        m.restore(api, old, items, accounts, ev, summary)
    assert all(
        method == "GET" or path == "/api/v1/auth/login"
        for method, path, _ in api.connection.requests
    )


def test_real_http_last_blocked_dependency_preflight_prevents_all_writes(
    application, tmp_path
):
    old, accounts, items, api, ev, summary = run_subject(application, tmp_path)
    with application[1]() as uow:
        # Last blocked task has a same-project predecessor still developing.
        uow.gateway.insert(
            "task_dependencies",
            dict(
                project_id=14,
                task_id=138,
                depends_on_task_id=538,
                created_by=1,
                created_at=datetime.now(UTC),
            ),
        )
    with pytest.raises(m.Stop, match="LIVE_TRANSITION_DEPENDENCY_UNSATISFIED"):
        m.restore(api, old, items, accounts, ev, summary)
    assert all(
        method == "GET" or path == "/api/v1/auth/login"
        for method, path, _ in api.connection.requests
    )
    with application[1]() as uow:
        assert not uow.gateway.rows("audit_events", {"operation_id": "transitionTask"})
        assert uow.gateway.get("tasks", 1)["state"] == 3


@pytest.mark.parametrize("state", [6, 7])
def test_changed_original_empty_graph_prevents_all_writes_even_delivered(
    application, tmp_path, state
):
    old, accounts, items, api, ev, summary = run_subject(application, tmp_path)
    with application[1]() as uow:
        uow.gateway.update("tasks", {"id": 538}, {"state": state})
        uow.gateway.insert(
            "task_dependencies",
            dict(
                project_id=14,
                task_id=138,
                depends_on_task_id=538,
                created_by=1,
                created_at=datetime.now(UTC),
            ),
        )
    with pytest.raises(
        m.Stop,
        match="ORIGINAL_EMPTY_TRANSITION_DEPENDENCIES_CHANGED|LIVE_TRANSITION_DEPENDENCY_UNSATISFIED",
    ):
        m.restore(api, old, items, accounts, ev, summary)
    assert all(
        method == "GET" or path == "/api/v1/auth/login"
        for method, path, _ in api.connection.requests
    )


def test_real_http_late_project_missing_developer_role_prevents_all_writes(
    application, tmp_path
):
    old, accounts, items, api, ev, summary = run_subject(application, tmp_path)
    with application[1]() as uow:
        # Active membership alone is insufficient: project 14 loses developer role.
        uow.gateway.update(
            "project_members", {"project_id": 14, "user_id": 2}, {"roles_mask": 4}
        )
    with pytest.raises(
        m.Stop, match="LIVE_DEVELOPER_PROJECT_ROLE_REQUIRED|REAL_PROJECT_ROLE_developer"
    ):
        m.restore(api, old, items, accounts, ev, summary)
    assert all(
        method == "GET" or path == "/api/v1/auth/login"
        for method, path, _ in api.connection.requests
    )
    with application[1]() as uow:
        assert not uow.gateway.rows("audit_events", {"operation_id": "transitionTask"})
        assert uow.gateway.get("tasks", 1)["state"] == 3


@pytest.mark.parametrize("failure", ["owner", "shape", "interrupt"])
def test_real_committed_response_failure_stops_and_readonly_inspection_proves_commit(
    application, tmp_path, failure
):
    old, accounts, items, api, ev, summary = run_subject(application, tmp_path)
    original = api.request

    def faulty(path, token=None, body=None, key=None):
        value = original(path, token, body, key)
        if path.endswith("/transitions"):
            if failure == "interrupt":
                raise KeyboardInterrupt()
            if failure == "owner":
                value["task"]["owner_id"] = 999
            else:
                value.pop("task")
        return value

    api.request = faulty
    expected_error = KeyboardInterrupt if failure == "interrupt" else m.Stop
    with pytest.raises(expected_error) as raised:
        m.restore(api, old, items, accounts, ev, summary)
    if failure != "interrupt":
        assert raised.value.category == "UNKNOWN"
    with application[1]() as uow:
        assert uow.gateway.get("tasks", 1)["state"] == 2
        assert uow.gateway.get("tasks", 2)["state"] == 3
        assert (
            len(
                uow.gateway.rows(
                    "audit_events", {"operation_id": "transitionTask", "outcome": 1}
                )
            )
            == 1
        )
    api.request = original
    m.put(
        ev.root / "guard.PUBLIC.json",
        m.canonical({"old_packet_sha256": summary["old_packet_sha256"]}),
    )
    inspect_ev = m.Evidence(tmp_path / "inspection", "synthetic-inspect")
    after = len(api.connection.requests)
    m.inspect_previous(api, old, items, accounts, inspect_ev, summary, ev.root)
    assert (
        summary["recovery_findings"][0]["classification"]
        == "UNKNOWN_POST_COMMIT_PROVEN_BY_AUDIT_AND_READBACK"
    )
    assert all(
        method == "GET" or path == "/api/v1/auth/login"
        for method, path, _ in api.connection.requests[after:]
    )


@pytest.mark.parametrize(
    "case,error",
    [
        ("reviewer", "REAL_PROJECT_ROLE_reviewer"),
        ("rules", "ACTUAL_FROZEN_RULES_READBACK"),
        ("event_missing", "CURRENT_ESCALATION_NOT_ELIGIBLE"),
        ("event_binding", "CURRENT_ESCALATION_NOT_ELIGIBLE"),
        ("escalation_terminal", "CURRENT_ESCALATION_NOT_ELIGIBLE"),
        ("stable_window", "ACTUAL_STABLE_ESCALATION_LEVEL_NOT_ELIGIBLE"),
    ],
)
def test_real_material_eligibility_guards_before_any_unblock(
    application, tmp_path, case, error
):
    old, accounts, items, api, ev, summary = run_subject(application, tmp_path)
    with application[1]() as uow:
        g = uow.gateway
        if case == "reviewer":
            g.update(
                "project_members", {"project_id": 40, "user_id": 3}, {"roles_mask": 1}
            )
        elif case == "event_missing":
            g.delete("escalation_events", {"task_id": 800})
        elif case == "event_binding":
            g.update("escalation_events", {"task_id": 800}, {"schedule_version": 2})
        elif case == "escalation_terminal":
            g.update("tasks", {"id": 800}, {"state": 6})
        elif case == "stable_window":
            g.update(
                "tasks",
                {"id": 800},
                {"planned_end": datetime.now(UTC) + timedelta(hours=1)},
            )
    if case == "rules":
        original = api.request

        def changed_rules(path, token=None, body=None, key=None):
            value = original(path, token, body, key)
            if path == "/projects/40/escalation-rules":
                value["version"] = 2
            return value

        api.request = changed_rules
    with pytest.raises(m.Stop, match=error):
        m.restore(api, old, items, accounts, ev, summary)
    assert all(
        method == "GET" or path == "/api/v1/auth/login"
        for method, path, _ in api.connection.requests
    )
    with application[1]() as uow:
        assert not uow.gateway.rows("audit_events", {"operation_id": "transitionTask"})


def test_embedded_rules_and_window_match_exact_source90b_boundaries():
    from t44.scheduling.rules import load_rules, select_window

    rules = load_rules()
    assert rules.snapshot() == m.FROZEN_RULES
    end = datetime(2026, 10, 30, tzinfo=UTC)
    for seconds in (-86401, -86400, -1, 0, 1, 86399, 86400, 86401):
        for microseconds in (-1, 0, 1):
            point = end + timedelta(seconds=seconds, microseconds=microseconds)
            expected = select_window(point, end, rules)
            assert m.selected_level(point, end) == (
                expected.level if expected else None
            )
