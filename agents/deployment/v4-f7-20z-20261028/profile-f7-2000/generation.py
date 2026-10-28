"""Fresh pinned production-entry generation; immutable prior campaigns remain untouched."""

import argparse
import hashlib
import importlib.util
import json
import os
import platform
import re
import secrets
import stat
import sys
import time
from datetime import datetime
from pathlib import Path
from uuid import uuid4

SOURCE = "f7cdb5fa3b19f84d8ab0d0b042bf51a5b8484e8f"
SOURCE_COUNT = 53
OLD_SOURCE = "935ab5b93bea788672c2b4a088c79cfeed848954"
FACTORY_SHA = "daaf29d3b47ab266ae4546f001e322275db5c3c902c9f36f8b8a2528690af2ea"
BUILDER_SHA = "d2fc28b2f0c19b19a81c2ac10c0712767c6182d8b3e2b5e7f2346da62bf2bbf5"
PROOF_SHA = "47b50d0111737d2b4ff7b47ce37c46bc5d7fc208d2f3933088b8a08dab326fc0"
RAW_SHA = "30b1ca48f152cae797862319cdda80c0a0b65ed5af32acf4b18ea55d531cc8d0"
HARDSTOP = "2026-10-28T20:00:00Z"
DOCKER = ["docker", "--context", "default"]
BUDGET_SHA = "305f9eaeea96b0ef882ec17a457f51852bafc8c34b5fe2e47056bd12625dd82d"


def budget_module(phase=None):
    directory = phase if phase is not None else Path(__file__).resolve().parent
    return load(directory / "mysql-budget.py", BUDGET_SHA, "v4_mysql_budget")
PROBE_FILES = """import hashlib,json,os,stat
from pathlib import Path
root=Path('/app/backend');paths=list((root/'t44').rglob('*'))+[root/'requirements.lock',root/'pyproject.toml'];rows=[]
for p in sorted(paths):
 s=p.lstat()
 if stat.S_ISLNK(s.st_mode) or not (stat.S_ISDIR(s.st_mode) or stat.S_ISREG(s.st_mode)): raise ValueError('UNEXPECTED_SOURCE_OBJECT')
 if p.is_file():
  data=p.read_bytes();rows.append({'path':'backend/'+p.relative_to(root).as_posix(),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'mode':stat.S_IMODE(s.st_mode)})
print(json.dumps({'files':rows,'uid':os.getuid(),'business_env_absent':not any(k in os.environ for k in ['DATABASE_URL','AMQP_URL','T44_DATABASE'])}))
"""


