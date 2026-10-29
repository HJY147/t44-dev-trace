"""Synthetic local checks only: no server, real account, signature or session issuance."""

import ast
import hashlib
import importlib
import json
import py_compile
import subprocess
import sys
import threading
from copy import deepcopy
from datetime import UTC, datetime, timedelta
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import pytest

CODE = Path(__file__).resolve().parents[2] / "agents/backend/neutral-r30"
sys.path.insert(0, str(CODE))
admin_seed = importlib.import_module("admin_seed")
assemble = importlib.import_module("assemble")
guard = importlib.import_module("guard")
prepare_http = importlib.import_module("prepare_http")

NOW = datetime(2026, 11, 1, 12, tzinfo=UTC)
GEN_SOURCE = CODE.parent / "window-20261029/profile/generation.py"
GEN_TREE = ast.parse(GEN_SOURCE.read_text())
GEN_DICTIONARY = next(
    node.value
    for node in ast.walk(GEN_TREE)
    if isinstance(node, ast.Assign)
    and isinstance(node.value, ast.Dict)
    and any(isinstance(target, ast.Name) and target.id == "binding" for target in node.targets)
)
GEN_FIELDS = {key.value for key in GEN_DICTIONARY.keys}
EXACT_PROOF_FIELDS = (
    "config_ids",
    "image_ids",
    "cryptographic_transport_proofs",
    "tls",
    "file_hashes",
)


def stamp(value):
    return value.isoformat(timespec="microseconds").replace("+00:00", "Z")


def sha(value):
    return hashlib.sha256(value.encode()).hexdigest()


