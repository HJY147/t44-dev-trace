"""Fresh R30 backend import and window adapter; never controls cloud lifecycle or issues sessions."""

import argparse
import ast
import importlib.util
import json
import os
import platform
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ARTIFACT_SHA = "e5af027a79cd5d5733a5ae28521757428b6c2c0317a1d2ab3e0267dfff3c3c01"
V4_SHA = "59422f53fb8d5069218b483fe237204177a2c6af9c229a91a882b45aeba69680"
RAW_SHA = "30b1ca48f152cae797862319cdda80c0a0b65ed5af32acf4b18ea55d531cc8d0"
FACTORY_COMMIT = "8784ba2279ec82834fc967f56b756ed708e20bed"
FACTORY_SHA = "daaf29d3b47ab266ae4546f001e322275db5c3c902c9f36f8b8a2528690af2ea"
ORIGINAL_BUDGET_SHA = "305f9eaeea96b0ef882ec17a457f51852bafc8c34b5fe2e47056bd12625dd82d"
HERE = Path(__file__).resolve().parent
KIND = "r30-official-backend-production-entry-window-v1"


def load(path, expected):
    import hashlib

    if path.is_symlink() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
        raise ValueError("EXACT_R30_REVIEWED_LIBRARY_REQUIRED")
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location("r30_window_" + path.stem.replace("-", "_"), path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def artifact():
    return load(HERE / "r30-backend-artifact.py", ARTIFACT_SHA)


def cached_roles(path):
    a = artifact()
    a.regular(path)
    if a.sha(path) != RAW_SHA:
        raise ValueError("ORIGINAL_FULL_PUBLIC_IMAGE_PROOF_REQUIRED")
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    if (rows[-1].get("kind") != "proof_final" or not rows[-1]["complete"]
            or not rows[-1]["all_seven_proven"]):
        raise ValueError("COMPLETE_ORIGINAL_PUBLIC_CACHE_PROOF_REQUIRED")
    proof = a.module("image-proof.py", a.PROOF_SHA)
    images, proofs = {}, {}
    for role in ["web", "python", "node", "nginx", "mysql", "rabbitmq"]:
        matches = [r for r in rows if r.get("kind") == "role_proof" and r.get("role") == role]
        if len(matches) != 1 or not matches[0]["proof"]["success"]:
            raise ValueError("EXACT_ORIGINAL_CACHE_ROLE_REQUIRED")
        row = matches[0]
        current = proof.actual_image(row["declared_CI"]["alias"])
        if any(current[k] != row["actual_projection_no_Env_or_Cmd"][k]
               for k in ["Id", "Descriptor", "RootFS", "Os", "Architecture", "Variant", "Config"]):
            raise ValueError("CACHED_ROLE_IDENTITY_CHANGED_NO_FALLBACK:" + role)
        images[role] = {"alias": row["declared_CI"]["alias"]}
        proofs[role] = row["proof"]
    return images, proofs


def backend(package, expected, probe=True):
    a = artifact()
    checked = a.verify_bundle(package, expected)
    bundle = json.loads((package / "backend-bundle-manifest.json").read_text())
    source, _ = a.verify_source(package, bundle["source_manifest_sha256"])
    proof = a.module("image-proof.py", a.PROOF_SHA)
    actual = proof.actual_image(checked["alias"])
    identity = proof.prove_role(proof.scan_archive(package / "backend-image.tar.gz"),
                                "backend", bundle["declared"], source, actual)
    observed = None
    if probe:
        marker = "'uid':os.getuid(),'files':"
        if a.PROBE.count(marker) != 1:
            raise ValueError("EXACT_RUNTIME_ENV_PROBE_PREIMAGE_REQUIRED")
        code = "import importlib.util,sys\n" + a.PROBE.replace(marker, "'uid':os.getuid(),'package_origin':importlib.util.find_spec('t44').origin,'python_version':sys.version,'sys_executable':sys.executable,'business_env_absent':not any(k in os.environ for k in ['DATABASE_URL','AMQP_URL','T44_DATABASE']),'files':")
        observed = json.loads(a.command([*a.DOCKER, "run", "--rm", "--network", "none", "--read-only",
                                        "--user", "10001:10001", "--cap-drop", "ALL", "--security-opt",
                                        "no-new-privileges:true", "--entrypoint", "python", checked["alias"],
                                        "-c", code]))
        a.verify_runtime(observed, source["files"])
        if observed.get("business_env_absent") is not True:
            raise ValueError("BUSINESS_ENV_FORBIDDEN_IN_FILE_PROBE")
        if observed.get("package_origin") != "/app/backend/t44/__init__.py":
            raise ValueError("EXACT_NONROOT_PACKAGE_RESOLUTION_ORIGIN_REQUIRED")
    return bundle, source, identity, observed


def import_backend(args):
    a = artifact()
    if os.geteuid() != 0 or platform.system() != "Linux" or platform.machine() not in {"x86_64", "amd64"}:
        raise ValueError("ROOT_LINUX_AMD64_HOST_REQUIRED")
    if args.receipt.exists():
        raise ValueError("NEW_IMPORT_RECEIPT_REQUIRED")
    checked = a.verify_bundle(args.package, args.manifest_sha256)
    import subprocess

    before = subprocess.run([*a.DOCKER, "image", "inspect", checked["alias"]],
                            capture_output=True, check=False, timeout=20)
    if before.returncode != 1 or b"no such image" not in before.stderr.lower():
        raise ValueError("FRESH_ALIAS_ABSENCE_REQUIRED_NO_RETAG_OR_OVERWRITE")
    a.command([*a.DOCKER, "image", "load", "--input", args.package / "backend-image.tar.gz"], timeout=240)
    bundle, _source, identity, observed = backend(args.package, args.manifest_sha256)
    a.save(args.receipt, {"kind": "r30-backend-import-receipt-v1", "source_sha": a.SOURCE,
                         "bundle_manifest_sha256": args.manifest_sha256,
                         "source_manifest_sha256": bundle["source_manifest_sha256"],
                         "identity": identity, "full_runtime_files": len(observed["files"]),
                         "package_resolution": observed,
                         "business_services_started": False, "volumes_modified": False})
    return {"success": True, "receipt": str(args.receipt), "source_sha": a.SOURCE}


def verified_images(args, lib):
    a = artifact()
    if args.upgrade_binding != args.source_package / "backend-bundle-manifest.json":
        raise ValueError("EXPLICIT_R30_BACKEND_BUNDLE_PATH_REQUIRED")
    bundle, source, identity, observed = backend(args.source_package, args.upgrade_binding_sha256)
    if bundle["source_manifest_sha256"] != args.source_manifest_sha256:
        raise ValueError("EXACT_R30_SOURCE_MANIFEST_BINDING_REQUIRED")
    images, proofs = cached_roles(args.original_proof)
    images["backend"] = {"alias": bundle["declared"]["alias"]}
    proofs["backend"] = identity
    # The inherited source probe/binding explicitly records all 53 backend files;
    # backend() independently verifies the full 60-file installed runtime context.
    subset = [r for r in source["files"] if r["path"].startswith("backend/")]
    source = {**source, "files": subset}
    observed = {"uid": observed["uid"], "files": [r for r in observed["files"] if r["path"].startswith("backend/")],
                "business_env_absent": observed["business_env_absent"]}
    frozen = json.loads((args.source_package / "frozen-comparison.json").read_text())
    frontend = {"frozen_file_set_sha256": a.digest(a.canonical(frozen["unchanged_files"]))}
    return images, proofs, frontend, source, observed


def replace_function(text, function, replacement):
    parsed = ast.parse(text)
    matches = [node for node in parsed.body if isinstance(node, ast.FunctionDef) and node.name == function]
    if len(matches) != 1:
        raise ValueError("EXACT_SINGLE_GENERATOR_FUNCTION_PREIMAGE_REQUIRED")
    node = matches[0]
    lines = text.splitlines(keepends=True)
    return "".join(lines[:node.lineno - 1]) + replacement + "\n\n" + "".join(lines[node.end_lineno:])


def derive(args):
    a = artifact()
    a.verify_bundle(args.package, args.manifest_sha256)
    legacy_v4 = load(HERE / "v4/derive-profile.py", V4_SHA)
    parent = legacy_v4.parent()
    parent.deadline(args.stop_utc, datetime.now(timezone.utc))  # noqa: UP017 -- cloud Python3.10
    if not re.fullmatch(r"r30[a-z0-9]{5,12}", args.run_id):
        raise ValueError("NEW_EXPLICIT_R30_WINDOW_RUN_ID_REQUIRED")
    texts = legacy_v4.derive_texts(parent, a.SOURCE, args.stop_utc, 53)
    old_generation_sha = a.digest(texts["generation.py"].encode())
    if a.digest(texts["mysql-budget.py"].encode()) != ORIGINAL_BUDGET_SHA:
        raise ValueError("EXACT_ORIGINAL_V4_BUDGET_TEMPLATE_REQUIRED")
    budget = parent.replacement(texts["mysql-budget.py"], 'KIND = "' + legacy_v4.KIND + '"',
                                'KIND = "' + KIND + '"')
    budget_sha = a.digest(budget.encode())
    generation = texts["generation.py"]
    generation = replace_function(generation, "verified_images", '''def verified_images(args, lib):
    adapter = load(Path(__file__).resolve().parent / "r30-window.py", R30_ADAPTER_SHA, "r30_backend_window")
    return adapter.verified_images(args, lib)''')
    generation = parent.replacement(generation, legacy_v4.KIND, KIND, 2)
    generation = parent.replacement(generation, 'BUDGET_SHA = "' + ORIGINAL_BUDGET_SHA + '"',
                                    'BUDGET_SHA = "' + budget_sha + '"')
    generation = parent.replacement(generation, "def prepare(args):\n", "def prepare(args):\n    if args.run_id != " + repr(args.run_id) + ":\n        raise ValueError('EXACT_R30_WINDOW_RUN_ID_REQUIRED')\n")
    generation = parent.replacement(generation, 'DOCKER = ["docker", "--context", "default"]',
                                    'R30_ADAPTER_SHA = "' + a.sha(Path(__file__)) + '"\nDOCKER = ["docker", "--context", "default"]')
    generation = generation.replace("target_frontend_frozen_equal_file_set_sha256", "r30_46_unchanged_frozen_file_set_sha256")
    # Retain budget logic and operation methods; bind the sole budget KIND change by a new pin.
    stream = parent.replacement(texts["resource-stream.py"], legacy_v4.KIND, KIND)
    stream = parent.replacement(stream, old_generation_sha, a.digest(generation.encode()))
    factory = a.command(["git", "-C", HERE.parent.parent, "show", FACTORY_COMMIT + ":deployment/cloud-reuse/app-campaign.py"])
    if a.digest(factory) != FACTORY_SHA:
        raise ValueError("EXACT_PUBLIC_FROZEN_FACTORY_BYTES_REQUIRED")
    outputs = {"generation.py": generation.encode(), "resource-stream.py": stream.encode(),
               "mysql-budget.py": budget.encode(), "r30-window.py": Path(__file__).read_bytes(),
               "r30-backend-artifact.py": (HERE / "r30-backend-artifact.py").read_bytes(),
               "image-proof.py": (HERE / "image-proof.py").read_bytes(), "factory.py": factory}
    for name, raw in outputs.items():
        compile(raw, name, "exec")
    a.new_directory(args.output)
    for name, raw in outputs.items():
        a.write(args.output / name, raw)
    value = {"kind": KIND, "source_sha": a.SOURCE, "run_id": args.run_id, "stop_utc": args.stop_utc,
             "backend_bundle_manifest_sha256": args.manifest_sha256,
             "derived_files": {n: {"sha256": a.digest(raw), "bytes": len(raw)} for n, raw in outputs.items()},
             "source_probe_backend_files": 53, "full_runtime_context_files": 60,
             "original_budget_sha256": ORIGINAL_BUDGET_SHA, "derived_budget_sha256": budget_sha,
             "frozen_factory_source_commit": FACTORY_COMMIT,
             "legacy_templates_modified": False, "old_source_only_builder_used": False,
             "cloud_or_SUT_or_session_issued": False,
             "authority": "preparation only; root and independent QA admission still required"}
    a.save(args.output / "profile.json", value)
    return value


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("action", choices=["derive", "import-backend", "verify-loaded", "verify-cache"])
    p.add_argument("--package", type=Path)
    p.add_argument("--manifest-sha256")
    p.add_argument("--original-proof", type=Path)
    p.add_argument("--receipt", type=Path)
    p.add_argument("--run-id")
    p.add_argument("--stop-utc")
    p.add_argument("--output", type=Path)
    args = p.parse_args()
    os.umask(0o077)
    if args.action == "derive":
        value = derive(args)
    elif args.action == "import-backend":
        value = import_backend(args)
    elif args.action == "verify-cache":
        images, proofs = cached_roles(args.original_proof)
        value = {"success": True, "cached_aliases": images, "proofs": proofs, "mutation_performed": False}
    else:
        _, _, identity, _ = backend(args.package, args.manifest_sha256)
        value = {"success": True, "identity": identity, "business_services_started": False}
    print(json.dumps(value))


if __name__ == "__main__":
    main()
