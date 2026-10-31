"""Owned APP PL1 profile: plan by default, three explicit SET PERSIST operations only."""

import argparse
import hashlib
import json
import os
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

APP_UTC = timezone.utc  # noqa: UP017 -- APP Python3.10

PROJECT = "t44-cloud-r30finalp09-p"
DATABASE = "t44c_r30finalp09_p"
MYSQL_IMAGE = "sha256:b8d06da71f6a65cce2ea38fce20cc0ce67bc985a84bc191d0544c2e948722625"
TARGET = {
    "innodb_redo_log_capacity": 2147483648,
    "innodb_io_capacity": 1000,
    "innodb_io_capacity_max": 2000,
}
KEEP = [
    "innodb_flush_log_at_trx_commit",
    "sync_binlog",
    "innodb_doublewrite",
    "innodb_buffer_pool_size",
    "innodb_buffer_pool_instances",
    "innodb_page_size",
    "innodb_flush_sync",
]
DOCKER = ["docker", "--context", "default"]
BASELINE = {
    "innodb_redo_log_capacity": 104857600,
    "innodb_io_capacity": 10000,
    "innodb_io_capacity_max": 20000,
}
MARGIN = 2 * 1024**3


def need(value, code):
    if not value:
        raise ValueError(code)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def put(path, value):
    with path.open("x") as f:
        os.chmod(path, 0o600)
        json.dump(value, f, indent=2)
        f.write("\n")


def run(args, data=None):
    r = subprocess.run(args, input=data, capture_output=True, timeout=40, check=False)
    need(r.returncode == 0, "COMMAND_FAILED_PRIVATE_ERROR_WITHHELD")
    return r.stdout


def sql(container, statement):
    # Credentials remain inside original owned container environment; never printed or argv.
    return run(
        DOCKER
        + [
            "exec",
            "-i",
            container,
            "sh",
            "-c",
            'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" exec mysql --user=root --batch --skip-column-names --raw',
        ],
        statement.encode(),
    )


def snapshot(container):
    keys = list(TARGET) + KEEP
    fields = ",".join("'" + k + "',@@GLOBAL." + k for k in keys)
    names = ",".join("'" + k + "'" for k in TARGET)
    statement = (
        "SELECT JSON_OBJECT('version',@@version,'datadir',@@datadir,'persisted_globals_load',@@GLOBAL.persisted_globals_load,'schema_present',(SELECT COUNT(*) FROM information_schema.schemata WHERE schema_name='"
        + DATABASE
        + "'),'values',JSON_OBJECT("
        + fields
        + "),'persisted',COALESCE((SELECT JSON_OBJECTAGG(VARIABLE_NAME,VARIABLE_VALUE) FROM performance_schema.persisted_variables WHERE VARIABLE_NAME IN ("
        + names
        + ")),JSON_OBJECT()),'resize_status',(SELECT VARIABLE_VALUE FROM performance_schema.global_status WHERE VARIABLE_NAME='Innodb_redo_log_resize_status'),'resized',(SELECT VARIABLE_VALUE FROM performance_schema.global_status WHERE VARIABLE_NAME='Innodb_redo_log_capacity_resized'));"
    )
    value = json.loads(sql(container, statement))
    need(
        value["version"].startswith("8.4.")
        and value["datadir"] == "/var/lib/mysql/"
        and value["schema_present"] == 1
        and value["persisted_globals_load"] == 1,
        "OWNED_84_DATABASE_DATADIR_PERSISTENCE_REQUIRED",
    )
    need(
        value["values"]["innodb_flush_log_at_trx_commit"] == 1
        and value["values"]["sync_binlog"] == 1
        and value["values"]["innodb_doublewrite"] in ("ON", 1),
        "DURABILITY_REQUIRED",
    )
    return value


