"""Frozen-guard-first local response prototype; no production writes or network."""

import argparse
import copy
import hashlib
import importlib.util
import itertools
import json
import os
import signal
import socket
import statistics
import sys
import tempfile
from collections import Counter
from importlib.metadata import version
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

from prototype import FastGate, Unsupported, graph

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "profile"))
from diagnose import FIXTURE_SHA, SOURCE, Probe, export_source


def mutations(value):
    def paths(node, path=()):
        if type(node) is dict:
            for key, child in node.items():
                yield path + (key,), child
                yield from paths(child, path + (key,))
        elif type(node) is list:
            for index, child in enumerate(node[:1]):
                yield path + (index,), child
                yield from paths(child, path + (index,))

    for path, _child in paths(value):
        for replacement in (None, False, 0, 1.5, "invalid", [], {}):
            changed = copy.deepcopy(value)
            parent = changed
            for key in path[:-1]:
                parent = parent[key]
            parent[path[-1]] = replacement
            yield changed
        if type(path[-1]) is str:
            changed = copy.deepcopy(value)
            parent = changed
            for key in path[:-1]:
                parent = parent[key]
            del parent[path[-1]]
            yield changed


def guard(gate, seeds, original, spec, report):
    details = []

    def check(schema, value, label, selected=gate):
        before = repr(value)
        try:
            expected = original(schema, value)
        except Exception as error:
            expected = ("exception", type(error).__name__, str(error))
        try:
            actual = selected(schema, value)
        except Exception as error:
            actual = ("exception", type(error).__name__, str(error))
        if actual != expected or repr(value) != before:
            report["counterexample"] = {"label": label, "value": repr(value), "expected": expected, "actual": actual}
            report["false_accept"] = bool(expected) and actual == []
            raise ValueError("GUARD_FAILED_DO_NOT_TIME")
        details.append(
            {
                "label": label,
                "original_error_count": len(expected) if type(expected) is list else None,
                "original_exception": expected[1] if type(expected) is tuple else None,
                "equal": True,
            }
        )

    for index, (schema, value) in enumerate(seeds):
        check(schema, value, f"valid-{index}")
        for number, changed in enumerate(itertools.islice(mutations(value), 50)):
            check(schema, changed, f"mutant-{index}-{number}")
    task_schema = spec["components"]["schemas"]["Task"]
    task = copy.deepcopy(seeds[0][1]["data"])
    task_gate = FastGate([task_schema], original, spec)
    for field, value in (
        ("state", True),
        ("id", 1.5),
        ("created_at", "2026-02-30T00:00:00Z"),
        ("created_at", "0999-01-01T00:00:00Z"),
        ("created_at", "2026-10-28T00:00:00.1234567Z"),
        ("created_at", "2026-10-28T08:00:00+08:00"),
        ("created_at", "2026-10-28T00:00:00Z\n"),
        ("state", 3),
        ("blocked_from_state", 1),
        ("artifact_revision", "a" * 40 + "\n"),
    ):
        changed = copy.deepcopy(task)
        changed[field] = value
        check(task_schema, changed, "task-boundary-" + field + repr(value), task_gate)
    root = seeds[0][0]
    root["not"] = {}
    try:
        check(root, seeds[0][1], "root-schema-mutation")
    finally:
        del root["not"]
    title = task_schema["properties"]["title"]
    old = title["maxLength"]
    title["maxLength"] = 0
    try:
        check(root, seeds[0][1], "referenced-schema-mutation")
    finally:
        title["maxLength"] = old
    unknowns = [
        {"oneOf": [{"type": "string", "pattern": "^a$"}, {"type": "string"}]},
        {"$ref": "#/components/schemas/Id", "maximum": 0},
        {"$ref": "#/components/schemas/UNKNOWN"},
        {"type": "number", "multipleOf": 0.1},
        {"type": "string", "format": "unknown"},
        {"$dynamicRef": "#unknown"},
        {"type": "object", "unevaluatedProperties": False},
    ]
    for index, schema in enumerate(unknowns):
        check(schema, "a\n" if index == 0 else 1, "unsupported-" + str(index), FastGate([schema], original, spec))
    cycle = {"$ref": "#/components/schemas/CYCLE"}
    cyclic = copy.deepcopy(spec)
    cyclic["components"]["schemas"]["CYCLE"] = cycle
    try:
        graph(cycle, cyclic)
    except Unsupported:
        details.append({"label": "cycle-rejected-before-compile", "equal": True})
    else:
        raise ValueError("CYCLE_NOT_REJECTED")
    for value in (float("nan"), float("inf"), (1, 2), {1: "non-string-key"}):
        schema = {"type": "array"}
        check(schema, value, "non-JSON-" + repr(value), FastGate([schema], original, spec))
    from jsonschema import FormatChecker

    saved = FormatChecker.checkers["date-time"]
    FormatChecker.checkers["date-time"] = (lambda value: False, ())
    try:
        check(root, seeds[0][1], "format-checker-current-registration")
    finally:
        FormatChecker.checkers["date-time"] = saved
    key = json.dumps(graph(root, spec), sort_keys=True, separators=(",", ":"))
    gate(root, seeds[0][1])
    if key not in gate.cache:
        raise ValueError("NO_COMPILED_FAST_FUNCTION_DO_NOT_TIME")
    saved = gate.cache[key]

    def broken(value):
        raise RuntimeError("INJECTED_FAST_FAILURE")

    gate.cache[key] = broken
    try:
        check(root, seeds[0][1], "injected-fast-exception")
    finally:
        gate.cache[key] = saved
    report["guard"] = {"status": "passed", "cases": len(details), "details": details, "false_accept": False}


