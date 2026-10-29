"""New-round policy guards only; no process, broker, database or independent access."""

import importlib.util
import subprocess
import types
from datetime import UTC, datetime
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]


def module(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / "deployment/native" / filename)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


@pytest.fixture(scope="module")
def basis():
    profile = module("r2_profile", "profile-prepare.py")
    old = {
        n: subprocess.run(
            ["git", "show", profile.BASE + ":deployment/native/" + n], cwd=ROOT, check=True, capture_output=True
        ).stdout
        for n in profile.PINS
    }
    w8, _ = profile.render("performance", old)
    w7, _ = module("r2_w7", "worker-seven.py").derive(w8)
    return w7


def test_round2_restores_exact_old_w7_and_separates_deadlines(basis):
    changed, receipts = module("r2_materializer", "round-two.py").derive(basis)
    for name, data in changed.items():
        restored = data.decode()
        for item in reversed(receipts[name]["allowed_changes"]):
            restored = restored.replace(item["new"], item["old"])
        assert restored.encode() == basis[name]
    policy = types.ModuleType("r2_policy")
    exec(compile(changed["isolated.py"], "derived.py", "exec"), policy.__dict__)
    assert datetime.fromtimestamp(policy.STOP, UTC).isoformat() == "2026-10-25T09:12:00+00:00"
    assert datetime.fromtimestamp(policy.HARD_STOP, UTC).isoformat() == "2026-10-25T09:15:00+00:00"
    assert b"module.STOP - 90" in changed["isolated-application.py"]
    assert b"!= 7" in changed["isolated-application.py"]
    assert b"2026-10-25T09:10:30Z" in changed["isolated-build.py"]
    assert b"native-performance-round2-20261025" in changed["isolated.py"]


@pytest.mark.parametrize("offset,allowed", [(-1, True), (0, False)])
def test_round2_first_start_fence_is_0900_not_broker_minus_two_minutes(basis, offset, allowed):
    changed, _ = module("r2_admission", "round-two.py").derive(basis)
    policy = types.ModuleType("r2_admission_policy")
    exec(compile(changed["isolated.py"], "derived.py", "exec"), policy.__dict__)
    now = datetime(2026, 10, 25, 9, 0, tzinfo=UTC).timestamp() + offset
    if allowed:
        policy.admitted(now)
    else:
        with pytest.raises(ValueError, match="WINDOW"):
            policy.admitted(now)


def test_changed_old_time_refused_instead_of_silent_override(basis):
    old = dict(basis)
    old["isolated.py"] = old["isolated.py"].replace(b"8, 50, tzinfo=UTC", b"8, 51, tzinfo=UTC")
    with pytest.raises(ValueError, match="PATCH_POSITION"):
        module("r2_counterexample", "round-two.py").derive(old)
