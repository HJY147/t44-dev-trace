"""Versioned, immutable review evidence and independent release-plan approval."""

import hashlib
import json
from importlib.resources import files

from .codes import State
from .common import model, task_model
from .errors import require

_TEMPLATE_BYTES = files("t44").joinpath("resources/review-template.json").read_bytes()
TEMPLATE = json.loads(_TEMPLATE_BYTES)
TEMPLATE_HASH = hashlib.sha256(_TEMPLATE_BYTES).digest()


class Reviews:
    def getReviewTemplate(self, g, c):
        require(
            c.query.get("version", TEMPLATE["version"]) == TEMPLATE["version"], "RESOURCE_NOT_FOUND"
        )
        return {**TEMPLATE, "decided_by": c.project["created_by"]}

    def review_complete(self, review):
        required = {i["item_id"] for i in TEMPLATE["items"] if i["required"]}
        passed = {i["item_id"] for i in review["checklist"] if i["judgment"] == 1 and i["evidence"]}
        return required <= passed

    def createTaskReview(self, g, c):
        c.reviewer()
        row = c.task(g)
        require(c.actor_id != row["owner_id"], "ACTION_FORBIDDEN")
        require(row["state"] == State.PENDING_REVIEW, "STATE_CONFLICT", current_state=row["state"])
        require(
            c.body["template_version"] == TEMPLATE["version"]
            and c.body["artifact_revision"] == row["artifact_revision"],
            "REVIEW_BASELINE_MISMATCH",
        )
        sections = [s["section_id"] for s in c.body["sections"]]
        items = [i["item_id"] for i in c.body["checklist"]]
        require(
            len(sections) == len(set(sections))
            and set(sections) == {s["section_id"] for s in TEMPLATE["sections"]}
            and len(items) == len(set(items))
            and set(items) == {i["item_id"] for i in TEMPLATE["items"]},
            "PARAMETER_INVALID",
        )
        require(c.body["verdict"] != 1 or self.review_complete(c.body), "EVIDENCE_REQUIRED")
        review = c.create(
            g,
            "reviews",
            {
                "task_id": row["id"],
                "delivery_cycle": row["delivery_cycle"],
                "review_cycle": row["review_cycle"],
                "template_version": TEMPLATE["version"],
                "template_hash": TEMPLATE_HASH,
                **{k: c.body[k] for k in ("artifact_revision", "sections", "checklist", "verdict")},
            },
            actor_field="reviewer_id",
        )
        changed = c.cas(g, "tasks", row, {"latest_review_id": review["id"]})
        return {"task": task_model(changed), "review": model("Review", review)}

    def createReleaseAssessment(self, g, c):
        c.manager()
        row = c.task(g)
        require(row["state"] == State.PENDING_RELEASE, "STATE_CONFLICT", current_state=row["state"])
        require(
            sorted(r["perspective"] for r in c.body["risks"]) == [1, 2, 3, 4], "PARAMETER_INVALID"
        )
        responsible = c.members(
            g, {"user_id": c.body["rollback_plan"]["responsible_user_id"], "active": 1}, limit=1
        )
        require(responsible, "RESOURCE_NOT_FOUND")
        last = g.rows(
            "release_assessments",
            {"task_id": row["id"]},
            order_by=("-rollback_plan_version",),
            limit=1,
        )
        assessment = c.create(
            g,
            "release_assessments",
            {
                "task_id": row["id"],
                "schedule_version": row["schedule_version"],
                "delivery_cycle": row["delivery_cycle"],
                "risks": c.body["risks"],
                "rollback_plan": c.body["rollback_plan"],
                "review_evidence": [],
                "rollback_plan_version": last[0]["rollback_plan_version"] + 1 if last else 1,
            },
            actor_field="created_by",
        )
        changed = c.cas(
            g,
            "tasks",
            row,
            {"approved_assessment_id": None, "approved_assessment_version": None},
        )
        return {"task": task_model(changed), "assessment": model("ReleaseAssessment", assessment)}

    def reviewReleaseAssessment(self, g, c):
        c.reviewer()
        row = c.task(g)
        assessment = c.resource(
            g, "release_assessments", c.path["assessment_id"], parent="task_id", lock="update"
        )
        require(c.actor_id != assessment["created_by"], "ACTION_FORBIDDEN")
        require(
            row["state"] == State.PENDING_RELEASE and assessment["status"] == 1,
            "STATE_CONFLICT",
            current_state=row["state"],
        )
        latest = g.rows(
            "release_assessments",
            {"task_id": row["id"]},
            order_by=("-rollback_plan_version",),
            limit=1,
        )[0]
        require(
            assessment["id"] == latest["id"]
            and assessment["schedule_version"] == row["schedule_version"]
            and assessment["delivery_cycle"] == row["delivery_cycle"],
            "ASSESSMENT_BASELINE_MISMATCH",
        )
        changed_assessment = c.cas(
            g,
            "release_assessments",
            assessment,
            {
                "status": 2 if c.body["verdict"] == 1 else 3,
                "reviewed_by": c.actor_id,
                "reviewed_at": c.clock,
                "review_reason": c.body["reason"],
                "review_evidence": c.body["evidence"],
            },
            expected=c.body["expected_assessment_version"],
        )
        values = {}
        if c.body["verdict"] == 1:
            values = {
                "approved_assessment_id": assessment["id"],
                "approved_assessment_version": changed_assessment["version"],
            }
        changed = c.cas(g, "tasks", row, values)
        return {
            "task": task_model(changed),
            "assessment": model("ReleaseAssessment", changed_assessment),
        }
