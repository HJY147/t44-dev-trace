"""Own new socket-only MySQL; real catalog regressions, never an existing URL/server."""

import argparse
import hashlib
import json
import os
import re
import signal
import subprocess
import time
from pathlib import Path

import pymysql
from cases import cases
from sqlalchemy import URL, create_engine
from sqlalchemy.exc import SQLAlchemyError
from t44.persistence.migrations import MigrationError, check_schema, migrate
from t44.persistence.schema import DDL_SHA256, ddl_text

PROJECT = Path("/Users/yang/Desktop/nothing/软件开发大作业")
BASEDIR = PROJECT / ".agent-worktrees/.runtime/mysql-8.4/mysql-8.4.11-macos15-arm64"
BINARY = BASEDIR / "bin/mysqld"


def run(stage, receipt):
    resource = PROJECT / "tmp/794" / stage
    resource.mkdir(parents=True, mode=0o700, exist_ok=False)
    data, sock, pidfile = resource / "data", resource / "s", resource / "pid"
    if len(os.fsencode(sock)) >= 100:
        raise ValueError("Own socket path too long")
    version = subprocess.check_output(
        [str(BINARY), "--no-defaults", "--version"], text=True
    )
    if "8.4.11" not in version:
        raise ValueError("Only approved official MySQL8.4.11")
    receipt.update(
        binary_version=version.strip(),
        binary_sha256=hashlib.sha256(BINARY.read_bytes()).hexdigest(),
    )
    process = connection = None
    started = time.monotonic()

    def deadline(*_):
        raise TimeoutError("Own570s deadline, reserve30s cleanup")

    previous = signal.signal(signal.SIGALRM, deadline)
    signal.setitimer(signal.ITIMER_REAL, 570)

    def owned():
        command = subprocess.check_output(
            ["ps", "-p", str(process.pid), "-o", "command="], text=True
        )
        if process.pid == 7980 or f"--datadir={data}" not in command:
            raise RuntimeError("Refuse to stop unowned process")
        if pidfile.exists() and int(pidfile.read_text().strip()) != process.pid:
            raise RuntimeError("Own PID file mismatch")
        return command.strip()

    try:
        subprocess.run(
            [
                str(BINARY),
                "--no-defaults",
                "--initialize-insecure",
                f"--basedir={BASEDIR}",
                f"--datadir={data}",
                "--innodb-buffer-pool-size=128M",
                f"--log-error={resource / 'initialize.log'}",
            ],
            check=True,
            timeout=90,
            capture_output=True,
        )
        args = [
            str(BINARY),
            "--no-defaults",
            f"--basedir={BASEDIR}",
            f"--datadir={data}",
            "--skip-networking",
            "--mysqlx=OFF",
            "--innodb-buffer-pool-size=128M",
            f"--socket={sock}",
            f"--pid-file={pidfile}",
            f"--log-error={resource / 'server.log'}",
        ]
        process = subprocess.Popen(
            args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        receipt["process"] = {"pid": process.pid, "args": args}
        for _ in range(150):
            if process.poll() is not None:
                raise RuntimeError("Own server exited during startup")
            try:
                connection = pymysql.connect(
                    user="root",
                    unix_socket=str(sock),
                    charset="utf8mb4",
                    autocommit=True,
                    connect_timeout=2,
                    read_timeout=15,
                    write_timeout=15,
                )
                break
            except pymysql.err.OperationalError:
                time.sleep(0.1)
        if connection is None:
            raise TimeoutError("Own socket startup")
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT @@datadir,@@pid_file,@@version,@@sql_mode,@@character_set_client,@@collation_server"
            )
            context = cursor.fetchone()
            if (
                Path(context[0]).resolve() != data.resolve()
                or Path(context[1]) != pidfile
            ):
                raise RuntimeError("Connected server identity mismatch")
            receipt["server_context"] = context
            receipt["owned_command"] = owned()
            reference = "t44_794_reference"
            cursor.execute(
                f"CREATE DATABASE `{reference}` CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci"
            )
            cursor.execute(f"USE `{reference}`")
            for sql in re.sub(r"--[^\n]*", "", ddl_text()).split(";"):
                if sql.strip():
                    cursor.execute(sql)
            cursor.execute(
                "SELECT TABLE_NAME,COLUMN_NAME,EXTRA,CHARACTER_SET_NAME,COLLATION_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA=DATABASE() ORDER BY TABLE_NAME,ORDINAL_POSITION"
            )
            receipt["baseline_columns"] = cursor.fetchall()
            receipt["cases"] = []
            for index, (name, expected_pass, _) in enumerate(
                cases(reference, "unused")
            ):
                schema = f"t44_794_{index:02d}"
                statements = cases(reference, schema)[index][2]
                # Each empty schema remains on disk, including failed mutation setup.
                cursor.execute(
                    f"CREATE DATABASE `{schema}` CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci"
                )
                engine = create_engine(
                    URL.create(
                        "mysql+pymysql",
                        username="root",
                        database=schema,
                        query={"unix_socket": str(sock), "charset": "utf8mb4"},
                    )
                )
                entry = {
                    "name": name,
                    "schema": schema,
                    "expected_pass": expected_pass,
                    "statements": statements,
                }
                receipt["cases"].append(entry)
                try:
                    entry["migration_before"] = migrate(
                        engine, expected_database=schema
                    )
                    cursor.execute(f"USE `{schema}`")
                    for sql in statements:
                        cursor.execute(sql)
                    entry["check"] = check_schema(engine)
                    try:
                        repeated = migrate(engine, expected_database=schema)
                        entry["repeat"] = {"accepted": True, "report": repeated}
                    except MigrationError as error:
                        entry["repeat"] = {"accepted": False, "error": str(error)}
                    entry["matches_requirement"] = (
                        entry["check"]["passed"] == expected_pass
                        and entry["repeat"]["accepted"] == expected_pass
                    )
                except pymysql.MySQLError as error:
                    entry["setup_error"] = {
                        "driver_code": error.args[0],
                        "kind": type(error).__name__,
                    }
                    entry["matches_requirement"] = False
                finally:
                    engine.dispose()
        receipt["requirement_passed"] = all(
            case["matches_requirement"] for case in receipt["cases"]
        )
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        if process is not None and process.poll() is None:
            receipt["owned_command_before_stop"] = owned()
            try:
                if connection is not None:
                    with connection.cursor() as cursor:
                        cursor.execute("SHUTDOWN")
                else:
                    process.terminate()
                process.wait(timeout=15)
            except (pymysql.MySQLError, subprocess.TimeoutExpired):
                if process.poll() is None:
                    owned()
                    process.terminate()
                    try:
                        process.wait(timeout=8)
                    except subprocess.TimeoutExpired:
                        owned()
                        process.kill()
                        process.wait(timeout=3)
        if connection is not None:
            connection.close()
        signal.signal(signal.SIGALRM, previous)
        receipt["own_server_stopped"] = process is None or process.poll() is not None
        receipt["own_server_exit"] = None if process is None else process.returncode
        receipt["wall_seconds_including_cleanup"] = time.monotonic() - started
        receipt["datadir_retained"] = str(data)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--stage", choices=["before", "after", "after-proof"], required=True
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    fd = os.open(
        args.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600
    )
    receipt = {
        "stage": args.stage,
        "ddl_sha256": DDL_SHA256,
        "old_13306_accesses": 0,
        "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "cases_sha256": hashlib.sha256(
            Path(__file__).with_name("cases.py").read_bytes()
        ).hexdigest(),
    }
    with os.fdopen(fd, "w") as stream:
        try:
            source_root = Path(__file__).resolve().parents[2]
            receipt["source_commit"] = subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=source_root, text=True
            ).strip()
            bindings = {}
            for relative in (
                "backend/t44/persistence/migrations.py",
                "backend/requirements.lock",
                "tmp/794_database_catalog_audit/794_native.py",
                "tmp/794_database_catalog_audit/cases.py",
            ):
                value = (source_root / relative).read_bytes()
                if value != subprocess.check_output(
                    ["git", "show", "HEAD:" + relative], cwd=source_root
                ):
                    raise ValueError("Commit exact source and tool before native proof")
                bindings[relative] = hashlib.sha256(value).hexdigest()
            receipt["committed_source_bindings"] = bindings
            run(args.stage, receipt)
        except (
            OSError,
            RuntimeError,
            ValueError,
            subprocess.SubprocessError,
            SQLAlchemyError,
            pymysql.MySQLError,
        ) as error:
            receipt["error"] = {"kind": type(error).__name__, "detail": str(error)}
        finally:
            json.dump(receipt, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
    print(
        json.dumps(
            {
                key: receipt[key]
                for key in ("stage", "requirement_passed", "own_server_stopped")
                if key in receipt
            }
        )
    )
    return (
        0
        if receipt.get("requirement_passed") and receipt.get("own_server_stopped")
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(main())
