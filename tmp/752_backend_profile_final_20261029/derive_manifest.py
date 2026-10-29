"""Derive a new 18-file PUBLIC code manifest; never approves a profile or touches SUT."""

import argparse
import hashlib
import json
from pathlib import Path

SOURCE = "356f29983c904e949245aedfad464efc1bf7b63d"
FILES = (
    "admin.py",
    "admin_seed.py",
    "assemble.py",
    "guard.py",
    "http_primitives.py",
    "make_evidence.py",
    "prepare_http.py",
    "stage_scope.py",
    "escalation_readback.py",
    "plan.template.PUBLIC.json",
    "intent.template.PUBLIC.json",
    "exclusive-proof.template.PUBLIC.json",
    "accounts.init-input.template.PUBLIC.json",
    "accounts.http-input.template.NO_SECRETS.json",
    "NEUTRAL_753.template.json",
    "TARGET_753.template.json",
    "source-manifest.json",
    "backend-bundle-manifest.json",
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--producer-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    directory = args.producer_dir.resolve()
    if {p.name for p in directory.glob("*.py")} != {name for name in FILES if name.endswith(".py")}:
        raise ValueError("EXACT_18_RUNTIME_PYTHON_SET_REQUIRED")
    result = {
        "kind": "r30-neutral-producer-code-manifest-v1",
        "source_sha": SOURCE,
        "files": {},
        "file_sizes": {},
        "status": "BUILD_FACTS_BOUND_ROOT_APPROVAL_AND_ACTUAL_IMPORT_PENDING",
        "actual_cloud_SUT_sessions": 0,
    }
    for name in FILES:
        path = directory / name
        if path.is_symlink() or not path.is_file():
            raise ValueError("REGULAR_OWNED_RUNTIME_FILE_REQUIRED")
        data = path.read_bytes()
        result["files"][name] = hashlib.sha256(data).hexdigest()
        result["file_sizes"][name] = len(data)
    with args.output.open("x") as stream:
        stream.write(json.dumps(result, indent=2) + "\n")
    print(hashlib.sha256(args.output.read_bytes()).hexdigest())


if __name__ == "__main__":
    main()
