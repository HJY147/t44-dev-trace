"""Design-only OpenAPI/annotation checks. Does not call HTTP or a database."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker
from openapi_spec_validator import validate
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012


ROOT = Path(__file__).resolve().parents[2]
SPEC_PATH = ROOT / "specs/contracts/openapi.json"
SPEC = json.loads(SPEC_PATH.read_text())
SCHEMAS = SPEC["components"]["schemas"]
URI = "urn:t44:contract-design-v2"
REGISTRY = Registry().with_resource(
    URI, Resource.from_contents(SPEC, default_specification=DRAFT202012)
)
FAILURES: list[str] = []
CHECKS = 0


def check(condition: bool, label: str) -> None:
    global CHECKS
    CHECKS += 1
    if not condition:
        FAILURES.append(label)


def validator(name: str) -> Draft202012Validator:
    return Draft202012Validator(
        {"$ref": URI + "#/components/schemas/" + name},
        registry=REGISTRY,
        format_checker=FormatChecker(),
    )


GENERIC = {
    "AUTH_REQUIRED", "INVALID_CREDENTIALS", "TOKEN_EXPIRED", "TOKEN_REVOKED",
    "PROJECT_ACCESS_DENIED", "ACTION_FORBIDDEN", "SERVICE_SCOPE_REQUIRED",
    "RESOURCE_NOT_FOUND", "PARAMETER_INVALID", "INVALID_JSON",
    "SECURITY_INPUT_REJECTED", "AUDIT_UNAVAILABLE", "DEPENDENCY_UNAVAILABLE",
    "TRANSACTION_UNCERTAIN", "RATE_LIMITED", "PAYLOAD_TOO_LARGE", "INTERNAL_ERROR",
}
IDEMPOTENT = {"IDEMPOTENCY_CONTENT_CONFLICT", "IDEMPOTENCY_IN_PROGRESS"}
HTTP_CODES = {
    "400": {"INVALID_JSON", "SECURITY_INPUT_REJECTED"},
    "401": {"AUTH_REQUIRED", "INVALID_CREDENTIALS", "TOKEN_EXPIRED", "TOKEN_REVOKED"},
    "403": {"PROJECT_ACCESS_DENIED", "ACTION_FORBIDDEN", "SERVICE_SCOPE_REQUIRED"},
    "404": {"RESOURCE_NOT_FOUND"},
    "409": {"STATE_CONFLICT", "VERSION_CONFLICT", *IDEMPOTENT,
            "DEPENDENCIES_UNSATISFIED", "DEPENDENCY_CYCLE", "DEPENDENCY_EDIT_LOCKED",
            "ASSIGNMENT_EDIT_LOCKED", "REVIEW_NOT_PASSED", "REVIEW_BASELINE_MISMATCH",
            "RELEASE_APPROVAL_REQUIRED", "ASSESSMENT_BASELINE_MISMATCH", "LAST_MANAGER",
            "MEMBER_IN_USE", "NOT_ELIGIBLE_FOR_ESCALATION", "SCHEDULE_VERSION_CONFLICT",
            "RULE_VERSION_CONFLICT"},
    "413": {"PAYLOAD_TOO_LARGE"},
    "422": {"PARAMETER_INVALID", "DEPENDENCY_SELF_REFERENCE", "EVIDENCE_REQUIRED",
            "OWNER_NOT_PROJECT_DEVELOPER", "ACCOUNT_NOT_INITIALIZED", "TIME_RANGE_INVALID",
            "CAPACITY_REFERENCE_INVALID", "CONTRACT_INVALID"},
    "429": {"RATE_LIMITED"},
    "503": {"AUDIT_UNAVAILABLE", "DEPENDENCY_UNAVAILABLE", "TRANSACTION_UNCERTAIN"},
    "500": {"INTERNAL_ERROR"},
}


def annotations(path: str, method: str, operation: dict) -> None:
    oid = operation["operationId"]
    business = operation.get("x-business-error-codes", [])
    responses = operation["responses"]
    allowed: set[str] = set()
    for status, response in responses.items():
        if status.startswith("2"):
            continue
        codes = response.get("x-error-codes", [])
        check(bool(codes) and len(codes) == len(set(codes)), f"C4 {oid}/{status}: code list")
        check(set(codes) <= HTTP_CODES[status], f"C4 {oid}/{status}: wrong HTTP status")
        all_of = response["content"]["application/json"]["schema"].get("allOf", [])
        restrictions = [part["properties"]["code"]["enum"] for part in all_of
                        if "code" in part.get("properties", {})]
        check(len(restrictions) == 1 and set(restrictions[0]) == set(codes),
              f"C4 {oid}/{status}: response schema differs from annotation")
        allowed.update(codes)
    check(set(business) == allowed - GENERIC, f"C4 {oid}: business/response drift")
    check(len(business) == len(set(business)), f"C4 {oid}: duplicate business code")
    cases = operation.get("x-error-cases", [])
    pair_list = [(str(case.get("http_status")), case.get("code")) for case in cases]
    declared = {(status, code) for status, response in responses.items()
                if not status.startswith("2") for code in response.get("x-error-codes", [])}
    check(len(pair_list) == len(set(pair_list)) and set(pair_list) == declared,
          f"C4 {oid}: trigger conditions do not cover exactly declared errors")
    check(all(len(case.get("condition", "").strip()) >= 8 for case in cases),
          f"C4 {oid}: missing concrete trigger")
    readonly = method == "get" or oid == "validateContractPayload"
    header_count = sum(parameter.get("$ref", "").endswith("/IdempotencyKey")
                       for parameter in operation.get("parameters", []))
    if readonly:
        check(not (set(business) | allowed) & IDEMPOTENT,
              f"C4 {oid}: read-only idempotency error")
        check(header_count == 0, f"C4 {oid}: read-only idempotency header")
    if not header_count:
        check(not allowed & IDEMPOTENT, f"C4 {oid}: idempotency error without key")
    if "project_id" not in path and oid != "listMyNotifications":
        check("PROJECT_ACCESS_DENIED" not in allowed, f"C4 {oid}: no project scope")
        check("RESOURCE_NOT_FOUND" not in allowed, f"C4 {oid}: no resource selector")
    if oid in {"getMe", "getDictionaries"}:
        check("422" not in responses, f"C4 {oid}: no typed input to reject as 422")


print("Command: .venv/bin/python agents/backend/validate_contract_design_v2.py", flush=True)
try:
    validate(SPEC)
    print("OpenAPI 3.1 normative validation: PASS")
except Exception as error:
    FAILURES.append(f"OpenAPI normative validation: {type(error).__name__}: {error}")

# C2: one owner plus 100 different managers, including the actual nested result types.
event = {
    "id": 1, "task_id": 1, "project_id": 1, "schedule_version": 1, "rule_version": 1,
    "level": 2, "recipient_ids": list(range(1, 102)), "disposition": 1,
    "scan_run_id": "00000000-0000-4000-8000-000000000001",
    "created_at": "2026-10-23T06:00:00Z", "handled_count": 101,
}
meta = {"request_id": "current-request", "server_time": "2026-10-23T06:00:00Z",
        "contract_version": "0.1.0-draft", "replayed": False, "original_request_id": None}
accepted = {"event": event, "created": True, "audit_id": 1, "task_version": 2}
for name, payload in (
    ("EscalationEvent", event), ("EscalationAccepted", accepted),
    ("EscalationEnvelope", {"data": accepted, "meta": meta}),
    ("EscalationPageEnvelope", {"data": {"items": [event], "page": 1,
                                         "page_size": 20, "total": 1}, "meta": meta}),
):
    check(validator(name).is_valid(payload), f"C2 {name}: 101 recipients/handled rejected")
recipients = SCHEMAS["EscalationEvent"]["properties"]["recipient_ids"]
handled = SCHEMAS["EscalationEvent"]["properties"]["handled_count"]
check("maxItems" not in recipients, "C2 recipient list must not truncate managers")
counter = Draft202012Validator(handled)
check(counter.is_valid(4294967295), "C2 handled_count UINT32 max")
check(not counter.is_valid(4294967296), "C2 handled_count overflow rejection")

# C3: FormatChecker is active; Plan/TaskCreate/read-only candidate share the same domain.
times = [("0001-01-01T00:00:00Z", False), ("0999-12-31T23:59:59.999999Z", False),
         ("1000-01-01T00:00:00Z", True), ("9999-12-31T23:59:59.999999Z", True),
         ("2026-10-23T00:00:00.1234567Z", False), ("10000-01-01T00:00:00Z", False),
         ("2026-10-23T08:00:00+08:00", False), ("2026-99-23T00:00:00Z", False)]
for value, expected in times:
    check(validator("UtcTime").is_valid(value) == expected, f"C3 shared UtcTime {value}")
for year, expected in [("0001", False), ("0999", False), ("1000", True), ("9999", True)]:
    plan = {"planned_start": year + "-01-01T00:00:00Z",
            "planned_end": year + "-01-02T00:00:00.999999Z",
            "estimated_hours": 1, "buffer_hours": 0, "delay_contingency": "合成边界示例"}
    ordered = datetime.fromisoformat(plan["planned_start"]) < datetime.fromisoformat(plan["planned_end"])
    check(ordered, f"C3 ordered cross-field example {year}")
    task = {"title": "时间边界", "iteration_id": 1, "owner_id": 1,
            "plan": plan, "dependency_task_ids": []}
    for name, payload in (("Plan", plan), ("TaskCreate", task),
                          ("ContractValidationRequest", {"category": 1, "payload": task})):
        check(validator(name).is_valid(payload) == expected, f"C3 {name} year {year}")
far_end = datetime.fromisoformat("9999-12-31T23:59:59.999999Z")
now = datetime.fromisoformat("2026-10-23T00:00:00Z")
check((now - far_end).total_seconds() < -86400, "C3 subtraction at year 9999")
near_end = datetime.fromisoformat("9999-12-30T23:59:59.999999Z")
check((far_end - near_end).total_seconds() == 86400, "C3 severe boundary without addition")

operations = 0
for path, item in SPEC["paths"].items():
    for method, operation in item.items():
        annotations(path, method, operation)
        operations += 1

for relative in ("specs/contracts/README.md", "specs/backend-design.md"):
    check("response_request_id" in (ROOT / relative).read_text(), f"C1 documented source: {relative}")

for failure in FAILURES:
    print("FAIL:", failure)
for prefix, label in (
    ("C2", "101 recipients through event/create/history envelopes; UINT32 handled_count"),
    ("C3", "FormatChecker+pattern 0001/0999 reject, 1000/9999 accept; shared Plan/TaskCreate/validation domain; no end+24h"),
    ("C4", "38 operations: annotation/response/HTTP/trigger equality; read-only has no idempotency errors"),
    ("C1", "backend replay-source documentation only; database field/CHECK is another role's work"),
):
    result = "FAIL" if any(failure.startswith(prefix) for failure in FAILURES) else "PASS"
    print(f"{prefix}: {result}: {label}")
print(f"Design checks: {CHECKS}; operations: {operations}; failures: {len(FAILURES)}")
print("LIMIT: specification/Schema-only examples and annotation checks; no HTTP, MySQL, scheduler or product test")
raise SystemExit(1 if FAILURES else 0)
