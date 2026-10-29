"""Pure exact-profile guards; no SUT, process, appenv or independent-case access."""

import importlib.util
import types
from datetime import UTC, datetime
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]


def helper():
    spec = importlib.util.spec_from_file_location(
        "campaign8_guard", ROOT / "deployment/native/campaign-eight.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize(
    "profile,api,stop,force,schema",
    [
        ("functional", 18098, "11:22:00", "11:25:00", "t44_f816_20261025"),
        ("performance", 18099, "11:32:00", "11:35:00", "t44_p816_20261025"),
    ],
)
def test_exact_new_profile(tmp_path, profile, api, stop, force, schema):
    tmp_path.chmod(0o700)
    h = helper()
    output = tmp_path / "new"
    h.materialize(ROOT, profile, output)
    old = {
        p.name: p.read_bytes()
        for p in (output / "previous-campaign-basis").glob("*.py")
    }
    new, receipts = h.derive(profile, old)
    for name, raw in new.items():
        text = raw.decode()
        for change in reversed(receipts[name]["allowed_changes"]):
            text = text.replace(change["new"], change["old"])
        assert text.encode() == old[name]
    policy = types.ModuleType("new_policy")
    exec(compile(new["isolated.py"], "generated.py", "exec"), policy.__dict__)  # noqa: S102 - pinned generated policy; never call its main
    assert policy.SOURCE == h.SOURCE
    assert policy.PORTS["api"] == api
    assert datetime.fromtimestamp(policy.STOP, UTC).strftime("%H:%M:%S") == stop
    assert datetime.fromtimestamp(policy.HARD_STOP, UTC).strftime("%H:%M:%S") == force
    policy.admitted(datetime(2026, 10, 25, 10, 49, 59, tzinfo=UTC).timestamp())
    with pytest.raises(ValueError):
        policy.admitted(datetime(2026, 10, 25, 10, 50, tzinfo=UTC).timestamp())
    assert schema.encode() in new["isolated-application.py"]
    assert b"module.STOP - 90" in new["isolated-application.py"]
    assert b"provisioned" in new["scheduler-control.py"]
    if profile == "performance":
        metrics = types.ModuleType("new_metrics")
        exec(  # noqa: S102 - pinned generated sampler; never call its main
            compile(new["interval-metrics.py"], "generated.py", "exec"),
            metrics.__dict__,
        )
        assert (
            datetime.fromtimestamp(metrics.END, UTC).strftime("%H:%M:%S") == "11:29:00"
        )


def test_unknown_profile_rejected():
    with pytest.raises(ValueError):
        helper().derive("other", {})


def test_changed_source_rejected(tmp_path):
    tmp_path.chmod(0o700)
    h = helper()
    output = tmp_path / "new"
    h.materialize(ROOT, "functional", output)
    old = {
        p.name: p.read_bytes()
        for p in (output / "previous-campaign-basis").glob("*.py")
    }
    old["isolated.py"] = old["isolated.py"].replace(h.OLD_SOURCE.encode(), b"0" * 40)
    with pytest.raises(ValueError, match="PATCH_POSITION"):
        h.derive("functional", old)
