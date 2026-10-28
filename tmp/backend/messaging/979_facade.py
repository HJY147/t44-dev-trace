from concurrent.futures import ThreadPoolExecutor, TimeoutError
from importlib import import_module
from threading import Barrier, Event

import pytest
from fastapi.testclient import TestClient
from t44.api import create_app
from t44.contracts import violations
from t44.persistence.delivery import OutboxStore
from t44.services.common import SCHEMAS
from t44.services.errors import Rejected
from t44.settings import Settings

NotificationFacade = import_module(
    "tmp.780_messaging_component_20261028.legacy_caller"
).NotificationFacade


def notices(case):
    eid = case.event(recipients=[case.user, case.other])
    OutboxStore(case.factory).consume(eid)
    with case.factory() as uow:
        return uow.gateway.rows("notifications", {"event_id": eid})


def test_scope_pagination_counts_and_boolean_wire(case):
    notices(case)
    notices(case)
    facade = NotificationFacade()
    with case.factory() as uow:
        result = facade.list(uow.gateway, actor_id=case.user, query={"page_size": 1})
        assert result["total"] == result["unread_count"] == result["unhandled_count"] == 2
        assert len(result["items"]) == 1 and result["items"][0]["fallback"] is False
        assert not violations({"$ref": "#/components/schemas/NotificationPage"}, result)
        empty = facade.list(uow.gateway, actor_id=case.outsider, query={})
        assert empty["items"] == [] and empty["total"] == 0
    with case.factory() as uow:
        uow.gateway.update(
            "project_members", {"project_id": case.project, "user_id": case.user}, {"active": 0}
        )
    with case.factory() as uow:
        assert facade.list(uow.gateway, actor_id=case.user, query={})["total"] == 0
        with pytest.raises(Rejected, match="PROJECT_ACCESS_DENIED"):
            facade.list(uow.gateway, actor_id=case.user, query={"project_id": case.project})


def test_read_handled_independent_cas_and_no_task_change(case):
    notice = notices(case)[0]
    facade = NotificationFacade()
    with case.factory() as uow:
        g = uow.gateway
        task_before = g.get("tasks", notice["task_id"])
        result = facade.mark_read(
            g,
            actor_id=case.user,
            project_id=case.project,
            notification_id=notice["id"],
            version=1,
            now=case.now,
        )
        assert result["version"] == 2 and result["read_at"] and result["handled_at"] is None
    with case.factory() as uow, pytest.raises(Rejected, match="VERSION_CONFLICT") as exc:
        facade.handle(
            uow.gateway,
            actor_id=case.user,
            project_id=case.project,
            notification_id=notice["id"],
            version=1,
            note="stale",
            evidence=[{}],
            now=case.now,
        )
    assert exc.value.current_version == 2
    evidence = [{"kind": 1, "reference": "synthetic/module-evidence", "description": "模块证据"}]
    with case.factory() as uow:
        result = facade.handle(
            uow.gateway,
            actor_id=case.user,
            project_id=case.project,
            notification_id=notice["id"],
            version=2,
            note="已核查",
            evidence=evidence,
            now=case.now,
        )
        assert result["version"] == 3 and result["handled_at"] and result["read_at"]
        assert not violations({"$ref": "#/components/schemas/Notification"}, result)
        assert uow.gateway.get("tasks", notice["task_id"]) == task_before
        saved = uow.gateway.get("notifications", notice["id"])
        assert saved["handling_evidence"] == evidence
        page = facade.list(uow.gateway, actor_id=case.user, query={"read": False})
        assert page["total"] == 0 and page["unhandled_count"] == 0


