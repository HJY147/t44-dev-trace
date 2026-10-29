"""Parameterized f7 P64 short diagnostic driver; no implicit paths or grants."""

import argparse
import base64
import datetime
import gzip
import hashlib
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
    configure("APP", argv)
    if (
        h((TOOLS / "manifest.json").read_bytes()) != MANIFEST
        or h((PHASE / "binding.json").read_bytes()) != BINDING
    ):
        raise SystemExit("frozen manifest or phase differs")
    if h((TRANSFER / "790_transfer.py").read_bytes()) != CONFIG["transfer_sha256"]:
        raise SystemExit("transfer helper differs")
    if h((Path(CONFIG["public_key_file"])).read_bytes()) != KEY:
        raise SystemExit("recipient differs")
    if h(Path(CONFIG["mirror_path"]).read_bytes()) != CONFIG["mirror_sha256"]:
        raise SystemExit("actual resource mirror handoff differs before session")
    RUN.mkdir(mode=0o700)
    argv = [
        "python3",
        "-B",
        str(TOOLS / "790_host.py"),
        "edge",
        "--phase-dir",
        str(PHASE),
        "--binding-sha256",
        BINDING,
        "--fixture-name",
        CONFIG["fixture_name"],
        "--split-name",
        CONFIG["split_name"],
        "--manifest-sha256",
        MANIFEST,
        "--budget-receipt",
        CONFIG["budget_receipt"],
        "--budget-receipt-sha256",
        CONFIG["budget_receipt_sha256"],
        "--root-grant",
        CONFIG["root_grant"],
        "--root-grant-sha256",
        CONFIG["root_grant_sha256"],
        "--scope-bridge-dir",
        CONFIG["scope_bridge_dir"],
    ]
    try:
        x = subprocess.run(argv, capture_output=True, timeout=340)
    except subprocess.TimeoutExpired as error:
        save(RUN / "stage2.stdout.PUBLIC", error.stdout or b"")
        save(RUN / "stage2.stderr.PRIVATE", error.stderr or b"")
        name = CONFIG["namespace"] + "-790s2"
        info = json.loads(
            subprocess.check_output(
                ["docker", "--context", "default", "inspect", "--format", "{{json .}}", name],
                timeout=15,
            )
        )
        if (
            info["Image"] != CONFIG["python_image_id"]
            or info["Config"]["Labels"].get("io.t44.contrast.owner") != CONFIG["namespace"]
        ):
            raise SystemExit("timeout owner differs; no signal") from None
        subprocess.run(
            ["docker", "--context", "default", "stop", "--time", "15", name], check=True, timeout=30
        )
        print(
            json.dumps(
                {
                    "kind": "S2_TIMEOUT_PARTIAL_PRESERVED_NO_RETRY",
                    "SUT_pressure_executed": False,
                    "root_grant_sha256": CONFIG["root_grant_sha256"],
                }
            )
        )
        return 1
    save(RUN / "stage2.stdout.PUBLIC", x.stdout)
    save(RUN / "stage2.stderr.PRIVATE", x.stderr)
    if x.returncode:
        print(
            json.dumps(
                {
                    "kind": "S2_FAILED_PARTIAL_PRESERVED_NO_RETRY",
                    "exit_code": x.returncode,
                    "SUT_pressure_executed": False,
                    "root_grant_sha256": CONFIG["root_grant_sha256"],
                }
            )
        )
        return x.returncode
    rows = [json.loads(v) for v in x.stdout.decode().splitlines()]
    complete = next(v for v in rows if v.get("kind") == "contrast790-s2-host-complete")
    finished = next(v for v in rows if v.get("kind") == "stage2-complete-not-acceptance")
    if not finished["diagnostic_valid"] or finished["slots"] != 441:
        raise SystemExit("incomplete real stage2")
    argv = [
        "python3",
        "-B",
        str(TRANSFER / "790_transfer.py"),
        "seal",
        "--public-key-file",
        str(Path(CONFIG["public_key_file"])),
        "--public-key-sha256",
        KEY,
        "--binding-sha256",
        BINDING,
        "--control",
        complete["control_path"],
        "--control-sha256",
        complete["control_sha256"],
        "--session",
        complete["packet_path"],
        "--packet-sha256",
        complete["packet_sha256"],
        "--ca",
        complete["ca_path"],
        "--ca-sha256",
        CONFIG["ca_sha256"],
        "--mirror",
        CONFIG["mirror_path"],
        "--mirror-sha256",
        CONFIG["mirror_sha256"],
        "--output-dir",
        str(RUN / "sealed"),
    ]
    x = subprocess.run(argv, capture_output=True, timeout=60)
    save(RUN / "seal.stdout.PUBLIC", x.stdout)
    save(RUN / "seal.stderr.PRIVATE", x.stderr)
    if x.returncode:
        raise SystemExit(x.returncode)
    raw = (RUN / "sealed/transfer.public.jsonl").read_bytes()
    meta = json.loads(raw.splitlines()[0])
    compressed = gzip.compress(raw, mtime=0)
    parts = [compressed[i : i + 11800] for i in range(0, len(compressed), 11800)]
    if len(parts) > 4:
        raise SystemExit("bounded export exceeded; no pressure")
    metadata = {
        "kind": "V4_OPAQUE_TRANSFER_METADATA",
        "source_sha": SOURCE,
        "phase_binding_sha256": BINDING,
        "s2_complete_utc": finished["utc"],
        "seal_complete_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),  # noqa: UP017 -- host3.10
        "original_public_meta": meta,
        "compressed_bytes": len(compressed),
        "compressed_sha256": h(compressed),
        "raw_bytes": len(raw),
        "raw_sha256": h(raw),
        "part_count": len(parts),
        "SUT_pressure_executed": False,
        "root_grant_sha256": CONFIG["root_grant_sha256"],
    }
    save(RUN / "metadata.PUBLIC.json", json.dumps(metadata, separators=(",", ":")).encode())
    for i, b in enumerate(parts):
        save(
            RUN / ("part-" + str(i) + ".OPAQUE.json"),
            json.dumps(
                {
                    "index": i,
                    "parts": len(parts),
                    "bytes": len(b),
                    "sha256": h(b),
                    "data": base64.b64encode(b).decode(),
                },
                separators=(",", ":"),
            ).encode(),
        )
    first = json.loads((RUN / "part-0.OPAQUE.json").read_bytes())
    result = {"metadata": metadata, "first_opaque_part": first}
    out = json.dumps(result, separators=(",", ":"))
    if len(out.encode()) > 17000:
        out = json.dumps({"metadata": metadata, "first_opaque_part": None}, separators=(",", ":"))
    save(RUN / "terminal.PUBLIC.json", out.encode())
    print(out, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
