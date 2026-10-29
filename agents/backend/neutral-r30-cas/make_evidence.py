"""Join actual local receipts without creating facts, credentials or an authorization."""

import argparse
import hashlib
from datetime import UTC, datetime
from pathlib import Path

from guard import check_evidence, need, read_json
from http_primitives import save


def join(plan, facts, counts, exclusive_proof):
    for value in (facts, counts, exclusive_proof):
        need(
            value["run_id"] == plan["run_id"]
            and value["namespace"] == plan["namespace"]
            and value["database"] == plan["target"]["database"]
            and value["binding_sha256"] == plan["target"]["binding_sha256"],
            "ACTUAL_RECEIPTS_HAVE_DIFFERENT_SCOPE",
        )
    clients = facts["inventory"]["clients"]
    value = {
        **facts,
        "actual_fixture_counts": counts["actual_fixture_counts"],
        "actual_fixture_sha256": counts["actual_fixture_sha256"],
        "exclusive_scope": {
            **exclusive_proof,
            "task_ids": [
                client[key]["id"]
                for client in clients
                for key in ("transition_task", "escalation_task")
            ],
            "event_ids": [client["escalation_event"]["id"] for client in clients],
        },
    }
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ("plan", "facts", "counts", "exclusive-proof", "output"):
        parser.add_argument("--" + key, type=Path, required=True)
    args = parser.parse_args()
    plan = read_json(args.plan)
    proof = read_json(args.exclusive_proof)
    proof["writer_evidence_sha256"] = hashlib.sha256(args.exclusive_proof.read_bytes()).hexdigest()
    result = join(plan, read_json(args.facts), read_json(args.counts), proof)
    check_evidence(plan, result, datetime.now(UTC))
    save(args.output, result)


if __name__ == "__main__":
    main()
