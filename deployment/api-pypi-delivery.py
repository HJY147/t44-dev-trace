"""Generate an external exact-C API delivery Dockerfile; never build or use the network."""

import argparse
import hashlib
import json
import os
import stat
import subprocess
from pathlib import Path

PRODUCT_C = "0dfb55c2191200d947c5423fd9ee74bb0812cc5a"
POLICY_SHA256 = "f9101355c4bf7b9d51e9feda2d8e48361e0d3a9ff81cb5f71ccd49bbb775e1f8"
PINNED = {
    "deployment/api.Dockerfile": "3862fc17da18717531bdadd79320571ac1465f8f48ee84420793c940c6be8d90",
    "deployment/api.Dockerfile.dockerignore": "302ac76f30a451a3977497fa3fda31f3784a04e9fecf136064b9189bfbc01c9f",
    "backend/requirements.lock": "3b15a7bdf93024750835ac20584a140eb93f1dc7476be61bb0af145e8ff0cc30",
}
ORIGINAL = b"RUN python -m pip install --no-cache-dir --require-hashes -r /tmp/requirements.lock"
ADDITION = b" --index-url https://mirrors.aliyun.com/pypi/simple/"
DOCKERFILE_NAME = "api-pypi-C.Dockerfile"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def transform(original: bytes) -> bytes:
    if sha256(original) != PINNED["deployment/api.Dockerfile"] or original.count(ORIGINAL) != 1:
        raise ValueError("original_Dockerfile_differs")
    changed = original.replace(ORIGINAL, ORIGINAL + ADDITION, 1)
    if changed.replace(ORIGINAL + ADDITION, ORIGINAL, 1) != original:
        raise ValueError("unexpected_Dockerfile_delta")
    return changed


def source_inputs(root: Path) -> dict[str, bytes]:
    if not root.is_absolute() or root.resolve() != root:
        raise ValueError("absolute_canonical_source_required")
    head = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"],
                          capture_output=True, check=True, timeout=5).stdout.decode().strip()
    if head != PRODUCT_C:
        raise ValueError("wrong_product_C")
    subprocess.run(["git", "-C", str(root), "diff", "--quiet", "HEAD", "--"],
                   capture_output=True, check=True, timeout=5)
    inputs = {}
    for name, expected in PINNED.items():
        path = root / name
        if not stat.S_ISREG(path.lstat().st_mode):
            raise ValueError("source_input_not_regular")
        data = path.read_bytes()
        if sha256(data) != expected:
            raise ValueError("source_input_hash_differs")
        inputs[name] = data
    return inputs


def exclusive_write(path: Path, data: bytes) -> None:
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, "wb") as stream:
        os.fchmod(stream.fileno(), 0o600)
        stream.write(data)


def generate(root: Path, runtime: Path) -> dict:
    if not runtime.is_absolute() or ".." in runtime.parts or runtime.parent.resolve() != runtime.parent:
        raise ValueError("absolute_canonical_runtime_required")
    if runtime.is_relative_to(root):
        raise ValueError("runtime_must_be_outside_C_source")
    parent = runtime.parent.lstat()
    if (not stat.S_ISDIR(parent.st_mode) or stat.S_IMODE(parent.st_mode) != 0o700
            or parent.st_uid != os.geteuid()):
        raise ValueError("private_owned_parent_required")
    inputs = source_inputs(root)
    original = inputs["deployment/api.Dockerfile"]
    changed = transform(original)
    ignore = inputs["deployment/api.Dockerfile.dockerignore"]
    runtime.mkdir(mode=0o700)  # No reuse, overwrite or cleanup of previous attempts.
    runtime.chmod(0o700)
    exclusive_write(runtime / DOCKERFILE_NAME, changed)
    exclusive_write(runtime / (DOCKERFILE_NAME + ".dockerignore"), ignore)
    manifest = {
        "product_source": PRODUCT_C,
        "source_root": str(root),
        "Dockerfile": DOCKERFILE_NAME,
        "Dockerfile_specific_ignore": DOCKERFILE_NAME + ".dockerignore",
        "original_Dockerfile_sha256": sha256(original),
        "delivery_Dockerfile_sha256": sha256(changed),
        "dockerignore_sha256": sha256(ignore),
        "requirements_lock_sha256": sha256(inputs["backend/requirements.lock"]),
        "source_policy_v2_sha256": POLICY_SHA256,
        "changed_channel_only": True,
        "not_original_Dockerfile_bytes": True,
        "only_delta": ADDITION.decode().strip(),
        "require_hashes_lock_and_base_digest_unchanged": True,
        "source_C_modified": False,
        "build_network_or_services_executed": False,
    }
    exclusive_write(runtime / "manifest.json", (json.dumps(manifest, indent=2) + "\n").encode())
    return manifest


def main() -> int:
    os.umask(0o077)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--runtime", type=Path, required=True)
    args = parser.parse_args()
    try:
        if os.geteuid() != 0:
            raise ValueError("root_required")
        manifest = generate(args.source_root, args.runtime)
    except (OSError, ValueError, subprocess.SubprocessError):
        print(json.dumps({"error": "API_PYPI_DELIVERY_GENERATION_FAILED", "generated": False,
                          "partial_runtime_may_exist": True, "build_executed": False}))
        return 1
    print(json.dumps(manifest))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
