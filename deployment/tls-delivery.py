"""One-stage exact-C TLS delivery; root executes only after review. No cloud API."""

import argparse
import hashlib
import ipaddress
import json
import os
import runpy
import stat
import subprocess
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path

PRODUCT_C = "0dfb55c2191200d947c5423fd9ee74bb0812cc5a"
DEADLINE = datetime(2026, 10, 24, 9, tzinfo=UTC).timestamp()
STAGE_END = DEADLINE - 120
IMAGES = {
    "mysql": "public.ecr.aws/docker/library/mysql:8.4@sha256:76f0358884cb92d9a086d24e5671c38048d3fef40f2588703d73eb55392d6b69",
    "rabbitmq": "public.ecr.aws/docker/library/rabbitmq:4-management-alpine@sha256:0452ee3fd3b9a74160b251e693338616b464f22df4d4ba43304c101bebdca292",
    "tls-gateway": "public.ecr.aws/docker/library/nginx:stable-alpine@sha256:47928bf67eb62a1863cb08d9ecb52d3e704304ba614eaee17884204677702951",
}
CAPS = {"prepare": 120, "config-check": 30, "pull": 300, "infra": 240,
        "migrate": 180, "seed": 300, "token": 120, "start": 240, "status": 30}
NGINX = """worker_processes auto;
pid /tmp/nginx.pid;
error_log /dev/stderr crit;
events { worker_connections 1024; }
http {
  access_log off;
  client_body_temp_path /tmp/client;
  proxy_temp_path /tmp/proxy;
  fastcgi_temp_path /tmp/fastcgi;
  uwsgi_temp_path /tmp/uwsgi;
  scgi_temp_path /tmp/scgi;
  server {
    listen 8443 ssl;
    ssl_certificate /etc/nginx/t44-server.crt;
    ssl_certificate_key /etc/nginx/t44-server.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    client_max_body_size 0;
    location / {
      proxy_pass http://web:8080;
      proxy_http_version 1.1;
      proxy_set_header Connection "";
      proxy_set_header Host $host;
      proxy_set_header X-Forwarded-Proto https;
      proxy_request_buffering off;
      proxy_connect_timeout 5s;
      proxy_send_timeout 30s;
      proxy_read_timeout 30s;
    }
  }
}
"""


def private_file(path: Path, mode: int = 0o600, owner: int | None = None) -> bytes:
    entry = path.lstat()
    if (not stat.S_ISREG(entry.st_mode) or stat.S_IMODE(entry.st_mode) != mode
            or entry.st_uid != (os.geteuid() if owner is None else owner)):
        raise ValueError("unsafe_private_file")
    return path.read_bytes()


def private_ip(path: Path) -> str:
    lines = private_file(path).decode().strip().splitlines()
    if len(lines) != 1 or not lines[0].startswith("T44_APP_PRIVATE_IPV4="):
        raise ValueError("neutral_environment_shape")
    value = lines[0].split("=", 1)[1]
    address = ipaddress.IPv4Address(value)
    if not any(address in ipaddress.IPv4Network(n) for n in ("10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16")):
        raise ValueError("RFC1918_required")
    return str(address)


def save(path: Path, data: bytes, mode: int = 0o600) -> None:
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, mode)
    with os.fdopen(fd, "wb") as stream:
        os.fchmod(stream.fileno(), mode)
        stream.write(data)


def invoke(command: list[str], cap: int, *, data: bytes | None = None,
           environment: dict | None = None) -> subprocess.CompletedProcess:
    left = int(min(DEADLINE - 120, STAGE_END) - time.time())
    if left <= 0:
        raise ValueError("deadline_reserve_reached")
    return subprocess.run(command, input=data, capture_output=True, check=True,
                          timeout=min(cap, left), env=environment)


