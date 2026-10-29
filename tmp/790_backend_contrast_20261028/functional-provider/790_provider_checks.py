"""Public development checks: real CLI/Runtime on own SQLite, natural 60-second expiry."""

import ast
import contextlib
import importlib.util
import io
import json
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from t44 import cli, persistence
from t44.persistence.schema import TABLES, metadata
from t44.settings import Settings

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    "provider790", HERE / "790_provider_core.py"
)
core = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core)
UTC = timezone.utc  # noqa: UP017 -- host parser compatibility.


@pytest.fixture(scope="module")
def world(tmp_path_factory):
    assert "product-source" in cli.__file__
    monkeypatch = pytest.MonkeyPatch()
    directory = tmp_path_factory.mktemp("neutral-provider-local-only")
    engine = create_engine("sqlite:///" + str(directory / "synthetic.sqlite"))
    metadata.create_all(engine)
    settings = Settings(
        database_url="mysql+pymysql://synthetic:local@mysql:3306/" + core.F_DATABASE
    )
    monkeypatch.setenv("DATABASE_URL", settings.database_url)
    monkeypatch.setenv("T44_DATABASE", core.F_DATABASE)
    monkeypatch.setenv("T44_SESSION_TTL_SECONDS", "3600")
    monkeypatch.setattr(cli, "create_mysql_engine", lambda _s: engine)
    factory = persistence.SqlAlchemyUnitOfWorkFactory(engine)
    calls = []

    def actual_cli(argv, secret_stdin, timeout):
        assert timeout > 0
        calls.append(argv)
        stdout, stderr = io.StringIO(), io.StringIO()
        monkeypatch.setattr(sys, "stdin", io.StringIO(secret_stdin.decode()))
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            status = cli.main(argv)
        assert status == 0
        assert "password" not in stdout.getvalue()
        return json.loads(stdout.getvalue())

    stop = datetime.now(UTC) + timedelta(seconds=180)
    accounts = core.create_five(
        factory, settings, prefix="synthetic790f", stop=stop, cli=actual_cli
    )
    # Sign the short legitimate session first, then use wall time while other checks execute.
    short = core.issue(factory, settings, accounts["x"], ttl=60, stop=stop)
    valid = {
        label: core.issue(factory, settings, account, ttl=3600, stop=stop)
        for label, account in accounts.items()
    }
    revocable = core.issue(factory, settings, accounts["m"], ttl=3600, stop=stop)
    try:
        yield (
            factory,
            settings,
            stop,
            actual_cli,
            accounts,
            short,
            valid,
            revocable,
            calls,
        )
    finally:
        monkeypatch.undo()
        engine.dispose()


def test_five_original_cli_users_no_seed(world):
    factory, _, _, _, accounts, _, _, _, calls = world
    assert set(accounts) == {"m", "d", "d2", "r", "x"}
    assert len({row["user_id"] for row in accounts.values()}) == 5
    assert [argv[0] for argv in calls[:5]] == ["init-user"] * 5
    with factory() as uow:
        counts = {name: uow.gateway.count(name) for name in TABLES}
    assert counts["users"] == 5 and counts["auth_sessions"] == 7
    assert counts["audit_events"] == 7
    assert all(
        value == 0
        for name, value in counts.items()
        if name not in {"users", "auth_sessions", "audit_events"}
    )


def test_five_normal_ttl_tokens_are_distinct_and_valid(world):
    factory, settings, stop, _, _, short, valid, revocable, _ = world
    tokens = [row["access_token"] for row in valid.values()] + [
        short["access_token"],
        revocable["access_token"],
    ]
    assert len(set(tokens)) == 7
    for session in valid.values():
        status, body, _, _ = core.get_me(factory, settings, session, stop=stop)
        assert status == 200 and body["id"] == session["user_id"]
        row = core.row_for_token(factory, session["access_token"])
        assert (row["expires_at"] - row["created_at"]).total_seconds() == 3600
    assert settings.session_ttl_seconds == 3600


