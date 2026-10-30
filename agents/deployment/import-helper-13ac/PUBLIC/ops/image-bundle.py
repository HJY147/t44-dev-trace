"""Build an exact public-source image bundle, or verify/load its explicitly trusted manifest."""

import argparse
import gzip
import hashlib
import io
import json
import os
import platform
import re
import shutil
import stat
import subprocess
import tarfile
from datetime import datetime, timezone
from pathlib import Path

PINS = {
    "python": "python:3.12-slim-bookworm@sha256:6a0e06f5ba0b373d051aabd3fffb9b873f27f9a2a3a14bcbe37dee6f0e3bbc70",
    "node": "node:24-bookworm-slim@sha256:55fb5f5a527ea2c5c4a95f963e48ef90aa38c7b346054fdc8ee9957a2b55d205",
    "nginx": "nginx:stable-alpine@sha256:47928bf67eb62a1863cb08d9ecb52d3e704304ba614eaee17884204677702951",
    "mysql": "mysql:8.4@sha256:76f0358884cb92d9a086d24e5671c38048d3fef40f2588703d73eb55392d6b69",
    "rabbitmq": "rabbitmq:4-management-alpine@sha256:0452ee3fd3b9a74160b251e693338616b464f22df4d4ba43304c101bebdca292",
}
SUBSET = (
    "backend/t44",
    "backend/requirements.lock",
    "backend/pyproject.toml",
    "specs/database",
    "specs/contracts",
    "deployment/api.Dockerfile",
    "deployment/api.Dockerfile.dockerignore",
    "deployment/web.Dockerfile",
    "deployment/web.Dockerfile.dockerignore",
    "deployment/runtime_probe.py",
    "deployment/credential_admin.py",
    "deployment/nginx",
    "frontend/src",
    "frontend/scripts",
    "frontend/public",
    "frontend/package.json",
    "frontend/pnpm-lock.yaml",
    "frontend/tsconfig.json",
    "frontend/vite.config.ts",
    "frontend/index.html",
)
EXPECTED_LOCK = "3b15a7bdf93024750835ac20584a140eb93f1dc7476be61bb0af145e8ff0cc30"
DOCKER = ["docker", "--context", "default"]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def file_digest(path):
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def gzip_digest(path):
    value = hashlib.sha256()
    size = 0
    with gzip.open(path, "rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            size += len(block)
            if size > 20 * 1024**3:
                raise ValueError("UNCOMPRESSED_ARCHIVE_SIZE_LIMIT")
            value.update(block)
    return value.hexdigest()


def save(path, data):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "wb") as stream:
        stream.write(data)


def command(argv, *, timeout=600):
    environment = {
        key: value
        for key, value in os.environ.items()
        if key not in {"DOCKER_HOST", "DOCKER_CONTEXT"}
    }
    return subprocess.run(
        list(map(str, argv)),
        check=True,
        capture_output=True,
        timeout=timeout,
        env=environment,
    ).stdout


def regular(path):
    info = path.lstat()
    if (
        not stat.S_ISREG(info.st_mode)
        or info.st_nlink != 1
        or info.st_uid != os.geteuid()
    ):
        raise ValueError("OWNED_REGULAR_SINGLE_LINK_FILE_REQUIRED")
    return info


def extract_context(raw, output):
    """Only the declared public build subset; reject links and private filenames before writes."""
    with tarfile.open(fileobj=io.BytesIO(raw)) as archive:
        members = archive.getmembers()
        for member in members:
            path = Path(member.name)
            allowed = any(
                member.name == prefix or member.name.startswith(prefix + "/")
                for prefix in SUBSET
            )
            structural = member.isdir() and any(
                prefix.startswith(member.name + "/") for prefix in SUBSET
            )
            if (
                path.is_absolute()
                or ".." in path.parts
                or not (allowed or structural)
                or not (member.isfile() or member.isdir())
                or any(p.startswith(".env") for p in path.parts)
                or path.suffix.lower() in {".pem", ".key", ".p12", ".pfx"}
            ):
                raise ValueError("UNEXPECTED_OR_PRIVATE_BUILD_ARCHIVE_ENTRY")
        output.mkdir(mode=0o700)
        for member in members:
            target = output / member.name
            if member.isdir():
                target.mkdir(mode=0o755, parents=True, exist_ok=True)
                target.chmod(0o755)
            else:
                target.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
                save(target, archive.extractfile(member).read())
                target.chmod(0o755 if member.mode & 0o111 else 0o644)


