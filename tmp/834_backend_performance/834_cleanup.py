"""Narrow real-run cleanup regression with in-memory operation/fixture stubs, no DB."""

import builtins
import importlib.util
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest


class PrimaryFailure(RuntimeError):
    pass


class CleanupFailure(RuntimeError):
    pass


def harness(monkeypatch, *, failure=None, cleanup_errors=(), observer_requested=True):
    modules = {
        name: ModuleType(name)
        for name in ("t44", "t44.contracts", "t44.services", "t44.services.codes")
    }
    modules["t44"].__path__ = []
    modules["t44.services"].__path__ = []
    names = (
        "login",
        "createProject",
        "addProjectMember",
        "createIteration",
        "createTask",
        "getTask",
        "listTasks",
        "validateContractPayload",
        "transitionTask",
    )
    modules["t44.contracts"].OPERATIONS = {
        name: {
            "method": "post",
            "path": "/" + name,
            "success_status": 200,
            "responses": {"200": {"content": {"application/json": {"schema": {}}}}},
        }
        for name in names
    }
    modules["t44.contracts"].violations = lambda *_: []
    modules["t44.services.codes"].Action = SimpleNamespace(BLOCK=2, UNBLOCK=3)
    for name, module in modules.items():
        monkeypatch.setitem(sys.modules, name, module)
    original_import = builtins.__import__

    def import_without_operational_modules(name, *args, **kwargs):
        if name.startswith(("sqlalchemy", "fastapi", "pymysql", "t44.persistence", "t44.api")):
            raise AssertionError("real DB/application import during cleanup regression")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", import_without_operational_modules)
    path = Path(__file__).with_name("834_request_profile.py")
    spec = importlib.util.spec_from_file_location("cleanup_driver_under_test", path)
    driver = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(driver)
    calls, primary = [], PrimaryFailure("synthetic primary")

    class Observer:
        installed = False
        close_called = False

        def install(self, _engine):
            calls.append("observer_install")
            self.installed = True
            if failure == "install":
                raise primary

        def snapshot(self):
            calls.append("observer_snapshot")
            if not self.installed or "observer_snapshot" in cleanup_errors:
                raise CleanupFailure("snapshot unavailable")
            return {"synthetic": True}

        def close(self):
            calls.append("observer_close")
            self.close_called = True
            if "observer_close" in cleanup_errors:
                raise CleanupFailure("close unavailable")

    class Stages:
        def __init__(self, *_):
            self.rows = [{"request_id": "preserved-request"}]

        def install(self, _app):
            calls.append("stages_install")
            if failure == "stages_install":
                raise primary

        def close(self):
            calls.append("stages_close")
            if "stages_close" in cleanup_errors:
                raise CleanupFailure("stage restore unavailable")

    class Client:
        def request(self, _method, path, **kwargs):
            operation = path.removeprefix("/api/v1/")
            data = {"id": 1}
            if operation == "login":
                data = {"access_token": "synthetic-only-token"}
            elif operation == "createTask":
                data = {"task": {"id": 1, "version": 1, "state": 1}}
            elif operation == "transitionTask":
                body = kwargs["json"]
                data = {
                    "task": {
                        "id": 1,
                        "version": body["expected_version"] + 1,
                        "state": 3 if body["action"] == 2 else 1,
                    }
                }
            return SimpleNamespace(
                status_code=200,
                headers={"x-request-id": "not-recorded"},
                json=lambda: {"data": data},
            )

    class Fixture:
        def __next__(self):
            if failure == "fixture_next":
                raise primary
            return (
                Client(),
                object(),
                object(),
                object(),
                {"manager": 1, "developer": 2, "reviewer": 3},
            )

        def close(self):
            calls.append("fixture_close")
            if "fixture_close" in cleanup_errors:
                raise CleanupFailure("fixture close unavailable")

    observer, fixture = Observer(), Fixture()

    def create_fixture(_):
        if failure == "fixture_create":
            raise primary
        return fixture

    monkeypatch.setattr(driver, "Stages", Stages)
    monkeypatch.setattr(driver, "observer_from", lambda _: observer if observer_requested else None)
    monkeypatch.setattr(driver, "fixture", create_fixture)
    return SimpleNamespace(
        driver=driver,
        observer=observer,
        fixture=fixture,
        report={},
        calls=calls,
        args=SimpleNamespace(
            samples=0, db_observer=Path("synthetic-observer") if observer_requested else None
        ),
        primary=primary,
    )


