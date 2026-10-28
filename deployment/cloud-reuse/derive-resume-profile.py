"""Derive new, explicitly pinned source/time tools without editing frozen prior helpers."""

import argparse
import hashlib
import importlib.util
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

TEMPLATES = {
    "backend-upgrade-v2.py": "5200f9e74a6ddbefd975e4f6e1c256201cd786ee7d28820bc9240eb1b0151e88",
    "generation-f4.py": "9c1abe24da6fc775976505af84dd5172c0e6484d890f77179c5e9bc7df886cf4",
    "resource-stream.py": "f911acf470a61221197e58fbd18d4cc42c1a5a7693ae929454f540e2c400f76d",
    "source-artifact-receive.py": "ef6e9c5f5b704ad2bf6c2d48f1bf9e6301c9a729acc7d4e4bb4ec17bcd34ecac",
}
OLD_TARGET = "f4bd382d4668130793fc553df9ce6363c4656ea6"
OLD_STOP = "2026-10-25T21:00:00Z"
OLD_KIND = "exact-f4-production-entry-generation"
NEW_KIND = "exact-pinned-production-entry-generation"
HERE = Path(__file__).resolve().parent


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def checked_templates():
    result = {}
    for name, expected in TEMPLATES.items():
        path = HERE / name
        if path.is_symlink():
            raise ValueError("REGULAR_REVIEWED_TEMPLATE_REQUIRED")
        raw = path.read_bytes()
        if digest(raw) != expected:
            raise ValueError("EXACT_REVIEWED_TEMPLATE_SHA_REQUIRED:" + name)
        result[name] = raw.decode("utf-8")
    return result


def replacement(text, before, after, count=1):
    if text.count(before) != count:
        raise ValueError("EXACT_TEMPLATE_PREIMAGE_COUNT_REQUIRED:" + before)
    return text.replace(before, after)


def deadline(value, now):
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", value):
        raise ValueError("EXPLICIT_ABSOLUTE_UTC_Z_DEADLINE_REQUIRED")
    # Python 3.10 is the original cloud host stdlib boundary.
    parsed = datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)  # noqa: UP017
    seconds = (parsed - now).total_seconds()
    if not 1800 <= seconds <= 43200:
        raise ValueError("NEW_WINDOW_30_MINUTES_TO_12_HOURS_REQUIRED")
    return parsed


