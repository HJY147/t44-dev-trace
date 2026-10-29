"""Run only published local backend checks, without cloud/network/session operations."""

import json
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "agents/backend/neutral-r30-cas"
commands = [
    [
        sys.executable,
        "-m",
        "pytest",
        "-q",
        "tmp/756_backend_neutral_cas_r30/756_conflict.py",
        "tmp/756_backend_neutral_cas_r30/756_regression.py",
        "tmp/756_backend_neutral_cas_r30/756_runtime_entry.py",
        "--junitxml=agents/backend/neutral-r30-cas/local-all.xml",
    ],
    [
        sys.executable,
        "-m",
        "ruff",
        "check",
        "--config",
        "backend/pyproject.toml",
        "agents/backend/neutral-r30-cas",
        "tmp/756_backend_neutral_cas_r30",
    ],
    [
        sys.executable,
        "-m",
        "ruff",
        "format",
        "--check",
        "--config",
        "backend/pyproject.toml",
        "agents/backend/neutral-r30-cas",
        "tmp/756_backend_neutral_cas_r30",
    ],
    ["git", "diff", "--check"],
    [
        "git",
        "diff",
        "--exit-code",
        "686d79da3967123be7a3c24d6740d77be008c1bb",
        "--",
        "agents/backend/neutral-r30",
        "agents/backend/neutral-transport-r30",
        "tmp/759_backend_neutral_r30",
        "tmp/758_backend_transport_r30",
        "backend",
        "frontend",
        "specs",
    ],
]


def main():
    environment = dict(os.environ, PYTHONPATH=str(ROOT / "backend"))
    records = []
    for command in commands:
        record = {"command": command, "started_at": datetime.now(UTC).isoformat()}
        result = subprocess.run(command, cwd=ROOT, env=environment, capture_output=True, text=True)
        record.update(
            exit_code=result.returncode,
            stdout=result.stdout,
            stderr=result.stderr,
            finished_at=datetime.now(UTC).isoformat(),
        )
        records.append(record)
    (HERE / "verification.json").write_text(
        json.dumps(
            {
                "scope": "LOCAL_PROJECT_RUNTIME_ONLY_NO_DOCKER_IMAGE_CLOUD_SUT_OR_SESSIONS",
                "invocation": [sys.executable, "-B", str(Path(__file__).resolve())],
                "checks": records,
            },
            indent=2,
        )
        + "\n"
    )
    (HERE / "local-all.log").write_text(records[0]["stdout"] + records[0]["stderr"])
    for record in records:
        print(json.dumps(record, ensure_ascii=False))
    raise SystemExit(any(record["exit_code"] for record in records))


if __name__ == "__main__":
    main()
