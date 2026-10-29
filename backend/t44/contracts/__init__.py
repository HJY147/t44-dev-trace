"""Frozen request/response contract used by the running API."""

import json
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
_ROOT_VALIDATOR = Draft202012Validator(
    {"$id": _URI, **SPEC}, registry=_REGISTRY, format_checker=FormatChecker()
)


def validator(schema):
    return _ROOT_VALIDATOR.evolve(schema=schema)


def resolve(schema):
    while "$ref" in schema:
        schema = _REGISTRY.resolver(_URI).lookup(schema["$ref"]).contents
    return schema


def violations(schema, value):
    return [
        {
            "path": "/" + "/".join(map(str, error.absolute_path)),
            "rule": str(error.validator),
            "message": f"Does not satisfy {error.validator}",
        }
        for error in list(validator(schema).iter_errors(value))[:100]
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
    data = resolve(schema)["properties"]["data"]
    operation["success_status"] = int(status)
    operation["data_schema"] = data
    operation["data_fields"] = resolve(data)["properties"]
