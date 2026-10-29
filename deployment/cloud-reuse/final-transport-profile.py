"""New source/magic/C thin policy; original 790 cryptographic bytes are immutable."""
import argparse
import hashlib
import json
import os
from pathlib import Path

HERE = Path(__file__).resolve().parent
OLD = HERE.parent.parent / "agents/backend/neutral-transport-r30"
PINS = {"790_transfer.original.py": "8600110b54f45240a6e45ea62c9be6f567529e374807d0ca593dde3fd7605db7",
        "policy_790.py": "aefc41b911a76cdbd61366e7779d4fd7613ab66deffb146520d464e454099f95",
        "five_files.py": "2ab17b332a9d0ccf0d75876ca31d966c56ab23955f4d4be7563ea4a8b81758f5",
        "opaque_tls.py": "cfc134519a9217f1dcc2c9cc7ce258789c18b577eb9d87d72691082d6a17fa65"}


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def derive(args):
    raw = args.timeplan.read_bytes()
    if args.timeplan.is_symlink() or digest(raw) != args.timeplan_sha256:
        raise ValueError("EXACT_ROOT_NEW_TIMEPLAN_REQUIRED")
    plan = json.loads(raw)
    if plan["phase"] not in {"f","p"} or plan["source_sha"] != "356f29983c904e949245aedfad464efc1bf7b63d":
        raise ValueError("EXACT_FINAL_P_TIMEPLAN_REQUIRED")
    output = {}
    for name, expected in PINS.items():
        original = (OLD / name).read_bytes()
        if digest(original) != expected or (OLD / name).is_symlink():
            raise ValueError("UNCHANGED_PUBLISHED_TRANSPORT_TEMPLATE_REQUIRED")
        if name == "790_transfer.original.py":
            output[name] = original
            continue
        text = original.decode().replace('SOURCE = "0bffe0c535e5897890aebf30879fdd3839dc52d6"', 'SOURCE = "' + plan["source_sha"] + '"')
        text = text.replace("CAP = 4 * 1024 * 1024", "CAP = 2_000_000")
        text = text.replace("NEUTRAL_772_INPUTS_V2_0B_V24", "NEUTRAL_753_INPUTS_V1")
        if name == "policy_790.py":
            text = text.replace("def load_policy(stop):", 'COST_STOP = ' + repr(plan["cost_stop_utc"]) + '\n\ndef load_policy(stop):\n    if stop != COST_STOP:\n        raise ValueError("EXACT_FROZEN_NEW_C_REQUIRED")')
        if name == "five_files.py":
            text = text.replace("def remaining(stop):", 'COST_STOP = ' + repr(plan["cost_stop_utc"]) + '\n\ndef remaining(stop):\n    need(stop == COST_STOP, "EXACT_FROZEN_NEW_C_REQUIRED")')
        compile(text, name, "exec")
        output[name] = text.encode()
    if args.output.exists() or not args.output.is_absolute() or args.output.parent.resolve() != args.output.parent:
        raise ValueError("NEW_CANONICAL_TRANSPORT_DIRECTORY_REQUIRED")
    args.output.mkdir(mode=0o700)
    for name, value in output.items():
        fd = os.open(args.output / name, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o600)
        with os.fdopen(fd, "wb") as stream:
            stream.write(value)
    metadata = {"kind": "final-neutral-transport-profile-v1", "source_sha": plan["source_sha"],
                "cost_stop_utc": plan["cost_stop_utc"], "timeplan_sha256": args.timeplan_sha256,
                "original_core_sha256": PINS["790_transfer.original.py"], "crypto_changed": False, "cap": 2_000_000,
                "files": {n: {"bytes": len(value), "sha256": digest(value)} for n, value in output.items()}, "executed": False}
    (args.output / "manifest.PUBLIC.json").write_text(json.dumps(metadata, sort_keys=True, indent=2) + "\n")
    (args.output / "manifest.PUBLIC.json").chmod(0o600)
    return metadata


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--timeplan", type=Path, required=True)
    p.add_argument("--timeplan-sha256", required=True)
    p.add_argument("--output", type=Path, required=True)
    os.umask(0o077)
    print(json.dumps(derive(p.parse_args())))


if __name__ == "__main__":
    main()
