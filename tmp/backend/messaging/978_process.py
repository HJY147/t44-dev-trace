import sys
from threading import Event
from unittest.mock import Mock

import pika
import pytest
from t44.messaging.__main__ import main
from t44.messaging.broker import BrokerSettings, BrokerUnavailable, PikaBroker
from t44.messaging.worker import DeliveryWorker
from t44.persistence import PersistenceUnavailable


def test_configuration_and_connect_failure_do_not_expose_amqp_credentials(monkeypatch, caplog):
    broker = PikaBroker(
        BrokerSettings("amqp://account:do-not-log-this@localhost/"),
        connect=Mock(side_effect=pika.exceptions.AMQPConnectionError("do-not-log-this")),
    )
    assert "do-not-log-this" not in repr(broker.settings)
    with pytest.raises(BrokerUnavailable) as exc:
        broker.get()
    assert "do-not-log-this" not in str(exc.value)
    monkeypatch.setattr(sys, "argv", ["t44.messaging", "--once"])
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("AMQP_URL", "amqp://account:do-not-log-this@localhost/")
    assert main() == 1 and "do-not-log-this" not in caplog.text


def test_run_retries_database_failure_and_closes_on_graceful_stop():
    store, publisher, consumer, stop = Mock(), Mock(), Mock(), Event()
    store.recover_confirmed.return_value = []
    store.claim.side_effect = PersistenceUnavailable("synthetic")
    worker = DeliveryWorker(store, publisher, consumer)
    original = stop.wait

    def wait_then_stop(seconds):
        stop.set()
        return original(0)

    stop.wait = wait_then_stop
    worker.run(stop, poll_seconds=0)
    publisher.close.assert_called_once()
    consumer.close.assert_called_once()


def test_consumer_ack_failure_keeps_database_and_reconnects():
    store, publisher, consumer, channel = Mock(), Mock(), Mock(), Mock()
    store.recover_confirmed.return_value = []
    store.claim.return_value = []
    store.get.return_value = dict(id=5, schema_version=1, event_type=2)
    channel.basic_ack.side_effect = pika.exceptions.AMQPConnectionError()
    method = Mock(delivery_tag=8)
    consumer.get.return_value = (
        channel,
        method,
        None,
        b'{"event_id":5,"schema_version":1,"event_type":2}',
    )
    result = DeliveryWorker(store, publisher, consumer).cycle()
    assert result["errors"] == 1 and result["consumed"] == 0
    store.consume.assert_called_once_with(5)
    consumer.close.assert_called_once()


def test_publisher_idle_heartbeat_is_serviced_and_failed_connection_is_replaced():
    connection = Mock()
    broker = PikaBroker(BrokerSettings("amqp://localhost/"), connect=Mock(return_value=connection))
    broker._channel()
    broker.keepalive()
    connection.process_data_events.assert_called_once_with(time_limit=0)
    connection.process_data_events.side_effect = pika.exceptions.AMQPConnectionError()
    with pytest.raises(BrokerUnavailable, match="BROKER_HEARTBEAT_FAILED"):
        broker.keepalive()
    assert broker.connection is None
    connection.close.assert_called_once()
