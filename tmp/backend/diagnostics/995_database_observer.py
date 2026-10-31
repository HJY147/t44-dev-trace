"""Synthetic local metrics boundaries, no network or SQL data in observer."""

import unittest
from unittest.mock import patch

import pytest
from sqlalchemy.exc import OperationalError
from t44 import diagnostics as d
from t44.persistence.errors import CommitUncertain, PersistenceUnavailable
from t44.persistence.uow import SqlAlchemyUnitOfWork

pytestmark = pytest.mark.contract


class Result:
    def __enter__(self):
        return self

    def __exit__(self, *a):
        pass

    def scalar_one(self):
        return 4


class Session:
    def __init__(self, fail=None):
        self.calls = []
        self.fail = fail

    def begin(self):
        self.calls.append("begin")

    def connection(self):
        self.calls.append("connection")
        if self.fail == "connection":
            raise OperationalError("", {}, Exception("synthetic"))

    def execute(self, *a):
        self.calls.append("execute")
        if self.fail == "execute":
            raise OperationalError("", {}, Exception("synthetic"))
        return Result()

    def commit(self):
        self.calls.append("commit")
        if self.fail == "commit":
            raise RuntimeError("synthetic")

    def rollback(self):
        self.calls.append("rollback")

    def close(self):
        self.calls.append("close")


class Checks(unittest.TestCase):
    def run_case(self, enabled, fail=None):
        trace = {}
        token = d._CURRENT.set(trace if enabled else None)
        s = Session(fail)
        try:
            try:
                with SqlAlchemyUnitOfWork(lambda: s) as u:
                    u.gateway._execute(object(), "count")
            except (PersistenceUnavailable, CommitUncertain) as e:
                return trace, s, type(e).__name__
            return trace, s, None
        finally:
            d._CURRENT.reset(token)

    def test_disabled_does_not_acquire_or_emit(self):
        with (
            patch.object(
                d, "perf_counter_ns", side_effect=AssertionError("disabled clock read")
            ),
            patch.object(
                d,
                "thread_time_ns",
                side_effect=AssertionError("disabled cpu clock read"),
            ),
        ):
            t, s, e = self.run_case(False)
        self.assertEqual(t, {})
        self.assertNotIn("connection", s.calls)
        self.assertIsNone(e)

    def test_enabled_boundaries(self):
        t, s, e = self.run_case(True)
        self.assertIsNone(e)
        self.assertEqual(t["db.statements"], 1)
        for n in ["db.acquire", "db.execute_fetch", "db.commit", "db.close"]:
            self.assertEqual(t[n + ".calls"], 1)
            self.assertGreaterEqual(t[n + ".wall_ns"], 0)
            self.assertGreaterEqual(t[n + ".cpu_ns"], 0)
        self.assertEqual(s.calls, ["begin", "connection", "execute", "commit", "close"])
        with patch.object(
            d,
            "perf_counter_ns",
            side_effect=RuntimeError("synthetic diagnostic clock fault"),
        ):
            t, s, e = self.run_case(True)
        self.assertIsNone(e)
        self.assertEqual(s.calls, ["begin", "connection", "execute", "commit", "close"])
        self.assertNotIn("rollback", s.calls)

    def test_connection_error_mapping_and_rollback(self):
        t, s, e = self.run_case(True, "connection")
        self.assertEqual(e, "PersistenceUnavailable")
        self.assertNotIn("execute", s.calls)
        self.assertIn("rollback", s.calls)
        self.assertEqual(t["db.acquire.calls"], 1)

    def test_execute_error_mapping_and_rollback(self):
        t, s, e = self.run_case(True, "execute")
        self.assertEqual(e, "PersistenceUnavailable")
        self.assertEqual(t["db.execute_fetch.calls"], 1)
        self.assertIn("rollback", s.calls)

    def test_commit_uncertain_preserved(self):
        t, s, e = self.run_case(True, "commit")
        self.assertEqual(e, "CommitUncertain")
        self.assertEqual(t["db.commit.calls"], 1)
        self.assertEqual(s.calls[-2:], ["rollback", "close"])
