"""Parameterized f7 P64 short diagnostic driver; no implicit paths or grants."""

import argparse
import gzip
import hashlib
import io
import json
import os
import re
import subprocess
from pathlib import Path

CONFIG = None
ROOT = PHASE = TOOLS = TRANSFER = RUN = WORK = MIRROR = None
BINDING = MANIFEST = KEY = MIRROR_BIND = None
SOURCE = "f7cdb5fa3b19f84d8ab0d0b042bf51a5b8484e8f"


def configure(side, argv):
    global \
        CONFIG, \
        ROOT, \
        PHASE, \
        TOOLS, \
        TRANSFER, \
        RUN, \
        WORK, \
        MIRROR, \
        BINDING, \
        MANIFEST, \
        KEY, \
        MIRROR_BIND
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--configuration", type=Path, required=True)
    parser.add_argument("--configuration-sha256", required=True)
    args = parser.parse_args(argv)
    fd = os.open(args.configuration, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(fd, "rb") as stream:
        raw = stream.read(100001)
    if len(raw) > 100000 or hashlib.sha256(raw).hexdigest() != args.configuration_sha256:
        raise ValueError("EXPLICIT_PUBLIC_DRIVER_CONFIGURATION_PIN_REQUIRED")
    CONFIG = json.loads(raw)
    if CONFIG["kind"] != "P790_F7_" + side + "_CONFIGURATION_V4" or CONFIG["source_sha"] != SOURCE:
        raise ValueError("EXACT_F7_DRIVER_ONLY")
    TOOLS = Path(CONFIG["tools_dir"])
    TRANSFER = TOOLS / "transport"
    MANIFEST = CONFIG["manifest_sha256"]
    BINDING = CONFIG["binding_sha256"]
    KEY = CONFIG["key_sha256"]
    if not re.fullmatch("[0-9a-f]{64}", BINDING) or not re.fullmatch(
        "[0-9a-f]{64}", CONFIG["root_grant_sha256"]
    ):
        raise ValueError("EXPLICIT_ACTUAL_BINDING_AND_PRESSURE_GRANT_REQUIRED")
    for path in (TOOLS, TRANSFER):
        if not path.is_absolute() or path.resolve() != path:
            raise ValueError("CANONICAL_PUBLIC_TOOLS_REQUIRED")
    if side == "APP":
        PHASE = Path(CONFIG["phase_dir"])
        RUN = Path(CONFIG["output_dir"])
    else:
        WORK = Path(CONFIG["work_dir"])
        MIRROR = Path(CONFIG["mirror_dir"])
        MIRROR_BIND = CONFIG["mirror_binding_sha256"]


def h(b):
    return hashlib.sha256(b).hexdigest()


def save(p, b):
    f = os.open(p, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(f, "wb") as s:
        s.write(b)
        s.flush()
        os.fsync(s.fileno())


def main(argv=None):
    configure("LOAD", argv)
    if h((TOOLS / "manifest.json").read_bytes()) != MANIFEST:
        raise SystemExit("frozen v3 tools differ")
    if h((TRANSFER / "790_transfer.py").read_bytes()) != CONFIG["transfer_sha256"]:
        raise SystemExit("transfer differs")
    m = json.loads((WORK / "metadata.PUBLIC.json").read_bytes())
    p = m["original_public_meta"]
    if m["root_grant_sha256"] != CONFIG["root_grant_sha256"]:
        raise SystemExit("explicit pressure grant differs")
    if (
        m["phase_binding_sha256"] != BINDING
        or m["source_sha"] != SOURCE
        or p["binding_sha256"] != BINDING
        or p["key_sha256"] != KEY
    ):
        raise SystemExit("new arm or recipient differs")
    if (
        p["files"]["control.private.json"]["sha256"] != CONFIG["control_sha256"]
        or p["files"]["ca.pem"]["sha256"] != CONFIG["ca_sha256"]
    ):
        raise SystemExit("actual APP control or CA differs")
    if p["files"]["session.private.json"]["bytes"] < 1000 or not re.fullmatch(
        "[a-f0-9]{64}", p["files"]["session.private.json"]["sha256"]
    ):
        raise SystemExit("noncredential material rejected before matrix")
    n = m["part_count"]
    if type(n) is not int or not 1 <= n <= 4:
        raise SystemExit("bounded complete parts required")
    compressed = b"".join((WORK / ("part-" + str(i) + ".OPAQUE")).read_bytes() for i in range(n))
    if (
        len(compressed) != m["compressed_bytes"]
        or len(compressed) > 47200
        or h(compressed) != m["compressed_sha256"]
    ):
        raise SystemExit("complete ciphertext transport differs")
    with gzip.GzipFile(fileobj=io.BytesIO(compressed)) as stream:
        raw = stream.read(2_000_001)
    if len(raw) > 2_000_000 or len(raw) != m["raw_bytes"] or h(raw) != m["raw_sha256"]:
        raise SystemExit("exact restored ciphertext envelope required")
    save(WORK / "transfer.OPAQUE.jsonl", raw)
    subprocess.run(
        [
            "python3",
            "-B",
            str(TRANSFER / "790_transfer.py"),
            "open",
            "--private-key",
            str(Path(CONFIG["private_key"])),
            "--transfer-file",
            str(WORK / "transfer.OPAQUE.jsonl"),
            "--public-record-sha256",
            p["public_record_sha256"],
            "--output-dir",
            str(WORK / "actual-session-opened01"),
        ],
        check=True,
        timeout=60,
    )
    if h((MIRROR / "binding.json").read_bytes()) != MIRROR_BIND:
        raise SystemExit("prestarted mirror binding differs")
    x = subprocess.run(
        [
            "python3",
            "-B",
            str(MIRROR / "controller.py"),
            "status",
            "--directory",
            str(MIRROR),
            "--binding-sha256",
            MIRROR_BIND,
        ],
        capture_output=True,
        timeout=15,
    )
    save(WORK / "mirror-before.PUBLIC.json", x.stdout)
    if x.returncode:
        raise SystemExit("mirror status refused; no matrix")
    v = json.loads(x.stdout)
    if (
        not v["observed_before_pid"]
        or v["observed_before_pid"] != v["observed_after_pid"]
        or not v.get("progress", {}).get("raw_bytes_observed")
    ):
        raise SystemExit("live numeric resource transport unproven")
    argv = [
        "python3",
        "-B",
        str(TOOLS / "790_load.py"),
        "--inputs-dir",
        str(WORK / "actual-session-opened01/inputs"),
        "--output-dir",
        str(WORK / "matrix01"),
        "--control-sha256",
        p["files"]["control.private.json"]["sha256"],
        "--packet-sha256",
        p["files"]["session.private.json"]["sha256"],
        "--manifest-sha256",
        MANIFEST,
        "--expected-host",
        CONFIG["expected_host"],
        "--python-image",
        CONFIG["python_image"],
        "--python-image-id",
        CONFIG["python_image_id"],
    ]
    x = subprocess.run(argv, capture_output=True, timeout=300)
    save(WORK / "matrix.stdout.PUBLIC.jsonl", x.stdout)
    save(WORK / "matrix.stderr.PRIVATE", x.stderr)
    print(x.stdout.decode(), end="", flush=True)
    if x.returncode:
        print(
            json.dumps(
                {"kind": "V4_MATRIX_FAILED_PREFIX_PRESERVED_NO_RETRY", "exit_code": x.returncode}
            )
        )
        return x.returncode
    print(
        json.dumps(
            {
                "kind": "V4_MATRIX_CONTROLLER_COMPLETE_NOT_ACCEPTANCE",
                "source_sha": m["source_sha"],
                "namespace": CONFIG["namespace"],
                "noncredential_resource_marker_never_used_as_session": True,
            }
        ),
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