def test_recipient_membership_and_handling_does_not_read(case):
    own, other = notices(case)
    facade = NotificationFacade()
    with case.factory() as uow, pytest.raises(Rejected, match="ACTION_FORBIDDEN"):
        facade.mark_read(
            uow.gateway,
            actor_id=case.user,
            project_id=case.project,
            notification_id=other["id"],
            version=1,
            now=case.now,
        )
    with case.factory() as uow, pytest.raises(Rejected, match="EVIDENCE_REQUIRED"):
        facade.handle(
            uow.gateway,
            actor_id=case.user,
            project_id=case.project,
            notification_id=own["id"],
            version=1,
            note="empty",
            evidence=[],
            now=case.now,
        )
    with case.factory() as uow:
        result = facade.handle(
            uow.gateway,
            actor_id=case.user,
            project_id=case.project,
            notification_id=own["id"],
            version=1,
            note="合成处理",
            evidence=[{"kind": 1, "reference": "test", "description": "证据"}],
            now=case.now,
        )
        assert result["read_at"] is None and result["handled_at"]
        uow.gateway.update(
            "project_members", {"project_id": case.project, "user_id": case.user}, {"active": 0}
        )
    with case.factory() as uow, pytest.raises(Rejected, match="PROJECT_ACCESS_DENIED"):
        facade.mark_read(
            uow.gateway,
            actor_id=case.user,
            project_id=case.project,
            notification_id=own["id"],
            version=2,
            now=case.now,
        )


def test_real_http_notification_signature_idempotency_and_error(case):
    notice = notices(case)[0]
    with case.factory() as uow:
        name = uow.gateway.get("users", case.user)["username"]
    with TestClient(create_app(factory=case.factory, settings=Settings())) as client:
        login = client.post(
            "/api/v1/auth/login", json={"username": name, "password": "synthetic-module-password"}
        )
        assert login.status_code == 200, login.json()
        token = login.json()["data"]["access_token"]
        headers = {"Authorization": "Bearer " + token, "Idempotency-Key": "msg-read-test-001"}
        url = f"/api/v1/projects/{case.project}/notifications/{notice['id']}/read"
        first = client.post(url, headers=headers, json={"expected_version": 1})
        assert first.status_code == 200, first.json()
        assert first.json()["data"]["fallback"] is False
        assert (
            client.post(url, headers=headers, json={"expected_version": 1}).json()["meta"][
                "replayed"
            ]
            is True
        )
        headers["Idempotency-Key"] = "msg-read-test-002"
        assert client.post(url, headers=headers, json={"expected_version": 1}).status_code == 409
        result = client.get("/api/v1/me/notifications", headers=headers)
        assert result.status_code == 200 and result.json()["data"]["unread_count"] == 0
        assert result.json()["data"]["unhandled_count"] == 1
        assert set(first.json()["data"]) == set(SCHEMAS["Notification"]["properties"])


@pytest.mark.integration
@pytest.mark.parametrize("factory", ["mysql"], indirect=True)
def test_real_mysql_concurrent_notification_cas_exactly_one_update(case):
    notice, gate = notices(case)[0], Barrier(2)

    def update():
        gate.wait()
        try:
            with case.factory() as uow:
                return NotificationFacade().mark_read(
                    uow.gateway,
                    actor_id=case.user,
                    project_id=case.project,
                    notification_id=notice["id"],
                    version=1,
                    now=case.now,
                )["version"]
        except Rejected as error:
            return error.code

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(lambda _: update(), range(2)))
    assert outcomes.count(2) == 1 and outcomes.count("VERSION_CONFLICT") == 1


@pytest.mark.integration
@pytest.mark.parametrize("factory", ["mysql"], indirect=True)
def test_real_mysql_list_scope_serializes_with_membership_revocation(case):
    notices(case)
    started = Event()

    def revoke():
        with case.factory() as uow:
            started.set()
            uow.gateway.update(
                "project_members",
                {"project_id": case.project, "user_id": case.user},
                {"active": 0},
            )

    with ThreadPoolExecutor(max_workers=1) as pool:
        with case.factory() as uow:
            result = NotificationFacade().list(uow.gateway, actor_id=case.user, query={})
            assert result["total"] == 1
            pending = pool.submit(revoke)
            assert started.wait(2)
            with pytest.raises(TimeoutError):
                pending.result(timeout=0.1)
        pending.result(timeout=3)
    with case.factory() as uow:
        assert NotificationFacade().list(uow.gateway, actor_id=case.user, query={})["total"] == 0
