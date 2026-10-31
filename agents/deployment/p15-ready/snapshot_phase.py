"""Read-only P15 phase checks against original full inspect; never starts/stops containers."""

import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

APP_UTC = timezone.utc  # noqa: UP017 -- APP Python3.10

PROJECT = "t44-cloud-r30finalp09-p"
SOURCE = "bcec3326b40814fdb1922bbfea7c29473b47ba47"
BACKEND = "sha256:479c406502b2e4834a0e8ab9ed3fd35e60df60601a041348b1e4a97825056f0e"
WEB = "sha256:866ce20bb8cbeb55b949870b96260fb3f7437b4f8c9b54686a16138c075bdf79"
APPS = {"api", "consumer", "scheduler", "web"}
ROLES = APPS | {"mysql", "rabbitmq", "tls-gateway"}
LIMITS = [
    "CpuPeriod",
    "CpuQuota",
    "Memory",
    "MemorySwap",
    "NanoCpus",
    "PidsLimit",
    "Ulimits",
]
D = ["docker", "--context", "default"]


def need(v, c):
    if not v:
        raise ValueError(c)


def call(argv):
    p = subprocess.run(argv, capture_output=True, timeout=30, check=False)
    need(p.returncode == 0, "READONLY_DOCKER_FAILED_PRIVATE_OUTPUT_WITHHELD")
    return p.stdout


def roles(rows):
    need(len(rows) == 7, "EXACT_SEVEN_REQUIRED")
    table = {r["Config"]["Labels"]["com.docker.compose.service"]: r for r in rows}
    need(
        set(table) == ROLES
        and all(
            r["Config"]["Labels"]["com.docker.compose.project"] == PROJECT for r in rows
        ),
        "OWNED_SEVEN_REQUIRED",
    )
    return table


def mounts(row):
    return sorted(
        [
            {
                k: m.get(k)
                for k in ["Type", "Name", "Source", "Destination", "RW", "Propagation"]
            }
            for m in row["Mounts"]
        ],
        key=lambda m: m["Destination"],
    )


def env(row):
    return dict(x.split("=", 1) for x in row["Config"]["Env"])


def validate(before, after, phase):
    old, new = roles(before), roles(after)
    need(phase in ["created", "api-web-ready", "all-ready"], "KNOWN_PHASE_REQUIRED")
    result = []
    for role, r in new.items():
        prior = old[role]
        need(
            all(r["HostConfig"][k] == prior["HostConfig"][k] for k in LIMITS),
            "RESOURCES_CHANGED",
        )
        need(mounts(r) == mounts(prior), "MOUNTS_CHANGED")
        for k in ["Cmd", "Entrypoint", "User", "WorkingDir", "Healthcheck"]:
            need(
                r["Config"].get(k) == prior["Config"].get(k),
                "RUNTIME_COMMAND_OR_HEALTH_CHANGED",
            )
        for k in [
            "PortBindings",
            "RestartPolicy",
            "ReadonlyRootfs",
            "CapDrop",
            "SecurityOpt",
            "Tmpfs",
        ]:
            need(
                r["HostConfig"].get(k) == prior["HostConfig"].get(k),
                "HOST_CONFIGURATION_CHANGED",
            )
        old_networks = prior["NetworkSettings"]["Networks"]
        new_networks = r["NetworkSettings"]["Networks"]
        need(
            set(old_networks) == set(new_networks)
            and r["HostConfig"].get("NetworkMode")
            == prior["HostConfig"].get("NetworkMode"),
            "NETWORK_CONFIGURATION_CHANGED",
        )
        for name, n in new_networks.items():
            need(
                n.get("NetworkID") == old_networks[name]["NetworkID"]
                or (
                    role in APPS
                    and not r["State"]["Running"]
                    and not n.get("NetworkID")
                ),
                "NETWORK_ID_CHANGED",
            )
        e, expected = env(r), env(prior)
        if role == "api":
            expected["T44_REQUEST_DIAGNOSTICS"] = "1"
        need(e == expected, "ENV_CHANGED_OUTSIDE_DIAGNOSTIC_FLAG")
        if role in APPS:
            need(
                r["Image"] == (WEB if role == "web" else BACKEND),
                "NEW_EXACT_IMAGE_REQUIRED",
            )
        else:
            need(
                r["Id"] == prior["Id"] and r["Image"] == prior["Image"],
                "INFRA_ID_OR_IMAGE_CHANGED",
            )
        running = r["State"]["Running"]
        health = r["State"].get("Health", {}).get("Status")
        must_run = (
            role not in APPS
            or phase == "all-ready"
            or phase == "api-web-ready"
            and role in {"api", "web"}
        )
        need(running == must_run, "PHASE_RUNNING_STATE_MISMATCH")
        if must_run and role in {"api", "consumer", "scheduler", "mysql", "rabbitmq"}:
            need(health == "healthy", "PHASE_NOT_HEALTHY")
        result.append(
            {
                "id": r["Id"],
                "image_id": r["Image"],
                "project": PROJECT,
                "role": role,
                "name": r["Name"],
                "user": r["Config"]["User"],
                "limits": {k: r["HostConfig"][k] for k in LIMITS},
                "running": running,
                "health": health,
            }
        )
    return result


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--before-private", type=Path, required=True)
    p.add_argument(
        "--phase", choices=["created", "api-web-ready", "all-ready"], required=True
    )
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    before_raw = a.before_private.read_bytes()
    ids = (
        call(
            D
            + [
                "ps",
                "-aq",
                "--no-trunc",
                "--filter",
                "label=com.docker.compose.project=" + PROJECT,
            ]
        )
        .decode()
        .split()
    )
    rows = json.loads(call(D + ["inspect", *ids]))
    before_rows = json.loads(before_raw)
    original_networks = {
        name: net["NetworkID"]
        for r in before_rows
        for name, net in r["NetworkSettings"]["Networks"].items()
    }
    for name, network_id in original_networks.items():
        observed = json.loads(call(D + ["network", "inspect", name]))[0]
        need(observed["Id"] == network_id, "ORIGINAL_NETWORK_OBJECT_CHANGED")
    result = validate(before_rows, rows, a.phase)
    v = {
        "root_approved": False,
        "checks_passed": True,
        "source_sha": SOURCE,
        "phase": a.phase,
        "observed_at": datetime.now(APP_UTC).isoformat(),
        "before_private_sha256": hashlib.sha256(before_raw).hexdigest(),
        "containers": result,
        "no_start_stop_or_VM_calls": True,
    }
    with a.output.open("x") as f:
        json.dump(v, f, indent=2)
        f.write("\n")
    print(
        json.dumps(
            {
                "status": "OBSERVED_CHECKED_NOT_ROOT_OR_QA_APPROVAL",
                "phase": a.phase,
                "output": str(a.output),
            }
        )
    )
