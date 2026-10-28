"""Prepare isolated F/P Compose, strict private TLS and persistent owned stop; never cloud lifecycle."""

import argparse
import copy
import hashlib
import importlib.util
import ipaddress
import json
import os
import platform
import re
import secrets
import socket
import stat
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

HELPER_SHA = "0a1c2cd5bf57717ba5218ff6bb5086d6acbb60ff54713940a6da73f495a1cfcd"
PROOF_SHA = "47b50d0111737d2b4ff7b47ce37c46bc5d7fc208d2f3933088b8a08dab326fc0"
PERSISTENT = ("mysql", "rabbitmq", "api", "consumer", "scheduler", "web", "tls-gateway")
DOCKER = ["docker", "--context", "default"]
LOGGING = {"driver": "json-file", "options": {"max-size": "10m", "max-file": "3"}}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, data):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "wb") as stream:
        stream.write(data)


def save(path, value):
    write(path, (json.dumps(value, indent=2) + "\n").encode())


def stamp():
    return datetime.now(timezone.utc).isoformat()  # noqa: UP017 - Ubuntu22 Python3.10


def command(argv, cap=120, data=None):
    env = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith(("MYSQL_", "RABBITMQ_", "COMPOSE_", "T44_", "DOCKER_"))
    }
    return subprocess.run(
        list(map(str, argv)),
        input=data,
        capture_output=True,
        check=True,
        timeout=cap,
        env=env,
    ).stdout


def private(path, directory=False):
    info = path.lstat()
    if (
        path.resolve() != path
        or info.st_uid != os.geteuid()
        or stat.S_IMODE(info.st_mode) != (0o700 if directory else 0o600)
        or not (stat.S_ISDIR(info.st_mode) if directory else stat.S_ISREG(info.st_mode))
    ):
        raise ValueError("PRIVATE_OWNED_CANONICAL_OBJECT_REQUIRED")


def expiry(value):
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", value):
        raise ValueError("EXACT_UTC_REQUIRED")
    return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()  # noqa: FURB162 - Python3.10


def private_ipv4(value):
    address = ipaddress.IPv4Address(value)
    if not any(
        address in ipaddress.IPv4Network(net)
        for net in ["10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"]
    ):
        raise ValueError("EXPLICIT_PRIVATE_APP_IPV4_REQUIRED")
    return str(address)


def bind_free(ip, port):
    with socket.socket() as connection:
        connection.bind((ip, port))


def nginx():
    return """worker_processes auto;
pid /tmp/nginx.pid;
error_log /dev/stderr crit;
events { worker_connections 2048; }
http {
  log_format minimal escape=json '{"request_id":"$request_id","status":$status,"request_time":$request_time,"upstream_time":"$upstream_response_time"}';
  access_log /dev/stdout minimal;
  client_body_temp_path /tmp/client_temp;
  proxy_temp_path /tmp/proxy_temp;
  upstream t44_web { server web:8080; keepalive 64; }
  server {
    listen 8443 ssl;
    ssl_certificate /run/t44-tls/server.pem;
    ssl_certificate_key /run/t44-tls/server.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    server_tokens off;
    client_max_body_size 2m;
    error_page 413 = @payload_too_large;
    location @payload_too_large {
      default_type application/json;
      return 413 '{"code":"PAYLOAD_TOO_LARGE","message":"Request body exceeds the proxy limit","request_id":"$request_id","audit_id":null,"current_version":null,"current_state":null,"original_error_code":null,"violations":[]}';
    }
    location / {
      proxy_http_version 1.1;
      proxy_set_header Connection "";
      proxy_set_header Host $host;
      proxy_set_header X-Forwarded-For $remote_addr;
      proxy_set_header X-Forwarded-Proto https;
      proxy_set_header X-Request-ID $request_id;
      proxy_pass http://t44_web;
    }
  }
}
"""


