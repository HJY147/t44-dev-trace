"""Exact final-source backend+web build/import; original generic builder stays immutable."""

import argparse
import ast
import hashlib
import importlib.util
import json
import os
import platform
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
GENERIC_SHA = "0a1c2cd5bf57717ba5218ff6bb5086d6acbb60ff54713940a6da73f495a1cfcd"
PROOF_SHA = "47b50d0111737d2b4ff7b47ce37c46bc5d7fc208d2f3933088b8a08dab326fc0"
FACTORY_SHA = "daaf29d3b47ab266ae4546f001e322275db5c3c902c9f36f8b8a2528690af2ea"
PUBLIC_CACHE_SHA = "30b1ca48f152cae797862319cdda80c0a0b65ed5af32acf4b18ea55d531cc8d0"
BUDGET_SHA = "9e98632fa1885bf4327b04a95daeba5cee4ad909b536e91ac8b11a1e58488a61"
KIND = "r30-official-backend-production-entry-window-v1"
DOCKER = ["docker", "--context", "default"]
RUNTIME = """import hashlib,importlib.util,json,os,stat,sys
from pathlib import Path
rows=[]
for prefix in ['backend','specs/database','specs/contracts','deployment']:
 for p in sorted((Path('/app')/prefix).rglob('*')):
  s=p.lstat()
  if not (stat.S_ISREG(s.st_mode) or stat.S_ISDIR(s.st_mode)): raise ValueError('RUNTIME_LINK_OR_SPECIAL')
  if p.is_file():
   data=p.read_bytes();rows.append({'path':p.relative_to('/app').as_posix(),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'mode':stat.S_IMODE(s.st_mode)})
print(json.dumps({'uid':os.getuid(),'package_origin':importlib.util.find_spec('t44').origin,'python_version':sys.version,'sys_executable':sys.executable,'business_env_absent':not any(k.startswith(('T44_','MYSQL_','RABBITMQ_','AMQP_','DATABASE_')) for k in os.environ),'files':sorted(rows,key=lambda r:r['path'])}))
"""


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def sha(path):
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for data in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(data)
    return value.hexdigest()


def load(path, expected):
    if path.is_symlink() or sha(path) != expected:
        raise ValueError("EXACT_REVIEWED_LIBRARY_REQUIRED:" + path.name)
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location("final_" + path.stem.replace("-", "_"), path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def generic():
    return load(HERE / "image-bundle.py", GENERIC_SHA)


def proof():
    return load(HERE / "image-proof.py", PROOF_SHA)


def write(path, data):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "wb") as stream:
        stream.write(data)


def save(path, value):
    write(path, (json.dumps(value, sort_keys=True, indent=2) + "\n").encode())


def new(path):
    if not path.is_absolute() or path.parent.resolve() != path.parent or path.exists():
        raise ValueError("NEW_CANONICAL_ABSOLUTE_OUTPUT_REQUIRED")
    path.mkdir(mode=0o700)


def source_data(repository, source):
    g = generic()
    if (not re.fullmatch(r"[0-9a-f]{40}", source or "")
            or g.command(["git", "-C", repository, "rev-parse", source + "^{commit}"]).decode().strip() != source):
        raise ValueError("EXACT_FINAL_FULL_GIT_COMMIT_REQUIRED")
    raw = g.command(["git", "-C", repository, "archive", source, *g.SUBSET])
    tree = g.command(["git", "-C", repository, "ls-tree", "-rz", "--full-tree", source, "--", *g.SUBSET])
    git_files = {}
    for line in tree.split(b"\0"):
        if not line:
            continue
        header, name = line.split(b"\t", 1)
        mode, kind, oid = header.decode().split()
        if mode not in {"100644", "100755"} or kind != "blob":
            raise ValueError("ONLY_GIT_REGULAR_BUILD_CONTEXT_FILES_REQUIRED")
        git_files[name.decode()] = (mode, oid)
    return g, raw, git_files


def context_rows(context, git_files):
    rows = []
    for name, (mode, oid) in sorted(git_files.items()):
        path = context / name
        data = path.read_bytes()
        git_oid = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()  # Git object ID; SHA256 content proof below.
        if git_oid != oid or path.is_symlink():
            raise ValueError("ARCHIVE_BYTES_DIFFER_FROM_EXACT_GIT_BLOB")
        rows.append({"path": name, "bytes": len(data), "sha256": digest(data), "mode": 0o755 if mode == "100755" else 0o644})
    actual = {p.relative_to(context).as_posix() for p in context.rglob("*") if p.is_file()}
    if actual != set(git_files):
        raise ValueError("COMPLETE_SOURCE_CONTEXT_SET_REQUIRED")
    return rows


