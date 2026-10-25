"""Run developer domain checks with explicit migration accounting; no product execution."""

import importlib
import json
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
_COUNTS = {"legacy_assertion_cases_exercising_v2": 0, "historical_constructor_only_cases": 0}


class Accounting:
    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_call(self, item):
        fixture = importlib.import_module("tmp.811_backend_size.legacy_fixture")
        before = fixture.CALLS
        yield
        if item.path.name == "994_transitions.py":
            key = (
                "legacy_assertion_cases_exercising_v2"
                if before < fixture.CALLS
                else "historical_constructor_only_cases"
            )
            _COUNTS[key] += 1

    def pytest_sessionfinish(self, session):
        (HERE / "legacy-migration-receipt.json").write_text(json.dumps(_COUNTS, indent=2) + "\n")


if __name__ == "__main__":
    raise SystemExit(
        pytest.main(
            [
                "-q",
                "-c",
                str(ROOT / "backend/pyproject.toml"),
                str(HERE / "811_differential.py"),
                str(HERE / "812_v2_boundary.py"),
                str(ROOT / "tmp/backend/backend/domain/994_transitions.py"),
                "--junitxml=" + str(HERE / "domain-v2-junit.xml"),
            ],
            plugins=[Accounting()],
        )
    )
