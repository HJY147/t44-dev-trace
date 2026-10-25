"""Public behavior properties for messaging's structure-only reduction; no external services."""

import json
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
from t44.messaging.facade import NotificationFacade
from t44.persistence import PersistenceUnavailable, StatementRejected
from t44.persistence.delivery import OutboxStore
from t44.services.errors import Rejected


@pytest.mark.parametrize("operation", ["publish", "get", "keepalive"])
@pytest.mark.parametrize(
    "failure", [OSError("synthetic"), pika.exceptions.AMQPConnectionError("synthetic")]
)
def test_transport_operations_preserve_error_class_and_cleanup(operation, failure):
    connection, channel = Mock(), Mock()
    connection.channel.return_value = channel
    broker = PikaBroker(
        BrokerSettings("amqp://localhost/"), connect=Mock(return_value=connection)
    )
    broker._channel()
    if operation == "publish":
        channel.basic_publish.side_effect = failure
        invoke = lambda: broker.publish({"id": 1, "schema_version": 1, "event_type": 2})
        code = "BROKER_PUBLISH_FAILED"
    else:
        connection.process_data_events.side_effect = failure
        invoke = getattr(broker, operation)
        code = (
            "BROKER_RECEIVE_FAILED" if operation == "get" else "BROKER_HEARTBEAT_FAILED"
        )
    with pytest.raises(BrokerUnavailable, match=code) as error:
        invoke()
    assert str(error.value) == code and error.value.__suppress_context__
    assert broker.connection is broker.channel is None
    connection.close.assert_called_once()


@pytest.mark.parametrize("failure", [ValueError("config"), OSError("socket")])
def test_connect_error_is_not_reclassified_as_publish_error(failure):
    broker = PikaBroker(
        BrokerSettings("amqp://localhost/"), connect=Mock(side_effect=failure)
    )
    with pytest.raises(BrokerUnavailable, match="^BROKER_CONNECT_FAILED$"):
        broker.publish({"id": 1, "schema_version": 1, "event_type": 2})
    assert broker.connection is None


def test_false_nack_and_unexpected_application_error_keep_their_boundary():
    connection, channel = Mock(), Mock()
    connection.channel.return_value = channel
    broker = PikaBroker(
        BrokerSettings("amqp://localhost/"), connect=Mock(return_value=connection)
    )
    channel.basic_publish.return_value = False
    with pytest.raises(BrokerUnavailable, match="^BROKER_NACK$"):
        broker.publish({"id": 1, "schema_version": 1, "event_type": 2})
    assert broker.connection is connection
    channel.basic_publish.side_effect = ValueError("application")
    with pytest.raises(ValueError, match="application"):
        broker.publish({"id": 1, "schema_version": 1, "event_type": 2})
    connection.close.assert_not_called()


@pytest.mark.parametrize(
    "failure", [StatementRejected("bad ledger"), UnicodeError("bad encoding")]
)
def test_value_error_subclasses_still_quarantine_without_ack(failure):
    store, channel = Mock(), Mock()
    store.get.side_effect = failure
    result = consume_delivery(
        store,
        channel,
        SimpleNamespace(delivery_tag=7),
        json.dumps(
            {
                "event_id": 1,
                "schema_version": 1,
                "event_type": 2,
            }
        ).encode(),
    )
    assert result == "quarantined"
    channel.basic_reject.assert_called_once_with(delivery_tag=7, requeue=False)
    channel.basic_ack.assert_not_called()
    channel.basic_nack.assert_not_called()


def test_database_failure_requeues_without_hiding_the_failure():
    store, channel = Mock(), Mock()
    store.get.side_effect = PersistenceUnavailable("database")
    with pytest.raises(PersistenceUnavailable):
        consume_delivery(
            store,
            channel,
            SimpleNamespace(delivery_tag=7),
            json.dumps(
                {
                    "event_id": 1,
                    "schema_version": 1,
                    "event_type": 2,
                }
            ).encode(),
        )
    channel.basic_nack.assert_called_once_with(delivery_tag=7, requeue=True)
    channel.basic_ack.assert_not_called()


def test_project_error_priority_and_membership_lock_are_preserved():
    facade, gateway = NotificationFacade(), Mock()
    gateway.get.return_value = None
    with pytest.raises(Rejected, match="RESOURCE_NOT_FOUND"):
        facade.list(gateway, actor_id=1, query={"project_id": 2})
    gateway.rows.assert_not_called()
    gateway.get.return_value = {"id": 2}
    gateway.rows.return_value = []
    with pytest.raises(Rejected, match="PROJECT_ACCESS_DENIED"):
        facade.list(gateway, actor_id=1, query={"project_id": 2})
    assert gateway.rows.call_args.kwargs["lock"] == "share"
    assert gateway.rows.call_args.args[1] == {
        "project_id": 2,
        "user_id": 1,
        "active": 1,
    }


@pytest.mark.parametrize("read", [None, False, True])
@pytest.mark.parametrize("handled", [None, False, True])
def test_pagination_and_unfiltered_counts_are_independent_properties(
    case, read, handled
):
    store = OutboxStore(case.factory)
    for index in range(4):
        eid = case.event(recipients=[case.user, case.other])
        store.consume(eid)
        with case.factory() as uow:
            own = uow.gateway.rows(
                "notifications", {"event_id": eid, "recipient_id": case.user}
            )[0]
            values = {}
            if index & 1:
                values["read_at"] = case.now
            if index & 2:
                values.update(
                    handled_at=case.now,
                    handling_note="synthetic",
                    handling_evidence=[{}],
                )
            if values:
                uow.gateway.update("notifications", {"id": own["id"]}, values)
    query = {"project_id": case.project, "page_size": 1, "page": 2}
    for name, value in [("read", read), ("handled", handled)]:
        if value is not None:
            query[name] = value
    with case.factory() as uow:
        result = NotificationFacade().list(uow.gateway, actor_id=case.user, query=query)
    expected = [
        index
        for index in range(4)
        if (read is None or bool(index & 1) == read)
        and (handled is None or bool(index & 2) == handled)
    ]
    assert result["total"] == len(expected)
    assert result["unread_count"] == result["unhandled_count"] == 2
    assert len(result["items"]) == int(len(expected) > 1)
    assert all(
        item["recipient_id"] == case.user and item["fallback"] is False
        for item in result["items"]
    )
