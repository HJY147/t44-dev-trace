"""Exact fresh-CI identity checks before any dependency/database activity."""

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

BASE = "ade5e4c1998b4c2f014afde8c011645c6c5a7412"
CANDIDATE = "c8cea7e82805de5283ce67501769fa9a4efc1047"
TOOLS = {
    "tmp/833_database_performance/833_mysql_lock_probe.py": "bf9bbedd1dd09196c99ca986a3072a3a506b5b9ffda38f48fc1e5dcd11af37a4",
    "tmp/834_backend_performance/834_shared_gate_http.py": "f77f2872fe6dfb8230fec6edb24be5fdcbfe048bf83c4ed319e1a6c7e713caff",
}
ROOTS = (
    "backend/t44",
    "backend/requirements.lock",
    "frontend/src",
    "database",
    "specs/contracts",
)


def require_environment(mode, env):
    if mode not in {"baseline", "candidate", "http"}:
        raise ValueError("Unknown finite diagnostic mode")
    database = "t44_gate_http" if mode == "http" else "t44_diagnostics"
    expected = {
        "CI": "true",
        "GITHUB_REPOSITORY": "HJY147/t44-dev-trace",
        "GITHUB_REF": "refs/heads/codex/lock-diagnostics-20261025",
        "T44_DATABASE": database,
        "DATABASE_URL": f"mysql+pymysql://t44:diag-app-disposable@127.0.0.1:3306/{database}",
    }
    if any(env.get(key) != value for key, value in expected.items()):
        raise ValueError("Exact disposable CI target required")
    return database


def main(mode):
    root = Path(__file__).resolve().parents[2]
    database = require_environment(mode, os.environ)

    def git(*args):
        return subprocess.check_output(["git", *args], cwd=root)

    head = git("rev-parse", "HEAD").decode().strip()
    if head != os.environ["GITHUB_SHA"]:
        raise ValueError("Actual checkout mismatch")
    reference = BASE if mode == "baseline" else CANDIDATE
    names = (
        git("ls-tree", "-r", "--name-only", reference, "--", *ROOTS)
        .decode()
        .splitlines()
    )
    if (
        names
        != git("ls-tree", "-r", "--name-only", "HEAD", "--", *ROOTS)
        .decode()
        .splitlines()
    ):
        raise ValueError("Application path inventory mismatch")
    for name in names:
        path = root / name
        if path.is_symlink() or path.read_bytes() != git("show", f"{reference}:{name}"):
            raise ValueError(f"Application bytes mismatch: {name}")
    for name, digest in TOOLS.items():
        path = root / name
        raw = path.read_bytes()
        if path.is_symlink() or hashlib.sha256(raw).hexdigest() != digest:
            raise ValueError(f"Tool hash mismatch: {name}")
        if raw != git("show", f"HEAD:{name}"):
            raise ValueError("Tool differs from checkout")
    request = json.loads(
        (root / "records/diagnostics/20261025/request-locks.json").read_text()
    )
    if request != {
        "baseline": BASE,
        "candidate": CANDIDATE,
        "modes": ["baseline", "candidate", "http"],
        "finite_development_only": True,
        "execution_nonce": "locks-20261025-02",
    }:
        raise ValueError("Explicit finite request mismatch")
    output = root / f"reports/lock-diagnostics/{mode}/admission.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "w") as stream:
        json.dump(
            {
                "checkout": head,
                "application_reference": reference,
                "mode": mode,
                "database": database,
                "tools": TOOLS,
                "application_files_checked": len(names),
                "formal_acceptance": False,
            },
            stream,
            indent=2,
        )


if __name__ == "__main__":
    main(sys.argv[1])