def check_source(root: Path) -> dict[str, str]:
    if not root.is_absolute() or root.is_symlink() or ".." in root.parts:
        raise ValueError("absolute_source_required")
    head = invoke(["git", "-C", str(root), "rev-parse", "HEAD"], 5).stdout.decode().strip()
    if head != PRODUCT_C:
        raise ValueError("wrong_product_source")
    invoke(["git", "-C", str(root), "diff", "--quiet", "HEAD", "--"], 5)
    private_file(root / ".env")
    values = runpy.run_path(str(root / "deployment/ops.py"))["load_env"](root / ".env")
    if values["T44_DOCKER_CONTEXT"] != "default":
        raise ValueError("local_default_context_required")
    return values


def render_overlay(runtime: Path, ip: str) -> dict:
    mounts = [{"type": "bind", "source": str(runtime / name), "target": target,
               "read_only": True, "bind": {"create_host_path": False}}
              for name, target in (("gateway.conf", "/etc/nginx/nginx.conf"),
                                   ("server.crt", "/etc/nginx/t44-server.crt"),
                                   ("server.key", "/etc/nginx/t44-server.key"))]
    return {"services": {
        "mysql": {"image": IMAGES["mysql"]}, "rabbitmq": {"image": IMAGES["rabbitmq"]},
        "tls-gateway": {"image": IMAGES["tls-gateway"], "init": True, "user": "10001:10001",
                        "entrypoint": ["nginx"], "command": ["-g", "daemon off;"],
                        "restart": "unless-stopped", "read_only": True,
                        "cap_drop": ["ALL"], "security_opt": ["no-new-privileges:true"],
                        "tmpfs": ["/tmp:rw,noexec,nosuid,size=64m,mode=1777"],
                        "networks": ["edge"], "volumes": mounts,
                        "ports": [{"target": 8443, "published": "8443", "host_ip": ip, "protocol": "tcp"}],
                        "depends_on": {"web": {"condition": "service_healthy"}},
                        "healthcheck": {"test": ["CMD", "nginx", "-t", "-q"], "interval": "20s",
                                        "timeout": "5s", "retries": 3},
                        "logging": {"driver": "json-file", "options": {"max-size": "10m", "max-file": "3"}}}}}


def verify_tls(runtime: Path, ip: str) -> None:
    invoke(["openssl", "verify", "-CAfile", str(runtime / "ca.crt"), str(runtime / "server.crt")], 5)
    invoke(["openssl", "x509", "-in", str(runtime / "server.crt"), "-noout", "-checkip", ip], 5)
    invoke(["openssl", "x509", "-in", str(runtime / "server.crt"), "-noout", "-checkend", "300"], 5)
    key = invoke(["openssl", "pkey", "-in", str(runtime / "server.key"), "-pubout", "-outform", "DER"], 5).stdout
    cert_pem = invoke(["openssl", "x509", "-in", str(runtime / "server.crt"), "-pubkey", "-noout"], 5).stdout
    cert_key = invoke(["openssl", "pkey", "-pubin", "-outform", "DER"], 5, data=cert_pem).stdout
    if key != cert_key:
        raise ValueError("certificate_key_mismatch")


