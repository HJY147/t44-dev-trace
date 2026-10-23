"""Real RabbitMQ + real MySQL checks. No mocked broker and no missing-config CI skip."""

import os
import time
from uuid import uuid4

import pytest
from t44.messaging.broker import BrokerSettings, BrokerUnavailable, PikaBroker, consume_delivery
from t44.persistence.delivery import OutboxStore

pytestmark = [pytest.mark.integration, pytest.mark.parametrize("factory", ["mysql"], indirect=True)]


@pytest.fixture
def brokers():
    if not (url := os.getenv("AMQP_URL")):
        if os.getenv("CI"):
            pytest.fail("Real RabbitMQ AMQP_URL missing in CI; refusing to skip")
        pytest.skip("No local RabbitMQ; set AMQP_URL for real broker checks")
    tag = uuid4().hex
    settings = BrokerSettings(url, exchange="t44.test." + tag, queue="t44.test." + tag)
    publisher, consumer = PikaBroker(settings, publisher=True), PikaBroker(settings)
    # An unavailable configured server is a real test failure, never a skip.
    publisher._channel()
    try:
        yield publisher, consumer
    finally:
        consumer.close()
        try:
            ch = publisher._channel()
            ch.queue_delete(settings.queue)
            ch.queue_delete(settings.queue + ".quarantine")
            ch.exchange_delete(settings.exchange)
            ch.exchange_delete(settings.exchange + ".quarantine")
        finally:
            publisher.close()


def wait_message(consumer):
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        if delivery := consumer.get():
            return delivery
        time.sleep(0.02)
    pytest.fail("Real broker delivery timed out")


def notice_rows(case, eid):
    with case.factory() as uow:
        return uow.gateway.rows("notifications", {"event_id": eid})


@pytest.mark.fault
def test_real_confirm_ack_loss_redelivery_and_connection_restart(case, brokers):
    publisher, consumer = brokers
    eid, store = case.event(), OutboxStore(case.factory)
    row = next(row for row in store.claim(limit=10000) if row["id"] == eid)
    publisher.publish(row)
    assert store.confirm(eid, row["lease_token"])
    channel, method, _props, body = wait_message(consumer)
    assert _props.delivery_mode == 2 and _props.message_id == str(eid)
    assert store.consume(eid)["created"] == 1
    # Commit succeeded but do not ACK: closing the actual AMQP connection forces broker redelivery.
    consumer.close()
    replacement = PikaBroker(consumer.settings)
    try:
        channel, method, _props, body = wait_message(replacement)
        assert method.redelivered
        assert consume_delivery(store, channel, method, body) == "consumed"
        assert len(notice_rows(case, eid)) == 1
        # A duplicate published with the same DB event remains idempotent after reconnection.
        publisher.close()
        publisher.publish(store.get(eid))
        channel, method, _props, body = wait_message(replacement)
        consume_delivery(store, channel, method, body)
        assert len(notice_rows(case, eid)) == 1
    finally:
        replacement.close()


@pytest.mark.fault
def test_real_mandatory_return_fallback_terminal_and_new_event_recovers(case, brokers):
    publisher, consumer = brokers
    eid, store = case.event(), OutboxStore(case.factory)
    row = next(row for row in store.claim(limit=10000) if row["id"] == eid)
    ch = publisher._channel()
    ch.queue_unbind(
        queue=publisher.settings.queue,
        exchange=publisher.settings.exchange,
        routing_key=publisher.settings.queue,
    )
    with pytest.raises(BrokerUnavailable, match="BROKER_PUBLISH_FAILED"):
        publisher.publish(row)  # Real Basic.Return from mandatory unroutable publication.
    assert store.fallback(eid, lease_token=row["lease_token"])["created"] == 1
    assert not store.confirm(eid, row["lease_token"])
    # Reconnect recreates the real route; the old event is already terminal.
    publisher.publish(
        store.get(eid)
    )  # Deliberate late/duplicate in-flight delivery, not recovery replay.
    channel, method, _props, body = wait_message(consumer)
    consume_delivery(store, channel, method, body)
    assert len(notice_rows(case, eid)) == 1 and notice_rows(case, eid)[0]["fallback"] == 1
    assert store.get(eid)["status"] == 4
    new = case.event()
    publisher.publish(store.get(new))
    channel, method, _props, body = wait_message(consumer)
    consume_delivery(store, channel, method, body)
    assert len(notice_rows(case, new)) == 1 and notice_rows(case, new)[0]["fallback"] == 0


def test_real_poison_message_goes_to_durable_quarantine(case, brokers):
    publisher, consumer = brokers
    ch = publisher._channel()
    ch.basic_publish(
        exchange=publisher.settings.exchange,
        routing_key=publisher.settings.queue,
        body=b"{invalid-json",
        mandatory=True,
    )
    channel, method, _props, body = wait_message(consumer)
    assert consume_delivery(OutboxStore(case.factory), channel, method, body) == "quarantined"
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        method, _props, body = ch.basic_get(
            publisher.settings.queue + ".quarantine", auto_ack=False
        )
        if method:
            assert body == b"{invalid-json"
            ch.basic_ack(method.delivery_tag)
            break
        publisher.connection.process_data_events(time_limit=0.02)
    else:
        pytest.fail("Real broker dead-letter routing failed")
