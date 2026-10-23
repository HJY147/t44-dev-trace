"""Actual child process + real MySQL + actual TCP refusal; not a live-broker success test."""

import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import pytest
from sqlalchemy import URL
from t44.persistence.delivery import OutboxStore

pytestmark = [
    pytest.mark.integration,
    pytest.mark.fault,
    pytest.mark.parametrize("factory", ["mysql"], indirect=True),
]


def process_env():
    env = dict(os.environ)
    if not env.get("DATABASE_URL"):
        values = json.loads(Path(env["T44_TEST_CREDENTIALS"]).read_text())
        env["DATABASE_URL"] = URL.create(
            "mysql+pymysql",
            username=values["username"],
            password=values["password"],
            host=values["host"],
            port=values["port"],
            database=env["T44_TEST_DATABASE"],
        ).render_as_string(hide_password=False)
        env["T44_DATABASE"] = env["T44_TEST_DATABASE"]
    env["AMQP_URL"] = "amqp://synthetic:never-log-this@127.0.0.1:1/%2F"
    return env


def test_real_process_unreachable_broker_commits_fallback_and_gracefully_stops(case):
    eid, store, env = case.event(), OutboxStore(case.factory), process_env()
    proc = subprocess.Popen(
        [sys.executable, "-m", "t44.messaging"],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        deadline = time.monotonic() + 20
        while time.monotonic() < deadline and store.get(eid)["status"] != 4:
            assert proc.poll() is None, "Messaging process exited before fallback"
            time.sleep(0.1)
        assert store.get(eid)["status"] == 4
        proc.send_signal(signal.SIGTERM)
        output, _ = proc.communicate(timeout=15)
        assert proc.returncode == 0
        assert "delivery_cycle" in output and "never-log-this" not in output
        assert store.consume(eid)["created"] == 0
        with case.factory() as uow:
            rows = uow.gateway.rows("notifications", {"event_id": eid})
            assert len(rows) == 1 and rows[0]["fallback"] == 1
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.communicate(timeout=5)