def test_short_session_is_legitimate_new_login_not_clock_or_store_tamper(world):
    factory, settings, stop, _, _, short, _, _, _ = world
    row = core.row_for_token(factory, short["access_token"])
    assert short["ttl_seconds"] == 60
    assert (row["expires_at"] - row["created_at"]).total_seconds() == 60
    assert row["revoked_at"] is None
    assert short["issued_at"] == short["created_at"]
    assert short["issuance_receipt"]["prior_auth_rows_unchanged"] is True
    assert short["issuance_receipt"]["new_auth_rows"] == 1
    assert short["issuance_receipt"]["clock_override_used"] is False
    assert short["issuance_receipt"]["main_settings_ttl_seconds"] == 3600
    assert core.get_me(factory, settings, short, stop=stop)[0] == 200
    with pytest.raises(ValueError, match="NOT_NATURALLY_EXPIRED"):
        core.observe_natural_expiry(factory, settings, short, stop=stop)


def test_exact_original_cli_revocation_does_not_revoke_other_valid_tokens(world):
    factory, settings, stop, actual_cli, _, _, valid, revocable, calls = world
    before = {
        label: core.row_for_token(factory, row["access_token"])
        for label, row in valid.items()
    }
    receipt = core.revoke_exact(factory, revocable, stop=stop, cli=actual_cli)
    assert receipt["revoked_sessions"] == 1
    assert calls[-1] == ["revoke-session", "--session-id", str(revocable["session_id"])]
    status, body, _, _ = core.get_me(factory, settings, revocable, stop=stop)
    assert status == 401 and body["code"] == "TOKEN_REVOKED"
    for label, row in valid.items():
        assert core.row_for_token(factory, row["access_token"]) == before[label]
        assert core.get_me(factory, settings, row, stop=stop)[0] == 200


def test_existing_f_tables_prevent_reprovision(world):
    factory, settings, stop, actual_cli, *_ = world
    with pytest.raises(ValueError, match="FRESH_EMPTY"):
        core.create_five(factory, settings, prefix="again", stop=stop, cli=actual_cli)


def test_main_ttl_or_db_mismatch_prevent_user_creation(world):
    factory, _, stop, actual_cli, *_ = world
    for settings in (
        Settings(
            database_url="mysql+pymysql://local@mysql:3306/" + core.F_DATABASE,
            session_ttl_seconds=60,
        ),
        Settings(database_url="mysql+pymysql://local@mysql:3306/other"),
    ):
        with pytest.raises(ValueError):
            core.create_five(factory, settings, prefix="no", stop=stop, cli=actual_cli)


def test_expired_authorization_window_blocks_before_cli(world):
    factory, settings, _, actual_cli, *_ = world
    with pytest.raises(ValueError, match="ABSOLUTE_WINDOW"):
        core.create_five(
            factory,
            settings,
            prefix="expired",
            stop=datetime(2000, 1, 1, tzinfo=UTC),
            cli=actual_cli,
        )


def test_core_has_no_auth_store_manual_mutations_and_no_cloud_main():
    tree = ast.parse(
        (HERE / "790_provider_core.py").read_text(), feature_version=(3, 10)
    )
    calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)]
    assert not any(
        isinstance(node.func, ast.Attribute)
        and node.func.attr in {"insert", "update", "delete"}
        for node in calls
    )
    assert (
        "PROVIDER_PUBLIC_HANDOFF_PROTOCOL_AND_VERIFIED_F_HOST_ADAPTER_REQUIRED"
        in (HERE / "790_provider_core.py").read_text()
    )


def test_natural_expiry_after_real_wall_time_and_main_tokens_survive(world):
    factory, settings, stop, _, _, short, valid, _, _ = world
    row_before = core.row_for_token(factory, short["access_token"])
    start = time.monotonic()
    while datetime.now(UTC) <= row_before["expires_at"] + timedelta(milliseconds=50):
        core.deadline(stop)
        time.sleep(0.2)
    receipt = core.observe_natural_expiry(factory, settings, short, stop=stop)
    assert receipt["original_getMe_code"] == "TOKEN_EXPIRED"
    assert receipt["unchanged_session_row"] is True
    assert core.row_for_token(factory, short["access_token"]) == row_before
    for session in valid.values():
        assert core.get_me(factory, settings, session, stop=stop)[0] == 200
    assert settings.session_ttl_seconds == 3600
    # Actual receipt is timing metadata only; no credential output.
    print(
        json.dumps(
            {
                "kind": "natural-expiry-local-only",
                "wait_seconds": time.monotonic() - start,
                **receipt,
            }
        )
    )
