"""Repartition only, retaining the original thirteen runtime files and manifest bytes."""

import base64
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "tmp/790_backend_contrast_20261028/p64-f7-window1600"
OUTPUT = ROOT / "tmp/790_backend_contrast_20261028/p64-f7-ui-encoded-v2"
DEST = "/root/t44-r9/p790-f7-1600-ui02"
MANIFEST = "1da8ff5eaede6d6349c04ee8c3208a85ea2628b6a7604351e9dcfe332feb1de8"
RAW_CAP = 12000


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def outer(raw):
    encoded = base64.b64encode(raw).decode()
    return (
        "python3 - <<'PY'\nimport base64,subprocess\nsubprocess.run(['bash'],input=base64.b64decode("
        + repr(encoded)
        + ",validate=True),check=True)\nPY\n"
    ).encode()


def main():
    spec = importlib.util.spec_from_file_location(
        "p64_original_install_format", Path(__file__).with_name("build-p64-f7.py")
    )
    original = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(original)
    original.DEST = DEST
    manifest_raw = (SOURCE / "manifest.json").read_bytes()
    assert sha(manifest_raw) == MANIFEST
    manifest = json.loads(manifest_raw)
    assert len(manifest["files"]) == 13
    entries = {}
    for name in (*original.FILES, "manifest.json"):
        raw = (SOURCE / name).read_bytes()
        if name != "manifest.json":
            assert sha(raw) == manifest["files"][name]["sha256"]
        entries[name] = {"text": raw.decode(), "sha256": sha(raw)}
    groups = []
    pending = {}
    for name, item in entries.items():
        candidate = {**pending, name: item}
        if (
            pending
            and len(original.command(candidate, MANIFEST, not groups, False).encode()) > RAW_CAP
        ):
            groups.append(pending)
            pending = {name: item}
        else:
            pending = candidate
    groups.append(pending)
    parts = []
    for index, group in enumerate(groups):
        raw = original.command(group, MANIFEST, index == 0, index == len(groups) - 1).encode()
        ui = outer(raw)
        assert len(raw) <= RAW_CAP
        assert len(base64.b64encode(raw)) + 300 < 18000
        assert len(ui) + 300 < 18000
        raw_name = f"raw-part{index + 1:02}.PUBLIC.sh"
        ui_name = f"ui-part{index + 1:02}.PUBLIC.txt"
        (OUTPUT / raw_name).write_bytes(raw)
        (OUTPUT / ui_name).write_bytes(ui)
        parts.append(
            {
                "raw_file": raw_name,
                "raw_bytes": len(raw),
                "raw_sha256": sha(raw),
                "base64_bytes": len(base64.b64encode(raw)),
                "base64_plus_description": len(base64.b64encode(raw)) + 300,
                "ui_file": ui_name,
                "ui_bytes": len(ui),
                "ui_sha256": sha(ui),
                "complete_ui_plus_description": len(ui) + 300,
                "description_allowance": 300,
                "files": list(group),
            }
        )
    value = {
        "kind": "P64_INSTALL_UI_OUTER_ENCODED_V2",
        "runtime_manifest_sha256": MANIFEST,
        "runtime_source_commit": "c0268820",
        "runtime_files_modified": False,
        "destination": DEST,
        "raw_cap": RAW_CAP,
        "ceiling": 18000,
        "parts": parts,
        "cloud_actions_executed": False,
        "usage": "raw_file may be base64-wrapped ONCE by root helper; ui_file is already complete and must be sent directly, never wrapped twice",
    }
    raw = (json.dumps(value, sort_keys=True, indent=2) + "\n").encode()
    (OUTPUT / "delivery.PUBLIC.json").write_bytes(raw)
    print(json.dumps({"delivery_sha256": sha(raw), "parts": parts}, sort_keys=True))


if __name__ == "__main__":
    main()
