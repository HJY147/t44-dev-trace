"""Exact baseline differential checks for the R30 contract-context candidate."""

import json
import subprocess
from types import ModuleType

import pytest
from t44 import api, contracts

BASE = "7374b3637b06465d448fc2e81952ba18fc676315"
VALUES = (None, True, 0, 1, 1.0, "", "2026-10-29T00:00:00Z", [], {}, {"x": None})


def baseline(path, name, package):
    source = subprocess.check_output(["git", "show", f"{BASE}:{path}"], text=True)
    module = ModuleType(name)
    module.__package__ = package
    exec(compile(source, f"{BASE}/{path}", "exec"), module.__dict__)
    return module


@pytest.fixture(scope="module")
def original():
    return baseline("backend/t44/contracts/__init__.py", "_r30_contracts", "t44.contracts")


@pytest.fixture(scope="module")
def original_api(original):
    module = baseline("backend/t44/api.py", "_r30_api", "t44")
    module.validator, module.violations = original.validator, original.violations
    return module


def errors(module, schema, value):
    try:
        detailed = [
            (list(error.absolute_path), error.validator, list(error.absolute_schema_path))
            for error in module.validator(schema).iter_errors(value)
        ]
        return module.violations(schema, value), detailed
    except Exception as error:
        return type(error).__name__, str(error)


@pytest.mark.parametrize("name", tuple(contracts.SPEC["components"]["schemas"]))
def test_every_frozen_schema_preserves_error_order(original, name):
    schema = {"$ref": f"#/components/schemas/{name}"}
    for value in VALUES:
        assert errors(contracts, schema, value) == errors(original, schema, value)


@pytest.mark.parametrize("operation_id", tuple(contracts.OPERATIONS))
def test_operation_metadata_parameter_resolution_and_body_selection(
    original, original_api, operation_id
):
    operation = contracts.OPERATIONS[operation_id]
    assert operation == original.OPERATIONS[operation_id]
    parameters = [contracts.resolve(item) for item in operation.get("parameters", [])]
    assert parameters == original_api._parameters(operation)
    for parameter in parameters:
        assert contracts.resolve(parameter["schema"]).get("type") == original_api._schema_type(
            parameter["schema"]
        )
    if "requestBody" in operation:
        schema = operation["requestBody"]["content"]["application/json"]["schema"]
        for value in (*VALUES, *({"action": action} for action in range(1, 10))):
            selected = api._body_schema(schema, value)
            old = original_api._body_schema(schema, value)
            assert selected == old
            assert errors(contracts, selected, value) == errors(original, old, value)


@pytest.mark.parametrize(
    "schema",
    [
        {"$ref": "#/components/schemas/TaskState"},
        {"$id": "urn:r30:inline", "$ref": "#/components/schemas/TaskState"},
        {
            "$id": "urn:r30:inline",
            "type": "object",
            "properties": {"state": {"$ref": "#/components/schemas/TaskState"}},
        },
        {
            "type": "object",
            "properties": {
                "state": {
                    "$id": "urn:r30:nested",
                    "$ref": "#/components/schemas/TaskState",
                }
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
def test_relative_references_ids_oneof_and_detailed_violations(original, schema):
    for value in (*VALUES, {"state": 1}, {"state": "bad"}, {"a": 1, "b": 2, "c": 3}):
        assert errors(contracts, schema, value) == errors(original, schema, value)


def test_large_violation_list_retains_first_hundred_and_schema_input(original):
    schema = {
        "type": "object",
        "properties": {str(index): {"type": "integer"} for index in range(120)},
    }
    original_bytes = json.dumps(schema, ensure_ascii=False)
    value = {str(index): "bad" for index in range(120)}
    assert errors(contracts, schema, value) == errors(original, schema, value)
    assert len(contracts.violations(schema, value)) == 100
    assert json.dumps(schema, ensure_ascii=False) == original_bytes
