"""Receive only the pinned five-file public resume source artifact after official ZIP SHA pinning."""

import argparse
import hashlib
import importlib.util
import json
import os
import re
import stat
import sys
import tarfile
import zipfile
from pathlib import Path

HELPER_SHA = "ebc91ce54ee73a418b9df11c3878ae75e348198b64c25060aeff8462de3949d1"
ALLOWLIST = {
    "source-backend.tar.gz",
    "source-manifest.json",
    "frozen-equality.json",
    "Dockerfile",
    "backend-upgrade.py",
}
MAXIMUM = 1024 * 1024


def sha(p):
    h = hashlib.sha256()
    with p.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def private(p, directory=False):
    info = p.lstat()
    if (
        p.resolve() != p
        or info.st_uid != os.geteuid()
        or stat.S_IMODE(info.st_mode) != (0o700 if directory else 0o600)
        or not (stat.S_ISDIR(info.st_mode) if directory else stat.S_ISREG(info.st_mode))
    ):
        raise ValueError("OWNED_CANONICAL_PRIVATE_OBJECT_REQUIRED")


def inspect_zip(path, expected, manifest_expected):
    private(path)
    if not re.fullmatch(r"[0-9a-f]{64}", expected) or sha(path) != expected:
        raise ValueError("OFFICIAL_WHOLE_ZIP_SHA256_REQUIRED")
    if not re.fullmatch(r"[0-9a-f]{64}", manifest_expected):
        raise ValueError("ROOT_VERIFIED_ACTUAL_MANIFEST_SHA_REQUIRED")
    with zipfile.ZipFile(path) as z:
        infos = z.infolist()
        if len(infos) != 5 or {v.filename for v in infos} != ALLOWLIST:
            raise ValueError("EXACT_FIVE_PUBLIC_FILES_NO_DIRECTORIES_OR_EXTRAS")
        if sum(v.file_size for v in infos) > MAXIMUM:
            raise ValueError("PUBLIC_SOURCE_ARTIFACT_SIZE_BOUND")
        for info in infos:
            kind = stat.S_IFMT(info.external_attr >> 16)
            if (
                info.is_dir()
                or kind not in {0, stat.S_IFREG}
                or info.flag_bits & 1
                or info.compress_type not in {zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED}
            ):
                raise ValueError("REGULAR_UNENCRYPTED_SUPPORTED_ZIP_ENTRIES_REQUIRED")
        if z.testzip() is not None:
            raise ValueError("ZIP_CRC_VERIFICATION_FAILED")
        data = {v.filename: z.read(v) for v in infos}
    if hashlib.sha256(data["backend-upgrade.py"]).hexdigest() != HELPER_SHA:
        raise ValueError("EXACT_REVIEWED_V2_BUILDER_REQUIRED")
    if hashlib.sha256(data["source-manifest.json"]).hexdigest() != manifest_expected:
        raise ValueError("ACTUAL_LINUX_MANIFEST_SHA_MISMATCH")
    return data


def receive(args):
    private(args.output.parent, True)
    data = inspect_zip(args.zip, args.zip_sha256, args.manifest_sha256)
    # No extractall: allowlisted literal basenames, fixed fds, new directory only.
    args.output.mkdir(mode=0o700)
    for name in sorted(ALLOWLIST):
        fd = os.open(
            args.output / name,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
            0o600,
        )
        with os.fdopen(fd, "wb") as f:
            f.write(data[name])
    helper = args.output / "backend-upgrade.py"
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location("reviewed_exact_v2_upgrade", helper)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    manifest, _ = m.source_package(args.output, args.manifest_sha256)
    if {p.name for p in args.output.iterdir()} != ALLOWLIST:
        raise ValueError("EXTRA_OBJECT_AFTER_VERIFICATION")
    return {
        "success": True,
        "directory": str(args.output),
        "official_zip_sha256": args.zip_sha256,
        "actual_manifest_sha256": args.manifest_sha256,
        "builder_sha256": HELPER_SHA,
        "source_sha": manifest["source_sha"],
        "source_archive_sha256": manifest["source_archive_sha256"],
        "files": 5,
        "ZIP_CRC_and_safe_TAR_verified": True,
        "Docker_or_business_started": False,
    }


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--zip", type=Path, required=True)
    p.add_argument("--zip-sha256", required=True)
    p.add_argument("--manifest-sha256", required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    os.umask(0o077)
    try:
        print(json.dumps(receive(args)))
    except (
        OSError,
        ValueError,
        KeyError,
        TypeError,
        zipfile.BadZipFile,
        tarfile.TarError,
        RuntimeError,
    ) as error:
        print(
            json.dumps(
                {
                    "success": False,
                    "error_class": type(error).__name__,
                    "reason": str(error),
                    "partial_state_preserved": args.output.exists(),
                    "Docker_or_business_started": False,
                }
            )
        )
        raise SystemExit(1) from None
