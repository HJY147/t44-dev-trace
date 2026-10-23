"""Durable claim/replay primitives; HTTP and business decisions remain in the service layer."""

from datetime import timedelta
from uuid import uuid4

from .codecs import utc_now
from .errors import PersistenceIntegrityError, StatementRejected


class IdempotencyStore:
    def __init__(self, factory):
        self.factory = factory

    def claim(
        self, *, actor_kind, actor_id, operation_id, key, request_hash, now=None, lease_seconds=60
    ):
        now = now or utc_now()
        if len(request_hash) != 32 or lease_seconds < 1:
            raise ValueError("SHA256 digest and positive lease required")
        scope = dict(
            actor_kind=actor_kind, actor_id=actor_id, operation_id=operation_id, idempotency_key=key
        )
        with self.factory() as uow:
            g = uow.gateway
            # Unique index arbitrates even if simultaneous inserts both saw no existing row.
            try:
                with g.savepoint():
                    id = g.insert(
                        "idempotency_requests",
                        dict(
                            **scope,
                            request_hash=request_hash,
                            status=1,
                            owner_token=uuid4().bytes,
                            lease_until=now + timedelta(seconds=lease_seconds),
                            response_status=None,
                            response_body=None,
                            response_request_id=None,
                            created_at=now,
                            completed_at=None,
                        ),
                    )
                return {"disposition": "claimed", "row": g.get("idempotency_requests", id)}
            except PersistenceIntegrityError as error:
                if error.kind != "duplicate":
                    raise
            row = g.rows("idempotency_requests", scope, lock="update", limit=1)[0]
            if row["request_hash"] != request_hash:
                return {"disposition": "mismatch", "row": row}
            if row["status"] == 2:
                return {"disposition": "replay", "row": row}
            if row["lease_until"] > now:
                return {"disposition": "in_progress", "row": row}
            # Row lock waits for any old owner's main transaction. New token fences stale owners.
            values = dict(
                owner_token=uuid4().bytes, lease_until=now + timedelta(seconds=lease_seconds)
            )
            changed = g.update(
                "idempotency_requests",
                {"id": row["id"], "status": 1, "owner_token": row["owner_token"]},
                values,
            )
            if changed != 1:
                raise StatementRejected("Idempotency lease ownership changed")
            row.update(values)
            return {"disposition": "claimed", "row": row}

    @staticmethod
    def lock_owner(gateway, id, owner_token, *, now=None):
        row = gateway.get("idempotency_requests", id, lock="update")
        if (
            not row
            or row["status"] != 1
            or row["owner_token"] != owner_token
            or row["lease_until"] <= (now or utc_now())
        ):
            raise StatementRejected("Idempotency owner is stale or lease expired")
        return row

    @classmethod
    def complete(
        cls,
        gateway,
        id,
        owner_token,
        *,
        response_status,
        response_body,
        response_request_id,
        now=None,
    ):
        now = now or utc_now()
        cls.lock_owner(gateway, id, owner_token, now=now)
        if not response_request_id or not response_request_id.strip():
            raise StatementRejected("Saved result requires its producing request ID")
        return gateway.update(
            "idempotency_requests",
            {"id": id, "owner_token": owner_token},
            dict(
                status=2,
                response_status=response_status,
                response_body=response_body,
                response_request_id=response_request_id,
                completed_at=now,
            ),
        )

    def reject_after_rollback(
        self, id, owner_token, *, audit_values, response_status, response_body, response_request_id
    ):
        """Call only after the main UoW has rolled back AND closed/released its locks."""
        with self.factory() as audit:
            self.lock_owner(audit.gateway, id, owner_token)
            audit_id = audit.gateway.insert("audit_events", audit_values)
            self.complete(
                audit.gateway,
                id,
                owner_token,
                response_status=response_status,
                response_body=response_body,
                response_request_id=response_request_id,
            )
        # CommitUncertain deliberately propagates; no second execution or assumed rollback.
        return audit_id
