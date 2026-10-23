"""Project membership and iteration planning, using the injected parameterized gateway."""

from .codes import State
from .common import mask, model, page, plan, plan_values, roles
from .errors import require


class Projects:
    def project_model(self, row, membership):
        return model("Project", row, my_roles=roles(membership["roles_mask"]))

    def member_model(self, g, row):
        return model(
            "Member",
            row,
            user=model("User", g.get("users", row["user_id"])),
            roles=roles(row["roles_mask"]),
            active=bool(row["active"]),
        )

    def createProject(self, g, c):
        c.project = c.create(
            g,
            "projects",
            {"name": c.body["name"], "description": c.body.get("description", "")},
            actor_field="created_by",
            updated=True,
            project=False,
        )
        c.path["project_id"] = c.project["id"]
        member = c.create(
            g, "project_members", {"user_id": c.actor_id, "roles_mask": 1}, updated=True
        )
        return self.project_model(c.project, member)

    def listProjects(self, g, c):
        memberships = g.rows("project_members", {"user_id": c.actor_id, "active": 1})
        by_project = {m["project_id"]: m for m in memberships}
        return page(
            g,
            "projects",
            {"id": list(by_project)},
            c.query,
            lambda r: self.project_model(r, by_project[r["id"]]),
        )

    def getProject(self, g, c):
        return self.project_model(c.project, c.membership)

    def listProjectMembers(self, g, c):
        return page(
            g,
            "project_members",
            {"project_id": c.project_id, "active": 1},
            c.query,
            lambda r: self.member_model(g, r),
        )

    def addProjectMember(self, g, c):
        c.manager()
        users = g.rows("users", {"username": c.body["username"], "active": 1}, limit=1)
        require(users, "ACCOUNT_NOT_INITIALIZED")
        user_id = users[0]["id"]
        existing = g.rows(
            "project_members",
            {"project_id": c.project_id, "user_id": user_id},
            lock="update",
            limit=1,
        )
        if existing and existing[0]["active"]:
            return self.member_model(g, existing[0])
        values = {"roles_mask": mask(c.body["roles"]), "active": 1}
        if existing:
            row = c.cas(g, "project_members", existing[0], values, expected=existing[0]["version"])
        else:
            row = c.create(g, "project_members", {**values, "user_id": user_id}, updated=True)
        return self.member_model(g, row)

    def _change_member(self, g, c, remove):
        c.manager()
        rows = g.rows(
            "project_members",
            {"project_id": c.project_id, "user_id": c.path["user_id"], "active": 1},
            lock="update",
            limit=1,
        )
        require(rows, "RESOURCE_NOT_FOUND")
        row = rows[0]
        new_mask = row["roles_mask"] if remove else mask(c.body["roles"])
        members = g.rows("project_members", {"project_id": c.project_id, "active": 1})
        if row["roles_mask"] & 1 and (remove or not new_mask & 1):
            require(sum(bool(m["roles_mask"] & 1) for m in members) > 1, "LAST_MANAGER")
        if remove or not new_mask & 2:
            active = g.rows(
                "tasks",
                {
                    "project_id": c.project_id,
                    "owner_id": row["user_id"],
                    "state": [
                        State.PENDING,
                        State.DEVELOPING,
                        State.BLOCKED,
                        State.PENDING_REVIEW,
                        State.PENDING_RELEASE,
                        State.ROLLED_BACK,
                    ],
                },
                lock="update",
            )
            require(not active, "MEMBER_IN_USE")
        changed = c.cas(
            g, "project_members", row, {"roles_mask": new_mask, "active": 0 if remove else 1}
        )
        return {"acknowledged": True} if remove else self.member_model(g, changed)

    def changeProjectMember(self, g, c):
        return self._change_member(g, c, False)

    def removeProjectMember(self, g, c):
        return self._change_member(g, c, True)

    def capacity(self, g, c, payload):
        identifiers = [entry["user_id"] for entry in payload["capacity"]]
        require(len(identifiers) == len(set(identifiers)), "CAPACITY_REFERENCE_INVALID")
        members = g.rows(
            "project_members", {"project_id": c.project_id, "user_id": identifiers, "active": 1}
        )
        require(
            len(members) == len(identifiers) and all(m["roles_mask"] & 2 for m in members),
            "CAPACITY_REFERENCE_INVALID",
        )
        return plan_values(payload)

    def iteration_model(self, row):
        return model("Iteration", row, plan=plan(row, iteration=True))

    def createIteration(self, g, c):
        c.manager()
        row = c.create(g, "iterations", self.capacity(g, c, c.body), updated=True)
        return self.iteration_model(row)

    def listIterations(self, g, c):
        return page(g, "iterations", {"project_id": c.project_id}, c.query, self.iteration_model)

    def changeIteration(self, g, c):
        c.manager()
        row = g.get("iterations", c.path["iteration_id"], lock="update")
        require(row and row["project_id"] == c.project_id, "RESOURCE_NOT_FOUND")
        values = self.capacity(g, c, c.body["plan"])
        c.check_version(row)
        owners = {entry["user_id"] for entry in values["capacity"]}
        active = g.rows(
            "tasks",
            {
                "project_id": c.project_id,
                "iteration_id": row["id"],
                "state": [
                    State.PENDING,
                    State.DEVELOPING,
                    State.BLOCKED,
                    State.PENDING_REVIEW,
                    State.PENDING_RELEASE,
                ],
            },
            order_by=("id",),
            lock="update",
        )
        require(all(task["owner_id"] in owners for task in active), "CAPACITY_REFERENCE_INVALID")
        changed = c.cas(g, "iterations", row, {**values, "plan_version": row["plan_version"] + 1})
        self.schedule_diff(g, c, row, changed, iteration=True)
        return self.iteration_model(changed)

    def schedule_diff(self, g, c, before, after, *, iteration=False):
        key = "plan_version" if iteration else "schedule_version"
        before_plan, after_plan = (
            plan(before, iteration=iteration),
            plan(after, iteration=iteration),
        )
        g.insert(
            "schedule_changes",
            {
                "project_id": c.project_id,
                "task_id": None if iteration else before["id"],
                "iteration_id": before["id"] if iteration else None,
                "from_version": before[key],
                "to_version": after[key],
                "before_plan": before_plan,
                "after_plan": after_plan,
                "reason": c.body["reason"],
                "evidence": c.body["evidence"],
                "changed_by": c.actor_id,
                "changed_at": c.clock,
            },
        )
        if not iteration:
            for side, row, value in ((c.before, before, before_plan), (c.after, after, after_plan)):
                side.extend(
                    {"field": field, "value": str(item)}
                    for field, item in {key: row[key], **value}.items()
                )
