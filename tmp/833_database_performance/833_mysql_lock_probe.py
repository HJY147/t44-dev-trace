"""CI-only finite production Runtime.locked_scope probe; not HTTP/business acceptance."""

import argparse
import hashlib
import json
import os
import signal
import threading
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4


def stamp():
    return {"utc": datetime.now(UTC).isoformat(), "monotonic_ns": time.perf_counter_ns()}


def failure(error):
    original = getattr(error, "orig", None)
    args = getattr(original, "args", ())
    return {
        "exception_class": type(error).__name__,
        "mysql_code": args[0] if args and type(args[0]) is int else None,
        "rejection_code": getattr(error, "code", None),
    }


def seed(factory):
    from t44.services.common import now
    from t44.services.identity import HASHER, issue_session

    clock = now()
    with factory() as uow:
        g = uow.gateway
        user = g.insert(
            "users",
            {
                "username": "db833_" + uuid4().hex[:16],
                "display_name": "Synthetic lock probe",
                "password_hash": HASHER.hash("synthetic-lock-probe-password"),
                "created_at": clock,
                "updated_at": clock,
            },
        )
        token = issue_session(g, user_id=user, clock=clock, ttl=3600)["access_token"]
        project = g.insert(
            "projects",
            {
                "name": "Synthetic DB lock probe",
                "description": "",
                "created_by": user,
                "created_at": clock,
                "updated_at": clock,
            },
        )
        g.insert(
            "project_members",
            {
                "project_id": project,
                "user_id": user,
                "roles_mask": 3,
                "created_at": clock,
                "updated_at": clock,
            },
        )
        plan = {
            "planned_start": clock,
            "planned_end": clock + timedelta(days=2),
            "buffer_quarters": 4,
            "delay_contingency": "Synthetic probe",
            "created_at": clock,
            "updated_at": clock,
        }
        iteration = g.insert(
            "iterations",
            {
                **plan,
                "project_id": project,
                "name": "Synthetic probe",
                "capacity": [{"user_id": user, "available_hours": 100}],
            },
        )
        tasks = [
            g.insert(
                "tasks",
                {
                    **plan,
                    "project_id": project,
                    "iteration_id": iteration,
                    "owner_id": user,
                    "title": "Synthetic lock task",
                    "description": "",
                    "estimated_quarters": 4,
                    "state": 6 if i == 4 else 1,
                },
            )
            for i in range(7)
        ]
        # Both directions of numeric target/predecessor ordering; no cycle.
        for child, predecessor in ((0, 4), (1, 4), (6, 2)):
            g.insert(
                "task_dependencies",
                {
                    "project_id": project,
                    "task_id": tasks[child],
                    "depends_on_task_id": tasks[predecessor],
                    "created_by": user,
                    "created_at": clock,
                },
            )
    return token, project, tasks


def lock_snapshot(engine, connection_ids):
    from sqlalchemy import bindparam, text

    statement = text(
        "SELECT t.PROCESSLIST_ID AS connection_id, l.OBJECT_NAME AS object_name, "
        "l.INDEX_NAME AS index_name, l.LOCK_TYPE AS lock_type, "
        "l.LOCK_MODE AS lock_mode, l.LOCK_STATUS AS lock_status "
        "FROM performance_schema.data_locks l JOIN performance_schema.threads t "
        "ON t.THREAD_ID=l.THREAD_ID WHERE t.PROCESSLIST_ID IN :ids "
        "ORDER BY connection_id, object_name, index_name, lock_mode"
    ).bindparams(bindparam("ids", expanding=True))
    waits = text(
        "SELECT a.PROCESSLIST_ID AS requesting_connection, "
        "b.PROCESSLIST_ID AS blocking_connection, l.OBJECT_NAME AS object_name, "
        "l.INDEX_NAME AS index_name, l.LOCK_MODE AS requested_mode "
        "FROM performance_schema.data_lock_waits w "
        "JOIN performance_schema.threads a ON a.THREAD_ID=w.REQUESTING_THREAD_ID "
        "JOIN performance_schema.threads b ON b.THREAD_ID=w.BLOCKING_THREAD_ID "
        "JOIN performance_schema.data_locks l "
        "ON l.ENGINE_LOCK_ID=w.REQUESTING_ENGINE_LOCK_ID "
        "AND l.ENGINE=w.ENGINE WHERE a.PROCESSLIST_ID IN :ids"
    ).bindparams(bindparam("ids", expanding=True))
    with engine.connect() as connection:
        return {
            "locks": [
                dict(r) for r in connection.execute(statement, {"ids": connection_ids}).mappings()
            ],
            "waits": [
                dict(r) for r in connection.execute(waits, {"ids": connection_ids}).mappings()
            ],
        }


