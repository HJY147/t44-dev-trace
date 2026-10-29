"""Owned single scheduler replacement; validate one supplied service session read-only."""

import argparse
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path

PROBE = r"""
import hashlib,hmac,json,os,sys
from datetime import UTC,datetime
from pathlib import Path
from sqlalchemy import create_engine,text
credential=json.loads(Path(sys.argv[1]).read_text())
expected=int(sys.argv[2]); token=credential['access_token']; sid=credential['session_id']
assert type(sid) is int and sid>0 and isinstance(token,str) and 32<=len(token)<=512
engine=create_engine(os.environ['DATABASE_URL'],pool_size=1,max_overflow=0)
try:
    with engine.connect() as connection:
        row=connection.execute(text('SELECT s.actor_kind,s.user_id,s.service_account_id,s.token_hash,s.project_ids,s.scopes,s.expires_at,s.created_at,s.revoked_at,a.active FROM auth_sessions s JOIN service_accounts a ON a.id=s.service_account_id WHERE s.id=:id'),{'id':sid}).mappings().one()
    project_ids=json.loads(row['project_ids']) if isinstance(row['project_ids'],str) else row['project_ids']
    scopes=json.loads(row['scopes']) if isinstance(row['scopes'],str) else row['scopes']
    assert row['actor_kind']==2 and row['user_id'] is None and row['active']==1 and row['revoked_at'] is None
    assert project_ids==[expected] and type(project_ids[0]) is int and scopes==['escalation:write']
    assert hmac.compare_digest(row['token_hash'],hashlib.sha256(token.encode()).digest())
    expiry=row['expires_at'].replace(tzinfo=UTC); created=row['created_at'].replace(tzinfo=UTC)
    assert (expiry-created).total_seconds()==3600 and expiry.timestamp()>datetime.now(UTC).timestamp()+60
    file_expiry=datetime.fromisoformat(credential['expires_at'].replace('Z','+00:00'))
    assert abs((file_expiry-expiry).total_seconds())<0.000001
    print(json.dumps({'session_id':sid,'service_account_id':row['service_account_id'],'actual_project_ids':project_ids,'actual_scopes':scopes,'actual_expiry_utc':expiry.strftime('%Y-%m-%dT%H:%M:%SZ'),'actual_expiry_full_utc':expiry.isoformat(),'actual_ttl_seconds':3600}))
finally:
    engine.dispose()
"""


def application(run):
    bound = json.loads((run / "application-binding.json").read_text())
    path = run / "application-controller.py"
    if path.is_symlink() or hashlib.sha256(path.read_bytes()).hexdigest() != bound["application_controller_sha256"]:
        raise ValueError("BOUND_CONTROLLER_CHANGED")
    spec = importlib.util.spec_from_file_location("scope_bound_application", path)
    app = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(app)
    module = app.controller(run)
    app.binding(run, module)
    return app, module, bound


def replace(run, project_id, token, expiry):
    app, module, bound = application(run)
    module.admitted()
    if type(project_id) is not int or not 0 < project_id <= 4294967295:
        raise ValueError("EXACT_SINGLE_PROJECT_REQUIRED")
    module.private(token)
    module.private(token.parent, True)
    allowed = module.PROJECT / ".agent-worktrees/.runtime/continuation-20261025/provisioned"
    if not token.resolve().is_relative_to(allowed) or token.name in ("admin.json", "identities.json"):
        raise ValueError("EXPLICIT_PROVISIONED_TOKEN_REQUIRED")
    app.token_window(expiry)
    env = module.read(run / "secrets/application-environment.json")
    result = module.command(
        run,
        [bound["python"], "-c", PROBE, token, str(project_id)],
        timeout=15,
        env_extra={"DATABASE_URL": env["DATABASE_URL"]},
    )
    metadata = json.loads(result)
    if metadata["actual_expiry_utc"] != expiry:
        raise ValueError("DECLARED_EXPIRY_DIFFERS_FROM_ACTUAL_SESSION")
    previous_path = run / "state/scheduler-scope.json"
    previous = module.read(previous_path) if previous_path.exists() else None
    stopped = module.stop_app(run, "scheduler")
    stop_receipt = module.receipt(
        run,
        "scheduler_scope_stop",
        **stopped,
        previous_actual_project_ids=previous["actual_project_ids"] if previous else None,
    )
    if not stopped["success"]:
        raise RuntimeError("OWNED_SCHEDULER_STOP_INCOMPLETE")
    started = app.scheduler_start(run, token, expiry)
    actual = {**metadata, "pid": started["pid"], "at_utc": module.stamp(), "source_sha": bound["source_commit"]}
    module.save(previous_path, actual, replace=True)
    return module.receipt(
        run,
        "scheduler_scope_replace",
        success=True,
        previous_actual_project_ids=previous["actual_project_ids"] if previous else None,
        actual_project_ids=metadata["actual_project_ids"],
        actual_scopes=metadata["actual_scopes"],
        actual_session_id=metadata["session_id"],
        actual_expiry_utc=metadata["actual_expiry_full_utc"],
        actual_ttl_seconds=3600,
        scheduler_pid=started["pid"],
        stopped_receipt=stop_receipt["receipt_id"],
        started_receipt=started["receipt_id"],
        previous_token_revoked=False,
        coverage="only the new exact single project is scheduled;old token authorization unchanged",
    )


def stop(run):
    _app, module, _bound = application(run)
    previous_path = run / "state/scheduler-scope.json"
    previous = module.read(previous_path) if previous_path.exists() else None
    return module.receipt(
        run,
        "scheduler_scope_stop",
        **module.stop_app(run, "scheduler"),
        previous_actual_project_ids=previous["actual_project_ids"] if previous else None,
        token_revoked=False,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("replace", "stop"))
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--project-id", type=int)
    parser.add_argument("--token-file", type=Path)
    parser.add_argument("--token-expires-utc")
    args = parser.parse_args()
    os.umask(0o077)
    try:
        _app, module, _bound = application(args.run_dir)
        lock = args.run_dir / "state/scheduler-provision.lock"
        descriptor = os.open(lock, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
        try:
            module.private(lock)
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
            value = (
                stop(args.run_dir)
                if args.command == "stop"
                else replace(args.run_dir, args.project_id, args.token_file, args.token_expires_utc)
            )
        finally:
            os.close(descriptor)
        print(json.dumps(value))
        raise SystemExit(0 if value["success"] else 1)
    except (OSError, RuntimeError, ValueError, TypeError, KeyError):
        print(json.dumps({"success": False, "error": "OWNED_SCHEDULER_SCOPE_STEP_FAILED"}))
        raise SystemExit(1) from None
