"""Read-only, field-scoped metadata for the current neutral Compose environment."""

import json
import os
import re
import subprocess
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from urllib.parse import urlsplit

SERVICES = ("mysql", "rabbitmq", "api", "consumer", "scheduler", "web")
RESOURCE_FIELDS = ("CpuQuota", "CpuPeriod", "NanoCpus", "Memory", "MemorySwap", "CpusetCpus", "PidsLimit")
INSPECT_TEMPLATE = ('{"id":{{json .Id}},"project":{{json (index .Config.Labels "com.docker.compose.project")}},'
                    '"service":{{json (index .Config.Labels "com.docker.compose.service")}},'
                    '"running":{{json .State.Running}},"resources":{' +
                    ','.join('"' + key + '":{{json .HostConfig.' + key + '}}' for key in RESOURCE_FIELDS) +
                    '},"health_interval_ns":{{if .Config.Healthcheck}}{{json .Config.Healthcheck.Interval}}'
                    '{{else}}null{{end}}}')
API_SCRIPT = '''import json,os
from pathlib import Path
supervisors=[]; spawned=0; unreadable=0
for p in Path('/proc').iterdir():
 if not p.name.isdecimal(): continue
 try: args=(p/'cmdline').read_bytes().split(b'\\0'); args=[a.decode('utf-8',errors='replace') for a in args if a]
 except FileNotFoundError: continue
 except (PermissionError,OSError): unreadable+=1; continue
 if 't44.api:app' in args and 'uvicorn' in args:
  try: workers=int(args[args.index('--workers')+1])
  except (ValueError,IndexError): workers=None
  supervisors.append(workers)
 if len(args)>2 and args[1]=='-c' and args[2].startswith('from multiprocessing.spawn import spawn_main;') and '--multiprocessing-fork' in args: spawned+=1
print(json.dumps({'supervisor_count':len(supervisors),'configured_workers':supervisors,'spawn_main_process_count':spawned,'unreadable_process_count':unreadable}))
'''
NGINX_FIELDS = ("worker_processes", "worker_connections", "keepalive", "proxy_connect_timeout",
                "proxy_read_timeout", "proxy_send_timeout")


def incomplete(component="control-state"):
    return {"schema_version": 1, "observation_complete": False, "started_at": datetime.now(UTC).isoformat(),
            "finished_at": None, "errors": [{"component": component, "code": "OBSERVATION_UNAVAILABLE"}]}


def capture(command):
    # Do not use Controls.compose: it persists raw stdout/stderr, including nginx -T.
    result = subprocess.run(command, capture_output=True, timeout=15, check=False)
    if result.returncode or len(result.stdout) > 2 * 1024 * 1024:
        raise ValueError("observation unavailable")
    return result.stdout


def validate_inspection(raw, container_id, project, service):
    value = json.loads(raw)
    if (value.get("id") != container_id or value.get("project") != project or value.get("service") != service
            or not re.fullmatch(r"[0-9a-f]{64}", container_id) or service not in SERVICES):
        raise ValueError("container scope mismatch")
    resources = value["resources"]
    if set(resources) != set(RESOURCE_FIELDS):
        raise ValueError("missing resource fields")
    for field in RESOURCE_FIELDS:
        item = resources[field]
        if field == "CpusetCpus":
            if not isinstance(item, str) or not re.fullmatch(r"[0-9,-]*", item):
                raise ValueError("invalid cpuset projection")
        elif item is not None and type(item) is not int:
            raise ValueError("invalid numeric projection")
    if type(value["running"]) is not bool:
        raise ValueError("invalid state projection")
    interval = value["health_interval_ns"]
    if interval is not None and (type(interval) is not int or interval < 0):
        raise ValueError("invalid probe interval")
    # Reconstruct a whitelist projection even if a caller supplies unexpected fields.
    return {"container_id": container_id, "running": value["running"],
            "host_config": {field: resources[field] for field in RESOURCE_FIELDS}, "health_interval_ns": interval}