def fixture():
    plan = json.loads((CODE / "plan.template.PUBLIC.json").read_text())
    plan.update(
        root_admit_preparation=True,
        run_id="r30window01",
        namespace="t44-cloud-r30window01-p",
        authorized_project_ids=list(range(1, 41)),
        allowed_writes=list(guard.OPERATIONS),
    )
    plan["target"].update(
        compose_project=plan["namespace"],
        database="t44c_r30window01_p",
        mysql_user="t44c_r30window01_p_app",
        binding_sha256=sha("binding"),
        origin="https://10.0.0.1:26445",
        connect_ip="10.0.0.1",
        ca_sha256=sha("synthetic-ca"),
    )
    plan["budget"]["actual_admission_receipt_sha256"] = sha("synthetic-budget")
    plan["window"] = {
        "start_utc": stamp(NOW + timedelta(seconds=180)),
        "end_utc": stamp(NOW + timedelta(seconds=960)),
        "stop_utc": stamp(NOW + timedelta(seconds=1080)),
    }
    plan["lifecycle"] = {
        "t0_utc": stamp(NOW - timedelta(seconds=1020)),
        "cost_stop_utc": stamp(NOW + timedelta(seconds=1380)),
        "packet_cutoff_utc": stamp(NOW + timedelta(seconds=30)),
    }
    gen = json.loads((CODE / "GEN_BINDING_SCHEMA_FIXTURE.PUBLIC.json").read_text())
    gen["stop_utc"] = plan["window"]["stop_utc"]
    for key in EXACT_PROOF_FIELDS:
        assert key in GEN_FIELDS
        gen[key] = {"synthetic_local_metadata_only": sha(key)}
    binding_path = Path(__file__).with_name("GEN_BINDING_SYNTHETIC_FULL_TEST_ONLY.json")
    binding_raw = json.dumps(gen).encode()
    binding_path.write_bytes(binding_raw)
    plan["gen_binding"] = {
        "path": str(binding_path),
        "sha256": hashlib.sha256(binding_raw).hexdigest(),
    }
    plan["target"]["binding_sha256"] = plan["gen_binding"]["sha256"]
    plan["seed"].update(seed=44, anchor_utc=stamp(NOW - timedelta(days=1)))
    for role, value in plan["runtime_roles"].items():
        value.update(running_observed=True, receipt_sha256=sha(role))
    for key in ("source", "images", "transfer", "preflight"):
        plan["readiness"][key] = {
            "sha256": sha(key),
            "completed_at": stamp(NOW - timedelta(seconds=90)),
        }
    plan["readiness"].update(
        all_ready_at=stamp(NOW - timedelta(seconds=60)),
        fixture_ready_at=stamp(NOW - timedelta(seconds=10)),
        admin_preserves_image_pythonpath=True,
    )
    receipt = {
        "kind": "r30-backend-import-receipt-v1",
        "source_sha": guard.SOURCE,
        "bundle_manifest_sha256": guard.BUNDLE_MANIFEST,
        "source_manifest_sha256": guard.SOURCE_MANIFEST,
        "full_runtime_files": 60,
        "identity": {"config": plan["images"]["backend"]},
        "package_resolution": {"t44": "/app/backend/t44"},
        "business_services_started": False,
        "volumes_modified": False,
    }
    raw = json.dumps(receipt).encode()
    plan["source"].update(
        actual_loaded_receipt_sha256=hashlib.sha256(raw).hexdigest(),
        actual_loaded_receipt_path="/root/t44-r30-synthetic/import.json",
        actual_loaded_observed_at=stamp(NOW - timedelta(seconds=120)),
        actual_loaded_full_chain_reviewed_by_root=True,
    )
    sessions, issued = {}, {}
    for role, uid in (("manager", 11), ("developer", 12), ("reviewer", 13), ("service", 21)):
        session = {
            "token": "SYNTHETIC_NOT_REAL_" + role,
            "user_id": uid,
            "expires_at": stamp(NOW + timedelta(seconds=1400)),
            "project_ids": list(range(1, 41)),
            "scopes": ["escalation:write"] if role == "service" else [],
        }
        sessions[role] = session
        issued[role] = {
            **{k: v for k, v in session.items() if k != "token"},
            "token_sha256": sha(session["token"]),
            "issued_at": stamp(NOW - timedelta(seconds=45)),
        }
        if role != "service":
            issued[role].pop("issued_at")
            issued[role].update(
                login_request_started_at=stamp(NOW - timedelta(seconds=45)),
                response_observed_at=stamp(NOW - timedelta(seconds=40)),
                response_meta={"server_time": stamp(NOW - timedelta(seconds=42))},
            )
    members, iterations, clients, deps = {}, {}, [], {}
    for pid in range(1, 41):
        members[str(pid)] = [
            {
                "project_id": pid,
                "user": {"id": uid, "username": "synthetic" + role, "display_name": "synthetic"},
                "roles": [code],
                "version": 1,
                "active": True,
            }
            for role, uid, code in (("manager", 11, 1), ("developer", 12, 2), ("reviewer", 13, 3))
        ]
        iterations[str(pid)] = {
            "id": pid,
            "project_id": pid,
            "version": 1,
            "plan_version": 1,
            "created_at": stamp(NOW - timedelta(days=5)),
            "updated_at": stamp(NOW - timedelta(days=1)),
            "plan": {
                "name": "synthetic",
                "planned_start": stamp(NOW - timedelta(days=5)),
                "planned_end": stamp(NOW + timedelta(days=30)),
                "capacity": [{"user_id": 12, "available_hours": 1000}],
                "buffer_hours": 1,
                "delay_contingency": "synthetic",
            },
        }
    for index in range(400):
        pid = index % 40 + 1
        task = {
            "id": index * 2 + 1,
            "project_id": pid,
            "iteration_id": pid,
            "title": "[synthetic] local fixture",
            "description": "synthetic",
            "owner_id": 12,
            "state": 2,
            "version": 2,
            "schedule_version": 1,
            "delivery_cycle": 1,
            "review_cycle": 1,
            "plan": {
                "planned_start": stamp(NOW - timedelta(days=3)),
                "planned_end": stamp(NOW + timedelta(days=3)),
                "estimated_hours": 1,
                "buffer_hours": 0.25,
                "delay_contingency": "synthetic",
            },
            "blocked_from_state": None,
            "block_reason": None,
            "responsibility_stage": None,
            "latest_review_id": None,
            "approved_review_id": None,
            "approved_assessment_id": None,
            "approved_assessment_version": None,
            "escalation_count": 0,
            "created_at": stamp(NOW - timedelta(days=5)),
            "updated_at": stamp(NOW - timedelta(seconds=20)),
            "artifact_revision": None,
        }
        escalation = deepcopy(task)
        escalation["id"] += 1
        escalation["plan"]["planned_end"] = stamp(NOW - timedelta(days=2))
        event = {
            "id": 10000 + index,
            "project_id": pid,
            "task_id": escalation["id"],
            "schedule_version": 1,
            "rule_version": 1,
            "level": 3,
            "recipient_ids": [11, 12],
            "disposition": 1,
            "scan_run_id": f"00000000-0000-0000-0000-{index:012d}",
            "created_at": stamp(NOW - timedelta(seconds=20)),
            "handled_count": 0,
        }
        clients.append(
            {
                "client_id": index,
                "project_id": pid,
                "transition_task": task,
                "escalation_task": escalation,
                "escalation_event": event,
                "project_manager_ids": [11],
            }
        )
        deps[str(task["id"])] = {
            "project_id": pid,
            "task_id": task["id"],
            "predecessor_ids": [],
            "predecessor_states": [],
        }
    evidence = {
        "run_id": plan["run_id"],
        "namespace": plan["namespace"],
        "database": plan["target"]["database"],
        "binding_sha256": plan["target"]["binding_sha256"],
        "actual_fixture_counts": {**guard.BASE_COUNTS, "tasks": 6400},
        "actual_fixture_sha256": sha("synthetic-snapshot"),
        "session_attestations": issued,
        "inventory": {
            "schema": "772-inventory-v1",
            "captured_at": stamp(NOW - timedelta(seconds=5)),
            "rule_version": 1,
            "clients": clients,
        },
        "memberships": members,
        "iterations": iterations,
        "transition_dependency_facts": deps,
        "exclusive_scope": {
            "task_ids": list(range(1, 801)),
            "event_ids": list(range(10000, 10400)),
            "other_workload_writer_absent": True,
            "writer_evidence_sha256": sha("synthetic-writers"),
            "scheduler_running": True,
            "consumer_running": True,
            "all_notifications_precreated": False,
        },
    }
    counts = {
        "actual_fixture_counts": evidence["actual_fixture_counts"],
        "actual_fixture_sha256": evidence["actual_fixture_sha256"],
        "raw_counts": {
            "projects": 40,
            "tasks": 6400,
            "task_dependencies": 9000,
            "reviews": 11400,
            "decisions": 3600,
        },
    }
    return plan, evidence, sessions, counts, raw


