"""New source935 TLS-only overlay; preserve frozen base/factory and verify real host HTTPS."""

import argparse
import calendar
import hashlib
import http.client
import importlib.util
import ipaddress
import json
import os
import ssl
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

BASE_BINDING = "770d774b715265ba517ea550aab5d001ecd8c04c58f3beb9cc558e752170ca06"
DIAG_BINDING = "56d78db5dc30cbd08db1e29e93c466c0986969e78165ffc4ce370f07f21ef32e"
BASE_CODE = "daaf29d3b47ab266ae4546f001e322275db5c3c902c9f36f8b8a2528690af2ea"
DIAG_CODE = "94caf90c9d711d68b55759ab4988b317943549ab1c2f4f966e676c5c4c39bfa3"
DOCKER = ["docker", "--context", "default"]


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def write(p, data):
    fd = os.open(p, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "wb") as f:
        f.write(data)


def save(p, row):
    write(p, (json.dumps(row, indent=2) + "\n").encode())


def stamp():
    return datetime.now(timezone.utc).isoformat()  # noqa: UP017 - host Python3.10


def module(p, expected, name):
    if sha(p) != expected:
        raise ValueError("EXACT_FROZEN_MODULE_REQUIRED")
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location(name, p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def patch_config(old):
    marker = "  proxy_temp_path /tmp/proxy_temp;\n"
    if old.count(marker) != 1 or any(
        key in old for key in ["fastcgi_temp_path", "uwsgi_temp_path", "scgi_temp_path"]
    ):
        raise ValueError("EXACT_UNPATCHED_NGINX_PREIMAGE_REQUIRED")
    return old.replace(
        marker,
        marker
        + "  fastcgi_temp_path /tmp/fastcgi_temp;\n  uwsgi_temp_path /tmp/uwsgi_temp;\n  scgi_temp_path /tmp/scgi_temp;\n",
    )


def validate_tls(tls, old, base, output, phase):
    for key in [
        "image",
        "user",
        "read_only",
        "entrypoint",
        "command",
        "cap_drop",
        "security_opt",
        "tmpfs",
    ]:
        if tls.get(key) != old.get(key):
            raise ValueError("ORIGINAL_TLS_SECURITY_CHANGED_" + key)
    volumes = {
        v["target"]: (v["source"], v.get("read_only", False)) for v in tls["volumes"]
    }
    if volumes != {
        "/etc/nginx/nginx.conf": (str(output / "nginx.conf"), True),
        "/run/t44-tls": (str(phase / "tls/server"), True),
    }:
        raise ValueError("EXACT_TWO_TLS_READONLY_MOUNTS_REQUIRED")
    ports = tls["ports"]
    if (
        len(ports) != 1
        or ports[0]["host_ip"] != base["app_private_ip"]
        or str(ports[0]["published"]) != str(base["tls_port"])
        or ports[0]["target"] != 8443
    ):
        raise ValueError("ORIGINAL_PRIVATE_IP_TLS_PORT_REQUIRED")
    if set(tls["networks"]) != {"edge", "application"}:
        raise ValueError("ORIGINAL_TLS_NETWORKS_REQUIRED")


def raw_command(argv, output, label, timeout=120):
    env = {
        k: v
        for k, v in os.environ.items()
        if not k.startswith(("DOCKER_", "COMPOSE_", "T44_", "MYSQL_", "RABBITMQ_"))
    }
    try:
        result = subprocess.run(
            list(map(str, argv)),
            capture_output=True,
            check=False,
            timeout=timeout,
            env=env,
        )
    except subprocess.TimeoutExpired as error:
        save(
            output / (label + ".json"),
            {
                "utc": stamp(),
                "timeout": timeout,
                "stdout": (error.stdout or b"").decode(errors="replace"),
                "stderr": (error.stderr or b"").decode(errors="replace"),
            },
        )
        raise
    save(
        output / (label + ".json"),
        {
            "utc": stamp(),
            "returncode": result.returncode,
            "stdout": result.stdout.decode(errors="replace"),
            "stderr": result.stderr.decode(errors="replace"),
        },
    )
    if result.returncode:
        raise ValueError("RECORDED_COMMAND_FAILED_" + label)
    return result.stdout


def https_probe(base, ca, receipts):
    context = ssl.create_default_context(cafile=str(ca))
    context.check_hostname = True
    context.verify_mode = ssl.CERT_REQUIRED
    address = base["app_private_ip"]
    if (
        not isinstance(ipaddress.ip_address(address), ipaddress.IPv4Address)
        or not ipaddress.ip_address(address).is_private
    ):
        raise ValueError("FROZEN_PRIVATE_IPV4_REQUIRED")
    start = time.monotonic()
    for index in range(1, 31):
        c = http.client.HTTPSConnection(
            address, base["tls_port"], context=context, timeout=5
        )
        row = {
            "utc": stamp(),
            "attempt": index,
            "elapsed_seconds": time.monotonic() - start,
            "method": "GET",
            "path": "/api/v1/projects",
            "credentials_sent": False,
        }
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
                body_truncated=len(body) > 1024 * 1024,
            )
        except (OSError, http.client.HTTPException) as error:
            row.update(
                error_class=type(error).__name__,
                error=str(error),
                strict_CA_and_IP_verified=False,
            )
        finally:
            c.close()
        save(receipts / ("https-attempt-" + str(index) + ".json"), row)
        if row.get("status") == 401 and not row.get("body_truncated"):
            return {
                "status": 401,
                "strict_CA_and_IP_verified": True,
                "credentials_sent": False,
                "attempts": index,
                "path": "/api/v1/projects",
            }
        if time.monotonic() - start >= 30:
            break
        time.sleep(1)
    raise ValueError("ACTUAL_HOST_STRICT_TLS_401_NOT_PROVEN")


