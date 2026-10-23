"""Explicit, standalone-process scheduler construction; no import-time worker."""

from collections.abc import Callable
from datetime import UTC
from inspect import iscoroutinefunction

from apscheduler.schedulers.base import SchedulerAlreadyRunningError
from apscheduler.schedulers.blocking import BlockingScheduler

from .rules import EscalationRules, load_rules

SCAN_JOB_ID = "t44-escalation-scan"


def build_scheduler(
    scan_callback: Callable[[], None], *, rules: EscalationRules | None = None
) -> BlockingScheduler:
    """Construct an unstarted APScheduler 3 instance around an injected real scanner.

    Intended only for a dedicated process composition root, never an API lifespan hook.
    The memory job store holds the interval job, not any business recovery or de-dup state.
    """
    if (
        not callable(scan_callback)
        or iscoroutinefunction(scan_callback)
        or iscoroutinefunction(type(scan_callback).__call__)
    ):
        raise TypeError("scan_callback must be a synchronous callable")
    configured = rules if rules is not None else load_rules()
    scheduler = BlockingScheduler(timezone=UTC)
    scheduler.add_job(
        scan_callback,
        "interval",
        seconds=configured.scan_interval_seconds,
        timezone=UTC,
        id=SCAN_JOB_ID,
        coalesce=True,
        max_instances=1,
        misfire_grace_time=None,
    )
    return scheduler


def run_scheduler(scheduler: BlockingScheduler) -> None:
    """Block until explicit shutdown/interrupt, then drain any running scan.

    A future process entry point must construct storage/messaging callbacks and wire its
    stop signal to scheduler.shutdown(wait=True). Other startup/runtime errors propagate.
    """
    if scheduler.running:
        raise SchedulerAlreadyRunningError
    try:
        scheduler.start()
    except KeyboardInterrupt:
        pass
    finally:
        if scheduler.running:
            scheduler.shutdown(wait=True)
