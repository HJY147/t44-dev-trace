"""Durable keyset scanning through the same authenticated Runtime as HTTP."""

import hashlib
from datetime import timedelta
from uuid import UUID, uuid4

from t44.contracts import SPEC, violations
from t44.persistence.rows import Pred
from t44.persistence.scans import ScanStore
from t44.services.common import Call, now, uuid_text
from t44.services.errors import Rejected, require
from t44.services.identity import token_digest


class ScanFailure(RuntimeError):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


def validate_call(c):
    require(
        not violations({"$ref": "#/components/schemas/EscalationRequest"}, c.body),
        "PARAMETER_INVALID",
    )
    require(
        all(
            type(c.path.get(k)) is int and 1 <= c.path[k] <= 4294967295
            for k in ("project_id", "task_id")
        ),
        "PARAMETER_INVALID",
    )
    require(
        not violations(SPEC["components"]["parameters"]["IdempotencyKey"]["schema"], c.key),
        "PARAMETER_INVALID",
    )


class Scanner:
    def __init__(self, runtime, token_provider, *, page_size=200, clock=now, store=None):
        if type(page_size) is not int or not 1 <= page_size <= 1000:
            raise ValueError("page_size must be in 1..1000")
        self.runtime, self.token_provider = runtime, token_provider
        self.page_size, self.clock = page_size, clock
        self.store = store or ScanStore(runtime.factory)

    def _scope(self):
        token = self.token_provider()
        with self.runtime.factory() as uow:
            sessions = uow.gateway.rows(
                "auth_sessions", {"token_hash": token_digest(token)}, limit=1
            )
        projects = sessions[0]["project_ids"] if sessions else []
        probe = Call(
            "createEscalation",
            str(uuid4()),
            token,
            path={"project_id": projects[0] if projects else 0},
        )
        try:
            self.runtime.authorize(probe)
        except Rejected as error:
            self.runtime.rejection(probe, error)
            raise ScanFailure(error.code) from None
        return set(probe.actor["project_ids"])

    def _execute(self, candidate, run_id, rules):
        for _ in range(3):
            body = dict(
                expected_version=candidate["version"],
                schedule_version=candidate["schedule_version"],
                rule_version=rules.version,
                scan_run_id=str(run_id),
            )
            key = hashlib.sha256(
                f"{run_id}:{candidate['id']}:{candidate['version']}:{candidate['schedule_version']}".encode()
            ).hexdigest()
            call = Call(
                "createEscalation",
                str(uuid4()),
                self.token_provider(),
                path={"project_id": candidate["project_id"], "task_id": candidate["id"]},
                body=body,
                key=key,
                clock=self.clock(),
            )
            status, result, _, _ = self.runtime.execute(call, validate_call, source="scheduler")
            if status == 202:
                return result
            code = result.get("code", "INTERNAL_ERROR")
            if code == "NOT_ELIGIBLE_FOR_ESCALATION":
                return None
            if code in ("VERSION_CONFLICT", "SCHEDULE_VERSION_CONFLICT"):
                with self.runtime.factory() as uow:
                    candidate = uow.gateway.get("tasks", candidate["id"])
                if candidate is None:
                    return None
                continue
            raise ScanFailure(code)
        raise ScanFailure("VERSION_CONFLICT")

    def run(self, run_id=None):
        projects = self._scope()
        rules = self.runtime.business.escalations.current()
        run_id = str(UUID(str(run_id))) if run_id is not None else str(uuid4())
        run = self.store.start(
            run_id,
            rule_version=rules.version,
            rule_snapshot=rules.snapshot(),
            rule_hash=rules.raw_hash,
            cutoff_at=self.clock(),
        )
        if run["status"] != 1:
            return run
        while True:
            page = self.store.page(run_id, limit=self.page_size)
            if not page:
                return self.store.checkpoint(
                    run_id, last_task_id=run["last_task_id"], finished=True
                )
            for candidate in page:
                created, duplicate = 0, 0
                if candidate["project_id"] in projects:
                    try:
                        result = self._execute(candidate, run_id, rules)
                    except ScanFailure as error:
                        if error.code == "RULE_VERSION_CONFLICT":
                            self.store.checkpoint(
                                run_id, last_task_id=run["last_task_id"], error_code=error.code
                            )
                        raise
                    if result:
                        # If commit preceded a crash before checkpoint, the ledger's run UUID
                        # still counts that committed creation exactly once when cursor advances.
                        created = int(result["event"]["scan_run_id"] == run_id)
                        duplicate = 1 - created
                run = self.store.checkpoint(
                    run_id,
                    last_task_id=candidate["id"],
                    scanned_delta=1,
                    created_delta=created,
                    duplicate_delta=duplicate,
                )

    def tick(self):
        rules = self.runtime.business.escalations.current()
        # The single process owns scans for the active immutable rule hash. Different rule
        # artifacts are not silently rewritten or adopted as current on recovery.
        with self.runtime.factory() as uow:
            recoveries = uow.gateway.rows(
                "scan_runs",
                {"status": 1, "rule_hash": rules.raw_hash},
                predicates=(Pred("heartbeat_at", "le", self.clock() - timedelta(seconds=120)),),
                limit=100,
            )
        for run in recoveries:
            self.run(uuid_text(run["run_key"]))
        return self.run()