def inspect_image(alias):
    result = json.loads(command([*DOCKER, "image", "inspect", alias]))
    if len(result) != 1:
        raise ValueError("ONE_IMAGE_REQUIRED")
    row = result[0]
    if (
        row["Os"] != "linux"
        or row["Architecture"] != "amd64"
        or not re.fullmatch(r"sha256:[0-9a-f]{64}", row["Id"])
    ):
        raise ValueError("LINUX_AMD64_CONFIG_ID_REQUIRED")
    return {
        "image_id": row["Id"],
        "os": row["Os"],
        "architecture": row["Architecture"],
        "repo_digests_observed_in_CI": row.get("RepoDigests", []),
        "revision_label": (row["Config"].get("Labels") or {}).get(
            "org.opencontainers.image.revision"
        ),
        "archive_label": (row["Config"].get("Labels") or {}).get(
            "io.t44.source-archive-sha256"
        ),
    }


def compress(source, output):
    fd = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with (
        source.open("rb") as incoming,
        os.fdopen(fd, "wb") as raw,
        gzip.GzipFile(
            filename="", fileobj=raw, mode="wb", compresslevel=1, mtime=0
        ) as outgoing,
    ):
        shutil.copyfileobj(incoming, outgoing, 1024 * 1024)


def build(repository, source, output):
    if not re.fullmatch(r"[0-9a-f]{40}", source):
        raise ValueError("FULL_PRODUCT_COMMIT_REQUIRED")
    if (
        output.exists()
        or not output.is_absolute()
        or output.parent.resolve() != output.parent
    ):
        raise ValueError("NEW_ABSOLUTE_OUTPUT_REQUIRED")
    output.mkdir(mode=0o700)
    raw = command(["git", "-C", repository, "archive", source, *SUBSET])
    source_sha = digest(raw)
    archive = output / "source-runtime-context.tar"
    save(archive, raw)
    context = output / "context"
    extract_context(raw, context)
    if file_digest(context / "backend/requirements.lock") != EXPECTED_LOCK:
        raise ValueError("DEPENDENCY_LOCK_CHANGED_REVIEW_REQUIRED")
    api = (context / "deployment/api.Dockerfile").read_text()
    web = (context / "deployment/web.Dockerfile").read_text()
    compose = command(
        ["git", "-C", repository, "show", source + ":compose.yaml"]
    ).decode()
    for name, pin in PINS.items():
        origin = (
            api if name == "python" else web if name in {"node", "nginx"} else compose
        )
        if origin.count(pin) != 1:
            raise ValueError("OFFICIAL_IMAGE_PIN_CHANGED_REVIEW_REQUIRED")
    if re.findall(r"^FROM\s+(\S+)", api, re.MULTILINE) != [
        PINS["python"]
    ] or re.findall(r"^FROM\s+(\S+)", web, re.MULTILINE) != [
        PINS["node"],
        PINS["nginx"],
    ]:
        raise ValueError("EXACT_OFFICIAL_FROM_SET_REQUIRED")
    images = {}
    for role, upstream in PINS.items():
        command([*DOCKER, "pull", "--platform", "linux/amd64", upstream], timeout=300)
        alias = "t44-official-" + role + ":" + upstream.split("sha256:")[1]
        observed = inspect_image(upstream)
        upstream_digest = upstream.split("@")[1]
        if not any(
            row.endswith("@" + upstream_digest)
            for row in observed["repo_digests_observed_in_CI"]
        ):
            raise ValueError("PULLED_UPSTREAM_DIGEST_NOT_OBSERVED")
        command([*DOCKER, "tag", upstream, alias])
        images[role] = {"alias": alias, "official_upstream_pin": upstream, **observed}
    for role, dockerfile in [("backend", "api"), ("web", "web")]:
        alias = "t44-" + role + ":src-" + source
        command(
            [
                *DOCKER,
                "build",
                "--platform",
                "linux/amd64",
                "--pull=false",
                "--file",
                context / ("deployment/" + dockerfile + ".Dockerfile"),
                "--label",
                "org.opencontainers.image.revision=" + source,
                "--label",
                "io.t44.source-archive-sha256=" + source_sha,
                "--tag",
                alias,
                context,
            ],
            timeout=1200,
        )
        images[role] = {
            "alias": alias,
            "official_upstream_pin": None,
            **inspect_image(alias),
        }
    image_tar = output / "images.tar"
    if image_tar.exists():
        raise ValueError("NEW_IMAGE_ARCHIVE_REQUIRED")
    command(
        [
            *DOCKER,
            "image",
            "save",
            "--output",
            image_tar,
            *(row["alias"] for row in images.values()),
        ],
        timeout=300,
    )
    compress(image_tar, output / "images.tar.gz")
    compress(archive, output / "source-runtime-context.tar.gz")
    manifest = {
        "schema": 1,
        "source_sha": source,
        "source_archive_sha256": source_sha,
        "built_utc": datetime.now(timezone.utc).isoformat(),  # noqa: UP017 - Ubuntu22 loader supports Python3.10
        "platform": "linux/amd64",
        "tool_git_sha": command(["git", "-C", repository, "rev-parse", "HEAD"])
        .decode()
        .strip(),
        "tool_sha256": file_digest(Path(__file__)),
        "github_run_id": os.environ.get("GITHUB_RUN_ID"),
        "dependency_lock_sha256": file_digest(context / "backend/requirements.lock"),
        "build_context_subset": list(SUBSET),
        "images": images,
        "files": {
            name: {
                "sha256": file_digest(output / name),
                "bytes": (output / name).stat().st_size,
            }
            for name in ["images.tar.gz", "source-runtime-context.tar.gz"]
        },
        "uncompressed_image_archive_sha256": file_digest(image_tar),
        "runtime_credentials_or_data_included": False,
        "application_or_performance_executed": False,
        "transport_identity": "upstream digest observed in CI; config image ID checked after save/load; RepoDigests retention not assumed",
    }
    save(
        output / "bundle-manifest.json",
        (json.dumps(manifest, indent=2) + "\n").encode(),
    )
    return {
        "success": True,
        "source_sha": source,
        "source_archive_sha256": source_sha,
        "manifest_sha256": file_digest(output / "bundle-manifest.json"),
        "manifest_path": str(output / "bundle-manifest.json"),
        "images_bytes": manifest["files"]["images.tar.gz"]["bytes"],
        "cloud_deployment_or_acceptance": False,
    }


