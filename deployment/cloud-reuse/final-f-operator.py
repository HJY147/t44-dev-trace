"""One public neutral request -> one atomic response; only existing owned F containers."""
import argparse
import hashlib
import http.client
import importlib.util
import json
import os
import re
import ssl
import stat
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

ACTIONS = ("scheduler_restart", "mq_stop", "mq_start", "api_restart", "api_ready_wait")
BUDGET = "9e98632fa1885bf4327b04a95daeba5cee4ad909b536e91ac8b11a1e58488a61"
KIND = "r30-official-backend-production-entry-window-v1"
DOCKER = ["docker", "--context", "default"]


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def utc(text):
    if not re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d+)?(?:Z|\+00:00)", text or ""):
        raise ValueError("EXACT_UTC_REQUIRED")
    return datetime.fromisoformat(text.replace("Z", "+00:00")).timestamp()  # noqa: FURB162 -- APP Python3.10


def stamp():
    return datetime.now(timezone.utc).isoformat()  # noqa: UP017 -- APP Python3.10


def pinned(path, expected):
    s = path.lstat()
    if (not path.is_absolute() or path.resolve() != path or not stat.S_ISREG(s.st_mode) or s.st_nlink != 1
            or s.st_size > 4 * 1024 * 1024 or not re.fullmatch(r"[0-9a-f]{64}", expected or "")):
        raise ValueError("ORIGINAL_CANONICAL_PINNED_INPUT_REQUIRED")
    raw = path.read_bytes()
    if sha(raw) != expected:
        raise ValueError("INPUT_RAW_HASH_CHANGED")
    return raw


def module(path, expected):
    pinned(path, expected)
    spec = importlib.util.spec_from_file_location("f_operator_" + path.stem.replace("-", "_"), path)
    obj = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obj)
    return obj


def context(args):
    if os.geteuid() != 0:
        raise ValueError("ROOT_APP_OPERATOR_REQUIRED")
    profile = json.loads(pinned(args.gen_profile, args.gen_profile_sha256))
    source = json.loads(pinned(args.source_profile, args.source_profile_sha256))
    gen = module(args.phase_dir / "controller.py", profile["derived_files"]["generation.py"]["sha256"])
    lib, value = gen.phase_binding(args.phase_dir, args.binding_sha256)
    if (args.phase_dir / "F-CLOSED").exists():
        raise ValueError("F_CLOSED_BEFORE_FIRST_P_NO_RESTART")
    budget = gen.budget_module(args.phase_dir)
    if (value["phase"] != "f" or value["generation_kind"] != KIND or budget.KIND != KIND
            or gen.BUDGET_SHA != BUDGET or source.get("root_approved") is not True
            or source["source_sha"] != value["source_sha"] or profile["source_sha"] != value["source_sha"]
            or profile["run_id"] + "-f" != value["project"].removeprefix("t44-cloud-")
            or source["backend_config_id"] != value["config_ids"]["backend"]):
        raise ValueError("EXACT_APPROVED_F_ONLY_SOURCE_GEN_AND_9E_BUDGET_REQUIRED")
    return gen, lib, value, budget, profile


def request(args, profile, value):
    raw = pinned(args.request_file, args.request_sha256)
    row = json.loads(raw)
    run = profile["run_id"]
    if (row.get("schema") != "753-neutral-operator-request-v1" or row.get("run_id") != run
            or row.get("phase") != "f" or not re.fullmatch(re.escape(run) + r"-\d{3}", row.get("request_id", ""))
            or args.request_file.name != row["request_id"] + ".request.json" or row.get("action") not in ACTIONS):
        raise ValueError("ONLY_FIXED_PUBLISHED_F_OPERATOR_REQUESTS")
    requested, end, now = utc(row["requested_utc"]), utc(row["deadline_utc"]), time.time()
    if not requested <= now < end <= requested + 180:
        raise ValueError("ONE_REQUEST_MAX180_SECONDS_NO_REPLAY")
    plan=json.loads(pinned(args.timeplan,args.timeplan_sha256))
    started=utc(args.f_started_utc)
    if (plan.get("kind")!="final-immutable-timeplan-v1" or plan["phase"]!="f" or plan["run_id"]!=run
            or plan["source_sha"]!=value["source_sha"] or plan["stop_utc"]!=value["stop_utc"]
            or plan["absolute_cost_cutoff_utc"]!=args.cost_cutoff_utc or not utc(plan["t0_utc"])<=started<=now):
        raise ValueError("SAME_F_TIMEPLAN_ACTUAL_START_AND_SOURCE_REQUIRED")
    maximum=min(1500,utc(value["stop_utc"])-started-120)
    end = min(end, started+maximum, utc(plan["cost_stop_utc"])-60, utc(args.cost_cutoff_utc)-60)
    if end <= now:
        raise ValueError("F_TOTAL2400_AND_COST_RESERVE_EXPIRED")
    return row, end


def command(args, argv, label, end):
    timeout = end - time.time()
    if timeout < 1:
        raise TimeoutError("OPERATOR_DEADLINE")
    result = subprocess.run(argv, check=False, capture_output=True, timeout=timeout,
                            env={k: v for k, v in os.environ.items() if k in {"PATH", "HOME", "LANG"}})
    facts = {"argv": argv, "returncode": result.returncode}
    for name, data in (("stdout", result.stdout), ("stderr", result.stderr)):
        path = args.evidence_dir / (label + "." + name + ".private")
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o600)
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
        facts[name] = {"path": str(path), "sha256": sha(data), "bytes": len(data)}
    if result.returncode:
        raise RuntimeError("FIXED_OPERATOR_COMMAND_NONZERO")
    return facts


