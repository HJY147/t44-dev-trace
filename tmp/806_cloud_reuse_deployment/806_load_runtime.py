"""Tool-runtime copy/identity/ENV isolation guards; no Docker or business environment access."""

import copy
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def module():
    spec = importlib.util.spec_from_file_location(
        "load_runtime", ROOT / "deployment/cloud-reuse/load-runtime.py"
    )
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def image():
    return {
        "Id": "sha256:" + "a" * 64,
        "Os": "linux",
        "Architecture": "amd64",
        "Config": {
            "User": "10001:10001",
            "WorkingDir": "/diagnostic",
            "Env": ["PYTHONPATH=", "PYTHONUNBUFFERED=1"],
            "Labels": {"kind": "synthetic-only"},
        },
    }


def test_final_stage_only_copies_dependencies_and_not_SUT():
    m = module()
    text = m.dockerfile().decode()
    lines = text.splitlines()
    assert [line for line in lines if line.startswith("FROM ")] == [
        "FROM " + m.BACKEND + " AS dependencies",
        "FROM " + m.PYTHON + " AS tool",
    ]
    assert [line for line in lines if line.startswith("COPY ")] == [
        "COPY --from=dependencies /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages"
    ]
    assert not any(line.startswith("RUN ") for line in lines)
    assert (
        "pip install" not in text
        and "/app/backend" not in text
        and "/app/specs" not in text
    )
    assert 'ENV PYTHONPATH=""' in text and "USER 10001:10001" in text


def test_only_exact_expected_tool_runtime_image_configuration_accepted(monkeypatch):
    m = module()
    v = image()
    monkeypatch.setattr(m, "command", lambda *a: json.dumps([v]).encode())
    assert (
        m.inspect_tool("fixed-derived:run", {"kind": "synthetic-only"})["Id"] == v["Id"]
    )


@pytest.mark.parametrize("change", ["user", "appenv", "pythonpath", "labels"])
def test_wrong_user_or_SUT_environment_or_labels_rejected(monkeypatch, change):
    m = module()
    v = copy.deepcopy(image())
    if change == "user":
        v["Config"]["User"] = "0:0"
    elif change == "appenv":
        v["Config"]["Env"].append("DATABASE_URL=synthetic-forbidden-value")
    elif change == "pythonpath":
        v["Config"]["Env"] = ["PYTHONPATH=/app/backend"]
    else:
        v["Config"]["Labels"]["extra"] = "unauthorized"
    monkeypatch.setattr(m, "command", lambda *a: json.dumps([v]).encode())
    with pytest.raises(ValueError, match="RUNTIME_USER_ENV_LABELS"):
        m.inspect_tool("fixed-derived:run", {"kind": "synthetic-only"})


def test_modified_binding_refuses_before_Docker(tmp_path, monkeypatch):
    m = module()
    p = tmp_path / "runtime-binding.json"
    p.write_text("{}")
    p.chmod(0o600)
    monkeypatch.setattr(
        m, "command", lambda *a: pytest.fail("untrustedbinding reached Docker")
    )
    with pytest.raises(ValueError, match="BINDING_SHA"):
        m.verify_binding(p, "0" * 64, tmp_path / "not-read-proof.py")
