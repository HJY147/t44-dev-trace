"""Development differential checks against the exact original Git blob, not acceptance."""

import importlib.util
import subprocess
import types
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from importlib.metadata import version
from pathlib import Path

import pytest
from jsonschema import FormatChecker
from t44 import api, contracts
from t44.services import application as business_module

ROOT = Path(__file__).resolve().parents[2]
BASE = "f7cdb5fa3b19f84d8ab0d0b042bf51a5b8484e8f"


def source_module(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


original = types.ModuleType("original774")
original.__package__ = "t44.contracts"
blob = subprocess.check_output(
    ["git", "show", f"{BASE}:backend/t44/contracts/__init__.py"], cwd=ROOT
)
exec(compile(blob, "<f7-contracts>", "exec"), original.__dict__)
samples = source_module("samples774", "tmp/backend/870_validator_profile.py").cases()
helpers = source_module("helpers774", "tmp/backend/contracts/986_http.py")
application = source_module("fixture774", "tmp/backend/contracts/conftest.py").application


def outcome(function, schema, value):
    try:
        return "result", function(schema, value)
    except Exception as error:
        return "exception", type(error).__module__, type(error).__name__, str(error)


def same(schema, value):
    assert outcome(contracts.violations, schema, value) == outcome(
        original.violations, schema, value
    )


def test_exact_versions_and_original_assets():
    assert version("jsonschema") == "4.26.0"
    assert version("referencing") == "0.37.0"
    assert version("attrs") == "26.1.0"
    assert original.SPEC == contracts.SPEC
    assert original.FROZEN_ERROR_NAMES == contracts.FROZEN_ERROR_NAMES


@pytest.mark.parametrize("case", samples, ids=lambda case: case["name"])
def test_existing_synthetic_samples_differential(case):
    same(case["schema"], case["value"])


@pytest.mark.parametrize("name", list(contracts.SPEC["components"]["schemas"]))
def test_all_frozen_components_on_boundary_values(name):
    schema = {"$ref": f"#/components/schemas/{name}"}
    for value in (None, True, 0, 1, 1.0, "", "2026-02-30T00:00:00Z", [], {}):
        same(schema, value)


def test_keyword_and_property_order_and_error_limit():
    schema = {
        "required": ["z"],
        "properties": {"b": {"type": "integer"}, "a": {"type": "integer"}},
        "additionalProperties": False,
    }
    first = contracts.violations(schema, {"a": True, "b": False, "extra": 1})
    reversed_schema = dict(reversed(list(schema.items())))
    second = contracts.violations(reversed_schema, {"a": True, "b": False, "extra": 1})
    same(schema, {"a": True, "b": False, "extra": 1})
    same(reversed_schema, {"a": True, "b": False, "extra": 1})
    assert first != second
    many = {"type": "array", "items": {"type": "integer"}}
    assert len(contracts.violations(many, [True] * 105)) == 100
    same(many, [True] * 105)


def test_schema_mutation_and_public_instances_are_isolated():
    schema = {"type": "integer", "minimum": 1}
    assert not contracts.violations(schema, 1)
    schema["minimum"] = 2
    assert contracts.violations(schema, 1)
    same(schema, 1)
    one, two = contracts.validator(schema), contracts.validator(schema)
    assert one is not two and one.schema is not two.schema
    one.schema["minimum"] = 99
    one.format_checker.checkers.clear()
    assert not list(two.iter_errors(3))
    assert not contracts.violations(schema, 3)
    nested = {"properties": {"x": {"type": "integer"}}}
    prior = contracts.validator(nested)
    nested["properties"]["x"]["type"] = "string"
    assert not list(prior.iter_errors({"x": 1}))
    same(nested, {"x": 1})


def test_dynamic_format_registration_replacement_and_removal(monkeypatch):
    registry = dict(FormatChecker.checkers)
    monkeypatch.setattr(FormatChecker, "checkers", registry)
    schema = {"format": "t44-test-774"}
    assert not contracts.violations(schema, "bad")
    registry["t44-test-774"] = (lambda value: value == "good", ())
    assert contracts.violations(schema, "bad")
    same(schema, "bad")
    registry["t44-test-774"] = (lambda value: value == "bad", ())
    assert not contracts.violations(schema, "bad")
    del registry["t44-test-774"]
    assert not contracts.violations(schema, "bad")


def test_all_errors_and_format_checks_still_run_on_every_value(monkeypatch):
    calls = []
    registry = dict(FormatChecker.checkers)
    registry["t44-count-774"] = (lambda value: calls.append(value) or False, ())
    monkeypatch.setattr(FormatChecker, "checkers", registry)
    schema = {"type": "array", "items": {"format": "t44-count-774"}}
    for _ in range(2):
        assert len(contracts.violations(schema, ["x"] * 105)) == 100
    assert calls == ["x"] * 210


def test_referenced_spec_mutation_remains_visible(monkeypatch):
    schema = {"$ref": "#/components/schemas/Id"}
    assert not contracts.violations(schema, 2)
    for module in (original, contracts):
        monkeypatch.setitem(module.SPEC["components"]["schemas"]["Id"], "minimum", 10)
    assert contracts.violations(schema, 2)
    same(schema, 2)


@pytest.mark.parametrize(
    "schema,value",
    [
        ({"enum": (1, 2)}, 1),
        ({"enum": {1, 2}}, 3),
        ({"type": "string", "pattern": "["}, "x"),
        ({"$ref": "#/components/schemas/DoesNotExist"}, {}),
        (
            {
                "$id": "urn:t44:other",
                "$defs": {"x": {"$anchor": "x", "type": "integer"}},
                "$ref": "#x",
            },
            True,
        ),
    ],
)
def test_non_native_schemas_and_exceptions_preserve_original(schema, value):
    same(schema, value)


def test_cached_validation_is_read_only_and_bounded_under_concurrency():
    contracts._compiled.cache_clear()
    schema = {"type": "array", "items": {"$ref": "#/components/schemas/Id"}}
    stable = deepcopy(schema)
    instance = contracts._validation_instance(schema)
    before = deepcopy(instance.schema)
    resolver, registry = instance._resolver, instance._registry
    one, two = instance.iter_errors([True, True]), instance.iter_errors([1, 2])
    assert next(one).path[0] == 0
    assert list(two) == []
    assert [list(error.path) for error in one] == [[1]]
    jobs = [samples[index % len(samples)] for index in range(760)]
    expected = [outcome(original.violations, c["schema"], c["value"]) for c in jobs]
    with ThreadPoolExecutor(max_workers=12) as pool:
        actual = list(
            pool.map(lambda c: outcome(contracts.violations, c["schema"], c["value"]), jobs)
        )
    assert actual == expected
    assert schema == stable and instance.schema == before
    assert instance._resolver is resolver and instance._registry is registry
    for index in range(300):
        same({"type": "integer", "minimum": index}, index)
    info = contracts._compiled.cache_info()
    assert info.maxsize == 128 and info.currsize == 128 and info.hits > 0


def test_http_success_runs_both_layers_on_every_request(application, monkeypatch):
    client, _ = application
    token = helpers.login(client)
    inner, outer = [], []
    actual = contracts.violations

    def inner_check(schema, value):
        inner.append(schema)
        return actual(schema, value)

    def outer_check(schema, value):
        outer.append(schema)
        return actual(schema, value)

    monkeypatch.setattr(business_module, "violations", inner_check)
    monkeypatch.setattr(api, "violations", outer_check)
    operation = contracts.OPERATIONS["createProject"]
    response_schema = operation["responses"]["201"]["content"]["application/json"]["schema"]
    for index in range(2):
        helpers.request(
            client, "createProject", token=token, body={"name": f"774-{index}"}, expect=201
        )
    assert sum(item is operation["data_schema"] for item in inner) == 2
    assert sum(item is response_schema for item in outer) == 2


def test_http_invalid_data_rolls_back_before_commit(application, monkeypatch):
    client, factory = application
    token = helpers.login(client)
    business = client.app.state.runtime.business
    original_create = business.createProject

    def invalid_result(gateway, call):
        result = original_create(gateway, call)
        result["id"] = True
        return result

    monkeypatch.setattr(business, "createProject", invalid_result)
    response = helpers.request(
        client, "createProject", token=token, body={"name": "774-invalid"}, expect=500
    )
    assert response.json()["code"] == "INTERNAL_ERROR"
    with factory() as uow:
        assert uow.gateway.rows("projects", {}) == []
