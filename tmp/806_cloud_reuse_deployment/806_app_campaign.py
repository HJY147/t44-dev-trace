"""Pure phase security and immutable hard-stop boundary guards; no Docker/systemd/certs/cloud."""

import importlib.util
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def module():
    spec = importlib.util.spec_from_file_location(
        "app_campaign", ROOT / "deployment/cloud-reuse/app-campaign.py"
    )
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


@pytest.mark.parametrize("workers,maxconn", [(4, 128), (7, 384), (16, 384)])
def test_explicit_seven_services_private_ports_credentials_and_connection_budget(
    tmp_path, workers, maxconn
):
    m = module()
    images = {
        role: {"alias": "synthetic-" + role + ":checked"}
        for role in ["backend", "web", "mysql", "rabbitmq", "nginx"]
    }
    value = m.compose_profile(images, tmp_path, "10.1.1.2", 18443, 18080, workers)
    services = value["services"]
    assert {name for name, row in services.items() if not row.get("profiles")} == set(
        m.PERSISTENT
    )
    assert all(
        "ports" not in services[name]
        for name in ["mysql", "rabbitmq", "api", "consumer", "scheduler"]
    )
    assert services["web"]["ports"] == ["127.0.0.1:18080:8080"]
    assert services["tls-gateway"]["ports"] == ["10.1.1.2:18443:8443"]
    assert all("ca.key" not in item for item in services["tls-gateway"]["volumes"])
    assert "--max-connections=" + str(maxconn) in services["mysql"]["command"]
    assert maxconn >= 15 * (workers + 4)
    assert services["api"]["command"][
        services["api"]["command"].index("--workers") + 1
    ] == str(workers)
    assert "T44_SCHEDULER_TOKEN_FILE" not in services["api"]["environment"]
    assert value["networks"]["data"]["internal"]
    assert "13306" not in json.dumps(value)


def binding_fixture(tmp_path, m):
    tmp_path.chmod(0o700)
    for name in ["controller.py", "compose.json", "application.env", "nginx.conf"]:
        p = tmp_path / name
        p.write_text("synthetic")
        p.chmod(0o600)
    v = {
        "kind": "isolated-cloud-campaign",
        "project": "t44-cloud-example1-p",
        "stop_utc": (datetime.now(UTC) + timedelta(seconds=300)).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        ),
        "service_unit": "t44-cloud-example1-p-stop.service",
        "timer_unit": "t44-cloud-example1-p-stop.timer",
        "file_hashes": {
            name: m.sha(tmp_path / name)
            for name in [
                "controller.py",
                "compose.json",
                "application.env",
                "nginx.conf",
            ]
        },
    }
    p = tmp_path / "binding.json"
    p.write_text(json.dumps(v))
    p.chmod(0o600)
    return v


def test_mutable_env_cannot_disable_frozen_owned_stop_but_blocks_new_start(tmp_path):
    m = module()
    binding_fixture(tmp_path, m)
    frozen = m.sha(tmp_path / "binding.json")
    (tmp_path / "application.env").write_text("changed root env")
    assert (
        m.binding(tmp_path, stopping=True, expected=frozen)["project"]
        == "t44-cloud-example1-p"
    )
    with pytest.raises(ValueError, match="CONFIG_OR_CONTROLLER"):
        m.binding(tmp_path)


def test_changed_frozen_stop_plan_refused(tmp_path):
    m = module()
    binding_fixture(tmp_path, m)
    frozen = m.sha(tmp_path / "binding.json")
    p = tmp_path / "binding.json"
    v = json.loads(p.read_text())
    v["project"] = "t44-cloud-otherxx-p"
    p.write_text(json.dumps(v))
    with pytest.raises(ValueError, match="FROZEN_STOP_BINDING"):
        m.binding(tmp_path, stopping=True, expected=frozen)


def test_persistent_timer_binds_exact_frozen_controller_plan_and_never_VM(
    tmp_path, monkeypatch
):
    m = module()
    v = binding_fixture(tmp_path, m)
    writes = {}
    monkeypatch.setattr(
        m, "write", lambda path, data: writes.setdefault(path.name, data.decode())
    )
    monkeypatch.setattr(Path, "chmod", lambda *a: None)
    calls = []
    monkeypatch.setattr(
        m, "command", lambda argv, *a, **k: calls.append(list(map(str, argv))) or b""
    )
    monkeypatch.setattr(m, "receipt", lambda *a, **k: k)
    assert m.arm(tmp_path, v)["success"]
    assert "Persistent=true" in writes[v["timer_unit"]]
    assert " UTC" in writes[v["timer_unit"]]
    assert (
        "--binding-sha256 " + m.sha(tmp_path / "binding.json")
        in writes[v["service_unit"]]
    )
    assert not any(
        any(word in ["poweroff", "reboot", "halt"] for word in call) for call in calls
    )