def pair(engine, factory, runtime, calls, *, name, expect_parallel=False, first=None, second=None):
    from sqlalchemy import text

    release = threading.Event()
    gates = [threading.Event(), threading.Event()]
    started = [threading.Event(), threading.Event()]
    report = {"name": name, "started": stamp(), "workers": [{}, {}]}

    def worker(index, action):
        row = report["workers"][index]
        try:
            with factory() as uow:
                session = uow._require_active()
                row["connection_id"] = session.execute(text("SELECT CONNECTION_ID()")).scalar_one()
                session.execute(text("SET SESSION innodb_lock_wait_timeout=5"))
                row["before_gate"] = stamp()
                started[index].set()
                runtime.locked_scope(uow.gateway, calls[index])
                row["gate_acquired"] = stamp()
                gates[index].set()
                # Keep both transactions open long enough for an actual lock inventory.
                if not release.wait(8):
                    raise TimeoutError("Controlled transaction release not received")
                if action:
                    row["action"] = action(uow.gateway, calls[index])
            row["committed"] = stamp()
        except BaseException as error:
            row["failure"] = failure(error)
        finally:
            row["ended"] = stamp()
            started[index].set()

    threads = [
        threading.Thread(target=worker, args=(i, action), daemon=True)
        for i, action in enumerate((first, second))
    ]
    try:
        threads[0].start()
        if not gates[0].wait(6):
            raise AssertionError("First transaction did not reach gate")
        threads[1].start()
        if not started[1].wait(6):
            raise AssertionError("Second transaction did not start")
        ids = [row["connection_id"] for row in report["workers"]]
        if len(set(ids)) != 2:
            raise AssertionError("Probe requires two physical connections")
        deadline = time.monotonic() + 3
        while time.monotonic() < deadline:
            snapshot = lock_snapshot(engine, ids)
            edge = any(
                w["requesting_connection"] == ids[1] and w["blocking_connection"] == ids[0]
                for w in snapshot["waits"]
            )
            if (expect_parallel and gates[1].is_set()) or (not expect_parallel and edge):
                report["observation"] = {**stamp(), **snapshot}
                break
            if "failure" in report["workers"][1]:
                raise AssertionError("Second transaction failed before observation")
            gates[1].wait(0.01)
        else:
            raise AssertionError("Required parallel gate or actual MySQL wait edge not observed")
        if not expect_parallel and gates[1].is_set():
            raise AssertionError("Blocked transaction unexpectedly passed gate")
        report["release"] = stamp()
    except BaseException as error:
        report["failure"] = failure(error)
    finally:
        release.set()
        for thread in threads:
            if thread.ident is not None:
                thread.join(8)
        report["threads_alive"] = [t.is_alive() for t in threads]
        report["ended"] = stamp()
    return report


def explain(engine, project, tasks):
    from sqlalchemy import select
    from t44.persistence.schema import TABLES

    table = TABLES["tasks"]
    statement = (
        select(table)
        .where(table.c.project_id == project, table.c.id.in_(sorted(tasks)))
        .order_by(table.c.id)
        .with_for_update()
    )
    compiled = statement.compile(
        dialect=engine.dialect, compile_kwargs={"render_postcompile": True}
    )
    with engine.connect() as connection:
        result = connection.exec_driver_sql("EXPLAIN " + str(compiled), compiled.params)
        rows = [dict(r) for r in result.mappings()]
    return {"shape_sha256": hashlib.sha256(str(compiled).encode()).hexdigest(), "plan": rows}