def prepare(runtime: Path, ip: str) -> None:
    parent = runtime.parent.lstat()
    if not stat.S_ISDIR(parent.st_mode) or stat.S_IMODE(parent.st_mode) != 0o700 or parent.st_uid != os.geteuid():
        raise ValueError("private_parent_required")
    runtime.mkdir(mode=0o700)
    invoke(["openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes", "-sha256", "-days", "1",
            "-subj", "/CN=T44 temporary delivery CA", "-addext", "basicConstraints=critical,CA:TRUE,pathlen:0",
            "-addext", "keyUsage=critical,keyCertSign,cRLSign", "-keyout", str(runtime / "ca.key"),
            "-out", str(runtime / "ca.crt")], 30)
    invoke(["openssl", "req", "-new", "-newkey", "rsa:2048", "-nodes", "-sha256", "-subj",
            "/CN=T44 private gateway", "-keyout", str(runtime / "server.key"), "-out", str(runtime / "server.csr")], 30)
    save(runtime / "server.ext", ("subjectAltName=IP:" + ip + "\nbasicConstraints=critical,CA:FALSE\n"
                                 "keyUsage=critical,digitalSignature,keyEncipherment\nextendedKeyUsage=serverAuth\n").encode())
    invoke(["openssl", "x509", "-req", "-in", str(runtime / "server.csr"), "-CA", str(runtime / "ca.crt"),
            "-CAkey", str(runtime / "ca.key"), "-CAcreateserial", "-days", "1", "-sha256", "-extfile",
            str(runtime / "server.ext"), "-out", str(runtime / "server.crt")], 10)
    for name in ("ca.key", "ca.crt", "server.key", "server.crt"):
        (runtime / name).chmod(0o600)
    verify_tls(runtime, ip)
    os.chown(runtime / "server.key", 10001, 10001)
    save(runtime / "gateway.conf", NGINX.encode(), 0o644)
    (runtime / "server.crt").chmod(0o644)
    overlay = render_overlay(runtime, ip)
    save(runtime / "overlay.json", (json.dumps(overlay, indent=2) + "\n").encode())
    files = ("overlay.json", "gateway.conf", "ca.crt", "server.crt", "server.key")
    manifest = {"product_source": PRODUCT_C, "private_ip": ip, "https_endpoint": f"https://{ip}:8443/api/v1",
                "file_sha256": {n: hashlib.sha256((runtime / n).read_bytes()).hexdigest() for n in files},
                "topology": "load HTTPS -> extra TLS gateway on app host -> C web HTTP -> API4workers",
                "CA_key_mounted": False, "gateway_resource_accounting": "additional to existing six-service sampler"}
    save(runtime / "manifest.json", (json.dumps(manifest, indent=2) + "\n").encode())


def validate_runtime(runtime: Path, ip: str) -> None:
    directory = runtime.lstat()
    if not stat.S_ISDIR(directory.st_mode) or stat.S_IMODE(directory.st_mode) != 0o700 or directory.st_uid != os.geteuid():
        raise ValueError("private_runtime_required")
    manifest = json.loads(private_file(runtime / "manifest.json"))
    if manifest["product_source"] != PRODUCT_C or manifest["private_ip"] != ip:
        raise ValueError("delivery_identity_differs")
    overlay = json.loads(private_file(runtime / "overlay.json"))
    if overlay != render_overlay(runtime, ip):
        raise ValueError("overlay_not_allowlisted")
    if set(manifest["file_sha256"]) != {"overlay.json", "gateway.conf", "ca.crt", "server.crt", "server.key"}:
        raise ValueError("manifest_file_set_differs")
    if (runtime / "gateway.conf").read_bytes() != NGINX.encode():
        raise ValueError("gateway_configuration_differs")
    private_file(runtime / "ca.key")
    for name, digest in manifest["file_sha256"].items():
        mode = 0o644 if name in {"gateway.conf", "server.crt"} else 0o600
        owner = 10001 if name == "server.key" else os.geteuid()
        data = private_file(runtime / name, mode, owner)
        if hashlib.sha256(data).hexdigest() != digest:
            raise ValueError("delivery_file_changed")
    verify_tls(runtime, ip)


def stage_arguments(args: argparse.Namespace, values: dict) -> list[str] | None:
    stage = args.stage
    if (args.execute and stage != "migrate" or args.database is not None and stage not in {"migrate", "seed"}
            or args.project_id is not None and stage != "token"):
        raise ValueError("stage_options_differ")
    if stage == "config-check":
        return ["config", "--quiet"]
    if stage == "pull":
        return ["pull", "--policy", "missing", "mysql", "rabbitmq", "tls-gateway"]
    if stage == "infra":
        return ["up", "-d", "--no-build", "--pull", "never", "--wait", "--wait-timeout", "180", "mysql", "rabbitmq"]
    if stage in {"migrate", "seed"}:
        if args.database != values["MYSQL_DATABASE"]:
            raise ValueError("explicit_database_differs")
        if stage == "migrate":
            return ["--profile", "operations", "run", "--rm", "-T", "--pull", "never", "--no-deps", "migrate"] if args.execute else None
        return ["--profile", "operations", "run", "--rm", "-T", "--pull", "never", "--no-deps", "admin", "seed-demo",
                "--projects", "40", "--tasks", "6000", "--dependencies", "9000", "--records", "15000"]
    if stage == "token":
        if not args.project_id or len(set(args.project_id)) != len(args.project_id) or any(p <= 0 or p > 4294967295 for p in args.project_id):
            raise ValueError("explicit_unique_projects_required")
        return ["--profile", "operations", "run", "--rm", "-T", "--pull", "never", "--no-deps", "credential-admin", "--name", "scheduler",
                *[s for p in args.project_id for s in ("--project-id", str(p))]]
    if stage == "start":
        return ["up", "-d", "--no-build", "--pull", "never", "--wait", "--wait-timeout", "180",
                "api", "consumer", "scheduler", "web", "tls-gateway"]
    return ["ps"]


