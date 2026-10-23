import json
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from threading import Event, Thread

import pytest
from apscheduler.events import EVENT_JOB_ERROR
from apscheduler.schedulers.base import STATE_STOPPED, SchedulerAlreadyRunningError
from t44.scheduling import build_scheduler, load_rules, run_scheduler
from t44.scheduling.runtime import SCAN_JOB_ID


def start_now(scheduler):
    scheduler.modify_job(SCAN_JOB_ID, next_run_time=datetime.now(UTC))
    thread = Thread(target=run_scheduler, args=(scheduler,), daemon=True)
    thread.start()
    return thread


def stop_and_join(scheduler, thread):
    if scheduler.running:
        scheduler.shutdown(wait=True)
    thread.join(timeout=3)
    assert not thread.is_alive()


def test_build_is_unstarted_and_uses_d001_single_instance_schedule():
    observed = Event()
    scheduler = build_scheduler(observed.set, rules=load_rules())
    assert scheduler.state == STATE_STOPPED
    assert not observed.is_set()
    job = scheduler.get_job(SCAN_JOB_ID)
    assert job.func == observed.set
    assert job.trigger.interval == timedelta(seconds=60)
    assert job.trigger.timezone.utcoffset(None) == timedelta(0)
    assert scheduler.timezone.utcoffset(None) == timedelta(0)
    assert job.coalesce is True
    assert job.max_instances == 1
    assert job.misfire_grace_time is None


def test_real_start_injected_scan_and_shutdown_lifecycle():
    scanned = Event()
    scheduler = build_scheduler(scanned.set)
    thread = start_now(scheduler)
    try:
        assert scanned.wait(3), "injected scan did not execute"
    finally:
        stop_and_join(scheduler, thread)
    assert scheduler.state == STATE_STOPPED


def test_shutdown_waits_for_in_flight_scan():
    entered, release, stopped = Event(), Event(), Event()

    def scan():
        entered.set()
        assert release.wait(3)

    scheduler = build_scheduler(scan)
    thread = start_now(scheduler)
    stopper = None
    try:
        assert entered.wait(3)

        def stop():
            scheduler.shutdown(wait=True)
            stopped.set()

        stopper = Thread(target=stop, daemon=True)
        stopper.start()
        assert not stopped.wait(0.05), "shutdown returned before scan finished"
    finally:
        release.set()
        if stopper is not None:
            stopper.join(timeout=3)
        stop_and_join(scheduler, thread)
    assert stopped.is_set()


def test_callback_failure_is_reported_as_job_error():
    observed = Event()
    errors = []

    def scan():
        raise RuntimeError("scan storage unavailable")

    def on_error(event):
        errors.append(event.exception)
        observed.set()

    scheduler = build_scheduler(scan)
    scheduler.add_listener(on_error, EVENT_JOB_ERROR)
    thread = start_now(scheduler)
    try:
        assert observed.wait(3)
    finally:
        stop_and_join(scheduler, thread)
    assert len(errors) == 1
    assert str(errors[0]) == "scan storage unavailable"


def test_keyboard_interrupt_drains_actual_scheduler(monkeypatch):
    scheduler = build_scheduler(lambda: None)

    def interrupt():
        raise KeyboardInterrupt

    monkeypatch.setattr(scheduler, "_main_loop", interrupt)
    run_scheduler(scheduler)
    assert scheduler.state == STATE_STOPPED


def test_start_failure_propagates(monkeypatch):
    scheduler = build_scheduler(lambda: None)

    def fail():
        raise RuntimeError("startup failure")

    monkeypatch.setattr(scheduler, "start", fail)
    with pytest.raises(RuntimeError, match="startup failure"):
        run_scheduler(scheduler)
    assert scheduler.state == STATE_STOPPED


def test_running_scheduler_is_rejected_without_stopping_its_owner():
    scanned = Event()
    scheduler = build_scheduler(scanned.set)
    thread = start_now(scheduler)
    try:
        assert scanned.wait(3)
        with pytest.raises(SchedulerAlreadyRunningError):
            run_scheduler(scheduler)
        assert scheduler.running
    finally:
        stop_and_join(scheduler, thread)


def test_non_callable_and_async_callbacks_rejected():
    async def async_scan():
        pass

    class AsyncScan:
        async def __call__(self):
            pass

    for callback in (None, async_scan, AsyncScan()):
        with pytest.raises(TypeError, match="synchronous"):
            build_scheduler(callback)


def test_callback_with_unsatisfied_arguments_rejected():
    with pytest.raises(ValueError, match="arguments have not been supplied"):
        build_scheduler(lambda required: None)


def test_each_api_worker_import_has_no_scheduler_or_threads():
    code = """
import json, threading
before = {t.ident for t in threading.enumerate()}
import t44.scheduling
after = {t.ident for t in threading.enumerate()}
print(json.dumps({'new_threads': len(after - before),
                  'global_scheduler': any(type(v).__name__ == 'BlockingScheduler'
                      for v in vars(t44.scheduling).values())}))
"""
    for _ in range(2):
        result = subprocess.run(
            [sys.executable, "-c", code], check=True, text=True, capture_output=True
        )
        assert json.loads(result.stdout) == {"new_threads": 0, "global_scheduler": False}
