"""Future root-invoked APP HTTP preparation only; no cloud lifecycle, SQL or QA grant."""

import argparse
import importlib.util
import json
import os
import re
import subprocess
import time
import uuid
from datetime import datetime
from pathlib import Path

ADMIN_SHA = "8e9d024b7aa38692a633b620a23a27380d155ed7a8725f45c9ee25dac0fe4d9a"
SOURCE = "0bffe0c535e5897890aebf30879fdd3839dc52d6"
CONFIG = "sha256:8e3e2a9d1f2d4706072eb0502b041d3db49d32b7a2fc48ac6b39fc2162336845"
ALIAS = "t44-backend-r30:src-" + SOURCE + "-r30ci40833943007"
SOURCE_MANIFEST = "0c5b0c0e027578b0f62711175beac4680aab8331bfbc4af2547f02398f38cc1b"
BUNDLE = "b2db2e1c5cf56fa5df4f20f7003d44d6b3b9ab4cd484b45d921c82640295d345"
FACTORY = "daaf29d3b47ab266ae4546f001e322275db5c3c902c9f36f8b8a2528690af2ea"
DOCKER = ["docker", "--context", "default"]


def tools():
    import hashlib

    path = Path(__file__).resolve().with_name("r30-neutral-admin.py")
    if path.is_symlink() or hashlib.sha256(path.read_bytes()).hexdigest() != ADMIN_SHA:
        raise ValueError("EXACT_REVIEWED_STAGING_LIBRARY_REQUIRED")
    spec = importlib.util.spec_from_file_location("r30_http_staging", path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def deadline(text):
    if not isinstance(text, str) or not re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ", text):
        raise ValueError("EXACT_IMMUTABLE_UTC_REQUIRED")
    return datetime.fromisoformat(text.replace("Z", "+00:00")).timestamp()  # noqa: FURB162 -- APP host Python3.10


def environment():
    # Docker run has no --env/--env-file; image PYTHONPATH remains untouched.
    return {k: v for k, v in os.environ.items() if k in {"PATH", "HOME", "LANG", "LC_ALL"}}


def command(argv):
    return json.loads(subprocess.run(argv, check=True, capture_output=True, timeout=20,
                                     env=environment()).stdout)


def checked(args, a):
    a.require_host()
    raw_binding = a.pinned(args.phase_dir / "binding.json", args.binding_sha256, private=True)
    binding = json.loads(raw_binding)
    plan_raw = a.raw(args.plan, private=True)
    plan = json.loads(plan_raw)
    run, phase = plan["run_id"], binding["phase"]
    if (not re.fullmatch(r"r30[a-z0-9]{5,12}", run) or run == "r30window01" or phase not in {"p", "f"}
            or binding["source_sha"] != SOURCE or binding["generation_kind"] != a.KIND
            or binding["project"] != "t44-cloud-" + run + "-" + phase
            or binding["database"] != "t44c_" + run + "_" + phase
            or binding["source_manifest_sha256"] != SOURCE_MANIFEST
            or binding["upgrade_binding_sha256"] != BUNDLE
            or binding["config_ids"]["backend"] != CONFIG or binding["images"]["backend"]["alias"] != ALIAS
            or plan.get("schema") != "t44-neutral-r30-plan-v1" or plan.get("synthetic") is not True
            or plan.get("root_admit_preparation") is not True or plan.get("benchmark_grant_allow") is not False
            or plan["source"]["git_commit"] != SOURCE or plan["namespace"] != binding["project"]
            or plan["target"]["compose_project"] != binding["project"]
            or plan["target"]["database"] != binding["database"]
            or plan["target"]["binding_sha256"] != args.binding_sha256
            or plan["gen_binding"]["sha256"] != args.binding_sha256
            or plan["gen_binding"]["path"] != "/neutral-input/binding.json"
            or plan["window"]["stop_utc"] != binding["stop_utc"]):
        raise ValueError("ROOT_APPROVED_NEW_RUN_EXACT_SOURCE_SCOPE_BINDING_REQUIRED")
    a.pinned(args.phase_dir / "factory.py", FACTORY)
    generation = a.module(args.phase_dir / "controller.py", binding["file_hashes"]["controller.py"])
    _, actual = generation.phase_binding(args.phase_dir, args.binding_sha256)
    if actual != binding or generation.BUDGET_SHA != a.BUDGET_SHA or generation.R30_ADAPTER_SHA != a.ADAPTER_SHA:
        raise ValueError("ACTUAL_REVIEWED_GEN_CHAIN_REQUIRED")
    now = time.time()
    t0, start, end, stop, cutoff = [deadline(x) for x in (
        plan["lifecycle"]["t0_utc"], plan["window"]["start_utc"], plan["window"]["end_utc"],
        binding["stop_utc"], plan["lifecycle"]["packet_cutoff_utc"])]
    cost = deadline(plan["lifecycle"]["cost_stop_utc"])
    if (not t0 <= now < cutoff < start < end <= stop or stop != t0 + 35 * 60
            or cost != t0 + 40 * 60 or cutoff != start - 150 or not 780 <= end - start <= 900
            or cost - end < 90):
        raise ValueError("LIVE_NEW_IMMUTABLE_PACKET_WINDOW_REQUIRED")
    timeout = min(300, cutoff - now - 10, stop - now - 10)
    if timeout < 1:
        raise ValueError("BOUNDED_HTTP_AND_OWNED_STOP_RESERVE_REQUIRED")
    inputs = {"plan.json": plan_raw, "binding.json": raw_binding,
              "accounts.json": a.raw(args.accounts, private=True),
              "service.json": a.raw(args.service, private=True),
              "backend-import-receipt.json": a.raw(args.import_receipt, private=True),
              "ca.pem": a.raw(args.ca)}
    if (a.digest(inputs["backend-import-receipt.json"]) != plan["source"]["actual_loaded_receipt_sha256"]
            or a.digest(inputs["ca.pem"]) != plan["target"]["ca_sha256"]
            or plan["target"]["ca_sha256"] != binding["tls"]["ca_sha256"]):
        raise ValueError("ORIGINAL_IMPORT_AND_CA_BYTES_REQUIRED")
    receipt = json.loads(inputs["backend-import-receipt.json"])
    proof = binding["cryptographic_transport_proofs"]["backend"]
    observed = receipt.get("package_resolution", {})
    if (receipt.get("kind") != "r30-backend-import-receipt-v1" or receipt.get("source_sha") != SOURCE
            or receipt.get("bundle_manifest_sha256") != BUNDLE or receipt.get("source_manifest_sha256") != SOURCE_MANIFEST
            or receipt.get("identity") != proof or proof.get("success") is not True
            or proof.get("config_id") != CONFIG or proof.get("actual_id") != binding["image_ids"]["backend"]
            or receipt.get("full_runtime_files") != 60 or len(observed.get("files", [])) != 60
            or observed.get("uid") != 10001 or observed.get("business_env_absent") is not True
            or observed.get("package_origin") != "/app/backend/t44/__init__.py"):
        raise ValueError("ORIGINAL_PROVEN_BACKEND_IDENTITY_AND_IMPORT60_REQUIRED")
    return binding, inputs, timeout


def image_and_edge(value):
    rows = command([*DOCKER, "image", "inspect", ALIAS])
    if len(rows) != 1:
        raise ValueError("ONE_ACTUAL_BACKEND_ALIAS_REQUIRED")
    row = rows[0]
    proof = value["cryptographic_transport_proofs"]["backend"]
    env = dict(x.split("=", 1) for x in row["Config"].get("Env", []))
    labels = row["Config"].get("Labels", {})
    if (row["Id"] != proof["actual_id"] or proof["config_id"] != CONFIG
            or row["Os"] != "linux" or row["Architecture"] != "amd64"
            or row.get("Variant") not in {None, ""}
            or row["RootFS"]["Type"] != "layers" or len(row["RootFS"]["Layers"]) != proof["ordered_layer_count"]
            or labels.get("org.opencontainers.image.revision") != SOURCE
            or labels.get("io.t44.source-archive-sha256") != "275970aa18117751e3a4fc8c404d0750cb9698310a70146d64061a634c37bf09"
            or env.get("PYTHONPATH") != "/app/backend"
            or any(k.startswith(("T44_", "MYSQL_", "RABBITMQ_", "AMQP_", "DATABASE_", "DB_", "SQLALCHEMY_")) for k in env)):
        raise ValueError("ACTUAL_PROVEN_ALIAS_PLATFORM_ENV_IDENTITY_CHANGED")
    if row["Id"] != CONFIG and (row.get("Descriptor", {}).get("digest") != row["Id"]
            or proof.get("identity_kind") != "oci-descriptor-to-original-config"
            or proof.get("actual_descriptor_sha256_recomputed_from_archive") is not True
            or proof.get("all_config_and_layer_descriptors_sha256_size_verified") is not True):
        raise ValueError("DOCKER29_ACTUAL_DESCRIPTOR_AND_CONFIG_CHAIN_REQUIRED")
    network = value["project"] + "_edge"
    networks = command([*DOCKER, "network", "inspect", network])
    if (len(networks) != 1 or networks[0]["Name"] != network
            or networks[0]["Labels"].get("com.docker.compose.project") != value["project"]
            or networks[0]["Labels"].get("com.docker.compose.network") != "edge"):
        raise ValueError("EXACT_EXISTING_OWNED_EDGE_NETWORK_REQUIRED")
    return network


def argv(args, value, network, name, *, runtime=False):
    prefix = [*DOCKER, "run", "--rm", "--pull", "never", "--name", name,
            "--label", "io.t44.r30.http.owner=" + value["project"], "--network", network,
            "--user", "10001:10001", "--read-only", "--cap-drop", "ALL", "--security-opt", "no-new-privileges:true",
            "--volume", str(args.output_dir / "code") + ":/neutral-code:ro",
            "--volume", str(args.output_dir / "inputs") + ":/neutral-input:ro",
            "--volume", str(args.output_dir / "output") + ":/neutral-output", "--entrypoint", "python", ALIAS]
    if runtime:
        return prefix + ["-B", "/neutral-code/escalation_readback.py", "--check-runtime-only"]
    return prefix + ["-B", "/neutral-code/prepare_http.py", "--plan", "/neutral-input/plan.json",
            "--accounts", "/neutral-input/accounts.json", "--service", "/neutral-input/service.json",
            "--ca", "/neutral-input/ca.pem", "--import-receipt", "/neutral-input/backend-import-receipt.json",
            "--binding", "/neutral-input/binding.json", "--output", "/neutral-output/result",
            "--root-admit-http-preparation"]


def owned_exit(value, name, *, stop=False):
    result = subprocess.run([*DOCKER, "inspect", name], check=False, capture_output=True, timeout=10, env=environment())
    if result.returncode == 1 and b"no such" in result.stderr.lower():
        return
    result.check_returncode()
    rows = json.loads(result.stdout)
    if (len(rows) != 1 or rows[0]["Name"] != "/" + name
            or rows[0]["Image"] not in {value["image_ids"]["backend"], CONFIG}
            or rows[0]["Config"]["Labels"].get("io.t44.r30.http.owner") != value["project"]):
        raise ValueError("ONLY_THIS_NEW_HTTP_CHILD_MAY_BE_STOPPED")
    if rows[0]["State"]["Running"]:
        if not stop:
            raise ValueError("HTTP_CHILD_EXIT_NOT_PROVEN")
        subprocess.run([*DOCKER, "stop", "--time", "5", name], check=True, capture_output=True,
                       timeout=10, env=environment())
        owned_exit(value, name)


def run(args):
    a = tools()
    value, inputs, timeout = checked(args, a)
    args.code_manifest = args.code_dir / "code-manifest.PUBLIC.json"
    code = a.producer_files(args)
    manifest = json.loads(code["producer-manifest.PUBLIC.json"])
    if (manifest.get("source_sha") != SOURCE or manifest.get("purpose") != "FUTURE_NEW_WINDOW_ONLY_NOT_R30WINDOW01_REPLAY"
            or len(manifest["files"]) != 18 or "prepare_http.py" not in code or "escalation_readback.py" not in code
            or a.digest(code["source-manifest.json"]) != SOURCE_MANIFEST
            or a.digest(code["backend-bundle-manifest.json"]) != BUNDLE):
        raise ValueError("EXACT_REVIEWED_FUTURE18_SOURCE_AND_BUNDLE_REQUIRED")
    network = image_and_edge(value)
    a.stage(args, inputs, code)
    name = value["project"] + "-http-" + uuid.uuid4().hex
    status = "FAILED_PREFIX_PRESERVED"
    try:
        preflight_name = name + "-runtime"
        rc = a.run_child(argv(args, value, network, preflight_name, runtime=True),
                         args.output_dir / "logs/runtime.stdout.private", args.output_dir / "logs/runtime.stderr.private",
                         None, min(20, timeout), environment(),
                         lambda stop=False: owned_exit(value, preflight_name, stop=stop))
        observed = json.loads((args.output_dir / "logs/runtime.stdout.private").read_bytes()) if rc == 0 else {}
        if (rc or observed.get("kind") != "NEUTRAL_HTTP_RUNTIME_FUNCTION_PROBE_ONLY"
                or observed.get("actual_image_identity_verified_by_probe") is not False
                or observed.get("required_backend_config") != CONFIG):
            raise ValueError("REAL_BACKEND_RUNTIME_FUNCTION_PROBE_REQUIRED")
        a.save(args.output_dir / "runtime.PUBLIC.json", {"probe": observed,
               "wrapper_observed_image_actual_id": value["image_ids"]["backend"], "proven_config_id": CONFIG,
               "identity_basis": "current alias inspect equals original raw binding/import proven content-addressed identity"})
        plan = json.loads(inputs["plan.json"])
        timeout = min(timeout, deadline(plan["lifecycle"]["packet_cutoff_utc"]) - time.time() - 10,
                      deadline(value["stop_utc"]) - time.time() - 10)
        if timeout < 1:
            raise ValueError("NO_HTTP_AFTER_PACKET_OR_G_RESERVE")
        rc = a.run_child(argv(args, value, network, name), args.output_dir / "logs/http.stdout.private",
                         args.output_dir / "logs/http.stderr.private", None, timeout, environment(),
                         lambda stop=False: owned_exit(value, name, stop=stop))
        if rc:
            raise subprocess.CalledProcessError(rc, ["fixed-http-preparation"])
        status = "CHILD_EXITED_ZERO_NOT_ACCEPTANCE"
    finally:
        paths = {}
        for p in sorted(args.output_dir.rglob("*")):
            if p.is_file() and not p.is_symlink() and p.parent.name not in {"inputs", "code"}:
                paths[p.relative_to(args.output_dir).as_posix()] = {"bytes": p.stat().st_size, "sha256": a.digest(p.read_bytes())}
        a.save(args.output_dir / "execution.PUBLIC.json", {"status": status, "output": str(args.output_dir / "output/result"),
               "binding_sha256": args.binding_sha256, "code_manifest_sha256": args.code_manifest_sha256,
               "original_input_paths": {k: str(getattr(args, k)) for k in ("plan", "accounts", "service", "import_receipt", "ca")},
               "paths": paths})
    return {"status": status, "receipt": str(args.output_dir / "execution.PUBLIC.json"),
            "sha256": a.digest((args.output_dir / "execution.PUBLIC.json").read_bytes())}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("phase-dir", "code-dir", "plan", "accounts", "service", "import-receipt", "ca", "output-dir"):
        p.add_argument("--" + name, type=Path, required=True)
    for name in ("binding-sha256", "code-manifest-sha256"):
        p.add_argument("--" + name, required=True)
    args = p.parse_args()
    os.umask(0o077)
    try:
        print(json.dumps(run(args)))
    except Exception as error:  # noqa: BLE001 -- boundary redacts private input/subprocess details
        print(json.dumps({"status": "FAILED", "error_type": type(error).__name__, "output": str(args.output_dir)}))
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
