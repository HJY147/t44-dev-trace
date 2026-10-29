"""Local metadata consistency guards. Never connects, issues sessions or authorizes a run."""

import argparse
import hashlib
import ipaddress
import json
import re
from datetime import UTC, datetime, timedelta
from pathlib import Path, PurePosixPath
from urllib.parse import urlsplit

SOURCE = "356f29983c904e949245aedfad464efc1bf7b63d"
PRODUCER_DIRECTORY = Path(__file__).resolve().parent
OPENAPI = "6f07cb53a7d9314240ba93ec490325d3c63dca7e4d077021047e216e7b26f478"
OLD_ADAPTER = "7b785defc44c91754ec4ea5a25cc07edced3605a130f4436d68572d1aec1ba18"
NEW_ADAPTER = "15b91449627218b011fff0768b1f84fe2e9274ec06c0486fd28f2ae9dce03f5d"
BUDGET_HELPER = "9e98632fa1885bf4327b04a95daeba5cee4ad909b536e91ac8b11a1e58488a61"
APP_ROLES = {"mysql", "rabbit", "api", "consumer", "scheduler", "web", "tls-gateway"}
IDENTITIES = {"manager", "developer", "reviewer", "service"}
BASE_COUNTS = {"projects": 40, "tasks": 6000, "dependencies": 9000, "reviews_and_decisions": 15000}
OPERATIONS = {
    "seed_demo",
    "init-user",
    "login",
    "service-token",
    "createTask",
    "transitionTask",
    "createEscalation",
    "addProjectMember",
    "createIteration",
}
SECRET_KEYS = {"token", "access_token", "password", "private_key", "database_url"}


class Refused(ValueError):
    pass


def need(condition, code):
    if not condition:
        raise Refused(code)


def timestamp(value):
    need(
        isinstance(value, str)
        and re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z", value),
        "EXACT_UTC_REQUIRED",
    )
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        raise Refused("INVALID_UTC") from None


def digest(value, *, image=False):
    pattern = r"sha256:[0-9a-f]{64}" if image else r"[0-9a-f]{64}"
    need(isinstance(value, str) and re.fullmatch(pattern, value), "ACTUAL_DIGEST_REQUIRED")
    need(len(set(value.removeprefix("sha256:"))) > 1, "PLACEHOLDER_DIGEST_REFUSED")


def no_secrets(value):
    if isinstance(value, dict):
        need(not SECRET_KEYS.intersection(value), "METADATA_ONLY_NO_CREDENTIAL_INPUT")
        for item in value.values():
            no_secrets(item)
    elif isinstance(value, list):
        for item in value:
            no_secrets(item)


def runtime_map(records, *, context=False):
    need(isinstance(records, list) and records, "COMPLETE_NONEMPTY_RUNTIME_RECORDS_REQUIRED")
    result = {}
    for record in records:
        name = record["path"]
        need(isinstance(name, str), "REPOSITORY_RELATIVE_RUNTIME_PATH_REQUIRED")
        path = PurePosixPath(name)
        need(
            not path.is_absolute()
            and ".." not in path.parts
            and str(path) == name
            and name.startswith(
                ("backend/", "specs/", "deployment/") + (("frontend/",) if context else ())
            )
            and name not in result
            and type(record["bytes"]) is int
            and record["bytes"] >= 0
            and type(record["mode"]) is int
            and record["mode"] in (420, 493),
            "EXACT_UNIQUE_PUBLIC_RUNTIME_RECORD_REQUIRED",
        )
        digest(record["sha256"])
        result[name] = record["sha256"]
    return result


def validate_image_identity(identity, expected_config):
    need(
        identity["success"] is True
        and identity["config_id"] == expected_config
        and type(identity["ordered_layer_count"]) is int
        and identity["ordered_layer_count"] > 0
        and identity["labels_architecture_rootfs_checked"] is True,
        "ACTUAL_IMAGE_CONFIG_AND_COMPLETE_CHAIN_REQUIRED",
    )
    digest(identity["actual_id"], image=True)
    need(
        (
            identity["identity_kind"] == "classic-config-id"
            and identity["actual_id"] == identity["config_id"]
        )
        or (
            identity["identity_kind"] == "oci-descriptor-to-original-config"
            and identity["actual_descriptor_sha256_recomputed_from_archive"] is True
            and identity["all_config_and_layer_descriptors_sha256_size_verified"] is True
        ),
        "ACTUAL_DOCKER_IDENTITY_KIND_CHAIN_REQUIRED",
    )