def test_full_400_synthetic_inventory_and_four_original_expiries():
    plan, evidence, *_ = fixture()
    result = guard.check_evidence(plan, evidence, NOW)
    assert result["clients"] == 400 and result["distinct_tasks"] == 800
    assert result["benchmark_authorized"] is False


@pytest.mark.parametrize(
    "mutation",
    [
        "source",
        "namespace",
        "budget",
        "background",
        "expiry",
        "early_issue",
        "duplicates",
        "owner",
        "horizon",
        "manager",
        "count",
        "secret",
    ],
)
def test_refuses_unsafe_or_stale_materials(mutation):
    plan, evidence, *_ = fixture()
    if mutation == "source":
        plan["source"]["git_commit"] = "f7cdb5fa3b19f84d8ab0d0b042bf51a5b8484e8f"
    elif mutation == "namespace":
        plan["namespace"] = "neutral-r29-01"
    elif mutation == "budget":
        plan["budget"]["helper_sha256"] = (
            "305f9eaeea96b0ef882ec17a457f51852bafc8c34b5fe2e47056bd12625dd82d"
        )
    elif mutation == "background":
        plan["runtime_roles"]["scheduler"]["running_observed"] = False
    elif mutation == "expiry":
        evidence["session_attestations"]["manager"]["expires_at"] = plan["window"]["end_utc"]
    elif mutation == "early_issue":
        evidence["session_attestations"]["manager"]["login_request_started_at"] = stamp(
            NOW - timedelta(seconds=61)
        )
    elif mutation == "duplicates":
        evidence["inventory"]["clients"][1]["transition_task"]["id"] = 1
    elif mutation == "owner":
        evidence["inventory"]["clients"][0]["transition_task"]["owner_id"] = 13
    elif mutation == "horizon":
        evidence["inventory"]["clients"][0]["transition_task"]["plan"]["planned_end"] = plan[
            "window"
        ]["end_utc"]
    elif mutation == "manager":
        evidence["inventory"]["clients"][0]["project_manager_ids"] = []
    elif mutation == "count":
        evidence["actual_fixture_counts"]["tasks"] = 6000
    elif mutation == "secret":
        evidence["token"] = "not permitted in metadata guard"
    with pytest.raises(guard.Refused):
        guard.check_evidence(plan, evidence, NOW)


