"""Fresh schema/window guards only; no env, independent, process or SUT access."""

import importlib.util
import subprocess
import types
from datetime import UTC, datetime
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]


def load(name):
    spec = importlib.util.spec_from_file_location(
        "guard_" + name.replace("-", "_"), ROOT / "deployment/native" / (name + ".py")
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def bases():
    profile = load("profile-prepare")
    original = {
        n: subprocess.run(
            ["git", "show", profile.BASE + ":deployment/native/" + n], cwd=ROOT, check=True, capture_output=True
        ).stdout
        for n in profile.PINS
    }
    functional, _ = profile.render("functional", original)
    perf, _ = profile.render("performance", original)
    w7, _ = load("worker-seven").derive(perf)
    r2, _ = load("round-two").derive(w7)
    r2["interval-metrics.py"] = subprocess.run(
        ["git", "show", load("round-three").METRICS_COMMIT + ":deployment/native/interval-metrics.py"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    ).stdout
    return functional, r2


def assert_restore(old, new, receipts):
    for name, data in new.items():
        text = data.decode()
        for item in reversed(receipts[name]["allowed_changes"]):
            text = text.replace(item["new"], item["old"])
        assert text.encode() == old[name]


def policy(data):
    value = types.ModuleType("pure_window_guard")
    exec(compile(data, "derived.py", "exec"), value.__dict__)
    return value


def test_round3_exact_schema_window_and_metrics_do_not_rewrite_round2(bases):
    old = bases[1]
    new, receipts = load("round-three").derive(old)
    assert_restore(old, new, receipts)
    p = policy(new["isolated.py"])
    assert datetime.fromtimestamp(p.STOP, UTC).isoformat() == "2026-10-25T09:42:00+00:00"
    assert datetime.fromtimestamp(p.HARD_STOP, UTC).isoformat() == "2026-10-25T09:45:00+00:00"
    with pytest.raises(ValueError):
        p.admitted(datetime(2026, 10, 25, 9, 20, tzinfo=UTC).timestamp())
    assert b"t44_p829c_20261025" in new["isolated-application.py"]
    assert b"t44_p829_20261025" not in new["isolated-application.py"]
    assert b"!= 7" in new["isolated-application.py"]
    metrics = policy(new["interval-metrics.py"])
    assert datetime.fromtimestamp(metrics.END, UTC).isoformat() == "2026-10-25T09:39:00+00:00"


def test_functional_v7_exact_empty_schema_and_window_are_separate(bases):
    old = bases[0]
    new, receipts = load("functional-seven").derive(old)
    assert_restore(old, new, receipts)
    p = policy(new["isolated.py"])
    assert datetime.fromtimestamp(p.STOP, UTC).isoformat() == "2026-10-25T09:24:00+00:00"
    assert datetime.fromtimestamp(p.HARD_STOP, UTC).isoformat() == "2026-10-25T09:25:00+00:00"
    assert b"t44_f817_20261025" in new["isolated-application.py"]
    assert b"!= 4" in new["isolated-application.py"]
    assert b"module.STOP - 90" in new["isolated-application.py"]


def test_round3_unknown_old_database_literal_is_refused(bases):
    old = dict(bases[1])
    old["isolated-application.py"] = old["isolated-application.py"].replace(b"t44_p829_20261025", b"unknown_db")
    with pytest.raises(ValueError, match="PATCH_POSITION"):
        load("round-three").derive(old)


def test_changed_metrics_template_is_refused(bases):
    old = dict(bases[1])
    old["interval-metrics.py"] += b"\n# changed"
    with pytest.raises(ValueError, match="METRICS_TEMPLATE"):
        load("round-three").derive(old)