def nginx_projection(raw):
    text = raw.decode("utf-8")
    text = re.sub(r"#.*", "", text)
    selected = {}
    for field in NGINX_FIELDS:
        values = re.findall(r"\b" + field + r"\s+([^;{}]+);", text)
        if not values or any(not re.fullmatch(r"(?:auto|[0-9]+(?:ms|s|m|h|d)?)", v.strip()) for v in values):
            raise ValueError("proxy directive unavailable")
        selected["upstream_keepalive" if field == "keepalive" else field] = sorted(set(v.strip() for v in values))
    return {"directives": selected, "source": "running container nginx -T; current config files validated; no reload",
            "limitation": "Does not prove the last reload used identical files; per-location values are listed, not guessed defaults."}


def cgroup_limits():
    """Read v2 controller limits along the current membership's visible ancestry."""
    membership = next((line.split(":", 2)[2] for line in Path("/proc/self/cgroup").read_text().splitlines()
                       if line.startswith("0::")), None)
    if membership is None:
        raise ValueError("cgroup v2 observation unavailable")
    group = PurePosixPath(membership)
    if not group.is_absolute() or ".." in group.parts:
        raise ValueError("cgroup membership unavailable")
    mounts = []
    for line in Path("/proc/self/mountinfo").read_text().splitlines():
        left, _, right = line.partition(" - ")
        fields = left.split()
        if right.split()[0] == "cgroup2" and len(fields) >= 5:
            mounts.append((PurePosixPath(fields[3]), Path(fields[4])))
    root, mount = next((root, mount) for root, mount in mounts if group.is_relative_to(root))
    current = mount / str(group.relative_to(root))
    files = ("cpu.max", "memory.max", "memory.swap.max", "pids.max", "cpuset.cpus.effective")
    observations = []
    while True:
        values = {}
        for name in files:
            path = current / name
            if path.exists():
                raw = path.read_text().strip()
                pattern = r"(?:max|[0-9]+) [0-9]+" if name == "cpu.max" else (
                    r"[0-9,-]*" if name == "cpuset.cpus.effective" else r"(?:max|[0-9]+)")
                if not re.fullmatch(pattern, raw):
                    raise ValueError("cgroup value unavailable")
                values[name] = raw
        observations.append({"ancestor_level": len(observations), "limits": values})
        if current == mount:
            break
        current = current.parent
    observed = {field for row in observations for field in row["limits"]}
    if not {"cpu.max", "memory.max", "pids.max"} <= observed:
        raise ValueError("required cgroup controllers unavailable")
    return {"version": 2, "visible_ancestry": observations,
            "meaning": "Raw visible controller values; max is that controller's setting, not infinite physical resources."}


def runner_metadata():
    cpus = os.cpu_count()
    match = re.search(r"^MemTotal:\s+(\d+) kB$", Path("/proc/meminfo").read_text(), re.MULTILINE)
    if not cpus or not match:
        raise ValueError("runner observation unavailable")
    return {"logical_cpu_count": cpus, "affinity_cpu_count": len(os.sched_getaffinity(0)),
            "visible_memory_total_bytes": int(match[1]) * 1024, "cgroup": cgroup_limits(),
            "scope": "Current command/harness runner OS view, not a physical-machine inventory."}


def api_projection(raw):
    value = json.loads(raw)
    if (set(value) != {"supervisor_count", "configured_workers", "spawn_main_process_count", "unreadable_process_count"}
            or type(value["supervisor_count"]) is not int or value["supervisor_count"] != 1
            or not isinstance(value["configured_workers"], list) or len(value["configured_workers"]) != 1
            or any(type(v) is not int or v <= 0 for v in value["configured_workers"])
            or type(value["spawn_main_process_count"]) is not int or value["spawn_main_process_count"] < 0
            or value["unreadable_process_count"] != 0):
        raise ValueError("API process observation incomplete")
    return value


