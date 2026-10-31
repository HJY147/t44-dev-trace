"""Package committed public P15 tools only; no network, credentials or approval."""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tarfile

ROOT = Path(__file__).resolve().parents[3]
SOURCE = "bcec3326b40814fdb1922bbfea7c29473b47ba47"
PREFIXES = {
    "agents/backend/bcec-material/release/": "backend/",
    "agents/deployment/p15-ready/": "deployment/",
    "records/qa/p15-install-v53.PUBLIC/": "qa-install/",
    "records/qa/p15-controls-v53.PUBLIC/": "qa-controls/",
    "agents/coordinator/manualp15-preparation/ssh/": "ssh/",
    "agents/coordinator/manualp15-preparation/coordinator/": "coordinator/",
}
CMS_SHA = "466fa0b7ce4d00d1cf5ab1209bdaff0ee266279210971cc76145d677af51ab26"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    out = args.output
    archive = out.with_suffix(".tar.gz")
    if not out.is_absolute() or out.exists() or archive.exists():
        raise ValueError("NEW_ABSOLUTE_OUTPUT_REQUIRED")
    head = git("rev-parse", "HEAD").decode().strip()
    if git("diff", "--name-only", SOURCE, head, "--", "backend/t44",
           "backend/requirements.lock", "frontend/src", "specs", "compose.yaml",
           "tmp/backend", ".github/workflows/product.yml"):
        raise ValueError("TESTED_PRODUCT_OR_ASSERTIONS_DRIFT")
    selected = {}
    for name in git("ls-tree", "-r", "--name-only", head).decode().splitlines():
        for prefix, target in PREFIXES.items():
            if name.startswith(prefix) and not name.endswith(".log"):
                selected[target + name[len(prefix):]] = git("show", head + ":" + name)
    for prefix in PREFIXES.values():
        if not any(name.startswith(prefix) for name in selected):
            raise ValueError("MISSING_OWNER_DELIVERY: " + prefix)
    selected["READY_AFTER_BOOT.md"] = git("show", head + ":agents/coordinator/manualp15-preparation/READY_AFTER_BOOT.md")
    common = Path(git("rev-parse", "--git-common-dir").decode().strip())
    if not common.is_absolute():
        common = ROOT / common
    cms = common.resolve().parent / ".agent-worktrees/.runtime/manual13-ready-20261030/deployment/cms_five_transport.py"
    raw = cms.read_bytes()
    if sha(raw) != CMS_SHA:
        raise ValueError("ORIGINAL_CMS_TRANSPORT_BYTES_REQUIRED")
    selected["transport/cms_five_transport.py"] = raw
    for folder, filename in (("backend/", "RELEASE.PUBLIC.json"),
                             ("qa-install/", "DELIVERY_MANIFEST.PUBLIC.json"),
                             ("qa-controls/", "DELIVERY_MANIFEST.PUBLIC.json")):
        manifest = json.loads(selected[folder + filename])
        for name, expected in manifest["files"].items():
            expected_sha = expected if isinstance(expected, str) else expected["sha256"]
            if sha(selected[folder + name]) != expected_sha:
                raise ValueError("OWNER_MANIFEST_MISMATCH: " + folder + name)
    backend = json.loads(selected["backend/RELEASE.PUBLIC.json"])
    if backend["source_sha"] != SOURCE or backend["grant_allow"] is not False:
        raise ValueError("CURRENT_SOURCE_FALSE_GRANT_REQUIRED")
    out.mkdir(mode=0o700)
    rows = {}
    for name, raw in sorted(selected.items()):
        path = Path(name)
        if path.is_absolute() or ".." in path.parts:
            raise ValueError("UNSAFE_ARCHIVE_MEMBER")
        path = out / path
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as stream:
            stream.write(raw)
        rows[name] = {"bytes": len(raw), "sha256": sha(raw)}
    manifest = {
        "schema": "t44-p15-offline-kit-v1", "source": SOURCE,
        "coordinator_head": head, "run": "r30manualp15",
        "material": "r30materialresume09", "maintenance": "r30restoretransition09",
        "workspace": "/root/t44-final-20261031/QA753_NEXT_V53",
        "status": "OFFLINE_PACKAGE_VERIFIED_LIVE_CHECKS_PENDING",
        "actual_grant_created": False, "cloud_actions": False,
        "ssh_authorization": "USER_AUTHORIZED_PERSISTENT_RESTRICTED_KEY_NO_EXPIRY",
        "automatic_vm_shutdown": False,
        "measurement": {"clients": 400, "warmup_seconds": 60,
                        "steady_seconds": 600, "p95_max_ms": 270,
                        "minimum_per_minute": 1000, "errors": 0},
        "files": rows,
    }
    encoded = (json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()
    (out / "MANIFEST.PUBLIC.json").write_bytes(encoded)
    with tarfile.open(archive, "w:gz") as stream:
        for path in sorted(out.rglob("*")):
            if path.is_file():
                stream.add(path, arcname=path.relative_to(out).as_posix(), recursive=False)
    with tarfile.open(archive) as stream:
        for member in stream.getmembers():
            if not member.isfile():
                raise ValueError("REGULAR_FILES_ONLY")
            actual = stream.extractfile(member).read()
            expected = encoded if member.name == "MANIFEST.PUBLIC.json" else selected[member.name]
            if actual != expected:
                raise ValueError("ARCHIVE_BYTE_MISMATCH")
    print(json.dumps({"archive": str(archive), "bytes": archive.stat().st_size,
                      "sha256": sha(archive.read_bytes()), "files": len(rows),
                      "manifest_sha256": sha(encoded), "actual_grant_created": False}))


if __name__ == "__main__":
    main()
