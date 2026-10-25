"""Explicit campaign policy guards; no process, env, SUT or independent-case access."""

import importlib.util
import subprocess
import types
from datetime import UTC, datetime
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]


def load(name):
    spec = importlib.util.spec_from_file_location(
        "campaign_guard_" + name.replace("-", "_"), ROOT / "deployment/native" / (name + ".py")
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def basis(profile):
    helper = load("profile-prepare")
    raw = {
        n: subprocess.run(
            ["git", "show", helper.BASE + ":deployment/native/" + n], cwd=ROOT, check=True, capture_output=True
        ).stdout
        for n in helper.PINS
    }
    old, _ = helper.render(profile, raw)
    if profile == "functional":
        return load("functional-seven").derive(old)[0]
    old = load("worker-seven").derive(old)[0]
    old = load("round-two").derive(old)[0]
    r3 = load("round-three")
    old["interval-metrics.py"] = subprocess.run(
        ["git", "show", r3.METRICS_COMMIT + ":deployment/native/interval-metrics.py"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    ).stdout
    return r3.derive(old)[0]


@pytest.mark.parametrize(
    "profile,stop,force,db",
    [
        ("functional", "10:22:00", "10:25:00", "t44_f817_20261025"),
        ("performance", "10:32:00", "10:35:00", "t44_p829c_20261025"),
    ],
)
def test_exact_campaign_restores_previous_bytes_and_keeps_schema(profile, stop, force, db):
    old = basis(profile)
    new, receipts = load("campaign-prepare").derive(profile, old)
    for name, data in new.items():
        text = data.decode()
        for item in reversed(receipts[name]["allowed_changes"]):
            text = text.replace(item["new"], item["old"])
        assert text.encode() == old[name]
    policy = types.ModuleType("campaign_policy")
    exec(compile(new["isolated.py"], "derived.py", "exec"), policy.__dict__)
    assert datetime.fromtimestamp(policy.STOP, UTC).strftime("%H:%M:%S") == stop
    assert datetime.fromtimestamp(policy.HARD_STOP, UTC).strftime("%H:%M:%S") == force
    policy.admitted(datetime(2026, 10, 25, 9, 59, 59, tzinfo=UTC).timestamp())
    with pytest.raises(ValueError):
        policy.admitted(datetime(2026, 10, 25, 10, 0, tzinfo=UTC).timestamp())
    assert db.encode() in new["isolated-application.py"]
    assert b"module.STOP - 90" in new["isolated-application.py"]
    if profile == "performance":
        sampler = types.ModuleType("campaign_metrics")
        exec(compile(new["interval-metrics.py"], "derived.py", "exec"), sampler.__dict__)
        assert datetime.fromtimestamp(sampler.END, UTC).strftime("%H:%M:%S") == "10:29:00"


def test_unknown_profile_rejected():
    with pytest.raises(ValueError):
        load("campaign-prepare").derive("other", {})


def test_changed_old_deadline_rejected_not_silently_extended():
    old = basis("functional")
    old["isolated.py"] = old["isolated.py"].replace(b"9, 24, tzinfo=UTC", b"9, 26, tzinfo=UTC")
    with pytest.raises(ValueError, match="PATCH_POSITION"):
        load("campaign-prepare").derive("functional", old)
