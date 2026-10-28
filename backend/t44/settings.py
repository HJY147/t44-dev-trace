"""Process settings. Database connections are created only by the persistence owner."""

import os
from dataclasses import dataclass

from sqlalchemy.engine import make_url

from t44.persistence import MySQLSettings


@dataclass(frozen=True)
class Settings:
    database_url: str = ""
    session_ttl_seconds: int = 3600
    login_attempts: int = 10
    login_window_seconds: int = 60
    idempotency_lease_seconds: int = 60

    def __post_init__(self):
        if type(self.session_ttl_seconds) is not int or not 60 <= self.session_ttl_seconds <= 86400:
            raise ValueError("Session TTL must be in 60..86400 seconds")

    @classmethod
    def from_env(cls):
        return cls(
            database_url=os.getenv("DATABASE_URL", ""),
            session_ttl_seconds=int(os.getenv("T44_SESSION_TTL_SECONDS", "3600")),
        )

    def mysql_settings(self):
        url = make_url(self.database_url)
        if url.drivername != "mysql+pymysql" or not url.database:
            raise ValueError("DATABASE_URL must select mysql+pymysql and an explicit database")
        declared = os.getenv("T44_DATABASE")
        if declared and declared != url.database:
            raise ValueError("T44_DATABASE differs from DATABASE_URL")
        return MySQLSettings(
            host=url.host,
            database=url.database,
            username=url.username,
            password=url.password or "",
            port=url.port or 3306,
            pool_size=int(os.getenv("T44_DB_POOL_SIZE", "5")),
            max_overflow=int(os.getenv("T44_DB_MAX_OVERFLOW", "10")),
        )

    def __repr__(self):
        return f"Settings(database_url=<redacted>, session_ttl_seconds={self.session_ttl_seconds})"
