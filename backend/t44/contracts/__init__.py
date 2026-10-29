"""Frozen request/response contract used by the running API."""

import json
from functools import lru_cache
from importlib.resources import files

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012

SPEC = json.loads(files(__package__).joinpath("openapi.json").read_text())
FROZEN_ERROR_NAMES = tuple(SPEC["components"]["schemas"]["ErrorCode"]["enum"])
VERSION = SPEC["info"]["version"]
_URI = "urn:t44:api"
_REGISTRY = Registry().with_resource(
    _URI, Resource.from_contents(SPEC, default_specification=DRAFT202012)
)


def validator(schema):
    return Draft202012Validator(
        {"$id": "urn:t44:validation", **_absolute_refs(schema)},
        registry=_REGISTRY,
        format_checker=FormatChecker(),
    )


def _absolute_refs(value):
    if isinstance(value, dict):
        return {
            key: _URI + item if key == "$ref" and item.startswith("#/") else _absolute_refs(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_absolute_refs(item) for item in value]
    return value


def _shape(value):
    if type(value) is dict:
        return dict, tuple((_shape(key), _shape(item)) for key, item in value.items())
    if type(value) is list:
        return list, tuple(map(_shape, value))
    if type(value) in (str, int, float, bool, type(None)):
        return type(value), value
    raise TypeError("Non-native schema value")


def _unshape(key):
    kind, value = key
    if kind is dict:
        return {_unshape(name): _unshape(item) for name, item in value}
    return list(map(_unshape, value)) if kind is list else value


@lru_cache(maxsize=128)
def _compiled(schema, checkers):
    result = validator(_unshape(schema))
    result.format_checker.checkers = dict(checkers)
    return result


def _validation_instance(schema):
    try:
        key, checkers = _shape(schema), tuple(FormatChecker.checkers.items())
        hash((key, checkers))
    except (TypeError, RecursionError):
        return validator(schema)
    return _compiled(key, checkers)


def violations(schema, value):
    return [
        {
            "path": "/" + "/".join(map(str, error.absolute_path)),
            "rule": str(error.validator),
            "message": f"Does not satisfy {error.validator}",
        }
        for error in list(_validation_instance(schema).iter_errors(value))[:100]
    ]


def normalized(value):
    if isinstance(value, dict):
        return {key: normalized(item) for key, item in value.items()}
    if isinstance(value, list):
        return [normalized(item) for item in value]
    return int(value) if isinstance(value, float) and value.is_integer() else value


OPERATIONS = {
    operation["operationId"]: {"path": path, "method": method, **operation}
    for path, methods in SPEC["paths"].items()
    for method, operation in methods.items()
}

# Resolve each success payload once; both pre-commit validation and HTTP use this contract.
for operation in OPERATIONS.values():
    status = next(code for code in operation["responses"] if code.startswith("2"))
    schema = operation["responses"][status]["content"]["application/json"]["schema"]
    data = SPEC["components"]["schemas"][schema["$ref"].split("/")[-1]]["properties"]["data"]
    operation["success_status"] = int(status)
    operation["data_schema"] = data
    operation["data_fields"] = (
        SPEC["components"]["schemas"][data["$ref"].split("/")[-1]] if "$ref" in data else data
    )["properties"]
