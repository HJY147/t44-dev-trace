"""Explicit persistence-to-contract codecs and request context."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from t44.contracts import SPEC
from t44.persistence.codecs import hours_to_quarters

from .errors import require

SCHEMAS = SPEC["components"]["schemas"]


def now():
    return datetime.now(UTC)


def wire(value):
    if isinstance(value, datetime):
        return value.astimezone(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, dict):
        return {key: wire(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [wire(item) for item in value]
    return value


def time(value):
    return datetime.fromisoformat(value)


def roles(mask):
    return [role for role, bit in ((1, 1), (2, 2), (3, 4)) if mask & bit]


def mask(values):
    return sum({1: 1, 2: 2, 3: 4}[value] for value in values)


def model(name, row, **extra):
    values = {**row, **extra}
    return wire({key: values[key] for key in SCHEMAS[name]["properties"]})


def plan(row, *, iteration=False):
    result = {key: row[key] for key in ("planned_start", "planned_end", "delay_contingency")}
    result["buffer_hours"] = row["buffer_quarters"] / 4
    if iteration:
        result.update(name=row["name"], capacity=row["capacity"])
    else:
        result["estimated_hours"] = row["estimated_quarters"] / 4
    return wire(result)


def plan_values(payload):
    require(time(payload["planned_start"]) < time(payload["planned_end"]), "TIME_RANGE_INVALID")
    result = {key: time(payload[key]) for key in ("planned_start", "planned_end")}
    result.update(
        buffer_quarters=hours_to_quarters(payload["buffer_hours"]),
        delay_contingency=payload["delay_contingency"],
    )
    if "estimated_hours" in payload:
        result["estimated_quarters"] = hours_to_quarters(payload["estimated_hours"])
    else:
        result.update(name=payload["name"], capacity=payload["capacity"])
    return result


def task_model(row):
    return model("Task", row, plan=plan(row))


def page(g, table, where, query, serialize, *, predicates=(), prepare=None):
    p, size = query.get("page", 1), query.get("page_size", 20)
    rows = g.rows(
        table,
        where,
        order_by=(query.get("sort", "id"), "id"),
        offset=(p - 1) * size,
        limit=size,
        predicates=predicates,
    )
    if prepare is not None:
        serialize = prepare(rows)
    return {
        "items": [serialize(row) for row in rows],
        "page": p,
        "page_size": size,
        "total": g.count(table, where, predicates=predicates),
    }


@dataclass
class Call:
    operation: str
    request_id: str
    token: str | None
    path: dict = field(default_factory=dict)
    query: dict = field(default_factory=dict)
    body: dict = field(default_factory=dict)
    key: str | None = None
    actor: dict | None = None
    membership: dict | None = None
    project: dict | None = None
    audit_id: int | None = None
    idem: dict | None = None
    before: list = field(default_factory=list)
    after: list = field(default_factory=list)
    clock: datetime = field(default_factory=now)

    @property
    def project_id(self):
        return self.path.get("project_id")

    @property
    def actor_id(self):
        return self.actor["actor_id"] if self.actor else None

    def manager(self):
        require(self.membership and self.membership["roles_mask"] & 1, "ACTION_FORBIDDEN")

    def reviewer(self):
        require(self.membership and self.membership["roles_mask"] & 5, "ACTION_FORBIDDEN")

    def task(self, g, *, lock=None):
        return self.resource(g, "tasks", self.path["task_id"], lock=lock)

    def resource(self, g, table, identifier, *, parent="project_id", lock=None):
        row = g.get(table, identifier, lock=lock)
        require(row and row[parent] == self.path[parent], "RESOURCE_NOT_FOUND")
        return row

    def members(self, g, where=None, **options):
        return g.rows(
            "project_members", {"project_id": self.project_id, **(where or {})}, **options
        )

    def create(self, g, table, values, **options):
        return g.get(table, self.insert(g, table, values, **options))

    def insert(self, g, table, values, *, actor_field=None, updated=False, project=True):
        """Trusted handler fields only; request bodies never choose a table or context field."""
        values = {**values, "created_at": self.clock}
        if project:
            values["project_id"] = self.project_id
        if updated:
            values["updated_at"] = self.clock
        if actor_field:
            values[actor_field] = self.actor_id
        return g.insert(table, values)

    def check_version(self, row, *, expected=None):
        expected = self.body.get("expected_version") if expected is None else expected
        require(
            row["version"] == expected and row["version"] < 2147483647,
            "VERSION_CONFLICT",
            current_version=row["version"],
            current_state=row.get("state"),
        )
        return expected

    def cas(self, g, table, row, values, *, expected=None, record_diff=True):
        expected = self.check_version(row, expected=expected)
        values = {**values, "version": row["version"] + 1}
        if "updated_at" in row:
            values["updated_at"] = self.clock
        require(
            g.update(table, {"id": row["id"], "version": expected}, values) == 1,
            "VERSION_CONFLICT",
            current_version=row["version"],
            current_state=row.get("state"),
        )
        if record_diff:
            self.before = [{"field": "version", "value": str(row["version"])}]
            self.after = [{"field": "version", "value": str(values["version"])}]
        return {**row, **values}


def uuid_text(value):
    return str(UUID(bytes=value))
