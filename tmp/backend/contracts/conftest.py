"""SQLite-backed HTTP self-tests; not evidence of MySQL locking/constraints or acceptance."""

from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from t44.api import create_app
from t44.persistence import SqlAlchemyUnitOfWorkFactory
from t44.persistence.schema import metadata
from t44.services.identity import HASHER
from t44.settings import Settings


@pytest.fixture
def application():
    engine = create_engine(
        "sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False}
    )
    metadata.create_all(engine)
    factory = SqlAlchemyUnitOfWorkFactory(engine)
    timestamp = datetime.now(UTC)
    hashed = HASHER.hash("test-only-password")
    with factory() as uow:
        for username in ("manager", "developer", "reviewer", "outsider"):
            uow.gateway.insert(
                "users",
                {
                    "username": username,
                    "display_name": username,
                    "password_hash": hashed,
                    "active": 1,
                    "created_at": timestamp,
                    "updated_at": timestamp,
                },
            )
    app = create_app(factory=factory, settings=Settings(login_attempts=1000))
    with TestClient(app) as client:
        yield client, factory
    engine.dispose()
