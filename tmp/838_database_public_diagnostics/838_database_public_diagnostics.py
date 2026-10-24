"""Explicit offline query recipes; no environment, credentials, network or HTTP input."""

import argparse
import ast
import hashlib
import json
import subprocess
from pathlib import Path

SOURCE = "0dfb55c2191200d947c5423fd9ee74bb0812cc5a"
FILES = (
    "api.py",
    "settings.py",
    "services/runtime.py",
    "services/identity.py",
    "services/tasks.py",
    "services/workflow.py",
    "services/common.py",
    "scheduling/facade.py",
    "messaging/facade.py",
    "persistence/rows.py",
    "persistence/engine.py",
    "persistence/uow.py",
    "domain/state_machine.py",
)


def provenance(root):
    receipts = {}
    for name in FILES:
        relative = "backend/t44/" + name
        data = (root / relative).read_bytes()
        original = subprocess.check_output(["git", "show", f"{SOURCE}:{relative}"], cwd=root)
        if data != original:
            raise ValueError(f"Source differs from fixed C: {relative}")
        tree = ast.parse(data)
        receipts[relative] = {
            "sha256": hashlib.sha256(data).hexdigest(),
            "functions": {
                f"{node.name}:{node.lineno}": node.end_lineno
                for node in ast.walk(tree)
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            },
        }
    return receipts


