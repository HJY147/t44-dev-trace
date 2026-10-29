"""Explicit-anchor seam for the root's budget-admitted admin. No automatic connection."""

from datetime import UTC, datetime

from guard import BASE_COUNTS, check_intent, need, timestamp


def seed_in_admitted_context(plan, intent, factory, actual_mysql_identity, *, now=None):
    """Caller holds the exact new budget admission/lock for this entire invocation."""
    now = now or datetime.now(UTC)
    check_intent(plan, intent, now)
    need(intent["operation"] == "seed_demo", "ONLY_ORIGINAL_SEED_FUNCTION_ALLOWED")
    target = plan["target"]
    need(actual_mysql_identity == {
        "database": target["database"], "host": target["mysql_host"],
        "port": target["mysql_port"], "username": target["mysql_user"],
    }, "ACTUAL_PROJECT_DATABASE_IDENTITY_REQUIRED")
    from t44.persistence.seed import seed_demo

    # Original function enforces empty dataset, manifest identity and one transaction.
    return seed_demo(
        factory, projects=BASE_COUNTS["projects"], tasks=BASE_COUNTS["tasks"],
        dependencies=BASE_COUNTS["dependencies"], records=BASE_COUNTS["reviews_and_decisions"],
        seed=plan["seed"]["seed"], anchor_at=timestamp(plan["seed"]["anchor_utc"]),
    )


if __name__ == "__main__":
    # Deliberately no engine, credentials or unbudgeted CLI execution path.
    raise SystemExit("ROOT_BUDGET_ADMITTED_CALLER_REQUIRED: seed_in_admitted_context")
