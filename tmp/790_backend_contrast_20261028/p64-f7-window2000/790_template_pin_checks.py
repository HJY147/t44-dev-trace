"""PUBLIC template pins must identify the exact frozen current runtime; no cloud/SUT."""

import hashlib
import json
import subprocess
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
FROZEN = "7779681010de99cbb4d5946ded9c4bcd5f8ae132"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


@pytest.mark.parametrize("side", ["APP", "LOAD"])
def test_template_transfer_pin_matches_manifest_and_actual_runtime(side):
    template = json.loads(
        (HERE / f"{side}-configuration.template.PUBLIC.json").read_bytes()
    )
    manifest_raw = (HERE / "manifest.json").read_bytes()
    manifest = json.loads(manifest_raw)
    transfer_raw = (HERE / "transport/790_transfer.py").read_bytes()
    assert template["manifest_sha256"] == sha(manifest_raw)
    assert (
        template["transfer_sha256"]
        == manifest["files"]["transport/790_transfer.py"]["sha256"]
        == sha(transfer_raw)
    )
    assert (
        len(transfer_raw)
        == manifest["files"]["transport/790_transfer.py"]["bytes"]
        == 12574
    )


@pytest.mark.parametrize("side", ["APP", "LOAD"])
def test_other_template_sha256_fields_are_unset_actual_inputs(side):
    template = json.loads(
        (HERE / f"{side}-configuration.template.PUBLIC.json").read_bytes()
    )
    for name, value in template.items():
        if name.endswith("_sha256") and name not in {
            "manifest_sha256",
            "transfer_sha256",
        }:
            assert value is None, (side, name)
    assert template["source_sha"] == "f7cdb5fa3b19f84d8ab0d0b042bf51a5b8484e8f"


def test_frozen_runtime_manifest_and_delivery_and_old16_templates_unchanged():
    manifest = json.loads((HERE / "manifest.json").read_bytes())
    names = [*manifest["files"], "manifest.json", "delivery.PUBLIC.json"]
    delivery = json.loads((HERE / "delivery.PUBLIC.json").read_bytes())
    for row in delivery["parts"]:
        names.extend((row["raw_file"], row["ui_file"]))
    paths = [HERE / name for name in names]
    old = HERE.parent / "p64-f7-window1600"
    paths.extend(
        old / f"{side}-configuration.template.PUBLIC.json" for side in ("APP", "LOAD")
    )
    for path in paths:
        relative = path.relative_to(ROOT).as_posix()
        original = subprocess.check_output(
            ["git", "show", FROZEN + ":" + relative], cwd=ROOT
        )
        assert path.read_bytes() == original, relative
