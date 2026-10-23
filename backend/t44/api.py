"""Strict frozen HTTP adapter and lazy dependency injection composition root."""

import json
import re
import threading
import time
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from t44.contracts import OPERATIONS, SPEC, VERSION, normalized, violations
from t44.messaging.facade import NotificationFacade
from t44.persistence import PersistenceUnavailable, SqlAlchemyUnitOfWorkFactory, create_mysql_engine
from t44.scheduling.facade import EscalationFacade
from t44.services.application import Business
from t44.services.common import Call, now, wire
from t44.services.errors import Rejected, require
from t44.services.runtime import Runtime
from t44.settings import Settings

_REF = "#/components/parameters/"
_ATTACK = re.compile(
    r"(?is)(?:\bunion\s+(?:all\s+)?select\b|;\s*(?:drop|truncate)\s+table\b|"
    r"['\"]\s*(?:or|and)\s+\d+\s*=\s*\d+\s*(?:--|#))"
)


def _security(value):
    if isinstance(value, str):
        require("\x00" not in value, "SECURITY_INPUT_REJECTED")
    elif isinstance(value, dict):
        for key, item in value.items():
            if key != "password":
                _security(item)
    elif isinstance(value, list):
        for item in value:
            _security(item)


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate key")
        result[key] = value
    return result


def _schema_type(schema):
    if "$ref" in schema:
        return _schema_type(SPEC["components"]["schemas"][schema["$ref"].split("/")[-1]])
    return schema.get("type")


def _parameters(operation):
    return [
        SPEC["components"]["parameters"][p["$ref"].removeprefix(_REF)] if "$ref" in p else p
        for p in operation.get("parameters", [])
    ]


def validate_request(request, operation, c):
    if "requestBody" in operation:
        require(not request.state.too_large, "PAYLOAD_TOO_LARGE")
    parameters = _parameters(operation)
    known_queries = {p["name"] for p in parameters if p["in"] == "query"}
    if parameters:
        require(not (set(request.query_params) - known_queries), "PARAMETER_INVALID")
    for p in parameters:
        source = (
            request.path_params
            if p["in"] == "path"
            else request.query_params
            if p["in"] == "query"
            else request.headers
        )
        value = source.get(p["name"])
        if value is None:
            require(not p.get("required"), "PARAMETER_INVALID")
            if p["in"] == "query" and "default" in p["schema"]:
                c.query[p["name"]] = p["schema"]["default"]
            continue
        if p["in"] == "query":
            require(len(request.query_params.getlist(p["name"])) == 1, "PARAMETER_INVALID")
        require(not _ATTACK.search(value) and "\x00" not in value, "SECURITY_INPUT_REJECTED")
        kind = _schema_type(p["schema"])
        if kind == "integer":
            require(bool(re.fullmatch(r"[0-9]+", value)), "PARAMETER_INVALID")
            value = int(value)
        elif kind == "boolean":
            require(value in ("true", "false"), "PARAMETER_INVALID")
            value = value == "true"
        errors = violations(p["schema"], value)
        require(not errors, "PARAMETER_INVALID", violations=errors)
        if p["in"] == "query":
            c.query[p["name"]] = value
        elif p["in"] == "path":
            c.path[p["name"]] = value
        else:
            c.key = value
    raw = request.state.raw_body
    if "requestBody" in operation:
        require(
            request.headers.get("content-type", "").split(";")[0].lower() == "application/json",
            "INVALID_JSON",
        )
        try:
            payload = json.loads(
                raw,
                object_pairs_hook=_unique_object,
                parse_constant=lambda _: (_ for _ in ()).throw(ValueError()),
            )
        except (ValueError, UnicodeDecodeError):
            raise Rejected("INVALID_JSON") from None
        schema = operation["requestBody"]["content"]["application/json"]["schema"]
        errors = violations(schema, payload)
        require(
            not errors,
            "CONTRACT_INVALID" if c.operation == "validateContractPayload" else "PARAMETER_INVALID",
            violations=errors,
        )
        c.body = normalized(payload)
        _security(c.body)
    elif operation["method"] != "get":
        require(not raw, "PARAMETER_INVALID")


class LazyFactory:
    """Construct the real owner-provided UoW once. Missing configuration never creates a fake store."""

    def __init__(self, settings):
        self.settings, self.factory, self.lock = settings, None, threading.Lock()

    def __call__(self):
        if self.factory is None:
            with self.lock:
                if self.factory is None:
                    try:
                        engine = create_mysql_engine(self.settings.mysql_settings())
                        self.factory = SqlAlchemyUnitOfWorkFactory(engine)
                    except Exception:
                        raise PersistenceUnavailable("Database configuration unavailable") from None
        return self.factory()


_DEFAULT = object()


def create_app(*, factory=None, settings=None, notifications=_DEFAULT, escalations=_DEFAULT):
    settings = settings or Settings.from_env()
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
    runtime = Runtime(
        factory or LazyFactory(settings),
        settings,
        Business(
            notifications=NotificationFacade() if notifications is _DEFAULT else notifications,
            escalations=EscalationFacade() if escalations is _DEFAULT else escalations,
        ),
    )
    app.state.runtime = runtime

    @app.middleware("http")
    async def capture(request, call_next):
        chunks, size = [], 0
        async for chunk in request.stream():
            size += len(chunk)
            if size <= 1048576:
                chunks.append(chunk)
        request.state.raw_body = b"".join(chunks)
        request.state.too_large = size > 1048576
        request.state.request_id = str(uuid4())
        return await call_next(request)

    def endpoint(operation):
        def handle(request: Request):
            started = time.perf_counter()
            auth = request.headers.get("authorization", "")
            token = auth[7:] if auth.startswith("Bearer ") else None
            # Numeric path decoding permits scope checks before parsing the body.
            path = {
                k: int(v) if re.fullmatch(r"[0-9]{1,10}", v) else 0
                for k, v in request.path_params.items()
            }
            c = Call(operation["operationId"], request.state.request_id, token, path=path)
            status, result, replayed, original = runtime.execute(
                c,
                lambda call: validate_request(request, operation, call),
                request.client.host if request.client else "unknown",
            )
            payload = (
                result
                if status >= 400
                else {
                    "data": result,
                    "meta": {
                        "request_id": c.request_id,
                        "server_time": wire(now()),
                        "contract_version": VERSION,
                        "replayed": replayed,
                        "original_request_id": original,
                    },
                }
            )
            schema = (
                operation["responses"]
                .get(str(status), {})
                .get("content", {})
                .get("application/json", {})
                .get("schema")
            )
            if schema is None or violations(schema, wire(payload)):
                # This is an implementation fault, never silently relax the frozen schema.
                status = 500
                payload = Rejected("INTERNAL_ERROR").payload(c.request_id)
            headers = {
                "X-Request-ID": c.request_id,
                "Cache-Control": "no-store",
                "Idempotency-Replayed": str(replayed).lower(),
                "Server-Timing": f"app;dur={(time.perf_counter() - started) * 1000:.3f}",
            }
            if status == 429 or (
                status == 409 and payload.get("code") == "IDEMPOTENCY_IN_PROGRESS"
            ):
                headers["Retry-After"] = (
                    "1" if status == 409 else str(settings.login_window_seconds)
                )
            return JSONResponse(wire(payload), status_code=status, headers=headers)

        return handle

    for operation in OPERATIONS.values():
        app.add_api_route(
            "/api/v1" + operation["path"],
            endpoint(operation),
            methods=[operation["method"].upper()],
            name=operation["operationId"],
        )
    return app


app = create_app()