def runtime_rows(rows):
    return [r for r in rows if r["path"].startswith(("backend/", "specs/database/", "specs/contracts/"))
            or r["path"] in {"deployment/runtime_probe.py", "deployment/credential_admin.py"}]


def verify_runtime(observed, rows):
    if (observed.get("uid") != 10001 or observed.get("business_env_absent") is not True
            or observed.get("package_origin") != "/app/backend/t44/__init__.py"
            or observed.get("files") != runtime_rows(rows)):
        raise ValueError("ACTUAL_COMPLETE_DYNAMIC_RUNTIME_BYTES_HASH_NONROOT_ORIGIN_REQUIRED")


def observe_runtime(alias):
    return json.loads(generic().command([*DOCKER, "run", "--rm", "--pull", "never", "--network", "none",
        "--read-only", "--user", "10001:10001", "--cap-drop", "ALL", "--security-opt", "no-new-privileges:true",
        "--entrypoint", "python", alias, "-B", "-c", RUNTIME], timeout=30))


def archive_config_ids(graph, images):
    table = graph["names"]["manifest.json"]["json"]
    output = {}
    for role, row in images.items():
        found = [r for r in table if row["alias"] in [t.removeprefix("docker.io/library/") for t in r.get("RepoTags") or []]]
        if len(found) != 1:
            raise ValueError("ONE_SAVED_ALIAS_CONFIG_BINDING_REQUIRED")
        output[role] = graph["names"][found[0]["Config"]]["digest"]
    return output


