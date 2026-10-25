"""Frozen server defaults against the committed implementation, using isolated SQLite."""

from datetime import UTC, datetime

import pytest
from argon2 import PasswordHasher
from sqlalchemy import create_engine
from t44.persistence import SqlAlchemyUnitOfWorkFactory, accounts, scans
from t44.persistence.errors import StatementRejected
from t44.persistence.schema import metadata
from test_migration_order import before

AT = datetime(2026, 10, 25, tzinfo=UTC)


@pytest.fixture
def factory(tmp_path):
    engines = []

    def make(name):
        engine = create_engine(f"sqlite:///{tmp_path / (name + '.sqlite')}")
        metadata.create_all(engine)
        engines.append(engine)
        return SqlAlchemyUnitOfWorkFactory(engine)

    yield make
    for engine in engines:
        engine.dispose()


@pytest.mark.parametrize("valid", [False, True])
def test_account_and_rejection_audit_defaults_are_unchanged(factory, tmp_path, monkeypatch, valid):
    legacy = before("accounts", tmp_path)
    password = PasswordHasher().hash("synthetic default regression") if valid else "not-a-hash"
    snapshots = []
    for name, module in (("new", accounts), ("old", legacy)):
        monkeypatch.setattr(module, "utc_now", lambda: AT)
        store = factory(name)
        try:
            result = module.initialize_user(
                store,
                username="synthetic-default",
                display_name="fixture",
                password_hash=password,
                request_id="synthetic-default",
            )
        except module.PasswordHashRejected as error:
            result = type(error).__name__, str(error)
        with store() as uow:
            snapshots.append((result, uow.gateway.rows("users"), uow.gateway.rows("audit_events")))
    assert snapshots[0] == snapshots[1]


def test_scan_defaults_duplicate_fence_and_checkpoint_are_unchanged(factory, tmp_path, monkeypatch):
    legacy, snapshots = before("scans", tmp_path), []
    for name, module in (("new", scans), ("old", legacy)):
        monkeypatch.setattr(module, "utc_now", lambda: AT)
        store = factory(name)
        scan = module.ScanStore(store)
        run = "00000000-0000-0000-0000-000000000044"
        options = dict(
            rule_version=1, rule_snapshot={"rules": []}, rule_hash=b"a" * 32, cutoff_at=AT
        )
        first = scan.start(run, **options)
        assert scan.start(run, **options) == first
        with pytest.raises(StatementRejected, match="cannot change"):
            scan.start(run, **{**options, "rule_hash": b"b" * 32})
        assert scan.checkpoint(
            run, last_task_id=3, scanned_delta=3, created_delta=2, duplicate_delta=1
        )
        assert scan.checkpoint(run, last_task_id=3, scanned_delta=3)["scanned_count"] == 3
        with pytest.raises(StatementRejected, match="backwards"):
            scan.checkpoint(run, last_task_id=2)
        final = scan.checkpoint(run, last_task_id=4, scanned_delta=1, finished=True)
        with store() as uow:
            snapshots.append((first, final, uow.gateway.rows("scan_runs")))
    assert snapshots[0] == snapshots[1]
