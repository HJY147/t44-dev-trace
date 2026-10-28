"""Real local raw/prefix/whole-SHA checks only, no service or cloud action."""

import hashlib
import importlib.util
import json
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "mirror_finalize", ROOT / "deployment/cloud-reuse/resource-mirror-finalize.py"
)
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)


def fixture(root, monkeypatch):
    def write(name, raw):
        path = root / name
        path.write_bytes(raw)
        path.chmod(0o600)

    controller = (
        ROOT / "agents/deployment/resume-20261028/window1030/profile/resource-stream.py"
    ).read_bytes()
    assert M.sha(controller) == M.CONTROLLER
    write("controller.py", controller)
    binding = json.dumps({"stream_id": "synthetic-mirror"}).encode()
    write("binding.json", binding)
    monkeypatch.setattr(M, "BINDING", M.sha(binding))
    prefix = (
        json.dumps(
            {
                "kind": "resource_header",
                "source_sha": M.SOURCE,
                "stream_id": "synthetic-mirror",
            }
        )
        + "\n"
    ).encode()
    prefix += (
        json.dumps(
            {"kind": "resource_sample", "role": "scheduler", "cpu_percent": None}
        )
        + "\n"
    ).encode()
    final = {
        "kind": "resource_final",
        "prefix_bytes": len(prefix),
        "prefix_sha256": M.sha(prefix),
        "reason": "explicit_seal",
    }
    raw = prefix + (json.dumps(final) + "\n").encode()
    write("app-raw.jsonl", raw)
    metadata = {
        "transport_complete": True,
        "from_offset_zero": True,
        "raw_bytes": len(raw),
        "raw_sha256": M.sha(raw),
        "actual_coverage": {"rows_with_null_CPU_or_RSS": 1},
    }
    write("mirror-final.json", json.dumps(metadata).encode())
    return raw


def test_exact_cross_node_seal_and_local_prefix_preserve_missing_metric(monkeypatch):
    with tempfile.TemporaryDirectory(
        dir=ROOT / "tmp/793_deployment_resume"
    ) as directory:
        root = Path(directory).resolve()
        raw = fixture(root, monkeypatch)
        result = M.verify(root, len(raw), M.sha(raw))
        assert (
            result["transport_complete"]
            and result["raw_sha256"] == hashlib.sha256(raw).hexdigest()
        )
        assert result["actual_coverage"]["rows_with_null_CPU_or_RSS"] == 1
        assert result["business_or_acceptance_verdict"] is None


def test_wrong_app_sha_or_partial_transport_refuses(monkeypatch):
    with tempfile.TemporaryDirectory(
        dir=ROOT / "tmp/793_deployment_resume"
    ) as directory:
        root = Path(directory).resolve()
        raw = fixture(root, monkeypatch)
        with pytest.raises(ValueError, match="APP_SEAL"):
            M.verify(root, len(raw), "0" * 64)
        final = json.loads((root / "mirror-final.json").read_bytes())
        final["transport_complete"] = False
        (root / "mirror-final.json").write_text(json.dumps(final))
        with pytest.raises(ValueError, match="COMPLETE_OFFSET"):
            M.verify(root, len(raw), M.sha(raw))


def test_raw_tamper_or_symlink_refuses(monkeypatch):
    for change in ("tamper", "symlink"):
        with tempfile.TemporaryDirectory(
            dir=ROOT / "tmp/793_deployment_resume"
        ) as directory:
            root = Path(directory).resolve()
            raw = fixture(root, monkeypatch)
            path = root / "app-raw.jsonl"
            if change == "tamper":
                path.write_bytes(raw + b"{}\n")
            else:
                path.rename(root / "original")
                path.symlink_to(root / "original")
            with pytest.raises((ValueError, OSError)):
                M.verify(root, len(raw), M.sha(raw))
