"""Fresh 0b/C policy around the pinned, byte-unchanged public 790 transport module."""

import argparse
import contextlib
import hashlib
import importlib.util
import io
import json
import os
from datetime import datetime, timezone
from pathlib import Path

SOURCE = "0bffe0c535e5897890aebf30879fdd3839dc52d6"
ORIGINAL_SHA = "8600110b54f45240a6e45ea62c9be6f567529e374807d0ca593dde3fd7605db7"
CAP = 4 * 1024 * 1024


def load_policy(stop):
    deadline = datetime.fromisoformat(stop.replace("Z", "+00:00"))
    if (
        not stop.endswith("Z")
        or not 0 < (deadline - datetime.now(timezone.utc)).total_seconds() <= 3600
    ):
        raise ValueError("FRESH_EXPLICIT_C_REQUIRED")
    path = Path(__file__).with_name("790_transfer.original.py")
    if path.is_symlink() or hashlib.sha256(path.read_bytes()).hexdigest() != ORIGINAL_SHA:
        raise ValueError("EXACT_ORIGINAL_790_REQUIRED")
    spec = importlib.util.spec_from_file_location("original_790_transport", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.SOURCE, module.STOP = SOURCE, deadline
    return module


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cost-stop-utc", required=True)
    args, remainder = parser.parse_known_args()
    module = load_policy(args.cost_stop_utc)
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        module.main(remainder)
    records = [json.loads(line) for line in output.getvalue().splitlines()]
    # Never echo decrypted private inputs or duplicate the potentially large opaque stream.
    public = records[0]
    if public["kind"] == "PUBLIC-790-TRANSFER":
        directory = Path(remainder[remainder.index("--output-dir") + 1])
        if (directory / "transfer.public.jsonl").stat().st_size > min(CAP, module.LIMIT):
            raise ValueError("OPAQUE_STREAM_EXCEEDS_ORIGINAL_OPEN_CAP_PREFIX_PRESERVED")
        public = {
            key: public[key]
            for key in (
                "kind",
                "public_record_sha256",
                "binding_sha256",
                "opaque_sha256",
                "opaque_chars",
            )
        }
        wire = (directory / "transfer.public.jsonl").read_bytes()
        public["transfer_file_bytes"] = len(wire)
        public["transfer_file_sha256"] = hashlib.sha256(wire).hexdigest()
    print(json.dumps(public, sort_keys=True))


if __name__ == "__main__":
    os.umask(0o077)
    main()
