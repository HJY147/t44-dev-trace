"""Package explicitly selected, hash-verified local review artifacts; never publish."""

import argparse
import hashlib
import io
import json
import os
import re
import stat
import subprocess
import zipfile
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath

DOCUMENTS = {"requirements", "design", "test-results", "ai-spec-guide"}
PUBLIC_MATERIALS = {
    "reports/final/ai-development-report.md",
    "reports/final/student-study-template.md",
    "reports/final/submission-map.md",
    "docs/prompting/M6-process-checkpoint.md",
    "docs/prompting/M7-night-process-evidence.md",
    "records/research/ai-software-engineering-primary-sources.md",
    "records/reflections/R001-original.md",
    "records/reflections/R002-provenance.json",
    "records/prompts/U001-original.md",
    "records/prompts/U002-original.md",
    "reports/independent-v3/stage06-formal-blackbox.md",
}
LIMIT = 120 * 1024 * 1024


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def regular_inside(root, relative):
    path = PurePosixPath(relative)
    if path.is_absolute() or ".." in path.parts or not path.parts:
        raise ValueError("Only project-relative regular artifact paths are accepted")
    current = root
    for part in path.parts:
        current = current / part
        if current.is_symlink():
            raise ValueError("Symlink artifact paths are not permitted")
    if not current.resolve().is_relative_to(root) or not current.is_file():
        raise ValueError("Artifact is missing or outside the selected project")
    if current.stat().st_size > LIMIT:
        raise ValueError("Artifact exceeds the review package size limit")
    return current


def exclusive_write(path, data):
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "wb") as handle:
        handle.write(data)


def verify_entry(root, entry):
    path = regular_inside(root, entry["path"])
    relative = PurePosixPath(entry["path"])
    kind = entry["kind"]
    if kind == "source":
        allowed = relative.parent == PurePosixPath(".submission-private/review-packages")
        allowed = allowed and relative.suffix == ".zip"
    elif kind == "technical":
        allowed = relative.parts[:2] == (".submission-private", "review-documents")
        allowed = allowed and len(relative.parts) >= 4 and relative.parts[2] in {"M6", "M7"}
        allowed = allowed and entry["document_id"] in DOCUMENTS
        expected_stage = "M7" if entry["document_id"] == "test-results" else "M6"
        allowed = allowed and relative.parts[2] == expected_stage
        allowed = allowed and relative.name == entry["document_id"] + "-review" + relative.suffix
        allowed = allowed and relative.suffix in {".docx", ".pdf"}
        allowed = allowed and bool(entry.get("qa_reference"))
    elif kind == "material":
        allowed = str(relative) in PUBLIC_MATERIALS
    else:
        allowed = False
    if not allowed:
        raise ValueError("Artifact is outside the positive review allowlist")
    member = PurePosixPath(entry["member"])
    if member.is_absolute() or ".." in member.parts or str(member) in {"", "manifest.json", "00_审阅说明.md"}:
        raise ValueError("Unsafe or reserved ZIP member name")
    data = path.read_bytes()
    if sha256(data) != entry["sha256"]:
        raise ValueError("Artifact hash differs from the reviewed input manifest")
    if not entry.get("authorship") or not entry.get("provenance"):
        raise ValueError("Every artifact must declare authorship and provenance")
    record = {**entry, "bytes": len(data)}
    return record, data


