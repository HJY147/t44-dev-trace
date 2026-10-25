"""Start only the reviewed environment provider after the exact PUBLIC receipt appears."""

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

PUBLIC = Path(
    "/Users/yang/Desktop/nothing/软件开发大作业/tmp/829_independent_acceptance_20261025/execution-v8-fresh/PUBLIC"
)
grant_path = Path(sys.argv[1])
grant = json.loads(grant_path.read_text())
stop = min(time.time() + 600, datetime.fromisoformat(grant["expires_at"]).timestamp())
if grant.get("admitted") is not True or grant.get("phase") != "functional":
    raise ValueError("Exact functional admission required")
while time.time() < stop:
    for path in (PUBLIC / "runtime").glob("*.receipt.PUBLIC.json"):
        if path.is_symlink() or path.stat().st_size > 32768:
            continue
        receipt = json.loads(path.read_text())
        if (
            receipt.get("tool_freeze_sha256") != grant["tool_freeze_sha256"]
            or receipt.get("expires_at") != grant["expires_at"]
        ):
            continue
        os.kill(receipt["supervisor_pid"], 0)
        os.kill(receipt["child_pid"], 0)
        helper = Path(__file__).with_name("815_provider_v8.py")
        print(
            json.dumps({"actual_receipt": str(path), "provider_pid": os.getpid()}),
            flush=True,
        )
        os.execv(
            sys.executable,
            [
                sys.executable,
                str(helper),
                "--grant",
                str(grant_path),
                "--supervisor-receipt",
                str(path),
            ],
        )
    time.sleep(0.05)
raise TimeoutError("No exact active functional receipt before provider deadline")
