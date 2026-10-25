"""Explicit finite SQLite developer sample. Never loads DSNs or existing databases."""

import argparse
import hashlib
import importlib.util
import json
import os
import platform
import subprocess
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-sqlite-demo", action="store_true")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if not args.run_sqlite_demo:
        parser.error("Explicit --run-sqlite-demo required; no external database input")
    root = Path(__file__).resolve().parents[2]
    module_path = Path(__file__).with_name("833_database_trace.py")
    tool_hashes = {}
    for path in (Path(__file__), module_path):
        relative = str(path.relative_to(root))
        data = path.read_bytes()
        original = subprocess.check_output(["git", "show", f"HEAD:{relative}"], cwd=root)
        if data != original:
            raise ValueError("Commit exact diagnostic source before running")
        tool_hashes[relative] = hashlib.sha256(data).hexdigest()
    production = {}
    for relative in subprocess.check_output(
        ["git", "ls-files", "backend/t44"], cwd=root, text=True
    ).splitlines():
        data = (root / relative).read_bytes()
        original = subprocess.check_output(["git", "show", f"HEAD:{relative}"], cwd=root)
        if data != original:
            raise ValueError("Production source differs from recorded commit")
        production[relative] = hashlib.sha256(data).hexdigest()
    if not hasattr(os, "O_NOFOLLOW"):
        parser.error("Output reservation requires no-follow support")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    except OSError:
        parser.error("Output exists or cannot be reserved; existing evidence retained")

    payload = {
        "source": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=root, text=True
        ).strip(),
        "tool_hashes": tool_hashes,
        "production_hashes": production,
        "operator": "database AI; not student manual execution",
        "scope": "finite synthetic SQLite Rows samples; not MySQL/HTTP/lock/cloud/performance acceptance",
        "python": sys.version,
        "platform": platform.platform(),
        "started_utc": datetime.now(UTC).isoformat(),
    }
    with os.fdopen(fd, "w", encoding="utf8") as output:
        try:
            payload.update(run_samples(module_path, args.output.parent))
            payload["status"] = "completed"
        except BaseException as error:
            payload["status"] = "failed; original exception retained"
            payload["error_class"] = type(error).__name__
            raise
        finally:
            payload["ended_utc"] = datetime.now(UTC).isoformat()
            output.write(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def run_samples(module_path, directory):
    import sqlalchemy
    import t44.persistence.rows as rows_module
    from sqlalchemy import Column, DateTime, Integer, MetaData, String, Table, create_engine
    from t44.persistence.uow import SqlAlchemyUnitOfWorkFactory

    spec = importlib.util.spec_from_file_location("database_trace_demo", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    signatures = []
    original_registry = rows_module.TABLES
    with tempfile.TemporaryDirectory(prefix="t44-sqlite-diagnostic-", dir=directory) as temporary:
        engine = create_engine(
            f"sqlite:///{Path(temporary) / 'synthetic.sqlite'}",
            pool_size=2,
            max_overflow=0,
            pool_pre_ping=True,
        )
        table = Table(
            "diagnostic_rows",
            MetaData(),
            Column("id", Integer, primary_key=True),
            Column("project_id", Integer, nullable=False),
            Column("note", String(200)),
            Column("at", DateTime),
        )
        rows_module.TABLES = {table.name: table}
        observer = module.DatabaseTrace().install(engine)
        try:
            table.metadata.create_all(engine)
            with engine.begin() as connection:
                connection.execute(
                    table.insert(),
                    [
                        {
                            "id": index,
                            "project_id": 1 if index <= 200 else 2,
                            "note": "synthetic",
                            "at": datetime(2026, 10, 25, tzinfo=UTC),
                        }
                        for index in range(1, 211)
                    ],
                )
            factory = SqlAlchemyUnitOfWorkFactory(engine)
            for cycle in ("A", "B"):
                for size in (1, 20, 100):
                    with (
                        observer.request(f"sqliteRowsPage{size}_{cycle}"),
                        factory() as uow,
                    ):
                        result = uow.gateway.rows(
                            table.name, {"project_id": 1}, order_by=("id",), limit=size
                        )
                        total = uow.gateway.count(table.name, {"project_id": 1})
                        assert len(result) == size and total == 200
                        assert [row["id"] for row in result] == list(range(1, size + 1))
                        assert all(row["at"].tzinfo == UTC for row in result)
                        signatures.append(
                            {
                                "label": f"sqliteRowsPage{size}_{cycle}",
                                "materialized_rows": len(result),
                                "total": total,
                                "ids_sha256": hashlib.sha256(
                                    json.dumps([row["id"] for row in result]).encode()
                                ).hexdigest(),
                            }
                        )
            before_dispose = observer.snapshot()
            assert engine.pool.checkedout() == 0
            engine.dispose()
            after_dispose = observer.snapshot()
            return {
                "sqlalchemy": sqlalchemy.__version__,
                "synthetic_fixture": {
                    "rows": 210,
                    "projects": 2,
                    "constraints": "own toy columns with id PK; not production DDL or business fixture",
                },
                "signatures": signatures,
                "trace_before_dispose": before_dispose,
                "trace_after_dispose": after_dispose,
                "engine_disposed": True,
                "six_requests_retained_no_warmup_discard": True,
            }
        finally:
            engine.dispose()
            observer.close()
            rows_module.TABLES = original_registry


if __name__ == "__main__":
    main()