def load_source_profile(plan):
    reference = plan["source_profile"]
    digest(reference["sha256"])
    need(Path(reference["path"]).is_absolute(), "EXACT_ABSOLUTE_SOURCE_PROFILE_REQUIRED")
    profile = read_json(reference["path"], expected_sha256=reference["sha256"])
    need(profile.get("root_approved") is True, "ROOT_APPROVED_ACTUAL_SOURCE_PROFILE_REQUIRED")
    return check_source_profile_facts(profile)


def check_source_profile_facts(profile):
    """Pure local metadata checks only; this does not approve or authorize a profile."""
    need(
        profile.get("schema") == "t44-final-source-profile-v1"
        and type(profile.get("version")) is int
        and profile["version"] == 1,
        "SOURCE_PROFILE_SCHEMA_REQUIRED",
    )
    no_secrets(profile)
    need(profile.get("source_sha") == SOURCE, "ONLY_ROOT_FROZEN_FINAL_PRODUCT_SOURCE_SUPPORTED")
    need(profile.get("actual_loaded") is False, "BUILD_PROFILE_IS_NOT_ACTUAL_APP_IMPORT")
    need(
        profile.get("gen_kind") == "r30-official-backend-production-entry-window-v1"
        and profile.get("budget_helper_sha256") == BUDGET_HELPER,
        "SAME_REVIEWED_GENERATION_AND_BUDGET_REQUIRED",
    )
    for name in (
        "source_manifest_sha256",
        "backend_bundle_manifest_sha256",
        "root_manifest_sha256",
        "backend_requirements_lock_sha256",
        "frontend_lock_sha256",
        "actual_build_receipt_sha256",
    ):
        digest(profile[name])
    for name in ("backend_config_id", "web_config_id", "load_python_config_id"):
        digest(profile[name], image=True)
    need(
        type(profile["runtime_file_count"]) is int
        and profile["runtime_file_count"] > 0
        and type(profile["context_file_count"]) is int
        and profile["context_file_count"] >= profile["runtime_file_count"],
        "ACTUAL_DYNAMIC_FILE_COUNTS_REQUIRED",
    )
    source = read_json(
        PRODUCER_DIRECTORY / "source-manifest.json",
        expected_sha256=profile["source_manifest_sha256"],
    )
    bundle = read_json(
        PRODUCER_DIRECTORY / "backend-bundle-manifest.json",
        expected_sha256=profile["backend_bundle_manifest_sha256"],
    )
    need(
        source["kind"] == "final-exact-public-runtime-context-v1"
        and bundle["kind"] == "final-backend-web-bundle-v1"
        and source["source_sha"] == bundle["source_sha"] == profile["source_sha"]
        and bundle["source_manifest_sha256"] == profile["source_manifest_sha256"]
        and source["dependency_lock_sha256"] == profile["backend_requirements_lock_sha256"]
        and source["frontend_lock_sha256"] == profile["frontend_lock_sha256"],
        "SAME_ACTUAL_BUILD_MANIFESTS_AND_LOCKS_REQUIRED",
    )
    need(
        len(source["files"]) == profile["context_file_count"]
        and source["context_file_count"] == profile["context_file_count"]
        and bundle["runtime_file_count"] == profile["runtime_file_count"]
        and len(source["backend_runtime_files"]) == profile["runtime_file_count"]
        and runtime_map(source["backend_runtime_files"]) == profile["runtime_files"],
        "COMPLETE_ACTUAL_PROFILE_RUNTIME_SET_REQUIRED",
    )
    context_files = runtime_map(source["files"], context=True)
    need(
        all(
            context_files.get(name) == digest_value
            for name, digest_value in profile["runtime_files"].items()
        ),
        "RUNTIME_SET_MUST_MATCH_PUBLIC_SOURCE_CONTEXT",
    )
    need(
        profile["root_manifest_sha256"] == profile["backend_bundle_manifest_sha256"]
        and source["source_archive_sha256"] == bundle["source_archive_sha256"]
        and profile["actual_build_receipt_sha256"]
        == bundle["files"]["actual-runtime-files.json"]["sha256"],
        "SAME_ROOT_BUNDLE_ARCHIVE_AND_ACTUAL_CI_FILEPROBE_REQUIRED",
    )
    for role in ("backend", "web"):
        image = bundle["images"][role]
        need(
            image["image_id"] == profile[role + "_config_id"]
            and image["revision_label"] == SOURCE
            and image["archive_label"] == source["source_archive_sha256"],
            "EXACT_BUILT_IMAGE_CONFIG_AND_REVISION_REQUIRED",
        )
    validate_image_identity(
        bundle["official_load_python_identity"], profile["load_python_config_id"]
    )
    return profile