def verify(bundle, expected):
    if not re.fullmatch(r"[0-9a-f]{64}", expected):
        raise ValueError("ROOT_VERIFIED_MANIFEST_SHA_REQUIRED")
    path = bundle / "bundle-manifest.json"
    regular(path)
    if file_digest(path) != expected:
        raise ValueError("MANIFEST_HASH_MISMATCH")
    manifest = json.loads(path.read_text())
    if (
        manifest["schema"] != 1
        or not re.fullmatch(r"[0-9a-f]{40}", manifest["source_sha"])
        or manifest["platform"] != "linux/amd64"
    ):
        raise ValueError("EXACT_BUNDLE_SCHEMA_SOURCE_PLATFORM_REQUIRED")
    if set(manifest["files"]) != {
        "images.tar.gz",
        "source-runtime-context.tar.gz",
    } or set(manifest["images"]) != {*PINS, "backend", "web"}:
        raise ValueError("EXACT_BUNDLE_OBJECT_SET_REQUIRED")
    for name, row in manifest["files"].items():
        file = bundle / name
        if regular(file).st_size != row["bytes"] or file_digest(file) != row["sha256"]:
            raise ValueError("ARCHIVE_BYTES_OR_HASH_MISMATCH")
    if manifest["dependency_lock_sha256"] != EXPECTED_LOCK:
        raise ValueError("DEPENDENCY_LOCK_CHANGED_REVIEW_REQUIRED")
    if (
        gzip_digest(bundle / "source-runtime-context.tar.gz")
        != manifest["source_archive_sha256"]
        or gzip_digest(bundle / "images.tar.gz")
        != manifest["uncompressed_image_archive_sha256"]
    ):
        raise ValueError("UNCOMPRESSED_SOURCE_OR_IMAGE_ARCHIVE_HASH_MISMATCH")
    for role, row in manifest["images"].items():
        expected_alias = (
            "t44-official-" + role + ":" + PINS[role].split("sha256:")[1]
            if role in PINS
            else "t44-" + role + ":src-" + manifest["source_sha"]
        )
        if (
            row["alias"] != expected_alias
            or not re.fullmatch(r"sha256:[0-9a-f]{64}", row["image_id"])
            or row["os"] != "linux"
            or row["architecture"] != "amd64"
            or row["official_upstream_pin"] != PINS.get(role)
        ):
            raise ValueError("EXACT_IMAGE_ALIAS_CONFIG_OR_UPSTREAM_REQUIRED")
        if role in {"backend", "web"} and (
            row["revision_label"] != manifest["source_sha"]
            or row["archive_label"] != manifest["source_archive_sha256"]
        ):
            raise ValueError("BUILT_IMAGE_SOURCE_BINDING_MISMATCH")
    return manifest


