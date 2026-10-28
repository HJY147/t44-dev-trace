"""LOAD metadata-only PID namespace mapping, before any callback preparation."""

import argparse
import os
import platform
import subprocess
from pathlib import Path

from bridge_common import Clock, canonical, parse, read, require, reserve, utc
from bridge_load import DockerProcObserver, proc_stat


def discover(container_id, grant, launch, command=None, proc_root=Path("/proc")):
    command = command or subprocess.check_output
    info = parse(
        command(
            ["docker", "--context", "default", "inspect", "--format", "{{json .}}", container_id],
            timeout=5,
        )
    )
    require(
        info["Id"] == container_id and info["State"]["Running"] is True,
        "ACTUAL_OWNED_CONTAINER_REQUIRED",
    )
    pids = (
        command(["docker", "--context", "default", "top", container_id, "-eo", "pid"], timeout=5)
        .decode()
        .splitlines()[1:]
    )
    matches = []
    for line in pids:
        pid = int(line.strip())
        folder = proc_root / str(pid)
        values = {
            x.split(":", 1)[0]: x.split(":", 1)[1].split()
            for x in (folder / "status").read_text().splitlines()
            if ":" in x
        }
        if (
            int(values["NSpid"][-1]) == launch["supervisor_pid"]
            and int(values["NSpgid"][-1]) == launch["owned_pgid"]
        ):
            metadata = proc_stat((folder / "stat").read_text())
            matches.append((pid, metadata, int(values["Uid"][1])))
    require(len(matches) == 1, "ONE_ACTUAL_SUPERVISOR_PID_MAPPING_REQUIRED")
    pid, sup, uid = matches[0]
    init_pid = info["State"]["Pid"]
    initial = proc_stat((proc_root / str(init_pid) / "stat").read_text())
    owner = {
        "container_id": container_id,
        "init_host_pid": init_pid,
        "init_start_ticks": initial["start_ticks"],
        "supervisor_host_pid": pid,
        "supervisor_start_ticks": sup["start_ticks"],
        "supervisor_host_pgid": sup["pgid"],
        "supervisor_container_pid": launch["supervisor_pid"],
        "supervisor_container_pgid": launch["owned_pgid"],
        "operator_uid": uid,
    }
    observation = DockerProcObserver(command, proc_root).observe(owner, grant)
    return owner, observation


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--container-id", required=True)
    for name in ("grant", "launch", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    for name in ("grant-sha256", "launch-sha256"):
        parser.add_argument("--" + name, required=True)
    args = parser.parse_args()
    require(os.geteuid() == 0 and platform.system() == "Linux", "LOAD_ROOT_LINUX_REQUIRED")
    grant = parse(read(args.grant, args.grant_sha256))
    launch = parse(read(args.launch, args.launch_sha256))
    owner, observation = discover(args.container_id, grant, launch)
    result = {
        "kind": "PUBLIC_SCOPE_OWNER_LOCATOR_NOT_CONTINUOUS_LIVENESS",
        "owner": owner,
        "observation": observation,
        "observed_utc": utc(Clock().now()),
    }
    reserve(args.output, canonical(result) + b"\n")
    print(canonical(result).decode())


if __name__ == "__main__":
    try:
        main()
    except Exception as error:  # noqa: BLE001 -- no raw Docker output in error messages.
        print(
            canonical(
                {"kind": "PUBLIC_SCOPE_OWNER_REFUSED", "error_type": type(error).__name__}
            ).decode()
        )
        raise SystemExit(1) from None
