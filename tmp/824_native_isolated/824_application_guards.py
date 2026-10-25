"""Final-source launcher synthetic boundaries; no real accounts or service calls."""

import importlib.util
import os
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("isolated_app_guard", ROOT / "deployment/native/isolated-application.py")
APP = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(APP)


@pytest.fixture
def env():
    return {
        "DATABASE_URL": "mysql+pymysql://t44_i829_20261025:synthetic@127.0.0.1:13306/t44_i829_20261025",
        "T44_DATABASE": "t44_i829_20261025",
        "T44_SESSION_TTL_SECONDS": "3600",
    }


@pytest.mark.parametrize(
    "before,after",
    [
        ("127.0.0.1", "localhost"),
        ("13306", "3306"),
        ("mysql+pymysql", "sqlite"),
        ("/t44_i829_20261025", "/old_database"),
        ("//t44_i829_20261025:", "//root:"),
        ("synthetic@", "@"),
        ("/t44_i829_20261025", "/t44_i829_20261025?charset=utf8"),
    ],
)
def test_unknown_db_destination_or_admin_account_rejected(env, before, after):
    env["DATABASE_URL"] = env["DATABASE_URL"].replace(before, after)
    with pytest.raises(ValueError):
        APP.database_env(env)


def test_explicit_new_database_environment_is_copied(env):
    result = APP.database_env(env)
    assert result == env and result is not env
    env["T44_DATABASE"] = "old_database"
    with pytest.raises(ValueError):
        APP.database_env(env)


@pytest.mark.parametrize("expiry", ["2026-10-25T07:00:59Z", "2026-10-25T06:59:59Z", "2026-10-25T07:10:00+00:00"])
def test_token_near_expiry_and_noncanonical_utc_refused(expiry):
    with pytest.raises(ValueError):
        APP.token_window(expiry, now=1792911600)


def test_registered_child_identity_reuse_does_not_grant_signal():
    record = {"pid": 20, "uid": os.getuid(), "started": "old", "pgid": 19, "command_sha256": "a"}
    assert APP.child_match(record, record)
    assert not APP.child_match(record, record | {"started": "reused"})
    assert not APP.child_match(record, record | {"pgid": 1})
    assert not APP.child_match(record, None)
