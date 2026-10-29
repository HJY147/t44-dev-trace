"""No-network checks of production/private target rejection."""

import importlib.util
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location(
    "lock_admission", Path(__file__).with_name("825_admission.py")
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def environment():
    return {
        "CI": "true",
        "GITHUB_REPOSITORY": "HJY147/t44-dev-trace",
        "GITHUB_REF": "refs/heads/codex/lock-diagnostics-20261025",
        "T44_DATABASE": "t44_diagnostics",
        "DATABASE_URL": "mysql+pymysql://t44:diag-app-disposable@127.0.0.1:3306/t44_diagnostics",
    }


@pytest.mark.parametrize(
    "key,value",
    [
        ("CI", "false"),
        ("GITHUB_REPOSITORY", "other/repo"),
        ("GITHUB_REF", "refs/heads/main"),
        ("T44_DATABASE", "t44_dev"),
        ("DATABASE_URL", "mysql+pymysql://t44:x@127.0.0.1:13306/t44_diagnostics"),
        ("DATABASE_URL", "mysql+pymysql://t44:x@example.com:3306/t44_diagnostics"),
    ],
)
def test_reject_private_or_unadmitted_target(key, value):
    env = environment()
    env[key] = value
    with pytest.raises(ValueError):
        module.require_environment("candidate", env)


def test_unknown_mode_rejected():
    with pytest.raises(ValueError):
        module.require_environment("production", environment())


def test_http_cannot_reuse_low_level_schema():
    with pytest.raises(ValueError):
        module.require_environment("http", environment())
