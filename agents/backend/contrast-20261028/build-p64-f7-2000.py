"""Offline 20Z window variant; preserve frozen 16Z runtime except exact time literals."""

import base64
import hashlib
import importlib.util
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OLD = ROOT / "tmp/790_backend_contrast_20261028/p64-f7-window1600"
OUT = ROOT / "tmp/790_backend_contrast_20261028/p64-f7-window2000"
DEST = "/root/t44-r9/p790-f7-2000-ui03"
OLD_MANIFEST = "1da8ff5eaede6d6349c04ee8c3208a85ea2628b6a7604351e9dcfe332feb1de8"
GEN_SHA = "9edafbbff0586b5f77a701bd37f715685fba4169abaae510474343af75a8b427"
GEN = Path(
    "/Users/yang/Desktop/nothing/软件开发大作业/.agent-worktrees/deployment-v4-f7-20z-20261028/agents/deployment/v4-f7-20z-20261028/profile-f7-2000/generation.py"
)
CHANGES = {
    "790_bootstrap.py": [
        (
            "datetime(2026, 10, 28, 16, 0, tzinfo=UTC)",
            "datetime(2026, 10, 28, 20, 0, tzinfo=UTC)",
        )
    ],
    "edge/790_http.py": [
        (
            "datetime(2026, 10, 28, 16, 0, tzinfo=UTC)",
            "datetime(2026, 10, 28, 20, 0, tzinfo=UTC)",
        )
    ],
    "transport/790_transfer.py": [
        (
            "datetime(2026, 10, 28, 16, 0, tzinfo=UTC)",
            "datetime(2026, 10, 28, 20, 0, tzinfo=UTC)",
        )
    ],
    "edge/790_authority.py": [
        ("2026-10-28T16:00:00Z", "2026-10-28T20:00:00Z"),
        ("EXACT_16Z_WINDOW", "EXACT_20Z_WINDOW"),
    ],
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def write(name, raw):
    target = OUT / name
    target.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o644)
    with os.fdopen(fd, "wb") as stream:
        stream.write(raw)


def load_builder(name):
    path = Path(__file__).with_name(name)
    spec = importlib.util.spec_from_file_location(
        "owned_" + path.stem.replace("-", "_"), path
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    original = load_builder("build-p64-f7.py")
    envelope = load_builder("build-p64-f7-ui-v2.py")
    original.DEST = DEST
    old_raw = (OLD / "manifest.json").read_bytes()
    assert sha(old_raw) == OLD_MANIFEST
    manifest = json.loads(old_raw)
    gen_raw = GEN.read_bytes()
    assert sha(gen_raw) == GEN_SHA
    OUT.mkdir()
    proof = []
    for name in original.FILES:
        raw = (OLD / name).read_bytes()
        assert sha(raw) == manifest["files"][name]["sha256"]
        new = raw.decode()
        for before, after in CHANGES.get(name, []):
            assert new.count(before) == 1
            new = new.replace(before, after)
        changed = new.encode()
        write(name, changed)
        proof.append(
            {
                "file": name,
                "old_sha256": sha(raw),
                "new_sha256": sha(changed),
                "allowlist": CHANGES.get(name, []),
                "unchanged": raw == changed,
            }
        )
    manifest["window_utc"] = "2026-10-28T20:00:00Z"
    manifest["supersedes_manifest_sha256"] = OLD_MANIFEST
    manifest["phase_GEN_sha256"] = GEN_SHA
    manifest["files"] = {
        name: {
            "bytes": (OUT / name).stat().st_size,
            "sha256": sha((OUT / name).read_bytes()),
        }
        for name in original.FILES
    }
    manifest_raw = canonical(manifest)
    bundle = sha(manifest_raw)
    write("manifest.json", manifest_raw)
    write("fixtures/generation-f7-2000.PUBLIC.py", gen_raw)
    write(
        "window-byte-proof.PUBLIC.json",
        canonical(
            {
                "kind": "P790_20Z_LITERAL_ALLOWLIST",
                "old_commit": "20eb4ae340375a0b687324df15dacf11e2a73c0b",
                "old_manifest_sha256": OLD_MANIFEST,
                "new_manifest_sha256": bundle,
                "files": proof,
                "cloud_SUT_actions": False,
            }
        ),
    )
    for side in ("APP", "LOAD"):
        value = json.loads(
            (OLD / f"{side}-configuration.template.PUBLIC.json").read_bytes()
        )
        value.update(tools_dir=DEST, manifest_sha256=bundle)
        write(f"{side}-configuration.template.PUBLIC.json", canonical(value))
    for mode in ("prep", "pressure"):
        value = json.loads((OLD / f"{mode}-grant.template.PUBLIC.json").read_bytes())
        value.update(stop_utc=manifest["window_utc"], expires_at=manifest["window_utc"])
        write(f"{mode}-grant.template.PUBLIC.json", canonical(value))
    entries = {
        name: {
            "text": (OUT / name).read_text(),
            "sha256": sha((OUT / name).read_bytes()),
        }
        for name in (*original.FILES, "manifest.json")
    }
    groups, pending = [], {}
    for name, item in entries.items():
        candidate = {**pending, name: item}
        if (
            pending
            and len(original.command(candidate, bundle, not groups, False).encode())
            > 12000
        ):
            groups.append(pending)
            pending = {name: item}
        else:
            pending = candidate
    groups.append(pending)
    parts = []
    for index, group in enumerate(groups):
        raw = original.command(
            group, bundle, index == 0, index == len(groups) - 1
        ).encode()
        ui = envelope.outer(raw)
        assert len(raw) <= 12000
        assert len(base64.b64encode(raw)) + 300 < 18000
        assert len(ui) + 300 < 18000
        raw_name, ui_name = (
            f"raw-part{index + 1:02}.PUBLIC.sh",
            f"ui-part{index + 1:02}.PUBLIC.txt",
        )
        write(raw_name, raw)
        write(ui_name, ui)
        parts.append(
            {
                "raw_file": raw_name,
                "raw_bytes": len(raw),
                "raw_sha256": sha(raw),
                "ui_file": ui_name,
                "ui_bytes": len(ui),
                "ui_sha256": sha(ui),
                "base64_plus_description": len(base64.b64encode(raw)) + 300,
                "complete_ui_plus_description": len(ui) + 300,
                "description_allowance": 300,
                "files": list(group),
            }
        )
    delivery = {
        "kind": "P64_F7_2000_UI03_WINDOW_VARIANT",
        "runtime_manifest_sha256": bundle,
        "old_runtime_manifest_sha256": OLD_MANIFEST,
        "old_UI_delivery_sha256": "243d90ca022aaf1d336854066fd9c65e9e49a65f20047594d22fae95184097c5",
        "destination": DEST,
        "raw_cap": 12000,
        "ceiling": 18000,
        "parts": parts,
        "cloud_actions_executed": False,
        "actual_root_grant_or_session_received": False,
        "usage": "raw_file may be base64-wrapped ONCE; ui_file is already complete and must be sent directly, never wrapped twice",
    }
    raw = canonical(delivery)
    write("delivery.PUBLIC.json", raw)
    print(
        json.dumps(
            {"manifest_sha256": bundle, "delivery_sha256": sha(raw), "parts": parts},
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