def ready(value, phase, end):
    ca = phase / "tls/ca.pem"
    if sha(ca.read_bytes()) != value["tls"]["ca_sha256"]:
        raise ValueError("ORIGINAL_F_CA_REQUIRED")
    ctx = ssl.create_default_context(cafile=str(ca))
    while time.time() < end:
        conn = http.client.HTTPSConnection(value["app_private_ip"], value["tls_port"], context=ctx, timeout=min(5, end - time.time()))
        try:
            conn.request("GET", "/api/v1/projects", headers={"Accept": "application/json", "Connection": "close"})
            response = conn.getresponse()
            response.read(1024)
            if response.status == 401:
                return {"https_status": 401, "CA_IP_checked": True, "credentials_sent": False, "observed_utc": stamp()}
        except (OSError, http.client.HTTPException):
            pass
        finally:
            conn.close()
        time.sleep(min(1, max(0, end - time.time())))
    raise TimeoutError("ACTUAL_F_API_READY_NOT_OBSERVED")


def operate(args, row, end, gen, lib, value, budget):
    role = {"scheduler_restart": "scheduler", "mq_stop": "rabbitmq", "mq_start": "rabbitmq", "api_restart": "api", "api_ready_wait": "api"}[row["action"]]
    before = gen.live(lib, value, role)
    if before.get("absent"):
        raise ValueError("EXISTING_OWNED_F_ROLE_REQUIRED_NO_ADOPTION")
    facts = {"before": before, "commands": []}
    action = row["action"]
    if action == "api_ready_wait":
        facts["readiness"] = ready(value, args.phase_dir, end)
    else:
        cid = before["container_id"]
        if action.endswith("restart") or action == "mq_stop":
            if before["state"]["Running"] is not True:
                raise ValueError("ACTUAL_RUNNING_F_ROLE_REQUIRED_BEFORE_STOP")
            facts["commands"].append(command(args, [*DOCKER, "stop", "--time", "10", cid], "stop", end))
        if action.endswith("restart") or action == "mq_start":
            with budget.operation_lock(args.phase_dir, args.binding_sha256, timeout_seconds=min(10, max(0, end - time.time()))):
                _, current = gen.phase_binding(args.phase_dir, args.binding_sha256)
                if current != value:
                    raise ValueError("IMMUTABLE_F_BINDING_CHANGED")
                budget.verify_runtime_environment(value, lambda r: gen.live(lib, value, r))
                facts["actual_admit"] = budget.admit(args.phase_dir, args.binding_sha256, value,
                    lambda r: gen.live(lib, value, r), args.budget_receipt, args.budget_receipt_sha256)
                facts["commands"].append(command(args, [*DOCKER, "start", cid], "start", end))
        after = gen.live(lib, value, role)
        if after.get("absent") or after["container_id"] != cid or after["state"]["Running"] is not (action != "mq_stop"):
            raise ValueError("REQUESTED_OWNED_F_STATE_NOT_OBSERVED")
        facts["after"] = after
    return facts


def respond(args):
    raw = json.loads(pinned(args.request_file, args.request_sha256))
    target = args.request_file.with_name(args.request_file.name.removesuffix(".request.json") + ".response.json")
    if target.exists():
        raise ValueError("EXISTING_RESPONSE_NO_REPLAY")
    claim = args.request_file.with_name(args.request_file.name + ".operator.claim")
    fd = os.open(claim, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "w") as stream:
        stream.write(args.request_sha256 + "\n")
    response = {"request_id": raw.get("request_id"), "action": raw.get("action"), "success": False, "observed_utc": stamp(),
                "facts": {"private_evidence_prefix": str(args.evidence_dir)}}
    args.evidence_dir.mkdir(mode=0o700)
    try:
        gen, lib, value, budget, profile = context(args)
        row, end = request(args, profile, value)
        response["facts"] = operate(args, row, end, gen, lib, value, budget)
        response["success"] = True
    except Exception as error:  # noqa: BLE001 -- only safe class published; preserve private evidence prefix
        response["error"] = type(error).__name__
    response["observed_utc"] = stamp()
    temp = args.evidence_dir / "response.json"
    temp.write_text(json.dumps(response, sort_keys=True, indent=2) + "\n")
    temp.chmod(0o600)
    os.chown(temp, 10001, 10001)
    os.link(temp, target)  # Atomic create; never overwrite an existing response.
    return {"status": "RESPONDED", "path": str(target), "sha256": sha(target.read_bytes())}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for key in ("phase-dir", "gen-profile", "source-profile", "request-file", "evidence-dir", "budget-receipt","timeplan"):
        p.add_argument("--" + key, type=Path, required=True)
    for key in ("binding-sha256", "gen-profile-sha256", "source-profile-sha256", "request-sha256", "budget-receipt-sha256", "f-started-utc", "cost-cutoff-utc","timeplan-sha256"):
        p.add_argument("--" + key, required=True)
    args = p.parse_args()
    os.umask(0o077)
    print(json.dumps(respond(args)))


if __name__ == "__main__":
    main()