def check_plan(plan, now, *, require_fixture_ready=True):
    no_secrets(plan)
    need(plan.get("schema") == "t44-neutral-r30-plan-v1", "PLAN_SCHEMA_REQUIRED")
    need(plan.get("synthetic") is True, "SYNTHETIC_DECLARATION_REQUIRED")
    need(plan.get("root_admit_preparation") is True, "ROOT_PREPARATION_ADMISSION_REQUIRED")
    profile = load_source_profile(plan)
    binding = load_gen_binding(plan)
    match = re.fullmatch(r"t44-cloud-(r30[a-z0-9]{5,12})-([pf])", binding["project"])
    need(match is not None, "ACTUAL_GEN_PROJECT_FORMAT_REQUIRED")
    run, phase = match.groups()
    need(run != "r30window01", "RETIRED_WINDOW_NAMESPACE_REFUSED")
    need(
        binding["database"] == f"t44c_{run}_{phase}" and binding["phase"] == phase,
        "ACTUAL_GEN_PROJECT_DATABASE_PAIR_REQUIRED",
    )
    need(
        plan["run_id"] == run and plan["namespace"] == binding["project"],
        "PLAN_MUST_USE_ACTUAL_GEN_RUN_AND_PROJECT",
    )
    namespace = binding["project"]
    need(plan["source"]["git_commit"] == profile["source_sha"], "EXACT_FINAL_SOURCE_REQUIRED")
    need(plan["source"]["openapi_sha256"] == OPENAPI, "FROZEN_OPENAPI_REQUIRED")
    for key in ("manifest_sha256", "files_proof_sha256", "artifact_sha256"):
        digest(plan["source"][key])
    need(
        plan["source"]["manifest_sha256"] == profile["source_manifest_sha256"]
        and plan["source"]["bundle_manifest_sha256"] == profile["backend_bundle_manifest_sha256"],
        "EXACT_DEPLOYMENT_MANIFESTS_REQUIRED",
    )
    need(
        plan["source"]["context_records"] == profile["context_file_count"]
        and plan["source"]["expected_runtime_files"] == profile["runtime_file_count"],
        "ACTUAL_CONTEXT_AND_RUNTIME_SETS_ARE_DISTINCT",
    )
    digest(plan["source"]["actual_loaded_receipt_sha256"])
    need(
        isinstance(plan["source"]["actual_loaded_receipt_path"], str)
        and Path(plan["source"]["actual_loaded_receipt_path"]).is_absolute(),
        "ORIGINAL_ACTUAL_IMPORT_PATH_REQUIRED",
    )
    need(
        0 <= (now - timestamp(plan["source"]["actual_loaded_observed_at"])).total_seconds() <= 3600,
        "FRESH_ACTUAL_IMPORT_OBSERVATION_REQUIRED",
    )
    need(plan["budget"]["helper_sha256"] == BUDGET_HELPER, "R30_STRICT_KIND_BUDGET_HELPER_REQUIRED")
    need(
        plan["source"]["actual_loaded_full_chain_reviewed_by_root"] is True,
        "ROOT_ACTUAL_IMPORT_CHAIN_REVIEW_REQUIRED",
    )
    digest(plan["budget"]["actual_admission_receipt_sha256"])
    approval = plan["public_tool_approval"]
    need(approval["supports_source_git"] == SOURCE, "NEW_PUBLIC_TOOL_APPROVAL_REQUIRED")
    digest(approval["receipt_sha256"])
    digest(approval["adapter_sha256"])
    need(approval["adapter_sha256"] != OLD_ADAPTER, "OLD_F7_ADAPTER_REFUSED")
    need(
        approval["adapter_sha256"] == profile.get("qa_adapter_sha256") == NEW_ADAPTER
        and approval["receipt_sha256"] == profile.get("qa_approval_receipt_sha256"),
        "EXACT_SOURCE_MATCHED_NEW_PUBLIC_APPROVAL_REQUIRED",
    )
    need(approval["root_relayed_approval"] is True, "ROOT_RELAYED_TOOL_APPROVAL_REQUIRED")
    target = plan["target"]
    need(target["compose_project"] == namespace, "EXACT_COMPOSE_NAMESPACE_REQUIRED")
    need(
        re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{0,63}", target["database"] or ""),
        "EXACT_PROJECT_DATABASE_REQUIRED",
    )
    need(target["database"] == binding["database"], "EXACT_GEN_DATABASE_REQUIRED")
    need(
        target["mysql_host"] == "mysql"
        and type(target["mysql_port"]) is int
        and target["mysql_port"] == 3306
        and target["mysql_user"] == target["database"] + "_app",
        "EXACT_DATABASE_BINDING_REQUIRED",
    )
    digest(target["binding_sha256"])
    need(
        target["binding_sha256"] == plan["gen_binding"]["sha256"],
        "SAME_ORIGINAL_BINDING_SHA_REQUIRED",
    )
    digest(target["ca_sha256"])
    origin = urlsplit(target["origin"] or "")
    need(
        origin.scheme == "https"
        and origin.hostname
        and not origin.username
        and not origin.password
        and origin.path in ("", "/")
        and not origin.query
        and not origin.fragment,
        "EXACT_TLS_ORIGIN_REQUIRED",
    )
    try:
        address = ipaddress.IPv4Address(target["connect_ip"])
        host = ipaddress.IPv4Address(origin.hostname)
        port = origin.port or 443
        need(
            address == host
            and address.is_private
            and not address.is_loopback
            and not address.is_link_local
            and not address.is_unspecified
            and not address.is_multicast
            and 1 <= port <= 65535,
            "EXACT_PRIVATE_IPV4_TLS_TARGET_REQUIRED",
        )
        need(
            str(address) == binding["app_private_ip"] and port == binding["tls_port"],
            "EXACT_GEN_TLS_TARGET_REQUIRED",
        )
    except (ValueError, TypeError):
        raise Refused("EXACT_PRIVATE_IPV4_TLS_TARGET_REQUIRED") from None
    for key in ("backend", "load_python"):
        digest(plan["images"][key], image=True)
    need(
        plan["images"]["backend"] == profile["backend_config_id"]
        and plan["images"]["load_python"] == profile["load_python_config_id"],
        "EXACT_BACKEND_AND_LOAD_CONFIG_IDENTITIES_REQUIRED",
    )
    roles = plan["runtime_roles"]
    need(set(roles) == APP_ROLES | {"load"}, "SEVEN_APP_ROLES_LOAD_SEPARATE_REQUIRED")
    for role in roles:
        if role == "scheduler" and not require_fixture_ready:
            need(roles[role]["required"] is True, "SCHEDULER_MUST_REMAIN_REQUIRED")
            continue
        need(
            roles[role]["required"] is True and roles[role]["running_observed"] is True,
            "REQUIRED_BACKGROUND_ROLE_NOT_OBSERVED",
        )
        digest(roles[role]["receipt_sha256"])
    window = plan["window"]
    start, end, stop = (timestamp(window[key]) for key in ("start_utc", "end_utc", "stop_utc"))
    lifecycle = plan["lifecycle"]
    t0, cost, cutoff = (
        timestamp(lifecycle[key]) for key in ("t0_utc", "cost_stop_utc", "packet_cutoff_utc")
    )
    need(
        window["stop_utc"] == binding["stop_utc"]
        and stop == t0 + timedelta(minutes=35)
        and cost == t0 + timedelta(minutes=40),
        "ACTUAL_GEN_G35_AND_COST_C40_REQUIRED",
    )
    need(
        cutoff == start - timedelta(seconds=150) and now <= cutoff,
        "PACKET_CUTOFF_RESERVES_TRANSFER_PREPARE120_AUTH30",
    )
    need(
        now < start < end <= stop
        and 780 <= (end - start).total_seconds() <= 900
        and (cost - end).total_seconds() >= 90,
        "FRESH_COMPLETE_WINDOW_REQUIRED",
    )
    need(timestamp(plan["seed"]["anchor_utc"]) <= now, "ACTUAL_SEED_ANCHOR_REQUIRED")
    need(
        type(plan["seed"]["seed"]) is int and plan["seed"]["fresh_empty_database_required"] is True,
        "EXPLICIT_FRESH_SYNTHETIC_SEED_REQUIRED",
    )
    need(plan["fixture_baseline_counts"] == BASE_COUNTS, "DECLARED_BASELINE_COUNTS_REQUIRED")
    need(
        set(plan["authorized_count_delta"]) == set(BASE_COUNTS)
        and all(type(v) is int and v >= 0 for v in plan["authorized_count_delta"].values()),
        "EXPLICIT_PREPARATION_DELTA_REQUIRED",
    )
    need(set(plan["allowed_writes"]) <= OPERATIONS, "UNSUPPORTED_PREPARATION_WRITE")
    ids = plan["authorized_project_ids"]
    need(
        isinstance(ids, list)
        and len(ids) == len(set(ids))
        and all(type(pid) is int and pid > 0 for pid in ids),
        "EXPLICIT_PROJECT_WRITE_SCOPE_REQUIRED",
    )
    need(plan["benchmark_grant_allow"] is False, "PREPARATION_IS_NOT_RUN_AUTHORIZATION")
    ready = []
    for key in ("source", "images", "transfer", "preflight"):
        receipt = plan["readiness"][key]
        digest(receipt["sha256"])
        ready.append(timestamp(receipt["completed_at"]))
    completed = timestamp(plan["readiness"]["all_ready_at"])
    need(max(ready) <= completed <= now, "READINESS_MUST_PRECEDE_FINAL_SESSIONS")
    if require_fixture_ready:
        fixture_ready = timestamp(plan["readiness"]["fixture_ready_at"])
        need(completed <= fixture_ready <= now, "ACTUAL_FIXTURE_READY_BEFORE_PACKET_REQUIRED")
    need(
        plan["readiness"]["admin_preserves_image_pythonpath"] is True,
        "ADMIN_MINUS_I_PYTHONPATH_HAZARD_REFUSED",
    )
    return start, end, completed