def compose_profile(images, phase, address, tls_port, http_port, workers):
    """Six persistent product services plus explicitly seventh TLS; operations profiles are one-off."""
    def image(role):
        return images[role]["alias"]
    env = {
        "PYTHONPATH": "/app/backend",
        "DATABASE_URL": "mysql+pymysql://${MYSQL_USER}:${MYSQL_PASSWORD}@mysql:3306/${MYSQL_DATABASE}",
        "T44_DATABASE": "${MYSQL_DATABASE}",
        "AMQP_URL": "amqp://${RABBITMQ_DEFAULT_USER}:${RABBITMQ_DEFAULT_PASS}@rabbitmq:5672/${RABBITMQ_DEFAULT_VHOST}",
        "T44_SESSION_TTL_SECONDS": "3600",
    }
    app = {
        "image": image("backend"),
        "pull_policy": "never",
        "init": True,
        "restart": "unless-stopped",
        "read_only": True,
        "tmpfs": ["/tmp"],
        "cap_drop": ["ALL"],
        "security_opt": ["no-new-privileges:true"],
        "stop_grace_period": "30s",
        "networks": ["data"],
        "environment": env,
        "logging": LOGGING,
    }
    dependency = {"mysql": {"condition": "service_healthy"}}
    services = {}
    for name, argv in [
        (
            "api",
            [
                "python",
                "-m",
                "uvicorn",
                "t44.api:app",
                "--host",
                "0.0.0.0",
                "--port",
                "8000",
                "--workers",
                str(workers),
                "--no-access-log",
                "--no-proxy-headers",
            ],
        ),
        ("consumer", ["python", "-m", "t44.messaging"]),
        ("scheduler", ["python", "-m", "t44.scheduling"]),
    ]:
        services[name] = copy.deepcopy(app)
        services[name].update(
            command=argv,
            depends_on=copy.deepcopy(dependency),
            mem_limit=("10g" if workers >= 7 else "2g") if name == "api" else "1g",
        )
        services[name]["healthcheck"] = {
            "test": ["CMD", "python", "/app/deployment/runtime_probe.py", name],
            "interval": "20s",
            "timeout": "8s",
            "retries": 3,
            "start_period": "30s",
        }
    services["api"]["networks"] = ["data", "application"]
    services["consumer"]["depends_on"]["rabbitmq"] = {"condition": "service_healthy"}
    services["scheduler"]["environment"].update(
        T44_SCHEDULER_TOKEN_FILE="/run/t44-secrets/scheduler-token.json",
        T44_SCHEDULER_LOCK_FILE="/var/lib/t44-scheduler/scan.lock",
    )
    services["scheduler"]["volumes"] = [
        str(phase / "scheduler-secrets") + ":/run/t44-secrets:ro",
        str(phase / "scheduler-locks") + ":/var/lib/t44-scheduler",
    ]
    services["mysql"] = {
        "image": image("mysql"),
        "pull_policy": "never",
        "restart": "unless-stopped",
        "mem_limit": "12g" if workers >= 7 else "2g",
        "environment": {
            name: "${" + name + "}"
            for name in [
                "MYSQL_DATABASE",
                "MYSQL_USER",
                "MYSQL_PASSWORD",
                "MYSQL_ROOT_PASSWORD",
            ]
        },
        "command": [
            "--character-set-server=utf8mb4",
            "--collation-server=utf8mb4_0900_ai_ci",
            "--max-connections=" + str(384 if workers >= 7 else 128),
            "--innodb-buffer-pool-size=" + ("8G" if workers >= 7 else "512M"),
        ],
        "volumes": ["mysql_data:/var/lib/mysql"],
        "networks": ["data"],
        "logging": LOGGING,
        "healthcheck": {
            "test": [
                "CMD-SHELL",
                'MYSQL_PWD="$$MYSQL_ROOT_PASSWORD" mysql --user=root --database="$$MYSQL_DATABASE" --execute="SELECT 1" --silent >/dev/null',
            ],
            "interval": "10s",
            "timeout": "5s",
            "retries": 18,
            "start_period": "40s",
        },
    }
    services["rabbitmq"] = {
        "image": image("rabbitmq"),
        "pull_policy": "never",
        "hostname": "rabbitmq",
        "restart": "unless-stopped",
        "mem_limit": "2g",
        "environment": {
            name: "${" + name + "}"
            for name in [
                "RABBITMQ_DEFAULT_USER",
                "RABBITMQ_DEFAULT_PASS",
                "RABBITMQ_DEFAULT_VHOST",
            ]
        },
        "volumes": ["rabbitmq_data:/var/lib/rabbitmq"],
        "networks": ["data"],
        "logging": LOGGING,
        "healthcheck": {
            "test": ["CMD", "rabbitmq-diagnostics", "-q", "ping"],
            "interval": "10s",
            "timeout": "5s",
            "retries": 18,
            "start_period": "30s",
        },
    }
    services["web"] = {
        "image": image("web"),
        "pull_policy": "never",
        "restart": "unless-stopped",
        "read_only": True,
        "tmpfs": ["/tmp"],
        "cap_drop": ["ALL"],
        "security_opt": ["no-new-privileges:true"],
        "mem_limit": "256m",
        "ports": [f"127.0.0.1:{http_port}:8080"],
        "networks": ["edge", "application"],
        "logging": LOGGING,
        "depends_on": {"api": {"condition": "service_healthy"}},
    }
    services["tls-gateway"] = {
        "image": image("nginx"),
        "pull_policy": "never",
        "user": "101:101",
        "restart": "unless-stopped",
        "read_only": True,
        "entrypoint": ["nginx"],
        "command": ["-g", "daemon off;"],
        "tmpfs": ["/tmp"],
        "cap_drop": ["ALL"],
        "security_opt": ["no-new-privileges:true"],
        "mem_limit": "256m",
        "ports": [f"{address}:{tls_port}:8443"],
        "networks": ["edge", "application"],
        "logging": LOGGING,
        "volumes": [
            str(phase / "nginx.conf") + ":/etc/nginx/nginx.conf:ro",
            str(phase / "tls/server") + ":/run/t44-tls:ro",
        ],
        "depends_on": {"web": {"condition": "service_started"}},
    }
    for name, entry, argv in [
        (
            "migrate",
            ["python", "-m", "t44.cli"],
            ["migrate", "--database", "${MYSQL_DATABASE}"],
        ),
        ("admin", ["python", "-m", "t44.cli"], ["--help"]),
        (
            "credential-admin",
            ["python", "/app/deployment/credential_admin.py"],
            ["--help"],
        ),
    ]:
        services[name] = copy.deepcopy(app)
        services[name].update(
            profiles=["operations"],
            restart="no",
            entrypoint=entry,
            command=argv,
            depends_on=copy.deepcopy(dependency),
        )
    services["credential-admin"]["volumes"] = [
        str(phase / "scheduler-secrets") + ":/run/t44-secrets"
    ]
    return {
        "services": services,
        "networks": {
            "data": {"internal": True},
            "application": {"internal": True},
            "edge": {},
        },
        "volumes": {"mysql_data": {}, "rabbitmq_data": {}},
    }


