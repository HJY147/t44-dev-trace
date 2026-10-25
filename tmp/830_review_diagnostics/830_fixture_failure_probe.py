"""One no-database failure-path probe for the exact diagnostic driver."""

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType
from unittest.mock import patch


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


root = Path(__file__).resolve().parents[2]
driver = load("review_driver", root / "tmp/834_backend_performance/834_request_profile.py")
database = load("review_database", root / "tmp/833_database_performance/833_database_trace.py")
observer = database.DatabaseTrace()
closed = []
original_close = observer.close


def close():
    closed.append(True)
    return original_close()


class SyntheticFixtureFailure(Exception):
    pass


def fixture(_args):
    raise SyntheticFixtureFailure("fixed synthetic setup sentinel")
    yield  # Keep the same generator protocol without importing an application.


observer.close = close
driver.observer_from = lambda _args: observer
driver.fixture = fixture
fake_contracts = ModuleType("t44.contracts")
fake_contracts.OPERATIONS = {}
fake_contracts.violations = lambda *_args: []
fake_codes = ModuleType("t44.services.codes")
fake_codes.Action = object()
report = {}
with patch.dict(sys.modules, {"t44.contracts": fake_contracts, "t44.services.codes": fake_codes}):
    try:
        driver.run(None, root, report)
    except BaseException as error:
        result = {
            "observed_exception_class": type(error).__name__,
            "original_exception_preserved_as_primary": isinstance(error, SyntheticFixtureFailure),
            "context_exception_class": type(error.__context__).__name__ if error.__context__ else None,
            "observer_close_called": bool(closed),
            "requests_field_written": "requests" in report,
            "database_engine_installed": observer.engine is not None,
            "database_or_application_imports": sorted(
                name for name in sys.modules
                if name.split(".")[0] in {"sqlalchemy", "pymysql", "t44", "httpx"}
                and name not in {"t44.contracts", "t44.services.codes"}
            ),
            "probe_scope": "fake pre-install fixture failure; no application, SQL, HTTP, service or CI execution",
        }
    else:
        raise AssertionError("Expected synthetic fixture failure")
print(json.dumps(result, indent=2))
