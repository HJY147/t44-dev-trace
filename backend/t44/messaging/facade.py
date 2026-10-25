"""Notification operations inside the caller's authenticated business transaction."""

from t44.persistence import Pred
from t44.services.common import model, page
from t44.services.errors import require


def notification(row):
    return model("Notification", row, fallback=bool(row["fallback"]))


class NotificationFacade:
    def _projects(self, g, actor_id, project_id=None):
        where = {"user_id": actor_id, "active": 1}
        if project_id is not None:
            require(g.get("projects", project_id), "RESOURCE_NOT_FOUND")
            where["project_id"] = project_id
        members = g.rows(
            "project_members",
            where,
            order_by=("project_id", "user_id"),
            lock="share",
        )
        if project_id is not None:
            require(members, "PROJECT_ACCESS_DENIED")
        return [member["project_id"] for member in members]

    def list(self, g, *, actor_id, query):
        where = {
            "recipient_id": actor_id,
            "project_id": self._projects(g, actor_id, query.get("project_id")),
        }
        predicates = tuple(
            Pred(column, "ne" if query[key] else "is_null", None)
            for key, column in (("read", "read_at"), ("handled", "handled_at"))
            if key in query
        )
        result = page(
            g,
            "notifications",
            where,
            {**query, "sort": "-id"},
            notification,
            predicates=predicates,
        )
        for name, column in (("unread_count", "read_at"), ("unhandled_count", "handled_at")):
            result[name] = g.count(
                "notifications",
                where,
                predicates=(Pred(column, "is_null"),),
            )
        return result

    def _update(self, g, *, actor_id, project_id, notification_id, version, values):
        self._projects(g, actor_id, project_id)
        row = g.get("notifications", notification_id, lock="update")
        require(row and row["project_id"] == project_id, "RESOURCE_NOT_FOUND")
        require(row["recipient_id"] == actor_id, "ACTION_FORBIDDEN")
        require(
            row["version"] == version and version < 2147483647,
            "VERSION_CONFLICT",
            current_version=row["version"],
        )
        values = {**values(row), "version": version + 1}
        require(
            g.update("notifications", {"id": notification_id, "version": version}, values) == 1,
            "VERSION_CONFLICT",
            current_version=row["version"],
        )
        return notification({**row, **values})

    def mark_read(self, g, *, actor_id, project_id, notification_id, version, now):
        return self._update(
            g,
            actor_id=actor_id,
            project_id=project_id,
            notification_id=notification_id,
            version=version,
            values=lambda row: {"read_at": row["read_at"] or now},
        )

    def handle(self, g, *, actor_id, project_id, notification_id, version, note, evidence, now):
        require(bool(evidence), "EVIDENCE_REQUIRED")
        return self._update(
            g,
            actor_id=actor_id,
            project_id=project_id,
            notification_id=notification_id,
            version=version,
            values=lambda row: {
                "handled_at": now,
                "handling_note": note,
                "handling_evidence": evidence,
            },
        )