def test_exact_binding_no_retime_no_overwrite_and_raw_proofs(tmp_path):
    plan, evidence, sessions, counts, receipt = fixture()
    original = deepcopy(sessions)
    packet = assemble.assemble(
        plan,
        evidence,
        sessions,
        counts,
        b"synthetic-ca",
        (CODE / "source-manifest.json").read_bytes(),
        (CODE / "backend-bundle-manifest.json").read_bytes(),
        receipt,
        tmp_path / "new",
        now=NOW,
    )
    binding = packet.pop("binding_sha256")
    assert binding == hashlib.sha256(assemble.canonical(packet)).hexdigest()
    assert packet["sessions"] == original and packet["created_at"] == stamp(NOW)
    assert packet["counts"]["tasks"] == 6400
    with pytest.raises(guard.Refused):
        assemble.assemble(
            plan,
            evidence,
            sessions,
            counts,
            b"synthetic-ca",
            (CODE / "source-manifest.json").read_bytes(),
            (CODE / "backend-bundle-manifest.json").read_bytes(),
            receipt,
            tmp_path / "new",
            now=NOW,
        )


def test_seed_calls_only_original_function_explicit_anchor_and_scope(monkeypatch):
    plan, *_ = fixture()
    intent = {
        "run_id": plan["run_id"],
        "namespace": plan["namespace"],
        "database": plan["target"]["database"],
        "binding_sha256": plan["target"]["binding_sha256"],
        "operation": "seed_demo",
        "project_ids": [],
        "empty_scope_observed": True,
    }
    seen = []
    monkeypatch.setattr(
        "t44.persistence.seed.seed_demo",
        lambda factory, **kw: seen.append(kw) or {"synthetic": True},
    )
    identity = {
        "database": plan["target"]["database"],
        "host": "mysql",
        "port": 3306,
        "username": plan["target"]["mysql_user"],
    }
    admin_seed.seed_in_admitted_context(plan, intent, object(), identity, now=NOW)
    assert seen[0] == {
        "projects": 40,
        "tasks": 6000,
        "dependencies": 9000,
        "records": 15000,
        "seed": 44,
        "anchor_at": guard.timestamp(plan["seed"]["anchor_utc"]),
    }
    with pytest.raises(guard.Refused):
        admin_seed.seed_in_admitted_context(
            plan, intent, object(), {**identity, "database": "unrelated"}, now=NOW
        )
    assert len(seen) == 1


def test_wrong_write_scope_and_default_template_refuse():
    plan, *_ = fixture()
    intent = {
        "run_id": plan["run_id"],
        "namespace": plan["namespace"],
        "database": "other",
        "binding_sha256": plan["target"]["binding_sha256"],
        "operation": "createTask",
        "project_ids": [1],
    }
    with pytest.raises(guard.Refused):
        guard.check_intent(plan, intent, NOW)
    with pytest.raises(guard.Refused):
        guard.check_plan(json.loads((CODE / "plan.template.PUBLIC.json").read_text()), NOW)