def check_intent(plan, intent, now):
    check_plan(plan, now, require_fixture_ready=intent.get("purpose") == "final_packet")
    no_secrets(intent)
    need(
        intent["run_id"] == plan["run_id"] and intent["namespace"] == plan["namespace"],
        "CROSS_RUN_INTENT_REFUSED",
    )
    need(
        intent["database"] == plan["target"]["database"]
        and intent["binding_sha256"] == plan["target"]["binding_sha256"],
        "CROSS_DATABASE_INTENT_REFUSED",
    )
    need(intent["operation"] in plan["allowed_writes"], "WRITE_NOT_AUTHORIZED")
    need(
        set(intent["project_ids"]) <= set(plan["authorized_project_ids"]),
        "CROSS_PROJECT_WRITE_REFUSED",
    )
    need(
        intent["operation"] != "seed_demo" or intent["empty_scope_observed"] is True,
        "SEED_REQUIRES_ACTUAL_EMPTY_SCOPE",
    )
    return {"status": "METADATA_CONSISTENT_NOT_EXECUTED", "operation": intent["operation"]}


def check_evidence(plan, evidence, now):
    start, end, ready_at = check_plan(plan, now)
    no_secrets(evidence)
    need(
        evidence["run_id"] == plan["run_id"] and evidence["namespace"] == plan["namespace"],
        "CROSS_RUN_EVIDENCE_REFUSED",
    )
    need(
        evidence["database"] == plan["target"]["database"]
        and evidence["binding_sha256"] == plan["target"]["binding_sha256"],
        "CROSS_DATABASE_EVIDENCE_REFUSED",
    )
    actual = evidence["actual_fixture_counts"]
    need(
        actual
        == {key: value + plan["authorized_count_delta"][key] for key, value in BASE_COUNTS.items()},
        "ACTUAL_COUNTS_DIFFER_FROM_EXPLICIT_BASELINE_PLUS_DELTA",
    )
    digest(evidence["actual_fixture_sha256"])
    issued = evidence["session_attestations"]
    need(set(issued) == IDENTITIES, "FOUR_ACTUAL_SESSION_ATTESTATIONS_REQUIRED")
    for role, item in issued.items():
        digest(item["token_sha256"])
        if role == "service":
            earliest = latest = timestamp(item["issued_at"])
        else:
            earliest = timestamp(item["login_request_started_at"])
            latest = timestamp(item["response_observed_at"])
            timestamp(item["response_meta"]["server_time"])
        need(
            ready_at <= earliest <= latest <= now < start
            and timestamp(item["expires_at"])
            > end + timedelta(seconds=plan["session_expiry_reserve_seconds"]),
            "LATE_FRESH_FULL_WINDOW_SESSION_REQUIRED",
        )
        need(
            type(item["user_id"]) is int
            and item["user_id"] > 0
            and len(item["project_ids"]) == len(set(item["project_ids"])),
            "ACTUAL_IDENTITY_SCOPE_REQUIRED",
        )
    need(
        len({issued[role]["user_id"] for role in ("manager", "developer", "reviewer")}) == 3,
        "THREE_DISTINCT_HUMAN_ROLE_ACCOUNTS_REQUIRED",
    )
    need(
        len({item["token_sha256"] for item in issued.values()}) == 4,
        "FOUR_DISTINCT_SESSION_DIGESTS_REQUIRED",
    )
    need(issued["service"]["scopes"] == ["escalation:write"], "EXACT_SERVICE_SCOPE_REQUIRED")
    inventory = evidence["inventory"]
    need(
        inventory["schema"] == "772-inventory-v1" and len(inventory["clients"]) == 400,
        "ACTUAL_400_CLIENT_INVENTORY_REQUIRED",
    )
    need(
        0 <= (now - timestamp(inventory["captured_at"])).total_seconds() <= 300,
        "FRESH_INVENTORY_REQUIRED",
    )
    need(ready_at <= timestamp(inventory["captured_at"]) <= now, "CURRENT_SNAPSHOT_TIME_REQUIRED")
    clients = inventory["clients"]
    need({c["client_id"] for c in clients} == set(range(400)), "CLIENT_IDS_REQUIRED")
    task_ids = [c[key]["id"] for c in clients for key in ("transition_task", "escalation_task")]
    need(len(set(task_ids)) == 800, "DISTINCT_800_CURRENT_TASKS_REQUIRED")
    event_ids = [c["escalation_event"]["id"] for c in clients]
    need(len(set(event_ids)) == 400, "DISTINCT_400_EXISTING_EVENTS_REQUIRED")
    projects = {c["project_id"] for c in clients}
    need(
        len(projects) >= 35 and projects <= set(plan["authorized_project_ids"]),
        "ACTUAL_AUTHORIZED_PROJECT_SPREAD_REQUIRED",
    )
    exclusive = evidence["exclusive_scope"]
    need(
        set(exclusive["task_ids"]) == set(task_ids)
        and set(exclusive["event_ids"]) == set(event_ids)
        and exclusive["other_workload_writer_absent"] is True,
        "ACTUAL_EXCLUSIVE_OBJECT_SCOPE_REQUIRED",
    )
    digest(exclusive["writer_evidence_sha256"])
    need(
        exclusive["scheduler_running"] is True
        and exclusive["consumer_running"] is True
        and exclusive["all_notifications_precreated"] is False,
        "BACKGROUND_BEHAVIOR_MUST_REMAIN_REAL",
    )
    from t44.contracts import violations
    from t44.scheduling.rules import load_rules, select_window

    rules = load_rules()
    need(inventory["rule_version"] == rules.version, "ACTUAL_FROZEN_RULE_VERSION_REQUIRED")
    managers = {}
    for pid in projects:
        members = evidence["memberships"][str(pid)]
        need(
            all(
                not violations({"$ref": "#/components/schemas/Member"}, member)
                and member["project_id"] == pid
                for member in members
            ),
            "CURRENT_MEMBERSHIP_SNAPSHOTS_REQUIRED",
        )
        for role, code in (("manager", 1), ("developer", 2), ("reviewer", 3)):
            need(
                any(
                    member["user"]["id"] == issued[role]["user_id"]
                    and member["active"]
                    and code in member["roles"]
                    for member in members
                ),
                "ACTUAL_ROLE_MEMBERSHIP_REQUIRED",
            )
        managers[pid] = {
            member["user"]["id"] for member in members if member["active"] and 1 in member["roles"]
        }
    for client in clients:
        pid = client["project_id"]
        for item in issued.values():
            need(pid in item["project_ids"], "ACTUAL_SESSION_PROJECT_SCOPE_REQUIRED")
        transition, escalation, event = (
            client[key] for key in ("transition_task", "escalation_task", "escalation_event")
        )
        for task in (transition, escalation):
            need(
                not violations({"$ref": "#/components/schemas/Task"}, task),
                "COMPLETE_CURRENT_TASK_SNAPSHOT_REQUIRED",
            )
            need(
                task["project_id"] == pid and timestamp(task["updated_at"]) <= now,
                "TASK_OWNERSHIP_OR_TIME_MISMATCH",
            )
            need(
                timestamp(task["plan"]["planned_start"]) < timestamp(task["plan"]["planned_end"]),
                "ACTUAL_TASK_TIME_RANGE_REQUIRED",
            )
        need(
            transition["state"] == 2 and transition["owner_id"] == issued["developer"]["user_id"],
            "DEVELOPING_TASK_ACTUAL_OWNER_REQUIRED",
        )
        facts = evidence["transition_dependency_facts"][str(transition["id"])]
        need(
            facts["project_id"] == pid
            and facts["task_id"] == transition["id"]
            and len(facts["predecessor_ids"]) == len(facts["predecessor_states"])
            and all(state == 6 for state in facts["predecessor_states"]),
            "ACTUAL_DELIVERED_DEPENDENCY_FACTS_REQUIRED",
        )
        iteration = evidence["iterations"][str(transition["iteration_id"])]
        need(
            not violations({"$ref": "#/components/schemas/Iteration"}, iteration)
            and iteration["project_id"] == pid
            and any(
                item["user_id"] == transition["owner_id"] for item in iteration["plan"]["capacity"]
            ),
            "ACTUAL_ITERATION_CAPACITY_FACTS_REQUIRED",
        )
        # This proves non-eligibility under the frozen scheduler rules, not a hidden QA case.
        need(
            select_window(start, transition["plan"]["planned_end"], rules) is None
            and select_window(end, transition["plan"]["planned_end"], rules) is None,
            "SCHEDULER_CAN_TOUCH_TRANSITION_SCOPE",
        )
        need(
            timestamp(transition["plan"]["planned_end"]) > end + timedelta(days=1),
            "PUBLISHED_V24_WHOLE_WINDOW_PLUS24H_REQUIRED",
        )
        need(
            not violations({"$ref": "#/components/schemas/EscalationEvent"}, event),
            "COMPLETE_EXISTING_EVENT_REQUIRED",
        )
        match = select_window(start, escalation["plan"]["planned_end"], rules)
        last = select_window(end, escalation["plan"]["planned_end"], rules)
        need(
            match
            and last
            and match.level == last.level == event["level"]
            and escalation["state"] in (1, 2, 3, 4, 5)
            and event["project_id"] == pid
            and event["task_id"] == escalation["id"]
            and event["schedule_version"] == escalation["schedule_version"]
            and event["rule_version"] == rules.version,
            "EXISTING_CURRENT_HIGHEST_EVENT_REQUIRED",
        )
        need(
            set(client["project_manager_ids"]) == managers[pid],
            "ALL_ACTUAL_ACTIVE_MANAGERS_REQUIRED",
        )
    return {
        "status": "LOCAL_METADATA_CONSISTENT_NOT_SUT_READY",
        "sessions": 4,
        "clients": 400,
        "distinct_tasks": 800,
        "projects": len(projects),
        "benchmark_authorized": False,
    }


