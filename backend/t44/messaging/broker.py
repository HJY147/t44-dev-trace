"""Pika 1.x blocking connections are used only by their owning process thread."""

import json
from dataclasses import dataclass, field
from urllib.parse import urlsplit

import pika

from t44.persistence import PersistenceError, StatementRejected


class BrokerUnavailable(Exception):
    """A deliberately credential-free broker error."""


@dataclass(frozen=True)
class BrokerSettings:
    url: str = field(repr=False)
    exchange: str = "t44.events"
    queue: str = "t44.notifications"

    def __post_init__(self):
        if urlsplit(self.url).scheme not in ("amqp", "amqps"):
            raise ValueError("AMQP_URL must use AMQP or AMQPS")
        if not self.exchange or not self.queue or len(self.queue.encode()) > 230:
            raise ValueError("Broker topology names are invalid")


class PikaBroker:
    def __init__(self, settings, *, publisher=False, connect=pika.BlockingConnection):
        self.settings, self.publisher, self.connect = settings, publisher, connect
        self.connection = self.channel = None

    def _channel(self):
        if self.connection is not None and self.connection.is_open and self.channel.is_open:
            return self.channel
        self.close()
        try:
            params = pika.URLParameters(self.settings.url)
            params.heartbeat = 60
            params.blocked_connection_timeout = 5
            params.socket_timeout = 5
            params.stack_timeout = 10
            params.connection_attempts = 1
            self.connection = self.connect(params)
            ch = self.channel = self.connection.channel()
            s = self.settings
            dead = s.exchange + ".quarantine"
            ch.exchange_declare(exchange=s.exchange, exchange_type="direct", durable=True)
            ch.exchange_declare(exchange=dead, exchange_type="direct", durable=True)
            ch.queue_declare(queue=s.queue + ".quarantine", durable=True)
            ch.queue_bind(queue=s.queue + ".quarantine", exchange=dead, routing_key=s.queue)
            ch.queue_declare(
                queue=s.queue,
                durable=True,
                arguments={"x-dead-letter-exchange": dead, "x-dead-letter-routing-key": s.queue},
            )
            ch.queue_bind(queue=s.queue, exchange=s.exchange, routing_key=s.queue)
            ch.basic_qos(prefetch_count=1)
            if self.publisher:
                ch.confirm_delivery()
            return ch
        except (pika.exceptions.AMQPError, OSError, ValueError):
            self.close()
            raise BrokerUnavailable("BROKER_CONNECT_FAILED") from None

    def publish(self, event):
        try:
            ch = self._channel()
            result = ch.basic_publish(
                exchange=self.settings.exchange,
                routing_key=self.settings.queue,
                body=json.dumps(
                    {
                        "event_id": event["id"],
                        "schema_version": event["schema_version"],
                        "event_type": event["event_type"],
                    }
                ).encode(),
                properties=pika.BasicProperties(
                    content_type="application/json",
                    delivery_mode=2,
                    message_id=str(event["id"]),
                    type="t44.event.v1",
                ),
                mandatory=True,
            )
            if result is False:
                raise BrokerUnavailable("BROKER_NACK")
        except (pika.exceptions.AMQPError, OSError):
            self.close()
            raise BrokerUnavailable("BROKER_PUBLISH_FAILED") from None

    def get(self):
        try:
            ch = self._channel()
            self.connection.process_data_events(time_limit=0)
            method, properties, body = ch.basic_get(self.settings.queue, auto_ack=False)
            return (ch, method, properties, body) if method else None
        except (pika.exceptions.AMQPError, OSError):
            self.close()
            raise BrokerUnavailable("BROKER_RECEIVE_FAILED") from None

    def keepalive(self):
        if self.connection is not None and self.connection.is_open:
            try:
                self.connection.process_data_events(time_limit=0)
            except (pika.exceptions.AMQPError, OSError):
                self.close()
                raise BrokerUnavailable("BROKER_HEARTBEAT_FAILED") from None

    def close(self):
        if self.connection is not None:
            try:
                if self.connection.is_open:
                    self.connection.close()
            except (pika.exceptions.AMQPError, OSError):
                pass
        self.connection = self.channel = None


def consume_delivery(store, channel, method, body):
    """DB consume returns only after commit. A lost ACK is safely redelivered."""
    try:
        message = json.loads(body)
        if not isinstance(message, dict) or set(message) != {
            "event_id",
            "schema_version",
            "event_type",
        }:
            raise ValueError
        if any(type(message[k]) is not int for k in message):
            raise ValueError
        if not 1 <= message["event_id"] <= 4294967295 or message["schema_version"] != 1:
            raise ValueError
        event = store.get(message["event_id"])
        if not event or any(event[k] != message[k] for k in ("schema_version", "event_type")):
            raise ValueError
        if event["event_type"] not in (1, 2):
            raise ValueError
        store.consume(event["id"])
    except (ValueError, TypeError, UnicodeError, StatementRejected):
        channel.basic_reject(delivery_tag=method.delivery_tag, requeue=False)
        return "quarantined"
    except PersistenceError:
        channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
        raise
    channel.basic_ack(delivery_tag=method.delivery_tag)
    return "consumed"
