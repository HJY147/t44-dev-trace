"""Prepare/build/verify only exact 0b backend bytes; no cloud lifecycle or credentials."""

import argparse
import gzip
import hashlib
import importlib.util
import io
import json
import os
import re
import stat
import subprocess
import tarfile
from pathlib import Path

SOURCE = "0bffe0c535e5897890aebf30879fdd3839dc52d6"
BASE = "935ab5b93bea788672c2b4a088c79cfeed848954"
PYTHON = "python:3.12-slim-bookworm@sha256:6a0e06f5ba0b373d051aabd3fffb9b873f27f9a2a3a14bcbe37dee6f0e3bbc70"
PROOF_SHA = "47b50d0111737d2b4ff7b47ce37c46bc5d7fc208d2f3933088b8a08dab326fc0"
BUILDER_SHA = "5200f9e74a6ddbefd975e4f6e1c256201cd786ee7d28820bc9240eb1b0151e88"
LOCK_SHA = "3b15a7bdf93024750835ac20584a140eb93f1dc7476be61bb0af145e8ff0cc30"
CONTEXT = (
    "backend/t44", "backend/requirements.lock", "backend/pyproject.toml",
    "specs/database", "specs/contracts", "deployment/api.Dockerfile",
    "deployment/api.Dockerfile.dockerignore", "deployment/runtime_probe.py",
    "deployment/credential_admin.py",
)
RUNTIME_EXCLUDED = {"deployment/api.Dockerfile", "deployment/api.Dockerfile.dockerignore"}
SCHEMA = "backend/t44/persistence/schema.py"
DOCKER = ["docker", "--context", "default"]
HERE = Path(__file__).resolve().parent
PROBE = """import hashlib,json,os,stat
from pathlib import Path
rows=[]
for prefix in ['backend','specs/database','specs/contracts','deployment']:
 root=Path('/app')/prefix
 for p in sorted(root.rglob('*')):
  s=p.lstat()
  if not (stat.S_ISREG(s.st_mode) or stat.S_ISDIR(s.st_mode)):
   raise ValueError('RUNTIME_LINK_OR_SPECIAL_FILE_REFUSED')
  if p.is_file():
   raw=p.read_bytes(); rows.append({'path':p.relative_to('/app').as_posix(),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'mode':stat.S_IMODE(s.st_mode)})
print(json.dumps({'uid':os.getuid(),'files':sorted(rows,key=lambda r:r['path'])}))
"""


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def sha(path):
    value = hashlib.sha256()
    with path.open("rb") as incoming:
        for block in iter(lambda: incoming.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def module(name, expected):
    path = HERE / name
    if path.is_symlink() or sha(path) != expected:
        raise ValueError("UNCHANGED_REVIEWED_HELPER_REQUIRED:" + name)
    spec = importlib.util.spec_from_file_location("r30_" + name.replace("-", "_"), path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def command(argv, timeout=120):
    return subprocess.run(
        list(map(str, argv)), check=True, capture_output=True, timeout=timeout,
        env={k: v for k, v in os.environ.items() if not k.startswith(
            ("DOCKER_", "COMPOSE_", "T44_", "MYSQL_", "RABBITMQ_"))},
    ).stdout


def write(path, raw):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "wb") as outgoing:
        outgoing.write(raw)
        outgoing.flush()
        os.fsync(outgoing.fileno())


def save(path, value):
    write(path, (json.dumps(value, indent=2) + "\n").encode())


def regular(path):
    info = path.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or path.is_symlink():
        raise ValueError("REGULAR_SINGLE_LINK_FILE_REQUIRED")
    return info


def new_directory(output):
    if not output.is_absolute() or output.parent.resolve() != output.parent:
        raise ValueError("NEW_CANONICAL_ABSOLUTE_OUTPUT_REQUIRED")
    output.mkdir(mode=0o700)


def archive_rows(raw):
    if len(raw) > 16 * 1024 * 1024:
        raise ValueError("SOURCE_ARCHIVE_TOO_LARGE")
    rows, contents, seen = [], {}, set()
    with tarfile.open(fileobj=io.BytesIO(raw), mode="r:") as archive:
        for entry in archive:
            name = entry.name.rstrip("/") if entry.isdir() else entry.name
            path = Path(name)
            allowed = any(name == p or name.startswith(p + "/") for p in CONTEXT)
            structural = entry.isdir() and any(p.startswith(name + "/") for p in CONTEXT)
            if (path.is_absolute() or ".." in path.parts or "\\" in name
                    or str(path) != name or name in seen
                    or not (entry.isfile() or entry.isdir())
                    or not (allowed or structural) or entry.size > 2 * 1024 * 1024):
                raise ValueError("UNSAFE_DUPLICATE_LINK_OR_UNEXPECTED_CONTEXT_ENTRY")
            seen.add(name)
            if entry.isdir():
                continue
            content = archive.extractfile(entry).read()
            rows.append({"path": name, "bytes": len(content), "sha256": digest(content),
                         "mode": 0o755 if entry.mode & 0o111 else 0o644})
            contents[name] = content
    return sorted(rows, key=lambda row: row["path"]), contents


def source_data(repository):
    helper = module("backend-upgrade-v2.py", BUILDER_SHA)
    if helper.git(repository, "rev-parse", SOURCE + "^{commit}").decode().strip() != SOURCE:
        raise ValueError("EXACT_0B_COMMIT_REQUIRED")
    rows = helper.tree(repository, SOURCE, CONTEXT)
    raw = helper.git(repository, "archive", "--format=tar", SOURCE, "--", *CONTEXT)
    observed, contents = archive_rows(raw)
    if rows != observed or digest(contents["backend/requirements.lock"]) != LOCK_SHA:
        raise ValueError("COMPLETE_GIT_BYTES_OR_LOCK_MISMATCH")
    before = helper.tree(repository, BASE, helper.FROZEN)
    after = helper.tree(repository, SOURCE, helper.FROZEN)
    old, new = ({r["path"]: r for r in table} for table in (before, after))
    differences = [p for p in sorted(old.keys() | new.keys()) if old.get(p) != new.get(p)]
    if differences != [SCHEMA]:
        raise ValueError("ONLY_PUBLISHED_0B_SCHEMA_IMPLEMENTATION_DIFFERENCE_ALLOWED")
    frozen = {"base_sha": BASE, "source_sha": SOURCE, "all_47_equal": False,
              "differences": [{"path": SCHEMA, "before": old[SCHEMA], "after": new[SCHEMA]}],
              "unchanged_files": [r for r in after if r["path"] != SCHEMA],
              "interpretation": "schema.py is exact published product source; canonical DDL/contracts/dependencies/frontend/support remain byte equal"}
    if contents["deployment/api.Dockerfile"].decode().splitlines()[0] != "FROM " + PYTHON:
        raise ValueError("OFFICIAL_PINNED_FROM_REQUIRED")
    return raw, rows, contents, frozen


def prepare(repository, output, run_id):
    if not re.fullmatch(r"r30[a-z0-9]{5,17}", run_id):
        raise ValueError("NEW_R30_RUN_ID_REQUIRED")
    raw, rows, _, frozen = source_data(repository)
    new_directory(output)
    write(output / "source-runtime-context.tar.gz", gzip.compress(raw, mtime=0))
    save(output / "frozen-comparison.json", frozen)
    manifest = {"kind": "r30-exact-0b-backend-context-v1", "source_sha": SOURCE,
                "run_id": run_id, "files": rows, "source_archive_sha256": digest(raw),
                "source_archive_bytes": len(raw), "context_paths": list(CONTEXT),
                "official_python": PYTHON, "dependency_lock_sha256": LOCK_SHA,
                "file_set_sha256": digest(canonical(rows)),
                "objects": {name: {"sha256": sha(output / name), "bytes": (output / name).stat().st_size}
                            for name in ["source-runtime-context.tar.gz", "frozen-comparison.json"]},
                "tool_sha256": sha(Path(__file__)),
                "business_services_or_cloud_started": False}
    save(output / "source-manifest.json", manifest)
    return manifest


def verify_source(package, expected):
    manifest_file = package / "source-manifest.json"
    regular(manifest_file)
    if not re.fullmatch(r"[a-f0-9]{64}", expected) or sha(manifest_file) != expected:
        raise ValueError("PINNED_SOURCE_MANIFEST_HASH_REQUIRED")
    value = json.loads(manifest_file.read_text())
    if (value["kind"] != "r30-exact-0b-backend-context-v1" or value["source_sha"] != SOURCE
            or value["context_paths"] != list(CONTEXT) or value["official_python"] != PYTHON
            or value["dependency_lock_sha256"] != LOCK_SHA
            or value["tool_sha256"] != sha(Path(__file__))
            or set(value["objects"]) != {"source-runtime-context.tar.gz", "frozen-comparison.json"}):
        raise ValueError("EXACT_SOURCE_SCHEMA_OR_OBJECT_SET_REQUIRED")
    for name, wanted in value["objects"].items():
        path = package / name
        if regular(path).st_size != wanted["bytes"] or sha(path) != wanted["sha256"]:
            raise ValueError("SOURCE_OBJECT_HASH_OR_SIZE_MISMATCH")
    with gzip.open(package / "source-runtime-context.tar.gz", "rb") as incoming:
        raw = incoming.read(16 * 1024 * 1024 + 1)
    if len(raw) != value["source_archive_bytes"] or digest(raw) != value["source_archive_sha256"]:
        raise ValueError("SOURCE_ARCHIVE_HASH_OR_SIZE_MISMATCH")
    rows, contents = archive_rows(raw)
    if rows != value["files"] or digest(canonical(rows)) != value["file_set_sha256"]:
        raise ValueError("COMPLETE_SOURCE_FILE_SET_REQUIRED")
    frozen = json.loads((package / "frozen-comparison.json").read_text())
    if (frozen["base_sha"] != BASE or frozen["source_sha"] != SOURCE or frozen["all_47_equal"]
            or [r["path"] for r in frozen["differences"]] != [SCHEMA]
            or len(frozen["unchanged_files"]) != 46
            or digest(contents["backend/requirements.lock"]) != LOCK_SHA):
        raise ValueError("EXPLICIT_0B_FROZEN_COMPARISON_REQUIRED")
    return value, contents


def materialize(output, manifest, contents):
    output.mkdir(mode=0o700)
    for row in manifest["files"]:
        path = output / row["path"]
        path.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
        write(path, contents[row["path"]])
        path.chmod(row["mode"])
    for path in output.rglob("*"):
        if path.is_dir():
            path.chmod(0o755)


def verify_runtime(observed, rows):
    wanted = [r for r in rows if r["path"] not in RUNTIME_EXCLUDED]
    if observed.get("uid") != 10001 or observed.get("files") != wanted:
        raise ValueError("EXACT_NONROOT_RUNTIME_FILE_BYTES_HASH_MODE_SET_REQUIRED")
    return {"uid": 10001, "exact_files": len(wanted), "stale_or_missing_files": False}


def build(repository, output, run_id):
    manifest = prepare(repository, output, run_id)
    expected = sha(output / "source-manifest.json")
    _, contents = verify_source(output, expected)
    context = output / "context"
    materialize(context, manifest, contents)
    proof = module("image-proof.py", PROOF_SHA)
    command([*DOCKER, "pull", "--platform", "linux/amd64", PYTHON], timeout=300)
    upstream = json.loads(command([*DOCKER, "image", "inspect", PYTHON]))[0]
    if (upstream["Os"] != "linux" or upstream["Architecture"] != "amd64"
            or not any(s.endswith("@" + PYTHON.split("@")[1]) for s in upstream.get("RepoDigests", []))):
        raise ValueError("OFFICIAL_UPSTREAM_REPO_DIGEST_PLATFORM_REQUIRED")
    name = "t44-backend-r30:src-" + SOURCE + "-" + run_id
    command([*DOCKER, "buildx", "build", "--load", "--platform", "linux/amd64",
             "--provenance=false", "--pull=false", "--metadata-file", output / "build-metadata.json",
             "--file", context / "deployment/api.Dockerfile", "--tag", name,
             "--label", "org.opencontainers.image.revision=" + SOURCE,
             "--label", "io.t44.source-archive-sha256=" + manifest["source_archive_sha256"],
             "--label", "io.t44.r30.source-manifest-sha256=" + expected,
             "--label", "io.t44.r30.run=" + run_id, context], timeout=900)
    archive = output / "backend-image.tar"
    command([*DOCKER, "image", "save", "--output", archive, name], timeout=180)
    graph = proof.scan_archive(archive)
    table = graph["names"]["manifest.json"]["json"]
    if len(table) != 1 or table[0]["RepoTags"] != [name]:
        raise ValueError("ONE_EXACT_BACKEND_ARCHIVE_REQUIRED")
    config_id = graph["names"][table[0]["Config"]]["digest"]
    declared = {"alias": name, "image_id": config_id, "revision_label": SOURCE,
                "archive_label": manifest["source_archive_sha256"]}
    identity = proof.prove_role(graph, "backend", declared, manifest, proof.actual_image(name))
    trusted = proof.trusted_role(graph, "backend", declared, manifest)
    upstream_diffs = upstream["RootFS"]["Layers"]
    if trusted["diff_ids"][:len(upstream_diffs)] != upstream_diffs:
        raise ValueError("OFFICIAL_UPSTREAM_ORDERED_LAYER_PREFIX_REQUIRED")
    observed = json.loads(command([*DOCKER, "run", "--rm", "--network", "none", "--read-only",
                                  "--user", "10001:10001", "--cap-drop", "ALL", "--security-opt",
                                  "no-new-privileges:true", "--entrypoint", "python", name, "-c", PROBE]))
    runtime = verify_runtime(observed, manifest["files"])
    save(output / "actual-runtime-files.json", observed)
    with archive.open("rb") as incoming:
        fd = os.open(output / "backend-image.tar.gz", os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "wb") as raw, gzip.GzipFile(filename="", fileobj=raw, mode="wb", mtime=0, compresslevel=1) as outgoing:
            for block in iter(lambda: incoming.read(1024 * 1024), b""):
                outgoing.write(block)
    bundle = {"kind": "r30-exact-0b-backend-only-image-v1", "source_sha": SOURCE,
              "run_id": run_id, "source_manifest_sha256": expected, "declared": declared,
              "source_archive_sha256": manifest["source_archive_sha256"],
              "image_identity_proof": identity, "runtime_verification": runtime,
              "official_python": {"pin": PYTHON, "repo_digests_observed": upstream["RepoDigests"],
                                  "diff_ids": upstream_diffs},
              "objects": {n: {"sha256": sha(output / n), "bytes": (output / n).stat().st_size}
                          for n in ["backend-image.tar.gz", "source-manifest.json", "source-runtime-context.tar.gz",
                                    "frozen-comparison.json", "actual-runtime-files.json", "build-metadata.json"]},
              "uncompressed_image_archive_sha256": sha(archive),
              "tool_sha256": sha(Path(__file__)), "github_run_id": os.environ.get("GITHUB_RUN_ID"),
              "cloud_or_SUT_or_performance_executed": False}
    save(output / "backend-bundle-manifest.json", bundle)
    return bundle


def verify_bundle(package, expected):
    path = package / "backend-bundle-manifest.json"
    regular(path)
    if not re.fullmatch(r"[a-f0-9]{64}", expected) or sha(path) != expected:
        raise ValueError("ROOT_PINNED_BACKEND_BUNDLE_HASH_REQUIRED")
    value = json.loads(path.read_text())
    if (value["kind"] != "r30-exact-0b-backend-only-image-v1" or value["source_sha"] != SOURCE
            or value["tool_sha256"] != sha(Path(__file__))
            or set(value["objects"]) != {"backend-image.tar.gz", "source-manifest.json", "source-runtime-context.tar.gz",
                                         "frozen-comparison.json", "actual-runtime-files.json", "build-metadata.json"}):
        raise ValueError("EXACT_BACKEND_BUNDLE_SOURCE_OBJECT_SET_REQUIRED")
    for name, wanted in value["objects"].items():
        candidate = package / name
        if regular(candidate).st_size != wanted["bytes"] or sha(candidate) != wanted["sha256"]:
            raise ValueError("BACKEND_BUNDLE_OBJECT_HASH_OR_SIZE_MISMATCH")
    source, _ = verify_source(package, value["source_manifest_sha256"])
    if source["run_id"] != value["run_id"] or source["source_archive_sha256"] != value["source_archive_sha256"]:
        raise ValueError("SOURCE_RUN_BINDING_MISMATCH")
    proof = module("image-proof.py", PROOF_SHA)
    graph = proof.scan_archive(package / "backend-image.tar.gz")
    trusted = proof.trusted_role(graph, "backend", value["declared"], source)
    official = value["official_python"]
    if (official["pin"] != PYTHON or not official["diff_ids"]
            or not any(r.endswith("@" + PYTHON.split("@")[1]) for r in official["repo_digests_observed"])
            or trusted["diff_ids"][:len(official["diff_ids"])] != official["diff_ids"]):
        raise ValueError("OFFICIAL_PIN_AND_ORDERED_LAYER_PREFIX_REQUIRED")
    verify_runtime(json.loads((package / "actual-runtime-files.json").read_text()), source["files"])
    return {"source_sha": SOURCE, "config_id": trusted["config_id"], "alias": value["declared"]["alias"],
            "archive_and_source_verified": True, "Docker_or_cloud_called": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("prepare", "build", "verify-source", "verify-bundle"))
    parser.add_argument("--repository", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--run-id")
    parser.add_argument("--package", type=Path)
    parser.add_argument("--manifest-sha256")
    args = parser.parse_args()
    os.umask(0o077)
    try:
        if args.action in {"prepare", "build"}:
            result = (build if args.action == "build" else prepare)(args.repository, args.output, args.run_id)
            print(json.dumps({"success": True, "source_sha": SOURCE, "run_id": result["run_id"],
                              "output": str(args.output), "cloud_or_SUT_started": False}))
        elif args.action == "verify-source":
            value, _ = verify_source(args.package, args.manifest_sha256)
            print(json.dumps({"success": True, "source_sha": value["source_sha"], "Docker_or_cloud_called": False}))
        else:
            print(json.dumps(verify_bundle(args.package, args.manifest_sha256)))
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError, tarfile.TarError) as error:
        failure = {"success": False, "reason": str(error), "error_class": type(error).__name__,
                   "partial_outputs_preserved": True, "cloud_lifecycle_never_called": True}
        if isinstance(error, subprocess.CalledProcessError):
            failure.update(argv=list(map(str, error.cmd)), exit_code=error.returncode,
                           stdout=error.stdout.decode(errors="replace"), stderr=error.stderr.decode(errors="replace"))
        if args.output and args.output.is_dir() and not (args.output / "first-failure.json").exists():
            save(args.output / "first-failure.json", failure)
        print(json.dumps(failure))
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