def load_gen_binding(plan):
    profile = load_source_profile(plan)
    path = Path(plan["gen_binding"]["path"])
    need(
        not path.is_symlink() and path.is_file() and path.stat().st_size <= 16 * 1024 * 1024,
        "ORIGINAL_GEN_BINDING_REGULAR_FILE_REQUIRED",
    )
    raw = path.read_bytes()
    need(
        hashlib.sha256(raw).hexdigest() == plan["gen_binding"]["sha256"],
        "ORIGINAL_GEN_BINDING_SHA_MISMATCH",
    )
    binding = json.loads(raw)
    need(
        binding["kind"] == "isolated-cloud-campaign"
        and binding["generation_kind"] == profile["gen_kind"]
        and binding["source_sha"] == SOURCE
        and binding["source_manifest_sha256"] == profile["source_manifest_sha256"]
        and binding["upgrade_binding_sha256"] == profile["backend_bundle_manifest_sha256"],
        "EXACT_R30_GEN_BINDING_SOURCE_REQUIRED",
    )
    need(
        all(
            binding.get(key)
            for key in (
                "config_ids",
                "image_ids",
                "cryptographic_transport_proofs",
                "tls",
                "file_hashes",
            )
        ),
        "MINIMAL_SCHEMA_PROJECTION_IS_NOT_FULL_ACTUAL_BINDING",
    )
    return binding