def verify_source_archive(data, source):
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        manifest = json.loads(archive.read("REVIEW-PACKAGE-MANIFEST.json"))
        files = manifest["files"]
        expected = {*files, "REVIEW-PACKAGE-MANIFEST.json"}
        if manifest["source_commit"] != source or len(archive.namelist()) != len(expected) or set(archive.namelist()) != expected:
            raise ValueError("Inner source archive differs from the declared source")
        for name, record in files.items():
            path = PurePosixPath(name)
            if path.is_absolute() or ".." in path.parts or name.startswith(("tmp/independent/", ".submission-private/", ".agent-worktrees/")):
                raise ValueError("Inner source archive contains a prohibited path")
            raw = archive.read(name)
            blob = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw, usedforsecurity=False).hexdigest()
            if len(raw) != record["size"] or sha256(raw) != record["sha256"] or blob != record["git_blob"]:
                raise ValueError("Inner source archive member hash mismatch")
        return len(files)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--input-manifest", required=True)
    parser.add_argument("--public-receipt", required=True)
    args = parser.parse_args()
    os.umask(0o077)
    root = args.project_root.resolve(strict=True)
    input_path = regular_inside(root, args.input_manifest)
    if not input_path.is_relative_to(root / ".submission-private"):
        raise ValueError("Selection manifest must stay in the private submission directory")
    selected = json.loads(input_path.read_text())
    if selected["status"] != "incomplete-review-only" or not selected.get("missing"):
        raise ValueError("This builder cannot label an incomplete review as final submission")
    source = selected["source_commit"]
    if not re.fullmatch("[0-9a-f]{40}", source):
        raise ValueError("Source must be an exact full commit SHA")
    entries = [verify_entry(root, entry) for entry in selected["entries"]]
    if sum(record["kind"] == "source" for record, _ in entries) != 1:
        raise ValueError("Exactly one verified source review archive is required")
    inner_count = verify_source_archive(next(data for record, data in entries if record["kind"] == "source"), source)
    technical = [(r["document_id"], Path(r["path"]).suffix) for r, _ in entries if r["kind"] == "technical"]
    if set(technical) != {(name, ext) for name in DOCUMENTS for ext in (".docx", ".pdf")} or len(technical) != 8:
        raise ValueError("Four distinct technical DOCX/PDF pairs are required")
    names = [r["member"] for r, _ in entries]
    if len(names) != len(set(names)) or sum(len(b) for _, b in entries) > LIMIT:
        raise ValueError("Duplicate entries or oversized review package")
    committed_source = subprocess.run(
        ["git", "-C", str(root), "rev-parse", source + "^{commit}"],
        check=True, capture_output=True, text=True,
    ).stdout.strip()
    if committed_source != source:
        raise ValueError("Source commit cannot be resolved exactly")
    manifest = {
        "created_at_utc": datetime.now(UTC).isoformat(),
        "status": selected["status"], "source_commit": source,
        "entries": [r for r, _ in entries], "missing": selected["missing"],
        "selection_manifest_sha256": sha256(input_path.read_bytes()),
        "inner_source_members_reverified": inner_count,
        "authorship_policy": "Technical/AI support material is not student-authored research or human modification evidence.",
        "publication": "Local private review only; no upload, release, merge or acceptance approval.",
    }
    explanation = (
        "# T44 本地审阅包\n\n这是一份未完成验收的审阅材料，不是最终提交。\n\n"
        "四份技术稿的截止版本各见manifest；三稿复用M6，测试稿另选已完成QA的M7。"
        "研究提纲和AI过程材料不等于学生本人最终研究正文。R002原话仍留原私密位置，这里只附公开出处。\n\n"
        "尚未完成或未证实：\n\n" + "".join("- " + item + "\n" for item in selected["missing"])
        + "\n先阅读提交物对照，再由本人补齐真实材料与判断。源码位于内层审阅ZIP，含其独立完整性清单。\n"
    ).encode()
    encoded = (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode()
    output = root / ".submission-private/coursework-review-bundles"
    if output.is_symlink():
        raise ValueError("Review output directory cannot be a symlink")
    output.mkdir(mode=0o700, parents=True, exist_ok=True)
    output.chmod(0o700)
    target = output / ("T44-coursework-review-M7-" + source[:12] + ".zip")
    receipt_path = root / args.public_receipt
    if receipt_path.parent != root / "records/validation" or receipt_path.suffix != ".json" or receipt_path.is_symlink():
        raise ValueError("Public receipt must be a new JSON in records/validation")
    if any(path.exists() or path.is_symlink() for path in (target, target.with_suffix(".manifest.json"), receipt_path)):
        raise FileExistsError("Review outputs must be new; old packages remain immutable")
    contents = {r["member"]: data for r, data in entries}
    contents.update({"manifest.json": encoded, "00_审阅说明.md": explanation})
    descriptor = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w+b") as handle, zipfile.ZipFile(handle, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, data in contents.items():
            info = zipfile.ZipInfo(name, datetime.now().timetuple()[:6])
            info.create_system = 3
            info.external_attr = (stat.S_IFREG | 0o600) << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, data)
    with zipfile.ZipFile(target) as archive:
        if len(archive.namelist()) != len(contents) or set(archive.namelist()) != set(contents) or archive.testzip():
            raise ValueError("Review ZIP member or CRC verification failed")
        for name, data in contents.items():
            if sha256(archive.read(name)) != sha256(data):
                raise ValueError("Review ZIP member hash verification failed")
    exclusive_write(target.with_suffix(".manifest.json"), encoded)
    receipt = {
        "created_at_utc": datetime.now(UTC).isoformat(), "actor": "coordinator AI",
        "status": selected["status"], "source_commit": source,
        "private_archive": str(target.relative_to(root)), "archive_sha256": sha256(target.read_bytes()),
        "bytes": target.stat().st_size, "member_count": len(contents),
        "all_member_hashes_and_CRC_verified": True, "output_mode": oct(stat.S_IMODE(target.stat().st_mode)),
        "inner_source_members_reverified": inner_count,
        "technical_versions": [{k: r[k] for k in ("document_id", "sha256", "provenance", "qa_reference")} for r, _ in entries if r["kind"] == "technical"],
        "missing": selected["missing"], "private_personal_fields_or_R002_raw_published": False,
        "not_final_submission_or_acceptance": True,
    }
    exclusive_write(receipt_path, (json.dumps(receipt, ensure_ascii=False, indent=2) + "\n").encode())
    print(json.dumps({"archive": str(target.relative_to(root)), "sha256": receipt["archive_sha256"], "members": len(contents), "status": selected["status"]}))


if __name__ == "__main__":
    main()
