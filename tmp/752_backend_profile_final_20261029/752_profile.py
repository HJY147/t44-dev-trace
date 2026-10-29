"""Synthetic local target facts only; never claims real root approval/image/session."""

import hashlib
import importlib
import json
import os
import py_compile
import shutil
import subprocess
import sys
from copy import deepcopy
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
CODE = ROOT / "agents/backend/neutral-final-20261029"
sys.path.insert(0, str(CODE))
guard = importlib.import_module("guard")
prepare = importlib.import_module("prepare_http")
NOW = datetime(2026, 11, 2, 12, tzinfo=UTC)


def sha(value):
    return hashlib.sha256(value.encode() if isinstance(value, str) else value).hexdigest()


def raw(value):
    return json.dumps(value, sort_keys=True).encode()


def stamp(value):
    return value.isoformat().replace("+00:00", "Z")


@pytest.fixture
def target(tmp_path, monkeypatch):
    directory = tmp_path / "synthetic-producer"
    directory.mkdir()
    monkeypatch.setattr(guard, "PRODUCER_DIRECTORY", directory)
    records = [
        {"path": name, "bytes": 12, "mode": 420, "sha256": sha(name)}
        for name in (
            "backend/t44/api.py",
            "backend/requirements.lock",
            "frontend/package-lock.json",
        )
    ]
    source = {
        "kind": "final-exact-public-runtime-context-v1",
        "source_sha": guard.SOURCE,
        "source_archive_sha256": sha("synthetic archive"),
        "files": records,
        "context_file_count": 3,
        "backend_runtime_files": records[:2],
        "dependency_lock_sha256": records[1]["sha256"],
        "frontend_lock_sha256": records[2]["sha256"],
    }
    source_raw = raw(source)
    (directory / "source-manifest.json").write_bytes(source_raw)
    configs = {
        role: "sha256:" + sha("synthetic config " + role)
        for role in ("backend", "web", "load_python")
    }
    probe = sha("synthetic actual fileprobe bytes")
    bundle = {
        "kind": "final-backend-web-bundle-v1",
        "source_sha": guard.SOURCE,
        "source_manifest_sha256": sha(source_raw),
        "source_archive_sha256": source["source_archive_sha256"],
        "images": {
            role: {
                "image_id": configs[role],
                "revision_label": guard.SOURCE,
                "archive_label": source["source_archive_sha256"],
            }
            for role in ("backend", "web")
        },
        "runtime_file_count": 2,
        "official_load_python_identity": {
            "success": True,
            "identity_kind": "classic-config-id",
            "actual_id": configs["load_python"],
            "config_id": configs["load_python"],
            "ordered_layer_count": 4,
            "labels_architecture_rootfs_checked": True,
        },
        "files": {"actual-runtime-files.json": {"sha256": probe, "bytes": 999}},
    }
    bundle_raw = raw(bundle)
    (directory / "backend-bundle-manifest.json").write_bytes(bundle_raw)
    profile = {
        "schema": "t44-final-source-profile-v1",
        "version": 1,
        "root_approved": True,
        "source_sha": guard.SOURCE,
        "source_manifest_sha256": sha(source_raw),
        "backend_bundle_manifest_sha256": sha(bundle_raw),
        "root_manifest_sha256": sha(bundle_raw),
        "backend_config_id": configs["backend"],
        "web_config_id": configs["web"],
        "load_python_config_id": configs["load_python"],
        "backend_requirements_lock_sha256": source["dependency_lock_sha256"],
        "frontend_lock_sha256": source["frontend_lock_sha256"],
        "runtime_files": {r["path"]: r["sha256"] for r in records[:2]},
        "runtime_file_count": 2,
        "context_file_count": 3,
        "actual_build_receipt_sha256": probe,
        "gen_kind": "r30-official-backend-production-entry-window-v1",
        "budget_helper_sha256": guard.BUDGET_HELPER,
        "actual_loaded": False,
        "qa_adapter_sha256": guard.NEW_ADAPTER,
        "qa_approval_receipt_sha256": sha("synthetic new 753 approval"),
    }
    profile_path = tmp_path / "synthetic-profile.json"
    profile_path.write_bytes(raw(profile))
    plan = json.loads((CODE / "plan.template.PUBLIC.json").read_bytes())
    plan.update(
        root_admit_preparation=True, run_id="r30finaltest", namespace="t44-cloud-r30finaltest-p"
    )
    plan["source_profile"] = {"path": str(profile_path), "sha256": sha(profile_path.read_bytes())}
    plan["source"].update(
        git_commit=guard.SOURCE,
        manifest_sha256=profile["source_manifest_sha256"],
        bundle_manifest_sha256=profile["backend_bundle_manifest_sha256"],
        context_records=3,
        expected_runtime_files=2,
        files_proof_sha256=sha("files proof"),
        artifact_sha256=sha("artifact"),
        actual_loaded_receipt_path="/synthetic-only/import-original.json",
        actual_loaded_observed_at=stamp(NOW - timedelta(seconds=30)),
        actual_loaded_full_chain_reviewed_by_root=True,
    )
    plan["images"].update(backend=configs["backend"], load_python=configs["load_python"])
    plan["budget"]["actual_admission_receipt_sha256"] = sha("synthetic original GEN probe")
    plan["public_tool_approval"].update(
        supports_source_git=guard.SOURCE,
        receipt_sha256=profile["qa_approval_receipt_sha256"],
        adapter_sha256=guard.NEW_ADAPTER,
        root_relayed_approval=True,
    )
    plan["target"].update(
        compose_project=plan["namespace"],
        database="t44c_r30finaltest_p",
        mysql_user="t44c_r30finaltest_p_app",
        origin="https://10.0.0.1:26445",
        connect_ip="10.0.0.1",
        ca_sha256=sha("synthetic-ca"),
    )
    t0 = NOW - timedelta(minutes=5)
    plan["window"] = {
        "start_utc": stamp(NOW + timedelta(minutes=10)),
        "end_utc": stamp(NOW + timedelta(minutes=23)),
        "stop_utc": stamp(t0 + timedelta(minutes=35)),
    }
    plan["lifecycle"] = {
        "t0_utc": stamp(t0),
        "cost_stop_utc": stamp(t0 + timedelta(minutes=40)),
        "packet_cutoff_utc": stamp(NOW + timedelta(minutes=7, seconds=30)),
    }
    plan["seed"].update(seed=44, anchor_utc=stamp(NOW - timedelta(days=1)))
    for key in ("source", "images", "transfer", "preflight"):
        plan["readiness"][key] = {
            "sha256": sha(key),
            "completed_at": stamp(NOW - timedelta(minutes=2)),
        }
    plan["readiness"].update(
        all_ready_at=stamp(NOW - timedelta(minutes=1)),
        fixture_ready_at=stamp(NOW - timedelta(seconds=30)),
        admin_preserves_image_pythonpath=True,
    )
    for role in plan["runtime_roles"]:
        plan["runtime_roles"][role].update(
            required=True, running_observed=True, receipt_sha256=sha(role)
        )
    binding = {
        "kind": "isolated-cloud-campaign",
        "generation_kind": profile["gen_kind"],
        "phase": "p",
        "project": plan["namespace"],
        "database": plan["target"]["database"],
        "source_sha": guard.SOURCE,
        "source_manifest_sha256": profile["source_manifest_sha256"],
        "upgrade_binding_sha256": profile["backend_bundle_manifest_sha256"],
        "stop_utc": plan["window"]["stop_utc"],
        "app_private_ip": "10.0.0.1",
        "tls_port": 26445,
        **{
            key: {"synthetic_only": True}
            for key in (
                "config_ids",
                "image_ids",
                "cryptographic_transport_proofs",
                "tls",
                "file_hashes",
            )
        },
    }
    binding_path = tmp_path / "synthetic-binding.json"
    binding_path.write_bytes(raw(binding))
    plan["gen_binding"] = {"path": str(binding_path), "sha256": sha(binding_path.read_bytes())}
    plan["target"]["binding_sha256"] = plan["gen_binding"]["sha256"]
    identities = {
        role: {
            "success": True,
            "identity_kind": "classic-config-id",
            "actual_id": configs[role],
            "config_id": configs[role],
            "ordered_layer_count": 5,
            "labels_architecture_rootfs_checked": True,
        }
        for role in ("backend", "web")
    }
    receipt = {
        "kind": "final-backend-web-import-v1",
        "observed_utc": plan["source"]["actual_loaded_observed_at"],
        "images_loaded_this_observation": False,
        "source_sha": guard.SOURCE,
        "source_manifest_sha256": profile["source_manifest_sha256"],
        "bundle_manifest_sha256": profile["backend_bundle_manifest_sha256"],
        "full_runtime_files": 2,
        "identity": deepcopy(identities["backend"]),
        "identities": identities,
        "business_services_started": False,
        "volumes_modified": False,
        "package_resolution": {
            "uid": 10001,
            "package_origin": "/app/backend/t44/__init__.py",
            "python_version": "SYNTHETIC_LOCAL_ONLY",
            "sys_executable": "/synthetic/python",
            "business_env_absent": True,
            "files": deepcopy(records[:2]),
        },
    }
    plan["source"]["actual_loaded_receipt_sha256"] = sha(raw(receipt))
    return plan, profile, receipt, directory, profile_path


