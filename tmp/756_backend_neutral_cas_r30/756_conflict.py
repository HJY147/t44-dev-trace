"""Future synthetic scheduler races; real HTTP error parser, no service or credentials."""

import hashlib
import importlib
import importlib.util
import json
import sys
from copy import deepcopy
from datetime import timedelta
from pathlib import Path

import pytest
from t44.scheduling.rules import load_rules

ROOT = Path(__file__).resolve().parents[2]
CODE = ROOT / "agents/backend/neutral-r30-cas"
sys.path.insert(0, str(CODE))
http = importlib.import_module("http_primitives")
prepare = importlib.import_module("prepare_http")
spec = importlib.util.spec_from_file_location(
    "synthetic_regression", Path(__file__).with_name("756_regression.py")
)
regression = importlib.util.module_from_spec(spec)
spec.loader.exec_module(regression)


def envelope(code="VERSION_CONFLICT"):
    return {
        "code": code,
        "message": "Version conflict",
        "request_id": "synthetic-request",
        "audit_id": 7,
        "current_state": 1,
        "current_version": 2,
        "original_error_code": None,
        "violations": [],
    }


class Response:
    def __init__(self, status, result):
        self.status, self.raw = status, json.dumps(result).encode()

    def read(self, cap):
        return self.raw[:cap]


class Connection:
    def __init__(self, response):
        self.response = response

    def request(self, *args, **kwargs):
        pass

    def getresponse(self):
        return self.response

    def close(self):
        pass


def reject_request(
    tmp_path, status=409, result=None, path="/internal/projects/16/tasks/2312/escalations"
):
    client = http.Client("https://10.0.0.1", tmp_path / "unused-ca", tmp_path, float("inf"))
    client.connection = Connection(Response(status, envelope() if result is None else result))
    return client.request(path, "synthetic-only", {"expected_version": 1})


def test_actual_error_parser_preserves_status_top_level_envelope_and_evidence(tmp_path):
    with pytest.raises(ValueError) as caught:
        reject_request(tmp_path)
    assert getattr(caught.value, "status", None) == 409
    assert caught.value.envelope == envelope()
    records = list(tmp_path.glob("*.private.json"))
    assert len(records) == 1
    record = json.loads(records[0].read_text())
    assert record["status"] == 409 and record["response"]["code"] == "VERSION_CONFLICT"
    assert record["response_sha256"] == hashlib.sha256(json.dumps(envelope()).encode()).hexdigest()
    assert records[0].stat().st_mode & 0o777 == 0o600


def test_full_400_flow_adopts_sixty_readback_events_without_post_retry(tmp_path, monkeypatch):
    original_prepare = prepare.prepare
    races = []

    def run(*args, client_type, **kwargs):
        class SchedulerClient(client_type):
            def request(self, path, token=None, body=None, method=None):
                if (
                    path.startswith("/internal/projects/")
                    and int(path.split("/")[3]) in range(16, 22)
                    and int(path.split("/")[5]) not in races
                ):
                    # The synthetic scheduler wins the CAS before this request. Its original
                    # persisted event remains in the fake store and must be read back intact.
                    raced = dict(body, scan_run_id="44444444-4444-4444-8444-444444444444")
                    super().request(path, token, raced, method)
                    races.append(int(path.split("/")[5]))
                    reject_request(args[4] / "requests", path=path)
                return super().request(path, token, body, method)

        return original_prepare(*args, client_type=SchedulerClient, **kwargs)

    monkeypatch.setattr(prepare, "prepare", run)
    regression.test_complete_40_project_400_api_preparation_fake_only(tmp_path, monkeypatch)
    assert len(races) == 60
    snapshots = json.loads((tmp_path / "out/factual-snapshots.json").read_text())
    recovered = [
        row for row in snapshots["inventory"]["clients"] if row["escalation_task"]["id"] in races
    ]
    assert len(recovered) == len(races)
    assert all(
        row["escalation_event"]["scan_run_id"] == "44444444-4444-4444-8444-444444444444"
        for row in recovered
    )
    assert len(list((tmp_path / "out/session-prefix").glob("*.json"))) == 3


readback = importlib.import_module("escalation_readback")