@pytest.mark.parametrize("failure", ["fixture_create", "fixture_next"])
def test_preinstall_fixture_failure_preserves_primary_and_closes_observer(monkeypatch, failure):
    h = harness(monkeypatch, failure=failure)
    with pytest.raises(PrimaryFailure) as caught:
        h.driver.run(h.args, Path.cwd(), h.report)
    assert caught.value is h.primary
    assert h.observer.close_called
    assert h.report["requests"] == [{"request_id": "preserved-request"}]
    assert h.report["database_observer"]["status"] == "NOT_INSTALLED"
    assert "observer_snapshot" not in h.calls


def test_partial_install_failure_still_closes_without_snapshot(monkeypatch):
    h = harness(monkeypatch, failure="install")
    with pytest.raises(PrimaryFailure) as caught:
        h.driver.run(h.args, Path.cwd(), h.report)
    assert caught.value is h.primary
    assert h.observer.close_called
    assert h.report["database_observer"]["status"] == "NOT_INSTALLED"
    assert "observer_snapshot" not in h.calls


def test_observer_construction_failure_is_requested_but_not_installed(monkeypatch):
    h = harness(monkeypatch)

    def fail(_args):
        raise h.primary

    monkeypatch.setattr(h.driver, "observer_from", fail)
    with pytest.raises(PrimaryFailure) as caught:
        h.driver.run(h.args, Path.cwd(), h.report)
    assert caught.value is h.primary
    assert h.report["requests"] == []
    assert h.report["database_observer"]["status"] == "NOT_INSTALLED"
    assert not h.observer.close_called  # No instance was returned for run to own.


@pytest.mark.parametrize(
    "phase", ["stages_close", "fixture_close", "observer_snapshot", "observer_close"]
)
def test_cleanup_failure_cannot_turn_successful_body_into_green(monkeypatch, phase):
    h = harness(monkeypatch, cleanup_errors=(phase,))
    with pytest.raises(RuntimeError) as caught:
        h.driver.run(h.args, Path.cwd(), h.report)
    assert type(caught.value).__name__ == "DiagnosticCleanupError"
    assert h.observer.close_called
    assert h.report["requests"] == [{"request_id": "preserved-request"}]
    assert [e["phase"] for e in h.report["cleanup_errors"]] == [phase]


def test_primary_exception_remains_primary_with_multiple_cleanup_failures(monkeypatch):
    phases = ("stages_close", "fixture_close", "observer_snapshot", "observer_close")
    h = harness(monkeypatch, failure="stages_install", cleanup_errors=phases)
    with pytest.raises(PrimaryFailure) as caught:
        h.driver.run(h.args, Path.cwd(), h.report)
    assert caught.value is h.primary
    assert h.observer.close_called
    assert [e["phase"] for e in h.report["cleanup_errors"]] == list(phases)
    assert h.report["requests"] == [{"request_id": "preserved-request"}]


def test_success_closes_all_and_keeps_snapshot(monkeypatch):
    h = harness(monkeypatch)
    h.driver.run(h.args, Path.cwd(), h.report)
    assert h.observer.close_called
    assert h.report["database_observer"] == {"synthetic": True}
    assert h.report["cleanup_errors"] == []
    assert h.report["requests"] == [{"request_id": "preserved-request"}]


def test_observer_not_requested_is_distinct_from_not_installed(monkeypatch):
    h = harness(monkeypatch, observer_requested=False)
    h.driver.run(h.args, Path.cwd(), h.report)
    assert h.report["database_observer"]["status"] == "NOT_REQUESTED"
    assert "observer_close" not in h.calls
    assert h.report["cleanup_errors"] == []