def save_profile(plan, profile, path):
    path.write_bytes(raw(profile))
    plan["source_profile"]["sha256"] = sha(path.read_bytes())


def test_new_source_dynamic_context_and_runtime_are_accepted_as_metadata_only(target):
    plan, profile, receipt, _, _ = target
    assert guard.load_source_profile(plan) == profile
    assert guard.check_plan(plan, NOW)[0] == guard.timestamp(plan["window"]["start_utc"])
    assert guard.validate_loaded_receipt(plan, raw(receipt)) == receipt
    assert profile["runtime_file_count"] == 2 and profile["context_file_count"] == 3
    assert profile["actual_loaded"] is False


@pytest.mark.parametrize(
    "key,value",
    [
        ("root_approved", False),
        ("source_sha", None),
        ("source_sha", "0bffe0c535e5897890aebf30879fdd3839dc52d6"),
        ("backend_config_id", None),
        ("backend_config_id", "TBD"),
        ("load_python_config_id", None),
        ("runtime_files", {}),
        ("runtime_file_count", 60),
        ("context_file_count", 62),
        ("source_manifest_sha256", sha("other")),
        ("backend_bundle_manifest_sha256", sha("other")),
        ("root_manifest_sha256", sha("other")),
        ("actual_build_receipt_sha256", sha("other")),
        ("actual_loaded", True),
        ("gen_kind", "other"),
        ("budget_helper_sha256", sha("old helper")),
    ],
)
def test_profile_placeholder_stale_or_mismatched_target_refused(target, key, value):
    plan, profile, _, _, path = target
    profile[key] = value
    save_profile(plan, profile, path)
    with pytest.raises((guard.Refused, KeyError, TypeError, ValueError)):
        guard.load_source_profile(plan)


