"""Review exact 2ca7 fix through real derived binding/flock/probe to a nonnetwork sentinel."""

import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2] / "deployment-preparation-r30"
TARGET = "2ca7fd377b7ad0bbe37ff9aea8924825b092a803"
ADAPTER = "f2f850b5e17bd688811413ac535d36c0345ec9a0472df18dc22b65e758342896"
NEW_BUDGET = "9e98632fa1885bf4327b04a95daeba5cee4ad909b536e91ac8b11a1e58488a61"
OLD_BUDGET = "305f9eaeea96b0ef882ec17a457f51852bafc8c34b5fe2e47056bd12625dd82d"
old_kind = "exact-pinned-production-entry-generation-v4"
real_run = subprocess.run


def only_git(argv, *args, **kwargs):
    assert str(argv[0]) == "git", "No service/network subprocess permitted"
    return real_run(argv, *args, **kwargs)


subprocess.run = only_git


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


adapter_path = ROOT / "deployment/cloud-reuse/r30-window.py"
assert hashlib.sha256(adapter_path.read_bytes()).hexdigest() == ADAPTER
assert adapter_path.read_bytes() == subprocess.check_output(["git", "show", TARGET + ":deployment/cloud-reuse/r30-window.py"])
m = load(adapter_path, "review_r30_fixed")
with tempfile.TemporaryDirectory(dir=HERE) as scratch:
    base = Path(scratch)
    profile = base / "profile"
    stop = (datetime.now(UTC) + timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M:%SZ")
    metadata = m.derive(SimpleNamespace(package=ROOT / "tmp/761_deployment_preparation_r30/official-artifact-12880320744", manifest_sha256="b2db2e1c5cf56fa5df4f20f7003d44d6b3b9ab4cd484b45d921c82640295d345", run_id="r30fixcheck", stop_utc=stop, output=profile))
    a = m.artifact()
    g = load(profile / "generation.py", "review_r30_fixed_generation")
    budget = g.budget_module()
    original = ROOT / "deployment/cloud-reuse/v4/mysql-budget.py"
    assert a.sha(original) == OLD_BUDGET
    assert (profile / "mysql-budget.py").read_text() == original.read_text().replace('KIND = "' + old_kind + '"', 'KIND = "' + m.KIND + '"')
    assert a.sha(profile / "mysql-budget.py") == g.BUDGET_SHA == NEW_BUDGET
    assert g.R30_ADAPTER_SHA == ADAPTER
    assert metadata["derived_budget_sha256"] == NEW_BUDGET and metadata["original_budget_sha256"] == OLD_BUDGET
    generation_hash = a.sha(profile / "generation.py")
    assert generation_hash in (profile / "resource-stream.py").read_text()
    for name, declared in metadata["derived_files"].items():
        assert a.sha(profile / name) == declared["sha256"]
    phase = base / "phase"
    phase.mkdir(mode=0o700)
    (phase / "receipts").mkdir(mode=0o700)
    a.write(phase / "mysql-budget.py", (profile / "mysql-budget.py").read_bytes())
    binding = dict(generation_kind=m.KIND, source_sha=a.SOURCE, stop_utc=stop,
                   phase="p", api_workers=64, v4_pool_plan=budget.pool_plan("p",64,5,0),
                   project="t44-cloud-r30fixcheck-p",database="t44c_r30fixcheck_p",
                   timer_unit="synthetic-r30-stop.timer")
    a.save(phase / "binding.json", binding)
    expected = a.sha(phase / "binding.json")
    assert budget.checked_binding(phase, expected) == binding
    with budget.operation_lock(phase, expected, timeout_seconds=0) as descriptor:
        assert descriptor >= 0 and (phase / ".v4-operation.lock").is_file()
    commands, live_roles = [], []

    class NoNetworkBoundary(RuntimeError):
        pass

    def sentinel(_lib, _value, role):
        live_roles.append(role)
        raise NoNetworkBoundary("actual probe reached mysql live sentinel")

    def command(argv):
        assert argv == ["systemctl", "is-active", "--quiet", binding["timer_unit"]]
        commands.append(argv)
        return b""

    factory = load(profile / "factory.py", "review_fixed_factory")
    lib = SimpleNamespace(expiry=factory.expiry, command=command)
    args = SimpleNamespace(action="probe-budget",phase_dir=phase,binding_sha256=expected)
    with patch.object(g,"phase_binding",return_value=(lib,binding)), patch.object(g,"live",side_effect=sentinel):
        try:
            g.operate(args)
        except NoNetworkBoundary:
            pass
        else:
            raise AssertionError("probe did not reach expected boundary")
    assert live_roles == ["mysql"] and len(commands) == 1
    (phase / "binding.json").unlink()
    a.save(phase / "binding.json", {**binding,"generation_kind":old_kind})
    try:
        budget.checked_binding(phase,a.sha(phase / "binding.json"))
    except ValueError as error:
        old_rejection = str(error)
    else:
        raise AssertionError("old v4 binding accepted")
    assert old_rejection == "V4_ONLY_NO_OLD_CAMPAIGN_ADOPTION"
    record = dict(target=TARGET,P1="R30-BUDGET-KIND-01",status="CLOSED_IN_EXACT_CODE_SCOPE",
                  adapter_sha256=ADAPTER,original_budget_sha256=OLD_BUDGET,derived_budget_sha256=NEW_BUDGET,
                  budget_only_one_kind_literal_changed=True,new_binding_accepted=True,
                  real_operation_flock_entered=True,GEN_probe_reached_nonnetwork_mysql_live=live_roles,
                  systemctl_command_was_stubbed=True,phase_binding_outer_wrapper_stubbed=True,
                  old_kind_rejected=old_rejection,resource_generation_and_profile_SHA_chain_verified=True,
                  actual_budget_SQL_or_cloud_or_Docker_or_service_or_session=False)
    (HERE / "budget-fix-review.json").write_text(json.dumps(record,indent=2)+"\n")
    print(json.dumps(record))