def certificate(phase, address):
    tls = phase / "tls"
    tls.mkdir(mode=0o700)
    server = tls / "server"
    server.mkdir(mode=0o700)
    command(
        [
            "openssl",
            "req",
            "-x509",
            "-newkey",
            "rsa:2048",
            "-nodes",
            "-days",
            "2",
            "-keyout",
            tls / "ca.key",
            "-out",
            tls / "ca.pem",
            "-subj",
            "/CN=T44 private campaign CA",
            "-addext",
            "basicConstraints=critical,CA:TRUE",
            "-addext",
            "keyUsage=critical,keyCertSign,cRLSign",
        ],
        cap=30,
    )
    command(
        [
            "openssl",
            "req",
            "-new",
            "-newkey",
            "rsa:2048",
            "-nodes",
            "-keyout",
            server / "server.key",
            "-out",
            tls / "server.csr",
            "-subj",
            "/CN=T44 private application",
        ],
        cap=30,
    )
    write(
        tls / "server.ext",
        (
            "basicConstraints=critical,CA:FALSE\nkeyUsage=critical,digitalSignature,keyEncipherment\nextendedKeyUsage=serverAuth\nsubjectAltName=IP:"
            + address
            + "\n"
        ).encode(),
    )
    command(
        [
            "openssl",
            "x509",
            "-req",
            "-in",
            tls / "server.csr",
            "-CA",
            tls / "ca.pem",
            "-CAkey",
            tls / "ca.key",
            "-CAcreateserial",
            "-days",
            "2",
            "-out",
            server / "server.pem",
            "-extfile",
            tls / "server.ext",
        ],
        cap=30,
    )
    command(
        [
            "openssl",
            "verify",
            "-CAfile",
            tls / "ca.pem",
            "-verify_ip",
            address,
            "-purpose",
            "sslserver",
            server / "server.pem",
        ]
    )
    os.chown(server, 101, 101)
    for path in server.iterdir():
        path.chmod(0o600)
        os.chown(path, 101, 101)
    return {
        "ca_sha256": sha(tls / "ca.pem"),
        "server_certificate_sha256": sha(server / "server.pem"),
        "CA_private_key_mounted": False,
    }


