"""Use actual seed counts to create a new phase plan; never alter binding/source/time."""

import argparse
from copy import deepcopy
from pathlib import Path

from guard import OPERATIONS, need, read_json
from http_primitives import save


def advance(plan, counts, operations):
    need(
        counts["run_id"] == plan["run_id"]
        and counts["namespace"] == plan["namespace"]
        and counts["database"] == plan["target"]["database"]
        and counts["binding_sha256"] == plan["target"]["binding_sha256"],
        "SAME_ACTUAL_COUNTS_SCOPE_REQUIRED",
    )
    ids = counts["project_ids"]
    need(
        len(ids) == len(set(ids)) == counts["raw_counts"]["projects"] == 40
        and all(type(pid) is int and pid > 0 for pid in ids),
        "ACTUAL_FORTY_PROJECT_IDS_REQUIRED",
    )
    need(set(operations) <= OPERATIONS, "EXPLICIT_FINITE_PHASE_WRITES_REQUIRED")
    result = deepcopy(plan)
    result["authorized_project_ids"] = sorted(ids)
    result["allowed_writes"] = list(operations)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ("seed-plan", "counts", "output"):
        parser.add_argument("--" + key, type=Path, required=True)
    parser.add_argument("--allow-write", action="append", default=[])
    args = parser.parse_args()
    save(args.output, advance(read_json(args.seed_plan), read_json(args.counts), args.allow_write))


if __name__ == "__main__":
    main()
