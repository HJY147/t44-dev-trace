import json
from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import Mock

import pika
import pytest
from t44.messaging.broker import (
    BrokerSettings,
    BrokerUnavailable,
    PikaBroker,
    consume_delivery,
)
from t44.messaging.worker import DeliveryWorker
from t44.persistence import PersistenceUnavailable
from t44.persistence.codecs import utc_now
from t44.persistence.delivery import OutboxStore


def encoded(eid):
    return json.dumps(dict(event_id=eid, schema_version=1, event_type=2)).encode()


def test_persistent_confirm_mandatory_and_failed_confirmation():
    ch, conn = Mock(), Mock()
    conn.channel.return_value = ch
    broker = PikaBroker(
        BrokerSettings("amqp://hidden:secret@localhost/"),
        publisher=True,
        connect=Mock(return_value=conn),
    )
    broker.publish(dict(id=1, schema_version=1, event_type=2))
    ch.confirm_delivery.assert_called_once()
    args = ch.basic_publish.call_args.kwargs
    assert args["mandatory"] and args["properties"].delivery_mode == 2
    assert b"secret" not in args["body"]
    ch.basic_publish.side_effect = pika.exceptions.NackError([])
    with pytest.raises(BrokerUnavailable, match="BROKER_PUBLISH_FAILED"):
        broker.publish(dict(id=1, schema_version=1, event_type=2))
    conn.close.assert_called_once()


def test_ack_only_after_commit_and_transient_error_requeues():
    calls = []
    store, ch = Mock(), Mock()
    store.get.return_value = dict(id=1, schema_version=1, event_type=2)
    store.consume.side_effect = lambda _: calls.append("committed")
    ch.basic_ack.side_effect = lambda **_: calls.append("ack")
    method = SimpleNamespace(delivery_tag=7)
    assert consume_delivery(store, ch, method, encoded(1)) == "consumed"
    assert calls == ["committed", "ack"]
    store.consume.side_effect = PersistenceUnavailable("synthetic")
    ch.reset_mock()
    with pytest.raises(PersistenceUnavailable):
        consume_delivery(store, ch, method, encoded(1))
    ch.basic_nack.assert_called_once_with(delivery_tag=7, requeue=True)
    ch.basic_ack.assert_not_called()


@pytest.mark.parametrize("body", [b"{bad", b"[]", b'{"event_id":true}', encoded(99)])
def test_permanent_messages_quarantined_without_ack(body):
    store, ch = Mock(), Mock()
    store.get.return_value = None
    assert consume_delivery(store, ch, SimpleNamespace(delivery_tag=1), body) == "quarantined"
    ch.basic_reject.assert_called_once_with(delivery_tag=1, requeue=False)
    ch.basic_ack.assert_not_called()
    store.consume.assert_not_called()


def test_duplicate_delivery_ack_loss_and_fallback_restart_preserve_state(case):
    eid, store = case.event(), OutboxStore(case.factory)
    ch, method = Mock(), SimpleNamespace(delivery_tag=1)
    ch.basic_ack.side_effect = pika.exceptions.AMQPConnectionError()
    with pytest.raises(pika.exceptions.AMQPConnectionError):
        consume_delivery(store, ch, method, encoded(eid))
    with case.factory() as uow:
        notice = uow.gateway.rows("notifications", {"event_id": eid})[0]
        uow.gateway.update("notifications", {"id": notice["id"]}, {"read_at": case.now})
    # Fresh store models process restart; it cannot erase read state or create a second row.
    fresh = OutboxStore(case.factory)
    assert consume_delivery(fresh, Mock(), method, encoded(eid)) == "consumed"
    fresh.fallback(eid)
    assert fresh.consume(eid)["created"] == 0
    with case.factory() as uow:
        rows = uow.gateway.rows("notifications", {"event_id": eid})
        assert len(rows) == 1 and rows[0]["read_at"] == case.now
        assert rows[0]["fallback"] == 0
        assert uow.gateway.get("outbox_events", eid)["status"] == 4


def test_worker_failed_broker_fallback_terminal_non_escalation_retry_and_lease(case):
    escalation, changed = case.event(), case.event(event_type=1)
    store, publisher, consumer = OutboxStore(case.factory), Mock(), Mock()
    publisher.publish.side_effect = BrokerUnavailable("REAL_BROKER_NOT_USED_IN_THIS_TEST")
    consumer.get.return_value = None
    with case.factory() as uow:
        fixture_batch = uow.gateway.count("outbox_events") + 1
    # This case verifies dispatch, not that our new IDs happen to be in the first production page.
    worker = DeliveryWorker(
        store, publisher, consumer, batch_size=fixture_batch, confirmed_recovery=lambda **_: []
    )
    result = worker.cycle()
    assert result["fallback"] >= 1 and result["retried"] >= 1
    assert store.get(escalation)["status"] == 4 and store.get(changed)["status"] == 1
    assert store.get(changed)["attempts"] >= 1
    assert all(e["id"] != escalation for e in store.claim(now=utc_now() + timedelta(seconds=10)))
    assert store.consume(escalation)["created"] == 0
    with case.factory() as uow:
        assert uow.gateway.count("notifications", {"event_id": escalation}) == 1


def test_stale_lease_cannot_confirm_and_recovery_injection(case):
    eid, store = case.event(), OutboxStore(case.factory)
    first = next(e for e in store.claim(lease_seconds=1) if e["id"] == eid)
    second = next(e for e in store.claim(now=utc_now() + timedelta(seconds=2)) if e["id"] == eid)
    assert first["lease_token"] != second["lease_token"]
    assert not store.confirm(eid, first["lease_token"])
    assert store.confirm(eid, second["lease_token"])
    recovery, consumer = Mock(return_value=[dict(event_id=eid, created=1, fallback=True)]), Mock()
    consumer.get.return_value = None
    result = DeliveryWorker(store, Mock(), consumer, confirmed_recovery=recovery).cycle()
    assert result["recovered"] == 1
    assert recovery.call_args.kwargs["limit"] == 50


@pytest.mark.integration
@pytest.mark.parametrize("factory", ["mysql"], indirect=True)
def test_real_mysql_worker_default_confirmed_recovery_preserves_complete_event(case):
    missing, complete = case.event(), case.event()
    store = OutboxStore(case.factory)
    claimed = {row["id"]: row for row in store.claim(limit=10000)}
    old = utc_now() - timedelta(seconds=180)
    for eid in (missing, complete):
        assert store.confirm(eid, claimed[eid]["lease_token"], now=old)
    store.consume(complete)
    consumer = Mock()
    consumer.get.return_value = None
    # Real DB method, not the temporary injected recovery callback used in isolated unit tests.
    result = DeliveryWorker(store, Mock(), consumer).cycle()
    assert result["recovered"] >= 1 and store.get(missing)["status"] == 4
    assert store.get(complete)["status"] == 3
    with case.factory() as uow:
        assert uow.gateway.count("notifications", {"event_id": missing}) == 1
    assert DeliveryWorker(OutboxStore(case.factory), Mock(), consumer).cycle()["recovered"] == 0
