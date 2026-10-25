"""Developer tests for the single API normalization boundary, including fault semantics."""

import ast
import hashlib
import importlib
import json
from collections import Counter
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from enum import Enum, IntEnum, StrEnum
from types import SimpleNamespace

import pytest
from t44.contracts import OPERATIONS
from t44.services.common import wire
from t44.settings import Settings

probe = importlib.import_module("tmp.811_backend_size.api-wire.probe")
CLOCK = "2026-10-25T12:34:56.123456Z"


class Number(IntEnum):
    ONE = 1


class Text(StrEnum):
    PROJECT = "Synthetic Unicode 工程"


class Plain(Enum):
    PROJECT = "not-a-json-string"


def project():
    return {
        "id": Decimal("1"),
        "name": Text.PROJECT,
        "description": "Synthetic",
        "version": Number.ONE,
        "my_roles": (Number.ONE,),
        "created_by": 1,
        "created_at": datetime(2026, 10, 25, 20, 0, tzinfo=timezone(timedelta(hours=8))),
    }


def rendered(renderer, result, *, operation=None, normalize=wire):
    return probe.render(
        renderer,
        operation or OPERATIONS["getProject"],
        SimpleNamespace(request_id="synthetic-request"),
        result,
        Settings(),
        server_time=CLOCK,
        duration_ms=1.234,
        normalize=normalize,
    )


def test_exact_base_api_ast_is_restored_by_only_the_two_normalization_expressions():
    manifest = json.loads((probe.HERE / "base-render-manifest.json").read_text())
    current = ast.parse((probe.ROOT / "backend/t44/api.py").read_text())
    restored = probe.RestoreNormalization().visit(current)
    assert (
        hashlib.sha256(ast.dump(restored, include_attributes=False).encode()).hexdigest()
        == manifest["api_ast_sha256"]
    )
    assert (
        hashlib.sha256((probe.ROOT / "backend/t44/services/runtime.py").read_bytes()).hexdigest()
        == manifest["runtime_sha256"]
    )


def test_one_normalized_public_payload_is_both_validated_and_sent_with_identical_bytes():
    counts = Counter()

    def normalize(label):
        def tracked(value):
            if isinstance(value, dict) and "data" in value and "meta" in value:
                counts[label] += 1
            return wire(value)

        return tracked

    result = (200, project(), True, "synthetic-original-request")
    before = rendered(probe.baseline_renderer(), result, normalize=normalize("base"))
    after = rendered(probe.candidate_renderer(), result, normalize=normalize("candidate"))
    assert after.body == before.body
    assert after.headers == before.headers
    assert after.status_code == before.status_code == 200
    assert counts == {"base": 2, "candidate": 1}
    value = json.loads(after.body)
    assert value["data"]["created_at"] == "2026-10-25T12:00:00.000000Z"
    assert value["data"]["my_roles"] == [1]
    assert value["meta"]["replayed"] is True
    assert value["meta"]["original_request_id"] == "synthetic-original-request"


@pytest.mark.parametrize("value", [Plain.PROJECT, float("nan"), float("inf"), float("-inf")])
def test_invalid_producer_values_keep_the_same_internal_error_fallback(value):
    result = (200, {**project(), "name": value}, False, None)
    before = rendered(probe.baseline_renderer(), result)
    after = rendered(probe.candidate_renderer(), result)
    assert after.status_code == before.status_code == 500
    assert after.body == before.body
    assert after.headers == before.headers
    assert json.loads(after.body)["code"] == "INTERNAL_ERROR"


def test_missing_response_schema_still_short_circuits_before_normalization():
    counts = Counter()

    def normalize(label):
        def tracked(value):
            counts[label] += 1
            assert value["code"] == "INTERNAL_ERROR"  # Original arbitrary result must not be read.
            return wire(value)

        return tracked

    result = (418, {"arbitrary": datetime.now(UTC)}, False, None)
    before = rendered(probe.baseline_renderer(), result, normalize=normalize("base"))
    after = rendered(probe.candidate_renderer(), result, normalize=normalize("candidate"))
    assert before.body == after.body
    assert before.headers == after.headers
    assert before.status_code == after.status_code == 500
    assert counts == {"base": 1}


@pytest.mark.parametrize("schema", [{}, {"$ref": "#/components/schemas/SyntheticMissing"}])
def test_encoding_and_reference_exceptions_keep_their_original_boundaries(schema):
    operation = {"responses": {"200": {"content": {"application/json": {"schema": schema}}}}}
    result = (200, {"number": float("nan")}, False, None)
    failures = []
    for renderer in (probe.baseline_renderer(), probe.candidate_renderer()):
        with pytest.raises(Exception) as error:
            rendered(renderer, result, operation=operation)
        failures.append((type(error.value), str(error.value)))
    assert failures[0] == failures[1]


@pytest.mark.parametrize(
    "value",
    [
        {"nested": [Decimal("0.25"), (Decimal("-0.00"), datetime(2026, 10, 25, tzinfo=UTC))]},
        {"enum": Number.ONE, "text": Text.PROJECT, "tuple": (None, True, "literal")},
        {"naive": datetime(2026, 10, 25, 12, 0), "float": 1.0},
    ],
)
def test_wire_output_is_a_fixed_point_for_supported_transport_values(value):
    once = wire(value)
    twice = wire(once)
    assert json.dumps(once, ensure_ascii=False, allow_nan=False) == json.dumps(
        twice, ensure_ascii=False, allow_nan=False
    )
