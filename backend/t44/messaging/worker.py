"""Outbox leases and terminal degradation; network I/O never holds a DB transaction."""

import logging
from datetime import timedelta

import pika

from t44.persistence import PersistenceError
from t44.persistence.codecs import utc_now

from .broker import BrokerUnavailable, consume_delivery

LOG = logging.getLogger(__name__)


class DeliveryWorker:
    def __init__(
        self,
        store,
        publisher,
        consumer,
        *,
        batch_size=50,
        lease_seconds=30,
        confirmed_recovery=None,
        confirmation_timeout=120,
    ):
        self.store, self.publisher, self.consumer = store, publisher, consumer
        self.batch_size, self.lease_seconds = batch_size, lease_seconds
        self.recover_confirmed = confirmed_recovery or store.recover_confirmed
        self.confirmation_timeout = confirmation_timeout

    def cycle(self):
        counts = dict(
            confirmed=0, fallback=0, recovered=0, retried=0, consumed=0, quarantined=0, errors=0
        )
        try:
            self.publisher.keepalive()
        except BrokerUnavailable:
            counts["errors"] += 1
        now = utc_now()
        recovered = self.recover_confirmed(
            confirmed_before=now - timedelta(seconds=self.confirmation_timeout),
            now=now,
            limit=self.batch_size,
        )
        counts["recovered"] = len(recovered)
        events = self.store.claim(
            now=utc_now(), limit=self.batch_size, lease_seconds=self.lease_seconds
        )
        for event in events:
            try:
                self.publisher.publish(event)
            except BrokerUnavailable:
                counts["errors"] += 1
                if event["event_type"] == 2:
                    result = self.store.fallback(
                        event["id"], lease_token=event["lease_token"], error_code="MQ_UNAVAILABLE"
                    )
                    counts["fallback"] += int(not result.get("stale_owner", False))
                else:
                    counts["retried"] += int(
                        self.store.retry(
                            event["id"], event["lease_token"], error_code="MQ_UNAVAILABLE"
                        )
                    )
            else:
                counts["confirmed"] += int(self.store.confirm(event["id"], event["lease_token"]))
        for _ in range(self.batch_size):
            try:
                delivery = self.consumer.get()
                if delivery is None:
                    break
                channel, method, _properties, body = delivery
                counts[consume_delivery(self.store, channel, method, body)] += 1
            except (BrokerUnavailable, pika.exceptions.AMQPError, OSError, PersistenceError):
                # No exception string: AMQP URLs and driver values must not enter logs.
                counts["errors"] += 1
                self.consumer.close()
                break
        return counts

    def run(self, stop, *, poll_seconds=1):
        try:
            while not stop.is_set():
                try:
                    counts = self.cycle()
                    if any(counts.values()):
                        LOG.info("delivery_cycle %s", counts)
                except PersistenceError:
                    LOG.error("delivery_cycle DATABASE_UNAVAILABLE; lease recovery retained")
                stop.wait(poll_seconds)
        finally:
            self.publisher.close()
            self.consumer.close()