def run_readback(tmp_path, *, status=409, error=None, mutate=None, offset=None):
    plan, evidence, _, _, _ = regression.fixture()
    selected = deepcopy(evidence["inventory"]["clients"][0]["escalation_task"])
    event = deepcopy(evidence["inventory"]["clients"][0]["escalation_event"])
    pid = selected["project_id"]
    if offset is not None:
        selected["plan"]["planned_end"] = regression.stamp(regression.NOW + offset)
    before, after = deepcopy(selected), deepcopy(selected)
    before["version"] += 1
    after["version"] += 1
    data = {
        "before": before,
        "after": after,
        "events": [event],
        "rules": load_rules().snapshot(),
        "current_rules": load_rules().snapshot(),
        "posted": deepcopy(event),
        "error": envelope() if error is None else error,
    }
    if mutate is not None:
        mutate(data)
    output = tmp_path / "event-readbacks"
    output.mkdir(mode=0o700)
    calls, task_reads = [], [0]

    class API:
        def request(self, path, token=None, body=None, method=None):
            calls.append((path, deepcopy(body)))
            if path.startswith("/internal/"):
                assert body["expected_version"] == selected["version"]
                assert body["schedule_version"] == selected["schedule_version"]
                assert body["rule_version"] == load_rules().version
                if status == 201:
                    return {"event": deepcopy(data["posted"])}
                reject_request(tmp_path, status=status, result=data["error"], path=path)
            if path.endswith("/escalation-rules"):
                return deepcopy(data["current_rules"])
            if "/escalations?" in path:
                return {"items": deepcopy(data["events"]), "total": len(data["events"])}
            if path == f"/projects/{pid}/tasks/{selected['id']}":
                task_reads[0] += 1
                return deepcopy(data["before" if task_reads[0] == 1 else "after"])
            raise AssertionError(path)

    try:
        result = readback.create_or_read_existing(
            API(),
            pid,
            selected,
            data["rules"],
            "synthetic-manager",
            "synthetic-service",
            plan["window"],
            lambda: regression.NOW,
            output,
        )
    finally:
        # Persist the synthetic operation sequence even for expected failures.
        (tmp_path / "synthetic-calls.json").write_text(json.dumps(calls))
    return result, data, calls, output


@pytest.mark.parametrize(
    "status,result",
    [
        (403, envelope()),
        (503, envelope()),
        (200, envelope()),
        (409, envelope("STATE_CONFLICT")),
        (409, envelope("SCHEDULE_VERSION_CONFLICT")),
        (409, envelope("RULE_VERSION_CONFLICT")),
        (409, {"error": {"code": "VERSION_CONFLICT"}}),
        (409, {"message": "Version conflict", "current_version": 999}),
    ],
)
def test_other_errors_never_enter_readback_or_retry(tmp_path, status, result):
    with pytest.raises(http.HttpRejected):
        run_readback(tmp_path, status=status, error=result)
    calls = json.loads((tmp_path / "synthetic-calls.json").read_text())
    assert len(calls) == 1 and calls[0][0].startswith("/internal/")
    assert not list((tmp_path / "event-readbacks").glob("*.json"))


def test_incomplete_top_level_conflict_is_not_enough(tmp_path):
    with pytest.raises(ValueError, match="COMPLETE_ORIGINAL_VERSION_CONFLICT_ENVELOPE_REQUIRED"):
        run_readback(tmp_path, error={"code": "VERSION_CONFLICT", "message": "Version conflict"})
    assert len(json.loads((tmp_path / "synthetic-calls.json").read_text())) == 1


def mutate_case(name, data):
    if name == "no-event":
        data["events"] = []
    elif name == "wrong-rule":
        data["events"][0]["rule_version"] += 1
    elif name == "old-schedule-event":
        data["events"][0]["schedule_version"] += 1
    elif name == "wrong-level":
        data["events"][0]["level"] = 1
    elif name == "wrong-project":
        data["events"][0]["project_id"] += 1
    elif name == "wrong-task":
        data["events"][0]["task_id"] += 1
    elif name == "missing-event-schema":
        del data["events"][0]["recipient_ids"]
    elif name == "future-event":
        data["events"][0]["created_at"] = regression.stamp(regression.NOW + timedelta(seconds=1))
    elif name == "duplicate-current-event":
        data["events"].append(dict(data["events"][0], id=data["events"][0]["id"] + 1))
    elif name == "changed-rules":
        data["current_rules"]["version"] += 1
    elif name == "missing-task-schema":
        del data["before"]["plan"]
    elif name == "changed-initial-schedule":
        data["before"]["schedule_version"] += 1
    elif name == "changed-initial-plan":
        data["before"]["plan"]["estimated_hours"] += 1
    elif name == "changed-initial-project":
        data["before"]["project_id"] += 1
    elif name == "not-eligible-state":
        data["before"]["state"] = 6
    elif name == "conflict-with-no-version-advance":
        data["before"]["version"] -= 1
    elif name == "changed-final-schedule":
        data["after"]["schedule_version"] += 1
    elif name == "changed-final-plan":
        data["after"]["plan"]["planned_end"] = regression.stamp(
            regression.NOW - timedelta(hours=25)
        )
    elif name == "changed-final-state":
        data["after"]["state"] = 1 if data["before"]["state"] != 1 else 2
    elif name == "changed-final-owner":
        data["after"]["owner_id"] += 1
    elif name == "task-version-moved-backwards":
        data["before"]["version"] += 2
    else:
        raise AssertionError(name)