def build(repository, source, output):
    g, source_raw, git_files = source_data(repository, source)
    # Exact lock bytes come from the explicitly supplied immutable source, not from working-tree files.
    lock = g.command(["git", "-C", repository, "show", source + ":backend/requirements.lock"])
    frontend_lock = g.command(["git", "-C", repository, "show", source + ":frontend/pnpm-lock.yaml"])
    expected_lock = digest(lock)
    g.EXPECTED_LOCK = expected_lock  # Explicit source-derived lock pin; generic build still compares actual context bytes.
    original_command = g.command
    captured = []

    def dual_only(argv, *, timeout=600):
        cmd = list(map(str, argv))
        if cmd[:5] == [*DOCKER, "image", "save"]:
            if cmd[5] != "--output" or len(cmd[7:]) != 7:
                raise ValueError("EXACT_GENERIC_SEVEN_ROLE_SAVE_PREIMAGE_REQUIRED")
            selected = [x for x in cmd[7:] if x in {"t44-backend:src-" + source, "t44-web:src-" + source}]
            if len(selected) != 2:
                raise ValueError("ONLY_NEW_BACKEND_AND_WEB_TRANSPORT_REQUIRED")
            captured.append(selected)
            cmd = cmd[:7] + selected
        try:
            return original_command(cmd, timeout=timeout)
        except subprocess.CalledProcessError as error:
            if output.is_dir() and not (output / "build-failure.PUBLIC.json").exists():
                save(output / "build-failure.PUBLIC.json", {"source_sha": source, "error_class": type(error).__name__,
                     "returncode": error.returncode, "argv": cmd, "prefix_preserved": True})
                write(output / "build.stdout.private", error.stdout or b"")
                write(output / "build.stderr.private", error.stderr or b"")
            raise

    g.command = dual_only
    new(output)
    g.build(repository, source, output / "work")
    if len(captured) != 1:
        raise ValueError("REAL_DUAL_ARCHIVE_BUILD_REQUIRED")
    work = output / "work"
    old = json.loads((work / "bundle-manifest.json").read_bytes())
    rows = context_rows(work / "context", git_files)
    if (old["source_archive_sha256"] != digest(source_raw) or old["dependency_lock_sha256"] != expected_lock
            or (work / "context/backend/requirements.lock").read_bytes() != lock):
        raise ValueError("SOURCE_ARCHIVE_OR_EXPLICIT_NEW_LOCK_MISMATCH")
    for name in ("images.tar.gz", "source-runtime-context.tar.gz"):
        shutil.copyfile(work / name, output / name)
        (output / name).chmod(0o600)
    source_manifest = {"kind": "final-exact-public-runtime-context-v1", "source_sha": source,
        "source_archive_sha256": digest(source_raw), "files": rows, "backend_runtime_files": runtime_rows(rows),
        "dependency_lock_sha256": expected_lock, "frontend_lock_sha256": digest(frontend_lock),
        "generic_helper_sha256": GENERIC_SHA, "producer_sha256": sha(Path(__file__)),
        "context_paths": list(g.SUBSET), "context_file_count": len(rows)}
    save(output / "source-manifest.json", source_manifest)
    p = proof()
    graph = p.scan_archive(output / "images.tar.gz")
    images = {r: old["images"][r] for r in ("backend", "web")}
    configs = archive_config_ids(graph, images)
    for role, row in images.items():
        row["actual_id_in_CI"] = row["image_id"]
        row["image_id"] = configs[role]
    identities = {r: p.prove_role(graph, r, row, source_manifest, p.actual_image(row["alias"])) for r, row in images.items()}
    # Official LOAD Python config is actually proven, even when CI uses a descriptor image store.
    original_command([*DOCKER, "image", "save", "--output", work / "python-identity.tar", old["images"]["python"]["alias"]])
    python_graph = p.scan_archive(work / "python-identity.tar")
    python_row = {**old["images"]["python"]}
    python_row["image_id"] = archive_config_ids(python_graph, {"python": python_row})["python"]
    python_identity = p.prove_role(python_graph, "python", python_row, source_manifest, p.actual_image(python_row["alias"]))
    observed = observe_runtime(images["backend"]["alias"])
    verify_runtime(observed, rows)
    save(output / "actual-runtime-files.json", observed)
    names = ("images.tar.gz", "source-runtime-context.tar.gz", "source-manifest.json", "actual-runtime-files.json")
    bundle = {"kind": "final-backend-web-bundle-v1", "source_sha": source,
        "source_manifest_sha256": sha(output / "source-manifest.json"), "source_archive_sha256": digest(source_raw),
        "images": images, "official_cache": {r: old["images"][r] for r in g.PINS}, "ci_image_proofs": identities,
        "official_load_python_identity": python_identity,
        "files": {n: {"sha256": sha(output / n), "bytes": (output / n).stat().st_size} for n in names},
        "dependency_lock_sha256": expected_lock, "frontend_lock_sha256": digest(frontend_lock),
        "transport_roles": ["backend", "web"], "runtime_file_count": len(observed["files"]),
        "tool_sha256": sha(Path(__file__)), "generic_helper_sha256": GENERIC_SHA,
        "tool_git_sha": original_command(["git", "-C", repository, "rev-parse", "HEAD"]).decode().strip(),
        "github_run_id": os.environ.get("GITHUB_RUN_ID"), "root_approved": False,
        "business_HTTP_SQL_cloud_QA_or_sessions_executed": False}
    save(output / "backend-bundle-manifest.json", bundle)
    profile = {"schema": "t44-final-source-profile-v1", "version": 1, "root_approved": False,
        "source_sha": source, "source_manifest_sha256": sha(output / "source-manifest.json"),
        "backend_bundle_manifest_sha256": sha(output / "backend-bundle-manifest.json"),
        "root_manifest_sha256": sha(output / "backend-bundle-manifest.json"),
        "backend_config_id": identities["backend"]["config_id"], "web_config_id": identities["web"]["config_id"],
        "load_python_config_id": python_identity["config_id"],
        "backend_requirements_lock_sha256": expected_lock, "frontend_lock_sha256": digest(frontend_lock),
        "runtime_files": {r["path"]: r["sha256"] for r in observed["files"]}, "runtime_file_count": len(observed["files"]),
        "context_file_count": len(rows), "actual_build_receipt_sha256": sha(output / "actual-runtime-files.json"),
        "gen_kind": KIND, "budget_helper_sha256": BUDGET_SHA, "actual_loaded": False}
    save(output / "source-profile.PUBLIC.json", profile)
    return {"status": "BUILT_NOT_ROOT_APPROVED_OR_LOADED", "source_sha": source,
            "manifest_sha256": sha(output / "backend-bundle-manifest.json"), "profile_sha256": sha(output / "source-profile.PUBLIC.json"),
            "images_bytes": bundle["files"]["images.tar.gz"]["bytes"]}


