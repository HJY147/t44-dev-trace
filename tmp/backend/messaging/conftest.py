"""Own synthetic module fixtures; MySQL and SQLite results are recorded separately."""

import json
import os
from datetime import timedelta
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from t44.persistence import MySQLSettings, SqlAlchemyUnitOfWorkFactory, create_mysql_engine
from t44.persistence.codecs import utc_now
from t44.persistence.migrations import migrate
from t44.persistence.scans import ScanStore
from t44.persistence.schema import metadata
from t44.services.identity import HASHER


@pytest.fixture(scope="module")
def mysql_factory():
    if source := os.getenv("DATABASE_URL"):
        url = make_url(source)
        database = os.getenv("T44_DATABASE")
        if (
            url.drivername != "mysql+pymysql"
            or database != url.database
            or database not in ("t44_ci", "t44_test")
        ):
            pytest.fail("A matching disposable T44 test database is required")
        values = dict(
            host=url.host, port=url.port or 3306, username=url.username, password=url.password
        )
    elif path := os.getenv("T44_TEST_CREDENTIALS"):
        database = os.getenv("T44_TEST_DATABASE")
        if database != "t44_test":
            pytest.fail("Local messaging checks require T44_TEST_DATABASE=t44_test")
        secret = json.loads(Path(path).read_text())
        values = {key: secret[key] for key in ("host", "port", "username", "password")}
    elif os.getenv("CI"):
        pytest.fail("Real MySQL configuration missing in CI; refusing to skip")
    else:
        pytest.skip("No real MySQL test configuration")
    engine = create_mysql_engine(MySQLSettings(database=database, **values))
    migrate(engine, expected_database=database)
    yield SqlAlchemyUnitOfWorkFactory(engine)
    engine.dispose()


@pytest.fixture(params=["sqlite", pytest.param("mysql", marks=pytest.mark.integration)])
def factory(request, tmp_path):
    if request.param == "mysql":
        yield request.getfixturevalue("mysql_factory")
    else:
        engine = create_engine(f"sqlite:///{tmp_path / 'messaging.sqlite'}")
        metadata.create_all(engine)
        yield SqlAlchemyUnitOfWorkFactory(engine)
        engine.dispose()


@pytest.fixture
def case(factory):
    now, suffix = utc_now(), uuid4().hex[:12]
    hashed = HASHER.hash("synthetic-module-password")
    with factory() as uow:
        g = uow.gateway
        users = [
            g.insert(
                "users",
                dict(
                    username=f"msg-{suffix}-{i}",
                    display_name="合成消息账户",
                    password_hash=hashed,
                    active=1,
                    created_at=now,
                    updated_at=now,
                ),
            )
            for i in range(3)
        ]
        pid = g.insert(
            "projects",
            dict(
                name="合成消息项目",
                description="module fixture",
                created_by=users[0],
                created_at=now,
                updated_at=now,
            ),
        )
        for uid in users[:2]:
            g.insert(
                "project_members",
                dict(
                    project_id=pid,
                    user_id=uid,
                    roles_mask=7,
                    active=1,
                    created_at=now,
                    updated_at=now,
                ),
            )
        iteration = g.insert(
            "iterations",
            dict(
                project_id=pid,
                name="synthetic",
                planned_start=now - timedelta(days=1),
                planned_end=now + timedelta(days=1),
                capacity=[{"user_id": users[0], "quarters": 400}],
                buffer_quarters=0,
                delay_contingency="fixture",
                created_at=now,
                updated_at=now,
            ),
        )
    result = SimpleNamespace(
        factory=factory,
        user=users[0],
        other=users[1],
        outsider=users[2],
        project=pid,
        iteration=iteration,
        now=now,
    )
    result.event = lambda **kwargs: event(result, **kwargs)
    return result


def event(case, *, event_type=2, recipients=None):
    now = utc_now()
    run = ScanStore(case.factory).start(
        uuid4(), rule_version=1, rule_snapshot={"rules": []}, rule_hash=b"m" * 32
    )
    with case.factory() as uow:
        g = uow.gateway
        task = g.insert(
            "tasks",
            dict(
                project_id=case.project,
                iteration_id=case.iteration,
                owner_id=case.user,
                title="合成升级任务",
                description="module fixture",
                planned_start=case.now - timedelta(days=1),
                planned_end=case.now,
                estimated_quarters=4,
                buffer_quarters=0,
                delay_contingency="fixture",
                created_at=now,
                updated_at=now,
            ),
        )
        eid = g.insert(
            "outbox_events",
            dict(
                event_type=event_type,
                schema_version=1,
                project_id=case.project,
                task_id=task,
                payload={"title": "合成升级", "message": "module test"},
                recipients=(recipients or [case.user]) if event_type == 2 else [],
                status=1,
                attempts=0,
                next_attempt_at=now,
                created_at=now,
                updated_at=now,
            ),
        )
        if event_type == 2:
            g.insert(
                "escalation_events",
                dict(
                    project_id=case.project,
                    task_id=task,
                    schedule_version=1,
                    level=1,
                    rule_version=1,
                    rule_snapshot={"rules": []},
                    rule_hash=b"m" * 32,
                    scan_run_id=run["id"],
                    planned_end=case.now,
                    observed_at=now,
                    event_id=eid,
                ),
            )
    return eid
