"""Explicit owner-only MySQL calibration; never use a URL, environment or existing server."""

import argparse
import hashlib
import json
import os
import re
import signal
import subprocess
import time
from pathlib import Path

BASE = "f4bd382d4668130793fc553df9ce6363c4656ea6"
PROJECT = Path("/Users/yang/Desktop/nothing/软件开发大作业")
BASEDIR = PROJECT / ".agent-worktrees/.runtime/mysql-8.4/mysql-8.4.11-macos15-arm64"
BINARY = BASEDIR / "bin/mysqld"
RESOURCE = PROJECT / "tmp796"
REFERENCE, ACTUAL = "t44_796_reference", "t44_796_actual"
DDL_HASH = "c0e740b203a85117fb125c578ab61401275bbe46ea80c629869c6cff39424bc4"


def normalize_show(ddl):
    """Only MySQL's table-option counter; never a column or literal substring."""
    return re.sub(r"(?m)^(\) ENGINE=\w+) AUTO_INCREMENT=\d+(?= DEFAULT CHARSET=)", r"\1", ddl)


def cases(corrected_fk=False):
    index = (
        "ALTER TABLE tasks DROP INDEX ix_tasks_project_state, ADD {} ix_tasks_project_state ({}){}"
    )
    foreign = "ALTER TABLE projects DROP FOREIGN KEY fk_projects_creator, ADD CONSTRAINT fk_projects_creator FOREIGN KEY(created_by) REFERENCES {}(id){}"
    check = (
        "ALTER TABLE users DROP CHECK ck_users_active, ADD CONSTRAINT ck_users_active CHECK ({})"
    )
    values = [
        ("counter_growth", True, "ALTER TABLE users AUTO_INCREMENT=1234"),
        ("redundant_parentheses", True, check.format("((`active` IN (0,1)))")),
        (
            "utf8mb4_introducer",
            True,
            "ALTER TABLE users DROP CHECK ck_users_hash_shape, ADD CONSTRAINT ck_users_hash_shape CHECK ((LEFT(`password_hash`,10)=_utf8mb4'$argon2id$') AND (CHAR_LENGTH(`password_hash`)>30))",
        ),
        (
            "ascii_introducer",
            True,
            "ALTER TABLE users DROP CHECK ck_users_hash_shape, ADD CONSTRAINT ck_users_hash_shape CHECK ((left(`password_hash`,10)=_ascii'$argon2id$') AND (char_length(`password_hash`)>30))",
        ),
        (
            "foreign_noaction_restrict",
            True,
            foreign.format("users", " ON DELETE NO ACTION ON UPDATE RESTRICT"),
        ),
        ("foreign_qualified_self", True, foreign.format(f"`{ACTUAL}`.`users`", "")),
        (
            "index_asc_btree",
            True,
            index.format("KEY", "project_id ASC,state ASC,id ASC", " USING BTREE"),
        ),
        ("index_rebuild_same_definition", True, index.format("KEY", "project_id,state,id", "")),
        ("index_order", False, index.format("KEY", "state,project_id,id", "")),
        ("index_unique", False, index.format("UNIQUE KEY", "project_id,state,id", "")),
        ("index_desc", False, index.format("KEY", "project_id,state DESC,id", "")),
        (
            "unique_to_nonunique",
            False,
            "ALTER TABLE users DROP INDEX uq_users_username, ADD KEY uq_users_username(username)",
        ),
        (
            "unique_column_order",
            False,
            "ALTER TABLE task_dependencies ADD KEY probe_support(project_id,task_id), DROP INDEX uq_dependencies_edge, ADD UNIQUE KEY uq_dependencies_edge(project_id,depends_on_task_id,task_id)",
        ),
        ("foreign_target_table", False, foreign.format("service_accounts", "")),
        ("foreign_target_schema", False, foreign.format(f"`{REFERENCE}`.`users`", "")),
        (
            "foreign_source_order",
            False,
            "ALTER TABLE task_dependencies DROP FOREIGN KEY fk_dependencies_task, ADD CONSTRAINT fk_dependencies_task FOREIGN KEY(task_id,project_id) REFERENCES tasks(project_id,id)",
        ),
        (
            "foreign_target_order",
            False,
            [
                "ALTER TABLE tasks ADD UNIQUE KEY probe_target(id,project_id)",
                "ALTER TABLE task_dependencies DROP FOREIGN KEY fk_dependencies_task, ADD CONSTRAINT fk_dependencies_task FOREIGN KEY(project_id,task_id) REFERENCES tasks(id,project_id)",
            ],
        ),
        ("foreign_cascade", False, foreign.format("users", " ON DELETE CASCADE")),
        ("check_true", False, check.format("1=1")),
        ("check_expanded_in", False, check.format("active IN (0,1,2)")),
        ("check_or_true", False, check.format("active IN (0,1) OR 1=1")),
        (
            "column_type",
            None,
            "ALTER TABLE users MODIFY active SMALLINT UNSIGNED NOT NULL DEFAULT 1",
        ),
        (
            "column_nullable",
            None,
            "ALTER TABLE users MODIFY active TINYINT UNSIGNED NULL DEFAULT 1",
        ),
        ("column_default", None, "ALTER TABLE users ALTER active SET DEFAULT 0"),
        (
            "column_auto_increment",
            None,
            "ALTER TABLE notifications MODIFY id INT UNSIGNED NOT NULL",
        ),
        (
            "index_prefix",
            None,
            "ALTER TABLE users DROP INDEX uq_users_username, ADD UNIQUE KEY uq_users_username(username(8))",
        ),
        ("engine", None, "ALTER TABLE idempotency_requests ENGINE=MyISAM"),
        ("table_collation", None, "ALTER TABLE projects DEFAULT COLLATE=utf8mb4_bin"),
        (
            "column_collation",
            None,
            "ALTER TABLE users MODIFY password_hash VARCHAR(255) CHARACTER SET ascii COLLATE ascii_general_ci NOT NULL",
        ),
        ("check_enforcement", None, "ALTER TABLE users ALTER CHECK ck_users_active NOT ENFORCED"),
    ]

    if not corrected_fk:
        return values
    selected = []
    names = {
        "foreign_noaction_restrict",
        "foreign_qualified_self",
        "foreign_target_table",
        "foreign_target_schema",
        "foreign_source_order",
        "foreign_target_order",
        "foreign_cascade",
    }
    for name, expected, changes in values:
        if name not in names:
            continue
        split = []
        for statement in [changes] if isinstance(changes, str) else changes:
            if " DROP FOREIGN KEY " in statement and ", ADD CONSTRAINT " in statement:
                drop, add = statement.split(", ADD CONSTRAINT ", 1)
                split.extend(
                    [drop, drop.split(" DROP FOREIGN KEY ", 1)[0] + " ADD CONSTRAINT " + add]
                )
            else:
                split.append(statement)
        selected.append((name, expected, split))
    return selected


