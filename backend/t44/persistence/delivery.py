"""Atomic DB half of publish/consume/fallback. Broker I/O belongs outside these transactions."""

from datetime import timedelta
from uuid import uuid4

from .codecs import utc_now
from .errors import StatementRejected
from .rows import Pred


class OutboxStore:
    def __init__(self, factory):
        self.factory = factory

    def get(self, event_id):
        with self.factory() as uow:
            return uow.gateway.get("outbox_events", event_id)

    def claim(self, *, now=None, limit=100, lease_seconds=30):
        now = now or utc_now()
        if limit < 1 or lease_seconds < 1:
            raise ValueError("Positive claim limit/lease required")
        with self.factory() as uow:
            g = uow.gateway
            rows = g.rows(
                "outbox_events",
                {"status": 1},
                predicates=(Pred("next_attempt_at", "le", now),),
                order_by=("next_attempt_at", "id"),
                limit=limit,
                lock="update",
                skip_locked=True,
            )
            if len(rows) < limit:
                rows += g.rows(
                    "outbox_events",
                    {"status": 2},
                    predicates=(Pred("lease_until", "le", now),),
                    order_by=("lease_until", "id"),
                    limit=limit - len(rows),
                    lock="update",
                    skip_locked=True,
                )
            for row in rows:
                values = dict(
                    status=2,
                    attempts=min(row["attempts"] + 1, 65535),
                    lease_token=uuid4().bytes,
                    lease_until=now + timedelta(seconds=lease_seconds),
                    updated_at=now,
                )
                g.update("outbox_events", {"id": row["id"]}, values)
                row.update(values)
            return rows

    def confirm(self, event_id, lease_token, *, now=None):
        now = now or utc_now()
        with self.factory() as uow:
            g = uow.gateway
            event = g.get("outbox_events", event_id, lock="update")
            if not event or event["status"] != 2 or event["lease_token"] != lease_token:
                return False
            g.update(
                "outbox_events",
                {"id": event_id},
                dict(
                    status=3, confirmed_at=now, lease_token=None, lease_until=None, updated_at=now
                ),
            )
            return True

    def _notices(self, g, event, *, fallback, now):
        if event["event_type"] != 2:
            return 0
        ledger = g.rows("escalation_events", {"event_id": event["id"]}, limit=1)
        if not ledger:
            raise StatementRejected("Escalation event has no committed ledger")
        existing = {n["recipient_id"] for n in g.rows("notifications", {"event_id": event["id"]})}
        created = 0
        for recipient in sorted(set(event["recipients"])):
            if recipient in existing:
                continue
            g.insert(
                "notifications",
                dict(
                    project_id=event["project_id"],
                    task_id=event["task_id"],
                    event_id=event["id"],
                    recipient_id=recipient,
                    version=1,
                    level=ledger[0]["level"],
                    title=event["payload"].get("title", f"任务 {event['task_id']} 升级"),
                    message=event["payload"].get("message", "计划时间已触发升级，请处理"),
                    fallback=int(fallback),
                    read_at=None,
                    handled_at=None,
                    handling_note=None,
                    handling_evidence=[],
                    created_at=now,
                ),
            )
            created += 1
        return created

    def consume(self, event_id, *, now=None):
        now = now or utc_now()
        with self.factory() as uow:
            g = uow.gateway
            event = g.get("outbox_events", event_id, lock="update")
            if not event:
                raise StatementRejected("Unknown event cannot be consumed")
            # Same event lock as fallback; terminal fallback cannot create a second reminder.
            count = self._notices(g, event, fallback=event["status"] == 4, now=now)
            return {"event_id": event_id, "created": count, "fallback": event["status"] == 4}

    def recover_confirmed(self, *, confirmed_before, now=None, limit=100):
        now = now or utc_now()
        recovered = []
        with self.factory() as uow:
            g = uow.gateway
            for event in g.confirmed_missing(confirmed_before=confirmed_before, limit=limit):
                # Recheck after locking: a racing consumer may already have filled every notice.
                count = self._notices(g, event, fallback=True, now=now)
                if count:
                    g.update(
                        "outbox_events",
                        {"id": event["id"], "status": 3},
                        dict(
                            status=4,
                            fallback_at=now,
                            updated_at=now,
                            last_error_code="CONSUMER_TIMEOUT",
                        ),
                    )
                    recovered.append(dict(event_id=event["id"], created=count, fallback=True))
        return recovered

    def fallback(self, event_id, *, now=None, lease_token=None, error_code="MQ_UNAVAILABLE"):
        now = now or utc_now()
        with self.factory() as uow:
            g = uow.gateway
            event = g.get("outbox_events", event_id, lock="update")
            if not event or event["event_type"] != 2:
                raise StatementRejected("Fallback requires an escalation event")
            if lease_token is not None and event["lease_token"] != lease_token:
                return {"event_id": event_id, "created": 0, "stale_owner": True}
            count = self._notices(g, event, fallback=True, now=now)
            g.update(
                "outbox_events",
                {"id": event_id},
                dict(
                    status=4,
                    fallback_at=event["fallback_at"] or now,
                    lease_token=None,
                    lease_until=None,
                    last_error_code=error_code,
                    updated_at=now,
                ),
            )
            return {"event_id": event_id, "created": count, "fallback": True}

    def retry(
        self, event_id, lease_token, *, now=None, delay_seconds=5, error_code="PUBLISH_FAILED"
    ):
        now = now or utc_now()
        with self.factory() as uow:
            g = uow.gateway
            return (
                g.update(
                    "outbox_events",
                    {"id": event_id, "status": 2, "lease_token": lease_token},
                    dict(
                        status=1,
                        lease_token=None,
                        lease_until=None,
                        next_attempt_at=now + timedelta(seconds=delay_seconds),
                        last_error_code=error_code,
                        updated_at=now,
                    ),
                )
                == 1
            )
