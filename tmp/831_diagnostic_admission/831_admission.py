"""Validate one bounded developer diagnostic on a fresh local GitHub service."""

import hashlib
import json
import os
import re
import subprocess
from pathlib import Path
from urllib.parse import urlsplit


def main():
    root = Path(__file__).resolve().parents[2]
    request_path = root / "records/diagnostics/20261025/request-before.json"
    request = json.loads(request_path.read_text())
    if request["authorized"] is not True or request["mode"] != "mysql":
        raise ValueError("Explicit developer diagnostic admission required")
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", request["request_id"]):
        raise ValueError("Invalid fixed diagnostic request id")
    if os.environ.get("CI") != "true" or request["samples"] != 12:
        raise ValueError("Only the bounded fresh CI plan is admitted")
    target = urlsplit(os.environ.get("DATABASE_URL", ""))
    if (
        target.scheme != "mysql+pymysql"
        or target.hostname not in {"127.0.0.1", "localhost"}
        or target.path != "/t44_diagnostics"
        or os.environ.get("T44_DATABASE") != "t44_diagnostics"
        or request["database"] != "t44_diagnostics"
    ):
        raise ValueError("Target is not the dedicated local CI database")
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    if head != os.environ.get("GITHUB_SHA"):
        raise ValueError("Actual checkout differs from event source")
    base = request["application_ref"]
    if not re.fullmatch(r"[0-9a-f]{40}", base):
        raise ValueError("An exact application source is required")
    subprocess.run(
        ["git", "diff", "--exit-code", base, "HEAD", "--", "backend", "frontend", "specs/contracts", "specs/database"],
        cwd=root,
        check=True,
    )
    hashes = {}
    for name, expected in request["tools"].items():
        if name not in {
            "tmp/834_backend_performance/834_request_profile.py",
            "tmp/833_database_performance/833_database_trace.py",
        }:
            raise ValueError("Tool is outside the fixed diagnostic allowlist")
        data = (root / name).read_bytes()
        committed = subprocess.check_output(["git", "show", f"HEAD:{name}"], cwd=root)
        actual = hashlib.sha256(data).hexdigest()
        if data != committed or actual != expected:
            raise ValueError("Diagnostic tool is dirty or differs from admitted hash")
        hashes[name] = actual
    if len(hashes) != 2:
        raise ValueError("Both exact diagnostic components are required")
    receipt = {
        "request_id": request["request_id"],
        "checkout": head,
        "application_ref": base,
        "tools": hashes,
        "database": "t44_diagnostics",
        "admitted": True,
        "formal_acceptance": False,
        "private_environment_loaded": False,
    }
    folder = root / "reports/diagnostics"
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / "admission-before.json"
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "w") as stream:
        stream.write(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt))


if __name__ == "__main__":
    main()
