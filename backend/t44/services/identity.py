"""Opaque sessions and live membership checks. Token material is never persisted."""

import hashlib
import secrets
import threading
import time as monotonic_time
from collections import deque
from datetime import timedelta

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

from .common import model, now
from .errors import require

BEARER_TYPE = "Bearer"
HASHER = PasswordHasher()
_DUMMY_HASH = HASHER.hash(secrets.token_urlsafe(32))


def token_digest(token):
    return hashlib.sha256(token.encode()).digest()


class LoginLimiter:
    def __init__(self, attempts, seconds):
        self.attempts, self.seconds = attempts, seconds
        self._entries, self._lock = {}, threading.Lock()

    def check(self, username, source):
        timestamp = monotonic_time.monotonic()
        key = hashlib.sha256(f"{username}\0{source}".encode()).digest()
        with self._lock:
            if len(self._entries) > 10000:
                self._entries = {
                    k: q for k, q in self._entries.items() if q and q[-1] > timestamp - self.seconds
                }
            queue = self._entries.setdefault(key, deque())
            while queue and queue[0] <= timestamp - self.seconds:
                queue.popleft()
            require(len(queue) < self.attempts, "RATE_LIMITED")
            queue.append(timestamp)


def authenticate(g, call, *, lock=None):
    require(call.token and 32 <= len(call.token) <= 512, "AUTH_REQUIRED")
    rows = g.rows("auth_sessions", {"token_hash": token_digest(call.token)}, lock=lock, limit=1)
    require(rows, "AUTH_REQUIRED")
    session = rows[0]
    call.actor = {
        **session,
        "actor_id": session["user_id"]
        if session["actor_kind"] == 1
        else session["service_account_id"],
    }
    require(session["revoked_at"] is None, "TOKEN_REVOKED")
    require(session["expires_at"] > now(), "TOKEN_EXPIRED")
    kind = session["actor_kind"]
    identity = g.get(
        "users" if kind == 1 else "service_accounts",
        session["user_id"] if kind == 1 else session["service_account_id"],
    )
    require(identity and identity["active"], "TOKEN_REVOKED")
    actor_id = identity["id"]
    call.actor = {**session, "actor_id": actor_id, "identity": identity}
    if call.operation == "createEscalation":
        require(kind == 2, "SERVICE_SCOPE_REQUIRED")
    if call.project_id is not None:
        if kind == 2:
            require(call.operation == "createEscalation", "ACTION_FORBIDDEN")
            require(
                "escalation:write" in session["scopes"]
                and call.project_id in session["project_ids"],
                "SERVICE_SCOPE_REQUIRED",
            )
        else:
            members = g.rows(
                "project_members",
                {"project_id": call.project_id, "user_id": actor_id, "active": 1},
                limit=1,
            )
            require(members, "PROJECT_ACCESS_DENIED")
            call.membership = members[0]
        call.project = g.get("projects", call.project_id)
        require(call.project, "RESOURCE_NOT_FOUND")
    elif kind == 2:
        require(False, "ACTION_FORBIDDEN")
    return call.actor


def login(g, call, settings):
    users = g.rows("users", {"username": call.body["username"]}, limit=1)
    user = users[0] if users else None
    try:
        valid = HASHER.verify(user["password_hash"] if user else _DUMMY_HASH, call.body["password"])
    except (VerificationError, InvalidHashError):
        valid = False
    require(valid and user and user["active"], "INVALID_CREDENTIALS")
    token = secrets.token_urlsafe(32)
    expires = call.clock + timedelta(seconds=settings.session_ttl_seconds)
    g.insert(
        "auth_sessions",
        {
            "actor_kind": 1,
            "user_id": user["id"],
            "service_account_id": None,
            "token_hash": token_digest(token),
            "project_ids": [],
            "scopes": [],
            "expires_at": expires,
            "revoked_at": None,
            "created_at": call.clock,
        },
    )
    call.actor = {"actor_kind": 1, "actor_id": user["id"]}
    return {
        "access_token": token,
        "token_type": BEARER_TYPE,
        "expires_at": expires,
        "user": model("User", user),
    }
