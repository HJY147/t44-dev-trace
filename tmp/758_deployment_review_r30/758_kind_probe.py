"""Offline reviewer reproduction; no Docker/cloud/business/credential calls."""

import hashlib
import importlib.util
import json
import os
import sys
import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
CANDIDATE = HERE.parents[2] / "deployment-preparation-r30"
PACKAGE = CANDIDATE / "tmp/761_deployment_preparation_r30/official-artifact-12880320744"
BUNDLE = "b2db2e1c5cf56fa5df4f20f7003d44d6b3b9ab4cd484b45d921c82640295d345"


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


adapter = module(CANDIDATE / "deployment/cloud-reuse/r30-window.py", "review_r30")
with tempfile.TemporaryDirectory(dir=HERE) as scratch:
    profile = Path(scratch) / "profile"
    args = SimpleNamespace(package=PACKAGE, manifest_sha256=BUNDLE, run_id="r30review01",
                           stop_utc=(datetime.now(UTC) + timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                           output=profile)
    result = adapter.derive(args)
    generation = module(profile / "generation.py", "review_r30_generation")
    budget = module(profile / "mysql-budget.py", "review_r30_budget")
    phase = Path(scratch) / "phase"
    phase.mkdir(mode=0o700)
    raw = json.dumps({"generation_kind": adapter.KIND}).encode()
    (phase / "binding.json").write_bytes(raw)
    (phase / "binding.json").chmod(0o600)
    expected = hashlib.sha256(raw).hexdigest()
    try:
        budget.checked_binding(phase, expected)
    except ValueError as error:
        rejection = str(error)
    else:
        raise AssertionError("R30 kind unexpectedly accepted")
    assert rejection == "V4_ONLY_NO_OLD_CAMPAIGN_ADOPTION"
    assert adapter.KIND != budget.KIND
    assert '"generation_kind": "' + adapter.KIND + '"' in (profile / "generation.py").read_text()
    record = dict(finding="R30-BUDGET-KIND-01",priority="P1",adapter_kind=adapter.KIND,
                  budget_kind=budget.KIND,rejection=rejection,
                  actual_derived_budget_sha256=result["inherited_budget_sha256"],
                  generated_kind_binding_statement_present=True,
                  fixture="Synthetic minimal public generation_kind binding; no credentials or service state",
                  docker_or_cloud_or_service_or_session_calls=False)
    (HERE / "kind-probe.json").write_text(json.dumps(record,indent=2)+"\n")
    print(json.dumps(record))