def owner(expected):
    need(
        expected.get("root_approved") is True, "CURRENT_ROOT_APPROVED_SNAPSHOT_REQUIRED"
    )
    rows = expected["containers"]
    need(
        len(rows) == 7
        and {r["role"] for r in rows}
        == {"mysql", "api", "consumer", "scheduler", "web", "tls-gateway", "rabbitmq"}
        and all(r["project"] == PROJECT for r in rows),
        "EXACT_SEVEN_REQUIRED",
    )
    row = next(r for r in rows if r["role"] == "mysql")
    need(
        row["project"] == PROJECT and row["image_id"] == MYSQL_IMAGE,
        "EXACT_NAMESPACE_AND_PINNED_MYSQL_IMAGE_REQUIRED",
    )
    actual = json.loads(run(DOCKER + ["inspect", row["id"]]))[0]
    need(
        actual["Id"] == row["id"]
        and actual["Image"] == row["image_id"]
        and actual["State"]["Running"]
        and actual["Config"]["Labels"]["com.docker.compose.project"] == PROJECT
        and actual["Config"]["Labels"]["com.docker.compose.service"] == "mysql",
        "OWNED_RUNNING_MYSQL_REQUIRED",
    )
    mounts = [m for m in actual["Mounts"] if m["Destination"] == "/var/lib/mysql"]
    need(
        len(mounts) == 1 and mounts[0]["Type"] == "volume" and mounts[0]["RW"],
        "ORIGINAL_RW_DATA_VOLUME_REQUIRED",
    )
    m = mounts[0]
    volume = json.loads(run(DOCKER + ["volume", "inspect", m["Name"]]))[0]
    need(
        volume["Mountpoint"] == m["Source"]
        and volume.get("Labels", {}).get("com.docker.compose.project") == PROJECT,
        "OWNED_VOLUME_REQUIRED",
    )
    fs = os.statvfs(m["Source"])
    return {
        "id": row["id"],
        "image_id": row["image_id"],
        "volume": m["Name"],
        "mount_source": m["Source"],
        "device": os.stat(m["Source"]).st_dev,
        "free_bytes": fs.f_bavail * fs.f_frsize,
    }


def set_statement(key, value):
    need(
        key in TARGET and type(value) is int and 1 <= value <= 2**63 - 1,
        "ONLY_PROFILE_INTEGERS_REQUIRED",
    )
    return "SET PERSIST " + key + "=" + str(value) + ";"


