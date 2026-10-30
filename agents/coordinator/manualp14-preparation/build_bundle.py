"""Assemble reviewed offline tools; no network, SUT, credentials or approvals."""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tarfile

ROOT = Path(__file__).resolve().parents[3]
SOURCE = "13acb43a804e717e7485091895378511fe3d9b76"
CMS_SHA = "466fa0b7ce4d00d1cf5ab1209bdaff0ee266279210971cc76145d677af51ab26"
PREFIXES = {
    "agents/backend/new-source-material/": "backend/",
    "agents/deployment/new-source-sequence/": "sequence/",
    "agents/deployment/import-helper-13ac/PUBLIC/ops/": "image-import/",
    "records/qa/next-install-v52.PUBLIC/": "qa-install/",
    "records/qa/p14-public-controls-v52/": "qa-controls/",
    "reports/independent-tests/next-offline-20261031/": "qa-protocol/",
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    out = args.output
    if not out.is_absolute() or out.exists() or out.with_suffix(".tar.gz").exists():
        raise ValueError("NEW_ABSOLUTE_OUTPUT_REQUIRED")
    head = git("rev-parse", "HEAD").decode().strip()
    if git("diff", "--name-only", SOURCE, head, "--", "backend/t44", "backend/requirements.lock",
           "tmp/backend", "frontend/src", "specs", "compose.yaml"):
        raise ValueError("TESTED_PRODUCT_SCOPE_DRIFT")
    selected = {}
    for name in git("ls-tree", "-r", "--name-only", head).decode().splitlines():
        for prefix, target in PREFIXES.items():
            if name.startswith(prefix) and not name.endswith(".log"):
                selected[target + name[len(prefix):]] = git("show", head + ":" + name)
    for source, target in {
        "deployment/cloud-reuse/locked-task-plan.py": "planner/locked-task-plan.py",
        "agents/coordinator/manualp14-preparation/READY_AFTER_BOOT.md": "READY_AFTER_BOOT.md",
    }.items():
        selected[target] = git("show", head + ":" + source)
    common = Path(git("rev-parse", "--git-common-dir").decode().strip())
    if not common.is_absolute():
        common = ROOT / common
    cms = (common.resolve().parent / ".agent-worktrees" / ".runtime"
           / "manual13-ready-20261030" / "deployment"
           / "cms_five_transport.py")
    raw = cms.read_bytes()
    if sha(raw) != CMS_SHA:
        raise ValueError("ORIGINAL_CMS_TRANSPORT_BYTES_REQUIRED")
    selected["transport/cms_five_transport.py"] = raw
    out.mkdir(mode=0o700)
    rows = {}
    for name, raw in sorted(selected.items()):
        relative = Path(name)
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("UNSAFE_ARCHIVE_MEMBER")
        path = out / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as stream:
            stream.write(raw)
        rows[name] = {"bytes": len(raw), "sha256": sha(raw)}
    manifest = {
        "schema": "t44-p14-offline-kit-v1", "source": SOURCE, "coordinator_head": head,
        "run": "r30manualp14", "material": "r30materialresume08",
        "maintenance": "r30restoretransition08", "actual_grant_created": False,
        "cloud_actions": False, "status": "OFFLINE_ONLY_CURRENT_LIVE_GATES_PENDING",
        "measurement": {"clients": 400, "warmup_seconds": 60, "steady_seconds": 600,
                        "p95_max_ms": 270, "minimum_per_minute": 1000, "errors": 0},
        "files": rows,
    }
    encoded = (json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()
    (out / "MANIFEST.PUBLIC.json").write_bytes(encoded)
    for name, row in rows.items():
        raw = (out / name).read_bytes()
        assert len(raw) == row["bytes"] and sha(raw) == row["sha256"]
    archive = out.with_suffix(".tar.gz")
    with tarfile.open(archive, "w:gz") as stream:
        for path in sorted(out.rglob("*")):
            if path.is_file():
                stream.add(path, arcname=path.relative_to(out).as_posix(), recursive=False)
    with tarfile.open(archive) as stream:
        members = stream.getmembers()
        assert all(member.isfile() for member in members)
        for member in members:
            raw = stream.extractfile(member).read()
            expected = encoded if member.name == "MANIFEST.PUBLIC.json" else selected[member.name]
            assert raw == expected
    print(json.dumps({"archive": str(archive), "files": len(rows),
                      "bytes": archive.stat().st_size, "sha256": sha(archive.read_bytes()),
                      "manifest_sha256": sha(encoded), "actual_grant_created": False}))


if __name__ == "__main__":
    main()
