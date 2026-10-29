"""APP bounded provisioning orchestration. LOAD liveness is explicitly only a snapshot."""

import base64
import fcntl
import os
from datetime import timedelta
from pathlib import Path

from bridge_common import (
    APP_MAX_SECONDS,
    APP_MIN_SECONDS,
    SNAPSHOT_SECONDS,
    Deadline,
    canonical,
    mkdir,
    require,
    reserve,
    sha,
    stamp,
    utc,
)
from bridge_protocol import validate


def provision(authority, state_dir, backend, clock, bundle_sha):
    facts = validate(authority, clock)
    require(authority["bridge_bundle_sha256"] == bundle_sha, "EXACT_BRIDGE_BUNDLE_REQUIRED")
    age = (clock.now() - stamp(authority["load_observation"]["utc"])).total_seconds()
    require(
        authority["load_observation"]["alive"] is True and 0 <= age <= SNAPSHOT_SECONDS,
        "FRESH_LOAD_SNAPSHOT_REQUIRED",
    )
    deadline = Deadline(
        clock,
        min(
            stamp(authority["app_lease_end_utc"]),
            facts["end"],
            clock.now() + timedelta(seconds=APP_MAX_SECONDS),
        ),
    )
    require(
        deadline.remaining() >= APP_MIN_SECONDS, "INSUFFICIENT_CALLBACK_BUDGET_BEFORE_PROVISION"
    )
    require(
        (stamp(facts["binding"]["stop_utc"]) - clock.now()).total_seconds() >= 600,
        "GEN_WINDOW_MINIMUM600",
    )
    backend.deadline = deadline
    backend.check_binding(facts, authority)
    state = Path(state_dir)
    state.mkdir(mode=0o700, exist_ok=True)
    require(state.resolve() == state, "CANONICAL_APP_STATE")
    claim = sha(
        (authority["documents"]["grant"]["sha256"] + ":" + facts["request"]["nonce"]).encode()
    )
    reserve(state / (claim + ".claimed"), authority["bridge_id"].encode())
    folder = mkdir(state / authority["bridge_id"])
    lock_path = state / (authority["documents"]["binding"]["sha256"] + ".phase.lock")
    lock = os.open(lock_path, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    dirty = state / (authority["documents"]["binding"]["sha256"] + ".inflight-or-quarantined")
    mutated = False
    receipts = []
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        require(not dirty.exists(), "PHASE_HAS_UNRESOLVED_INFLIGHT_OPERATION")
        deadline.remaining()
        backend.preflight(facts, authority, folder, deadline)
        deadline.remaining()
        current = backend.scheduler_state(facts)
        action = "scheduler-token" if current["absent"] else "scheduler-rotate"
        require(
            not current["absent"] or not current["credential_exists"],
            "ORPHAN_CREDENTIAL_NOT_RESUMABLE",
        )
        require(
            current["absent"] or current["healthy_owned"],
            "OWNED_RUNNING_SCHEDULER_REQUIRED_FOR_ROTATION",
        )
        reserve(
            dirty,
            canonical(
                {
                    "bridge_id": authority["bridge_id"],
                    "nonce": facts["request"]["nonce"],
                    "started_utc": utc(clock.now()),
                }
            ),
        )
        mutated = True
        for stage in (action, "scheduler-start"):
            validate(authority, clock)
            deadline.remaining()
            backend.check_binding(facts, authority)
            receipts.append(backend.generation(stage, facts, folder, deadline))
        deadline.remaining()
        scheduler = backend.confirm_scheduler(facts, folder)
        deadline.remaining()
        opaque = backend.seal(facts, authority, scheduler, folder, deadline)
        deadline.remaining()
        sealed = __import__("json").loads(opaque)
        require(
            sealed["kind"] == "SEALED_SERVICE_SCOPE"
            and sealed["nonce"] == facts["request"]["nonce"]
            and sealed["project_ids"] == facts["request"]["project_ids"]
            and sealed["context"] == facts["request"]["context"],
            "DATA_WORKER_WIRE_MISMATCH",
        )
        receipt = {
            "kind": "PUBLIC_SCOPE_PROVISIONED_V1",
            "bridge_id": authority["bridge_id"],
            "authority_sha256": sha(canonical(authority) + b"\n"),
            "bridge_bundle_sha256": bundle_sha,
            "request_sha256": authority["documents"]["request"]["sha256"],
            "source_sha": facts["binding"]["source_sha"],
            "binding_sha256": authority["documents"]["binding"]["sha256"],
            "opaque_sha256": sha(opaque),
            "opaque_bytes": len(opaque),
            "controller_receipt_sha256": [sha(canonical(r)) for r in receipts],
            "scheduler": scheduler,
            "load_observation_was_snapshot_only": True,
            "completed_utc": utc(clock.now()),
            "app_monotonic": clock.mono(),
            "no_automatic_retry": True,
            "private_output_printed": False,
        }
        result = {
            "kind": "PUBLIC_SCOPE_APP_RESULT_V1",
            "receipt": receipt,
            "opaque_b64": base64.b64encode(opaque).decode(),
        }
        reserve(folder / "opaque-result.PUBLIC.json", canonical(result) + b"\n")
        reserve(folder / "completed.PUBLIC.json", canonical(receipt) + b"\n")
        dirty.unlink()
        return result
    except BaseException:
        failure = {
            "kind": "PUBLIC_SCOPE_APP_STOPPED",
            "bridge_id": authority["bridge_id"],
            "provision_may_have_committed": mutated,
            "inflight_may_complete": mutated,
            "no_automatic_retry": True,
            "private_output_printed": False,
        }
        reserve(folder / "failed.PUBLIC.json", canonical(failure) + b"\n")
        raise
    finally:
        os.close(lock)
