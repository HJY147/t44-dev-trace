"""Detach the exact public direct runner; keep controller writes outside its workspace."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys


def put(path, value):
    with path.open("x") as stream:
        json.dump(value, stream)
        stream.write("\n")
    path.chmod(0o600)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--workspace", type=Path, required=True)
    p.add_argument("--inputs", type=Path, required=True)
    p.add_argument("--channel", type=Path, required=True)
    p.add_argument("--shell-sha256", required=True)
    p.add_argument("--worker", action="store_true")
    a = p.parse_args()
    os.umask(0o077)
    script = a.workspace / "public/DIRECT_PRESSURE.sh"
    if not all(x.is_absolute() for x in (a.workspace, a.inputs, a.channel)):
        raise ValueError("ABSOLUTE_PATHS_REQUIRED")
    if a.channel.is_relative_to(a.workspace):
        raise ValueError("CONTROLLER_MUST_BE_OUTSIDE_WORKSPACE")
    if hashlib.sha256(script.read_bytes()).hexdigest() != a.shell_sha256:
        raise ValueError("EXACT_DIRECT_SHELL_REQUIRED")
    if not a.inputs.is_file() or a.inputs.is_symlink():
        raise ValueError("INPUT_FILE_REQUIRED")
    if a.worker:
        with (a.channel / "stdout.private").open("xb") as out, (a.channel / "stderr.private").open("xb") as err:
            result = subprocess.run(["sh", str(script), str(a.workspace), str(a.inputs)],
                                    stdin=subprocess.DEVNULL, stdout=out, stderr=err)
        put(a.channel / "wrapper-exit.PUBLIC.json", {
            "exit_code": result.returncode,
            "exited_utc": datetime.now(timezone.utc).isoformat(),
            "classification": "DIAGNOSTIC_PRESSURE_NOT_FORMAL_ACCEPTANCE",
            "automatic_vm_shutdown": False,
        })
        return
    a.channel.mkdir(mode=0o700)
    argv = [sys.executable, "-B", str(Path(__file__).resolve()),
            "--workspace", str(a.workspace), "--inputs", str(a.inputs),
            "--channel", str(a.channel), "--shell-sha256", a.shell_sha256, "--worker"]
    process = subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL, start_new_session=True)
    put(a.channel / "launch.PUBLIC.json", {"pid": process.pid, "actual_barrier_observed": False})
    print(json.dumps({"status": "DIRECT_RUNNER_DISPATCHED", "pid": process.pid}))


if __name__ == "__main__":
    main()
