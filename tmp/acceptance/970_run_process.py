"""Run a public process against the dedicated acceptance snapshot without printing credentials."""

import json
import os
import subprocess
import sys
from pathlib import Path

from sqlalchemy import URL

ROOT = Path(__file__).resolve().parents[2]
RUNTIME = ROOT / ".agent-worktrees/.runtime"


def main():
    arguments = sys.argv[1:]
    if not arguments or arguments[0] not in {"cli", "messaging", "scheduling"}:
        raise SystemExit("Choose cli, messaging or scheduling; acceptance environment only")
    manifest = json.loads((RUNTIME / "acceptance-api.json").read_text())
    credentials = json.loads((RUNTIME / "mysql-8.4/credentials.json").read_text())
    url = URL.create("mysql+pymysql", database="t44_acceptance", **credentials)
    environment = {
        **os.environ,
        "PYTHONPATH": str(Path(manifest["snapshot_path"]) / "backend"),
        "DATABASE_URL": url.render_as_string(hide_password=False),
        "T44_DATABASE": "t44_acceptance",
        "T44_SESSION_TTL_SECONDS": "86400",
        "AMQP_URL": "amqp://unavailable:unavailable@127.0.0.1:13307/t44_acceptance",
    }
    return subprocess.run(
        [sys.executable, "-m", "t44." + arguments[0], *arguments[1:]],
        cwd=manifest["snapshot_path"],
        env=environment,
        check=False,
    ).returncode


if __name__ == "__main__":
    raise SystemExit(main())