def recipes():
    # Imports happen only after the explicit CLI gate. All tables/data below are local toys.
    from sqlalchemy import Column, MetaData, Table, create_engine, delete, insert
    from sqlalchemy.dialects import mysql
    from sqlalchemy.orm import Session
    from t44.persistence.rows import RowsGateway
    from t44.persistence.schema import TABLES

    engine = create_engine("sqlite+pysqlite:///:memory:")
    metadata = MetaData()
    toys = {
        name: Table(
            name,
            metadata,
            *(
                Column(c.name, c.type, primary_key=c.name == "id", nullable=c.name != "id")
                for c in TABLES[name].columns
            ),
        )
        for name in ("tasks", "task_dependencies", "project_members")
    }
    output = {
        "scope": "Local synthetic column-only SQLite tables; not production DDL/constraints",
        "measurements": [],
        "executions": [],
        "no_mysql_connection": True,
        "not_http_trace_or_latency_or_lock_or_concurrent_cas_proof": True,
    }
    log = output["executions"]

    class Observed(RowsGateway):
        def _execute(self, statement, mode, parameters=None):
            entry = {
                "mysql_compiled_shape": str(statement.compile(dialect=mysql.dialect())),
                "mode": mode,
            }
            log.append(entry)
            result = super()._execute(statement, mode, parameters)
            entry["materialized_rows"] = len(result) if mode == "rows" else None
            return result

    def populate(dependencies, members):
        with engine.begin() as connection:
            for name in ("task_dependencies", "project_members", "tasks"):
                connection.execute(delete(toys[name]))
            connection.execute(
                insert(toys["tasks"]),
                [
                    {"id": i, "project_id": 1, "state": 1 if i == 1 else 6, "version": 1}
                    for i in range(1, 34)
                ]
                + [
                    {"id": 1001, "project_id": 2, "state": 2, "version": 1},
                    {"id": 1002, "project_id": 2, "state": 6, "version": 1},
                ],
            )
            connection.execute(
                insert(toys["project_members"]),
                [
                    {"id": i, "project_id": 1, "user_id": i, "active": 1, "roles_mask": 2}
                    for i in range(1, members + 1)
                ],
            )
            connection.execute(
                insert(toys["task_dependencies"]),
                [
                    {"id": i, "project_id": 1, "task_id": 1, "depends_on_task_id": i + 1}
                    for i in range(1, dependencies + 1)
                ]
                + [{"id": 999, "project_id": 2, "task_id": 1001, "depends_on_task_id": 1002}],
            )

    try:
        metadata.create_all(engine)
        with Session(engine) as session:
            g = Observed(lambda: session, lambda: None)

            def measure(label, operation):
                start = len(log)
                result = operation()
                entries = log[start:]
                output["measurements"].append(
                    {
                        "recipe": label,
                        "statement_count": len(entries),
                        "materialized_rows": sum(e["materialized_rows"] or 0 for e in entries),
                        "result_signature": result,
                        "execution_range": [start, len(log)],
                    }
                )
                session.rollback()
                return result, len(entries)

            def dependencies(skip_empty=False):
                edges = g.rows("task_dependencies", {"project_id": 1, "task_id": 1})
                ids = [row["depends_on_task_id"] for row in edges]
                predecessors = (
                    g.rows("tasks", {"project_id": 1, "id": ids}) if ids or not skip_empty else []
                )
                return [[r["id"], r["state"]] for r in predecessors]

            for degree in (0, 4, 32):
                populate(degree, 3)
                baseline, count = measure(
                    f"C_dependency_two_read_recipe_degree={degree}", dependencies
                )
                assert count == 2 and len(baseline) == degree
                candidate, count = measure(
                    f"UNAPPLIED_skip_empty_predecessors_degree={degree}",
                    lambda: dependencies(skip_empty=True),
                )
                assert candidate == baseline and count == (2 if degree else 1)
                _, count = measure(f"UNAPPLIED_guard_not_using_dependencies_degree={degree}", list)
                assert count == 0  # This is a recipe, not execution of a production action.

            for size in (3, 32):
                populate(32, size)
                result, count = measure(
                    f"C_project_members_share_recipe_members={size}",
                    lambda: [
                        r["user_id"]
                        for r in g.rows(
                            "project_members",
                            {"project_id": 1},
                            order_by=("user_id",),
                            lock="share",
                        )
                    ],
                )
                assert count == 1 and result == list(range(1, size + 1))

            def dependency_page(size, batch):
                edges = g.rows("task_dependencies", {"project_id": 1, "task_id": 1}, limit=size)
                by_id = (
                    {
                        r["id"]: r
                        for r in g.rows(
                            "tasks",
                            {"project_id": 1, "id": [e["depends_on_task_id"] for e in edges]},
                        )
                    }
                    if batch and edges
                    else {}
                )
                result = []
                for edge in edges:
                    predecessor = (
                        by_id.get(edge["depends_on_task_id"])
                        if batch
                        else g.get("tasks", edge["depends_on_task_id"])
                    )
                    result.append([edge["id"], predecessor["state"] == 6])
                return result

            for size in (1, 4, 32):
                original, count = measure(
                    f"C_dependency_page_recipe_size={size}",
                    lambda size=size: dependency_page(size, False),
                )
                assert count == 1 + size
                candidate, count = measure(
                    f"UNAPPLIED_batch_dependency_page_size={size}",
                    lambda size=size: dependency_page(size, True),
                )
                assert candidate == original and count == 2
            with engine.begin() as connection:
                connection.execute(delete(toys["tasks"]).where(toys["tasks"].c.id == 5))
            failures = []
            for batch in (False, True):
                try:
                    dependency_page(32, batch)
                except TypeError:
                    failures.append("TypeError: missing reference does not default to satisfied")
                finally:
                    session.rollback()
            assert len(failures) == 2
            output["missing_reference_failclosed"] = failures
            populate(32, 3)
            page, count = measure(
                "C_list_tasks_rows_and_count_recipe",
                lambda: {
                    "ids": [r["id"] for r in g.rows("tasks", {"project_id": 1}, limit=20)],
                    "total": g.count("tasks", {"project_id": 1}),
                },
            )
            assert count == 2 and len(page["ids"]) == 20 and page["total"] == 33
            _, count = measure(
                "C_task_update_lock_recipe",
                lambda: [
                    r["id"] for r in g.rows("tasks", {"project_id": 1, "id": [1, 2]}, lock="update")
                ],
            )
            assert count == 1
            start = len(log)
            assert g.update("tasks", {"id": 1, "version": 1}, {"version": 2}) == 1
            assert g.update("tasks", {"id": 1, "version": 1}, {"version": 2}) == 0
            session.rollback()
            output["sequential_version_predicate_recipe"] = {
                "rowcounts": [1, 0],
                "execution_range": [start, len(log)],
                "not_mysql_cas_or_lock_test": True,
            }
    finally:
        engine.dispose()
        output["local_engine_disposed"] = True
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not args.run:
        parser.error("Explicit --run required; offline SQLite only")
    if args.output.exists():
        parser.error("Output must not exist; retain previous results")
    root = Path(__file__).resolve().parents[2]
    tool_bytes = Path(__file__).read_bytes()
    committed_tool = subprocess.check_output(
        [
            "git",
            "show",
            "HEAD:tmp/838_database_public_diagnostics/838_database_public_diagnostics.py",
        ],
        cwd=root,
    )
    if tool_bytes != committed_tool:
        raise ValueError("Commit the exact tool before running; no dirty tool execution")
    receipt = {
        "fixed_source": SOURCE,
        "tool_git_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=root, text=True
        ).strip(),
        "tool_sha256": hashlib.sha256(tool_bytes).hexdigest(),
        "source_files": provenance(root),
    }
    try:
        receipt["local_query_recipes"] = recipes()
        receipt["status"] = "completed offline only; no production optimization applied"
    except Exception as error:
        receipt["status"] = "failed; original failure retained"
        receipt["error_class"] = type(error).__name__
        raise
    finally:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"status": receipt["status"], "output": str(args.output)}))


if __name__ == "__main__":
    main()
