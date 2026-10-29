"""Offline tool-only Python+crypto derivation; two fixed proven bases, no product filesystem in final."""

import argparse
import hashlib
import importlib.util
import json
import os
import re
import stat
import subprocess
from pathlib import Path
from uuid import uuid4

PROOF_CODE_SHA = "47b50d0111737d2b4ff7b47ce37c46bc5d7fc208d2f3933088b8a08dab326fc0"
BASE_PROOF_RAW_SHA = "30b1ca48f152cae797862319cdda80c0a0b65ed5af32acf4b18ea55d531cc8d0"
BACKEND = "t44-backend:src-935ab5b93bea788672c2b4a088c79cfeed848954"
PYTHON = "t44-official-python:6a0e06f5ba0b373d051aabd3fffb9b873f27f9a2a3a14bcbe37dee6f0e3bbc70"
DOCKER = ["docker", "--context", "default"]
PROBE = """import importlib.util,json,os,ssl,sys,cryptography
assert importlib.util.find_spec('t44') is None
assert not any(os.path.exists(p) for p in ['/app/backend','/app/specs','/app/deployment'])
assert os.environ.get('PYTHONPATH','') == ''
assert not any(k in os.environ for k in ['DATABASE_URL','AMQP_URL','T44_DATABASE','MYSQL_ROOT_PASSWORD'])
print(json.dumps({'python':sys.version,'cryptography':cryptography.__version__,'ssl':ssl.OPENSSL_VERSION,'t44_spec_is_none':True,'product_paths_absent':True,'PYTHONPATH_empty':True,'app_env_absent':True}))
"""


def dockerfile():
    return (
        "FROM " + BACKEND + " AS dependencies\nFROM " + PYTHON + " AS tool\n"
        "COPY --from=dependencies /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages\n"
        'ENV PYTHONPATH="" PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1\n'
        'WORKDIR /diagnostic\nUSER 10001:10001\nCMD ["python"]\n'
    ).encode()


def sha(path):
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def private(path, directory=False):
    info = path.lstat()
    if (
        path.resolve() != path
        or info.st_uid != os.geteuid()
        or stat.S_IMODE(info.st_mode) != (0o700 if directory else 0o600)
        or not (stat.S_ISDIR(info.st_mode) if directory else stat.S_ISREG(info.st_mode))
    ):
        raise ValueError("OWNED_PRIVATE_CANONICAL_OBJECT_REQUIRED")


def write(path, data):
    descriptor = os.open(
        path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600
    )
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(data)


def save(path, value):
    write(path, (json.dumps(value, indent=2) + "\n").encode())


def environment():
    return {
        key: value
        for key, value in os.environ.items()
        if not key.startswith(("DOCKER_", "COMPOSE_", "T44_", "MYSQL_", "RABBITMQ_"))
    }


def command(argv, timeout=120):
    return subprocess.run(
        list(map(str, argv)),
        capture_output=True,
        check=True,
        timeout=timeout,
        env=environment(),
    ).stdout