def run(args, report):
    from sqlalchemy import text
    from t44.persistence import SqlAlchemyUnitOfWorkFactory, create_mysql_engine
    from t44.services.codes import Action, State
    from t44.services.common import Call
    from t44.services.runtime import Runtime
    from t44.settings import Settings

    if os.environ.get("CI") != "true" or not args.allow_fresh_mysql_ci:
        raise ValueError("Fresh CI MySQL gate required")
    settings = Settings.from_env().mysql_settings()
    if settings.host not in {"localhost", "127.0.0.1"} or settings.port == 13306:
        raise ValueError("Only dedicated local fresh CI service allowed")
    if (
        settings.database != "t44_diagnostics"
        or os.environ.get("T44_DATABASE") != settings.database
    ):
        raise ValueError("Explicit diagnostic database required")
    runtime_file = Path(__file__).resolve().parents[2] / "backend/t44/services/runtime.py"
    if hashlib.sha256(runtime_file.read_bytes()).hexdigest() != args.expected_runtime_sha256:
        raise ValueError("Runtime source hash mismatch")
    engine = create_mysql_engine(settings)
    factory = SqlAlchemyUnitOfWorkFactory(engine)
    runtime = Runtime(factory, Settings(), None)
    try:
        with engine.connect() as connection:
            report["mysql"] = dict(
                connection.execute(
                    text(
                        "SELECT VERSION() AS version, @@transaction_isolation AS isolation, "
                        "@@innodb_deadlock_detect AS deadlock_detect, "
                        "@@innodb_autoinc_lock_mode AS autoinc_lock_mode"
                    )
                )
                .mappings()
                .one()
            )
        token, project, tasks = seed(factory)

        def call(task_index=None, operation="transitionTask", action=Action.START):
            c = Call(
                operation,
                str(uuid4()),
                token,
                path={
                    "project_id": project,
                    **({"task_id": tasks[task_index]} if task_index is not None else {}),
                },
                body={"action": action, "expected_version": 1},
                key=str(uuid4()),
            )
            runtime.prepare(c, lambda _: None)
            return c

        report["explain_target_pred"] = explain(engine, project, [tasks[0], tasks[4]])
        report["cases"] = []

        def record(*calls, **kwargs):
            case = pair(engine, factory, runtime, calls, **kwargs)
            report["cases"].append(case)
            if "failure" in case or any(case["threads_alive"]):
                raise AssertionError("Controlled lock probe failed; evidence retained")
            return case

        shared = args.expected_reader_lock == "share"
        record(call(3), call(5), name="disjoint_target_readers", expect_parallel=shared)
        record(
            call(0), call(6), name="disjoint_reverse_id_predecessor_sets", expect_parallel=shared
        )
        record(call(3), call(operation="createTask"), name="graph_writer_waits")
        record(call(0), call(1), name="shared_predecessor_still_serializes")

        def rollback_pred(g, c):
            row = c.task(g)
            changed = c.cas(g, "tasks", row, {"state": State.ROLLED_BACK})
            return {"state": changed["state"], "version": changed["version"]}

        def observe_pred(g, _c):
            return {"predecessor_state": g.get("tasks", tasks[4])["state"]}

        case = record(
            call(4, action=Action.ROLLBACK),
            call(0),
            name="predecessor_latest_after_wait",
            first=rollback_pred,
            second=observe_pred,
        )
        if case["workers"][1].get("action", {}).get("predecessor_state") != State.ROLLED_BACK:
            raise AssertionError("Waiting reader did not observe predecessor commit")

        def cas(g, c):
            row = c.task(g)
            return {"version": c.cas(g, "tasks", row, {"state": State.DEVELOPING})["version"]}

        case = record(call(3), call(3), name="same_target_same_version_cas", first=cas, second=cas)
        if case["workers"][0].get("action") != {"version": 2}:
            raise AssertionError("First CAS did not succeed")
        if case["workers"][1].get("failure", {}).get("rejection_code") != "VERSION_CONFLICT":
            raise AssertionError("Second CAS did not reject stale version")
        for case in report["cases"]:
            for index, row in enumerate(case["workers"]):
                expected = case["name"] == "same_target_same_version_cas" and index == 1
                if "failure" in row and not expected:
                    raise AssertionError("Unexpected worker failure")
        report["status"] = "passed finite Runtime/database development probes only"
    finally:
        report["checkedout_before_dispose"] = engine.pool.checkedout()
        engine.dispose()
        report["disposed"] = True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--allow-fresh-mysql-ci", action="store_true")
    parser.add_argument("--expected-reader-lock", required=True, choices=("share", "update"))
    parser.add_argument("--expected-runtime-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = {
        "schema": "runtime_mysql_lock_probe_v1",
        "started": stamp(),
        "expected_reader_lock": args.expected_reader_lock,
        "expected_runtime_sha256": args.expected_runtime_sha256,
        "formal_acceptance": False,
        "limits": [
            "Development DB lock/CAS probes, not HTTP/role/business-state acceptance",
            "Fixture task states are direct synthetic DB rows, not approved business history",
            "EXPLAIN and held locks are observations, not a proof of lock acquisition order",
            "No token, DSN, SQL text, binding values, lock_data or exception messages retained",
        ],
    }

    def stop(_signum, _frame):
        raise TimeoutError("Finite probe wall limit")

    signal.signal(signal.SIGALRM, stop)
    fd = os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as stream:
        try:
            signal.alarm(120)
            run(args, report)
        except BaseException as error:
            report["status"], report["failure"] = "failed retained", failure(error)
            raise
        finally:
            signal.alarm(0)
            report["ended"] = stamp()
            stream.write(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"status": report["status"], "cases": len(report["cases"])}))


if __name__ == "__main__":
    main()
