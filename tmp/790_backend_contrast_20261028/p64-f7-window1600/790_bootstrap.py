"""Root-only fresh f7 P-arm bootstrap; original CLI users and original V2 seed function."""

import argparse
import hashlib
import importlib
import json
import os
import platform
import re
import secrets
import stat
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

UTC = timezone.utc  # noqa: UP017 -- cloud host Python 3.10.
SOURCE = "f7cdb5fa3b19f84d8ab0d0b042bf51a5b8484e8f"
HARDSTOP = datetime(2026, 10, 28, 16, 0, tzinfo=UTC)
ANCHOR = "2026-10-28T04:00:00Z"
DOCKER = ["docker", "--context", "default"]
sys.path.insert(0, str(Path(__file__).resolve().parent / "edge"))
authority = importlib.import_module("790_authority")
budget_guard = importlib.import_module("790_budget")


def write(path, value):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "wb") as stream:
        stream.write(value)
        stream.flush()
        os.fsync(stream.fileno())


def save(path, value):
    write(path, (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode())


def raw(path, private=False):
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(fd, "rb") as stream:
        info = os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode) or (private and (info.st_mode & 0o077)):
            raise ValueError("REGULAR_PRIVATE_INPUT_REQUIRED")
        return stream.read()


def stamp(value):
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.tzinfo is None or result.utcoffset().total_seconds() != 0:
        raise ValueError("EXPLICIT_UTC_REQUIRED")
    return result


def remaining_timeout(stop_utc, cap):
    remaining = (min(stamp(stop_utc), HARDSTOP) - datetime.now(UTC)).total_seconds()
    if remaining <= 0:
        raise ValueError("ABSOLUTE_DIAGNOSTIC_DEADLINE_EXPIRED")
    return min(cap, remaining)


def validate_binding(binding, now):
    match = re.fullmatch(r"t44-cloud-(r28p(7|16|64)gen[0-9]{2})-p", binding["project"])
    if (
        not match
        or binding["source_sha"] != SOURCE
        or binding["phase"] != "p"
        or binding["generation_kind"] != "exact-pinned-production-entry-generation-v4"
        or type(binding["source_file_count"]) is not int
        or binding["source_file_count"] < 1
        or binding["database"] != "t44c_" + match[1] + "_p"
        or binding["api_workers"] != int(match[2])
        or binding["entrypoint"] != "t44.api:app"
        or binding["profiling"] is not False
        or not now.timestamp() + 120
        < stamp(binding["stop_utc"]).timestamp()
        <= HARDSTOP.timestamp()
    ):
        raise ValueError("FRESH_EXACT_SOURCE_P7_P16_OR_P64_LIVE_BINDING_REQUIRED")
    return match[1]


def environment():
    return {
        key: value
        for key, value in os.environ.items()
        if not key.startswith(("MYSQL_", "RABBITMQ_", "COMPOSE_", "T44_", "DOCKER_"))
        and key not in {"DATABASE_URL", "AMQP_URL"}
    }


