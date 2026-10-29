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

    def list(self, g, c):
        actor_id, query = c.actor_id, c.query
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

    def _update(self, g, c, values):
        self._projects(g, c.actor_id, c.project_id)
        row = g.get("notifications", c.path["notification_id"], lock="update")
        require(row and row["project_id"] == c.project_id, "RESOURCE_NOT_FOUND")
        require(row["recipient_id"] == c.actor_id, "ACTION_FORBIDDEN")
        c.check_version(row)
        changed = c.cas(g, "notifications", row, values(row), record_diff=False)
        return notification(changed)

    def mark_read(self, g, c):
        return self._update(g, c, lambda row: {"read_at": row["read_at"] or c.clock})

    def handle(self, g, c):
        require(bool(c.body["evidence"]), "EVIDENCE_REQUIRED")
        return self._update(
            g,
            c,
            lambda row: {
                "handled_at": c.clock,
                "handling_note": c.body["note"],
                "handling_evidence": c.body["evidence"],
            },
        )
