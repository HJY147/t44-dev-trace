"""A real standalone scheduler process; configuration or scan failure exits nonzero."""

import argparse
import fcntl
import json
import os
import signal
import stat
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path

from t44.persistence import SqlAlchemyUnitOfWorkFactory, create_mysql_engine
from t44.services.application import Business
from t44.services.common import wire
from t44.services.runtime import Runtime
from t44.settings import Settings

from .facade import EscalationFacade
from .rules import load_rules
from .runtime import build_scheduler, run_scheduler
from .scanner import Scanner


def read_token(path):
    credential = Path(path)
    if not stat.S_ISREG(credential.stat().st_mode) or credential.stat().st_mode & 0o077:
        raise ValueError("A private regular token file is required")
    token = json.loads(credential.read_text())["access_token"]
    if not isinstance(token, str) or not 32 <= len(token) <= 512:
        raise ValueError("Invalid service token file")
    return token


@contextmanager
def single_instance(path):
    descriptor = os.open(path, os.O_RDWR | os.O_CREAT, 0o600)
    try:
        if os.fstat(descriptor).st_mode & 0o077:
            raise ValueError("Scheduler lock file must be private")
        fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield
    finally:
        os.close(descriptor)


def main(argv=None):
    parser = argparse.ArgumentParser(prog="python -m t44.scheduling")
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--resume-run")
    parser.add_argument("--page-size", type=int, default=200)
    parser.add_argument("--token-file", default=os.getenv("T44_SCHEDULER_TOKEN_FILE"))
    parser.add_argument("--rules", default=os.getenv("T44_ESCALATION_RULES"))
    args = parser.parse_args(argv)
    engine = None
    try:
        if not args.token_file or (args.resume_run and not args.once):
            raise ValueError("A token file and an explicit once mode for resume are required")
        settings = Settings.from_env()
        mysql = settings.mysql_settings()
        lock = os.getenv(
            "T44_SCHEDULER_LOCK_FILE",
            str(Path(tempfile.gettempdir()) / f"t44-scheduler-{mysql.database}.lock"),
        )
        with single_instance(lock):
            engine = create_mysql_engine(mysql)
            factory = SqlAlchemyUnitOfWorkFactory(engine)
            facade = EscalationFacade(load_rules(args.rules)) if args.rules else EscalationFacade()
            runtime = Runtime(factory, settings, Business(escalations=facade))
            scanner = Scanner(
                runtime, lambda: read_token(args.token_file), page_size=args.page_size
            )
            if args.once:
                if args.resume_run:
                    scanner.store.get(args.resume_run)
                result = scanner.run(args.resume_run)
                print(
                    json.dumps(
                        wire(
                            {
                                k: v
                                for k, v in result.items()
                                if k not in ("rule_snapshot", "rule_hash", "run_key")
                            }
                        ),
                        ensure_ascii=False,
                    )
                )
            else:
                scanner.tick()
                scheduler = build_scheduler(scanner.tick, rules=facade.current())
                previous = signal.signal(signal.SIGTERM, lambda *_: scheduler.shutdown(wait=True))
                try:
                    run_scheduler(scheduler)
                finally:
                    signal.signal(signal.SIGTERM, previous)
        return 0
    except Exception:
        print(json.dumps({"error": "SCHEDULER_FAILED"}), file=sys.stderr)
        return 1
    finally:
        if engine is not None:
            engine.dispose()


if __name__ == "__main__":
    raise SystemExit(main())