def prepare(args):
    if (
        os.geteuid() != 0
        or not re.fullmatch(r"[a-z][a-z0-9]{5,15}", args.run_id)
        or args.p_workers not in {7, 16}
    ):
        raise ValueError("ROOT_FRESH_RUNID_AND_EXPLICIT_P_WORKERS7_OR16_REQUIRED")
    if platform.system() != "Linux" or platform.machine() not in {"x86_64", "amd64"}:
        raise ValueError("DESIGNATED_LINUX_AMD64_APP_HOST_REQUIRED")
    deadline = expiry(args.stop_utc)
    if not 600 <= deadline - time.time() <= 43200:
        raise ValueError("TEN_MINUTE_TO_TWELVE_HOUR_WORKLOAD_WINDOW_REQUIRED")
    address = private_ipv4(args.app_ip)
    if (
        not args.output.is_absolute()
        or args.output.parent.resolve() != args.output.parent
    ):
        raise ValueError("FRESH_CANONICAL_PRIVATE_OUTPUT_REQUIRED")
    private(args.bundle_helper)
    if sha(args.bundle_helper) != HELPER_SHA:
        raise ValueError("EXACT_APPROVED_BUNDLE_HELPER_REQUIRED")
    spec = importlib.util.spec_from_file_location("approved_bundle", args.bundle_helper)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    manifest = module.verify(args.bundle, args.manifest_sha256)
    private(args.image_proof)
    if sha(args.image_proof) != PROOF_SHA:
        raise ValueError("EXACT_CRYPTOGRAPHIC_TRANSPORT_PROOF_REQUIRED")
    spec = importlib.util.spec_from_file_location(
        "reviewed_archive_proof", args.image_proof
    )
    proof_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(proof_module)
    graph = proof_module.scan_archive(args.bundle / "images.tar.gz")
    identity_proofs = {
        role: proof_module.prove_role(
            graph, role, row, manifest, proof_module.actual_image(row["alias"])
        )
        for role, row in manifest["images"].items()
    }
    ports = [("f", 18443, 18080, 4), ("p", 18445, 18081, args.p_workers)]
    for _, tls_port, http_port, _ in ports:
        bind_free(address, tls_port)
        bind_free("127.0.0.1", http_port)
    private(args.output.parent, True)
    if not re.fullmatch(r"/[A-Za-z0-9_./-]+", str(args.output)):
        raise ValueError("SYSTEMD_SAFE_CANONICAL_OUTPUT_PATH_REQUIRED")
    args.output.mkdir(mode=0o700)
    phases = {}
    for role, tls_port, http_port, workers in ports:
        project = "t44-cloud-" + args.run_id + "-" + role
        database = "t44c_" + args.run_id + "_" + role
        if command(
            [
                *DOCKER,
                "volume",
                "ls",
                "--quiet",
                "--filter",
                "label=com.docker.compose.project=" + project,
            ]
        ).strip():
            raise ValueError("EXISTING_PROJECT_DATA_REFUSE_REUSE_OR_RESET")
        phase = args.output / role
        phase.mkdir(mode=0o700)
        (phase / "receipts").mkdir(mode=0o700)
        for name in ["scheduler-secrets", "scheduler-locks"]:
            path = phase / name
            path.mkdir(mode=0o700)
            os.chown(path, 10001, 10001)
        values = {
            "COMPOSE_PROJECT_NAME": project,
            "MYSQL_DATABASE": database,
            "MYSQL_USER": database + "_app",
            "MYSQL_PASSWORD": secrets.token_hex(32),
            "MYSQL_ROOT_PASSWORD": secrets.token_hex(32),
            "RABBITMQ_DEFAULT_USER": "t44",
            "RABBITMQ_DEFAULT_PASS": secrets.token_hex(32),
            "RABBITMQ_DEFAULT_VHOST": project,
        }
        write(
            phase / "application.env",
            "".join(key + "=" + value + "\n" for key, value in values.items()).encode(),
        )
        tls = certificate(phase, address)
        write(phase / "nginx.conf", nginx().encode())
        (phase / "nginx.conf").chmod(0o644)
        save(
            phase / "compose.json",
            compose_profile(
                manifest["images"], phase, address, tls_port, http_port, workers
            ),
        )
        write(phase / "controller.py", Path(__file__).read_bytes())
        binding = {
            "kind": "isolated-cloud-campaign",
            "created_utc": stamp(),
            "phase": role,
            "project": project,
            "database": database,
            "source_sha": manifest["source_sha"],
            "source_archive_sha256": manifest["source_archive_sha256"],
            "image_bundle_manifest_sha256": args.manifest_sha256,
            "image_ids": {
                name: row["actual_id"] for name, row in identity_proofs.items()
            },
            "config_ids": {
                name: row["config_id"] for name, row in identity_proofs.items()
            },
            "cryptographic_transport_proofs": identity_proofs,
            "app_private_ip": address,
            "tls_port": tls_port,
            "api_workers": workers,
            "mysql_max_connections": 384 if role == "p" else 128,
            "connection_model_upper_bound_with_two_operations": 15 * (workers + 4),
            "connection_model_assumption": "one engine5+10 per API worker/consumer/scheduler; two operations; runtime peak must be observed",
            "stop_utc": args.stop_utc,
            "timer_unit": project + "-stop.timer",
            "service_unit": project + "-stop.service",
            "tls": tls,
            "file_hashes": {
                name: sha(phase / name)
                for name in [
                    "compose.json",
                    "application.env",
                    "controller.py",
                    "nginx.conf",
                ]
            },
            "services_started": False,
            "initial_scheduler_pending_exact_scope": True,
            "synthetic_data_or_accounts_seeded": False,
        }
        save(phase / "binding.json", binding)
        phases[role] = {
            "phase_dir": str(phase),
            "project": project,
            "database": database,
            "api_workers": workers,
            "binding_sha256": sha(phase / "binding.json"),
            "ca_path": str(phase / "tls/ca.pem"),
            "ca_sha256": tls["ca_sha256"],
            "stop_utc": args.stop_utc,
        }
    return {
        "success": True,
        "source_sha": manifest["source_sha"],
        "phases": phases,
        "services_started": False,
        "data_or_accounts_seeded": False,
    }