def run(receipt, corrected_fk=False):
    import pymysql
    from sqlalchemy import URL, create_engine
    from t44.persistence.migrations import check_schema

    root = Path(__file__).resolve().parents[2]
    ddl = (root / "specs/database/schema.sql").read_bytes()
    if hashlib.sha256(ddl).hexdigest() != DDL_HASH:
        raise ValueError("Frozen DDL mismatch")
    statements = [s.strip() for s in re.sub(r"--[^\n]*", "", ddl.decode()).split(";") if s.strip()]
    tables = re.findall(r"CREATE TABLE (\w+)", ddl.decode())
    if len(tables) != 18:
        raise ValueError("Unexpected frozen table set")
    version = subprocess.check_output([str(BINARY), "--no-defaults", "--version"], text=True)
    if "8.4.11" not in version:
        raise ValueError("Only root-approved pinned8.4.11 binary")
    receipt["binary_version"] = version.strip()
    if corrected_fk:
        if RESOURCE.is_symlink() or not RESOURCE.is_dir():
            raise ValueError("Approved resource directory identity changed")
        data, sock, pidfile = RESOURCE / "data2", RESOURCE / "s2", RESOURCE / "pid2"
        if data.exists() or sock.exists() or pidfile.exists():
            raise ValueError("Correction resources must be new; preserve previous data")
    else:
        RESOURCE.mkdir(mode=0o700, exist_ok=False)
        data, sock, pidfile = RESOURCE / "data", RESOURCE / "s", RESOURCE / "pid"
    suffix = "2" if corrected_fk else ""
    if len(os.fsencode(sock)) >= 100:
        raise ValueError("Socket path too long")
    process = connection = None
    started = time.monotonic()

    def deadline(*_):
        raise TimeoutError("Calibration570second deadline; reserve30forcleanup")

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
                f"--log-error={RESOURCE / ('initialize' + suffix + '.log')}",
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
            f"--log-error={RESOURCE / ('server' + suffix + '.log')}",
        ]
        process = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        receipt["process"] = {"pid": process.pid, "args": args}
        for _ in range(150):
            if process.poll() is not None:
                raise RuntimeError("Own mysqld exited before startup; logs preserved")
            try:
                connection = pymysql.connect(
                    user="root",
                    unix_socket=str(sock),
                    charset="utf8mb4",
                    connect_timeout=2,
                    read_timeout=10,
                    write_timeout=10,
                    autocommit=True,
                )
                break
            except pymysql.err.OperationalError:
                time.sleep(0.1)
        if connection is None:
            raise TimeoutError("Own socket server startup")
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT @@datadir,@@pid_file,@@version,@@sql_mode,@@sql_quote_show_create,@@character_set_client,@@collation_server,@@lower_case_table_names"
            )
            values = cursor.fetchone()
            if Path(values[0]).resolve() != data.resolve() or Path(values[1]) != pidfile:
                raise RuntimeError("Connected server is not owned instance")
            receipt["server_context"] = dict(
                zip(
                    (
                        "datadir",
                        "pid_file",
                        "version",
                        "sql_mode",
                        "sql_quote_show_create",
                        "character_set_client",
                        "collation_server",
                        "lower_case_table_names",
                    ),
                    values,
                    strict=True,
                )
            )
            receipt["owned_command_before_cases"] = owned()

            def create(schema, reset=False):
                if schema not in (REFERENCE, ACTUAL):
                    raise ValueError("Only two approved fresh schemas")
                if reset:
                    cursor.execute(f"DROP DATABASE `{schema}`")
                cursor.execute(
                    f"CREATE DATABASE `{schema}` CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci"
                )
                cursor.execute(f"USE `{schema}`")
                for statement in statements:
                    cursor.execute(statement)

            def show(schema):
                cursor.execute(f"USE `{schema}`")
                values = {}
                for table in tables:
                    cursor.execute(f"SHOW CREATE TABLE `{table}`")
                    values[table] = cursor.fetchone()[1]
                return values

            def legacy():
                engine = create_engine(
                    URL.create(
                        "mysql+pymysql",
                        username="root",
                        database=ACTUAL,
                        query={"unix_socket": str(sock), "charset": "utf8mb4"},
                    )
                )
                try:
                    return check_schema(engine)
                finally:
                    engine.dispose()

            create(REFERENCE)
            expected = show(REFERENCE)
            receipt["reference"] = {
                "source_ddl_sha256": DDL_HASH,
                "origin": "fresh approved schema from frozenDDL;not target marker",
                "show_create": expected,
            }
            reference = {k: normalize_show(v) for k, v in expected.items()}
            create(ACTUAL)
            baseline = show(ACTUAL)
            receipt["baseline"] = {
                "show_create": baseline,
                "raw_canonical_pass": {k: normalize_show(v) for k, v in baseline.items()}
                == reference,
                "legacy": legacy(),
            }
            receipt["cases"] = []
            for name, expected_legacy, changes in cases(corrected_fk):
                create(ACTUAL, reset=True)
                entry = {
                    "name": name,
                    "old_required_pass": expected_legacy,
                    "changes": [changes] if isinstance(changes, str) else changes,
                }
                try:
                    for statement in entry["changes"]:
                        cursor.execute(statement)
                    actual = show(ACTUAL)
                    entry.update(
                        show_create=actual,
                        legacy=legacy(),
                        raw_canonical_defects=[
                            k for k, v in actual.items() if normalize_show(v) != reference[k]
                        ],
                    )
                    entry["raw_canonical_pass"] = not entry["raw_canonical_defects"]
                    entry["raw_breaks_old_compatible_case"] = (
                        expected_legacy is True and not entry["raw_canonical_pass"]
                    )
                except pymysql.MySQLError as error:
                    entry["DDL_REJECTED"] = {
                        "class": type(error).__name__,
                        "driver_code": error.args[0],
                    }
                receipt["cases"].append(entry)
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
            except Exception as error:
                receipt["shutdown_error_class"] = type(error).__name__
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
    parser.add_argument("--execute-approved", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--fk-correction", action="store_true")
    args = parser.parse_args()
    if not args.execute_approved:
        parser.error("Root approval and explicit execution required")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    receipt = {
        "base": BASE,
        "resource_approval": "root explicit socket-only two schemas/128M/600s",
        "old_13306_accesses": 0,
    }
    try:
        stream = os.fdopen(fd, "w", encoding="utf8")
    except BaseException:
        os.close(fd)
        raise
    with stream as output:
        try:
            source_root = Path(__file__).resolve().parents[2]
            receipt["tool_commit"] = subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=source_root, text=True
            ).strip()
            tool_source = Path(__file__).read_bytes()
            expected_source = subprocess.check_output(
                ["git", "show", "HEAD:tmp/796_database_ddl_probe/796_canonical_probe.py"],
                cwd=source_root,
            )
            if tool_source != expected_source:
                raise ValueError("Commit the exact prototype before calibration")
            receipt["tool_sha256"] = hashlib.sha256(tool_source).hexdigest()
            receipt["correction_of_first_run_setup"] = args.fk_correction
            run(receipt, corrected_fk=args.fk_correction)
            receipt["status"] = "calibrated;candidatecompatibilityresultsnotforcedgreen"
        except BaseException as error:
            receipt.update(
                status="failed;partialresultsanddatadirretained", error_class=type(error).__name__
            )
            raise
        finally:
            output.write(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n")
    print(
        json.dumps(
            {
                "status": receipt["status"],
                "stopped": receipt["own_server_stopped"],
                "cases": len(receipt.get("cases", [])),
            }
        )
    )


if __name__ == "__main__":
    main()
