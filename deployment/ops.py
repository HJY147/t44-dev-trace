"""Explicit local operations. No source/reset/down-volume or live-database restore."""

import argparse
import getpass
import hashlib
import json
import os
import re
import secrets
import stat
import subprocess
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IDENTIFIER = re.compile(r"[a-z][a-z0-9_]{0,47}\Z")
PROJECT = re.compile(r"t44-restore-[a-z0-9][a-z0-9-]{0,31}\Z")
MYSQL = 'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" exec mysql --user=root --batch --skip-column-names'
DUMP = (
    'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" exec mysqldump --user=root '
    '--single-transaction --quick --hex-blob --no-tablespaces --set-gtid-purged=OFF '
    '--column-statistics=0 --skip-add-drop-table --skip-add-locks --skip-disable-keys '
    '--skip-comments --skip-triggers --routines=false --events=false "$MYSQL_DATABASE"'
)


def identifier(value: str) -> str:
    if not IDENTIFIER.fullmatch(value) or value in {"mysql", "sys", "information_schema", "performance_schema"}:
        raise ValueError("database/user must be a non-system lowercase identifier")
    return value


def generate_env(path: Path) -> None:
    values = {
        "COMPOSE_PROJECT_NAME": "t44",
        "T44_DOCKER_CONTEXT": "default",
        "MYSQL_DATABASE": "t44",
        "MYSQL_USER": "t44",
        "MYSQL_PASSWORD": secrets.token_hex(32),
        "MYSQL_ROOT_PASSWORD": secrets.token_hex(32),
        "RABBITMQ_DEFAULT_USER": "t44",
        "RABBITMQ_DEFAULT_PASS": secrets.token_hex(32),
        "RABBITMQ_DEFAULT_VHOST": "t44",
        "T44_HTTP_PORT": "8080",
        "T44_SESSION_TTL_SECONDS": "3600",
        "T44_IMAGE_TAG": "local",
    }
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w") as stream:
        stream.write("# Private generated configuration; do not commit or paste into logs.\n")
        stream.writelines(f"{key}={value}\n" for key, value in values.items())
    print(f"Created private configuration at {path}; existing files are never overwritten.")


def load_env(path: Path) -> dict[str, str]:
    if path.is_symlink() or not path.is_file() or stat.S_IMODE(path.stat().st_mode) & 0o077:
        raise ValueError("configuration must be a regular private file (mode 0600)")
    values = {}
    for line in path.read_text().splitlines():
        if not line or line.startswith("#"):
            continue
        key, separator, value = line.partition("=")
        if not separator or not re.fullmatch(r"[A-Z][A-Z0-9_]*", key) or key in values:
            raise ValueError("invalid or duplicate configuration entry")
        if not re.fullmatch(r"[A-Za-z0-9_.-]+", value):
            raise ValueError("configuration supports only unquoted URL-safe values")
        values[key] = value
    identifier(values["MYSQL_DATABASE"])
    identifier(values["MYSQL_USER"])
    for name in ["MYSQL_PASSWORD", "MYSQL_ROOT_PASSWORD", "RABBITMQ_DEFAULT_PASS"]:
        if not re.fullmatch(r"[0-9a-f]{64}", values[name]):
            raise ValueError("generate independent 256-bit credentials with init-env")
    if len({values[key] for key in ["MYSQL_PASSWORD", "MYSQL_ROOT_PASSWORD", "RABBITMQ_DEFAULT_PASS"]}) != 3:
        raise ValueError("credentials must be independent")
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,47}", values["COMPOSE_PROJECT_NAME"]):
        raise ValueError("invalid Compose project")
    return values


def compose(env_file: Path, values: dict[str, str], *args: str, project: str | None = None, **kwargs):
    # Prevent an inherited shell DATABASE/COMPOSE setting from changing the selected target.
    environment = {key: value for key, value in os.environ.items()
                   if key not in values and key not in {"DOCKER_HOST", "DOCKER_CONTEXT"}}
    environment.update(values)
    command = ["docker", "--context", values["T44_DOCKER_CONTEXT"], "compose",
               "--env-file", str(env_file), "--file", str(ROOT / "compose.yaml")]
    command += ["--project-name", project or values["COMPOSE_PROJECT_NAME"], *args]
    return subprocess.run(command, env=environment, check=True, **kwargs)


def query(env_file: Path, values: dict[str, str], sql: str, project: str | None = None) -> str:
    result = compose(env_file, values, "exec", "-T", "mysql", "sh", "-c", MYSQL, project=project,
                     input=sql.encode(), stdout=subprocess.PIPE)
    return result.stdout.decode().strip()


def check_primary(values: dict[str, str], database: str) -> None:
    if identifier(database) != values["MYSQL_DATABASE"]:
        raise ValueError("explicit database differs from configured application database")


