"""Exact error-order and nested-$id differentials against the frozen integration code."""

import json
import subprocess
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from types import ModuleType

import pytest
from t44 import api, contracts

BASE = "5868779e949adef066fe26bffbc4f2e8afee7649"
VALUES = (None, True, 0, 1, 1.0, "", "2026-10-29T00:00:00Z", [], {}, {"x": None})


@pytest.fixture(scope="module")
def original():
    source = subprocess.check_output(
        ["git", "show", BASE + ":backend/t44/contracts/__init__.py"], text=True
    )
    module = ModuleType("_final_original_contracts")
    module.__package__ = "t44.contracts"
    exec(compile(source, BASE + "/contracts.py", "exec"), module.__dict__)
    return module


def outcome(module, schema, value):
    try:
        return module.violations(schema, value), [
            (list(e.absolute_path), e.validator, list(e.absolute_schema_path))
            for e in module.validator(schema).iter_errors(value)
        ]
    except Exception as error:
        return type(error).__name__, str(error)


@pytest.mark.parametrize("name", tuple(contracts.SPEC["components"]["schemas"]))
def test_every_cached_component_keeps_all_detailed_errors_in_order(original, name):
    schema = contracts.SPEC["components"]["schemas"][name]
    for value in VALUES:
        assert outcome(contracts, schema, value) == outcome(original, schema, value)


@pytest.mark.parametrize("operation_id", tuple(contracts.OPERATIONS))
def test_api_body_selection_and_all_cached_response_shapes(original, operation_id):
    operation = contracts.OPERATIONS[operation_id]
    for response in operation["responses"].values():
        schema = response.get("content", {}).get("application/json", {}).get("schema")
        if schema is not None:
            for value in VALUES:
                assert outcome(contracts, schema, value) == outcome(original, schema, value)
    if "requestBody" in operation:
        schema = operation["requestBody"]["content"]["application/json"]["schema"]
        for value in (*VALUES, *({"action": n} for n in range(1, 10))):
            selected = api._body_schema(schema, value)
            assert outcome(contracts, selected, value) == outcome(original, selected, value)


@pytest.mark.parametrize(
    "schema",
    [
        {"$ref": "#/components/schemas/TaskState"},
        {"$id": "urn:final:inline", "$ref": "#/components/schemas/TaskState"},
        {
            "$id": "urn:final:inline",
            "type": "object",
            "properties": {"state": {"$ref": "#/components/schemas/TaskState"}},
        },
        {
            "type": "object",
            "properties": {
                "state": {"$id": "urn:final:nested", "$ref": "#/components/schemas/TaskState"}
            },
        },
        {
            "oneOf": [
                {"$ref": "#/components/schemas/TaskState"},
                {"type": "object", "required": ["a", "b"], "additionalProperties": False},
            ]
        },
    ],
)
def test_ad_hoc_relative_refs_root_and_nested_ids_oneof_are_unchanged(original, schema):
    before = json.dumps(schema)
    for value in (*VALUES, {"state": 1}, {"state": "bad"}, {"a": 1, "b": 2, "c": 3}):
        assert outcome(contracts, schema, value) == outcome(original, schema, value)
    assert json.dumps(schema) == before


def test_large_errors_mutable_dynamic_schema_and_parallel_frozen_calls(original):
    schema = {"type": "object", "properties": {str(n): {"type": "integer"} for n in range(120)}}
    value = {str(n): "bad" for n in range(120)}
    assert outcome(contracts, schema, value) == outcome(original, schema, value)
    assert len(contracts.violations(schema, value)) == 100
    schema["properties"]["0"]["type"] = "string"
    assert outcome(contracts, schema, value) == outcome(original, schema, value)
    state = contracts.SPEC["components"]["schemas"]["TaskState"]
    values = list(VALUES) * 100
    expected = [original.violations(state, value) for value in values]
    with ThreadPoolExecutor(max_workers=8) as pool:
        actual = list(pool.map(lambda value: contracts.violations(state, value), values))
    assert actual == expected


def test_frozen_schema_reuses_prepared_validator_but_arbitrary_schema_does_not(monkeypatch):
    schema = contracts.SPEC["components"]["schemas"]["TaskState"]
    original = contracts.validator
    calls = []

    def count(candidate):
        calls.append(candidate)
        return original(candidate)

    monkeypatch.setattr(contracts, "validator", count)
    for value in VALUES:
        contracts.violations(schema, value)
    assert not calls
    for value in VALUES:
        contracts.violations(deepcopy(schema), value)
    assert len(calls) == len(VALUES)


def test_frozen_error_iterator_stops_at_exact_hundred_without_changing_prefix(
    original, monkeypatch
):
    schema = contracts.SPEC["components"]["schemas"]["EvidenceRefs"]
    value = [None] * 500
    expected = original.violations(schema, value)
    assert len(expected) == 100
    prepared = contracts._COMPILED[id(schema)]
    old = type(prepared).iter_errors
    emitted = []

    def tracked(self, instance, *args, **kwargs):
        for error in old(self, instance, *args, **kwargs):
            if self is prepared:
                emitted.append(error)
            yield error

    monkeypatch.setattr(type(prepared), "iter_errors", tracked)
    assert contracts.violations(schema, value) == expected
    assert len(emitted) == 100


def test_dynamic_invalid_reference_after_many_errors_retains_original_exception(original):
    schema = {
        "type": "object",
        "properties": {str(n): {"type": "integer"} for n in range(150)},
        "allOf": [{"$ref": "#/missing-root"}],
    }
    value = {str(n): "bad" for n in range(150)}
    assert outcome(contracts, schema, value) == outcome(original, schema, value)
    assert isinstance(outcome(contracts, schema, value)[0], str)
