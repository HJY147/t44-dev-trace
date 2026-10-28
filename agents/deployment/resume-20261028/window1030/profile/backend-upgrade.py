"""Pinned resume offline upgrade; normalized COPY directories despite restrictive host umask."""

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
from pathlib import Path, PurePosixPath
from uuid import uuid4

BASE = "935ab5b93bea788672c2b4a088c79cfeed848954"
TARGET = "a12e9e70b963bacafda3242bb6d82e53ee912ff1"
BASE_ALIAS = "t44-backend:src-" + BASE
WEB_ALIAS = "t44-web:src-" + BASE
PROOF_SHA = "47b50d0111737d2b4ff7b47ce37c46bc5d7fc208d2f3933088b8a08dab326fc0"
BASE_RAW_SHA = "30b1ca48f152cae797862319cdda80c0a0b65ed5af32acf4b18ea55d531cc8d0"
LOCK_SHA = "3b15a7bdf93024750835ac20584a140eb93f1dc7476be61bb0af145e8ff0cc30"
SOURCE_PATHS = ("backend/t44", "backend/requirements.lock", "backend/pyproject.toml")
FROZEN = (
    "backend/requirements.lock",
    "backend/pyproject.toml",
    "backend/t44/contracts/openapi.json",
    "backend/t44/persistence/schema.py",
    "backend/t44/persistence/schema_v1.sql",
    "specs/database",
    "specs/contracts",
    "deployment/runtime_probe.py",
    "deployment/credential_admin.py",
    "deployment/api.Dockerfile",
    "deployment/api.Dockerfile.dockerignore",
    "deployment/web.Dockerfile",
    "deployment/web.Dockerfile.dockerignore",
    "deployment/nginx",
    "frontend",
)
DOCKER = ["docker", "--context", "default"]
PROBE = """import hashlib,json,os,stat
from pathlib import Path
root=Path('/app/backend/t44'); rows=[]
for p in sorted(root.rglob('*')):
 s=p.lstat()
 if stat.S_ISLNK(s.st_mode) or not (stat.S_ISDIR(s.st_mode) or stat.S_ISREG(s.st_mode)):
  raise ValueError('UNEXPECTED_PRODUCT_FILESYSTEM_OBJECT')
 if p.is_file():
  raw=p.read_bytes()
  rows.append({'path':'backend/t44/'+p.relative_to(root).as_posix(),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'mode':stat.S_IMODE(s.st_mode)})
print(json.dumps({'files':rows,'uid':os.getuid(),'database_env_absent':not any(k in os.environ for k in ['DATABASE_URL','AMQP_URL','T44_DATABASE','MYSQL_ROOT_PASSWORD'])}))
"""


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def private(path, directory=False):
    s = path.lstat()
    if (
        path.resolve() != path
        or s.st_uid != os.geteuid()
        or stat.S_IMODE(s.st_mode) != (0o700 if directory else 0o600)
        or not (stat.S_ISDIR(s.st_mode) if directory else stat.S_ISREG(s.st_mode))
    ):
        raise ValueError("OWNED_CANONICAL_PRIVATE_OBJECT_REQUIRED")


def write(path, raw, mode=0o600):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, mode)
    with os.fdopen(fd, "wb") as f:
        f.write(raw)
    path.chmod(mode)


