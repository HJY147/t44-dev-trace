"""Capture actual local owner checks; never connect external components."""

import json
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "agents/database/dry-r29b"
COMMANDS = EVIDENCE / "commands.json"


def run(label, arguments):
    environment = dict(os.environ, PYTHONPATH="backend")
    for key in ("DATABASE_URL", "T44_TEST_CREDENTIALS", "CI"):
        environment.pop(key, None)
    started = datetime.now(UTC).isoformat()
    result = subprocess.run(arguments, cwd=ROOT, env=environment, capture_output=True, check=False)
    (EVIDENCE / f"{label}.stdout.txt").write_bytes(result.stdout)
    (EVIDENCE / f"{label}.stderr.txt").write_bytes(result.stderr)
    record = dict(
        label=label,
        command=arguments,
        cwd=str(ROOT),
        source=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip(),
        started_utc=started,
        exit=result.returncode,
        environment=dict(PYTHONPATH="backend"),
        unset_environment=["DATABASE_URL", "T44_TEST_CREDENTIALS", "CI"],
        stdout=f"{label}.stdout.txt",
        stderr=f"{label}.stderr.txt",
    )
    (EVIDENCE / f"{label}.command.json").write_text(
        json.dumps(record, ensure_ascii=False, indent=2) + "\n"
    )
    records = json.loads(COMMANDS.read_text()) if COMMANDS.exists() else []
    records.append(record)
    COMMANDS.write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(dict(label=label, exit=result.returncode)))
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(run(sys.argv[1], sys.argv[2:]))
