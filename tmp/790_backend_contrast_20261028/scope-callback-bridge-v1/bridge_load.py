"""LOAD-only freshness and final publication. Never decrypts any credential."""

import base64
import os
import secrets
import subprocess
from datetime import timedelta
from pathlib import Path

from bridge_common import (
    LEASE_SECONDS,
    RETURN_MARGIN,
    Deadline,
    canonical,
    decode_document,
    document,
    export_packet,
    mkdir,
    parse,
    read,
    require,
    reserve,
    sha,
    stamp,
    utc,
)
from bridge_protocol import validate


def proc_stat(raw):
    parts = raw[raw.rfind(")") + 2 :].split()
    return {
        "state": parts[0],
        "ppid": int(parts[1]),
        "pgid": int(parts[2]),
        "start_ticks": parts[19],
    }


class DockerProcObserver:
    def __init__(self, command=None, proc_root=Path("/proc")):
        self.command = command or subprocess.check_output
        self.proc_root = proc_root

    def observe(self, owner, grant):
        cid = owner["container_id"]
        raw = self.command(
            ["docker", "--context", "default", "inspect", "--format", "{{json .}}", cid], timeout=5
        )
        info = parse(raw)
        require(
            info["Id"] == cid
            and info["State"]["Running"] is True
            and not info["State"].get("OOMKilled"),
            "OWNED_CONTAINER_NOT_LIVE",
        )
        require(info["State"]["Pid"] == owner["init_host_pid"], "CONTAINER_PID_CHANGED")
        require(
            info["Config"]["User"] == "10001:10001"
            and info["HostConfig"]["ReadonlyRootfs"] is True,
            "OPERATOR_SANDBOX_CHANGED",
        )
        require(
            info["HostConfig"]["NetworkMode"] == grant["network_name"], "OPERATOR_NETWORK_CHANGED"
        )
        initial = proc_stat((self.proc_root / str(owner["init_host_pid"]) / "stat").read_text())
        sup_dir = self.proc_root / str(owner["supervisor_host_pid"])
        supervisor = proc_stat((sup_dir / "stat").read_text())
        require(
            initial["start_ticks"] == str(owner["init_start_ticks"])
            and supervisor["start_ticks"] == str(owner["supervisor_start_ticks"]),
            "PID_REUSED",
        )
        require(
            initial["state"] not in {"Z", "X"}
            and supervisor["state"] not in {"Z", "X"}
            and supervisor["pgid"] == owner["supervisor_host_pgid"],
            "SUPERVISOR_NOT_LIVE",
        )
        status = (sup_dir / "status").read_text().splitlines()
        names = {
            line.split(":", 1)[0]: line.split(":", 1)[1].split() for line in status if ":" in line
        }
        require(
            int(names["NSpid"][-1]) == owner["supervisor_container_pid"]
            and int(names["NSpgid"][-1]) == owner["supervisor_container_pgid"],
            "CONTAINER_HOST_PID_MAPPING_CHANGED",
        )
        cursor, seen = owner["supervisor_host_pid"], set()
        while cursor != owner["init_host_pid"]:
            require(
                cursor > 1 and cursor not in seen and len(seen) < 64,
                "SUPERVISOR_NOT_OWNED_DESCENDANT",
            )
            seen.add(cursor)
            cursor = proc_stat((self.proc_root / str(cursor) / "stat").read_text())["ppid"]
        require(
            os.readlink(self.proc_root / "self/ns/time") == os.readlink(sup_dir / "ns/time"),
            "LOAD_SUPERVISOR_MONOTONIC_NAMESPACE_CHANGED",
        )
        return {
            "operator_uid": int(names["Uid"][1]),
            "monotonic_namespace_same_as_load": True,
            "alive": True,
            "container_id": cid,
            "supervisor_host_pid": owner["supervisor_host_pid"],
            "supervisor_start_ticks": supervisor["start_ticks"],
        }


def load_originals(configuration):
    require(
        set(configuration["originals"])
        == {"grant", "launch", "supervisor", "binding", "neutral", "admission"},
        "EXACT_ORIGINAL_INPUTS_REQUIRED",
    )
    require(
        all(
            isinstance(item["sha256"], str) and len(item["sha256"]) == 64
            for item in configuration["originals"].values()
        ),
        "EXPLICIT_ORIGINAL_SHA_REQUIRED",
    )
    return {
        name: document(read(Path(item["path"]), item["sha256"]))
        for name, item in configuration["originals"].items()
    }


