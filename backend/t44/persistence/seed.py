"""Deterministic synthetic business fixtures, never evidence of real human decisions."""

import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from importlib.resources import files
from pathlib import Path
from secrets import token_bytes

from argon2 import PasswordHasher

from .codecs import from_db_time, to_db_time, utc_now
from .errors import StatementRejected
from .schema import TABLES

VERSION = 1
OPERATION = "syntheticSeedV1"
ARTIFACT = "a83fe2806a68ec8dc938748d623bf28c9a16b293"
EVIDENCE = [
    {
        "kind": 2,
        "locator": "backend/t44/persistence/SYNTHETIC-DATA.md",
        "description": "[synthetic] Generated fixture, not human review or execution proof",
    }
]


def _snapshot(name, path):
    raw = Path(path).read_bytes() if path else files("t44").joinpath("resources", name).read_bytes()
    return json.loads(raw), hashlib.sha256(raw).hexdigest()


def _populate(g, manifest, template, actors, batch_size):
    projects, tasks, dependencies, records = (
        manifest[k] for k in ("projects", "tasks", "dependencies", "records")
    )
    per_project, delivered = tasks // projects, tasks // projects * 2 // 5
    states = [
        6 if i < delivered else (1, 2, 3, 4, 5, 7)[(i - delivered) % 6] for i in range(per_project)
    ]
    advanced = projects * sum(s in (4, 5, 6, 7) for s in states)
    decisions = projects * (states.count(6) + states.count(7) * 2)
    reviews = records - decisions
    if advanced < 1 or reviews < advanced:
        raise ValueError(
            "Record count must cover each reviewed task and delivery/rollback decisions"
        )
    at = from_db_time(to_db_time(datetime.fromisoformat(manifest["anchor_at"])))
    created, manager, developer, reviewer = at - timedelta(days=14), *actors
    tables = defaultdict(list)
    context = dict(
        created_at=created,
        updated_at=at,
        delivery_cycle=1,
        schedule_version=1,
        created_by=manager,
        rollback_plan_version=1,
        evidence=EVIDENCE,
    )

    def add(table, **values):
        # Context is trusted fixture construction; explicit values still pass Rows validation.
        row = {**{k: v for k, v in context.items() if k in TABLES[table].c}, **values}
        tables[table].append(row)
        return row

    pointers, review_index = [], 0

    def annotations(items, key, **values):
        return [{key: item[key], **values, "evidence": EVIDENCE} for item in items]

    sections = annotations(
        template["sections"], "section_id", content="[synthetic] 合成八段记录；非实际评审结论"
    )
    passed = annotations(
        template["items"],
        "item_id",
        judgment=1,
        rationale="[synthetic] 演示通过分支，不是执行证据",
    )
    failed = [{**item, "judgment": 3, "rationale": "[synthetic] 待验证分支"} for item in passed]
    for p in range(projects):
        pid = p + 1
        context["project_id"] = pid
        add(
            "projects",
            id=pid,
            name=f"[synthetic] 项目 {pid:02}",
            description="程序合成演示/压测夹具，不代表真实项目经历",
        )
        for uid, role in zip(actors, (1, 2, 4), strict=True):
            add(
                "project_members",
                user_id=uid,
                roles_mask=role,
            )
        add(
            "iterations",
            id=pid,
            name="[synthetic] 迭代",
            planned_start=created,
            planned_end=at + timedelta(days=14),
            capacity=[dict(user_id=developer, available_hours=per_project * 1.25 + 20)],
            buffer_quarters=40,
            delay_contingency="[synthetic] 延期时保存差异、重新评审并调整计划",
        )
        for local, state in enumerate(states):
            tid = p * per_project + local + 1
            context["task_id"] = tid
            start = (
                at - timedelta(days=12) + timedelta(hours=local * 2)
                if state == 6
                else at - timedelta(days=4)
            )
            end = (
                start + timedelta(minutes=75)
                if state == 6
                else at + timedelta(hours=(-48, -1, 12, 48)[(local + manifest["seed"]) % 4])
            )
            if start < created or end > at + timedelta(days=14) or end <= start:
                raise ValueError("Requested project size exceeds the synthetic planning horizon")
            count = (
                reviews // advanced + (review_index < reviews % advanced)
                if state in (4, 5, 6, 7)
                else 0
            )
            version = {1: 1, 2: 2, 3: 3}.get(
                state, 3 * count + {4: 1, 5: 2, 6: 5, 7: 6}.get(state, 0)
            )
            pointer = dict.fromkeys(
                (
                    "latest_review_id",
                    "approved_review_id",
                    "approved_assessment_id",
                    "approved_assessment_version",
                )
            )
            pointer["id"] = tid
            task = add(
                "tasks",
                **pointer,
                iteration_id=pid,
                title=f"[synthetic] 任务 {tid:05}",
                description="Synthetic fixture; no human delivery/review claim",
                owner_id=developer,
                state=state,
                version=version,
                review_cycle=count or 1,
                planned_start=start,
                planned_end=end,
                estimated_quarters=4,
                buffer_quarters=1,
                delay_contingency="[synthetic] 延期须保留前后排期及证据",
                blocked_from_state=2 if state == 3 else None,
                block_reason="[synthetic] 外部接口待确认" if state == 3 else None,
                responsibility_stage=2 if state == 3 else None,
                artifact_revision=ARTIFACT if count else None,
            )
            for cycle in range(1, count + 1):
                rid = len(tables["reviews"]) + 1
                add(
                    "reviews",
                    id=rid,
                    review_cycle=cycle,
                    template_version=template["version"],
                    template_hash=bytes.fromhex(manifest["template_sha256"]),
                    artifact_revision=ARTIFACT,
                    sections=sections,
                    checklist=passed if cycle == count else failed,
                    verdict=1 if cycle == count else 2,
                    reviewer_id=reviewer,
                    created_at=start + timedelta(minutes=cycle * 3),
                )
                pointer["latest_review_id"] = rid
            if count:
                review_index += 1
            if state in (5, 6, 7):
                pointer["approved_review_id"] = pointer["latest_review_id"]
                aid = len(tables["release_assessments"]) + 1
                status = (1, 2, 3)[(local // 6) % 3] if state == 5 else 2
                add(
                    "release_assessments",
                    id=aid,
                    version=1 if status == 1 else 2,
                    status=status,
                    risks=[
                        dict(
                            perspective=i,
                            severity=1,
                            risk=f"[synthetic] 风险视角{i}",
                            mitigation="[synthetic] 按预案验证并保留记录",
                            evidence=EVIDENCE,
                        )
                        for i in (1, 2, 3, 4)
                    ],
                    rollback_plan=dict(
                        target_version="synthetic-baseline",
                        trigger="[synthetic] 回归不符合预期",
                        steps=["[synthetic] 恢复隔离演示基线"],
                        impact="[synthetic] 仅影响合成环境",
                        verification="[synthetic] 按演示检查项核对",
                        responsible_user_id=developer,
                        evidence=EVIDENCE,
                    ),
                    reviewed_by=None if status == 1 else reviewer,
                    reviewed_at=None if status == 1 else start + timedelta(minutes=21),
                    review_reason=None
                    if status == 1
                    else "[synthetic] 合成批准/退回分支，非真人决定",
                    review_evidence=[] if status == 1 else EVIDENCE,
                    created_at=start + timedelta(minutes=20),
                )
                if status == 2:
                    pointer.update(approved_assessment_id=aid, approved_assessment_version=2)
                if state == 5:
                    task["version"] += 1 + (status != 1)
                for dtype in (1, 2) if state == 7 else (1,) if state == 6 else ():
                    add(
                        "decisions",
                        type=dtype,
                        decided_by=manager,
                        reason="[synthetic] 合成发布/回滚决定，非真人操作",
                        impact="[synthetic] 仅演示数据" if dtype == 2 else None,
                        target_version="synthetic-baseline" if dtype == 2 else "synthetic-v1",
                        assessment_id=aid,
                        decided_at=start + timedelta(minutes=30 if dtype == 1 else 40),
                    )
            pointers.append(pointer)
        add(
            "audit_events",
            task_id=None,
            actor_kind=3,
            actor_id=None,
            request_id=f"synthetic-seed-v1-{pid}",
            operation_id=OPERATION,
            outcome=1,
            before_values=[],
            after_values=[dict(field="seed_manifest", value=json.dumps(manifest, sort_keys=True))],
            created_at=at,
        )
    edges = tables["task_dependencies"]
    for distance in range(1, delivered + 1):
        for p in range(projects):
            for local in range(1, per_project):
                predecessor = min(local, delivered) - distance
                if predecessor >= 0 and len(edges) < dependencies:
                    add(
                        "task_dependencies",
                        project_id=p + 1,
                        task_id=p * per_project + local + 1,
                        depends_on_task_id=p * per_project + predecessor + 1,
                    )
        if len(edges) == dependencies:
            break
    if len(edges) != dependencies:
        raise ValueError("Requested dependency count exceeds acyclic fixture capacity")
    # The frozen registry retains FK insertion/locking order, independent of buffer creation.
    for table in TABLES:
        rows = tables.get(table, [])
        for first in range(0, len(rows), batch_size):
            g.insert_many(table, rows[first : first + batch_size])
    for first in range(0, len(pointers), batch_size):
        g.update_many("tasks", pointers[first : first + batch_size])
    return dict(
        projects=projects,
        tasks=tasks,
        dependencies=dependencies,
        reviews=reviews,
        decisions=decisions,
        assessments=len(tables["release_assessments"]),
        states=dict(Counter(t["state"] for t in tables["tasks"])),
    )


def seed_demo(
    factory,
    *,
    projects=40,
    tasks=6000,
    dependencies=9000,
    records=15000,
    manager_username="synthetic-manager",
    seed=44,
    anchor_at=None,
    template_path=None,
    rules_path=None,
    batch_size=250,
):
    if (
        any(type(v) is not int or v < 1 for v in (projects, tasks, records, batch_size))
        or type(dependencies) is not int
        or dependencies < 0
        or type(seed) is not int
        or tasks % projects
        or tasks // projects < 10
    ):
        raise ValueError(
            "Positive counts, integral seed, and at least ten tasks per project required"
        )
    template, template_hash = _snapshot("review-template.json", template_path)
    rules, rules_hash = _snapshot("escalation-rules.json", rules_path)
    if len(template["sections"]) != 8 or len(template["items"]) < 10:
        raise ValueError("Incomplete adopted review template")
    with factory() as uow:
        g = uow.gateway
        marker = g.rows("audit_events", {"operation_id": OPERATION}, limit=1)
        prior = json.loads(marker[0]["after_values"][0]["value"]) if marker else None
        at = anchor_at or (
            datetime.fromisoformat(prior["anchor_at"])
            if prior
            else utc_now().replace(microsecond=0)
        )
        manifest = dict(
            version=VERSION,
            seed=seed,
            anchor_at=from_db_time(to_db_time(at)).isoformat(),
            projects=projects,
            tasks=tasks,
            dependencies=dependencies,
            records=records,
            template_version=template["version"],
            template_sha256=template_hash,
            rule_version=rules["version"],
            rule_effective_at=rules["effective_at"],
            rule_decided_by=rules["decided_by"],
            rules_sha256=rules_hash,
            artifact_revision=ARTIFACT,
            synthetic=True,
        )
        digest = hashlib.sha256(
            json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        if prior:
            if prior != manifest:
                raise StatementRejected(
                    "Seed manifest differs in configuration/version/parameters; existing dataset "
                    "preserved, choose a new empty project schema"
                )
            return dict(already_seeded=True, manifest=manifest, manifest_sha256=digest)
        if any(g.count(table) for table in ("projects", "tasks", "reviews", "decisions")):
            raise StatementRejected("Seed requires an empty project dataset; no delete/overwrite")
        users = []
        for username in (manager_username, "synthetic-developer", "synthetic-reviewer"):
            rows = g.rows("users", {"username": username}, limit=1)
            if rows and not rows[0]["active"]:
                raise StatementRejected("Seed users must be active")
            users.append(
                rows[0]["id"]
                if rows
                else g.insert(
                    "users",
                    dict(
                        username=username,
                        display_name=f"[synthetic] {username}",
                        password_hash=PasswordHasher().hash(token_bytes(32)),
                        active=1,
                        created_at=at,
                        updated_at=at,
                    ),
                )
            )
        if len(set(users)) != 3:
            raise ValueError("Manager/developer/reviewer must be independent identities")
        result = _populate(g, manifest, template, users, batch_size)
    return dict(already_seeded=False, **result, manifest=manifest, manifest_sha256=digest)
