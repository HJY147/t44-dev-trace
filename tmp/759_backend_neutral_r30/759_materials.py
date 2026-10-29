"""Synthetic local checks only: no server, real account, signature or session issuance."""

import hashlib
import importlib
import json
import sys
from copy import deepcopy
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

CODE = Path(__file__).resolve().parents[2] / "agents/backend/neutral-r30"
sys.path.insert(0, str(CODE))
admin_seed = importlib.import_module("admin_seed")
assemble = importlib.import_module("assemble")
guard = importlib.import_module("guard")
prepare_http = importlib.import_module("prepare_http")

NOW = datetime(2026, 11, 1, 12, tzinfo=UTC)


def stamp(value):
    return value.isoformat(timespec="microseconds").replace("+00:00", "Z")


def sha(value):
    return hashlib.sha256(value.encode()).hexdigest()


def fixture():
    plan = json.loads((CODE / "plan.template.PUBLIC.json").read_text())
    plan.update(
        root_admit_preparation=True,
        run_id="r30-synthetic-tests",
        namespace="t44-r30-synthetic-tests",
        authorized_project_ids=list(range(1, 41)),
        allowed_writes=list(guard.OPERATIONS),
    )
    plan["target"].update(
        compose_project=plan["namespace"],
        database="t44_r30_synthetic_tests",
        mysql_user="t44_r30_synthetic_tests_app",
        binding_sha256=sha("binding"),
        origin="https://10.0.0.1:8443",
        connect_ip="10.0.0.1",
        ca_sha256=sha("synthetic-ca"),
    )
    plan["budget"]["actual_admission_receipt_sha256"] = sha("synthetic-budget")
    plan["window"] = {
        "start_utc": stamp(NOW + timedelta(seconds=120)),
        "end_utc": stamp(NOW + timedelta(seconds=1020)),
        "stop_utc": stamp(NOW + timedelta(seconds=1110)),
    }
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
        evidence["session_attestations"]["manager"]["issued_at"] = stamp(
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


@pytest.mark.parametrize("mutation", ["backend", "load", "dns", "mismatch", "loopback", "public", "window901"])
def test_review_target_guard_precedes_every_client_and_write(tmp_path, mutation):
    plan, *_ = fixture()
    if mutation == "backend": plan["images"]["backend"] = "sha256:" + sha("other-backend")
    elif mutation == "load": plan["images"]["load_python"] = "sha256:" + sha("other-load")
    elif mutation == "dns": plan["target"]["origin"] = "https://different.example:8443"
    elif mutation == "mismatch": plan["target"]["origin"] = "https://10.0.0.2:8443"
    elif mutation == "loopback": plan["target"].update(origin="https://127.0.0.1:8443", connect_ip="127.0.0.1")
    elif mutation == "public": plan["target"].update(origin="https://8.8.8.8:8443", connect_ip="8.8.8.8")
    elif mutation == "window901":
        plan["window"]["end_utc"] = stamp(NOW + timedelta(seconds=1021))
        plan["window"]["stop_utc"] = stamp(NOW + timedelta(seconds=1111))
    ca = tmp_path / "synthetic-ca.pem"
    ca.write_bytes(b"synthetic-ca")
    called = []
    def client(*args):
        called.append(True)
        raise RuntimeError("UNSAFE_CLIENT_CONSTRUCTION_BEFORE_TARGET_GUARD")
    with pytest.raises(guard.Refused):
        prepare_http.prepare(plan, {}, {}, ca, tmp_path / "output", clock=lambda: NOW, client_type=client)
    assert not called
    assert not (tmp_path / "output").exists()
