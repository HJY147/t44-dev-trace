"""Pure developer differential checks; no HTTP, database, independent cases or cloud."""

import importlib.util
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
from t44 import contracts


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


HERE = Path(__file__).parent
PROTOTYPE = load(HERE / "834_reference_experiment.py", "reference_experiment")
SAMPLES = load(HERE.parent / "backend/870_validator_profile.py", "public_old_synthetic_samples")


def signature(factory, schema, value):
    try:
        errors = list(factory(schema).iter_errors(value))
    except Exception as error:
        return {"exception": type(error).__module__ + "." + type(error).__name__}
    return {
        "errors": [
            {
                "path": "/" + "/".join(map(str, error.absolute_path)),
                "rule": str(error.validator),
                "message": f"Does not satisfy {error.validator}",
                "evidence_only": (
                    error.validator == "minItems"
                    and error.instance == []
                    and list(error.absolute_path)[-1:] == ["evidence"]
                )
                or (
                    error.validator == "required"
                    and isinstance(error.instance, dict)
                    and set(error.validator_value) - set(error.instance) == {"evidence"}
                ),
            }
            for error in errors[:100]
        ],
        "uncapped_count": len(errors),
    }


EXTRA = [
    ("ref-sibling-maximum", {"$ref": "#/components/schemas/Id", "maximum": 5}, 6),
    ("sibling-order", {"maximum": 5, "$ref": "#/components/schemas/Id"}, True),
    ("annotation-sibling", {"$ref": "#/components/schemas/Id", "description": "diagnostic"}, 0),
    ("explicit-id", {"$id": "urn:diagnostic:scope", "type": "integer"}, True),
    (
        "explicit-draft",
        {"$schema": "https://json-schema.org/draft/2020-12/schema", "type": "integer"},
        True,
    ),
    ("anchor", {"$anchor": "diagnostic", "type": "integer"}, True),
    (
        "dynamic-ref",
        {"$defs": {"i": {"$dynamicAnchor": "i", "type": "integer"}}, "$dynamicRef": "#i"},
        True,
    ),
    (
        "unevaluated",
        {"properties": {"x": {"type": "integer"}}, "unevaluatedProperties": False},
        {"y": 1},
    ),
    ("urn-unknown", {"$ref": "urn:diagnostic:missing"}, 1),
    ("invalid-uuid", {"type": "string", "format": "uuid"}, "invalid"),
    ("boolean-schema", True, 1),
    ("nonstring-ref", {"$ref": True}, 1),
    (
        "nested-pure-refs",
        {"type": "array", "items": {"$ref": "#/components/schemas/Id"}},
        [1, True, 3],
    ),
]
CASES = [(case["name"], case["schema"], case["value"]) for case in SAMPLES.cases()] + EXTRA


@pytest.mark.parametrize("name,schema,value", CASES, ids=[case[0] for case in CASES])
def test_contract_error_surface_matches_original(name, schema, value):
    candidate = PROTOTYPE.factory(contracts.validator, contracts.SPEC)
    before = json.dumps({"schema": schema, "value": value, "spec": contracts.SPEC}, sort_keys=True)
    assert signature(candidate, schema, value) == signature(contracts.validator, schema, value), (
        name
    )
    assert (
        json.dumps({"schema": schema, "value": value, "spec": contracts.SPEC}, sort_keys=True)
        == before
    )


def test_per_call_expansion_observes_component_mutation_without_cross_request_cache(monkeypatch):
    schema = {"$ref": "#/components/schemas/Id"}
    candidate = PROTOTYPE.factory(contracts.validator, contracts.SPEC)
    assert signature(candidate, schema, 8) == signature(contracts.validator, schema, 8)
    monkeypatch.setitem(contracts.SPEC["components"]["schemas"]["Id"], "maximum", 7)
    assert signature(candidate, schema, 8) == signature(contracts.validator, schema, 8)
    assert signature(candidate, schema, 8)["errors"][0]["rule"] == "maximum"


def test_recursive_component_falls_back_without_expansion_recursion(monkeypatch):
    schema = {"$ref": "#/components/schemas/DiagnosticRecursive"}
    monkeypatch.setitem(
        contracts.SPEC["components"]["schemas"],
        "DiagnosticRecursive",
        {
            "type": "object",
            "required": ["next"],
            "additionalProperties": False,
            "properties": {"next": {"anyOf": [schema, {"type": "null"}]}},
        },
    )
    candidate = PROTOTYPE.factory(contracts.validator, contracts.SPEC)
    for value in ({"next": {"next": None}}, {"next": {"next": True}}):
        assert signature(candidate, schema, value) == signature(contracts.validator, schema, value)


def test_parallel_calls_use_distinct_local_expansion_state():
    candidate = PROTOTYPE.factory(contracts.validator, contracts.SPEC)
    schema = {"$ref": "#/components/schemas/TaskCreate"}
    valid = next(case["value"] for case in SAMPLES.cases() if case["name"] == "task-valid")
    values = [valid, {**valid, "owner_id": True}] * 16
    expected = [signature(contracts.validator, schema, value) for value in values]
    with ThreadPoolExecutor(max_workers=4) as pool:
        actual = list(pool.map(lambda value: signature(candidate, schema, value), values))
    assert actual == expected