def load(bundle, expected):
    manifest = verify(bundle, expected)
    if platform.system() != "Linux" or platform.machine() not in {"x86_64", "amd64"}:
        raise ValueError("DESIGNATED_LINUX_AMD64_HOST_REQUIRED")
    if shutil.disk_usage(bundle).free < 12 * 1024**3:
        raise ValueError("TWELVE_GIB_FREE_REQUIRED_BEFORE_LOAD")
    for row in manifest["images"].values():
        result = subprocess.run(
            [*DOCKER, "image", "inspect", "--format", "{{.Id}}", row["alias"]],
            capture_output=True,
            timeout=10,
            check=False,
            env={
                key: value
                for key, value in os.environ.items()
                if key not in {"DOCKER_HOST", "DOCKER_CONTEXT"}
            },
        )
        if result.returncode == 0 and result.stdout.decode().strip() != row["image_id"]:
            raise ValueError("EXISTING_ALIAS_DIFFERS_REFUSE_OVERWRITE")
    command(
        [*DOCKER, "image", "load", "--input", bundle / "images.tar.gz"], timeout=600
    )
    for row in manifest["images"].values():
        actual = inspect_image(row["alias"])
        if (
            actual["image_id"] != row["image_id"]
            or actual["revision_label"] != row["revision_label"]
            or actual["archive_label"] != row["archive_label"]
        ):
            raise ValueError("LOADED_IMAGE_CONFIG_OR_LABEL_MISMATCH")
    backend = manifest["images"]["backend"]["alias"]
    services = {
        name: {"image": backend, "pull_policy": "never"}
        for name in [
            "api",
            "consumer",
            "scheduler",
            "migrate",
            "admin",
            "credential-admin",
        ]
    }
    services.update(
        {
            name: {"image": manifest["images"][role]["alias"], "pull_policy": "never"}
            for name, role in [
                ("mysql", "mysql"),
                ("rabbitmq", "rabbitmq"),
                ("web", "web"),
            ]
        }
    )
    save(
        bundle / "images-overlay.json",
        (json.dumps({"services": services}, indent=2) + "\n").encode(),
    )
    return {
        "success": True,
        "source_sha": manifest["source_sha"],
        "manifest_sha256": expected,
        "image_ids": {
            name: row["image_id"] for name, row in manifest["images"].items()
        },
        "images_overlay_path": str(bundle / "images-overlay.json"),
        "services_started": False,
        "volumes_or_data_removed": False,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("build", "verify", "load"))
    parser.add_argument("--repository", type=Path)
    parser.add_argument("--source-sha")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--bundle", type=Path)
    parser.add_argument("--manifest-sha256")
    args = parser.parse_args()
    os.umask(0o077)
    try:
        value = (
            build(args.repository, args.source_sha, args.output)
            if args.action == "build"
            else load(args.bundle, args.manifest_sha256)
            if args.action == "load"
            else {
                "success": True,
                "source_sha": verify(args.bundle, args.manifest_sha256)["source_sha"],
                "docker_not_called": True,
            }
        )
        print(json.dumps(value))
    except (
        OSError,
        ValueError,
        KeyError,
        TypeError,
        subprocess.SubprocessError,
        tarfile.TarError,
    ) as error:
        if args.action == "build" and args.output and args.output.is_dir():
            failure = {
                "error_class": type(error).__name__,
                "source_sha": args.source_sha,
                "partial_outputs_preserved": True,
                "docker_background_cleanup_not_proven": True,
            }
            if isinstance(error, subprocess.CalledProcessError):
                failure.update(
                    exit_code=error.returncode,
                    argv=list(map(str, error.cmd)),
                    stdout=error.stdout.decode(errors="replace")
                    if error.stdout
                    else "",
                    stderr=error.stderr.decode(errors="replace")
                    if error.stderr
                    else "",
                )
            elif isinstance(error, subprocess.TimeoutExpired):
                failure.update(timed_out=True, argv=list(map(str, error.cmd)))
            else:
                failure["reason"] = str(error)
            save(
                args.output / "build-failure.json",
                (json.dumps(failure, indent=2) + "\n").encode(),
            )
        print(
            json.dumps(
                {
                    "success": False,
                    "error": "EXACT_IMAGE_BUNDLE_STEP_REFUSED",
                    "error_class": type(error).__name__,
                    "partial_outputs_preserved": True,
                }
            )
        )
        raise SystemExit(1) from None