def test_raw_profile_hash_and_source_manifest_hash_are_binding(target):
    plan, profile, _, directory, path = target
    path.write_bytes(path.read_bytes() + b" ")
    with pytest.raises(guard.Refused, match="METADATA_RAW_SHA_MISMATCH"):
        guard.load_source_profile(plan)
    save_profile(plan, profile, path)
    (directory / "source-manifest.json").write_text("{}")
    with pytest.raises(guard.Refused, match="METADATA_RAW_SHA_MISMATCH"):
        guard.load_source_profile(plan)


@pytest.mark.parametrize(
    "field,value",
    [
        ("qa_adapter_sha256", sha("not approved")),
        ("qa_approval_receipt_sha256", sha("old receipt")),
    ],
)
def test_actual_qa_approval_has_to_match_new_source_profile(target, field, value):
    plan, profile, _, _, path = target
    profile[field] = value
    save_profile(plan, profile, path)
    with pytest.raises(guard.Refused):
        guard.check_plan(plan, NOW)


@pytest.mark.parametrize(
    "case",
    [
        "old-kind",
        "wrong-source",
        "old-count",
        "wrong-config",
        "false-chain",
        "wrong-uid",
        "business-env",
        "missing-file",
        "duplicate-file",
        "path-escape",
        "wrong-file-sha",
        "wrong-size",
        "wrong-mode",
    ],
)
def test_actual_import_checks_exact_identity_and_complete_runtime_records(target, case):
    plan, _, receipt, _, _ = target
    if case == "old-kind":
        receipt["kind"] = "r30-backend-import-receipt-v1"
    elif case == "wrong-source":
        receipt["source_sha"] = "0bffe0c535e5897890aebf30879fdd3839dc52d6"
    elif case == "old-count":
        receipt["full_runtime_files"] = 60
    elif case == "wrong-config":
        receipt["identities"]["backend"]["config_id"] = "sha256:" + sha("other")
    elif case == "false-chain":
        receipt["identities"]["backend"]["labels_architecture_rootfs_checked"] = False
    elif case == "wrong-uid":
        receipt["package_resolution"]["uid"] = 0
    elif case == "business-env":
        receipt["package_resolution"]["business_env_absent"] = False
    elif case == "missing-file":
        receipt["package_resolution"]["files"].pop()
    elif case == "duplicate-file":
        receipt["package_resolution"]["files"][1] = deepcopy(
            receipt["package_resolution"]["files"][0]
        )
    elif case == "path-escape":
        receipt["package_resolution"]["files"][0]["path"] = "../backend/t44/api.py"
    elif case == "wrong-file-sha":
        receipt["package_resolution"]["files"][0]["sha256"] = sha("other")
    elif case == "wrong-size":
        receipt["package_resolution"]["files"][0]["bytes"] += 1
    elif case == "wrong-mode":
        receipt["package_resolution"]["files"][0]["mode"] = 493
    receipt["identity"] = deepcopy(receipt["identities"]["backend"])
    plan["source"]["actual_loaded_receipt_sha256"] = sha(raw(receipt))
    with pytest.raises((guard.Refused, KeyError, TypeError, ValueError)):
        guard.validate_loaded_receipt(plan, raw(receipt))


