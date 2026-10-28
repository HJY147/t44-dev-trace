"""Experimental response-only success predicate; every uncertain/rejected case uses original errors."""

import json
import math
import time
from collections import Counter

import fastjsonschema
from jsonschema import FormatChecker


class Unsupported(ValueError):
    pass


KEYS = {
    "type",
    "enum",
    "const",
    "minimum",
    "maximum",
    "exclusiveMinimum",
    "exclusiveMaximum",
    "minLength",
    "maxLength",
    "pattern",
    "format",
    "minItems",
    "maxItems",
    "uniqueItems",
    "items",
    "properties",
    "required",
    "additionalProperties",
    "anyOf",
    "allOf",
    "if",
    "then",
    "else",
    "multipleOf",
    "description",
    "title",
    "default",
    "examples",
    "readOnly",
    "writeOnly",
}


def graph(schema, spec):
    definitions = {}

    def visit(node, stack=()):
        if not isinstance(node, dict):
            raise Unsupported("DICT_SCHEMA_REQUIRED")
        if "$ref" in node:
            ref = node["$ref"]
            if len(node) != 1 or not isinstance(ref, str) or not ref.startswith("#/components/schemas/"):
                raise Unsupported("REF_SIBLING_OR_NONLOCAL")
            name = ref.removeprefix("#/components/schemas/")
            if name in stack or name not in spec["components"]["schemas"]:
                raise Unsupported("CYCLE_OR_UNKNOWN_REF")
            if name not in definitions:
                definitions[name] = visit(spec["components"]["schemas"][name], (*stack, name))
            return {"$ref": "#/definitions/" + name}
        if any(k not in KEYS and not k.startswith("x-") for k in node):
            raise Unsupported("UNKNOWN_KEYWORD")
        if "multipleOf" in node and not (
            type(node["multipleOf"]) is int and node["multipleOf"] > 0 or node["multipleOf"] == 0.25
        ):
            raise Unsupported("NUMERIC_MULTIPLE_NOT_ADMITTED")
        if "format" in node and node["format"] not in ("date-time", "uuid"):
            raise Unsupported("FORMAT_NOT_ADMITTED")
        if "if" in node:
            condition = node["if"]
            if (
                set(condition) - {"properties", "required"}
                or not condition.get("properties")
                or any(
                    set(v) != {"const"} or type(v["const"]) not in (int, str, bool, type(None))
                    for v in condition["properties"].values()
                )
            ):
                raise Unsupported("CONDITIONAL_NOT_LITERAL")
        result = dict(node)
        for keyword in ("items", "if", "then", "else"):
            if keyword in node:
                result[keyword] = visit(node[keyword], stack)
        if "additionalProperties" in node and type(node["additionalProperties"]) is not bool:
            result["additionalProperties"] = visit(node["additionalProperties"], stack)
        if "properties" in node:
            result["properties"] = {k: visit(v, stack) for k, v in node["properties"].items()}
        for keyword in ("allOf", "anyOf"):
            if keyword in node:
                result[keyword] = [visit(v, stack) for v in node[keyword]]
        return result

    root = visit(schema)
    return {"$schema": "http://json-schema.org/draft-07/schema#", **root, "definitions": definitions}


def json_value(value, depth=0):
    if depth > 128:
        return False
    if type(value) in (str, int, bool, type(None)):
        return True
    if type(value) is float:
        return math.isfinite(value)
    if type(value) is list:
        return all(json_value(v, depth + 1) for v in value)
    if type(value) is dict:
        return all(type(k) is str and json_value(v, depth + 1) for k, v in value.items())
    return False


class FastGate:
    def __init__(self, roots, original, spec):
        self.roots, self.original, self.spec = tuple(roots), original, spec
        self.cache, self.counts = {}, Counter()
        self.compile_cpu_seconds = 0

    def __call__(self, schema, value):
        self.counts["calls"] += 1
        if not any(schema is root for root in self.roots) or not json_value(value):
            self.counts["fallback_identity_or_value"] += 1
            return self.original(schema, value)
        try:
            compatible = graph(schema, self.spec)
            key = json.dumps(compatible, sort_keys=True, separators=(",", ":"))
            if key not in self.cache:
                before = time.thread_time()
                formats = {
                    name: (lambda value, name=name: FormatChecker().conforms(value, name))
                    for name in ("date-time", "uuid")
                }
                function = fastjsonschema.compile(
                    compatible, formats=formats, use_default=False, detailed_exceptions=True
                )
                self.compile_cpu_seconds += time.thread_time() - before
                if len(self.cache) >= 16:
                    self.cache.clear()
                self.cache[key] = function
                self.counts["compiled"] += 1
            self.cache[key](value)
        except Unsupported:
            self.counts["fallback_unsupported"] += 1
        except Exception:
            self.counts["fallback_fast_reject_or_exception"] += 1
        else:
            self.counts["fast_success"] += 1
            return []
        return self.original(schema, value)
