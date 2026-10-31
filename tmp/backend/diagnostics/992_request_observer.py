"""Diagnostic-off equivalence, privacy, exception cleanup and concurrent isolation."""

import contextlib
import importlib
import os
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from t44 import diagnostics as d

pytestmark = pytest.mark.contract


class Checks(unittest.TestCase):
    def test_disabled_is_noop(self):
        with d.span("unused"):
            d.count("unused")
        self.assertFalse(d.active())

    def test_exception_cleanup(self):
        class State:
            diagnostic_dispatch_ready_ns = 0

        class Request:
            state = State()

        @d.diagnosed(True)
        def handle(request):
            raise ValueError("synthetic")

        with self.assertRaises(ValueError):
            handle(Request())
        self.assertFalse(d.active())

    def test_parallel_contexts_are_not_shared(self):
        barrier = threading.Barrier(2)

        def run(value):
            token = d._CURRENT.set({})
            try:
                d.count("count", value)
                barrier.wait(timeout=2)
                return dict(d._CURRENT.get())
            finally:
                d._CURRENT.reset(token)

        with ThreadPoolExecutor(2) as pool:
            jobs = [pool.submit(run, v) for v in [3, 9]]
            self.assertEqual([j.result() for j in jobs], [{"count": 3}, {"count": 9}])

    def test_clock_and_export_failure_do_not_change_business(self):
        request = SimpleNamespace(state=SimpleNamespace(diagnostic_dispatch_ready_ns=0))
        for target in [
            "perf_counter_ns",
            "thread_time_ns",
            "_export",
            "count",
            "getpid",
        ]:
            response = SimpleNamespace(headers={"Server-Timing": "app;dur=1"})
            calls = []

            @d.diagnosed(True)
            def handle(request, *, _calls=calls, _response=response):
                _calls.append("business")
                return _response

            with (
                self.subTest(target=target),
                patch.object(d, target, side_effect=ValueError("measurement fault")),
            ):
                self.assertIs(handle(request), response)
            if target == "getpid":
                self.assertNotIn("diag-worker-pid", response.headers["Server-Timing"])
                self.assertIn(
                    'diag-incomplete;desc="1"', response.headers["Server-Timing"]
                )
            self.assertEqual(calls, ["business"])
            self.assertFalse(d.active())

    def test_business_exception_is_not_replaced_by_clock_failure(self):
        request = SimpleNamespace(state=SimpleNamespace(diagnostic_dispatch_ready_ns=0))
        error = RuntimeError("business sentinel")

        @d.diagnosed(True)
        def handle(request):
            raise error

        with (
            patch.object(d, "perf_counter_ns", side_effect=ValueError("clock")),
            self.assertRaises(RuntimeError) as raised,
        ):
            handle(request)
        self.assertIs(raised.exception, error)
        self.assertFalse(d.active())

    def test_numeric_header_bound_and_metric_limit(self):
        request = SimpleNamespace(state=SimpleNamespace(diagnostic_dispatch_ready_ns=0))

        @d.diagnosed(True)
        def handle(request):
            for i in range(1000):
                d.count("value" + str(i), i)
            d.count("invalid header\r\nsecret", 1)
            d.count("string", "sensitive")
            self.assertLessEqual(len(d._CURRENT.get()), 64)
            return SimpleNamespace(headers={"Server-Timing": "app;dur=1"})

        response = handle(request)
        self.assertLessEqual(len(response.headers["Server-Timing"]), 2048)
        self.assertNotIn("secret", response.headers["Server-Timing"])
        self.assertFalse(d.active())
        self.assertIn('diag-incomplete;desc="1"', response.headers["Server-Timing"])

    def test_real_http_on_off_and_no_token_projection(self):
        env = patch.dict(os.environ, {}, clear=False)
        env.start()
        self.addCleanup(env.stop)
        fixture = importlib.import_module("tmp.backend.contracts.conftest")
        http = importlib.import_module("tmp.backend.contracts.986_http")
        for flag in ["0", "1"]:
            os.environ["T44_REQUEST_DIAGNOSTICS"] = flag
            gen = fixture.application.__wrapped__()
            client, _ = next(gen)
            try:
                tokens, pid, iid = http.setup_project(client)
                task = http.create_task(client, tokens, pid, iid)
                if flag == "0":
                    with (
                        patch(
                            "t44.api.time.perf_counter_ns",
                            side_effect=RuntimeError("must not read optional clock"),
                        ),
                        patch.object(
                            d,
                            "getpid",
                            side_effect=RuntimeError("must not read optional PID"),
                        ),
                    ):
                        response = http.request(
                            client,
                            "getTask",
                            token=tokens["manager"],
                            project_id=pid,
                            task_id=task["id"],
                            expect=200,
                        )
                else:
                    response = http.request(
                        client,
                        "getTask",
                        token=tokens["manager"],
                        project_id=pid,
                        task_id=task["id"],
                        expect=200,
                    )
                timing = response.headers["server-timing"]
                self.assertEqual("diag-handle-wall" in timing, flag == "1")
                self.assertEqual("diag-worker-pid" in timing, flag == "1")
                if flag == "1":
                    self.assertIn(f'diag-worker-pid;desc="{os.getpid()}"', timing)
                self.assertNotIn(tokens["manager"], timing)
                self.assertNotIn("SELECT", timing)
                self.assertFalse(d.active())
            finally:
                with contextlib.suppress(StopIteration):
                    next(gen)
        os.environ.pop("T44_REQUEST_DIAGNOSTICS", None)


if __name__ == "__main__":
    unittest.main()