def admission(auth, plan_raw):
    need(
        auth.get("root_approved") is True
        and auth.get("exclusive_no_benchmark_migration_other_writer") is True
        and auth.get("action")
        == (
            "apply-pl1-candidate"
            if json.loads(plan_raw)["profile"] == TARGET
            else "restore-pl1-before-values"
        )
        and auth.get("resource_profile") == "APP64CPU128GiB-PL1-40GiB-3800IOPS"
        and auth.get("plan_sha256") == sha(plan_raw),
        "EXPLICIT_CURRENT_PLAN_APPROVAL_REQUIRED",
    )
    stamp = datetime.fromisoformat(auth["approved_at"].replace("Z", "+00:00"))  # noqa: FURB162 -- Python3.10
    need(
        stamp.tzinfo is not None
        and stamp.utcoffset().total_seconds() == 0
        and 0 <= (datetime.now(APP_UTC) - stamp).total_seconds() <= 300,
        "CURRENT_UTC_APPROVAL_REQUIRED",
    )


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("action", nargs="?", choices=["plan", "apply"], default="plan")
    p.add_argument("--expected-seven", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--plan", type=Path)
    p.add_argument("--approval", type=Path)
    p.add_argument("--restore-from", type=Path)
    a = p.parse_args()
    need(os.geteuid() == 0, "APP_ROOT_REQUIRED")
    need(
        a.output.is_absolute()
        and a.output.parent.resolve() == a.output.parent
        and not a.output.exists(),
        "NEW_CANONICAL_OUTPUT_REQUIRED",
    )
    desired = TARGET
    restore = None
    if a.restore_from is not None:
        need(a.action == "plan", "RESTORE_FROM_ONLY_FRESH_PLAN")
        restore = json.loads(a.restore_from.read_bytes())
        need(
            restore["profile"] == TARGET
            and restore["project"] == PROJECT
            and restore["database"] == DATABASE
            and restore["rollback_runtime_values"] == BASELINE,
            "EXACT_ORIGINAL_RESTORE_PLAN_REQUIRED",
        )
        desired = BASELINE
    if a.action == "apply":
        need(
            a.plan is not None and a.approval is not None, "PLAN_AND_APPROVAL_REQUIRED"
        )
        raw = a.plan.read_bytes()
        plan = json.loads(raw)
        admission(json.loads(a.approval.read_bytes()), raw)
        need(
            plan["profile"] in (TARGET, BASELINE)
            and plan["project"] == PROJECT
            and plan["database"] == DATABASE,
            "EXACT_CANDIDATE_PLAN_REQUIRED",
        )
    if a.action == "apply":
        desired = plan["profile"]
    expected_raw = a.expected_seven.read_bytes()
    current = owner(json.loads(expected_raw))
    before = snapshot(current["id"])
    reserve = (
        max(
            0,
            desired["innodb_redo_log_capacity"]
            - int(before["values"]["innodb_redo_log_capacity"]),
        )
        + MARGIN
    )
    need(
        current["free_bytes"] >= reserve,
        "ACTUAL_DATA_FILESYSTEM_EXTRA_REDO_AND_MARGIN_REQUIRED",
    )
    a.output.mkdir(mode=0o700)
    if a.action == "plan":
        need(
            {k: before["values"][k] for k in TARGET}
            == (TARGET if restore else BASELINE),
            "REVIEW_CHANGED_BASELINE_NO_AUTO_TUNING",
        )
        if restore:
            need(
                all(
                    current[k] == restore["owner"][k]
                    for k in ["id", "image_id", "volume", "mount_source", "device"]
                ),
                "RESTORE_ORIGINAL_OWNER_REQUIRED",
            )
        put(
            a.output / "plan.PUBLIC.json",
            {
                "project": PROJECT,
                "database": DATABASE,
                "profile": desired,
                "owner": current,
                "before": before,
                "expected_seven_sha256": sha(expected_raw),
                "required_free_bytes": reserve,
                "planned_at": datetime.now(APP_UTC).isoformat(),
                "applied": False,
                "rollback_runtime_values": {k: before["values"][k] for k in TARGET},
            },
        )
        return
    need(
        plan["expected_seven_sha256"] == sha(expected_raw)
        and all(
            current[k] == plan["owner"][k]
            for k in ["id", "image_id", "volume", "mount_source", "device"]
        )
        and before == plan["before"],
        "PLAN_FACTS_CHANGED_REPLAN_REQUIRED",
    )
    receipt = {
        "status": "PARTIAL_OR_UNKNOWN",
        "before": before,
        "owner": current,
        "steps": [],
        "atomic": False,
        "automatic_rollback": False,
    }
    try:
        order = (
            ["innodb_io_capacity", "innodb_io_capacity_max"]
            if desired["innodb_io_capacity_max"]
            < before["values"]["innodb_io_capacity"]
            else ["innodb_io_capacity_max", "innodb_io_capacity"]
        )
        for key in order + ["innodb_redo_log_capacity"]:
            receipt["steps"].append(
                {"variable": key, "attempted": True, "completed": False}
            )
            put(
                a.output / (str(len(receipt["steps"])) + "-attempt.PUBLIC.json"),
                receipt["steps"][-1],
            )
            sql(current["id"], set_statement(key, desired[key]))
            receipt["steps"][-1]["completed"] = True
        end = time.monotonic() + 120
        while True:
            after = snapshot(current["id"])
            receipt["after"] = after
            need(
                all(after["values"][k] == before["values"][k] for k in KEEP),
                "PRESERVED_SETTINGS_CHANGED",
            )
            need(
                all(
                    after["values"][k] == desired[k]
                    and int(after["persisted"].get(k, -1)) == desired[k]
                    for k in TARGET
                ),
                "DYNAMIC_OR_PERSISTED_VALUE_MISMATCH",
            )
            if (
                after["resize_status"] == "OK"
                and int(after["resized"]) == desired["innodb_redo_log_capacity"]
            ):
                need(time.monotonic() < end, "LATE_RESIZE_OBSERVATION_NOT_ACCEPTED")
                receipt["status"] = (
                    "APPLIED_AND_PERSISTED_RESIZED_NOT_PERFORMANCE_ACCEPTANCE"
                )
                break
            need(time.monotonic() < end, "RESIZE_PENDING_NO_AUTOMATIC_RETRY")
            time.sleep(1)
    except Exception as error:
        receipt["error_class"] = type(error).__name__
        raise
    finally:
        put(a.output / "receipt.PUBLIC.json", receipt)


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001 -- never export credential-bearing subprocess errors
        raise SystemExit(
            "PROFILE_REFUSED_OR_PARTIAL: inspect own receipt; private errors withheld"
        ) from None