def test_oci_descriptor_is_distinct_from_config_with_complete_proofs(target):
    plan, _, receipt, _, _ = target
    for identity in receipt["identities"].values():
        identity.update(
            identity_kind="oci-descriptor-to-original-config",
            actual_id="sha256:" + sha("actual OCI descriptor"),
            actual_descriptor_sha256_recomputed_from_archive=True,
            all_config_and_layer_descriptors_sha256_size_verified=True,
        )
    receipt["identity"] = deepcopy(receipt["identities"]["backend"])
    plan["source"]["actual_loaded_receipt_sha256"] = sha(raw(receipt))
    assert guard.validate_loaded_receipt(plan, raw(receipt)) == receipt
    receipt["identities"]["backend"]["all_config_and_layer_descriptors_sha256_size_verified"] = (
        False
    )
    receipt["identity"] = deepcopy(receipt["identities"]["backend"])
    plan["source"]["actual_loaded_receipt_sha256"] = sha(raw(receipt))
    with pytest.raises(guard.Refused):
        guard.validate_loaded_receipt(plan, raw(receipt))


def test_unapproved_profile_refuses_complete_http_entry_before_client_or_output(target, tmp_path):
    plan, profile, _, _, path = target
    profile["root_approved"] = False
    save_profile(plan, profile, path)
    calls = []

    def forbidden(*args):
        calls.append(args)
        raise AssertionError("CLIENT_MUST_NOT_EXIST")

    with pytest.raises(guard.Refused, match="ROOT_APPROVED_ACTUAL_SOURCE_PROFILE_REQUIRED"):
        prepare.prepare(
            plan,
            {},
            {},
            tmp_path / "absent-ca",
            tmp_path / "new-out",
            clock=lambda: NOW,
            client_type=forbidden,
        )
    assert not calls and not (tmp_path / "new-out").exists()


