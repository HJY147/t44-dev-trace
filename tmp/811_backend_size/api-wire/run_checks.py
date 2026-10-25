"""Opt-in public-response differential run and matched render CPU measurement."""

import copy
import cProfile
import gc
import hashlib
import importlib
import json
import pstats
import statistics
import sys
import threading
import time
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

import pytest
from t44.contracts import OPERATIONS

probe = importlib.import_module("tmp.811_backend_size.api-wire.probe")
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PREFIX = "page-shapes-" if "--page-shapes-only" in sys.argv else ""


@dataclass
class Captured:
    operation: str
    call: object
    result: tuple
    settings: object
    server_time: str | None
    duration_ms: float
    body: bytes
    headers: dict

    def render(self, renderer):
        return probe.render(
            renderer,
            OPERATIONS[self.operation],
            self.call,
            self.result,
            self.settings,
            server_time=self.server_time,
            duration_ms=self.duration_ms,
        )


class Differential:
    def __init__(self):
        self.base = probe.baseline_renderer()
        self.candidate = probe.candidate_renderer()
        self.lock = threading.Lock()
        self.results = []
        self.non_envelope = 0

    @pytest.hookimpl(hookwrapper=True)
    def pytest_fixture_setup(self, fixturedef, request):
        outcome = yield
        if fixturedef.argname == "application":
            client, _ = outcome.get_result()
            self.observe(client)

    def observe(self, client):
        runtime = client.app.state.runtime
        execute, request = runtime.execute, client.request
        pending = {}
        lock = threading.Lock()

        def captured_execute(call, validate, source="unknown"):
            result = execute(call, validate, source)
            with lock:
                pending[call.request_id] = (call, result)
            return result

        def paired_request(*args, **kwargs):
            response = request(*args, **kwargs)
            request_id = response.headers.get("X-Request-ID")
            if request_id is None:
                with self.lock:
                    self.non_envelope += 1
                return response
            with lock:
                call, result = pending.pop(request_id)
            data = response.json()
            meta = data.get("meta", {})
            duration = float(response.headers["Server-Timing"].removeprefix("app;dur="))
            captured = Captured(
                call.operation,
                call,
                result,
                runtime.settings,
                meta.get("server_time"),
                duration,
                response.content,
                dict(response.headers),
            )
            original = copy.deepcopy(result)
            reference = captured.render(self.base)
            candidate = captured.render(self.candidate)
            for label, rendered in (("base", reference), ("candidate", candidate)):
                if (
                    rendered.status_code != response.status_code
                    or rendered.body != response.content
                ):
                    raise AssertionError(
                        f"{label} response mismatch: {call.operation}; payload bytes withheld"
                    )
                if dict(rendered.headers) != dict(response.headers):
                    raise AssertionError(f"{label} header mismatch: {call.operation}")
            if result != original:
                raise AssertionError(f"Rendering mutated Runtime data: {call.operation}")
            with self.lock:
                self.results.append(captured)
            return response

        runtime.execute, client.request = captured_execute, paired_request

    def write_summary(self):
        counts = Counter((item.operation, item.result[0]) for item in self.results)
        receipt = {
            "base": "d63fe18f3227e1779d3951072636efcdb6181550",
            "requests_compared": len(self.results),
            "mismatches": 0,
            "non_envelope_responses": self.non_envelope,
            "scope": "actual candidate HTTP responses versus exact base render tail on same Runtime output; body and all headers exact",
            "runtime_byte_identical": True,
            "tokens_or_payload_bodies_persisted": False,
            "operations_and_statuses": [
                {"operation": operation, "status": status, "count": count}
                for (operation, status), count in sorted(counts.items())
            ],
            "payload_hashes": [
                {
                    "operation": item.operation,
                    "status": item.result[0],
                    "bytes": len(item.body),
                    "sha256": hashlib.sha256(item.body).hexdigest(),
                }
                for item in self.results
            ],
        }
        (HERE / (PREFIX + "http-differential.json")).write_text(
            json.dumps(receipt, indent=2) + "\n"
        )

    def benchmark(self):
        selected = {}
        for item in self.results:
            if item.result[0] < 400 and item.operation in (
                "getTask",
                "listTasks",
                "transitionTask",
                "listProjectAuditEvents",
            ):
                label = item.operation
                if item.operation == "listTasks":
                    label += "/page_size=" + str(item.result[1]["page_size"])
                if label not in selected or len(item.body) > len(selected[label].body):
                    selected[label] = item
        cases, profiles = [], []
        for operation, item in sorted(selected.items()):
            iterations = 12 if len(item.body) > 15000 else 40
            samples = {"base": [], "candidate": []}
            enabled = gc.isenabled()
            gc.disable()
            try:
                for repeat in range(9):
                    pairs = (("base", self.base), ("candidate", self.candidate))
                    for label, renderer in pairs if repeat % 2 else reversed(pairs):
                        started = time.process_time_ns()
                        for _ in range(iterations):
                            value = item.render(renderer)
                            if value.body != item.body:
                                raise AssertionError(
                                    "Timed renderer output changed; payload bytes withheld"
                                )
                        samples[label].append((time.process_time_ns() - started) / iterations)
            finally:
                if enabled:
                    gc.enable()
            profile = {"operation": operation, "calls_per_renderer": 5, "wire": {}}
            for label, renderer in (("base", self.base), ("candidate", self.candidate)):
                profiler = cProfile.Profile()
                profiler.enable()
                for _ in range(5):
                    item.render(renderer)
                profiler.disable()
                entry = next(
                    value
                    for (filename, _, name), value in pstats.Stats(profiler).stats.items()
                    if filename.endswith("/t44/services/common.py") and name == "wire"
                )
                profile["wire"][label] = dict(
                    zip(
                        (
                            "primitive_calls",
                            "all_recursive_calls",
                            "own_cpu_seconds",
                            "inclusive_cpu_seconds",
                        ),
                        entry[:4],
                        strict=True,
                    )
                )
            profiles.append(profile)
            medians = {label: statistics.median(values) for label, values in samples.items()}
            cases.append(
                {
                    "operation": operation,
                    "payload_bytes": len(item.body),
                    "iterations_per_sample": iterations,
                    "repeats": 9,
                    "cpu_ns_per_call": samples,
                    "median_cpu_ns": medians,
                    "candidate_over_base": medians["candidate"] / medians["base"],
                }
            )
        (HERE / (PREFIX + "render-cpu.json")).write_text(
            json.dumps(
                {
                    "scope": "matched API render tail including real frozen response schema; excludes Runtime/SQL/network",
                    "sample_order": "alternating base-candidate and candidate-base",
                    "gc_during_timing": False,
                    "cases": cases,
                    "formal_performance_proven": False,
                },
                indent=2,
            )
            + "\n"
        )
        (HERE / (PREFIX + "wire-profile.json")).write_text(
            json.dumps(
                {
                    "scope": "wire only; inclusive CPU not summed with parent frames",
                    "cases": profiles,
                },
                indent=2,
            )
            + "\n"
        )
        print(
            json.dumps(
                [
                    {
                        key: case[key]
                        for key in (
                            "operation",
                            "payload_bytes",
                            "median_cpu_ns",
                            "candidate_over_base",
                        )
                    }
                    for case in cases
                ]
            )
        )


if __name__ == "__main__":
    differential = Differential()
    selected_tests = (
        [str(ROOT / "tmp/811_backend_size/816_api_wire_pages.py")]
        if PREFIX
        else [
            str(ROOT / "tmp/811_backend_size/815_api_wire_boundary.py"),
            *[
                str(ROOT / ("tmp/backend/contracts/" + name + ".py"))
                for name in (
                    "986_http",
                    "987_faults",
                    "856_release_error_priority",
                    "859_dependency_delivered",
                    "816_acceptance_followup_20261025",
                )
            ],
        ]
    )
    code = pytest.main(
        [
            "-q",
            "-c",
            str(ROOT / "backend/pyproject.toml"),
            *selected_tests,
            "--junitxml=" + str(HERE / (PREFIX + "all-junit.xml")),
        ],
        plugins=[differential],
    )
    if code == 0:
        differential.write_summary()
        differential.benchmark()
    raise SystemExit(code)
