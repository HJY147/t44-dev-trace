"""Explicit synthetic fixtures for demonstration/benchmarking, never human review evidence."""

import hashlib
import json
from datetime import timedelta
from importlib.resources import files
from pathlib import Path
from secrets import token_urlsafe

from argon2 import PasswordHasher

from .codecs import utc_now
from .errors import StatementRejected

SEED_OPERATION = "syntheticSeedV1"
ARTIFACT_REVISION = "8095b6ee5ccc7d7f4f8729d581c56be1227d55c4"
EVIDENCE = [
    {
        "kind": 2,
        "locator": "backend/t44/persistence/SYNTHETIC-DATA.md",
        "description": "合成夹具声明；不代表真实评审、真人决定或测试通过",
    }
]


def seed_demo(
    factory,
    *,
    projects=40,
    tasks=6000,
    dependencies=9000,
    records=15000,
    manager_username="synthetic-manager",
    template_path=None,
) -> dict:
    """One transaction, empty business database only; repeat returns the committed seed marker."""
    if (
        any(type(v) is not int or v < 1 for v in (projects, tasks, records))
        or type(dependencies) is not int
        or dependencies < 0
        or tasks % projects
        or tasks // projects < 4
        or records < tasks
    ):
        raise ValueError(
            "Positive evenly distributed project/task counts and valid record count required"
        )
    per_project = tasks // projects
    delivered_per_project = min(per_project // 2, records // (5 * projects))
    if delivered_per_project < 1:
        raise ValueError("Each project needs a synthetic delivered predecessor")
    decisions = projects * delivered_per_project
    reviews = records - decisions
    if reviews < tasks:
        raise ValueError("At least one review per synthetic task is required")
    source = (
        Path(template_path)
        if template_path
        else files("t44").joinpath("resources/review-template.json")
    )
    raw = source.read_bytes()
    template, template_hash = json.loads(raw), hashlib.sha256(raw).digest()
    if len(template["sections"]) != 8 or len(template["items"]) < 10:
        raise ValueError("Adopted review template is incomplete")
    now = utc_now()
    counts = dict(
        projects=projects,
        tasks=tasks,
        dependencies=dependencies,
        reviews=reviews,
        decisions=decisions,
        synthetic=True,
    )
    with factory() as uow:
        g = uow.gateway
        marker = g.rows("audit_events", {"operation_id": SEED_OPERATION}, limit=1)
        if marker:
            existing = marker[0]["after_values"][0]
            if existing != counts:
                raise StatementRejected("A different synthetic dataset is already committed")
            return {**existing, "already_seeded": True}
        if any(g.count(table) for table in ("projects", "tasks", "reviews", "decisions")):
            raise StatementRejected(
                "Synthetic seed requires an empty project dataset; no overwrite/delete"
            )
        users = []
        for username in (manager_username, "synthetic-developer", "synthetic-reviewer"):
            existing = g.rows("users", {"username": username}, limit=1)
            users.append(
                existing[0]["id"]
                if existing
                else g.insert(
                    "users",
                    dict(
                        username=username,
                        display_name=f"合成账户 {username}",
                        password_hash=PasswordHasher().hash(token_urlsafe(32)),
                        active=1,
                        created_at=now,
                        updated_at=now,
                    ),
                )
            )
        manager, developer, reviewer = users
        if len(set(users)) != 3:
            raise ValueError("Synthetic manager/developer/reviewer must be separate users")
        sections = [
            dict(
                section_id=s["section_id"],
                content="合成八段记录；非实际评审结论",
                evidence=EVIDENCE,
            )
            for s in template["sections"]
        ]
        checklist = [
            dict(
                item_id=i["item_id"],
                judgment=1,
                rationale="演示通过分支夹具；非执行证据",
                evidence=EVIDENCE,
            )
            for i in template["items"]
        ]
        project_tasks, global_index = [], 0
        for number in range(projects):
            pid = g.insert(
                "projects",
                dict(
                    name=f"合成项目 {number + 1:02}",
                    description="仅用于演示与压测；非真人项目经历",
                    created_by=manager,
                    created_at=now,
                    updated_at=now,
                ),
            )
            for user, role in ((manager, 1), (developer, 2), (reviewer, 4)):
                g.insert(
                    "project_members",
                    dict(
                        project_id=pid,
                        user_id=user,
                        roles_mask=role,
                        active=1,
                        created_at=now,
                        updated_at=now,
                    ),
                )
            iid = g.insert(
                "iterations",
                dict(
                    project_id=pid,
                    name="合成迭代",
                    planned_start=now - timedelta(days=2),
                    planned_end=now + timedelta(days=7),
                    capacity=[{"user_id": developer, "available_hours": per_project * 2}],
                    buffer_quarters=40,
                    delay_contingency="合成延期预案：分批演示",
                    created_at=now,
                    updated_at=now,
                ),
            )
            local_tasks = []
            for local in range(per_project):
                review_count = reviews // tasks + (global_index < reviews % tasks)
                delivered = local < delivered_per_project
                tid = g.insert(
                    "tasks",
                    dict(
                        project_id=pid,
                        iteration_id=iid,
                        title=f"合成任务 {number + 1:02}-{local + 1:03}",
                        description="合成数据，不代表真实交付或评审经历",
                        owner_id=developer,
                        state=6 if delivered else 5,
                        version=1,
                        schedule_version=1,
                        delivery_cycle=1,
                        review_cycle=review_count,
                        planned_start=now - timedelta(days=1),
                        planned_end=now + timedelta(days=2),
                        estimated_quarters=4,
                        buffer_quarters=1,
                        delay_contingency="合成预案：延迟时记录再排期",
                        artifact_revision=ARTIFACT_REVISION,
                        created_at=now,
                        updated_at=now,
                    ),
                )
                local_tasks.append(tid)
                rid = None
                for cycle in range(1, review_count + 1):
                    rid = g.insert(
                        "reviews",
                        dict(
                            project_id=pid,
                            task_id=tid,
                            version=1,
                            delivery_cycle=1,
                            review_cycle=cycle,
                            template_version=template["version"],
                            template_hash=template_hash,
                            artifact_revision=ARTIFACT_REVISION,
                            sections=sections,
                            checklist=checklist
                            if cycle == review_count
                            else [
                                {**item, "judgment": 3, "rationale": "合成未验证分支"}
                                for item in checklist
                            ],
                            verdict=1 if cycle == review_count else 2,
                            reviewer_id=reviewer,
                            created_at=now,
                        ),
                    )
                pointers = dict(latest_review_id=rid, approved_review_id=rid)
                if delivered:
                    risks = [
                        dict(
                            perspective=i,
                            severity=1,
                            risk="合成风险",
                            mitigation="合成缓解预案",
                            evidence=EVIDENCE,
                        )
                        for i in (1, 2, 3, 4)
                    ]
                    plan = dict(
                        target_version="synthetic-baseline",
                        trigger="合成回滚条件",
                        steps=["仅供演示的操作步骤"],
                        impact="无真实生产系统",
                        verification="合成验证说明，未声明执行",
                        responsible_user_id=developer,
                        evidence=EVIDENCE,
                    )
                    aid = g.insert(
                        "release_assessments",
                        dict(
                            project_id=pid,
                            task_id=tid,
                            version=2,
                            schedule_version=1,
                            delivery_cycle=1,
                            status=2,
                            risks=risks,
                            rollback_plan_version=1,
                            rollback_plan=plan,
                            created_by=developer,
                            reviewed_by=reviewer,
                            reviewed_at=now,
                            review_reason="合成批准分支夹具，非真人批准",
                            review_evidence=EVIDENCE,
                            created_at=now,
                        ),
                    )
                    pointers.update(approved_assessment_id=aid, approved_assessment_version=2)
                    g.insert(
                        "decisions",
                        dict(
                            project_id=pid,
                            task_id=tid,
                            type=1,
                            decided_by=manager,
                            delivery_cycle=1,
                            reason="合成交付决定；不作为项目证据",
                            impact=None,
                            target_version="synthetic-v1",
                            assessment_id=aid,
                            rollback_plan_version=1,
                            evidence=EVIDENCE,
                            decided_at=now,
                        ),
                    )
                g.update("tasks", {"id": tid}, pointers)
                global_index += 1
            project_tasks.append((pid, local_tasks))
        edges = 0
        for distance in range(1, per_project):
            for pid, ids in project_tasks:
                for local in range(1, per_project):
                    predecessor = min(local, delivered_per_project) - distance
                    if predecessor >= 0 and edges < dependencies:
                        g.insert(
                            "task_dependencies",
                            dict(
                                project_id=pid,
                                task_id=ids[local],
                                depends_on_task_id=ids[predecessor],
                                created_by=manager,
                                created_at=now,
                            ),
                        )
                        edges += 1
            if edges == dependencies:
                break
        if edges != dependencies:
            raise ValueError("Requested dependency count exceeds this acyclic fixture capacity")
        g.insert(
            "audit_events",
            dict(
                actor_kind=3,
                actor_id=None,
                request_id="synthetic-seed-v1",
                operation_id=SEED_OPERATION,
                outcome=1,
                before_values=[],
                after_values=[counts],
                evidence=EVIDENCE,
                created_at=now,
            ),
        )
        return {
            **counts,
            "already_seeded": False,
            "manager_user_id": manager,
            "template_sha256": template_hash.hex(),
        }