def validate_loaded_receipt(plan, raw):
    profile = load_source_profile(plan)
    need(isinstance(raw, bytes), "ORIGINAL_ACTUAL_IMPORT_BYTES_REQUIRED_BEFORE_ACTION")
    need(
        hashlib.sha256(raw).hexdigest() == plan["source"]["actual_loaded_receipt_sha256"],
        "ACTUAL_IMPORT_RAW_HASH_MISMATCH",
    )
    proof = json.loads(raw)
    need(
        proof["kind"] == "final-backend-web-import-v1"
        and proof["source_sha"] == profile["source_sha"]
        and proof["source_manifest_sha256"] == profile["source_manifest_sha256"]
        and proof["bundle_manifest_sha256"] == profile["backend_bundle_manifest_sha256"]
        and type(proof["full_runtime_files"]) is int
        and proof["full_runtime_files"] == profile["runtime_file_count"]
        and proof["business_services_started"] is False
        and proof["volumes_modified"] is False
        and type(proof["images_loaded_this_observation"]) is bool
        and proof["observed_utc"] == plan["source"]["actual_loaded_observed_at"],
        "EXACT_ACTUAL_APP_IMPORT_RECEIPT_REQUIRED",
    )
    need(
        proof["identity"] == proof["identities"]["backend"], "SAME_BACKEND_IDENTITY_PROOF_REQUIRED"
    )
    for role in ("backend", "web"):
        validate_image_identity(proof["identities"][role], profile[role + "_config_id"])
    package = proof["package_resolution"]
    need(
        package["uid"] == 10001
        and package["package_origin"] == "/app/backend/t44/__init__.py"
        and package["business_env_absent"] is True
        and isinstance(package["python_version"], str)
        and package["python_version"]
        and isinstance(package["sys_executable"], str)
        and package["sys_executable"].startswith("/"),
        "ACTUAL_BACKEND_PACKAGE_UID_AND_ENV_REQUIRED",
    )
    need(
        runtime_map(package["files"]) == profile["runtime_files"],
        "ACTUAL_RUNTIME_FILE_SET_AND_SHA_REQUIRED",
    )
    source = read_json(
        PRODUCER_DIRECTORY / "source-manifest.json",
        expected_sha256=profile["source_manifest_sha256"],
    )
    expected_records = {row["path"]: row for row in source["backend_runtime_files"]}
    need(
        all(row == expected_records[row["path"]] for row in package["files"]),
        "ACTUAL_RUNTIME_BYTES_MODES_AND_SHA_REQUIRED",
    )
    return proof