def reviewed_builder():
    path = HERE / "backend-upgrade-v2.py"
    if path.is_symlink() or digest(path.read_bytes()) != TEMPLATES[path.name]:
        raise ValueError("EXACT_REVIEWED_BUILDER_REQUIRED")
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location("reviewed_builder", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def derive_texts(templates, source, stop_utc, source_count):
    if (
        not re.fullmatch(r"[0-9a-f]{40}", source)
        or type(source_count) is not int
        or source_count < 3
    ):
        raise ValueError("EXACT_FULL_SOURCE_AND_REAL_FILE_COUNT_REQUIRED")
    builder = replacement(
        templates["backend-upgrade-v2.py"],
        'TARGET = "' + OLD_TARGET + '"',
        'TARGET = "' + source + '"',
    )
    builder = replacement(
        builder,
        "exact-source935-to-f4-offline-backend-upgrade",
        "exact-source935-to-resume-offline-backend-upgrade",
        2,
    )
    builder = replacement(
        builder, "V2 exact f4 offline upgrade;", "Pinned resume offline upgrade;"
    )
    builder_sha = digest(builder.encode())
    generation = templates["generation-f4.py"]
    changes = [
        (
            'SOURCE = "' + OLD_TARGET + '"',
            'SOURCE = "' + source + '"\nSOURCE_COUNT = ' + str(source_count),
            1,
        ),
        (
            'BUILDER_SHA = "' + TEMPLATES["backend-upgrade-v2.py"] + '"',
            'BUILDER_SHA = "' + builder_sha + '"',
            1,
        ),
        ('HARDSTOP = "' + OLD_STOP + '"', 'HARDSTOP = "' + stop_utc + '"', 1),
        (OLD_KIND, NEW_KIND, 2),
        ("len(expected) != 53", "len(expected) != SOURCE_COUNT", 1),
        ('"files": 53', '"files": SOURCE_COUNT', 1),
        ('"source53_count": 53', '"source_file_count": SOURCE_COUNT', 1),
        ("source53_actual_proof_sha256", "source_actual_proof_sha256", 1),
        ("source53_verified", "source_files_verified", 1),
        ("actual53-source-files.json", "actual-source-files.json", 2),
        (
            "ACTUAL_COMPLETE_53_SOURCE_FILES_REQUIRED",
            "ACTUAL_COMPLETE_SOURCE_FILES_REQUIRED",
            1,
        ),
        ("PROBE53", "PROBE_FILES", 2),
        ("exact53", "exact_files", 2),
        (
            "Fresh production-entry f4 generation;",
            "Fresh pinned production-entry generation;",
            1,
        ),
        (
            "f4_frontend_frozen_equal_file_set_sha256",
            "target_frontend_frozen_equal_file_set_sha256",
            1,
        ),
        ("relabelled_to_f4", "relabelled_to_target", 1),
        (
            "BOUNDED_FUTURE_WINDOW_NOT_AFTER_21Z_REQUIRED",
            "BOUNDED_FUTURE_WINDOW_WITHIN_RESUME_PROFILE_REQUIRED",
            1,
        ),
    ]
    for before, after, count in changes:
        generation = replacement(generation, before, after, count)
    generation_sha = digest(generation.encode())
    stream = templates["resource-stream.py"]
    for before, after, count in [
        ('SOURCE = "' + OLD_TARGET + '"', 'SOURCE = "' + source + '"', 1),
        (
            'GENERATOR_SHA = "' + TEMPLATES["generation-f4.py"] + '"',
            'GENERATOR_SHA = "' + generation_sha + '"',
            1,
        ),
        ('HARDSTOP = "' + OLD_STOP + '"', 'HARDSTOP = "' + stop_utc + '"', 1),
        (OLD_KIND, NEW_KIND, 1),
        (
            "FUTURE_SAMPLE_AND_FINALTAIL_WINDOW_WITHIN_21Z_REQUIRED",
            "FUTURE_SAMPLE_AND_FINALTAIL_WINDOW_WITHIN_PROFILE_REQUIRED",
            1,
        ),
        ("ABSOLUTE_21Z_BOUND_REQUIRED", "ABSOLUTE_PROFILE_BOUND_REQUIRED", 1),
    ]:
        stream = replacement(stream, before, after, count)
    receiver = replacement(
        templates["source-artifact-receive.py"],
        'HELPER_SHA = "' + TEMPLATES["backend-upgrade-v2.py"] + '"',
        'HELPER_SHA = "' + builder_sha + '"',
    )
    receiver = replacement(
        receiver,
        "fixed five-file public f4 source artifact",
        "pinned five-file public resume source artifact",
    )
    texts = {
        "backend-upgrade.py": builder,
        "generation.py": generation,
        "resource-stream.py": stream,
        "source-artifact-receive.py": receiver,
    }
    for name, text in texts.items():
        compile(text, name, "exec")
    return texts


def new_directory(path):
    if not path.is_absolute() or path.parent.resolve() != path.parent:
        raise ValueError("NEW_CANONICAL_ABSOLUTE_DIRECTORY_REQUIRED")
    path.mkdir(mode=0o700)


def write_new(path, raw):
    descriptor = os.open(
        path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600
    )
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())