def pending(authority, locations):
    request = decode_document(authority["documents"]["request"])
    path = Path(locations["request"])
    require(
        path.name == request["nonce"] + ".request.PUBLIC.json", "FIXED_REQUEST_FILENAME_REQUIRED"
    )
    read(path, authority["documents"]["request"]["sha256"])
    final = path.parent / (request["nonce"] + ".sealed.PUBLIC.json")
    require(not final.exists() and not final.is_symlink(), "NONCE_ALREADY_DELIVERED")
    return final


def fresh_observation(authority, configuration, observer, clock):
    grant = decode_document(authority["documents"]["grant"])
    require(
        authority["owner"]["supervisor_container_pgid"]
        == decode_document(authority["documents"]["launch"])["owned_pgid"],
        "OWNED_GROUP_BINDING",
    )
    observed = observer.observe(authority["owner"], grant)
    require(observed["alive"] is True, "LOAD_NOT_LIVE")
    require(
        observed["operator_uid"] == authority["owner"]["operator_uid"],
        "OPERATOR_HOST_UID_MAPPING_CHANGED",
    )
    status_path = configuration.get("status_path")
    if status_path and Path(status_path).exists():
        status = parse(read(Path(status_path)))
        require(
            status.get("returncode") is None
            and not status.get("hard_stopped")
            and not status.get("rss_stopped"),
            "SUPERVISOR_ALREADY_FINISHED",
        )
        require(
            not str(status.get("status", "")).startswith("PROCESS_FINISHED"),
            "SUPERVISOR_ALREADY_FINISHED",
        )
    return {
        **observed,
        "utc": utc(clock.now()),
        "monotonic": clock.mono(),
        "status_metadata_present": bool(status_path and Path(status_path).exists()),
    }


def prepare(configuration, request_path, request_sha, state_dir, observer, clock):
    documents = load_originals(configuration)
    documents["request"] = document(read(Path(request_path), request_sha))
    g, launch, sup, binding, request = (
        decode_document(documents[name])
        for name in ("grant", "launch", "supervisor", "binding", "request")
    )
    end = min(
        stamp(request["requested_utc"]) + timedelta(seconds=120),
        *(
            stamp(v)
            for v in (g["expires_at"], launch["expires_at"], sup["expires_at"], binding["stop_utc"])
        ),
    )
    authority = {
        "kind": "PUBLIC_SCOPE_AUTHORITY_V1",
        "bridge_id": secrets.token_hex(16),
        "bridge_bundle_sha256": configuration["bridge_bundle_sha256"],
        "documents": documents,
        "owner": configuration["owner"],
        "app_phase_dir": configuration["app_phase_dir"],
        "forbidden_key_shas": configuration["forbidden_key_shas"],
        "supervisor_nonce": sup["nonce"],
        "callback_deadline_utc": utc(end),
    }
    validate(authority, clock)
    locations = {name: item["path"] for name, item in configuration["originals"].items()}
    locations["request"] = str(request_path)
    pending(authority, locations)
    observation = fresh_observation(authority, configuration, observer, clock)
    authority["load_observation"] = observation
    authority["app_lease_end_utc"] = utc(
        min(clock.now() + timedelta(seconds=LEASE_SECONDS), end - timedelta(seconds=RETURN_MARGIN))
    )
    require(stamp(authority["app_lease_end_utc"]) > clock.now(), "NO_CALLBACK_BUDGET")
    require(observation["monotonic_namespace_same_as_load"] is True, "SAME_HOST_MONOTONIC_REQUIRED")
    deadline = Deadline(clock, end, sup["hard_deadline_monotonic"])
    root = Path(state_dir)
    root.mkdir(mode=0o700, exist_ok=True)
    require(root.resolve() == root, "CANONICAL_LOAD_STATE")
    nonce_key = sha((documents["grant"]["sha256"] + ":" + request["nonce"]).encode())
    reserve(root / (nonce_key + ".nonce-reserved"), authority["bridge_id"].encode())
    folder = mkdir(root / authority["bridge_id"])
    packet = export_packet(authority)
    reserve(folder / "authority.packet.PUBLIC.json", packet)
    state = {
        "authority": authority,
        "configuration": configuration,
        "locations": locations,
        "deadline_monotonic": deadline.monotonic_end,
        "packet_sha256": sha(packet),
    }
    reserve(folder / "reservation.PUBLIC.json", canonical(state) + b"\n")
    return {
        "folder": str(folder),
        "packet_sha256": sha(packet),
        "packet_bytes": len(packet),
        "bridge_id": authority["bridge_id"],
        "request_nonce": request["nonce"],
        "snapshot_alive_only_at_observation": True,
    }


