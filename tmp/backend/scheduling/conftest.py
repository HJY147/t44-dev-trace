"""Scheduler-owned synthetic namespaces on real MySQL; CI must not silently skip."""

import json
import os
import subprocess
import sys
from datetime import timedelta
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import URL
from t44.persistence import MySQLSettings, SqlAlchemyUnitOfWorkFactory, create_mysql_engine
from t44.persistence.accounts import initialize_user
from t44.persistence.migrations import migrate
from t44.scheduling.facade import EscalationFacade
from t44.scheduling.rules import load_rules
from t44.services.application import Business
from t44.services.common import now
from t44.services.identity import HASHER
from t44.services.runtime import Runtime
from t44.settings import Settings


class PrivateValues(dict):
    def __repr__(self):
        return "<private scheduler test configuration>"


@pytest.fixture(scope="module")
def mysql():
    if os.getenv("DATABASE_URL"):
        target = os.getenv("T44_DATABASE")
        configured = Settings.from_env().mysql_settings()
        if target != configured.database:
            pytest.fail("CI/local DATABASE_URL requires matching T44_DATABASE")
    elif path := os.getenv("T44_SCHEDULER_TEST_CREDENTIALS"):
        target = os.getenv("T44_SCHEDULER_TEST_DATABASE")
        private = json.loads(Path(path).read_text())
        configured = MySQLSettings(database=target, **private)
    elif os.getenv("CI"):
        pytest.fail("CI must provide real MySQL DATABASE_URL/T44_DATABASE")
    else:
        pytest.skip("Declare a real MySQL scheduler test database")
    if target not in ("t44_test", "t44_ci"):
        pytest.fail("Scheduler tests are limited to named project test schemas")
    engine = create_mysql_engine(configured)
    migrate(engine, expected_database=target)
    url = URL.create(
        "mysql+pymysql",
        username=configured.username,
        password=configured.password,
        host=configured.host,
        port=configured.port,
        database=target,
    )
    yield (
        SqlAlchemyUnitOfWorkFactory(engine),
        PrivateValues(
            os.environ,
            DATABASE_URL=url.render_as_string(hide_password=False),
            T44_DATABASE=target,
            PYTHONPATH="backend",
        ),
    )
    engine.dispose()


@pytest.fixture
def team(mysql, tmp_path):
    factory, env = mysql
    stamp, suffix = now(), uuid4().hex[:12]
    password, users = uuid4().hex, []
    hashed = HASHER.hash(password)
    for role in ("owner", "manager", "manager2", "inactive-manager"):
        users.append(
            initialize_user(
                factory,
                username=f"sch-{role}-{suffix}",
                display_name="Synthetic scheduler test identity",
                password_hash=hashed,
            )
        )
    with factory() as uow:
        g = uow.gateway
        pid = g.insert(
            "projects",
            dict(
                name=f"sch-{suffix}",
                description="Synthetic scanner fixture",
                created_by=users[1],
                created_at=stamp,
                updated_at=stamp,
            ),
        )
        for index, uid in enumerate(users):
            g.insert(
                "project_members",
                dict(
                    project_id=pid,
                    user_id=uid,
                    roles_mask=2 if index == 0 else 1,
                    active=int(index != 3),
                    created_at=stamp,
                    updated_at=stamp,
                ),
            )
        iteration = g.insert(
            "iterations",
            dict(
                project_id=pid,
                name=f"sch-{suffix}",
                planned_start=stamp - timedelta(days=30),
                planned_end=stamp + timedelta(days=30),
                capacity=[{"user_id": users[0], "quarters": 400}],
                buffer_quarters=0,
                delay_contingency="Synthetic only",
                created_at=stamp,
                updated_at=stamp,
            ),
        )
    token_file = tmp_path / "service.json"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "t44.cli",
            "service-token",
            "--name",
            f"sch-{suffix}",
            "--project-id",
            str(pid),
            "--token-file",
            str(token_file),
        ],
        env=env,
        text=True,
        capture_output=True,
    )
    assert result.returncode == 0, result.stderr
    token = json.loads(token_file.read_text())["access_token"]
    config = load_rules().snapshot()
    # Real fixture IDs are mapped here; these are synthetic setup metadata, not human approval.
    config.update(version=1000000 + users[1], decided_by=users[1])
    rule_file = tmp_path / "rules.json"
    rule_file.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n")
    rules = load_rules(rule_file)
    runtime = Runtime(
        factory, Settings(login_attempts=1000), Business(escalations=EscalationFacade(rules))
    )

    def task(*, state=2, end=None, owner=None):
        end = end or now() - timedelta(days=3)
        with factory() as uow:
            return uow.gateway.insert(
                "tasks",
                dict(
                    project_id=pid,
                    iteration_id=iteration,
                    title=f"sch-{suffix}",
                    description="Synthetic initial state, not a workflow verdict",
                    owner_id=owner or users[0],
                    state=state,
                    planned_start=end - timedelta(days=2),
                    planned_end=end,
                    estimated_quarters=4,
                    buffer_quarters=0,
                    delay_contingency="Synthetic only",
                    created_at=stamp,
                    updated_at=stamp,
                    blocked_from_state=2 if state == 3 else None,
                    block_reason="Synthetic blocker" if state == 3 else None,
                    responsibility_stage=1 if state == 3 else None,
                ),
            )

    return PrivateValues(
        factory=factory,
        env=env,
        project=pid,
        users=users,
        token=token,
        token_file=token_file,
        rules=rules,
        rule_file=rule_file,
        runtime=runtime,
        task=task,
        password=password,
    )
