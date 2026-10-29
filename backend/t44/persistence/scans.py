"""Durable UUID-keyed scans with a monotone cursor and rule snapshot."""

from datetime import UTC, datetime, timedelta

from .codecs import utc_now, uuid_to_bytes
from .errors import PersistenceIntegrityError, StatementRejected
from .rows import Pred


class ScanStore:
    def __init__(self, factory):
        self.factory = factory

    def _run(self, g, run_id, *, lock=None):
        rows = g.rows("scan_runs", {"run_key": uuid_to_bytes(run_id)}, limit=1, lock=lock)
        if not rows:
            raise StatementRejected("Unknown scan run")
        return rows[0]

    def start(self, run_id, *, rule_version, rule_snapshot, rule_hash, cutoff_at=None):
        now = cutoff_at or utc_now()
        with self.factory() as uow:
            g = uow.gateway
            try:
                with g.savepoint():
                    id = g.insert(
                        "scan_runs",
                        dict(
                            run_key=uuid_to_bytes(run_id),
                            rule_version=rule_version,
                            rule_snapshot=rule_snapshot,
                            rule_hash=rule_hash,
                            cutoff_at=now,
                            status=1,
                            started_at=now,
                            heartbeat_at=now,
                        ),
                    )
                return g.get("scan_runs", id)
            except PersistenceIntegrityError as error:
                if error.kind != "duplicate":
                    raise
            existing = self._run(g, run_id, lock="update")
            if existing["rule_hash"] != rule_hash or existing["rule_version"] != rule_version:
                raise StatementRejected("Run UUID cannot change rule snapshot")
            return existing

    def get(self, run_id):
        with self.factory() as uow:
            return self._run(uow.gateway, run_id)

    def recoverable(self, *, heartbeat_before, limit=100):
        with self.factory() as uow:
            return uow.gateway.rows(
                "scan_runs",
                {"status": 1},
                predicates=(Pred("heartbeat_at", "le", heartbeat_before),),
                limit=limit,
            )

    def page(self, run_id, *, limit=200):
        with self.factory() as uow:
            g = uow.gateway
            run = self._run(g, run_id)
            if run["status"] != 1:
                return []
            predicates = [Pred("id", "gt", run["last_task_id"])]
            offsets = [r.get("start_offset_seconds") for r in run["rule_snapshot"]["rules"]]
            if offsets and all(x is not None for x in offsets):
                try:
                    upper = run["cutoff_at"] - timedelta(seconds=min(offsets))
                except OverflowError:
                    upper = datetime.max.replace(tzinfo=UTC)
                predicates.append(Pred("planned_end", "le", upper))
            return g.rows(
                "tasks", {"state": (1, 2, 3, 4, 5)}, predicates=tuple(predicates), limit=limit
            )

    def checkpoint(
        self,
        run_id,
        *,
        last_task_id,
        scanned_delta=0,
        created_delta=0,
        duplicate_delta=0,
        finished=False,
        error_code=None,
    ):
        if any(
            type(v) is not int or v < 0
            for v in (last_task_id, scanned_delta, created_delta, duplicate_delta)
        ):
            raise ValueError("Scan counters/cursor must be nonnegative integers")
        now = utc_now()
        with self.factory() as uow:
            g = uow.gateway
            run = self._run(g, run_id, lock="update")
            if run["status"] != 1:
                return run
            values = dict(heartbeat_at=now)
            if last_task_id > run["last_task_id"]:
                values.update(
                    last_task_id=last_task_id,
                    scanned_count=run["scanned_count"] + scanned_delta,
                    created_count=run["created_count"] + created_delta,
                    duplicate_count=run["duplicate_count"] + duplicate_delta,
                )
            elif last_task_id < run["last_task_id"]:
                raise StatementRejected("Scan cursor cannot move backwards")
            if finished or error_code:
                values.update(status=3 if error_code else 2, finished_at=now, error_code=error_code)
            g.update("scan_runs", {"id": run["id"]}, values)
            return g.get("scan_runs", run["id"])