def deliver(reservation, app_result, observer, clock):
    state = parse(read(Path(reservation)))
    authority = state["authority"]
    facts = validate(authority, clock)
    deadline = Deadline(clock, facts["end"], state["deadline_monotonic"])
    for name, path in state["locations"].items():
        read(Path(path), authority["documents"][name]["sha256"])
    result = app_result
    require(result["kind"] == "PUBLIC_SCOPE_APP_RESULT_V1", "OPAQUE_APP_RESULT_REQUIRED")
    receipt = result["receipt"]
    require(
        receipt["authority_sha256"] == sha(canonical(authority) + b"\n")
        and receipt["bridge_id"] == authority["bridge_id"]
        and receipt["request_sha256"] == authority["documents"]["request"]["sha256"]
        and receipt["bridge_bundle_sha256"] == authority["bridge_bundle_sha256"],
        "APP_RECEIPT_BINDING",
    )
    raw = base64.b64decode(result["opaque_b64"], validate=True)
    require(sha(raw) == receipt["opaque_sha256"], "OPAQUE_DIGEST_CHANGED")
    sealed = parse(raw)
    request = facts["request"]
    require(
        set(sealed)
        == {
            "kind",
            "nonce",
            "project_ids",
            "context",
            "wrapped_key_b64",
            "iv_b64",
            "ciphertext_b64",
            "hmac_sha256",
            "sealed_utc",
        },
        "EXACT_SEALED_SCOPE_WIRE",
    )
    require(
        sealed["kind"] == "SEALED_SERVICE_SCOPE"
        and sealed["nonce"] == request["nonce"]
        and sealed["project_ids"] == request["project_ids"]
        and sealed["context"] == request["context"],
        "OPAQUE_REQUEST_CONTEXT_CHANGED",
    )
    require(
        stamp(request["requested_utc"])
        <= stamp(sealed["sealed_utc"])
        <= stamp(authority["app_lease_end_utc"]),
        "SEALED_OUTSIDE_AUTHORITY_LEASE",
    )
    require(
        len(base64.b64decode(sealed["wrapped_key_b64"], validate=True)) == 384
        and len(base64.b64decode(sealed["iv_b64"], validate=True)) == 16,
        "RSA3072_AES_WIRE_REQUIRED",
    )
    require(
        len(base64.b64decode(sealed["ciphertext_b64"], validate=True)) > 0
        and len(base64.b64decode(sealed["ciphertext_b64"], validate=True)) % 16 == 0
        and len(sealed["hmac_sha256"]) == 64,
        "CIPHER_MAC_WIRE_REQUIRED",
    )
    target = pending(authority, state["locations"])
    temp = target.parent / (".bridge-" + authority["bridge_id"] + ".opaque.tmp")
    reserve(temp, raw, uid=authority["owner"]["operator_uid"])
    deadline.remaining()
    observation = fresh_observation(authority, state["configuration"], observer, clock)
    pending(authority, state["locations"])
    deadline.remaining()
    os.link(temp, target, follow_symlinks=False)
    temp.unlink()
    directory_fd = os.open(target.parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(directory_fd)
    finally:
        os.close(directory_fd)
    result = {
        "kind": "PUBLIC_SCOPE_DELIVERED_NOT_BUSINESS_VERDICT",
        "nonce": request["nonce"],
        "bridge_id": authority["bridge_id"],
        "reply_sha256": sha(raw),
        "reply_path": str(target),
        "final_load_observation": observation,
        "published_utc": utc(clock.now()),
        "published_monotonic": clock.mono(),
        "process_check_and_filesystem_commit_not_one_atomic_transaction": True,
        "decrypted_by_root": False,
        "no_retry": True,
    }
    reserve(Path(reservation).parent / "delivered.PUBLIC.json", canonical(result) + b"\n")
    return result
