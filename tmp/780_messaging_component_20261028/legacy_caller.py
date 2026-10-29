"""Test-only old fixture caller adapter; production exposes only the new Call API."""

from t44.messaging.facade import NotificationFacade as CurrentFacade
from t44.services.common import Call


def context(actor_id, *, query=None, project_id=None, notification_id=None,
            version=None, now=None, note=None, evidence=None):
    values = {"clock": now} if now is not None else {}
    return Call(
        "notification-fixture", "synthetic-old-caller", None,
        actor={"actor_id": actor_id}, query=query or {},
        path={"project_id": project_id, "notification_id": notification_id},
        body={"expected_version": version, "note": note, "evidence": evidence},
        **values,
    )


class NotificationFacade(CurrentFacade):
    def list(self, g, **values):
        return super().list(g, context(**values))

    def mark_read(self, g, **values):
        return super().mark_read(g, context(**values))

    def handle(self, g, **values):
        return super().handle(g, context(**values))
