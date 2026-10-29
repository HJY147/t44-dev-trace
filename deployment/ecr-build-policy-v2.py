"""Generate exact-C BuildKit delivery policy only; no Docker or network execution."""

import argparse
import hashlib
import json
import os
import stat
import subprocess
from pathlib import Path

PRODUCT_C = "0dfb55c2191200d947c5423fd9ee74bb0812cc5a"
BASE_IMAGES = (
    "python:3.12-slim-bookworm@sha256:6a0e06f5ba0b373d051aabd3fffb9b873f27f9a2a3a14bcbe37dee6f0e3bbc70",
    "node:24-bookworm-slim@sha256:55fb5f5a527ea2c5c4a95f963e48ef90aa38c7b346054fdc8ee9957a2b55d205",
    "nginx:stable-alpine@sha256:47928bf67eb62a1863cb08d9ecb52d3e704304ba614eaee17884204677702951",
)


def policy_for(dockerfiles: list[str]) -> dict:
    actual = [line.split()[1] for text in dockerfiles for line in text.splitlines()
              if line.startswith("FROM ")]
    if actual != list(BASE_IMAGES):
        raise ValueError("from_set_differs")
    rules = [{"action": "CONVERT", "selector": {
        "identifier": "docker-image://docker.io/library/" + image,
        "match_type": "WILDCARD"}, "updates": {
        "identifier": "docker-image://public.ecr.aws/docker/library/" + image}}
        for image in BASE_IMAGES]
    rules.append({"action": "DENY", "selector": {
        "identifier": "docker-image://docker.io/*", "match_type": "WILDCARD"}})
    return {"version": 1, "rules": rules}


def checked_source(root: Path) -> list[str]:
    head = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"],
                          check=True, capture_output=True, text=True, timeout=5)
    if head.stdout.strip() != PRODUCT_C:
        raise ValueError("source_head_differs")
    subprocess.run(["git", "-C", str(root), "diff", "--quiet", "HEAD", "--"],
                   check=True, capture_output=True, timeout=5)
    return [(root / "deployment" / name).read_text()
            for name in ("api.Dockerfile", "web.Dockerfile")]


def write_policy(output: Path, data: bytes) -> None:
    if not output.is_absolute() or ".." in output.parts:
        raise ValueError("absolute_output_required")
    parent = output.parent.lstat()
    if (not stat.S_ISDIR(parent.st_mode) or parent.st_uid != os.geteuid()
            or stat.S_IMODE(parent.st_mode) != 0o700):
        raise ValueError("private_owned_parent_required")
    descriptor = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        policy = policy_for(checked_source(args.source_root))
        data = (json.dumps(policy, indent=2) + "\n").encode()
        write_policy(args.output, data)
        print(json.dumps({"product_source": PRODUCT_C, "policy_file": str(args.output),
                          "policy_sha256": hashlib.sha256(data).hexdigest(), "rule_count": 4}))
        return 0
    except (OSError, ValueError, subprocess.SubprocessError):
        print(json.dumps({"error": "policy_generation_failed"}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