def proof_module(path):
    private(path)
    if sha(path) != PROOF_CODE_SHA:
        raise ValueError("FROZEN_CRYPTO_PROOF_MODULE_REQUIRED")
    spec = importlib.util.spec_from_file_location("reviewed_image_proof", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def base_records(path, module):
    private(path)
    if sha(path) != BASE_PROOF_RAW_SHA:
        raise ValueError("EXACT_ROOT_PROVEN_935_RAW_REQUIRED")
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    if (
        rows[-1].get("kind") != "proof_final"
        or not rows[-1]["complete"]
        or not rows[-1]["all_seven_proven"]
    ):
        raise ValueError("COMPLETE_SEVEN_IMAGE_PROOF_REQUIRED")
    result = {}
    for role, name in [("backend", BACKEND), ("python", PYTHON)]:
        matches = [
            row
            for row in rows
            if row.get("kind") == "role_proof" and row.get("role") == role
        ]
        if (
            len(matches) != 1
            or not matches[0]["proof"]["success"]
            or matches[0]["declared_CI"]["alias"] != name
        ):
            raise ValueError("EXACT_BACKEND935_AND_OFFICIAL_PYTHON_BASE_REQUIRED")
        row = matches[0]
        current = module.actual_image(name)
        original = row["actual_projection_no_Env_or_Cmd"]
        if any(
            current[key] != original[key]
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
            raise ValueError("PROVEN_BASE_CHANGED_NO_RETAG_OR_FALLBACK")
        result[role] = {
            "alias": name,
            "CI_config_id": row["proof"]["config_id"],
            "actual_descriptor_id": row["proof"]["actual_id"],
            "actual_descriptor": current["Descriptor"],
            "config_labels": current["Config"]["Labels"] or {},
        }
    return result


def inspect_tool(name, expected_labels):
    rows = json.loads(command([*DOCKER, "image", "inspect", name]))
    if len(rows) != 1:
        raise ValueError("ONE_TOOL_IMAGE_REQUIRED")
    raw = rows[0]
    config = raw["Config"]
    values = dict(line.split("=", 1) for line in config.get("Env") or [])
    if (
        raw["Os"] != "linux"
        or raw["Architecture"] != "amd64"
        or config.get("User") != "10001:10001"
        or config.get("WorkingDir") != "/diagnostic"
        or values.get("PYTHONPATH") != ""
        or any(
            key.startswith(("MYSQL_", "RABBITMQ_"))
            or key in {"DATABASE_URL", "AMQP_URL", "T44_DATABASE"}
            for key in values
        )
        or (config.get("Labels") or {}) != expected_labels
    ):
        raise ValueError("DEDICATED_RUNTIME_USER_ENV_LABELS_OR_PLATFORM_MISMATCH")
    return {
        key: raw.get(key)
        for key in ["Id", "Descriptor", "RootFS", "Os", "Architecture", "Variant"]
    } | {"Config": {"Labels": config.get("Labels")}}


def import_probe(name):
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
        "--tmpfs",
        "/tmp:rw,size=64m",
        name,
        "python",
        "-c",
        PROBE,
    ]
    result = json.loads(command(argv))
    if not all(
        result.get(key) is True
        for key in [
            "t44_spec_is_none",
            "product_paths_absent",
            "PYTHONPATH_empty",
            "app_env_absent",
        ]
    ):
        raise ValueError("TOOL_RUNTIME_ISOLATION_IMPORT_PROBE_FAILED")
    return result


def build(args):
    if os.geteuid() != 0 or not re.fullmatch(r"[a-z][a-z0-9]{5,15}", args.run_id):
        raise ValueError("ROOT_AND_FRESH_RUNTIME_RUNID_REQUIRED")
    module = proof_module(args.image_proof)
    bases = base_records(args.proof_raw, module)
    private(args.output.parent, True)
    args.output.mkdir(mode=0o700)
    write(args.output / "Dockerfile", dockerfile())
    image = "t44-calibration-runtime:" + args.run_id
    existing = subprocess.run(
        [*DOCKER, "image", "inspect", image],
        capture_output=True,
        check=False,
        timeout=15,
        env=environment(),
    )
    if existing.returncode == 0:
        raise ValueError("NEW_TOOL_RUNTIME_ALIAS_REQUIRED_NO_OVERWRITE")
    expected = dict(bases["python"]["config_labels"])
    expected.update(
        {
            "io.t44.tool-runtime.kind": "synthetic-only-python-crypto",
            "io.t44.tool-runtime.run": args.run_id,
            "io.t44.tool-runtime.dockerfile-sha256": hashlib.sha256(
                dockerfile()
            ).hexdigest(),
            "io.t44.tool-runtime.base-proof-sha256": BASE_PROOF_RAW_SHA,
        }
    )
    labels = [
        item
        for key, value in expected.items()
        for item in ["--label", key + "=" + value]
    ]
    output = command(
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
            args.output / "Dockerfile",
            "--tag",
            image,
            *labels,
            args.output,
        ],
        timeout=300,
    )
    write(args.output / "build.stdout", output)
    actual = inspect_tool(image, expected)
    # Read-only local export after build. Fixed descriptor; no tag/load/pull mutation.
    archive = args.output / "tool-runtime.tar"
    descriptor = os.open(
        archive, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600
    )
    with os.fdopen(descriptor, "wb") as stream:
        subprocess.run(
            [*DOCKER, "image", "save", image],
            stdout=stream,
            stderr=subprocess.PIPE,
            check=True,
            timeout=180,
            env=environment(),
        )
    graph = module.scan_archive(archive)
    table = graph["names"]["manifest.json"]["json"]
    matches = [
        row
        for row in table
        if image in [module.alias(tag) for tag in row.get("RepoTags") or []]
    ]
    if len(matches) != 1:
        raise ValueError("EXACT_DERIVED_RUNTIME_TAG_REQUIRED")
    config_id = graph["names"][matches[0]["Config"]]["digest"]
    labels_config = (
        graph["names"][matches[0]["Config"]]["json"]["config"].get("Labels") or {}
    )
    declared = {
        "alias": image,
        "image_id": config_id,
        "revision_label": labels_config.get("org.opencontainers.image.revision"),
        "archive_label": labels_config.get("io.t44.source-archive-sha256"),
    }
    identity_proof = module.prove_role(graph, "tool-runtime", declared, {}, actual)
    probe = import_probe(image)
    binding = {
        "kind": "offline-tool-only-python-crypto-runtime",
        "run_id": args.run_id,
        "image_alias": image,
        "actual_image_id": actual["Id"],
        "runtime_config_id": config_id,
        "actual_descriptor": actual["Descriptor"],
        "image_identity_proof": identity_proof,
        "dockerfile_sha256": sha(args.output / "Dockerfile"),
        "build_metadata_sha256": sha(args.output / "build-metadata.json"),
        "attestation_policy": "single-platform local tool image; registry attestation disabled; separate build metadata and full blob/config/layer proof retained",
        "tool_runtime_archive_sha256": sha(archive),
        "expected_labels": expected,
        "bases": bases,
        "base_proof_raw_sha256": BASE_PROOF_RAW_SHA,
        "verification": probe,
        "builder_sha256": sha(Path(__file__)),
        "SUT_paths_copied": False,
        "business_env_read_or_passed": False,
        "pip_install_requested": False,
        "external_download_step_in_Dockerfile": False,
        "build_network_mode": "none; verified local FROM aliases; no fallback",
        "main_calibration_container_started": False,
    }
    save(args.output / "runtime-binding.json", binding)
    return {
        "success": True,
        "binding_path": str(args.output / "runtime-binding.json"),
        "binding_sha256": sha(args.output / "runtime-binding.json"),
        "image_alias": image,
        "actual_image_id": actual["Id"],
        "config_id": config_id,
        "runtime_versions_and_isolation": probe,
        "main_container_started": False,
        "business_env_read_or_passed": False,
    }