@pytest.mark.parametrize(
    "case",
    [
        "no-event",
        "wrong-rule",
        "old-schedule-event",
        "wrong-level",
        "wrong-project",
        "wrong-task",
        "missing-event-schema",
        "future-event",
        "duplicate-current-event",
        "changed-rules",
        "missing-task-schema",
        "changed-initial-schedule",
        "changed-initial-plan",
        "changed-initial-project",
        "not-eligible-state",
        "conflict-with-no-version-advance",
        "changed-final-schedule",
        "changed-final-plan",
        "changed-final-state",
        "changed-final-owner",
        "task-version-moved-backwards",
    ],
)
def test_invalid_or_unstable_readback_fails_and_keeps_409_prefix(tmp_path, case):
    with pytest.raises(ValueError):
        run_readback(tmp_path, mutate=lambda data: mutate_case(case, data))
    calls = json.loads((tmp_path / "synthetic-calls.json").read_text())
    assert sum(path.startswith("/internal/") for path, _ in calls) == 1
    assert not list((tmp_path / "event-readbacks").glob("*.json"))
    records = list(tmp_path.glob("*.private.json"))
    assert len(records) == 1
    assert json.loads(records[0].read_text())["response"] == envelope()
    assert records[0].stat().st_mode & 0o777 == 0o600


def test_original_409_current_version_is_not_a_task_or_a_success(tmp_path):
    result, data, calls, output = run_readback(
        tmp_path,
        error=dict(envelope(), current_version=999),
        mutate=lambda data: data["after"].update(version=data["before"]["version"] + 1),
    )
    task, event = result
    assert task == data["after"] and task["version"] != 999
    assert event == data["events"][0]
    assert sum(path.startswith("/internal/") for path, _ in calls) == 1
    receipt = json.loads(next(output.glob("*.json")).read_text())
    assert receipt["post_outcome"] == "http_409_VERSION_CONFLICT"
    assert receipt["task"] == task and receipt["event"] == event
    record = json.loads(next(tmp_path.glob("*.private.json")).read_text())
    assert record["status"] == 409 and record["failure_type"] == "HttpRejected"


@pytest.mark.parametrize(
    "offset,level",
    [
        (timedelta(days=-2), 3),
        (timedelta(hours=-12), 2),
        (timedelta(hours=12), 1),
    ],
)
def test_official_rule_selection_determines_level_without_hardcoded_three(tmp_path, offset, level):
    result, data, _, _ = run_readback(
        tmp_path,
        offset=offset,
        mutate=lambda data: data["events"][0].update(level=level),
    )
    assert result[1] == data["events"][0] and result[1]["level"] == level


def test_rule_level_boundary_inside_window_refuses(tmp_path):
    with pytest.raises(ValueError, match="SAME_RULE_SELECTED_LEVEL"):
        run_readback(tmp_path, offset=timedelta(minutes=5))


def test_successful_post_reads_actual_consumer_disposition_without_rewriting(tmp_path):
    result, data, calls, output = run_readback(
        tmp_path,
        status=201,
        mutate=lambda data: data["events"][0].update(disposition=2, handled_count=7),
    )
    assert result[1] == data["events"][0]
    assert result[1]["disposition"] == 2 and result[1]["handled_count"] == 7
    assert data["posted"]["disposition"] == 1 and data["posted"]["handled_count"] == 0
    assert sum(path.startswith("/internal/") for path, _ in calls) == 1
    assert (
        json.loads(next(output.glob("*.json")).read_text())["post_outcome"] == "successful_response"
    )