def binding(phase, stopping=False, expected=None):
    private(phase, True)
    private(phase / "binding.json")
    if expected is not None and sha(phase / "binding.json") != expected:
        raise ValueError("FROZEN_STOP_BINDING_CHANGED")
    value = json.loads((phase / "binding.json").read_text())
    if value["kind"] != "isolated-cloud-campaign" or not re.fullmatch(
        r"t44-cloud-[a-z][a-z0-9]{5,15}-[fp]", value["project"]
    ):
        raise ValueError("EXACT_OWNED_PHASE_REQUIRED")
    for name, file_hash in value["file_hashes"].items():
        if stopping and name != "controller.py":
            continue
        if sha(phase / name) != file_hash:
            raise ValueError("OWNED_CONFIG_OR_CONTROLLER_CHANGED")
    return value


def receipt(phase, action, **fields):
    value = {"utc": stamp(), "receipt_id": uuid4().hex, "action": action, **fields}
    save(phase / "receipts" / (value["receipt_id"] + ".json"), value)
    return value


def arm(phase, value):
    if expiry(value["stop_utc"]) <= time.time() + 60:
        raise ValueError("NEW_WORKLOAD_TIMER_MUST_BE_FUTURE")
    service = (
        "[Unit]\nDescription=T44 exact owned campaign stop\n[Service]\nType=oneshot\nTimeoutStartSec=180\nExecStart=/usr/bin/python3 "
        + str(phase / "controller.py")
        + " stop --phase-dir "
        + str(phase)
        + " --binding-sha256 "
        + sha(phase / "binding.json")
        + "\n"
    )
    timer = (
        "[Unit]\nDescription=T44 bounded campaign expiry\n[Timer]\nOnCalendar="
        + value["stop_utc"].replace("T", " ").replace("Z", " UTC")
        + "\nPersistent=true\nAccuracySec=1s\nRandomizedDelaySec=0\n[Install]\nWantedBy=timers.target\n"
    )
    for name, text in [(value["service_unit"], service), (value["timer_unit"], timer)]:
        path = Path("/etc/systemd/system") / name
        write(path, text.encode())
        path.chmod(0o644)
    command(["systemctl", "daemon-reload"])
    command(["systemctl", "enable", "--now", value["timer_unit"]])
    command(["systemctl", "is-active", "--quiet", value["timer_unit"]])
    return receipt(
        phase,
        "persistent_timer_armed",
        success=True,
        timer=value["timer_unit"],
        stop_utc=value["stop_utc"],
        cloud_lifecycle_changed=False,
    )