@pytest.mark.parametrize(
    "mutation", ["backend", "load", "dns", "mismatch", "loopback", "public", "window901"]
)
def test_review_target_guard_precedes_every_client_and_write(tmp_path, mutation):
    plan, *_ = fixture()
    if mutation == "backend":
        plan["images"]["backend"] = "sha256:" + sha("other-backend")
    elif mutation == "load":
        plan["images"]["load_python"] = "sha256:" + sha("other-load")
    elif mutation == "dns":
        plan["target"]["origin"] = "https://different.example:8443"
    elif mutation == "mismatch":
        plan["target"]["origin"] = "https://10.0.0.2:8443"
    elif mutation == "loopback":
        plan["target"].update(origin="https://127.0.0.1:8443", connect_ip="127.0.0.1")
    elif mutation == "public":
        plan["target"].update(origin="https://8.8.8.8:8443", connect_ip="8.8.8.8")
    elif mutation == "window901":
        start = guard.timestamp(plan["window"]["start_utc"])
        plan["window"]["end_utc"] = stamp(start + timedelta(seconds=901))
        stop = start + timedelta(seconds=1021)
        binding_path = Path(plan["gen_binding"]["path"])
        raw = json.loads(binding_path.read_text())
        raw["stop_utc"] = stamp(stop)
        data = json.dumps(raw).encode()
        binding_path.write_bytes(data)
        plan["gen_binding"]["sha256"] = plan["target"]["binding_sha256"] = hashlib.sha256(
            data
        ).hexdigest()
        plan["window"]["stop_utc"] = stamp(stop)
        plan["lifecycle"]["t0_utc"] = stamp(stop - timedelta(minutes=35))
        plan["lifecycle"]["cost_stop_utc"] = stamp(stop + timedelta(minutes=5))
    ca = tmp_path / "synthetic-ca.pem"
    ca.write_bytes(b"synthetic-ca")
    called = []

    def client(*args):
        called.append(True)
        raise RuntimeError("UNSAFE_CLIENT_CONSTRUCTION_BEFORE_TARGET_GUARD")

    with pytest.raises(guard.Refused):
        prepare_http.prepare(
            plan, {}, {}, ca, tmp_path / "output", clock=lambda: NOW, client_type=client
        )
    assert not called
    assert not (tmp_path / "output").exists()


def test_third_login_failure_keeps_original_first_two_prefixes(tmp_path):
    plan, evidence, sessions, _, receipt = fixture()
    ca = tmp_path / "ca.pem"
    ca.write_bytes(b"synthetic-ca")
    calls = []

    class LoginClient:
        def __init__(self, *args):
            self.last_meta = {"server_time": stamp(NOW)}

        def request(self, path, token=None, body=None):
            role = body["username"]
            calls.append(role)
            if role == "reviewer":
                raise RuntimeError("THIRD_LOGIN_SYNTHETIC_FAILURE")
            return {
                "access_token": sessions[role]["token"],
                "user": {"id": sessions[role]["user_id"]},
                "expires_at": sessions[role]["expires_at"],
            }

        def close(self):
            pass

    accounts = {
        role: {"username": role, "password": "synthetic-only", "user_id": sessions[role]["user_id"]}
        for role in ("manager", "developer", "reviewer")
    }
    service = {
        "session": sessions["service"],
        "attestation": evidence["session_attestations"]["service"],
    }
    with pytest.raises(RuntimeError, match="THIRD_LOGIN_SYNTHETIC_FAILURE"):
        prepare_http.prepare(
            plan,
            accounts,
            service,
            ca,
            tmp_path / "out",
            clock=lambda: NOW,
            client_type=LoginClient,
            import_receipt_raw=receipt,
        )
    assert calls == ["manager", "developer", "reviewer"]
    for role in ("manager", "developer"):
        path = tmp_path / "out" / "session-prefix" / (role + ".json")
        assert path.is_file()
        value = json.loads(path.read_text())
        assert value["original_login_data"]["access_token"] == sessions[role]["token"]
        assert value["original_login_data"]["expires_at"] == sessions[role]["expires_at"]
        assert path.stat().st_mode & 0o777 == 0o600
        assert value["login_request_started_at"] == stamp(NOW)
        assert value["response_observed_at"] == stamp(NOW)
        assert value["response_meta"]["server_time"] == stamp(NOW)