QUERY = """import json
from sqlalchemy import text
from t44.settings import Settings
from t44.persistence import create_mysql_engine,SqlAlchemyUnitOfWorkFactory
from t44.persistence.schema import TABLES
settings=Settings.from_env().mysql_settings()
assert settings.database == EXPECTED
engine=create_mysql_engine(settings)
with engine.connect() as c: assert c.execute(text('SELECT DATABASE()')).scalar_one()==EXPECTED
with SqlAlchemyUnitOfWorkFactory(engine)() as u:
 counts={name:u.gateway.count(name) for name in TABLES}
 projects=u.gateway.rows('projects',columns=('id',),order_by=('id',))
print(json.dumps({'counts':counts,'project_ids':[r['id'] for r in projects]}))
engine.dispose()
"""
PROBE = """import hashlib,json,os,stat
from pathlib import Path
root=Path('/app/backend');rows=[]
for p in sorted(list((root/'t44').rglob('*'))+[root/'requirements.lock',root/'pyproject.toml']):
 s=p.lstat()
 if stat.S_ISLNK(s.st_mode) or not (stat.S_ISDIR(s.st_mode) or stat.S_ISREG(s.st_mode)): raise ValueError('UNEXPECTED_SOURCE_OBJECT')
 if p.is_file(): rows.append({'path':'backend/'+p.relative_to(root).as_posix(),'bytes':s.st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'mode':stat.S_IMODE(s.st_mode)})
print(json.dumps({'files':rows,'uid':os.getuid()}))
"""


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase-dir", type=Path, required=True)
    parser.add_argument("--binding-sha256", required=True)
    parser.add_argument("--output-name", required=True)
    parser.add_argument("--anchor-at", required=True)
    parser.add_argument("--manifest-sha256", required=True)
    for name in ("budget-receipt", "root-grant", "scope-bridge-dir"):
        parser.add_argument("--" + name, type=Path, required=True)
    for name in ("budget-receipt-sha256", "root-grant-sha256"):
        parser.add_argument("--" + name, required=True)
    args = parser.parse_args(argv)
    phase = args.phase_dir
    if (
        os.geteuid() != 0
        or platform.system() != "Linux"
        or not phase.is_absolute()
        or phase.resolve() != phase
        or not re.fullmatch(r"[0-9a-f]{64}", args.binding_sha256)
        or not re.fullmatch(r"fixture790-[a-z0-9-]{1,32}", args.output_name)
        or args.anchor_at != ANCHOR
    ):
        raise ValueError("EXPLICIT_NEW_ROOT_PHASE_OUTPUT_AND_ANCHOR_REQUIRED")
    binding_raw = raw(phase / "binding.json", True)
    if hashlib.sha256(binding_raw).hexdigest() != args.binding_sha256:
        raise ValueError("EXACT_PHASE_BINDING_SHA_REQUIRED")
    binding = json.loads(binding_raw)
    run_id = validate_binding(binding, datetime.now(UTC))
    tool_root = Path(__file__).resolve().parent
    manifest_raw = raw(tool_root / "manifest.json")
    if hashlib.sha256(manifest_raw).hexdigest() != args.manifest_sha256:
        raise ValueError("EXACT_TOOL_MANIFEST_REQUIRED")
    for name, row in json.loads(manifest_raw)["files"].items():
        if hashlib.sha256(raw(tool_root / name)).hexdigest() != row["sha256"]:
            raise ValueError("EXACT_TOOL_FILE_REQUIRED")
    for name, wanted in binding["file_hashes"].items():
        path = phase / name
        if path.resolve() != path or hashlib.sha256(raw(path)).hexdigest() != wanted:
            raise ValueError("BOUND_PHASE_FILE_CHANGED")
    proof_raw = raw(phase.parent / "actual-source-files.json", True)
    if hashlib.sha256(proof_raw).hexdigest() != binding["source_actual_proof_sha256"]:
        raise ValueError("FULL_SOURCE_PROOF_CHANGED")
    proof = json.loads(proof_raw)
    if len(proof["files"]) != binding["source_file_count"]:
        raise ValueError("SOURCE_FILE_COUNT_DIFFERS_FROM_BOUND_PROOF")
    env = environment()
    subprocess.run(
        ["systemctl", "is-active", "--quiet", binding["timer_unit"]],
        check=True,
        timeout=15,
        env=env,
    )
    actual = (
        subprocess.check_output(
            DOCKER
            + ["image", "inspect", "--format", "{{.Id}}", binding["images"]["backend"]["alias"]],
            timeout=15,
            env=env,
        )
        .decode()
        .strip()
    )
    if actual not in {binding["image_ids"]["backend"], binding["config_ids"]["backend"]}:
        raise ValueError("EXACT_SOURCE_IMAGE_ID_REQUIRED")
    composition = json.loads(raw(phase / "compose.json", True))
    if set(composition["services"]["admin"]["networks"]) != {"data"}:
        raise ValueError("ADMIN_DATA_ONLY_NETWORK_REQUIRED")
    output = phase / args.output_name
    output.mkdir(mode=0o700)
    ca = raw(phase / "tls/ca.pem")
    if hashlib.sha256(ca).hexdigest() != binding["tls"]["ca_sha256"]:
        raise ValueError("BOUND_CA_CHANGED")
    control = {
        "kind": "t44-contrast-development-v1",
        "source_sha": SOURCE,
        "run_id": run_id,
        "binding_sha256": args.binding_sha256,
        "namespace": binding["project"],
        "database": binding["database"],
        "api_workers": binding["api_workers"],
        "url": f"https://{binding['app_private_ip']}:{binding['tls_port']}",
        "ca_sha256": binding["tls"]["ca_sha256"],
        "stop_utc": binding["stop_utc"],
        "seed": 44,
        "anchor_at": ANCHOR,
        "backend_image_id": actual,
        "source_proof_sha256": binding["source_actual_proof_sha256"],
        "source_file_count": len(proof["files"]),
    }
    control = authority.attach(control, raw(args.root_grant), args.root_grant_sha256, "prep", datetime.now(UTC))
    grant = authority.check_control(control, "prep", datetime.now(UTC))
    budget_guard.verify_roles(args, binding, grant, binding["stop_utc"])
    save(output / "control.private.json", control)
    base = DOCKER + [
        "compose",
        "--env-file",
        str(phase / "application.env"),
        "--file",
        str(phase / "compose.json"),
        "--project-name",
        binding["project"],
        "--profile",
        "operations",
        "run",
        "--rm",
        "--no-deps",
        "-T",
    ]

    def call(label, tail, data=None, timeout=120):
        name = run_id + "-790-" + label
        command = base + [
            "--name",
            name,
            "--label",
            "io.t44.contrast.owner=" + run_id,
            "--entrypoint",
            "python",
            "admin",
            "-B",
            *tail,
        ]
        budget = remaining_timeout(binding["stop_utc"], timeout)
        try:
            with budget_guard.admitted(args, binding, binding["stop_utc"]) as admission:
                save(output / (label + ".budget.PUBLIC.json"), admission)
                result = subprocess.run(
                    command, input=data, capture_output=True, check=False,
                    timeout=remaining_timeout(binding["stop_utc"], budget), env=env
                )
        except subprocess.TimeoutExpired as error:
            write(output / (label + ".stdout"), error.stdout or b"")
            write(output / (label + ".stderr"), error.stderr or b"")
            info = json.loads(
                subprocess.check_output(
                    DOCKER + ["inspect", "--format", "{{json .}}", name], env=env, timeout=15
                )
            )
            if (
                info["Image"]
                not in {binding["image_ids"]["backend"], binding["config_ids"]["backend"]}
                or info["Config"]["Labels"].get("io.t44.contrast.owner") != run_id
            ):
                raise RuntimeError("OWNED_TIMEOUT_CONTAINER_IDENTITY_MISMATCH") from None
            subprocess.run(
                DOCKER + ["stop", "--time", "15", name],
                capture_output=True,
                check=True,
                timeout=30,
                env=env,
            )
            raise RuntimeError("OWNED_BOOTSTRAP_TIMEOUT_PREFIX_PRESERVED") from None
        write(output / (label + ".stdout"), result.stdout)
        write(output / (label + ".stderr"), result.stderr)
        if result.returncode:
            raise RuntimeError("ORIGINAL_PRODUCT_COMMAND_FAILED_PREFIX_PRESERVED")
        remaining_timeout(binding["stop_utc"], timeout)
        return json.loads(result.stdout)

    observed = call("00-source", ["-c", PROBE])
    if observed["uid"] != 10001 or observed["files"] != proof["files"]:
        raise ValueError("ACTUAL_FULL_SOURCE_FILE_BYTES_MODES_DIFFER")
    query = "EXPECTED=" + repr(binding["database"]) + "\n" + QUERY
    before = call("01-empty", ["-c", query])
    if any(before["counts"].values()):
        raise ValueError("FRESH_EMPTY_APPLICATION_TABLES_REQUIRED")
    accounts = {
        role: {"username": "synthetic-" + role, "password": secrets.token_urlsafe(32)}
        for role in ("manager", "developer", "reviewer")
    }
    save(output / "credentials-reserved.private.json", accounts)
    for role, account in accounts.items():
        result = call(
            "02-init-" + role,
            [
                "-m",
                "t44.cli",
                "init-user",
                "--username",
                account["username"],
                "--display-name",
                "[synthetic] contrast " + role,
                "--password-stdin",
            ],
            (account["password"] + "\n").encode(),
        )
        if type(result.get("user_id")) is not int or result["user_id"] <= 0:
            raise ValueError("REAL_POSITIVE_USER_ID_REQUIRED")
        account["user_id"] = result["user_id"]
    if len({a["user_id"] for a in accounts.values()}) != 3:
        raise ValueError("THREE_DISTINCT_CLI_USERS_REQUIRED")
    save(output / "accounts.private.json", accounts)
    save(
        output / "identities.private.json",
        {
            role: {key: row[key] for key in ("username", "user_id")}
            for role, row in accounts.items()
        },
    )
    seed_code = """import json
from datetime import datetime
from t44.settings import Settings
from t44.persistence import create_mysql_engine,SqlAlchemyUnitOfWorkFactory
from t44.persistence.seed import seed_demo
from t44.services.common import wire
engine=create_mysql_engine(Settings.from_env().mysql_settings())
result=seed_demo(SqlAlchemyUnitOfWorkFactory(engine),projects=40,tasks=6000,dependencies=9000,records=15000,seed=44,anchor_at=datetime.fromisoformat(ANCHOR))
print(json.dumps(wire(result)));engine.dispose()
"""
    seed = call("03-seed-v2", ["-c", "ANCHOR=" + repr(ANCHOR) + "\n" + seed_code], timeout=600)
    after = call("04-counts", ["-c", query])
    counts = after["counts"]
    if (
        counts["users"] != 3
        or counts["projects"] != 40
        or counts["tasks"] != 6000
        or counts["task_dependencies"] != 9000
        or counts["reviews"] + counts["decisions"] != 15000
        or len(after["project_ids"]) != 40
        or seed["manifest"]["version"] != 2
        or seed["manifest"]["seed"] != 44
        or stamp(seed["manifest"]["anchor_at"]) != stamp(ANCHOR)
    ):
        raise ValueError("ACTUAL_V2_SEED_OR_COUNTS_DIFFER")
    receipt = {
        "kind": "contrast790-bootstrap-complete-not-acceptance",
        "source_sha": SOURCE,
        "binding_sha256": args.binding_sha256,
        "namespace": binding["project"],
        "database": binding["database"],
        "counts": counts,
        "project_ids": after["project_ids"],
        "seed_manifest": seed["manifest"],
        "seed_manifest_sha256": seed["manifest_sha256"],
        "account_ids": {role: value["user_id"] for role, value in accounts.items()},
        "full_source_files_verified": len(observed["files"]),
        "output_dir": str(output),
        "control_sha256": hashlib.sha256(raw(output / "control.private.json", True)).hexdigest(),
        "api_scheduler_or_load_started": False,
        "root_prep_grant_sha256": args.root_grant_sha256,
        "session_nonce": grant["session_nonce"],
        "formal_acceptance": False,
    }
    save(output / "result.public.json", receipt)
    print(json.dumps(receipt))


if __name__ == "__main__":
    os.umask(0o077)
    try:
        main()
    except (
        OSError,
        ValueError,
        RuntimeError,
        KeyError,
        TypeError,
        AssertionError,
        subprocess.SubprocessError,
    ) as error:
        print(
            json.dumps({"bootstrap_failed": type(error).__name__, "partial_state_preserved": True})
        )
        raise SystemExit(1) from None