def verify(package, expected):
    if not re.fullmatch(r"[0-9a-f]{64}", expected or "") or sha(package / "backend-bundle-manifest.json") != expected:
        raise ValueError("ROOT_PINNED_NEW_BUNDLE_MANIFEST_REQUIRED")
    value = json.loads((package / "backend-bundle-manifest.json").read_bytes())
    if (value["kind"] != "final-backend-web-bundle-v1" or not re.fullmatch(r"[0-9a-f]{40}", value["source_sha"])
            or set(value["images"]) != {"backend", "web"} or set(value["official_cache"]) != set(generic().PINS)
            or value["transport_roles"] != ["backend", "web"]
            or set(value["files"]) != {"images.tar.gz", "source-runtime-context.tar.gz", "source-manifest.json", "actual-runtime-files.json"}):
        raise ValueError("EXACT_FINAL_DUAL_BUNDLE_SCHEMA_REQUIRED")
    for name, row in value["files"].items():
        if generic().regular(package / name).st_size != row["bytes"] or sha(package / name) != row["sha256"]:
            raise ValueError("EXACT_BUNDLE_OBJECT_BYTES_HASH_REQUIRED")
    source = json.loads((package / "source-manifest.json").read_bytes())
    if (sha(package / "source-manifest.json") != value["source_manifest_sha256"]
            or source["source_sha"] != value["source_sha"]
            or source["dependency_lock_sha256"] != value["dependency_lock_sha256"]
            or generic().gzip_digest(package / "source-runtime-context.tar.gz") != source["source_archive_sha256"]):
        raise ValueError("SOURCE_LOCK_AND_CONTEXT_ARCHIVE_CHAIN_REQUIRED")
    verify_runtime(json.loads((package / "actual-runtime-files.json").read_bytes()), source["files"])
    for role, row in value["images"].items():
        if (row["alias"] != "t44-" + role + ":src-" + value["source_sha"]
                or row["revision_label"] != value["source_sha"] or row["archive_label"] != source["source_archive_sha256"]):
            raise ValueError("ACTUAL_NEW_SOURCE_IMAGE_ALIAS_AND_LABELS_REQUIRED")
    return value, source


def imported(package, expected):
    bundle, source = verify(package, expected)
    p = proof()
    graph = p.scan_archive(package / "images.tar.gz")
    identities = {r: p.prove_role(graph, r, row, source, p.actual_image(row["alias"])) for r, row in bundle["images"].items()}
    observed = observe_runtime(bundle["images"]["backend"]["alias"])
    verify_runtime(observed, source["files"])
    return bundle, source, identities, observed


def import_bundle(args):
    if (os.geteuid() != 0 or platform.system() != "Linux" or platform.machine() not in {"amd64", "x86_64"}
            or args.receipt.exists()):
        raise ValueError("ROOT_NEW_ORIGINAL_IMPORT_RECEIPT_REQUIRED")
    bundle, _ = verify(args.package, args.manifest_sha256)
    for row in bundle["images"].values():
        result = subprocess.run([*DOCKER, "image", "inspect", row["alias"]], check=False, capture_output=True, timeout=20)
        if result.returncode != 1 or b"no such image" not in result.stderr.lower():
            raise ValueError("NEW_ALIASES_REQUIRED_NO_RETAG_OR_OVERWRITE")
    generic().command([*DOCKER, "image", "load", "--input", args.package / "images.tar.gz"], timeout=300)
    bundle, source, identities, observed = imported(args.package, args.manifest_sha256)
    save(args.receipt, {"kind": "final-backend-web-import-v1", "source_sha": source["source_sha"],
        "bundle_manifest_sha256": args.manifest_sha256, "source_manifest_sha256": bundle["source_manifest_sha256"],
        "identity": identities["backend"], "identities": identities, "full_runtime_files": len(observed["files"]),
        "package_resolution": observed, "business_services_started": False})
    return {"status": "IMPORTED_PROVEN_NOT_ACCEPTANCE", "receipt": str(args.receipt), "sha256": sha(args.receipt)}


