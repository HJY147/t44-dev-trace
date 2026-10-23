"""Archive an explicit public Git snapshot for private review, never a working tree."""

import argparse
import hashlib
import io
import json
import os
import re
import stat
import subprocess
import tarfile
import zipfile
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[2]
ROOTS = ("backend", "frontend", "deployment", "scripts", "specs", "docs", "agents",
         "records", "reports", "tmp/backend", "tmp/frontend", "tmp/deployment", "tmp/ci",
         "tmp/reviewer", ".github", "README.md", "LICENSE", "AGENTS.md", "compose.yaml")
FORBIDDEN_PARTS = {".git", ".agent-worktrees", ".submission-private", "node_modules", ".venv",
                   "__pycache__", ".pytest_cache", "coverage", "dist", "independent"}


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT)


def allowed(name):
    path = PurePosixPath(name)
    return (not path.is_absolute() and ".." not in path.parts
            and not FORBIDDEN_PARTS.intersection(path.parts)
            and not path.name.startswith(".env") or name == "deployment/.env.example")


def selected_files(commit):
    entries = {}
    for item in git("ls-tree", "-rz", commit, "--", *ROOTS).split(b"\0"):
        if not item:
            continue
        metadata, raw_name = item.split(b"\t", 1)
        mode, kind, object_id = metadata.decode().split()
        name = raw_name.decode("utf-8")
        if not allowed(name):
            continue
        if mode not in {"100644", "100755"} or kind != "blob":
            raise ValueError("archive accepts regular tracked files only")
        if PurePosixPath(name).suffix.lower() in {".key", ".pem", ".p12", ".pfx"}:
            raise ValueError("key-like tracked file requires explicit separate review")
        entries[name] = {"git_blob": object_id, "mode": mode}
    if not entries or "README.md" not in entries or "compose.yaml" not in entries:
        raise ValueError("required public source roots are absent")
    return entries


def output_directory():
    parent = ROOT / ".submission-private"
    if parent.is_symlink() or not parent.is_dir():
        raise ValueError("existing private project directory is required")
    target = parent / "review-packages"
    target.mkdir(mode=0o700, exist_ok=True)
    for folder in (parent, target):
        value = folder.lstat()
        if (not stat.S_ISDIR(value.st_mode) or value.st_uid != os.getuid()
                or stat.S_IMODE(value.st_mode) & 0o077):
            raise ValueError("private output directory ownership or mode differs")
    return target


def add_member(archive, name, data, mode=0o644):
    info = zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
    info.create_system = 3
    info.external_attr = (stat.S_IFREG | mode) << 16
    info.compress_type = zipfile.ZIP_DEFLATED
    archive.writestr(info, data)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--commit", default="HEAD")
    args = parser.parse_args()
    if args.commit != "HEAD" and not re.fullmatch(r"[0-9a-f]{40}", args.commit):
        raise ValueError("use HEAD or an exact forty-character commit")
    commit = git("rev-parse", "--verify", args.commit + "^{commit}").decode().strip()
    entries = selected_files(commit)
    folder = output_directory()
    destination = folder / ("T44-source-review-" + commit[:12] + ".zip")
    sidecar = destination.with_suffix(".manifest.json")
    if destination.exists() or sidecar.exists() or destination.is_symlink() or sidecar.is_symlink():
        raise FileExistsError("review outputs must not already exist")
    raw = git("archive", "--format=tar", commit, "--", *sorted(entries))
    manifest = {"schema_version": 1, "purpose": "source review only; not final coursework acceptance",
                "source_commit": commit, "created_at_utc": datetime.now(UTC).isoformat(),
                "selection_roots": ROOTS, "working_tree_read": False,
                "independent_private_contents_read": False,
                "private_Word_or_personal_data_included": False,
                "open_gates": ["independent full acceptance", "formal P95", "source budget",
                               "student-authored study and actual human-specific evidence"],
                "files": entries}
    own_outputs = []
    try:
        descriptor = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        own_outputs.append(destination)
        with os.fdopen(descriptor, "wb") as stream, zipfile.ZipFile(stream, "w") as archive:
            seen = set()
            with tarfile.open(fileobj=io.BytesIO(raw)) as snapshot:
                for member in snapshot:
                    if member.isdir():
                        continue
                    if member.name not in entries or not member.isfile() or member.name in seen:
                        raise ValueError("Git archive member differs from selected regular source")
                    if member.size > 100 * 1024 * 1024:
                        raise ValueError("unexpected source artifact size")
                    data = snapshot.extractfile(member).read()
                    entry = entries[member.name]
                    entry.update(size=len(data), sha256=hashlib.sha256(data).hexdigest())
                    add_member(archive, member.name, data, 0o755 if entry["mode"] == "100755" else 0o644)
                    seen.add(member.name)
            if seen != set(entries):
                raise ValueError("Git archive did not supply every selected file")
            add_member(archive, "REVIEW-PACKAGE-MANIFEST.json",
                       (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode())
        with zipfile.ZipFile(destination) as archive:
            expected = {*entries, "REVIEW-PACKAGE-MANIFEST.json"}
            if len(archive.namelist()) != len(expected) or set(archive.namelist()) != expected:
                raise ValueError("ZIP member set or duplication mismatch")
            for name, entry in entries.items():
                data = archive.read(name)
                if len(data) != entry["size"] or hashlib.sha256(data).hexdigest() != entry["sha256"]:
                    raise ValueError("ZIP source byte integrity mismatch")
            if json.loads(archive.read("REVIEW-PACKAGE-MANIFEST.json")) != json.loads(json.dumps(manifest)):
                raise ValueError("ZIP manifest mismatch")
        manifest["archive_sha256"] = hashlib.sha256(destination.read_bytes()).hexdigest()
        manifest["archive_size"] = destination.stat().st_size
        manifest["verified_member_count"] = len(entries)
        descriptor = os.open(sidecar, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        own_outputs.append(sidecar)
        with os.fdopen(descriptor, "w") as stream:
            json.dump(manifest, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
        print(json.dumps({"source_commit": commit, "source_files": len(entries),
                          "archive": str(destination), "sha256": manifest["archive_sha256"],
                          "verified": True}, ensure_ascii=False))
    except BaseException:
        for path in reversed(own_outputs):
            path.unlink(missing_ok=True)
        raise
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
