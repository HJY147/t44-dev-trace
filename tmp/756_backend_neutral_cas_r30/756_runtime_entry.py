"""LOCAL_PROJECT_RUNTIME_ONLY: real project packages, no Docker/image/cloud claim."""

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HELPER = ROOT / "agents/backend/neutral-r30-cas/escalation_readback.py"


def test_source_free_environment_cannot_be_ready(tmp_path):
    environment = {key: value for key, value in os.environ.items() if key != "PYTHONPATH"}
    result = subprocess.run(
        [sys.executable, "-B", str(HELPER), "--check-runtime-only"],
        cwd=tmp_path,
        env=environment,
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "OFFICIAL_BACKEND_T44_RUNTIME_REQUIRED_NOT_READY" in result.stderr
    assert not result.stdout.strip()
    assert not list(tmp_path.iterdir())


def test_local_project_runtime_resolves_real_validator_and_rules_only(tmp_path):
    environment = dict(os.environ, PYTHONPATH=str(ROOT / "backend"))
    result = subprocess.run(
        [sys.executable, "-B", str(HELPER), "--check-runtime-only"],
        cwd=tmp_path,
        env=environment,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    receipt = json.loads(result.stdout)
    assert receipt["scope"] == "PACKAGE_RESOLUTION_ONLY_NOT_IMAGE_OR_CLOUD_READINESS"
    assert (
        receipt["required_backend_config"]
        == "sha256:8e3e2a9d1f2d4706072eb0502b041d3db49d32b7a2fc48ac6b39fc2162336845"
    )
    assert receipt["actual_image_identity_verified_by_probe"] is False
    for name, module in (
        ("violations", "t44.contracts"),
        ("load_rules", "t44.scheduling.rules"),
        ("select_window", "t44.scheduling.rules"),
    ):
        function = receipt["resolved_functions"][name]
        assert function["module"] == module
        assert Path(function["file"]).resolve().is_relative_to((ROOT / "backend/t44").resolve())
    assert receipt["frozen_rule_schema_valid"] is True
    assert receipt["invalid_task_rejected"] is True
    assert receipt["rule_version"] == 1
    assert not list(tmp_path.iterdir())


def test_production_python_file_set_exactly_matches_manifest():
    directory = HELPER.parent
    manifest = json.loads((directory / "code-manifest.PUBLIC.json").read_bytes())
    declared = {name for name in manifest["files"] if name.endswith(".py")}
    actual = {path.name for path in directory.glob("*.py")}
    assert actual == declared
    assert "verify-local.py" not in actual
    assert len(manifest["files"]) == 18