def backup(env_file: Path, values: dict[str, str], database: str, output: Path) -> None:
    check_primary(values, database)
    manifest = output.with_name(output.name + ".manifest.json")
    if output.exists() or output.is_symlink() or manifest.exists() or manifest.is_symlink():
        raise ValueError("backup and manifest targets must not exist")
    # Current schema has tables only: fail rather than silently omit new executable objects.
    count = query(env_file, values,
                  f"SELECT (SELECT COUNT(*) FROM information_schema.TRIGGERS WHERE TRIGGER_SCHEMA='{database}')"
                  f"+(SELECT COUNT(*) FROM information_schema.ROUTINES WHERE ROUTINE_SCHEMA='{database}')"
                  f"+(SELECT COUNT(*) FROM information_schema.EVENTS WHERE EVENT_SCHEMA='{database}');")
    if count != "0":
        raise ValueError("programmable objects require a separately reviewed backup contract")
    invalid = query(env_file, values,
                    f"SELECT COUNT(*) FROM information_schema.TABLES WHERE TABLE_SCHEMA='{database}'"
                    " AND (TABLE_TYPE <> 'BASE TABLE' OR COALESCE(ENGINE,'') <> 'InnoDB');")
    table_count = int(query(env_file, values,
                           f"SELECT COUNT(*) FROM information_schema.TABLES WHERE TABLE_SCHEMA='{database}';"))
    if invalid != "0" or table_count == 0:
        raise ValueError("backup requires a nonempty InnoDB-only schema without views")
    with tempfile.NamedTemporaryFile(dir=output.parent, prefix=".t44-backup-", delete=False) as stream:
        temporary = Path(stream.name)
        try:
            compose(env_file, values, "exec", "-T", "mysql", "sh", "-c", DUMP, stdout=stream)
            stream.flush()
            os.fsync(stream.fileno())
            if not temporary.stat().st_size:
                raise ValueError("empty backup")
            with temporary.open("rb") as saved:
                digest = hashlib.file_digest(saved, "sha256").hexdigest()
            metadata = {"format": "t44-table-dump-v1", "database": database, "sha256": digest,
                        "created_at": datetime.now(UTC).isoformat(), "table_count": table_count,
                        "scope": "InnoDB tables; no routines/events/triggers/views"}
            # Exclusive hard-link publication never overwrites an existing file/symlink.
            os.link(temporary, output)
            descriptor = os.open(manifest, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(descriptor, "w") as sidecar:
                json.dump(metadata, sidecar, indent=2)
                sidecar.write("\n")
        finally:
            temporary.unlink(missing_ok=True)
    print(f"Backup and checksum manifest created: {output}")


def restore(env_file: Path, values: dict[str, str], args) -> None:
    target = identifier(args.database)
    if target == values["MYSQL_DATABASE"] or not PROJECT.fullmatch(args.project):
        raise ValueError("restore requires a new t44-restore-* project and a different database")
    if args.confirm_target != f"{args.project}/{target}":
        raise ValueError("--confirm-target must exactly match project/database")
    manifest = args.input.with_name(args.input.name + ".manifest.json")
    if args.input.is_symlink() or manifest.is_symlink():
        raise ValueError("backup/manifest symlinks are not accepted")
    metadata = json.loads(manifest.read_text())
    with args.input.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    if metadata.get("format") != "t44-table-dump-v1" or metadata.get("sha256") != digest:
        raise ValueError("unsupported backup format or checksum mismatch")
    identifier(metadata["database"])
    print(f"Isolated recovery target: project={args.project}, database={target}; checksum verified.")
    if not args.execute:
        print("Plan only. --execute creates a fresh isolated MySQL volume and imports the selected backup.")
        return
    if args.project == values["COMPOSE_PROJECT_NAME"]:
        raise ValueError("refusing live project")
    existing = subprocess.run(["docker", "--context", values["T44_DOCKER_CONTEXT"],
                               "volume", "inspect", f"{args.project}_mysql_data"],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
    if existing.returncode == 0:
        raise ValueError("recovery volume already exists; choose a new project, never reset it")
    isolated = {**values, "MYSQL_DATABASE": target}
    compose(env_file, isolated, "up", "-d", "--wait", "--wait-timeout", "180", "mysql", project=args.project)
    count = query(env_file, isolated,
                  f"SELECT COUNT(*) FROM information_schema.TABLES WHERE TABLE_SCHEMA='{target}';", args.project)
    if count != "0":
        raise ValueError("recovery target is not empty")
    # Input is our checksum-verified dump, generated without DROP/USE/CREATE DATABASE.
    with args.input.open("rb") as stream:
        compose(env_file, isolated, "exec", "-T", "mysql", "sh", "-c",
                MYSQL + ' --binary-mode=1 --database="$MYSQL_DATABASE"', project=args.project, stdin=stream)
    recovered = int(query(env_file, isolated,
                          f"SELECT COUNT(*) FROM information_schema.TABLES WHERE TABLE_SCHEMA='{target}';", args.project))
    if recovered != metadata.get("table_count"):
        raise ValueError("recovered table count differs from backup manifest; keep isolated for investigation")
    print("Imported into isolated recovery instance. Schema/version/row-count and application verification remain required.")
    print("The recovery instance remains running; this tool never removes its volume or replaces live data.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-file", type=Path, default=ROOT / ".env")
    sub = parser.add_subparsers(dest="operation", required=True)
    generate = sub.add_parser("init-env")
    generate.add_argument("--output", type=Path, default=ROOT / ".env")
    for name in ["build", "infra", "start", "stop", "status", "config-check"]:
        sub.add_parser(name)
    migrate = sub.add_parser("migrate")
    migrate.add_argument("--database", required=True)
    migrate.add_argument("--execute", action="store_true")
    save = sub.add_parser("backup")
    save.add_argument("--database", required=True)
    save.add_argument("--output", type=Path, required=True)
    recover = sub.add_parser("restore")
    recover.add_argument("--database", required=True)
    recover.add_argument("--project", required=True)
    recover.add_argument("--confirm-target", required=True)
    recover.add_argument("--input", type=Path, required=True)
    recover.add_argument("--execute", action="store_true")
    scheduler_token = sub.add_parser("scheduler-token")
    scheduler_token.add_argument("--name", default="scheduler")
    scheduler_token.add_argument("--project-id", type=int, action="append", required=True)
    scheduler_token.add_argument("--rotate", action="store_true")
    seed = sub.add_parser("seed-demo")
    seed.add_argument("--database", required=True)
    for name, default in [("projects", 40), ("tasks", 6000), ("dependencies", 9000), ("records", 15000)]:
        seed.add_argument("--" + name, type=int, default=default)
    account = sub.add_parser("account")
    account_sub = account.add_subparsers(dest="action", required=True)
    initialize = account_sub.add_parser("init-user")
    initialize.add_argument("--username", required=True)
    initialize.add_argument("--display-name", required=True)
    revoke_user = account_sub.add_parser("revoke-sessions")
    revoke_user.add_argument("--user-id", required=True)
    revoke_session = account_sub.add_parser("revoke-session")
    revoke_session.add_argument("--session-id", required=True)
    args = parser.parse_args()
    try:
        if args.operation == "init-env":
            generate_env(args.output)
            return 0
        values = load_env(args.env_file)
        if args.operation == "backup":
            backup(args.env_file, values, args.database, args.output)
        elif args.operation == "restore":
            restore(args.env_file, values, args)
        elif args.operation == "migrate":
            check_primary(values, args.database)
            if not args.execute:
                print("Plan only: reviewed backend t44.cli migrate --database <selected database>; implementation required.")
            else:
                compose(args.env_file, values, "--profile", "operations", "run", "--rm", "-T", "migrate")
        elif args.operation == "seed-demo":
            check_primary(values, args.database)
            command = ["seed-demo"]
            for name in ["projects", "tasks", "dependencies", "records"]:
                command += ["--" + name, str(getattr(args, name))]
            compose(args.env_file, values, "--profile", "operations", "run", "--rm", "-T", "admin", *command)
        elif args.operation == "scheduler-token":
            running = False
            if args.rotate:
                listing = compose(args.env_file, values, "ps", "--services", "--status", "running",
                                  stdout=subprocess.PIPE, text=True)
                running = "scheduler" in listing.stdout.splitlines()
                if running:
                    compose(args.env_file, values, "stop", "scheduler")
            command = ["--name", args.name]
            for project in args.project_id:
                command += ["--project-id", str(project)]
            if args.rotate:
                command.append("--rotate")
            compose(args.env_file, values, "--profile", "operations", "run", "--rm", "-T", "credential-admin", *command)
            if running:
                compose(args.env_file, values, "up", "-d", "--no-deps", "--wait", "scheduler")
        elif args.operation == "account":
            command = [args.action]
            password = None
            if args.action == "init-user":
                if not sys.stdin.isatty() or not sys.stderr.isatty():
                    raise ValueError("interactive account initialization requires a terminal without echo")
                command += ["--username", args.username, "--display-name", args.display_name, "--password-stdin"]
                password = getpass.getpass("New account password: ")
                if not password or password != getpass.getpass("Repeat password: "):
                    raise ValueError("passwords must be nonempty and match")
            elif args.action == "revoke-sessions":
                command += ["--user-id", args.user_id]
            else:
                command += ["--session-id", args.session_id]
            compose(args.env_file, values, "--profile", "operations", "run", "--rm", "-T", "admin", *command,
                    input=(password + "\n").encode() if password else None)
        else:
            commands = {"build": ["build", "api", "web"],
                        "infra": ["up", "-d", "--wait", "mysql", "rabbitmq"],
                        "start": ["up", "-d", "--build", "--wait", "api", "consumer", "scheduler", "web"],
                        "stop": ["stop"], "status": ["ps"], "config-check": ["config", "--quiet"]}
            compose(args.env_file, values, *commands[args.operation])
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError):
        print("Operation failed; verify target, private configuration and Docker/application prerequisites. Secrets are suppressed.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
