"""Load archived/candidate modules and install only four methods during developer tests."""

import importlib.util
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OPERATIONS = {
    "addTaskDependency": "tasks",
    "removeTaskDependency": "tasks",
    "createTaskReview": "reviews",
    "createReleaseAssessment": "reviews",
}


def load(name, path):
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def modules(phase):
    directory = HERE / phase / "backend/t44/services"
    if phase == "candidate":
        load("t44.services.operation_plan", directory / "operation_plan.py")
    return {
        name: load(f"t44.services._{phase}_{name}", directory / f"{name}.py")
        for name in ("tasks", "reviews")
    }


def methods(phase):
    loaded = modules(phase)
    return {
        operation: getattr(
            getattr(loaded[module], "Tasks" if module == "tasks" else "Reviews"), operation
        )
        for operation, module in OPERATIONS.items()
    }


class CandidatePlugin:
    def pytest_sessionstart(self, session):
        from t44.services.reviews import Reviews
        from t44.services.tasks import Tasks

        self.originals = []
        for operation, callback in methods("candidate").items():
            owner = Tasks if OPERATIONS[operation] == "tasks" else Reviews
            self.originals.append((owner, operation, getattr(owner, operation)))
            setattr(owner, operation, callback)

    def pytest_sessionfinish(self, session):
        for owner, operation, callback in self.originals:
            setattr(owner, operation, callback)
