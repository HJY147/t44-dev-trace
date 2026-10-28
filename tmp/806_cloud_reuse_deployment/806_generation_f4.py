"""New generation source/scope/stop/entry guards, without Docker or product imports."""

import copy
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[2]


def load(name):
    spec = importlib.util.spec_from_file_location(
        name.replace("-", "_"), ROOT / "deployment/cloud-reuse" / name
    )
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_all_temporary_paths_explicit_and_original_ssl_bits_preserved():
    lib = load("app-campaign.py")
    m = load("generation-f4.py")
    old = lib.nginx()
    new = m.nginx(lib)
    assert "client_body_temp_path /tmp/client_temp;" in new
    for name in ["proxy", "fastcgi", "uwsgi", "scgi"]:
        assert f"{name}_temp_path /tmp/{name}_temp;" in new
    for name in ["fastcgi", "uwsgi", "scgi"]:
        new = new.replace(f"  {name}_temp_path /tmp/{name}_temp;\n", "")
    assert new == old


def rows():
    return [
        {
            "path": f"backend/t44/fixture{i:02d}.py",
            "bytes": 1,
            "sha256": "a" * 64,
            "mode": 0o644,
        }
        for i in range(53)
    ]


def test_complete_nonroot_53_files_requires_exact_dependency_and_product_set():
    m = load("generation-f4.py")
    expected = rows()
    assert (
        m.exact53(
            {"files": expected, "uid": 10001, "business_env_absent": True}, expected
        )["files"]
        == 53
    )


@pytest.mark.parametrize("change", ["extra", "missing", "mode", "bytes", "uid", "env"])
def test_wrong_actual_source_probe_rejected(change):
    m = load("generation-f4.py")
    expected = rows()
    probe = {
        "files": copy.deepcopy(expected),
        "uid": 10001,
        "business_env_absent": True,
    }
    if change == "extra":
        probe["files"].append({"path": "backend/t44/domain/commands.py"})
    elif change == "missing":
        probe["files"].pop()
    elif change in {"mode", "bytes"}:
        probe["files"][0][change] = 0
    elif change == "uid":
        probe["uid"] = 0
    else:
        probe["business_env_absent"] = False
    with pytest.raises(ValueError, match="COMPLETE_53"):
        m.exact53(probe, expected)


def test_fixed_21UTC_ceiling_and_real_future_window(monkeypatch):
    m = load("generation-f4.py")
    lib = load("app-campaign.py")
    monkeypatch.setattr(m.time, "time", lambda: lib.expiry("2026-10-25T15:00:00Z"))
    m.valid_window(lib, "2026-10-25T21:00:00Z")
    with pytest.raises(ValueError):
        m.valid_window(lib, "2026-10-25T21:00:01Z")
    with pytest.raises(ValueError):
        m.valid_window(lib, "2026-10-25T15:00:01Z")


def test_plain_product_entry_original_backend_and_no_database_host_port():
    lib = load("app-campaign.py")
    images = {
        role: {"alias": "fixed-new-" + role}
        for role in ["backend", "web", "mysql", "rabbitmq", "nginx"]
    }
    v = lib.compose_profile(images, Path("/new/phase"), "10.20.0.1", 19445, 18181, 7)
    api = v["services"]["api"]
    assert api["command"][3] == "t44.api:app"
    assert "810" not in json.dumps(v) and "--factory" not in api["command"]
    assert api["environment"]["PYTHONPATH"] == "/app/backend"
    assert (
        "--workers" in api["command"]
        and api["command"][api["command"].index("--workers") + 1] == "7"
    )
    assert not v["services"]["mysql"].get("ports") and not v["services"][
        "rabbitmq"
    ].get("ports")
    assert v["services"]["scheduler"]["volumes"][0].endswith(":/run/t44-secrets:ro")


def test_foreign_container_image_is_not_an_owned_scheduler():
    m = load("generation-f4.py")
    cid = "a" * 64

    def command(argv):
        if "ps" in argv:
            return cid.encode()
        return ('"' + cid + '"\t"sha256:foreign"\t{"Running":true}\t0').encode()

    lib = SimpleNamespace(command=command)
    value = {
        "project": "t44-cloud-r10newtest-p",
        "image_ids": {"backend": "sha256:good"},
        "config_ids": {"backend": "sha256:config"},
    }
    with pytest.raises(ValueError, match="IMAGE_IDENTITY"):
        m.live(lib, value, "scheduler")


@pytest.mark.parametrize("pin", [None, "", "0" * 63])
def test_unpinned_phase_refuses_before_reading_library(pin):
    with pytest.raises(ValueError, match="FROZEN_PHASE_BINDING_SHA"):
        load("generation-f4.py").phase_binding(Path("/does-not-exist"), pin)