def sha(p):
    h = hashlib.sha256()
    with p.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def load(p, expected, name):
    if sha(p) != expected:
        raise ValueError("EXACT_FROZEN_PUBLIC_LIBRARY_REQUIRED")
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location(name, p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def valid_window(lib, value, minimum=240):
    deadline = lib.expiry(value)
    if deadline > lib.expiry(HARDSTOP) or deadline < time.time() + minimum:
        raise ValueError("BOUNDED_FUTURE_WINDOW_WITHIN_RESUME_PROFILE_REQUIRED")


def exact_files(observed, expected):
    if (
        len(expected) != SOURCE_COUNT
        or observed.get("uid") != 10001
        or observed.get("business_env_absent") is not True
        or observed.get("files") != expected
    ):
        raise ValueError("ACTUAL_COMPLETE_SOURCE_FILES_REQUIRED")
    return {
        "files": SOURCE_COUNT,
        "bytes_hash_modes_and_nonroot_checked": True,
        "business_services_started": False,
    }


def nginx(lib):
    old = lib.nginx()
    marker = "  proxy_temp_path /tmp/proxy_temp;\n"
    if old.count(marker) != 1:
        raise ValueError("EXACT_FROZEN_NGINX_PREIMAGE_REQUIRED")
    return old.replace(
        marker,
        marker
        + "  fastcgi_temp_path /tmp/fastcgi_temp;\n  uwsgi_temp_path /tmp/uwsgi_temp;\n  scgi_temp_path /tmp/scgi_temp;\n",
    )


def verified_images(args, lib):
    lib.private(args.upgrade_binding)
    if sha(args.upgrade_binding) != args.upgrade_binding_sha256:
        raise ValueError("ROOT_PINNED_DERIVED_IMAGE_BINDING_REQUIRED")
    value = json.loads(args.upgrade_binding.read_text())
    if (
        value["kind"] != "offline-exact-source-backend-derived-build-only"
        or value["source_sha"] != SOURCE
        or value["base_source_sha"] != OLD_SOURCE
        or value["builder_sha256"] != BUILDER_SHA
    ):
        raise ValueError("EXACT_F4_DERIVED_V2_BUILD_REQUIRED")
    builder = load(
        args.source_package / "backend-upgrade.py", BUILDER_SHA, "frozen_upgrade_v2"
    )
    manifest, _ = builder.source_package(
        args.source_package, args.source_manifest_sha256
    )
    if (
        value["source_manifest_sha256"] != args.source_manifest_sha256
        or value["source_archive_sha256"] != manifest["source_archive_sha256"]
    ):
        raise ValueError("DERIVED_SOURCE_ARCHIVE_BINDING_MISMATCH")
    proof = load(args.image_proof, PROOF_SHA, "frozen_crypto_proof")
    archive = args.upgrade_binding.parent / "derived-backend.tar"
    lib.private(archive)
    if sha(archive) != value["derived_image_archive_sha256"]:
        raise ValueError("ACTUAL_DERIVED_ARCHIVE_CHANGED")
    actual = proof.actual_image(value["image_alias"])
    if (
        actual["Id"] != value["actual_image_id"]
        or actual["Descriptor"] != value["actual_descriptor"]
        or actual["Config"]["Labels"] != value["expected_labels"]
    ):
        raise ValueError("ACTUAL_DERIVED_RUNTIME_IDENTITY_CHANGED")
    identity = proof.prove_role(
        proof.scan_archive(archive),
        "backend",
        {
            "alias": value["image_alias"],
            "image_id": value["config_id"],
            "revision_label": SOURCE,
            "archive_label": manifest["source_archive_sha256"],
        },
        {
            "source_sha": SOURCE,
            "source_archive_sha256": manifest["source_archive_sha256"],
        },
        actual,
    )
    lib.private(args.original_proof)
    if sha(args.original_proof) != RAW_SHA:
        raise ValueError("ORIGINAL_COMPLETE_IMAGE_PROOF_REQUIRED")
    rows = [json.loads(line) for line in args.original_proof.read_text().splitlines()]
    if (
        rows[-1].get("kind") != "proof_final"
        or not rows[-1]["complete"]
        or not rows[-1]["all_seven_proven"]
    ):
        raise ValueError("ALL_ORIGINAL_ROLES_REQUIRED")
    images, proofs = {}, {}
    for role in ["backend", "web", "python", "node", "nginx", "mysql", "rabbitmq"]:
        matches = [
            r for r in rows if r.get("kind") == "role_proof" and r.get("role") == role
        ]
        if len(matches) != 1 or not matches[0]["proof"]["success"]:
            raise ValueError("EXACT_ORIGINAL_ROLE_REQUIRED")
        row = matches[0]
        current = proof.actual_image(row["declared_CI"]["alias"])
        if any(
            current[k] != row["actual_projection_no_Env_or_Cmd"][k]
            for k in [
                "Id",
                "Descriptor",
                "RootFS",
                "Os",
                "Architecture",
                "Variant",
                "Config",
            ]
        ):
            raise ValueError("PROVEN_ORIGINAL_ALIAS_CHANGED")
        images[role] = {"alias": row["declared_CI"]["alias"]}
        proofs[role] = row["proof"]
    images["backend"] = {"alias": value["image_alias"]}
    proofs["backend"] = identity
    probe = json.loads(
        lib.command(
            [
                *DOCKER,
                "run",
                "--rm",
                "--network",
                "none",
                "--read-only",
                "--user",
                "10001:10001",
                "--cap-drop",
                "ALL",
                "--security-opt",
                "no-new-privileges:true",
                "--entrypoint",
                "python",
                value["image_alias"],
                "-c",
                PROBE_FILES,
            ]
        )
    )
    exact_files(probe, manifest["files"])
    return images, proofs, value, manifest, probe


def prepare(args):
    lib = load(args.factory, FACTORY_SHA, "frozen_factory")
    if (
        os.geteuid() != 0
        or platform.system() != "Linux"
        or platform.machine() not in {"x86_64", "amd64"}
        or not re.fullmatch(r"[a-z][a-z0-9]{5,15}", args.run_id)
        or args.p_workers not in {7, 16, 64}
    ):
        raise ValueError("ROOT_LINUX_AMD64_FRESH_RUN_AND_EXPLICIT_WORKERS_REQUIRED")
    budget = budget_module()
    budget.pool_plan("p", args.p_workers, args.p_pool_size, args.p_max_overflow)
    valid_window(lib, args.stop_utc, 600)
    address = lib.private_ipv4(args.app_ip)
    ports = [
        ("f", args.f_tls_port, args.f_http_port, 4),
        ("p", args.p_tls_port, args.p_http_port, args.p_workers),
    ]
    all_ports = [v for _, a, b, _ in ports for v in [a, b]]
    if len(set(all_ports)) != 4 or any(
        type(v) is not int or not 1024 <= v <= 65535 or v == 13306 for v in all_ports
    ):
        raise ValueError("FOUR_FRESH_DISTINCT_NONMYSQL_PORTS_REQUIRED")
    for _, tls, http, _ in ports:
        lib.bind_free(address, tls)
        lib.bind_free("127.0.0.1", http)
    lib.private(args.output.parent, True)
    if not re.fullmatch(r"/[A-Za-z0-9_./-]+", str(args.output)):
        raise ValueError("SYSTEMD_SAFE_NEW_OUTPUT_REQUIRED")
    images, proofs, upgrade, manifest, observed = verified_images(args, lib)
    args.output.mkdir(mode=0o700)
    lib.save(args.output / "actual-source-files.json", observed)
    phases = {}
    for role, tls_port, http_port, workers in ports:
        project = "t44-cloud-" + args.run_id + "-" + role
        database = "t44c_" + args.run_id + "_" + role
        if (
            lib.command(
                [
                    *DOCKER,
                    "volume",
                    "ls",
                    "--quiet",
                    "--filter",
                    "label=com.docker.compose.project=" + project,
                ]
            ).strip()
            or lib.command(
                [
                    *DOCKER,
                    "ps",
                    "--all",
                    "--quiet",
                    "--filter",
                    "label=com.docker.compose.project=" + project,
                ]
            ).strip()
        ):
            raise ValueError("NEW_NAMESPACE_ONLY_NO_EXISTING_DATA_OR_CONTAINERS")
        phase = args.output / role
        phase.mkdir(mode=0o700)
        (phase / "receipts").mkdir(mode=0o700)
        for name in ["scheduler-secrets", "scheduler-locks"]:
            p = phase / name
            p.mkdir(mode=0o700)
            os.chown(p, 10001, 10001)
        env = {
            "COMPOSE_PROJECT_NAME": project,
            "MYSQL_DATABASE": database,
            "MYSQL_USER": database + "_app",
            "MYSQL_PASSWORD": secrets.token_hex(32),
            "MYSQL_ROOT_PASSWORD": secrets.token_hex(32),
            "RABBITMQ_DEFAULT_USER": "t44",
            "RABBITMQ_DEFAULT_PASS": secrets.token_hex(32),
            "RABBITMQ_DEFAULT_VHOST": project,
        }
        lib.write(
            phase / "application.env",
            "".join(k + "=" + v + "\n" for k, v in env.items()).encode(),
        )
        tls = lib.certificate(phase, address)
        lib.write(phase / "nginx.conf", nginx(lib).encode())
        (phase / "nginx.conf").chmod(0o644)
        composition = lib.compose_profile(images, phase, address, tls_port, http_port, workers)
        plan = budget.pool_plan(role, workers, args.p_pool_size if role == "p" else 5,
                                args.p_max_overflow if role == "p" else 10)
        if role == "p":
            composition["services"]["api"]["environment"].update(
                T44_DB_POOL_SIZE=str(plan["api_pool_size"]),
                T44_DB_MAX_OVERFLOW=str(plan["api_max_overflow"]))
        lib.save(phase / "compose.json", composition)
        module_path = Path(__file__).resolve().parent / "mysql-budget.py"
        if sha(module_path) != BUDGET_SHA:
            raise ValueError("EXACT_V4_BUDGET_MODULE_REQUIRED")
        lib.write(phase / "mysql-budget.py", module_path.read_bytes())
        lib.write(phase / "factory.py", args.factory.read_bytes())
        lib.write(phase / "controller.py", Path(__file__).read_bytes())
        binding = {
            "kind": "isolated-cloud-campaign",
            "generation_kind": "exact-pinned-production-entry-generation-v4",
            "created_utc": lib.stamp(),
            "phase": role,
            "project": project,
            "database": database,
            "source_sha": SOURCE,
            "source_archive_sha256": manifest["source_archive_sha256"],
            "source_manifest_sha256": args.source_manifest_sha256,
            "upgrade_binding_sha256": args.upgrade_binding_sha256,
            "source_actual_proof_sha256": sha(
                args.output / "actual-source-files.json"
            ),
            "source_file_count": SOURCE_COUNT,
            "image_ids": {k: v["actual_id"] for k, v in proofs.items()},
            "config_ids": {k: v["config_id"] for k, v in proofs.items()},
            "images": images,
            "cryptographic_transport_proofs": proofs,
            "web_component": {
                "source_sha": OLD_SOURCE,
                "reused_original_tag": images["web"]["alias"],
                "target_frontend_frozen_equal_file_set_sha256": upgrade[
                    "frozen_file_set_sha256"
                ],
                "relabelled_to_target": False,
            },
            "app_private_ip": address,
            "tls_port": tls_port,
            "api_workers": workers,
            "v4_pool_plan": plan,
            "entrypoint": "t44.api:app",
            "profiling": False,
            "mysql_max_connections_configured_prior": 384 if role == "p" else 128,
            "mysql_capacity_is_actual_observation": False,
            "stop_utc": args.stop_utc,
            "timer_unit": project + "-stop.timer",
            "service_unit": project + "-stop.service",
            "tls": tls,
            "file_hashes": {
                n: sha(phase / n)
                for n in [
                    "compose.json",
                    "mysql-budget.py",
                    "application.env",
                    "controller.py",
                    "factory.py",
                    "nginx.conf",
                ]
            },
            "services_started": False,
            "initial_scheduler_pending_exact_scope": True,
            "synthetic_accounts_or_data_seeded": False,
        }
        lib.save(phase / "binding.json", binding)
        phases[role] = {
            "phase_dir": str(phase),
            "binding_sha256": sha(phase / "binding.json"),
            "project": project,
            "database": database,
            "api_workers": workers,
            "v4_pool_plan": plan,
            "ca_path": str(phase / "tls/ca.pem"),
            "ca_sha256": tls["ca_sha256"],
            "tls_port": tls_port,
            "stop_utc": args.stop_utc,
        }
    return {
        "success": True,
        "source_sha": SOURCE,
        "source_files_verified": True,
        "phases": phases,
        "services_started": False,
    }


def phase_binding(phase, expected, stopping=False):
    if not isinstance(expected, str) or not re.fullmatch(r"[0-9a-f]{64}", expected):
        raise ValueError("EXPLICIT_FROZEN_PHASE_BINDING_SHA_REQUIRED")
    lib = load(phase / "factory.py", FACTORY_SHA, "fixed_phase_factory")
    value = lib.binding(phase, stopping=stopping, expected=expected)
    if (
        value["generation_kind"] != "exact-pinned-production-entry-generation-v4"
        or value["source_sha"] != SOURCE
        or value["entrypoint"] != "t44.api:app"
        or value["profiling"] is not False
        or lib.expiry(value["stop_utc"]) > lib.expiry(HARDSTOP)
    ):
        raise ValueError("EXACT_PRODUCTION_F4_GENERATION_REQUIRED")
    return lib, value


def logged(lib, phase, argv, label, timeout=180):
    from subprocess import CalledProcessError

    env = {
        k: v
        for k, v in os.environ.items()
        if not k.startswith(("DOCKER_", "COMPOSE_", "T44_", "MYSQL_", "RABBITMQ_"))
    }
    import subprocess

    r = subprocess.run(
        list(map(str, argv)), capture_output=True, check=False, timeout=timeout, env=env
    )
    lib.save(
        phase / "receipts" / (label + "-" + uuid4().hex + ".json"),
        {
            "utc": lib.stamp(),
            "returncode": r.returncode,
            "stdout": r.stdout.decode(errors="replace"),
            "stderr": r.stderr.decode(errors="replace"),
        },
    )
    if r.returncode:
        raise CalledProcessError(r.returncode, argv, r.stdout, r.stderr)
    return r.stdout


def live(lib, value, role):
    ids = (
        lib.command(
            [
                *DOCKER,
                "ps",
                "--all",
                "--quiet",
                "--no-trunc",
                "--filter",
                "label=com.docker.compose.project=" + value["project"],
                "--filter",
                "label=com.docker.compose.service=" + role,
            ]
        )
        .decode()
        .split()
    )
    if not ids:
        return {"role": role, "absent": True}
    if len(ids) != 1 or not re.fullmatch(r"[0-9a-f]{64}", ids[0]):
        raise ValueError("ONE_EXACT_OWNED_ROLE_CONTAINER_REQUIRED")
    raw = lib.command(
        [
            *DOCKER,
            "inspect",
            "--format",
            "{{json .Id}}\t{{json .Image}}\t{{json .State}}\t{{json .RestartCount}}",
            ids[0],
        ]
    ).decode()
    row = json.loads("[" + raw.replace("\t", ",") + "]")
    mapped = {
        "tls-gateway": "nginx",
        "web": "web",
        "mysql": "mysql",
        "rabbitmq": "rabbitmq",
    }.get(role, "backend")
    if row[0] != ids[0] or row[1] not in {
        value["image_ids"][mapped],
        value["config_ids"][mapped],
    }:
        raise ValueError("OWNED_ROLE_IMAGE_IDENTITY_MISMATCH")
    return {
        "role": role,
        "container_id": row[0],
        "image_id": row[1],
        "state": row[2],
        "restart_count": row[3],
    }


def https(lib, phase, value):
    import http.client
    import ssl

    ca = phase / "tls/ca.pem"
    if sha(ca) != value["tls"]["ca_sha256"]:
        raise ValueError("FROZEN_CA_CHANGED")
    ctx = ssl.create_default_context(cafile=str(ca))
    for attempt in range(1, 16):
        c = http.client.HTTPSConnection(
            value["app_private_ip"], value["tls_port"], context=ctx, timeout=5
        )
        row = {"utc": lib.stamp(), "attempt": attempt, "credentials_sent": False}
        try:
            c.request(
                "GET",
                "/api/v1/projects",
                headers={"Accept": "application/json", "Connection": "close"},
            )
            response = c.getresponse()
            body = response.read(1024 * 1024 + 1)
            row.update(
                status=response.status,
                strict_CA_and_IP_verified=True,
                body=body[: 1024 * 1024].decode(errors="replace"),
                truncated=len(body) > 1024 * 1024,
            )
        except (OSError, http.client.HTTPException) as error:
            row.update(
                error_class=type(error).__name__,
                error=str(error),
                strict_CA_and_IP_verified=False,
            )
        finally:
            c.close()
        lib.save(phase / "receipts" / ("https-" + uuid4().hex + ".json"), row)
        if row.get("status") == 401 and not row.get("truncated"):
            return {
                "status": 401,
                "strict_CA_and_IP_verified": True,
                "attempts": attempt,
            }
        time.sleep(1)
    raise ValueError("ACTUAL_HOST_STRICT_TLS_401_NOT_PROVEN")


def _operate_without_mutex(args):
    lib, value = phase_binding(
        args.phase_dir, args.binding_sha256, args.action == "stop"
    )
    phase = args.phase_dir
    if args.action == "arm":
        valid_window(lib, value["stop_utc"], 60)
        return lib.arm(phase, value)
    if args.action == "stop":
        return lib.stop(phase, value)
    if args.action == "status":
        return lib.receipt(
            phase,
            "status",
            success=True,
            resources=[live(lib, value, r) for r in lib.PERSISTENT],
        )
    valid_window(lib, value["stop_utc"], 600)
    lib.command(["systemctl", "is-active", "--quiet", value["timer_unit"]])
    for role, image in value["images"].items():
        actual = (
            lib.command(
                [*DOCKER, "image", "inspect", "--format", "{{.Id}}", image["alias"]]
            )
            .decode()
            .strip()
        )
        if actual not in {value["image_ids"][role], value["config_ids"][role]}:
            raise ValueError("BOUND_IMAGE_ALIAS_CHANGED")
    argv = [
        *DOCKER,
        "compose",
        "--env-file",
        phase / "application.env",
        "--file",
        phase / "compose.json",
        "--project-name",
        value["project"],
    ]
    host = None
    if args.action == "config":
        lib.command([*argv, "config", "--quiet"])
    elif args.action == "infra":
        logged(
            lib,
            phase,
            [
                *argv,
                "up",
                "-d",
                "--wait",
                "--no-build",
                "--pull",
                "never",
                "mysql",
                "rabbitmq",
            ],
            "infra",
            300,
        )
    elif args.action == "migrate":
        if args.database != value["database"]:
            raise ValueError("EXPLICIT_NEW_SCHEMA_ONLY")
        logged(
            lib,
            phase,
            [
                *argv,
                "--profile",
                "operations",
                "run",
                "--rm",
                "--no-deps",
                "-T",
                "migrate",
            ],
            "migrate",
        )
    elif args.action == "idle":
        logged(
            lib,
            phase,
            [
                *argv,
                "up",
                "-d",
                "--wait",
                "--no-build",
                "--pull",
                "never",
                "api",
                "consumer",
                "web",
            ],
            "api-consumer-web",
        )
        logged(
            lib,
            phase,
            [*argv, "run", "--rm", "--no-deps", "-T", "tls-gateway", "-t"],
            "nginx-t",
            60,
        )
        logged(
            lib,
            phase,
            [
                *argv,
                "up",
                "-d",
                "--no-deps",
                "--no-build",
                "--pull",
                "never",
                "tls-gateway",
            ],
            "tls",
        )
        host = https(lib, phase, value)
    elif args.action in {"scheduler-token", "scheduler-rotate"}:
        if not args.project_id or any(
            type(n) is not int or not 1 <= n <= 4294967295 for n in args.project_id
        ):
            raise ValueError("ACTUAL_POSITIVE_PROJECT_IDS_REQUIRED")
        if args.action == "scheduler-rotate":
            live(lib, value, "scheduler")
            logged(
                lib,
                phase,
                [*argv, "stop", "--timeout", "30", "scheduler"],
                "scheduler-stop",
                60,
            )
        scope = [
            a for p in sorted(set(args.project_id)) for a in ["--project-id", str(p)]
        ]
        logged(
            lib,
            phase,
            [
                *argv,
                "--profile",
                "operations",
                "run",
                "--rm",
                "--no-deps",
                "-T",
                "credential-admin",
                *scope,
                *(["--rotate"] if args.action == "scheduler-rotate" else []),
            ],
            args.action,
        )
    elif args.action == "scheduler-start":
        token = phase / "scheduler-secrets/scheduler-token.json"
        s = token.lstat()
        if (
            token.resolve() != token
            or not stat.S_ISREG(s.st_mode)
            or s.st_uid != 10001
            or s.st_mode & 0o777 != 0o600
        ):
            raise ValueError("ROOT_SCOPED_PRIVATE_CREDENTIAL_REQUIRED")
        metadata = json.loads(token.read_text())
        expires = datetime.fromisoformat(metadata["expires_at"].replace("Z", "+00:00"))  # noqa: FURB162 - Ubuntu22 Python3.10
        if expires.tzinfo is None or expires.timestamp() <= time.time() + 60:
            raise ValueError("FRESH_SCOPED_CREDENTIAL_REQUIRED")
        logged(
            lib,
            phase,
            [*argv, "up", "-d", "--wait", "--no-build", "--pull", "never", "scheduler"],
            "scheduler-start",
            120,
        )
    elif args.action == "scheduler-stop":
        live(lib, value, "scheduler")
        logged(
            lib,
            phase,
            [*argv, "stop", "--timeout", "30", "scheduler"],
            "scheduler-stop",
            60,
        )
    resources = [live(lib, value, r) for r in lib.PERSISTENT]
    capacity_environment = []
    if args.action in {"migrate", "idle", "scheduler-token", "scheduler-rotate", "scheduler-start"}:
        capacity_environment = budget_module(phase).verify_runtime_environment(
            value, lambda role: live(lib, value, role))
    startup = {
        "infra": {"mysql", "rabbitmq"},
        "idle": {"api", "consumer", "web", "tls-gateway"},
        "scheduler-start": {"scheduler"},
    }.get(args.action, set())
    clean = all(
        not r.get("absent")
        and r.get("state", {}).get("Running") is True
        and r.get("restart_count") == 0
        for r in resources
        if r["role"] in startup
    )
    if not clean:
        lib.receipt(
            phase,
            args.action,
            success=False,
            resources=resources,
            actual_startup_restart_or_state_failure=True,
        )
        raise ValueError("INITIAL_STARTUP_RESTART_OR_ROLE_STATE_FAILED")
    return lib.receipt(
        phase,
        args.action,
        success=True,
        source_sha=SOURCE,
        resources=resources,
        host_https=host,
        capacity_environment_projection=capacity_environment,
        restarts_observed={
            r["role"]: r["restart_count"] for r in resources if r.get("restart_count")
        },
        performance_or_business_verdict=None,
    )



def operate(args):
    # Stop/status never need an actual-budget receipt or wait behind an operations lock.
    if args.action in {"stop", "status"}:
        return _operate_without_mutex(args)
    lib, value = phase_binding(args.phase_dir, args.binding_sha256)
    budget = budget_module(args.phase_dir)
    valid_window(lib, value["stop_utc"], 600)
    if args.action == "observe-mysql":
        lib.command(["systemctl", "is-active", "--quiet", value["timer_unit"]])
        return budget.observe(args.phase_dir, args.binding_sha256, value,
                              lambda role: live(lib, value, role), args)
    with budget.operation_lock(args.phase_dir, args.binding_sha256):
        if args.action == "probe-budget":
            lib.command(["systemctl", "is-active", "--quiet", value["timer_unit"]])
            return budget.probe(args.phase_dir, args.binding_sha256, value,
                                lambda role: live(lib, value, role))
        if args.action in {"migrate", "idle", "scheduler-token", "scheduler-rotate", "scheduler-start"}:
            budget.verify_runtime_environment(value, lambda role: live(lib, value, role))
            budget.admit(args.phase_dir, args.binding_sha256, value,
                         lambda role: live(lib, value, role), args.budget_receipt,
                         args.budget_receipt_sha256)
        return _operate_without_mutex(args)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "action",
        choices=[
            "prepare",
            "probe-budget",
            "observe-mysql",
            "arm",
            "config",
            "infra",
            "migrate",
            "idle",
            "scheduler-token",
            "scheduler-rotate",
            "scheduler-start",
            "scheduler-stop",
            "status",
            "stop",
        ],
    )
    for name in [
        "factory",
        "upgrade-binding",
        "source-package",
        "original-proof",
        "image-proof",
        "output",
        "phase-dir",
    ]:
        p.add_argument("--" + name, type=Path)
    for name in [
        "upgrade-binding-sha256",
        "source-manifest-sha256",
        "run-id",
        "app-ip",
        "stop-utc",
        "binding-sha256",
        "database",
    ]:
        p.add_argument("--" + name)
    for name in ["f-tls-port", "f-http-port", "p-tls-port", "p-http-port"]:
        p.add_argument("--" + name, type=int)
    p.add_argument("--p-workers", type=int, default=7)
    p.add_argument("--project-id", type=int, action="append")
    p.add_argument("--p-pool-size", type=int)
    p.add_argument("--p-max-overflow", type=int)
    p.add_argument("--budget-receipt", type=Path)
    p.add_argument("--budget-receipt-sha256")
    p.add_argument("--until-utc")
    p.add_argument("--interval-seconds", type=int, default=5)
    args = p.parse_args()
    os.umask(0o077)
    try:
        print(json.dumps(prepare(args) if args.action == "prepare" else operate(args)))
    except Exception as error:  # noqa: BLE001 - preserve private failure, no credentials on stdout
        location = args.output if args.action == "prepare" else args.phase_dir
        failure = None
        if location and location.is_dir():
            failure = location / ("failure-" + uuid4().hex + ".json")
            data = {
                "error_class": type(error).__name__,
                "reason": str(error),
                "partial_state_preserved": True,
            }
            if hasattr(error, "stdout"):
                data.update(
                    stdout=(error.stdout or b"").decode(errors="replace"),
                    stderr=(error.stderr or b"").decode(errors="replace"),
                )
            fd = os.open(
                failure, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600
            )
            with os.fdopen(fd, "w") as f:
                json.dump(data, f)
        print(
            json.dumps(
                {
                    "success": False,
                    "error": "F4_GENERATION_REFUSED",
                    "private_failure_path": str(failure) if failure else None,
                }
            )
        )
        raise SystemExit(1) from None
