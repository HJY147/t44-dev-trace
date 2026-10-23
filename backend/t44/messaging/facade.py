"""Notification operations inside the caller's authenticated business transaction."""

from t44.persistence import Pred
from t44.services.common import model
from t44.services.errors import require


def notification(row):
    return model("Notification", row, fallback=bool(row["fallback"]))


class NotificationFacade:
    def _membership(self, g, actor_id, project_id, *, lock=None):
        require(g.get("projects", project_id), "RESOURCE_NOT_FOUND")
        members = g.rows(
            "project_members",
            {"project_id": project_id, "user_id": actor_id, "active": 1},
            lock=lock,
        )
        require(members, "PROJECT_ACCESS_DENIED")

    def list(self, g, *, actor_id, query):
        if project_id := query.get("project_id"):
            self._membership(g, actor_id, project_id, lock="share")
            projects = [project_id]
        else:
            projects = [
                m["project_id"]
                for m in g.rows(
                    "project_members",
                    {"user_id": actor_id, "active": 1},
                    order_by=("project_id", "user_id"),
                    lock="share",
                )
            ]
        where = {"recipient_id": actor_id, "project_id": projects}
        predicates = tuple(
            Pred(column, "ne" if query[key] else "is_null", None)
            for key, column in (("read", "read_at"), ("handled", "handled_at"))
            if key in query
        )
        page, size = query.get("page", 1), query.get("page_size", 20)
        rows = g.rows(
            "notifications",
            where,
            predicates=predicates,
            order_by=("-id",),
            limit=size,
            offset=(page - 1) * size,
        )
        return {
            "items": [notification(row) for row in rows],
            "page": page,
            "page_size": size,
            "total": g.count("notifications", where, predicates=predicates),
            "unread_count": g.count(
                "notifications", where, predicates=(Pred("read_at", "is_null"),)
            ),
            "unhandled_count": g.count(
                "notifications", where, predicates=(Pred("handled_at", "is_null"),)
            ),
        }

    def _update(self, g, *, actor_id, project_id, notification_id, version, values):
        self._membership(g, actor_id, project_id, lock="share")
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