def execute(root, exported, report):
    def denied(*args, **kwargs):
        report["network_or_mysql_attempts"] += 1
        raise RuntimeError("NO_NETWORK_OR_MYSQL")

    socket.socket.connect = socket.socket.connect_ex = socket.create_connection = denied
    sys.path.insert(0, str(exported / "backend"))
    from t44 import api, contracts, persistence
    from t44.services import application
    from t44.services.codes import Action

    persistence.create_mysql_engine = denied
    path = root / "tmp/834_backend_performance/834_request_profile.py"
    assert hashlib.sha256(path.read_bytes()).hexdigest() == FIXTURE_SHA
    module_spec = importlib.util.spec_from_file_location("fresh_fixture", path)
    fixture = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(fixture)
    generator = fixture.fixture(SimpleNamespace(mode="sqlite"))
    probe = Probe()
    count = 0
    original = contracts.violations
    try:
        client, app, _, engine, users = next(generator)
        assert engine.url.drivername == "sqlite" and engine.url.database is None

        def send(operation, token=None, body=None, **values):
            nonlocal count
            count += 1
            if count > 200:
                raise ValueError("HTTP_CAP")
            op = contracts.OPERATIONS[operation]
            headers = {"Authorization": "Bearer " + token} if token else {}
            if any(p.get("$ref", "").endswith("/IdempotencyKey") for p in op.get("parameters", [])):
                headers["Idempotency-Key"] = str(uuid4())
            response = client.request(op["method"], "/api/v1" + op["path"].format(**values), headers=headers, json=body)
            if response.status_code != op["success_status"]:
                raise ValueError("HTTP_" + operation + "_" + str(response.status_code))
            payload = response.json()
            schema = op["responses"][str(response.status_code)]["content"]["application/json"]["schema"]
            if original(schema, payload):
                raise ValueError("ORIGINAL_RESPONSE_ORACLE_FAILED")
            return payload

        tokens = {
            role: send("login", body={"username": role, "password": "synthetic-diagnostic-password"})["data"][
                "access_token"
            ]
            for role in users
        }
        pid = send("createProject", token=tokens["manager"], body={"name": "Schema CPU prototype"})["data"]["id"]
        for role, roles in (("developer", [2]), ("reviewer", [1, 3])):
            send(
                "addProjectMember",
                token=tokens["manager"],
                project_id=pid,
                body={"username": role, "roles": roles, "reason": "Synthetic"},
            )
        iid = send(
            "createIteration",
            token=tokens["manager"],
            project_id=pid,
            body={
                "name": "profile",
                **{k: v for k, v in fixture.PLAN.items() if k != "estimated_hours"},
                "capacity": [{"user_id": users["developer"], "available_hours": 240}],
            },
        )["data"]["id"]
        payload = {
            "title": "Synthetic schema task",
            "iteration_id": iid,
            "owner_id": users["developer"],
            "plan": fixture.PLAN,
            "dependency_task_ids": [],
        }
        tasks = [
            send("createTask", token=tokens["manager"], project_id=pid, body=payload)["data"]["task"] for _ in range(20)
        ]
        task = tasks[0]
        report["setup_requests"] = count

        def transition():
            nonlocal task
            blocked = task["state"] == 3
            fields = (
                {"basis": "Resume", "evidence": fixture.EVIDENCE}
                if blocked
                else {"reason": "Block", "responsibility_stage": 1, "evidence": fixture.EVIDENCE}
            )
            response = send(
                "transitionTask",
                token=tokens["manager"],
                project_id=pid,
                task_id=task["id"],
                body={
                    "expected_version": task["version"],
                    "action": Action.UNBLOCK if blocked else Action.BLOCK,
                    **fields,
                },
            )
            task = response["data"]["task"]
            return response

        operations = ("getTask", "listTasks", "validateContractPayload", "transitionTask")
        calls = (
            lambda: send("getTask", token=tokens["developer"], project_id=pid, task_id=task["id"]),
            lambda: send("listTasks", token=tokens["developer"], project_id=pid),
            lambda: send(
                "validateContractPayload",
                token=tokens["developer"],
                project_id=pid,
                body={"category": 1, "payload": payload},
            ),
            transition,
        )
        roots = []
        seeds = []
        for operation, call in zip(operations, calls, strict=True):
            op = contracts.OPERATIONS[operation]
            schema = op["responses"][str(op["success_status"])]["content"]["application/json"]["schema"]
            response = call()
            roots.extend([schema, op["data_schema"]])
            seeds.extend([(schema, response), (op["data_schema"], response["data"])])
        gate = FastGate(roots, original, contracts.SPEC)
        report["pre_guard_SPEC_sha256"] = hashlib.sha256(
            json.dumps(contracts.SPEC, sort_keys=True).encode()
        ).hexdigest()
        # The first seed is a full getTask envelope. Guards finish before any timed prototype call.
        guard(gate, seeds, original, contracts.SPEC, report)
        assert (
            report["pre_guard_SPEC_sha256"]
            == hashlib.sha256(json.dumps(contracts.SPEC, sort_keys=True).encode()).hexdigest()
        )
        probe.install(app)
        report["phases"] = []
        for label, use_fast in (("A1", False), ("B1", True), ("B2", True), ("A2", False)):
            api.violations = application.violations = gate if use_fast else original
            probe.phase = "warm-" + label
            for call in calls:
                call()
            counters = Counter(gate.counts)
            compile_before = gate.compile_cpu_seconds
            probe.phase = label
            for _ in range(7):
                for call in calls:
                    call()
            phase = {
                "label": label,
                "fast": use_fast,
                "operations": {},
                "gate_counts": dict(gate.counts - counters),
                "compile_CPU_seconds_in_measured": gate.compile_cpu_seconds - compile_before,
            }
            for operation in operations:
                rows = [r for r in probe.rows if r["phase"] == label and r["operation"] == operation]
                phase["operations"][operation] = {
                    "n": len(rows),
                    "thread_CPU_median_ms": statistics.median(r["thread_cpu_ms"] for r in rows),
                    "handler_wall_median_ms": statistics.median(r["handler_wall_ms"] for r in rows),
                }
            report["phases"].append(phase)
        report.update(
            status="completed",
            gate_counts=dict(gate.counts),
            compile_cpu_seconds=gate.compile_cpu_seconds,
            rows=probe.rows,
        )
    finally:
        api.violations = application.violations = original
        report["HTTP_requests"] = count
        probe.close()
        generator.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    assert (
        hashlib.sha256(Path(__file__).with_name("DESIGN-AMENDMENT-01.md").read_bytes()).hexdigest()
        == "ab4b9ff40452250549a2f8096f53e1a51b4b13e5ecac72c26f096c49b33b646f"
    )
    assert (
        hashlib.sha256(Path(__file__).with_name("DESIGN-FROZEN.md").read_bytes()).hexdigest()
        == "f48690390196ca1802da9ab380ab587bdaf6e66a34db21e9f21c555799d45734"
    )
    assert args.output.parent.resolve() == root / "agents/backend/p16-schema-response-20261028"
    assert not os.environ.get("DATABASE_URL") and not os.environ.get("T44_DATABASE")
    fd = os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    report = {
        "source": SOURCE,
        "status": "started",
        "network_or_mysql_attempts": 0,
        "formal_acceptance": False,
        "fastjsonschema_version": version("fastjsonschema"),
        "tool_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "prototype_sha256": hashlib.sha256(Path(__file__).with_name("prototype.py").read_bytes()).hexdigest(),
        "frozen_design_sha256": hashlib.sha256(Path(__file__).with_name("DESIGN-FROZEN.md").read_bytes()).hexdigest(),
        "design_amendment_sha256": hashlib.sha256(
            Path(__file__).with_name("DESIGN-AMENDMENT-01.md").read_bytes()
        ).hexdigest(),
    }

    def expired(*args):
        raise TimeoutError("LOCAL_90_SECONDS")

    signal.signal(signal.SIGALRM, expired)
    signal.alarm(90)
    try:
        with tempfile.TemporaryDirectory(prefix="t44-schema-response-") as tmp:
            exported = Path(tmp)
            report["source_manifest"] = export_source(root, exported)
            execute(root, exported, report)
    except BaseException as error:
        report.update(status="failed", failure_class=type(error).__name__)
        raise
    finally:
        signal.alarm(0)
        with os.fdopen(fd, "w") as output:
            json.dump(report, output, indent=2)
            output.write("\n")
    print(json.dumps({k: report.get(k) for k in ("status", "HTTP_requests", "guard", "phases")}, default=str))


if __name__ == "__main__":
    main()
