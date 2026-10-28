"""Separate diagnostic profile boundaries; no live factory/Docker/DB or packet access."""

import copy
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def module():
    spec = importlib.util.spec_from_file_location(
        "diagnostic_overlay", ROOT / "deployment/cloud-reuse/diagnostic-overlay.py"
    )
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def base():
    return {
        "database": "t44c_synthetic_p",
        "project": "t44-cloud-synthetic-p",
        "image_ids": {"backend": "sha256:" + "1" * 64},
        "config_ids": {"backend": "sha256:" + "2" * 64},
    }


def compose():
    return {
        "services": {
            "api": {
                "command": [
                    "python",
                    "-m",
                    "uvicorn",
                    "t44.api:app",
                    "--host",
                    "0.0.0.0",
                    "--port",
                    "8000",
                    "--workers",
                    "7",
                ],
                "environment": {
                    "PYTHONPATH": "/app/backend",
                    "DATABASE_URL": "synthetic-original-selector",
                },
            }
        }
    }


def test_explicit_diag_env_only_has_gate_selectors_no_password_or_DSN():
    m = module()
    env = m.diagnostic_env(base(), {"MYSQL_USER": "t44c_synthetic_p_app"}, "all")
    assert len(env) == 10 and all(key.startswith("T44_DIAG_") for key in env)
    assert env["T44_DIAG_HOST"] == "mysql" and env["T44_DIAG_PORT"] == "3306"
    assert (
        env["T44_DIAG_LIMIT"] == "10000"
        and env["T44_DIAG_MODULE_SHA256"] == m.TOOLS["810_stage.py"]
    )
    assert not any("PASSWORD" in key or "DATABASE_URL" == key for key in env)


def test_overlay_preserves_original_command_ENV_and_same_workers(tmp_path):
    m = module()
    old = compose()
    before = copy.deepcopy(old)
    env = m.diagnostic_env(base(), {"MYSQL_USER": "t44c_synthetic_p_app"}, "all")
    overlay = m.render_overlay(old, env, tmp_path)
    api = overlay["services"]["api"]
    assert old == before
    assert api["command"][3:5] == ["810_stage:app_factory", "--factory"]
    assert api["command"][api["command"].index("--workers") + 1] == "7"
    assert api["environment"]["PYTHONPATH"] == "/app/backend:/opt/t44-diagnostic"
    assert (
        "DATABASE_URL" not in api["environment"]
        and "T44_DATABASE" not in api["environment"]
    )
    assert len(api["volumes"]) == 2 and api["volumes"][0]["read_only"]
    assert api["labels"]["io.t44.diagnostic.production-entrypoint"] == "false"


def test_instrumented_preimage_is_not_silently_reinstrumented(tmp_path):
    m = module()
    old = compose()
    old["services"]["api"]["command"][3] = "other:factory"
    with pytest.raises(ValueError, match="UNINSTRUMENTED"):
        m.render_overlay(old, {}, tmp_path)


@pytest.mark.parametrize("wrong", [False, True])
def test_exact_API_identity_before_source935_diagnostic_stop(monkeypatch, wrong):
    m = module()
    b = base()
    overlay = m.render_overlay(compose(), {}, Path("/synthetic/new"))
    argv = ["synthetic-compose"]
    labels = {
        "com.docker.compose.project": b["project"],
        "com.docker.compose.service": "api",
        "io.t44.diagnostic.stage-sha256": m.TOOLS["810_stage.py"],
    }

    def command(args):
        if "inspect" not in args:
            return ("a" * 64 + "\n").encode()
        image = "sha256:" + "9" * 64 if wrong else b["image_ids"]["backend"]
        return (
            "\t".join(
                json.dumps(x)
                for x in [
                    "a" * 64,
                    image,
                    labels,
                    overlay["services"]["api"]["command"],
                    True,
                ]
            )
            + "\n"
        ).encode()

    monkeypatch.setattr(m, "command", command)
    if wrong:
        with pytest.raises(ValueError, match="IMAGE_COMMAND_OR_LABELS"):
            m.api_identity(argv, b, overlay)
    else:
        assert m.api_identity(argv, b, overlay)["production_entrypoint"] is False
