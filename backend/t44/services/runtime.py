"""One transaction boundary for audit, idempotency, sessions, and application writes."""

import hashlib
import json
import logging
import secrets
from datetime import timedelta

from t44.contracts import OPERATIONS
from t44.persistence import CommitUncertain, PersistenceError, PersistenceIntegrityError

from .codes import ERROR_IDS, Action
from .common import wire
from .errors import Rejected, require
from .identity import LoginLimiter, authenticate, login

_LOG = logging.getLogger("t44.audit")
_PROJECT_LOCK = {
    "addProjectMember",
    "changeProjectMember",
    "removeProjectMember",
    "createTask",
    "addTaskDependency",
    "removeTaskDependency",
    "createIteration",
    "changeIteration",
}


def _audit_integer(value, maximum, minimum=0):
    return value if type(value) is int and minimum <= value <= maximum else None


class Runtime:
    def __init__(self, factory, settings, business):
        self.factory, self.settings, self.business = factory, settings, business
        self.limiter = LoginLimiter(settings.login_attempts, settings.login_window_seconds)

    def authorize(self, call):
        if call.operation != "login":
            with self.factory() as uow:
                authenticate(uow.gateway, call)

    def audit(self, g, call, error=None):
        project = call.project_id if call.project and g.get("projects", call.project_id) else None
        task_id = call.path.get("task_id")
        if task_id is not None and not (
            project and g.rows("tasks", {"id": task_id, "project_id": project}, limit=1)
        ):
            task_id = None
        return g.insert(
            "audit_events",
            {
                "project_id": project,
                "task_id": task_id,
                "attempted_project_id": _audit_integer(call.project_id, 4294967295),
                "attempted_task_id": _audit_integer(call.path.get("task_id"), 4294967295),
                "actor_kind": call.actor["actor_kind"] if call.actor else 3,
                "actor_id": call.actor_id,
                "request_id": call.request_id,
                "operation_id": call.operation,
                "outcome": 2 if error else 1,
                "reason_code": ERROR_IDS[error.code] if error else None,
                "expected_version": _audit_integer(
                    call.body.get("expected_version"), 2147483647, 1
                ),
                "observed_version": error.current_version if error else None,
                "before_values": [] if error else call.before,
                "after_values": [] if error else call.after,
                "evidence": [] if error else call.body.get("evidence", []),
                "created_at": call.clock,
            },
        )

    def rejection(self, call, error):
        try:
            with self.factory() as uow:
                g = uow.gateway
                # Session precedes the owned idempotency row, including this independent transaction.
                if call.actor and call.token:
                    g.get("auth_sessions", call.actor["id"], lock="share")
                idem = (
                    g.get("idempotency_requests", call.idem["id"], lock="update")
                    if call.idem
                    else None
                )
                call.audit_id = self.audit(g, call, error)
                payload = error.payload(call.request_id, call.audit_id)
                if (
                    idem
                    and idem["owner_token"] == call.idem["owner_token"]
                    and idem["status"] == 1
                    and error.status < 500
                ):
                    saved = {k: v for k, v in payload.items() if k != "request_id"}
                    self.complete(g, call, error.status, {"error": saved})
            return error.status, payload, False, None
        except PersistenceError:
            _LOG.error(
                "audit_unavailable request_id=%s operation=%s", call.request_id, call.operation
            )
            return (
                503,
                Rejected("AUDIT_UNAVAILABLE").payload(call.request_id, original=error.code),
                False,
                None,
            )

    def complete(self, g, call, status, result):
        require(
            g.update(
                "idempotency_requests",
                {"id": call.idem["id"], "status": 1, "owner_token": call.idem["owner_token"]},
                {
                    "status": 2,
                    "response_status": status,
                    "response_body": wire(result),
                    "response_request_id": call.request_id,
                    "completed_at": call.clock,
                },
            )
            == 1,
            "IDEMPOTENCY_IN_PROGRESS",
        )

    def claim(self, call):
        digest = hashlib.sha256(
            json.dumps(
                {"path": call.path, "query": call.query, "body": call.body},
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
            ).encode()
        ).digest()
        scope = {
            "actor_kind": call.actor["actor_kind"],
            "actor_id": call.actor_id,
            "operation_id": call.operation,
            "idempotency_key": call.key,
        }
        with self.factory() as uow:
            g = uow.gateway
            authenticate(g, call, lock="share")
            existing = g.rows("idempotency_requests", scope, lock="update", limit=1)
            if not existing:
                try:
                    with g.savepoint():
                        identifier = g.insert(
                            "idempotency_requests",
                            {
                                **scope,
                                "request_hash": digest,
                                "status": 1,
                                "owner_token": secrets.token_bytes(16),
                                "lease_until": call.clock
                                + timedelta(seconds=self.settings.idempotency_lease_seconds),
                                "created_at": call.clock,
                            },
                        )
                    call.idem = g.get("idempotency_requests", identifier)
                    return None
                except PersistenceIntegrityError as error:
                    if error.kind != "duplicate":
                        raise
                    existing = g.rows("idempotency_requests", scope, lock="update", limit=1)
            row = existing[0]
            require(row["request_hash"] == digest, "IDEMPOTENCY_CONTENT_CONFLICT")
            if row["status"] == 2:
                return row
            require(row["lease_until"] <= call.clock, "IDEMPOTENCY_IN_PROGRESS")
            # FOR UPDATE waited for the old main transaction. Replacing owner fences it out.
            owner = secrets.token_bytes(16)
            g.update(
                "idempotency_requests",
                {"id": row["id"]},
                {
                    "owner_token": owner,
                    "lease_until": call.clock
                    + timedelta(seconds=self.settings.idempotency_lease_seconds),
                },
            )
            call.idem = {**row, "owner_token": owner}
        return None

    def locked_scope(self, g, call):
        authenticate(g, call, lock="update" if call.operation == "logout" else "share")
        if call.idem:
            row = g.get("idempotency_requests", call.idem["id"], lock="update")
            require(
                row["status"] == 1 and row["owner_token"] == call.idem["owner_token"],
                "IDEMPOTENCY_IN_PROGRESS",
            )
        if call.project_id is None:
            return
        graph_lock = call.operation in _PROJECT_LOCK or (
            call.operation == "transitionTask"
            and call.body["action"] in (Action.START, Action.UNBLOCK, Action.REWORK)
        )
        if graph_lock:
            g.get("projects", call.project_id, lock="update")
        members = g.rows(
            "project_members", {"project_id": call.project_id}, order_by=("user_id",), lock="share"
        )
        if call.actor["actor_kind"] == 1:
            call.membership = next(
                (m for m in members if m["user_id"] == call.actor_id and m["active"]), None
            )
            require(call.membership, "PROJECT_ACCESS_DENIED")
        if "task_id" in call.path:
            ids = {call.path["task_id"]}
            if graph_lock:
                ids.update(
                    d["depends_on_task_id"]
                    for d in g.rows(
                        "task_dependencies",
                        {"project_id": call.project_id, "task_id": call.path["task_id"]},
                    )
                )
                if "depends_on_task_id" in call.body:
                    ids.add(call.body["depends_on_task_id"])
            g.rows("tasks", {"project_id": call.project_id, "id": sorted(ids)}, lock="update")

    def execute(self, call, validate, source="unknown"):
        try:
            self.authorize(call)
            validate(call)
            if call.operation == "login":
                self.limiter.check(call.body["username"], source)
                with self.factory() as uow:
                    result = login(uow.gateway, call, self.settings)
                    self.business.validate_data("login", wire(result))
                    self.audit(uow.gateway, call)
                return 200, wire(result), False, None
            operation = OPERATIONS[call.operation]
            write = operation["method"] != "get" and call.operation != "validateContractPayload"
            if write and call.operation != "logout":
                replay = self.claim(call)
                if replay:
                    body = replay["response_body"]
                    result = (
                        {**body["error"], "request_id": call.request_id}
                        if "error" in body
                        else body["data"]
                    )
                    return replay["response_status"], result, True, replay["response_request_id"]
            with self.factory() as uow:
                g = uow.gateway
                if write:
                    self.locked_scope(g, call)
                else:
                    authenticate(g, call)
                if call.operation == "logout":
                    # Shared session lock is upgraded only for the session being revoked.
                    g.update("auth_sessions", {"id": call.actor["id"]}, {"revoked_at": call.clock})
                    result = {"acknowledged": True}
                else:
                    result = self.business.dispatch(g, call)
                if write:
                    call.audit_id = self.audit(g, call)
                    result = self.business.finalize(result, call)
                    self.business.validate_data(call.operation, result)
                    project = (
                        result.get("id") if call.operation == "createProject" else call.project_id
                    )
                    if project and call.operation != "createEscalation":
                        g.insert("outbox_events", self.business.outbox(call, project))
                    if call.idem:
                        self.complete(
                            g, call, self.business.status(call.operation), {"data": result}
                        )
            return self.business.status(call.operation), wire(result), False, None
        except Rejected as error:
            return self.rejection(call, error)
        except CommitUncertain:
            code = "TRANSACTION_UNCERTAIN" if call.idem else "DEPENDENCY_UNAVAILABLE"
            return 503, Rejected(code).payload(call.request_id), False, None
        except PersistenceError:
            return self.rejection(call, Rejected("DEPENDENCY_UNAVAILABLE"))
        except Exception:
            _LOG.error("internal_error request_id=%s operation=%s", call.request_id, call.operation)
            return self.rejection(call, Rejected("INTERNAL_ERROR"))