def test_all_runtime_modules_compile_and_helpers_resolve_real_local_package(target, tmp_path):
    plan, profile, _, directory, _ = target
    for path in CODE.glob("*.py"):
        py_compile.compile(str(path), cfile=str(tmp_path / (path.stem + ".pyc")), doraise=True)
        importlib.import_module(path.stem)
    helper = importlib.import_module("escalation_readback")
    result = helper.check_runtime_only(plan)
    assert result["required_backend_config"] == profile["backend_config_id"]
    assert result["actual_image_identity_verified_by_probe"] is False
    assert result["scope"] == "PACKAGE_RESOLUTION_ONLY_NOT_IMAGE_OR_CLOUD_READINESS"
    # Real CLI in an isolated synthetic code directory, same source bytes and real t44.
    for path in CODE.glob("*.py"):
        shutil.copyfile(path, directory / path.name)
    plan_path = tmp_path / "synthetic-plan.json"
    plan_path.write_bytes(raw(plan))
    process = subprocess.run(
        [
            sys.executable,
            "-B",
            str(directory / "escalation_readback.py"),
            "--check-runtime-only",
            "--plan",
            str(plan_path),
        ],
        env=dict(os.environ, PYTHONPATH=str(ROOT / "backend")),
        capture_output=True,
        text=True,
    )
    assert process.returncode == 0, process.stderr
    assert json.loads(process.stdout)["required_backend_config"] == profile["backend_config_id"]


@pytest.mark.parametrize("role", ["backend", "load_python"])
def test_plan_cannot_override_approved_profile_config_identity(target, role):
    plan, *_ = target
    plan["images"][role] = "sha256:" + sha("other valid config")
    with pytest.raises(guard.Refused):
        guard.check_plan(plan, NOW)


def test_actual_public_ci_build_shape_is_valid_without_granting_root_approval(monkeypatch):
    monkeypatch.setattr(guard, "PRODUCER_DIRECTORY", CODE)
    profile = json.loads((CODE / "source-profile.BUILD_UNAPPROVED.PUBLIC.json").read_bytes())
    checked = guard.check_source_profile_facts(profile)
    assert checked is profile and checked["root_approved"] is False
    assert checked["actual_loaded"] is False
    assert checked["context_file_count"] == 94 and checked["runtime_file_count"] == 60
    assert (
        checked["load_python_config_id"]
        == "sha256:3c4d812a6efe003770aafbdba65f9c1960ba8234ab23a133934205a70bdcda77"
    )
    path = CODE / "source-profile.BUILD_UNAPPROVED.PUBLIC.json"
    plan = {"source_profile": {"path": str(path.resolve()), "sha256": sha(path.read_bytes())}}
    with pytest.raises(guard.Refused, match="ROOT_APPROVED_ACTUAL_SOURCE_PROFILE_REQUIRED"):
        guard.load_source_profile(plan)


def test_actual_observation_time_must_match_original_receipt_without_retime(target):
    plan, _, receipt, _, _ = target
    receipt["observed_utc"] = stamp(NOW - timedelta(days=1))
    plan["source"]["actual_loaded_receipt_sha256"] = sha(raw(receipt))
    with pytest.raises(guard.Refused):
        guard.validate_loaded_receipt(plan, raw(receipt))