def read_json(path, *, expected_sha256=None):
    path = Path(path)
    need(
        not path.is_symlink() and path.is_file() and path.stat().st_size <= 16 * 1024 * 1024,
        "BOUNDED_REGULAR_METADATA_FILE_REQUIRED",
    )

    def unique(pairs):
        result = {}
        for key, value in pairs:
            need(key not in result, "DUPLICATE_JSON_KEY")
            result[key] = value
        return result

    raw = path.read_bytes()
    need(
        expected_sha256 is None or hashlib.sha256(raw).hexdigest() == expected_sha256,
        "METADATA_RAW_SHA_MISMATCH",
    )
    return json.loads(raw, object_pairs_hook=unique)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("plan", "intent", "evidence"))
    parser.add_argument("plan")
    parser.add_argument("--metadata")
    args = parser.parse_args()
    try:
        plan, now = read_json(args.plan), datetime.now(UTC)
        if args.mode == "plan":
            check_plan(plan, now)
            result = {"status": "PLAN_CONSISTENT_NOT_AUTHORIZED", "sut_requests": 0}
        else:
            need(args.metadata is not None, "METADATA_PATH_REQUIRED")
            check = check_intent if args.mode == "intent" else check_evidence
            result = check(plan, read_json(args.metadata), now)
        print(json.dumps(result, sort_keys=True))
        return 0
    except (Refused, KeyError, TypeError, ValueError, OSError):
        # No raw input or secrets in error output; invalid templates fail before any action.
        print(json.dumps({"status": "UNREADY_REFUSED", "sut_requests": 0, "authorized": False}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