def derive(args):
    now = datetime.now(timezone.utc)  # noqa: UP017 -- Python 3.10 cloud-compatible.
    deadline(args.stop_utc, now)
    if not re.fullmatch(r"[0-9a-f]{40}", args.source):
        raise ValueError("EXPLICIT_COMPLETE_SOURCE_COMMIT_REQUIRED")
    templates = checked_templates()
    old_builder = reviewed_builder()
    resolved = (
        old_builder.git(args.repository, "rev-parse", args.source + "^{commit}")
        .decode()
        .strip()
    )
    if resolved != args.source:
        raise ValueError("EXACT_GIT_COMMIT_REQUIRED")
    source_files = old_builder.tree(
        args.repository, args.source, old_builder.SOURCE_PATHS
    )
    old_builder.TARGET = args.source
    frozen = old_builder.compare_frozen(
        old_builder.tree(args.repository, old_builder.BASE, old_builder.FROZEN),
        old_builder.tree(args.repository, args.source, old_builder.FROZEN),
    )
    texts = derive_texts(templates, args.source, args.stop_utc, len(source_files))
    new_directory(args.output)
    metadata = {}
    for name, text in texts.items():
        raw = text.encode()
        write_new(args.output / name, raw)
        metadata[name] = {"bytes": len(raw), "sha256": digest(raw)}
    profile = {
        "kind": "new-explicit-source-time-resume-profile-v1",
        "created_utc": now.isoformat(),
        "source_sha": args.source,
        "stop_utc": args.stop_utc,
        "source_file_count": len(source_files),
        "source_file_set_sha256": digest(
            json.dumps(source_files, sort_keys=True, separators=(",", ":")).encode()
        ),
        "frozen_file_set_sha256": frozen["file_set_sha256"],
        "template_sha256": TEMPLATES,
        "derived_files": metadata,
        "old_helpers_modified": False,
        "cloud_or_SUT_executed": False,
    }
    raw = (json.dumps(profile, indent=2, sort_keys=True) + "\n").encode()
    write_new(args.output / "profile.json", raw)
    return {
        "success": True,
        "profile": str(args.output / "profile.json"),
        "profile_sha256": digest(raw),
        "source_sha": args.source,
        "source_file_count": len(source_files),
        "stop_utc": args.stop_utc,
        "cloud_or_SUT_executed": False,
    }


def package(args):
    import zipfile

    if digest(args.profile.read_bytes()) != args.profile_sha256:
        raise ValueError("ROOT_PINNED_NEW_PROFILE_SHA_REQUIRED")
    profile = json.loads(args.profile.read_bytes())
    if profile["kind"] != "new-explicit-source-time-resume-profile-v1":
        raise ValueError("EXACT_RESUME_PROFILE_REQUIRED")
    for name, record in profile["derived_files"].items():
        path = args.profile.parent / name
        if path.is_symlink() or digest(path.read_bytes()) != record["sha256"]:
            raise ValueError("DERIVED_PROFILE_OBJECT_CHANGED")
    new_directory(args.output)
    path = args.profile.parent / "backend-upgrade.py"
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location("pinned_resume_builder", path)
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    result = builder.prepare(
        SimpleNamespace(repository=args.repository, output=args.output / "source")
    )
    files = {
        name: (args.output / "source" / name).read_bytes()
        for name in (
            "source-backend.tar.gz",
            "source-manifest.json",
            "frozen-equality.json",
            "Dockerfile",
        )
    }
    files["backend-upgrade.py"] = path.read_bytes()
    if sum(map(len, files.values())) >= 1024 * 1024:
        raise ValueError("FIVE_FILE_ARTIFACT_SIZE_BOUND")
    artifact = args.output / "source-artifact.zip"
    descriptor = os.open(
        artifact, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600
    )
    with os.fdopen(descriptor, "w+b") as stream:
        with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for name, raw in sorted(files.items()):
                archive.writestr(name, raw)
        stream.flush()
        os.fsync(stream.fileno())
    return {
        "success": True,
        "source_sha": profile["source_sha"],
        "artifact": str(artifact),
        "bytes": artifact.stat().st_size,
        "sha256": digest(artifact.read_bytes()),
        "manifest_sha256": result["manifest_sha256"],
        "builder_sha256": profile["derived_files"]["backend-upgrade.py"]["sha256"],
        "cloud_or_SUT_executed": False,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="action", required=True)
    for action in ("derive", "package"):
        command = commands.add_parser(action)
        command.add_argument("--repository", type=Path, required=True)
        command.add_argument("--output", type=Path, required=True)
        if action == "derive":
            command.add_argument("--source", required=True)
            command.add_argument("--stop-utc", required=True)
        else:
            command.add_argument("--profile", type=Path, required=True)
            command.add_argument("--profile-sha256", required=True)
    arguments = parser.parse_args()
    os.umask(0o077)
    print(
        json.dumps(
            derive(arguments) if arguments.action == "derive" else package(arguments)
        )
    )
