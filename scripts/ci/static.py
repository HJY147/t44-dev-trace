"""Static gate records actual results; a missing app keeps the product gate red."""

import json
import subprocess
import sys

from preflight import REPORTS, ROOT, require_application


def main() -> int:
    REPORTS.mkdir(parents=True, exist_ok=True)
    commands = [
        [sys.executable, "scripts/ci/validate_config.py"],
        [sys.executable, "-m", "pytest", "-c", "backend/pyproject.toml", "tmp/deployment/997_ops.py", "tmp/deployment/971_credentials.py", "tmp/ci/996_gates.py", "-q"],
        [sys.executable, "-m", "ruff", "check", "--config", "scripts/ci/ruff.toml", "deployment", "scripts/ci", "tmp/deployment", "tmp/ci"],
    ]
    missing = require_application()
    if not missing:
        commands.extend([
            [sys.executable, "-m", "ruff", "check", "--config", "scripts/ci/ruff.toml", "backend/t44", "tmp/backend"],
            [sys.executable, "-m", "bandit", "-r", "backend/t44", "-f", "json", "-o", str(REPORTS / "bandit.json")],
        ])
    results = []
    for index, command in enumerate(commands):
        print("RUN", " ".join(command), flush=True)
        completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
        (REPORTS / f"static-{index}.log").write_text(completed.stdout + completed.stderr)
        print(completed.stdout + completed.stderr, end="")
        results.append({"command": command, "exit_code": completed.returncode})
    (REPORTS / "static.json").write_text(json.dumps({"missing": missing, "commands": results}, indent=2) + "\n")
    return int(bool(missing) or any(item["exit_code"] for item in results))


if __name__ == "__main__":
    raise SystemExit(main())