def apply(args):
    if os.geteuid() != 0:
        raise ValueError("ROOT_CLOUD_OPERATOR_REQUIRED")
    bm = module(args.base_phase / "controller.py", BASE_CODE, "frozen_campaign")
    dm = module(args.diagnostic_profile / "controller.py", DIAG_CODE, "frozen_factory")
    dm.private(args.diagnostic_profile, True)
    if sha(args.diagnostic_profile / "binding.json") != DIAG_BINDING:
        raise ValueError("EXACT_FACTORY_BINDING_REQUIRED")
    diag = dm.profile(args.diagnostic_profile)
    base, _ = dm.base_phase(args.base_phase, BASE_BINDING)
    if (
        diag["base_phase"] != str(args.base_phase)
        or diag["base_binding_sha256"] != BASE_BINDING
    ):
        raise ValueError("EXACT_FACTORY_TO_BASE_RELATION_REQUIRED")
    if time.time() + 240 >= calendar.timegm(
        time.strptime(base["stop_utc"], "%Y-%m-%dT%H:%M:%SZ")
    ):
        raise ValueError("ORIGINAL_STOP_WINDOW_CLOSED_NO_EXTENSION")
    dm.command(["systemctl", "is-active", "--quiet", base["timer_unit"]])
    original = (args.base_phase / "nginx.conf").read_text()
    if original != bm.nginx():
        raise ValueError("EXACT_FROZEN_NGINX_CONFIG_REQUIRED")
    ca = args.base_phase / "tls/ca.pem"
    if sha(ca) != base["tls"]["ca_sha256"]:
        raise ValueError("ORIGINAL_CA_CHANGED")
    dm.private(args.output.parent, True)
    args.output.mkdir(mode=0o700)
    receipts = args.output / "receipts"
    receipts.mkdir(mode=0o700)
    write(args.output / "nginx.conf", patch_config(original).encode())
    (args.output / "nginx.conf").chmod(0o644)
    overlay = {
        "services": {
            "tls-gateway": {
                "volumes": [
                    {
                        "type": "bind",
                        "source": str(args.output / "nginx.conf"),
                        "target": "/etc/nginx/nginx.conf",
                        "read_only": True,
                    }
                ],
                "labels": {
                    "io.t44.tls-repair.kind": "explicit-readonly-temp-paths",
                    "io.t44.tls-repair.config-sha256": sha(args.output / "nginx.conf"),
                },
            }
        }
    }
    save(args.output / "overlay.json", overlay)
    binding = {
        "kind": "source935-tls-temp-path-repair",
        "utc": stamp(),
        "base_phase": str(args.base_phase),
        "base_binding_sha256": BASE_BINDING,
        "factory_profile": str(args.diagnostic_profile),
        "factory_binding_sha256": DIAG_BINDING,
        "base_project": base["project"],
        "source_sha": base["source_sha"],
        "original_stop_utc_unchanged": base["stop_utc"],
        "timer_unchanged": base["timer_unit"],
        "CA_sha256_unchanged": base["tls"]["ca_sha256"],
        "old_config_sha256": sha(args.base_phase / "nginx.conf"),
        "new_config_sha256": sha(args.output / "nginx.conf"),
        "overlay_sha256": sha(args.output / "overlay.json"),
        "helper_sha256": sha(Path(__file__)),
        "only_service_to_up": "tls-gateway",
        "original_files_modified": False,
    }
    save(args.output / "binding.json", binding)
    argv = [
        *DOCKER,
        "compose",
        "--env-file",
        args.base_phase / "application.env",
        "--file",
        args.base_phase / "compose.json",
        "--file",
        args.diagnostic_profile / "overlay.json",
        "--file",
        args.output / "overlay.json",
        "--project-name",
        base["project"],
    ]
    # Full rendered config contains private DB env: memory-only, never log this stdout.
    rendered = json.loads(dm.command([*argv, "config", "--format", "json"]))
    old_compose = json.loads((args.base_phase / "compose.json").read_text())
    actual_nginx_id = (
        dm.command(
            [
                *DOCKER,
                "image",
                "inspect",
                "--format",
                "{{.Id}}",
                old_compose["services"]["tls-gateway"]["image"],
            ]
        )
        .decode()
        .strip()
    )
    if actual_nginx_id not in {base["image_ids"]["nginx"], base["config_ids"]["nginx"]}:
        raise ValueError("ORIGINAL_PROVEN_NGINX_IMAGE_REQUIRED")
    validate_tls(
        rendered["services"]["tls-gateway"],
        old_compose["services"]["tls-gateway"],
        base,
        args.output,
        args.base_phase,
    )
    raw_command(
        [*argv, "run", "--rm", "--no-deps", "-T", "tls-gateway", "-t"],
        receipts,
        "nginx-t",
        60,
    )
    raw_command(
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
        receipts,
        "tls-up",
        90,
    )
    probe = https_probe(base, ca, receipts)
    save(receipts / "host-https-success.json", {"utc": stamp(), **probe})
    dm.base_phase(args.base_phase, BASE_BINDING)
    dm.profile(args.diagnostic_profile)
    result = {
        "success": True,
        "binding_path": str(args.output / "binding.json"),
        "binding_sha256": sha(args.output / "binding.json"),
        "nginx_t_passed": True,
        "host_https": probe,
        "only_tls_gateway_up": True,
        "old_base_factory_and_stop_unchanged": True,
    }
    save(receipts / "apply-success.json", result)
    return result


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--base-phase", type=Path, required=True)
    p.add_argument("--diagnostic-profile", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    os.umask(0o077)
    try:
        print(json.dumps(apply(args)))
    except (
        OSError,
        ValueError,
        KeyError,
        TypeError,
        subprocess.SubprocessError,
        http.client.HTTPException,
    ) as error:
        failure = None
        if args.output.is_dir():
            failure = args.output / ("failure-" + uuid4().hex + ".json")
            save(
                failure,
                {
                    "utc": stamp(),
                    "error_class": type(error).__name__,
                    "reason": str(error),
                    "partial_state_preserved": True,
                },
            )
        print(
            json.dumps(
                {
                    "success": False,
                    "error": "TLS_REPAIR_OR_STRICT_HOST_PROBE_FAILED",
                    "private_failure_path": str(failure) if failure else None,
                    "original_files_modified": False,
                }
            )
        )
        raise SystemExit(1) from None