def save(path, value):
    write(path, (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode())


def environment():
    return {
        k: v
        for k, v in os.environ.items()
        if not k.startswith(("DOCKER_", "COMPOSE_", "T44_", "MYSQL_", "RABBITMQ_"))
    }


def command(argv, timeout=120):
    return subprocess.run(
        list(map(str, argv)),
        capture_output=True,
        check=True,
        timeout=timeout,
        env=environment(),
    ).stdout


def git(repository, *args):
    return command(["git", "-C", repository, *args])


def tree(repository, source, paths):
    rows = []
    raw = git(repository, "ls-tree", "-r", "-z", "--full-tree", source, "--", *paths)
    for item in raw.split(b"\0"):
        if not item:
            continue
        meta, name = item.split(b"\t", 1)
        mode, kind, oid = meta.decode().split()
        name = name.decode()
        safe_name(name)
        if mode not in {"100644", "100755"} or kind != "blob":
            raise ValueError("TRACKED_SOURCE_REGULAR_FILES_ONLY")
        content = git(repository, "cat-file", "blob", oid)
        rows.append(
            {
                "path": name,
                "bytes": len(content),
                "sha256": digest(content),
                "mode": int(mode[-3:], 8),
            }
        )
    return sorted(rows, key=lambda row: row["path"])


def safe_name(name):
    p = PurePosixPath(name)
    if not name or p.is_absolute() or ".." in p.parts or str(p) != name or "\\" in name:
        raise ValueError("SAFE_CANONICAL_RELATIVE_SOURCE_PATH_REQUIRED")
    return name


def compare_frozen(before, after):
    if not before or before != after:
        raise ValueError("DEPENDENCIES_REST_DDL_FRONTEND_OR_BASE_SUPPORT_CHANGED")
    lock = [r for r in after if r["path"] == "backend/requirements.lock"]
    if len(lock) != 1 or lock[0]["sha256"] != LOCK_SHA:
        raise ValueError("EXACT_EXISTING_HASH_LOCK_REQUIRED_NO_INSTALL")
    return {
        "paths": list(FROZEN),
        "files": after,
        "file_set_sha256": digest(
            json.dumps(after, sort_keys=True, separators=(",", ":")).encode()
        ),
        "base_sha": BASE,
        "target_sha": TARGET,
        "equal": True,
        "web_reuse": "original source935 web tag, same complete tracked frontend bytes/modes; no new web tag",
    }


def archive_files(raw):
    rows, contents = [], {}
    if len(raw) > 10 * 1024 * 1024:
        raise ValueError("SOURCE_ARCHIVE_SIZE_LIMIT")
    with tarfile.open(fileobj=io.BytesIO(raw), mode="r:") as archive:
        for member in archive:
            name = member.name.rstrip("/") if member.isdir() else member.name
            safe_name(name)
            if member.isdir():
                continue
            if not member.isfile() or name in contents or member.size > 2 * 1024 * 1024:
                raise ValueError("SOURCE_ARCHIVE_LINK_DUPLICATE_OR_SIZE_REFUSED")
            if not (name.startswith("backend/t44/") or name in SOURCE_PATHS[1:]):
                raise ValueError("SOURCE_ARCHIVE_UNEXPECTED_FILE")
            content = archive.extractfile(member).read()
            mode = 0o755 if member.mode & 0o111 else 0o644
            rows.append(
                {
                    "path": name,
                    "bytes": len(content),
                    "sha256": digest(content),
                    "mode": mode,
                }
            )
            contents[name] = content
    rows.sort(key=lambda row: row["path"])
    if not rows or not any(r["path"] == "backend/t44/__init__.py" for r in rows):
        raise ValueError("COMPLETE_BACKEND_PACKAGE_REQUIRED")
    return rows, contents


def dockerfile():
    return (
        "FROM " + BASE_ALIAS + "\nUSER 0:0\n"
        "RUN rm -rf /app/backend/t44\n"
        "COPY backend/t44/ /app/backend/t44/\n"
        "COPY backend/requirements.lock backend/pyproject.toml /app/backend/\n"
        "USER 10001:10001\n"
    ).encode()


def prepare(args):
    if (
        git(args.repository, "rev-parse", TARGET + "^{commit}").decode().strip()
        != TARGET
    ):
        raise ValueError("EXACT_TARGET_COMMIT_REQUIRED")
    old = tree(args.repository, BASE, FROZEN)
    new = tree(args.repository, TARGET, FROZEN)
    unchanged = compare_frozen(old, new)
    expected = tree(args.repository, TARGET, SOURCE_PATHS)
    raw = git(args.repository, "archive", "--format=tar", TARGET, "--", *SOURCE_PATHS)
    actual, _ = archive_files(raw)
    if actual != expected:
        raise ValueError("ACTUAL_GIT_ARCHIVE_BYTES_NOT_COMPLETE_TRACKED_SOURCE")
    private(args.output.parent, True)
    args.output.mkdir(mode=0o700)
    write(args.output / "source-backend.tar", raw)
    gz = gzip.compress(raw, mtime=0)
    write(args.output / "source-backend.tar.gz", gz)
    save(args.output / "frozen-equality.json", unchanged)
    write(args.output / "Dockerfile", dockerfile())
    manifest = {
        "kind": "exact-source935-to-resume-offline-backend-upgrade",
        "base_source_sha": BASE,
        "source_sha": TARGET,
        "source_paths": list(SOURCE_PATHS),
        "source_archive_sha256": digest(raw),
        "compressed_source_archive_sha256": digest(gz),
        "source_archive_bytes": len(raw),
        "files": expected,
        "dependency_lock_sha256": LOCK_SHA,
        "frozen_equality_sha256": sha(args.output / "frozen-equality.json"),
        "frozen_file_set_sha256": unchanged["file_set_sha256"],
        "dockerfile_sha256": digest(dockerfile()),
        "preparer_sha256": sha(Path(__file__)),
        "docker_or_business_service_started": False,
    }
    save(args.output / "source-manifest.json", manifest)
    return {
        "success": True,
        "source_sha": TARGET,
        "manifest_path": str(args.output / "source-manifest.json"),
        "manifest_sha256": sha(args.output / "source-manifest.json"),
        "source_archive_sha256": digest(raw),
        "compressed_bytes": len(gz),
        "files": len(expected),
        "frozen_comparison_passed": True,
        "docker_or_business_service_started": False,
    }


def source_package(directory, expected):
    private(directory, True)
    path = directory / "source-manifest.json"
    private(path)
    if not re.fullmatch(r"[0-9a-f]{64}", expected) or sha(path) != expected:
        raise ValueError("ROOT_PINNED_SOURCE_MANIFEST_SHA_REQUIRED")
    value = json.loads(path.read_text())
    if (
        value["kind"] != "exact-source935-to-resume-offline-backend-upgrade"
        or value["source_sha"] != TARGET
        or value["base_source_sha"] != BASE
        or value["source_paths"] != list(SOURCE_PATHS)
        or value["dependency_lock_sha256"] != LOCK_SHA
        or value["dockerfile_sha256"] != digest(dockerfile())
        or value["preparer_sha256"] != sha(Path(__file__))
    ):
        raise ValueError("EXACT_UPGRADE_SOURCE_AND_DEPENDENCY_IDENTITY_REQUIRED")
    for name, field in [
        ("source-backend.tar.gz", "compressed_source_archive_sha256"),
        ("frozen-equality.json", "frozen_equality_sha256"),
        ("Dockerfile", "dockerfile_sha256"),
    ]:
        private(directory / name)
        if sha(directory / name) != value[field]:
            raise ValueError("PINNED_SOURCE_PACKAGE_OBJECT_CHANGED")
    raw = gzip.decompress((directory / "source-backend.tar.gz").read_bytes())
    if (
        len(raw) != value["source_archive_bytes"]
        or digest(raw) != value["source_archive_sha256"]
    ):
        raise ValueError("ACTUAL_SOURCE_ARCHIVE_HASH_OR_SIZE_MISMATCH")
    rows, contents = archive_files(raw)
    if rows != value["files"]:
        raise ValueError("EXACT_COMPLETE_SOURCE_FILE_SET_REQUIRED")
    frozen = json.loads((directory / "frozen-equality.json").read_text())
    compare_frozen(frozen["files"], frozen["files"])
    commitment = digest(
        json.dumps(frozen["files"], sort_keys=True, separators=(",", ":")).encode()
    )
    if (
        not frozen["equal"]
        or frozen["paths"] != list(FROZEN)
        or frozen["base_sha"] != BASE
        or frozen["target_sha"] != TARGET
        or commitment != value["frozen_file_set_sha256"]
    ):
        raise ValueError("FROZEN_EQUALITY_COMMITMENT_REQUIRED")
    if digest(contents["backend/requirements.lock"]) != LOCK_SHA:
        raise ValueError("LOCK_BYTES_MISMATCH")
    return value, contents


def proof_module(path):
    private(path)
    if sha(path) != PROOF_SHA:
        raise ValueError("FROZEN_CRYPTO_PROOF_MODULE_REQUIRED")
    spec = importlib.util.spec_from_file_location("frozen_image_proof", path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def base_images(path, proof):
    private(path)
    if sha(path) != BASE_RAW_SHA:
        raise ValueError("EXACT_ROOT_PROVEN_SEVEN_IMAGE_RAW_REQUIRED")
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    if (
        rows[-1].get("kind") != "proof_final"
        or not rows[-1]["complete"]
        or not rows[-1]["all_seven_proven"]
    ):
        raise ValueError("COMPLETE_ORIGINAL_IMAGE_PROOF_REQUIRED")
    result = {}
    for role, name in [("backend", BASE_ALIAS), ("web", WEB_ALIAS)]:
        matches = [
            r for r in rows if r.get("kind") == "role_proof" and r.get("role") == role
        ]
        if (
            len(matches) != 1
            or not matches[0]["proof"]["success"]
            or matches[0]["declared_CI"]["alias"] != name
        ):
            raise ValueError("EXACT_PROVEN_SOURCE935_BASE_AND_WEB_REQUIRED")
        row = matches[0]
        actual = proof.actual_image(name)
        old = row["actual_projection_no_Env_or_Cmd"]
        if any(
            actual[key] != old[key]
            for key in [
                "Id",
                "Descriptor",
                "RootFS",
                "Os",
                "Architecture",
                "Variant",
                "Config",
            ]
        ):
            raise ValueError("PROVEN_BASE_OR_WEB_CHANGED_NO_FALLBACK")
        result[role] = {
            "alias": name,
            "CI_config_id": row["proof"]["config_id"],
            "actual": actual,
        }
    return result


def inspect_configuration(image, labels, base_config):
    rows = json.loads(command([*DOCKER, "image", "inspect", image]))
    if len(rows) != 1:
        raise ValueError("ONE_EXACT_DERIVED_BACKEND_IMAGE_REQUIRED")
    row = rows[0]
    config = row["Config"]
    if (
        row["Os"] != "linux"
        or row["Architecture"] != "amd64"
        or config.get("Labels") != labels
    ):
        raise ValueError("DERIVED_BACKEND_PLATFORM_OR_LABELS_MISMATCH")
    if config.get("User") != "10001:10001" or config.get("WorkingDir") != "/app":
        raise ValueError("ORIGINAL_NONROOT_BACKEND_CONFIGURATION_REQUIRED")
    for field in [
        "Env",
        "Cmd",
        "Entrypoint",
        "User",
        "WorkingDir",
        "ExposedPorts",
        "Volumes",
        "StopSignal",
        "Healthcheck",
        "Shell",
    ]:
        if config.get(field) != base_config.get(field):
            raise ValueError("ORIGINAL_RUNTIME_CONFIGURATION_CHANGED_" + field)
    env = dict(v.split("=", 1) for v in config.get("Env") or [])
    if any(
        k in env
        for k in ["DATABASE_URL", "AMQP_URL", "T44_DATABASE", "MYSQL_ROOT_PASSWORD"]
    ):
        raise ValueError("BUSINESS_ENV_FORBIDDEN_IN_BUILD_IMAGE")
    return {
        k: row.get(k)
        for k in ["Id", "Descriptor", "RootFS", "Os", "Architecture", "Variant"]
    } | {"Config": {"Labels": labels}}


def verify_product_files(observed, expected):
    wanted = [r for r in expected if r["path"].startswith("backend/t44/")]
    if (
        observed.get("uid") != 10001
        or not observed.get("database_env_absent")
        or observed.get("files") != wanted
    ):
        raise ValueError(
            "ACTUAL_CONTAINER_PRODUCT_FILE_SET_HASH_MODE_OR_ISOLATION_MISMATCH"
        )
    return {
        "complete_exact_file_set": True,
        "files": len(wanted),
        "no_stale_source935_files": True,
        "uid": 10001,
    }


def materialize_context(context, manifest, contents):
    context.mkdir(mode=0o700)
    for record in manifest["files"]:
        target = context / record["path"]
        target.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
        write(target, contents[record["path"]], record["mode"])
    # umask077 narrows mkdir(0755) to0700. COPY preserves nested directory modes:
    # root-owned source must remain readable/traversable by the restored UID10001.
    for directory in context.rglob("*"):
        if directory.is_dir():
            directory.chmod(0o755)
    write(context / "Dockerfile", dockerfile(), 0o644)


def build(args):
    if os.geteuid() != 0 or not re.fullmatch(r"[a-z][a-z0-9]{5,15}", args.run_id):
        raise ValueError("ROOT_AND_NEW_BUILD_RUNID_REQUIRED")
    manifest, contents = source_package(args.package, args.manifest_sha256)
    proof = proof_module(args.image_proof)
    bases = base_images(args.proof_raw, proof)
    base_config = json.loads(command([*DOCKER, "image", "inspect", BASE_ALIAS]))[0][
        "Config"
    ]
    name = "t44-backend-upgrade:src-" + TARGET + "-" + args.run_id
    existing = subprocess.run(
        [*DOCKER, "image", "inspect", name],
        capture_output=True,
        check=False,
        timeout=15,
        env=environment(),
    )
    if existing.returncode == 0:
        raise ValueError("NEW_ALIAS_REQUIRED_NO_RETAG_OR_OVERWRITE")
    if existing.returncode != 1 or b"no such image" not in existing.stderr.lower():
        raise ValueError("NEW_ALIAS_ABSENCE_NOT_PROVEN")
    private(args.output.parent, True)
    args.output.mkdir(mode=0o700)
    context = args.output / "context"
    materialize_context(context, manifest, contents)
    labels = dict(base_config.get("Labels") or {})
    labels.update(
        {
            "org.opencontainers.image.revision": TARGET,
            "io.t44.source-archive-sha256": manifest["source_archive_sha256"],
            "io.t44.upgrade.base-revision": BASE,
            "io.t44.upgrade.base-config-id": bases["backend"]["CI_config_id"],
            "io.t44.upgrade.base-descriptor-id": bases["backend"]["actual"]["Id"],
            "io.t44.upgrade.source-manifest-sha256": args.manifest_sha256,
            "io.t44.upgrade.dockerfile-sha256": digest(dockerfile()),
            "io.t44.upgrade.kind": "offline-full-t44-replacement",
            "io.t44.upgrade.run": args.run_id,
        }
    )
    label_args = [
        v for k, value in labels.items() for v in ["--label", k + "=" + value]
    ]
    stdout = command(
        [
            *DOCKER,
            "build",
            "--platform",
            "linux/amd64",
            "--provenance=false",
            "--metadata-file",
            args.output / "build-metadata.json",
            "--pull=false",
            "--network",
            "none",
            "--file",
            context / "Dockerfile",
            "--tag",
            name,
            *label_args,
            context,
        ],
        timeout=300,
    )
    write(args.output / "build.stdout", stdout)
    actual = inspect_configuration(name, labels, base_config)
    archive = args.output / "derived-backend.tar"
    fd = os.open(archive, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "wb") as stream:
        subprocess.run(
            [*DOCKER, "image", "save", name],
            stdout=stream,
            stderr=subprocess.PIPE,
            check=True,
            timeout=180,
            env=environment(),
        )
    graph = proof.scan_archive(archive)
    table = graph["names"]["manifest.json"]["json"]
    rows = [
        r for r in table if name in [proof.alias(t) for t in r.get("RepoTags") or []]
    ]
    if len(rows) != 1:
        raise ValueError("EXACT_DERIVED_BACKEND_ARCHIVE_TAG_REQUIRED")
    config_id = graph["names"][rows[0]["Config"]]["digest"]
    declared = {
        "alias": name,
        "image_id": config_id,
        "revision_label": TARGET,
        "archive_label": manifest["source_archive_sha256"],
    }
    identity = proof.prove_role(
        graph,
        "backend",
        declared,
        {
            "source_sha": TARGET,
            "source_archive_sha256": manifest["source_archive_sha256"],
        },
        actual,
    )
    argv = [
        *DOCKER,
        "run",
        "--rm",
        "--network",
        "none",
        "--read-only",
        "--user",
        "10001:10001",
        "--cap-drop",
        "ALL",
        "--security-opt",
        "no-new-privileges:true",
        "--entrypoint",
        "python",
        name,
        "-c",
        PROBE,
    ]
    observed = json.loads(command(argv))
    save(args.output / "actual-container-files.json", observed)
    files_proof = verify_product_files(observed, manifest["files"])
    base_images(args.proof_raw, proof)
    binding = {
        "kind": "offline-exact-source-backend-derived-build-only",
        "source_sha": TARGET,
        "base_source_sha": BASE,
        "run_id": args.run_id,
        "image_alias": name,
        "actual_image_id": actual["Id"],
        "config_id": config_id,
        "actual_descriptor": actual["Descriptor"],
        "expected_labels": labels,
        "source_manifest_sha256": args.manifest_sha256,
        "source_archive_sha256": manifest["source_archive_sha256"],
        "dependency_lock_sha256": LOCK_SHA,
        "frozen_file_set_sha256": manifest["frozen_file_set_sha256"],
        "dockerfile_sha256": digest(dockerfile()),
        "build_metadata_sha256": sha(args.output / "build-metadata.json"),
        "derived_image_archive_sha256": sha(archive),
        "identity_proof": identity,
        "actual_container_files_sha256": sha(
            args.output / "actual-container-files.json"
        ),
        "file_set_verification": files_proof,
        "bases_unchanged_after_build": bases,
        "web_reuse_original_tag": WEB_ALIAS,
        "old_backend_tag_unchanged": BASE_ALIAS,
        "builder_sha256": sha(Path(__file__)),
        "attestation_policy": "local single-platform image, registry attestation disabled; independent metadata and full archived OCI config/layer proof retained",
        "network": "none; pull=false; no pip/install/download",
        "business_services_started": False,
        "databases_or_volumes_modified": False,
    }
    save(args.output / "upgrade-binding.json", binding)
    return {
        "success": True,
        "source_sha": TARGET,
        "binding_path": str(args.output / "upgrade-binding.json"),
        "binding_sha256": sha(args.output / "upgrade-binding.json"),
        "image_alias": name,
        "actual_image_id": actual["Id"],
        "config_id": config_id,
        "product_file_set": files_proof,
        "business_services_started": False,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("prepare", "build"))
    parser.add_argument("--repository", type=Path)
    parser.add_argument("--package", type=Path)
    parser.add_argument("--manifest-sha256")
    parser.add_argument("--image-proof", type=Path)
    parser.add_argument("--proof-raw", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--run-id")
    args = parser.parse_args()
    os.umask(0o077)
    try:
        print(json.dumps(prepare(args) if args.action == "prepare" else build(args)))
    except (
        OSError,
        ValueError,
        KeyError,
        TypeError,
        subprocess.SubprocessError,
        tarfile.TarError,
    ) as error:
        failure = None
        if args.output.is_dir():
            failure = args.output / ("failure-" + uuid4().hex + ".json")
            details = {
                "error_class": type(error).__name__,
                "reason": str(error),
                "partial_state_preserved": True,
            }
            if isinstance(error, subprocess.CalledProcessError):
                details.update(
                    stdout=(error.stdout or b"").decode(errors="replace"),
                    stderr=(error.stderr or b"").decode(errors="replace"),
                )
            save(failure, details)
        print(
            json.dumps(
                {
                    "success": False,
                    "error": "OFFLINE_BACKEND_UPGRADE_REFUSED",
                    "private_failure_path": str(failure) if failure else None,
                    "business_services_started": False,
                }
            )
        )
        raise SystemExit(1) from None
