"""Frozen request/response contract used by the running API."""

import json
from importlib.resources import files
from itertools import islice

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012

from t44.diagnostics import measured

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


_COMPILED = {}


@measured("schema.validate")
def violations(schema, value):
    entry = _COMPILED.get(id(schema))
    prepared = entry[1] if entry is not None and entry[0] is schema else None
    errors = (prepared if prepared is not None else validator(schema)).iter_errors(value)
    bounded = islice(errors, 100) if prepared is not None else list(errors)[:100]
    return [
        {
            "path": "/" + "/".join(map(str, error.absolute_path)),
            "rule": str(error.validator),
            "message": f"Does not satisfy {error.validator}",
        }
        for error in bounded
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


# Only identity-locked frozen inputs are shared. Dynamic schemas retain the original
# constructor and reference-context behavior, including arbitrary root/nested $id.
for schema in (
    *SPEC["components"]["schemas"].values(),
    *(parameter["schema"] for parameter in SPEC["components"]["parameters"].values()),
    *(operation["data_schema"] for operation in OPERATIONS.values()),
    *(
        response["content"]["application/json"]["schema"]
        for operation in OPERATIONS.values()
        for response in operation["responses"].values()
    ),
):
    _COMPILED[id(schema)] = (schema, validator(schema))