def verify_binding(path, expected, image_proof):
    private(path)
    if not re.fullmatch(r"[0-9a-f]{64}", expected) or sha(path) != expected:
        raise ValueError("ROOT_VERIFIED_TOOL_RUNTIME_BINDING_SHA_REQUIRED")
    value = json.loads(path.read_text())
    if (
        value["kind"] != "offline-tool-only-python-crypto-runtime"
        or not re.fullmatch(r"[a-z][a-z0-9]{5,15}", value["run_id"])
        or value["image_alias"] != "t44-calibration-runtime:" + value["run_id"]
        or value["base_proof_raw_sha256"] != BASE_PROOF_RAW_SHA
        or value["dockerfile_sha256"] != hashlib.sha256(dockerfile()).hexdigest()
        or sha(path.parent / "Dockerfile") != value["dockerfile_sha256"]
        or value["bases"]["backend"]["alias"] != BACKEND
        or value["bases"]["python"]["alias"] != PYTHON
    ):
        raise ValueError("EXACT_DEDICATED_RUNTIME_FACTORY_BINDING_REQUIRED")
    actual = inspect_tool(value["image_alias"], value["expected_labels"])
    if (
        actual["Id"] != value["actual_image_id"]
        or actual["Descriptor"] != value["actual_descriptor"]
    ):
        raise ValueError("DERIVED_RUNTIME_IDENTITY_CHANGED")
    if sha(path.parent / "tool-runtime.tar") != value["tool_runtime_archive_sha256"]:
        raise ValueError("DERIVED_RUNTIME_ARCHIVE_CHANGED")
    module = proof_module(image_proof)
    graph = module.scan_archive(path.parent / "tool-runtime.tar")
    labels = value["expected_labels"]
    declared = {
        "alias": value["image_alias"],
        "image_id": value["runtime_config_id"],
        "revision_label": labels.get("org.opencontainers.image.revision"),
        "archive_label": labels.get("io.t44.source-archive-sha256"),
    }
    module.prove_role(graph, "tool-runtime", declared, {}, actual)
    return value, import_probe(value["image_alias"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("build", "verify"))
    parser.add_argument("--image-proof", type=Path, required=True)
    parser.add_argument("--proof-raw", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--run-id")
    parser.add_argument("--binding", type=Path)
    parser.add_argument("--binding-sha256")
    args = parser.parse_args()
    os.umask(0o077)
    try:
        result = (
            build(args)
            if args.action == "build"
            else {
                "success": True,
                "verification": verify_binding(
                    args.binding, args.binding_sha256, args.image_proof
                )[1],
                "main_container_started": False,
            }
        )
        print(json.dumps(result))
    except (
        OSError,
        ValueError,
        KeyError,
        TypeError,
        subprocess.SubprocessError,
    ) as error:
        failure = None
        if args.output and args.output.is_dir():
            failure = args.output / ("build-failure-" + uuid4().hex + ".json")
            row = {
                "error_class": type(error).__name__,
                "reason": str(error),
                "partial_state_preserved": True,
            }
            if isinstance(error, subprocess.CalledProcessError):
                row.update(
                    stdout=error.stdout.decode(errors="replace")
                    if error.stdout
                    else "",
                    stderr=error.stderr.decode(errors="replace")
                    if error.stderr
                    else "",
                )
            save(failure, row)
        print(
            json.dumps(
                {
                    "success": False,
                    "error": "OFFLINE_TOOL_RUNTIME_REFUSED",
                    "private_failure_path": str(failure) if failure else None,
                    "main_container_started": False,
                }
            )
        )
        raise SystemExit(1) from None