def mysql_projection(raw):
    rows = raw.decode("ascii").strip().splitlines()
    if len(rows) != 2 or rows[0] != "@@max_connections" or not re.fullmatch(r"[1-9][0-9]*", rows[1]):
        raise ValueError("max_connections unavailable")
    return int(rows[1])


def collect(controls):
    report = incomplete()
    report["errors"] = []
    report["containers"] = {}
    run_id = os.environ.get("GITHUB_RUN_ID", "")
    report["github_run_id"] = run_id if re.fullmatch(r"[0-9]+", run_id) else None
    report["compose_project"] = controls.values["COMPOSE_PROJECT_NAME"]
    report["meaning"] = "Read-only snapshot, not a performance/functional verdict; no continuous traffic capture."
    report["resource_interpretation"] = "Docker 0/null/empty settings do not mean infinite CPU, memory or hardware."

    def observe(component, action):
        try:
            return action()
        except Exception:  # noqa: BLE001 -- do not expose raw driver output, paths, arguments or credentials
            report["errors"].append({"component": component, "code": "OBSERVATION_UNAVAILABLE"})
            return None

    report["runner"] = observe("runner", runner_metadata)
    docker = ["docker", "--context", controls.values["T44_DOCKER_CONTEXT"]]
    project = controls.values["COMPOSE_PROJECT_NAME"]

    def transport():
        endpoint = json.loads(capture([*docker, "context", "inspect", "--format", "{{json .Endpoints.docker.Host}} "]))
        if not isinstance(endpoint, str) or not urlsplit(endpoint).scheme:
            raise ValueError("daemon transport unknown")
        local = urlsplit(endpoint).scheme == "unix"
        return {"transport": "local-unix" if local else "non-unix", "local_unix_socket": local,
                "load_process_location": "Workflow executes the frozen Python harness on this runner; individual traffic origins are not traced",
                "services_relation": "six scoped containers queried through the same Docker context/daemon",
                "physical_colocation": "unknown; a unix socket alone does not establish physical-machine identity"}

    report["daemon_relation"] = observe("daemon-transport", transport)
    for service in SERVICES:
        def inspect_service(service=service):
            raw_id = controls.compose("ps", "-q", service, timeout=15).stdout.decode().strip()
            if not re.fullmatch(r"[0-9a-f]{64}", raw_id):
                raise ValueError("one full container ID required")
            raw = capture([*docker, "inspect", "--type", "container", "--format", INSPECT_TEMPLATE, raw_id])
            return validate_inspection(raw, raw_id, project, service)
        value = observe("container:" + service, inspect_service)
        report["containers"][service] = value
    api = report["containers"].get("api")
    web = report["containers"].get("web")
    report["api_processes"] = observe("api-processes", lambda: api_projection(capture(
        [*docker, "exec", api["container_id"], "python", "-c", API_SCRIPT]))) if api else None
    report["nginx"] = observe("nginx-directives", lambda: nginx_projection(capture(
        [*docker, "exec", web["container_id"], "nginx", "-T"]))) if web else None
    report["mysql_max_connections"] = observe("mysql-max-connections", lambda: mysql_projection(
        controls.audit("SELECT @@max_connections")))
    report["background_activity"] = {"scheduler_baseline_interval_seconds": 60,
        "scheduler_cadence_source": "neutral environment baseline, not measured traffic or an arbitrary SQL read",
        "scheduler_running": (report["containers"].get("scheduler") or {}).get("running"),
        "consumer_running": (report["containers"].get("consumer") or {}).get("running"),
        "health_probes": "Container health intervals are reported above; probes/scheduler/consumer may run during load.",
        "other_traffic": "unknown; no continuous packet capture or workload attribution performed"}
    report["observation_complete"] = not report["errors"]
    report["finished_at"] = datetime.now(UTC).isoformat()
    return report
