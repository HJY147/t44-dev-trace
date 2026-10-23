"""Task registration, immutable execution boundaries, and dependency graph policy."""

from .common import model, page, plan_values, task_model
from .errors import require


class Tasks:
    def owner(self, g, c, identifier):
        rows = g.rows(
            "project_members",
            {"project_id": c.project_id, "user_id": identifier, "active": 1},
            limit=1,
        )
        require(rows and rows[0]["roles_mask"] & 2, "OWNER_NOT_PROJECT_DEVELOPER")

    def iteration(self, g, c, identifier):
        row = g.get("iterations", identifier)
        require(row and row["project_id"] == c.project_id, "RESOURCE_NOT_FOUND")

    def prestart(self, row):
        return row["state"] == 1 or (row["state"] == 3 and row["blocked_from_state"] == 1)

    def dependency_model(self, g, row):
        predecessor = g.get("tasks", row["depends_on_task_id"])
        return model("Dependency", row, satisfied=predecessor["state"] == 6)

    def check_graph(self, g, c, identifier, dependencies):
        require(identifier not in dependencies, "DEPENDENCY_SELF_REFERENCE")
        rows = g.rows(
            "tasks", {"project_id": c.project_id, "id": list(dependencies)}, lock="update"
        )
        require(len(rows) == len(set(dependencies)), "RESOURCE_NOT_FOUND")
        adjacency = {}
        for edge in g.rows("task_dependencies", {"project_id": c.project_id}):
            adjacency.setdefault(edge["task_id"], []).append(edge["depends_on_task_id"])
        adjacency.setdefault(identifier, []).extend(dependencies)
        # Iterative traversal handles long chains without recursion limits.
        for predecessor in dependencies:
            visited, stack = set(), [predecessor]
            while stack:
                node = stack.pop()
                require(node != identifier, "DEPENDENCY_CYCLE")
                if node not in visited:
                    visited.add(node)
                    stack.extend(adjacency.get(node, ()))

    def createTask(self, g, c):
        c.manager()
        self.owner(g, c, c.body["owner_id"])
        self.iteration(g, c, c.body["iteration_id"])
        values = plan_values(c.body["plan"])
        dependencies = c.body["dependency_task_ids"]
        # Project lock is held before task IDs are locked in ascending order.
        self.check_graph(g, c, None, dependencies)
        identifier = g.insert(
            "tasks",
            {
                **values,
                "project_id": c.project_id,
                "iteration_id": c.body["iteration_id"],
                "title": c.body["title"],
                "description": c.body.get("description", ""),
                "owner_id": c.body["owner_id"],
                "state": 1,
                "version": 1,
                "schedule_version": 1,
                "delivery_cycle": 1,
                "review_cycle": 1,
                "blocked_from_state": None,
                "block_reason": None,
                "responsibility_stage": None,
                "artifact_revision": None,
                "latest_review_id": None,
                "approved_review_id": None,
                "approved_assessment_id": None,
                "approved_assessment_version": None,
                "escalation_count": 0,
                "created_at": c.clock,
                "updated_at": c.clock,
            },
        )
        for predecessor in dependencies:
            g.insert(
                "task_dependencies",
                {
                    "project_id": c.project_id,
                    "task_id": identifier,
                    "depends_on_task_id": predecessor,
                    "created_by": c.actor_id,
                    "created_at": c.clock,
                },
            )
        c.path["task_id"] = identifier
        return {"task": task_model(g.get("tasks", identifier))}

    def listTasks(self, g, c):
        where = {
            "project_id": c.project_id,
            **{k: v for k, v in c.query.items() if k in ("state", "owner_id", "iteration_id")},
        }
        return page(g, "tasks", where, c.query, task_model)

    def getTask(self, g, c):
        return task_model(c.task(g))

    def changeTaskPlan(self, g, c):
        c.manager()
        row = c.task(g)
        require(row["state"] not in (6, 7), "STATE_CONFLICT", current_state=row["state"])
        changed = c.cas(
            g,
            "tasks",
            row,
            {
                **plan_values(c.body["plan"]),
                "schedule_version": row["schedule_version"] + 1,
                "approved_assessment_id": None,
                "approved_assessment_version": None,
            },
        )
        self.schedule_diff(g, c, row, changed)
        return {"task": task_model(changed)}

    def changeTaskAssignment(self, g, c):
        c.manager()
        row = c.task(g)
        require(self.prestart(row), "ASSIGNMENT_EDIT_LOCKED", current_state=row["state"])
        self.owner(g, c, c.body["owner_id"])
        changed = c.cas(g, "tasks", row, {"owner_id": c.body["owner_id"]})
        return {"task": task_model(changed)}

    def listTaskDependencies(self, g, c):
        c.task(g)
        return page(
            g,
            "task_dependencies",
            {"project_id": c.project_id, "task_id": c.path["task_id"]},
            c.query,
            lambda r: self.dependency_model(g, r),
        )

    def addTaskDependency(self, g, c):
        c.manager()
        row = c.task(g)
        require(self.prestart(row), "DEPENDENCY_EDIT_LOCKED", current_state=row["state"])
        predecessor = c.body["depends_on_task_id"]
        existing = g.rows(
            "task_dependencies", {"task_id": row["id"], "depends_on_task_id": predecessor}
        )
        require(not existing, "STATE_CONFLICT")
        self.check_graph(g, c, row["id"], [predecessor])
        changed = c.cas(g, "tasks", row, {})
        identifier = g.insert(
            "task_dependencies",
            {
                "project_id": c.project_id,
                "task_id": row["id"],
                "depends_on_task_id": predecessor,
                "created_by": c.actor_id,
                "created_at": c.clock,
            },
        )
        return {
            "task": task_model(changed),
            "dependency": self.dependency_model(g, g.get("task_dependencies", identifier)),
        }

    def removeTaskDependency(self, g, c):
        c.manager()
        row = c.task(g)
        require(self.prestart(row), "DEPENDENCY_EDIT_LOCKED", current_state=row["state"])
        edge = g.get("task_dependencies", c.path["dependency_id"])
        require(
            edge and edge["task_id"] == row["id"] and edge["project_id"] == c.project_id,
            "RESOURCE_NOT_FOUND",
        )
        changed = c.cas(g, "tasks", row, {})
        g.delete("task_dependencies", {"id": edge["id"]})
        return {"task": task_model(changed)}
