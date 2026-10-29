"""Atomic DB half of publish/consume/fallback. Broker I/O belongs outside these transactions."""

from datetime import timedelta
from uuid import uuid4

from .codecs import utc_now
from .errors import StatementRejected
from .rows import Pred


class OutboxStore:
    def __init__(self, factory):
        self.factory = factory

    def _update(self, g, where, now, **values):
        return g.update("outbox_events", where, dict(updated_at=now, **values))

    def get(self, event_id):
        with self.factory() as uow:
            return uow.gateway.get("outbox_events", event_id)

    def claim(self, *, now=None, limit=100, lease_seconds=30):
        now = now or utc_now()
        if limit < 1 or lease_seconds < 1:
            raise ValueError("Positive claim limit/lease required")
        with self.factory() as uow:
            g = uow.gateway
            rows = []
            for status, due in ((1, "next_attempt_at"), (2, "lease_until")):
                if len(rows) == limit:
                    break
                rows.extend(
                    g.rows(
                        "outbox_events",
                        {"status": status},
                        predicates=(Pred(due, "le", now),),
                        order_by=(due, "id"),
                        limit=limit if status == 1 else limit - len(rows),
                        lock="update",
                        skip_locked=True,
                    )
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
            self._update(
                g,
                {"id": event_id},
                now,
                status=3,
                confirmed_at=now,
                lease_token=None,
                lease_until=None,
            )
            return True

    def _notices(self, g, event, *, fallback, now):
        if event["event_type"] != 2:
            return 0
        ledger = g.rows("escalation_events", {"event_id": event["id"]}, limit=1)
        if not ledger:
            raise StatementRejected("Escalation event has no committed ledger")
        existing = {n["recipient_id"] for n in g.rows("notifications", {"event_id": event["id"]})}
        notices = [
            dict(
                project_id=event["project_id"],
                task_id=event["task_id"],
                event_id=event["id"],
                recipient_id=recipient,
                level=ledger[0]["level"],
                title=event["payload"].get("title", f"任务 {event['task_id']} 升级"),
                message=event["payload"].get("message", "计划时间已触发升级，请处理"),
                fallback=int(fallback),
                handling_evidence=[],
                created_at=now,
            )
            for recipient in sorted(set(event["recipients"]) - existing)
        ]
        g.insert_many("notifications", notices)
        return len(notices)

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
                    self._update(
                        g,
                        {"id": event["id"], "status": 3},
                        now,
                        status=4,
                        fallback_at=now,
                        last_error_code="CONSUMER_TIMEOUT",
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
            self._update(
                g,
                {"id": event_id},
                now,
                status=4,
                fallback_at=event["fallback_at"] or now,
                lease_token=None,
                lease_until=None,
                last_error_code=error_code,
            )
            return {"event_id": event_id, "created": count, "fallback": True}

    def retry(
        self, event_id, lease_token, *, now=None, delay_seconds=5, error_code="PUBLISH_FAILED"
    ):
        now = now or utc_now()
        with self.factory() as uow:
            g = uow.gateway
            return (
                self._update(
                    g,
                    {"id": event_id, "status": 2, "lease_token": lease_token},
                    now,
                    status=1,
                    lease_token=None,
                    lease_until=None,
                    next_attempt_at=now + timedelta(seconds=delay_seconds),
                    last_error_code=error_code,
                )
                == 1
            )
