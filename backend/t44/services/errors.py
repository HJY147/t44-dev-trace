"""Approved application errors, with no raw request, SQL or credentials in messages."""

from t44.contracts import OPERATIONS

STATUS = {
    case["code"]: case["http_status"]
    for operation in OPERATIONS.values()
    for case in operation["x-error-cases"]
}


class Rejected(Exception):
    def __init__(self, code, *, violations=(), current_version=None, current_state=None):
        self.code = code
        self.status = STATUS[code]
        self.violations = list(violations)
        self.current_version = current_version
        self.current_state = current_state
        super().__init__(code)

    def payload(self, request_id, audit_id=None, original=None):
        return {
            "code": self.code,
            "message": self.code.replace("_", " ").capitalize(),
            "request_id": request_id,
            "audit_id": audit_id,
            "current_version": self.current_version,
            "current_state": self.current_state,
            "original_error_code": original,
            "violations": self.violations,
        }


def require(condition, code, **details):
    if not condition:
        raise Rejected(code, **details)