def main() -> int:
    global STAGE_END
    os.umask(0o077)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--runtime", type=Path, required=True)
    parser.add_argument("--private-env", type=Path, required=True)
    parser.add_argument("stage", choices=CAPS)
    parser.add_argument("--database")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--project-id", action="append", type=int)
    args = parser.parse_args()
    started = time.time()
    try:
        if os.geteuid() != 0 or not args.runtime.is_absolute() or ".." in args.runtime.parts:
            raise ValueError("root_and_absolute_runtime_required")
        if DEADLINE - started < CAPS[args.stage] + 120:
            raise ValueError("insufficient_deadline_budget")
        STAGE_END = min(DEADLINE - 120, started + CAPS[args.stage])
        stage_arguments(args, {"MYSQL_DATABASE": args.database})
        values = check_source(args.source_root)
        ip = private_ip(args.private_env)
        if args.stage == "prepare":
            prepare(args.runtime, ip)
        else:
            validate_runtime(args.runtime, ip)
            action = stage_arguments(args, values)
            if action is None:
                print(json.dumps({"stage": "migrate", "plan_only": True, "execute_required": True}))
                return 0
            environment = {k: v for k, v in os.environ.items()
                           if k not in values and k not in {"DOCKER_HOST", "DOCKER_CONTEXT"}
                           and not k.startswith("COMPOSE_")}
            environment.update(values)
            endpoint = invoke(["docker", "--context", "default", "context", "inspect", "default", "--format", "{{.Endpoints.docker.Host}}"], 5, environment=environment)
            if not endpoint.stdout.decode().strip().startswith("unix://"):
                raise ValueError("local_unix_daemon_required")
            base = ["docker", "--context", "default", "compose", "--project-name", values["COMPOSE_PROJECT_NAME"],
                       "--env-file", str(args.source_root / ".env"), "-f", str(args.source_root / "compose.yaml"),
                       "-f", str(args.runtime / "overlay.json")]
            if args.stage == "token":
                listing = invoke([*base, "ps", "--services", "--status", "running"], 10, environment=environment)
                if "scheduler" in listing.stdout.decode().splitlines():
                    raise ValueError("initial_token_requires_scheduler_stopped")
            stem = args.stage + "-" + uuid.uuid4().hex
            try:
                result = invoke([*base, *action], CAPS[args.stage], environment=environment)
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as failure:
                save(args.runtime / (stem + ".stdout"), failure.stdout or b"")
                save(args.runtime / (stem + ".stderr"), failure.stderr or b"")
                save(args.runtime / (stem + ".json"), json.dumps({"stage": args.stage,
                     "actual_exit_code": getattr(failure, "returncode", None),
                     "timed_out": isinstance(failure, subprocess.TimeoutExpired),
                     "state_requires_observation": True, "rollback_or_cleanup_attempted": False}).encode())
                raise
            else:
                save(args.runtime / (stem + ".stdout"), result.stdout)
                save(args.runtime / (stem + ".stderr"), result.stderr)
        print(json.dumps({"stage": args.stage, "actual_exit_code": 0, "elapsed_seconds": round(time.time() - started, 3),
                          "product_source": PRODUCT_C, "runtime": str(args.runtime), "application_or_performance_passed": False}))
        return 0
    except (OSError, ValueError, TypeError, KeyError, subprocess.SubprocessError):
        print(json.dumps({"stage": args.stage, "error": "delivery_stage_failed", "state_requires_observation": True}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