def test_all_owned_modules_real_compile_import_and_cli_help(tmp_path):
    for path in CODE.glob("*.py"):
        py_compile.compile(str(path), cfile=str(tmp_path / (path.stem + ".pyc")), doraise=True)
        importlib.import_module(path.stem)
    for name in (
        "admin.py",
        "prepare_http.py",
        "assemble.py",
        "make_evidence.py",
        "guard.py",
        "stage_scope.py",
    ):
        result = subprocess.run(
            [sys.executable, "-B", str(CODE / name), "--help"],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr


def test_complete_40_project_400_api_preparation_fake_only(tmp_path, monkeypatch):
    plan, evidence, sessions, _, receipt = fixture()
    ca = tmp_path / "ca.pem"
    ca.write_bytes(b"synthetic-ca")
    source_tasks = {
        item["escalation_task"]["id"]: deepcopy(item["escalation_task"])
        for item in evidence["inventory"]["clients"]
    }
    template = deepcopy(evidence["inventory"]["clients"][0]["transition_task"])
    events, calls, next_id, lock = {}, [], [6000], threading.Lock()

    def no_connection(*args, **kwargs):
        raise AssertionError("REAL_HTTPS_IS_FORBIDDEN_IN_THIS_TEST")

    monkeypatch.setattr("http.client.HTTPSConnection", no_connection)

    class FakeClient:
        def __init__(self, *args):
            self.last_meta = {"server_time": stamp(NOW)}

        def close(self):
            pass

        def request(self, path, token=None, body=None, method=None):
            with lock:
                calls.append((path, deepcopy(body)))
                parsed = urlsplit(path)
                parts, query = parsed.path.strip("/").split("/"), parse_qs(parsed.query)
                if parts == ["auth", "login"]:
                    role = body["username"]
                    return {
                        "access_token": sessions[role]["token"],
                        "user": {"id": sessions[role]["user_id"]},
                        "expires_at": sessions[role]["expires_at"],
                    }
                if parts == ["projects"]:
                    rows = [{"id": pid} for pid in range(1, 41)]
                else:
                    internal = parts[0] == "internal"
                    if internal:
                        parts = parts[1:]
                    pid = int(parts[1])
                    if parts[2] == "members":
                        rows = evidence["memberships"][str(pid)]
                    elif parts[2] == "iterations":
                        rows = [evidence["iterations"][str(pid)]]
                    elif parts[2] == "escalation-rules":
                        return {"version": 1}
                    elif parts[2] == "escalations":
                        rows = [deepcopy(events[int(query["task_id"][0])])]
                    elif parts[2] == "tasks" and len(parts) == 3:
                        if body is None:
                            rows = [
                                deepcopy(row)
                                for row in source_tasks.values()
                                if row["project_id"] == pid
                            ]
                        else:
                            next_id[0] += 1
                            row = {
                                **deepcopy(template),
                                **{
                                    key: deepcopy(body[key])
                                    for key in (
                                        "title",
                                        "description",
                                        "iteration_id",
                                        "owner_id",
                                        "plan",
                                    )
                                },
                                "id": next_id[0],
                                "project_id": pid,
                                "state": 1,
                                "version": 1,
                                "updated_at": stamp(NOW),
                            }
                            source_tasks[row["id"]] = row
                            return {"task": deepcopy(row)}
                    else:
                        tid = int(parts[3])
                        row = source_tasks[tid]
                        if len(parts) == 4:
                            return deepcopy(row)
                        if parts[4] == "dependencies":
                            rows = []
                        elif parts[4] == "transitions":
                            assert body == {"expected_version": row["version"], "action": 1}
                            row.update(state=2, version=row["version"] + 1, updated_at=stamp(NOW))
                            return {"task": deepcopy(row)}
                        elif internal and parts[4] == "escalations":
                            assert body["expected_version"] == row["version"]
                            row.update(
                                version=row["version"] + 1,
                                escalation_count=row["escalation_count"] + 1,
                            )
                            event = {
                                "id": tid + 10000,
                                "task_id": tid,
                                "project_id": pid,
                                "schedule_version": row["schedule_version"],
                                "rule_version": 1,
                                "level": 3,
                                "recipient_ids": [11, 12],
                                "disposition": 1,
                                "scan_run_id": body["scan_run_id"],
                                "created_at": stamp(NOW),
                                "handled_count": 0,
                            }
                            events[tid] = event
                            return {"event": deepcopy(event)}
                        else:
                            raise AssertionError(path)
                return {"items": deepcopy(rows), "total": len(rows), "page": 1, "page_size": 100}

    accounts = {
        role: {"username": role, "password": "synthetic-only", "user_id": sessions[role]["user_id"]}
        for role in ("manager", "developer", "reviewer")
    }
    service = {
        "session": sessions["service"],
        "attestation": evidence["session_attestations"]["service"],
    }
    result = prepare_http.prepare(
        plan,
        accounts,
        service,
        ca,
        tmp_path / "out",
        clock=lambda: NOW,
        client_type=FakeClient,
        import_receipt_raw=receipt,
    )
    assert len(result["inventory"]["clients"]) == 400 and next_id[0] == 6400
    assert sum(path == "/auth/login" for path, _ in calls) == 3
    assert sum(path.endswith("/transitions") for path, _ in calls) == 400
    assert sum(path.startswith("/internal/") for path, _ in calls) == 400
    assert json.loads((tmp_path / "out" / "sessions.json").read_text()) == sessions
    assert result["generated_complete_utc"] == stamp(NOW)
    assert all(
        "issued_at" not in result["session_attestations"][role]
        for role in ("manager", "developer", "reviewer")
    )


def test_stale_service_refuses_before_first_human_login(tmp_path):
    plan, evidence, sessions, _, receipt = fixture()
    service = {
        "session": sessions["service"],
        "attestation": evidence["session_attestations"]["service"],
    }
    service["session"]["expires_at"] = plan["window"]["end_utc"]
    ca = tmp_path / "ca.pem"
    ca.write_bytes(b"synthetic-ca")
    called = []

    def client(*args):
        called.append(True)
        raise RuntimeError("HUMAN_LOGIN_CLIENT_MUST_NOT_BE_CREATED")

    with pytest.raises(guard.Refused):
        prepare_http.prepare(
            plan,
            {},
            service,
            ca,
            tmp_path / "out",
            clock=lambda: NOW,
            client_type=client,
            import_receipt_raw=receipt,
        )
    assert not called


def test_exact_published_gen_scope_has_a_real_plan_intersection(tmp_path):
    plan, *_ = fixture()
    original = json.loads((CODE / "GEN_BINDING_SCHEMA_FIXTURE.PUBLIC.json").read_text())
    for key in EXACT_PROOF_FIELDS:
        assert key in GEN_FIELDS
        original[key] = {"synthetic_local_test_only": sha(key)}
    original["stop_utc"] = stamp(NOW + timedelta(seconds=1080))
    path = tmp_path / "synthetic-full-binding.json"
    raw = json.dumps(original).encode()
    path.write_bytes(raw)
    plan.update(run_id="r30window01", namespace=original["project"])
    plan["target"].update(
        compose_project=original["project"],
        database=original["database"],
        mysql_user=original["database"] + "_app",
        binding_sha256=hashlib.sha256(raw).hexdigest(),
        origin="https://10.0.0.1:26445",
    )
    plan["gen_binding"] = {"path": str(path), "sha256": hashlib.sha256(raw).hexdigest()}
    plan["window"] = {
        "start_utc": stamp(NOW + timedelta(seconds=180)),
        "end_utc": stamp(NOW + timedelta(seconds=960)),
        "stop_utc": original["stop_utc"],
    }
    plan["lifecycle"] = {
        "t0_utc": stamp(NOW - timedelta(seconds=1020)),
        "cost_stop_utc": stamp(NOW + timedelta(seconds=1380)),
        "packet_cutoff_utc": stamp(NOW + timedelta(seconds=30)),
    }
    assert guard.check_plan(plan, NOW)[0] == guard.timestamp(plan["window"]["start_utc"])


@pytest.mark.parametrize(
    "mutation",
    [
        "raw_sha",
        "run",
        "database",
        "gen_stop",
        "cost_is_not_gen_stop",
        "late_packet",
        "minimal_projection",
    ],
)
def test_gen_binding_and_lifecycle_refuse_before_action(tmp_path, mutation):
    plan, *_ = fixture()
    if mutation == "raw_sha":
        plan["gen_binding"]["sha256"] = sha("wrong-raw")
    elif mutation == "run":
        plan["run_id"] = "r30window02"
    elif mutation == "database":
        plan["target"]["database"] = "t44c_r30window01_f"
    elif mutation == "gen_stop":
        plan["window"]["stop_utc"] = stamp(NOW + timedelta(seconds=1079))
    elif mutation == "cost_is_not_gen_stop":
        plan["window"]["stop_utc"] = plan["lifecycle"]["cost_stop_utc"]
    elif mutation == "late_packet":
        plan["lifecycle"]["packet_cutoff_utc"] = stamp(NOW - timedelta(seconds=1))
    elif mutation == "minimal_projection":
        raw = (CODE / "GEN_BINDING_SCHEMA_FIXTURE.PUBLIC.json").read_bytes()
        path = tmp_path / "minimal-only.json"
        path.write_bytes(raw)
        plan["gen_binding"] = {"path": str(path), "sha256": hashlib.sha256(raw).hexdigest()}
        plan["target"]["binding_sha256"] = plan["gen_binding"]["sha256"]
    with pytest.raises(guard.Refused):
        guard.check_plan(plan, NOW)


def test_seed_before_project_ids_then_actual_count_scope_without_retime():
    plan, *_ = fixture()
    plan["authorized_project_ids"] = []
    plan["runtime_roles"]["scheduler"]["running_observed"] = False
    intent = {
        "run_id": plan["run_id"],
        "namespace": plan["namespace"],
        "database": plan["target"]["database"],
        "binding_sha256": plan["target"]["binding_sha256"],
        "operation": "seed_demo",
        "project_ids": [],
        "empty_scope_observed": True,
    }
    assert guard.check_intent(plan, intent, NOW)["status"] == "METADATA_CONSISTENT_NOT_EXECUTED"
    scope = importlib.import_module("stage_scope")
    counts = {key: intent[key] for key in ("run_id", "namespace", "database", "binding_sha256")}
    counts.update(project_ids=list(range(101, 141)), raw_counts={"projects": 40})
    result = scope.advance(
        plan, counts, ["login", "service-token", "createTask", "transitionTask", "createEscalation"]
    )
    assert result["authorized_project_ids"] == list(range(101, 141))
    assert plan["authorized_project_ids"] == []
    for key in ("source", "target", "gen_binding", "window", "lifecycle"):
        assert result[key] == plan[key]


@pytest.mark.parametrize("variant", ["exact_gen_keys", "wrong_short_name", "missing_proof"])
def test_actual_gen_cryptographic_field_contract(variant):
    plan, *_ = fixture()
    path = Path(plan["gen_binding"]["path"])
    value = json.loads(path.read_text())
    assert set(value) <= GEN_FIELDS
    if variant != "exact_gen_keys":
        proof = value.pop("cryptographic_transport_proofs")
        if variant == "wrong_short_name":
            value["crypto_transport_proofs"] = proof
        raw = json.dumps(value).encode()
        path.write_bytes(raw)
        plan["gen_binding"]["sha256"] = plan["target"]["binding_sha256"] = hashlib.sha256(
            raw
        ).hexdigest()
        with pytest.raises(guard.Refused):
            guard.check_plan(plan, NOW)
    else:
        assert guard.check_plan(plan, NOW)[0] == guard.timestamp(plan["window"]["start_utc"])


def test_every_required_binding_key_exists_in_original_gen_dictionary():
    tree = ast.parse((CODE / "guard.py").read_text())
    keys = {
        node.slice.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Subscript)
        and isinstance(node.value, ast.Name)
        and node.value.id == "binding"
        and isinstance(node.slice, ast.Constant)
        and isinstance(node.slice.value, str)
    }
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.GeneratorExp)
            and isinstance(node.elt, ast.Call)
            and isinstance(node.elt.func, ast.Attribute)
            and isinstance(node.elt.func.value, ast.Name)
            and node.elt.func.value.id == "binding"
            and node.elt.func.attr == "get"
        ):
            for generator in node.generators:
                if isinstance(generator.iter, ast.Tuple):
                    keys.update(item.value for item in generator.iter.elts)
    assert keys <= GEN_FIELDS, sorted(keys - GEN_FIELDS)
    assert "cryptographic_transport_proofs" in GEN_FIELDS
    assert "crypto_transport_proofs" not in GEN_FIELDS