def cached(path):
    if sha(path) != PUBLIC_CACHE_SHA:
        raise ValueError("ORIGINAL_PUBLIC_CACHE_PROOF_REQUIRED")
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    if not rows[-1].get("all_seven_proven") or not rows[-1].get("complete"):
        raise ValueError("COMPLETE_ORIGINAL_CACHE_CHAIN_REQUIRED")
    images, identities = {}, {}
    p = proof()
    for role, pin in generic().PINS.items():
        matches = [r for r in rows if r.get("kind") == "role_proof" and r.get("role") == role]
        if len(matches) != 1 or matches[0]["declared_CI"]["official_upstream_pin"] != pin:
            raise ValueError("UNCHANGED_OFFICIAL_CACHE_PIN_REQUIRED")
        row = matches[0]
        current = p.actual_image(row["declared_CI"]["alias"])
        if any(current[k] != row["actual_projection_no_Env_or_Cmd"][k] for k in
               ("Id", "Descriptor", "RootFS", "Os", "Architecture", "Variant", "Config")):
            raise ValueError("ORIGINAL_OFFICIAL_CACHE_ACTUAL_IDENTITY_CHANGED")
        images[role], identities[role] = {"alias": row["declared_CI"]["alias"]}, row["proof"]
    return images, identities


def verified_images(args, lib):
    bundle, source, identities, observed = imported(args.source_package, args.upgrade_binding_sha256)
    if bundle["source_manifest_sha256"] != args.source_manifest_sha256:
        raise ValueError("EXACT_NEW_SOURCE_MANIFEST_REQUIRED")
    images, old_proofs = cached(args.original_proof)
    images.update({r: {"alias": row["alias"]} for r, row in bundle["images"].items()})
    old_proofs.update(identities)
    backend = [r for r in source["files"] if r["path"].startswith("backend/")]
    # Inherited GEN stores its backend-only source observation; complete runtime proof remains original import receipt.
    frontend = [r for r in source["files"] if r["path"].startswith("frontend/")]
    return images, old_proofs, {"frozen_file_set_sha256": digest(json.dumps(frontend, sort_keys=True).encode())}, \
        {**source, "files": backend}, {"uid": observed["uid"], "files": [r for r in observed["files"] if r["path"].startswith("backend/")],
                                     "business_env_absent": observed["business_env_absent"]}


def replace_function(text, name, replacement):
    matches = [n for n in ast.parse(text).body if isinstance(n, ast.FunctionDef) and n.name == name]
    if len(matches) != 1:
        raise ValueError("EXACT_GENERATOR_FUNCTION_PREIMAGE_REQUIRED")
    n = matches[0]
    lines = text.splitlines(keepends=True)
    return "".join(lines[:n.lineno - 1]) + replacement + "\n\n" + "".join(lines[n.end_lineno:])


