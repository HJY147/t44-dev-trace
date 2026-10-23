"""Fail explicitly on missing implementation; no success placeholders or test stubs."""

import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPORTS = ROOT / os.environ.get("T44_CI_REPORTS", "reports/ci")


def require_application() -> list[str]:
    required = ["backend/pyproject.toml", "backend/requirements.lock", "backend/t44", "backend/tests",
                "specs/contracts/openapi.json", "specs/database/schema.sql"]
    missing = [name for name in required if not (ROOT / name).exists()]
    if not list((ROOT / "backend/t44").rglob("*.py")):
        missing.append("production Python implementation under backend/t44")
    if not list((ROOT / "backend/tests").rglob("test_*.py")):
        missing.append("real application tests under backend/tests")
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / "preflight.json").write_text(json.dumps({"missing": missing, "ready": not missing}, indent=2) + "\n")
    for item in missing:
        print(f"MISSING IMPLEMENTATION: {item}")
    return missing


if __name__ == "__main__":
    raise SystemExit(1 if require_application() else 0)
