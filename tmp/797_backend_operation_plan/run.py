"""Run only the scoped developer scenarios with temporary candidate methods installed."""

import importlib
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
probe = importlib.import_module("tmp.797_backend_operation_plan.probe")

if __name__ == "__main__":
    raise SystemExit(
        pytest.main(
            [
                "-q",
                "-c",
                str(ROOT / "backend/pyproject.toml"),
                str(HERE / "797_plan_differential.py"),
                str(HERE / "797_plan_http_faults.py"),
                *[
                    str(ROOT / "tmp/backend/contracts" / name)
                    for name in (
                        "986_http.py",
                        "987_faults.py",
                        "856_release_error_priority.py",
                        "859_dependency_delivered.py",
                        "816_acceptance_followup_20261025.py",
                    )
                ],
                "--junitxml=" + str(HERE / "candidate-junit.xml"),
            ],
            plugins=[probe.CandidatePlugin()],
        )
    )