def derive(args):
    _bundle, source = verify(args.package, args.manifest_sha256)
    v4 = load(HERE / "v4/derive-profile.py", "59422f53fb8d5069218b483fe237204177a2c6af9c229a91a882b45aeba69680")
    parent = v4.parent()
    parent.deadline(args.stop_utc, datetime.now(timezone.utc))  # noqa: UP017 -- APP Python3.10
    if not re.fullmatch(r"r30[a-z0-9]{5,12}", args.run_id or "") or args.run_id == "r30window01":
        raise ValueError("ROOT_APPROVED_FRESH_RUN_REQUIRED")
    count = len([r for r in source["files"] if r["path"].startswith("backend/")])
    texts = v4.derive_texts(parent, source["source_sha"], args.stop_utc, count)
    old_gen_sha = digest(texts["generation.py"].encode())
    budget = parent.replacement(texts["mysql-budget.py"], 'KIND = "' + v4.KIND + '"', 'KIND = "' + KIND + '"')
    if digest(budget.encode()) != BUDGET_SHA:
        raise ValueError("EXACT_UNCHANGED_9E_BUDGET_LOGIC_REQUIRED")
    gen = replace_function(texts["generation.py"], "verified_images", '''def verified_images(args, lib):
    adapter = load(Path(__file__).resolve().parent / "final-image-bundle.py", FINAL_ADAPTER_SHA, "final_source_adapter")
    return adapter.verified_images(args, lib)''')
    gen = parent.replacement(gen, v4.KIND, KIND, 2)
    gen = parent.replacement(gen, 'BUDGET_SHA = "305f9eaeea96b0ef882ec17a457f51852bafc8c34b5fe2e47056bd12625dd82d"', 'BUDGET_SHA = "' + BUDGET_SHA + '"')
    gen = parent.replacement(gen, 'DOCKER = ["docker", "--context", "default"]', 'FINAL_ADAPTER_SHA = "' + sha(Path(__file__)) + '"\nDOCKER = ["docker", "--context", "default"]')
    gen = parent.replacement(gen, "def prepare(args):\n", "def prepare(args):\n    if args.run_id != " + repr(args.run_id) + ":\n        raise ValueError('EXACT_NEW_SOURCE_RUN_REQUIRED')\n")
    gen = parent.replacement(gen, '"source_sha": OLD_SOURCE,', '"source_sha": SOURCE,')
    gen = parent.replacement(gen, '"reused_original_tag":', '"newly_built_alias":')
    gen = gen.replace("target_frontend_frozen_equal_file_set_sha256", "actual_new_frontend_source_file_set_sha256")
    stream = parent.replacement(texts["resource-stream.py"], v4.KIND, KIND)
    stream = parent.replacement(stream, old_gen_sha, digest(gen.encode()))
    # Observer may serve proof until cost cutoff, independently of business workload G.
    stop = datetime.strptime(args.stop_utc, "%Y-%m-%dT%H:%M:%SZ")
    cost = datetime.strptime(args.cost_stop_utc, "%Y-%m-%dT%H:%M:%SZ")
    if (cost - stop).total_seconds() != 300:
        raise ValueError("G35_C40_OBSERVER_EXPORT_RESERVE_REQUIRED")
    stream = parent.replacement(stream, 'HARDSTOP = "' + args.stop_utc + '"', 'HARDSTOP = "' + args.cost_stop_utc + '"')
    factory = generic().command(["git", "-C", HERE.parent.parent, "show", "8784ba2279ec82834fc967f56b756ed708e20bed:deployment/cloud-reuse/app-campaign.py"])
    if digest(factory) != FACTORY_SHA:
        raise ValueError("ORIGINAL_FROZEN_FACTORY_REQUIRED")
    outputs = {"generation.py": gen.encode(), "resource-stream.py": stream.encode(), "mysql-budget.py": budget.encode(),
        "final-image-bundle.py": Path(__file__).read_bytes(), "image-bundle.py": (HERE / "image-bundle.py").read_bytes(),
        "image-proof.py": (HERE / "image-proof.py").read_bytes(), "factory.py": factory}
    new(args.output)
    for name, raw in outputs.items():
        compile(raw, name, "exec")
        write(args.output / name, raw)
    save(args.output / "profile.json", {"kind": KIND, "source_sha": source["source_sha"], "run_id": args.run_id,
        "stop_utc": args.stop_utc, "cost_stop_utc": args.cost_stop_utc, "backend_bundle_manifest_sha256": args.manifest_sha256,
        "derived_budget_sha256": BUDGET_SHA, "source_probe_backend_files": count,
        "full_runtime_context_files": len(runtime_rows(source["files"])),
        "derived_files": {n: {"bytes": len(raw), "sha256": digest(raw)} for n, raw in outputs.items()},
        "root_approved": False, "old_helpers_modified": False, "cloud_executed": False})
    return {"status": "DERIVED_NOT_APPROVED_OR_EXECUTED", "profile": str(args.output / "profile.json"), "sha256": sha(args.output / "profile.json")}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("action", choices=("build", "verify", "import", "derive", "verify-cache"))
    for key in ("repository", "output", "package", "receipt", "original-proof"):
        p.add_argument("--" + key, type=Path)
    for key in ("source-sha", "manifest-sha256", "run-id", "stop-utc", "cost-stop-utc"):
        p.add_argument("--" + key)
    args = p.parse_args()
    os.umask(0o077)
    if args.action == "build":
        value = build(args.repository, args.source_sha, args.output)
    elif args.action == "derive":
        value = derive(args)
    elif args.action == "import":
        value = import_bundle(args)
    elif args.action == "verify-cache":
        images, identities = cached(args.original_proof)
        value = {"status": "CACHE_PROVEN", "images": images, "identities": identities}
    else:
        bundle, source = verify(args.package, args.manifest_sha256)
        value = {"status": "VERIFIED_NOT_LOADED", "source_sha": source["source_sha"], "images": list(bundle["images"])}
    print(json.dumps(value))


if __name__ == "__main__":
    main()