def stop(phase, value):
    ids = (
        command(
            [
                *DOCKER,
                "ps",
                "--all",
                "--quiet",
                "--no-trunc",
                "--filter",
                "label=com.docker.compose.project=" + value["project"],
            ]
        )
        .decode()
        .split()
    )
    approved, unexpected = [], []
    roles = {
        "mysql": "mysql",
        "rabbitmq": "rabbitmq",
        "web": "web",
        "tls-gateway": "nginx",
        **{
            name: "backend"
            for name in [
                "api",
                "consumer",
                "scheduler",
                "migrate",
                "admin",
                "credential-admin",
            ]
        },
    }
    for container in ids:
        if not re.fullmatch(r"[0-9a-f]{64}", container):
            raise ValueError("EXACT_CONTAINER_ID_REQUIRED")
        raw = (
            command(
                [
                    *DOCKER,
                    "inspect",
                    "--format",
                    '{{json .Id}}\t{{json (index .Config.Labels "com.docker.compose.project")}}\t{{json (index .Config.Labels "com.docker.compose.service")}}\t{{json .Image}}\t{{json .State.Running}}',
                    container,
                ]
            )
            .decode()
            .strip()
        )
        ident, project, service, image, running = [
            json.loads(part) for part in raw.split("\t")
        ]
        if (
            ident != container
            or project != value["project"]
            or service not in roles
            or image
            not in {
                value["image_ids"][roles[service]],
                value["config_ids"][roles[service]],
            }
        ):
            unexpected.append(
                {"container_id": container, "recognized_owned_identity": False}
            )
        elif running:
            approved.append(container)
    if approved:
        command([*DOCKER, "stop", "--time", "30", *approved], cap=90)
    states = {
        container: command(
            [
                *DOCKER,
                "inspect",
                "--format",
                "{{json .State.Running}}\t{{json .State.ExitCode}}\t{{json .State.OOMKilled}}",
                container,
            ]
        )
        .decode()
        .strip()
        for container in approved
    }
    success = not unexpected and all(
        json.loads(row.split("\t")[0]) is False for row in states.values()
    )
    return receipt(
        phase,
        "owned_containers_stop",
        success=success,
        stopped_container_ids=approved,
        actual_final_state_running_exitcode_oom=states,
        unexpected_not_signaled=unexpected,
        engine_grace_seconds=30,
        force_status="not inferred from exit code; Docker may kill after grace",
        volumes_deleted=False,
        VM_stopped_or_released=False,
    )


