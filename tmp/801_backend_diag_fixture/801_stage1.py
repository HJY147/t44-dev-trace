"""S1: original admin/data network only; DB candidates and original CLI token, no HTTP."""

import argparse
import hashlib
import importlib
import json
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

http = importlib.import_module("801_http")
original = importlib.import_module("801_prepare")


def main(argv=None):
    parser = argparse.ArgumentParser()
    for name in ("identities", "output-dir", "host", "user"):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--slots", type=int, default=400)
    args = parser.parse_args(argv)
    if not 1 <= args.slots <= 400:
        raise http.InvalidDiagnostic("Bounded slot count required")
    _settings, mysql = original.guarded_settings(args.host, args.port, args.user)
    identities = http.private_json(args.identities)
    if set(identities) != {"manager", "developer", "reviewer"} or any(
        set(value) != {"username", "user_id"} or type(value["user_id"]) is not int
        for value in identities.values()
    ):
        raise http.InvalidDiagnostic(
            "Identity-only explicit three-role mapping required"
        )
    directory = Path(args.output_dir)
    if not directory.is_absolute():
        raise http.InvalidDiagnostic("New absolute output directory required")
    directory.mkdir(mode=0o700)
    status_fd, candidate_fd = http.reserve(directory / "status.public.jsonl"), None
    engine, writes_started, phase = None, False, "database_candidates"
    try:
        from t44.persistence import SqlAlchemyUnitOfWorkFactory, create_mysql_engine
        from t44.services.common import task_model

        engine = create_mysql_engine(mysql)
        factory = SqlAlchemyUnitOfWorkFactory(engine)
        with factory() as uow:
            g = uow.gateway
            projects, transitions, escalations, rule_version = original.candidates(
                g,
                identities,
                args.slots,
                datetime.now(UTC),
                lambda value: http.write_fd(status_fd, value),
            )
            selected = [
                row["id"]
                for pair in zip(transitions, escalations, strict=True)
                for row in pair
            ]
            selected_events = g.count("escalation_events", {"task_id": selected})
            events_before = g.count("escalation_events")
            http.write_fd(
                status_fd,
                {
                    "kind": "pre_service_event_observation",
                    "utc": http.utc(),
                    "selected_existing_events": selected_events,
                    "total_events": events_before,
                },
            )
            if selected_events:
                raise http.InvalidDiagnostic(
                    "Selected fixture already has escalation events; preserve and review"
                )
            slots = [
                {"transition": task_model(left), "escalation": task_model(right)}
                for left, right in zip(transitions, escalations, strict=True)
            ]
        candidate_fd = http.reserve(directory / "candidate.private.json")
        service_path = directory / "service.private.json"
        command = [
            sys.executable,
            "-m",
            "t44.cli",
            "service-token",
            "--name",
            "diag801s1-" + uuid4().hex,
            "--token-file",
            str(service_path),
        ]
        for identifier in projects:
            command.extend(("--project-id", str(identifier)))
        phase, writes_started = "original_service_token_cli", True
        result = subprocess.run(
            command,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            check=False,
            timeout=60,
        )
        if result.returncode:
            raise http.InvalidDiagnostic("Original CLI failed")
        service = http.private_json(service_path)
        phase = "service_scope_and_event_verification"
        with factory() as uow:
            g = uow.gateway
            session = g.get("auth_sessions", service["session_id"])
            if (
                not session
                or session["actor_kind"] != 2
                or session["project_ids"] != projects
                or session["scopes"] != ["escalation:write"]
                or session["revoked_at"] is not None
                or session["expires_at"] <= datetime.now(UTC)
                or session["token_hash"]
                != hashlib.sha256(service["access_token"].encode()).digest()
            ):
                raise http.InvalidDiagnostic("Actual scoped service session differs")
            events_after = g.count("escalation_events")
            if events_after != events_before or g.count(
                "escalation_events", {"task_id": selected}
            ):
                raise http.InvalidDiagnostic(
                    "Escalation events changed during S1; preserve and review"
                )
        packet = {
            "kind": "source935-stage1-candidates",
            "product": http.PRODUCT,
            "database": http.DATABASE,
            "created_at": http.utc(),
            "project_ids": projects,
            "identities": identities,
            "rule_version": rule_version,
            "service": service,
            "slots": slots,
            "provenance": {
                "candidate_source": "original source935 SQL and task_model",
                "service_source": "original python -m t44.cli service-token with actual IDs",
                "selected_escalation_events_before": selected_events,
                "total_escalation_events_before": events_before,
                "total_escalation_events_after": events_after,
            },
        }
        phase = "write_private_candidate"
        http.write_fd(candidate_fd, packet)
        os.fsync(candidate_fd)
        digest = hashlib.sha256(
            (directory / "candidate.private.json").read_bytes()
        ).hexdigest()
        http.write_fd(
            status_fd,
            {
                "kind": "stage1-complete-not-acceptance",
                "utc": http.utc(),
                "slots": len(slots),
                "project_scope_count": len(projects),
                "candidate_sha256": digest,
                "escalation_events_unchanged": True,
                "http_constructed_or_called": False,
                "diagnostic_valid": True,
            },
        )
        os.fsync(status_fd)
        return 0
    except BaseException as error:
        http.write_fd(
            status_fd,
            {
                "diagnostic_valid": False,
                "utc": http.utc(),
                "phase": phase,
                "failure": type(error).__name__,
                "errno": getattr(error, "errno", None),
                "partial_service_account_or_audit_may_exist": writes_started,
                "http_constructed_or_called": False,
            },
        )
        raise
    finally:
        if engine is not None:
            engine.dispose()
        os.close(status_fd)
        if candidate_fd is not None:
            os.close(candidate_fd)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as error:  # noqa: BLE001 - private failure details must not be printed
        print(json.dumps({"stage1_failed": type(error).__name__}), file=sys.stderr)
        sys.exit(1)
