"""Injected persistence faults over actual HTTP; no claim of real component failure."""

import pytest
from t44.persistence import CommitUncertain, PersistenceUnavailable

from .test_http import login, request

pytestmark = [pytest.mark.contract, pytest.mark.fault]


class FaultFactory:
    def __init__(self, underlying, fail_table=None, uncertain=False):
        self.underlying, self.fail_table, self.uncertain = underlying, fail_table, uncertain

    def __call__(self):
        parent = self
        uow = self.underlying()

        class Scope:
            def __enter__(self):
                uow.__enter__()
                return self

            @property
            def gateway(self):
                original = uow.gateway

                class Gateway:
                    def insert(self, table, values):
                        if table == parent.fail_table:
                            raise PersistenceUnavailable("Injected persistence failure")
                        return original.insert(table, values)

                    def __getattr__(self, name):
                        return getattr(original, name)

                return Gateway()

            def __exit__(self, typ, value, traceback):
                uow.__exit__(typ, value, traceback)
                if typ is None and parent.uncertain:
                    parent.uncertain = False
                    raise CommitUncertain("Injected lost acknowledgement")

        return Scope()


def test_rejection_audit_failure_is_503_no_false_audit_id(application):
    client, factory = application
    token = login(client)
    client.app.state.runtime.factory = FaultFactory(factory, fail_table="audit_events")
    response = request(client, "createProject", token=token, body={}, expect=503)
    assert response.json()["code"] == "AUDIT_UNAVAILABLE"
    assert response.json()["audit_id"] is None
    assert response.json()["original_error_code"] == "PARAMETER_INVALID"


def test_outbox_failure_rolls_back_business_change_and_leaves_retryable_key(application):
    client, factory = application
    token = login(client)
    client.app.state.runtime.factory = FaultFactory(factory, fail_table="outbox_events")
    response = request(
        client, "createProject", token=token, body={"name": "Must roll back"}, expect=503
    )
    assert response.json()["code"] == "DEPENDENCY_UNAVAILABLE"
    with factory() as uow:
        assert uow.gateway.count("projects") == 0
        assert uow.gateway.count("project_members") == 0
        assert uow.gateway.count("idempotency_requests", {"status": 2}) == 0


def test_missing_notification_dependency_returns_real_503(application):
    client, _ = application
    token = login(client)
    request(client, "listMyNotifications", token=token, expect=503)