def operate(args):
    phase = args.phase_dir
    value = binding(phase, stopping=args.action == "stop", expected=args.binding_sha256)
    if args.action == "arm":
        return arm(phase, value)
    if args.action == "stop":
        return stop(phase, value)
    if args.action == "status":
        return receipt(
            phase,
            "status",
            success=True,
            compose_ps=command(
                [
                    *DOCKER,
                    "compose",
                    "--env-file",
                    phase / "application.env",
                    "--file",
                    phase / "compose.json",
                    "--project-name",
                    value["project"],
                    "ps",
                    "--format",
                    "json",
                ]
            ).decode(),
        )
    if expiry(value["stop_utc"]) <= time.time() + 120:
        raise ValueError("WORKLOAD_WINDOW_CLOSED_NO_NEW_SPAWN")
    command(["systemctl", "is-active", "--quiet", value["timer_unit"]])
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
    if args.action == "config":
        command([*argv, "config", "--quiet"])
    elif args.action == "infra":
        command(
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
            cap=300,
        )
    elif args.action == "migrate":
        if args.database != value["database"]:
            raise ValueError("EXPLICIT_EXACT_NEW_DATABASE_REQUIRED")
        command(
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
            cap=180,
        )
    elif args.action == "idle":
        command(
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
                "tls-gateway",
            ],
            cap=180,
        )
    elif args.action == "scheduler-token":
        if not args.project_id or any(project <= 0 for project in args.project_id):
            raise ValueError("ACTUAL_PROJECT_IDS_REQUIRED_NO_WILDCARD")
        scopes = [
            part
            for project in args.project_id
            for part in ["--project-id", str(project)]
        ]
        command(
            [
                *argv,
                "--profile",
                "operations",
                "run",
                "--rm",
                "--no-deps",
                "-T",
                "credential-admin",
                *scopes,
            ]
        )
    elif args.action == "scheduler-start":
        if not (phase / "scheduler-secrets/scheduler-token.json").is_file():
            raise ValueError("ROOT_SCOPED_TOKEN_MUST_EXIST")
        command(
            [*argv, "up", "-d", "--wait", "--no-build", "--pull", "never", "scheduler"],
            cap=120,
        )
    return receipt(
        phase,
        args.action,
        success=True,
        source_sha=value["source_sha"],
        project=value["project"],
        database=value["database"],
        api_workers=value["api_workers"],
        test_or_performance_verdict=None,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "action",
        choices=(
            "prepare",
            "arm",
            "config",
            "infra",
            "migrate",
            "idle",
            "scheduler-token",
            "scheduler-start",
            "status",
            "stop",
        ),
    )
    parser.add_argument("--bundle", type=Path)
    parser.add_argument("--bundle-helper", type=Path)
    parser.add_argument("--image-proof", type=Path)
    parser.add_argument("--manifest-sha256")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--run-id")
    parser.add_argument("--app-ip")
    parser.add_argument("--p-workers", type=int, default=7)
    parser.add_argument("--stop-utc")
    parser.add_argument("--phase-dir", type=Path)
    parser.add_argument("--binding-sha256")
    parser.add_argument("--database")
    parser.add_argument("--project-id", type=int, action="append")
    args = parser.parse_args()
    os.umask(0o077)
    try:
        print(json.dumps(prepare(args) if args.action == "prepare" else operate(args)))
    except (
        OSError,
        ValueError,
        KeyError,
        TypeError,
        subprocess.SubprocessError,
    ) as error:
        failure_path = None
        if args.phase_dir and (args.phase_dir / "receipts").is_dir():
            failure_path = (
                args.phase_dir / "receipts" / ("stage-failure-" + uuid4().hex + ".json")
            )
            failure = {
                "action": args.action,
                "utc": stamp(),
                "error_class": type(error).__name__,
                "partial_state_preserved": True,
            }
            if isinstance(error, subprocess.CalledProcessError):
                failure.update(
                    exit_code=error.returncode,
                    argv=list(map(str, error.cmd)),
                    stdout=error.stdout.decode(errors="replace")
                    if error.stdout
                    else "",
                    stderr=error.stderr.decode(errors="replace")
                    if error.stderr
                    else "",
                )
            elif isinstance(error, subprocess.TimeoutExpired):
                failure.update(timed_out=True, argv=list(map(str, error.cmd)))
            else:
                failure["reason"] = str(error)
            save(failure_path, failure)
        print(
            json.dumps(
                {
                    "success": False,
                    "error": "EXACT_CLOUD_CAMPAIGN_STAGE_REFUSED",
                    "error_class": type(error).__name__,
                    "private_error_receipt": str(failure_path)
                    if failure_path
                    else None,
                    "existing_data_or_partial_outputs_preserved": True,
                }
            )
        )
        raise SystemExit(1) from None
