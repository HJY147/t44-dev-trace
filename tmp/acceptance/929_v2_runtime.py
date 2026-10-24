"""Neutral local v2 runtime provisioning; no independent cases or assertions are read."""

import argparse
import hashlib
import json
import os
import secrets
import subprocess
import sys
import tarfile
from datetime import UTC, datetime
from pathlib import Path

import pymysql
from sqlalchemy import URL

ROOT = Path(__file__).resolve().parents[2]
RUNTIME = ROOT / ".agent-worktrees/.runtime"
PRIVATE = RUNTIME / "local-acceptance-v2"
SOURCE = "4c20f32b71635016815420472b9d4bb4fa850df0"
TARGETS = {"ui": "t44_ui_v2", "perf": "t44_perf_v2"}


def private_json(path, value):
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w") as output:
        json.dump(value, output, ensure_ascii=False, indent=2)
        output.write("\n")


def environment(target):
    return {
        **os.environ,
        **json.loads((PRIVATE / (target + "-environment.json")).read_text()),
    }


def provision():
    if PRIVATE.exists():
        raise RuntimeError("Refuse to overwrite an existing v2 runtime directory")
    PRIVATE.mkdir(mode=0o700)
    snapshot = PRIVATE / "source" / SOURCE
    snapshot.mkdir(parents=True)
    archive = PRIVATE / "source.tar"
    selected = ["backend", "frontend", "specs/contracts/openapi.json"]
    with archive.open("wb") as output:
        subprocess.run(
            ["git", "archive", SOURCE, *selected], cwd=ROOT, stdout=output, check=True
        )
    with tarfile.open(archive) as contents:
        contents.extractall(snapshot, filter="data")
    archive.unlink()
    app = json.loads((RUNTIME / "mysql-8.4/credentials.json").read_text())
    admin = json.loads((RUNTIME / "mysql-8.4/admin.json").read_text())
    with (
        pymysql.connect(
            host=app["host"],
            port=app["port"],
            user=app["username"],
            password=app["password"],
        ) as connection,
        connection.cursor() as cursor,
    ):
        cursor.execute("SELECT CURRENT_USER()")
        username, hostname = cursor.fetchone()[0].rsplit("@", 1)
    if hostname not in {"localhost", "127.0.0.1", "::1"}:
        raise RuntimeError("Expected a loopback-only project application principal")
    created = []
    with (
        pymysql.connect(
            unix_socket=admin["socket"],
            user=admin["username"],
            password=admin["password"],
            autocommit=True,
        ) as connection,
        connection.cursor() as cursor,
    ):
        for label, database in TARGETS.items():
            cursor.execute(
                "SELECT COUNT(*) FROM information_schema.schemata WHERE schema_name=%s",
                (database,),
            )
            if cursor.fetchone()[0]:
                raise RuntimeError("Refuse to reuse existing v2 database")
            cursor.execute(
                f"CREATE DATABASE `{database}` CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci"
            )
            cursor.execute(
                f"GRANT ALL PRIVILEGES ON `{database}`.* TO %s@%s",
                (username, hostname),
            )
            audit_user, audit_password = (
                "t44_v2_" + label + "_audit",
                secrets.token_urlsafe(32),
            )
            cursor.execute(
                "CREATE USER %s@%s IDENTIFIED BY %s",
                (audit_user, hostname, audit_password),
            )
            cursor.execute(
                f"GRANT SELECT ON `{database}`.* TO %s@%s", (audit_user, hostname)
            )
            read_url = URL.create(
                "mysql+pymysql",
                username=audit_user,
                password=audit_password,
                host=app["host"],
                port=app["port"],
                database=database,
            )
            private_json(
                PRIVATE / (label + "-readonly.json"),
                {"database_url": read_url.render_as_string(hide_password=False)},
            )
            url = URL.create("mysql+pymysql", database=database, **app)
            private_json(
                PRIVATE / (label + "-environment.json"),
                {
                    "PYTHONPATH": str(snapshot / "backend"),
                    "DATABASE_URL": url.render_as_string(hide_password=False),
                    "T44_DATABASE": database,
                    "T44_SESSION_TTL_SECONDS": "86400",
                    "AMQP_URL": "amqp://unavailable:unavailable@127.0.0.1:13307/"
                    + database,
                },
            )
            created.append(database)
    commands = []
    for label, database in TARGETS.items():
        accounts = {}

        def run(arguments, data=None, *, label=label):
            result = subprocess.run(
                [sys.executable, "-m", "t44.cli", *arguments],
                input=data,
                capture_output=True,
                text=True,
                cwd=snapshot,
                env=environment(label),
                timeout=120,
                check=False,
            )
            commands.append(
                {
                    "target": label,
                    "arguments": arguments,
                    "exit_code": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                }
            )
            if result.returncode:
                raise RuntimeError("Neutral CLI provisioning step failed")
            return json.loads(result.stdout)

        run(["migrate", "--database", database])
        for role in ("manager", "developer", "reviewer"):
            password = secrets.token_urlsafe(30)
            result = run(
                [
                    "init-user",
                    "--username",
                    "synthetic-" + role,
                    "--display-name",
                    "[synthetic] v2 " + role,
                    "--password-stdin",
                ],
                password + "\n",
            )
            accounts[role] = {
                "username": "synthetic-" + role,
                "password": password,
                **result,
            }
        private_json(PRIVATE / (label + "-credentials.json"), accounts)
        run(["seed-demo"])
    source_hashes = {
        str(path.relative_to(snapshot)): hashlib.sha256(path.read_bytes()).hexdigest()
        for directory in (snapshot / "backend/t44", snapshot / "frontend/src")
        for path in sorted(directory.rglob("*"))
        if path.is_file() and "__pycache__" not in path.parts
    }
    receipt = {
        "prepared_at": datetime.now(UTC).isoformat(),
        "source_commit": SOURCE,
        "snapshot": str(snapshot.relative_to(ROOT)),
        "new_databases": created,
        "old_independent_databases_accessed": False,
        "new_readonly_audit_principals": True,
        "commands": commands,
        "source_file_hashes": source_hashes,
        "processes_started": False,
        "independent_cases_accessed": False,
        "independent_tests_executed": False,
        "secrets": "Only local ignored 0600 files; not in this receipt",
    }
    (ROOT / "records/validation/local-acceptance-v2-provisioning.json").write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2) + "\n"
    )
    print(
        json.dumps(
            {
                "prepared": True,
                "source_commit": SOURCE,
                "new_databases": created,
                "processes_started": False,
            }
        )
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["provision", "cli", "api"])
    parser.add_argument("--target", choices=tuple(TARGETS), default="ui")
    args, arguments = parser.parse_known_args()
    if arguments and args.mode != "cli":
        parser.error("Only cli accepts additional arguments")
    if args.mode == "provision":
        provision()
        return 0
    env = environment(args.target)
    snapshot = PRIVATE / "source" / SOURCE
    if args.mode == "cli":
        return subprocess.run(
            [sys.executable, "-m", "t44.cli", *arguments],
            cwd=snapshot,
            env=env,
            check=False,
        ).returncode
    port, workers = (18084, 1) if args.target == "ui" else (18085, 4)
    os.chdir(snapshot)
    os.environ.update(env)
    os.execv(
        sys.executable,
        [
            sys.executable,
            "-m",
            "uvicorn",
            "t44.api:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
            "--workers",
            str(workers),
        ],
    )


if __name__ == "__main__":
    raise SystemExit(main())
