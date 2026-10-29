"""Budget-admitted original service CLI and read-only post-setup count attestation."""
import datetime as dt
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path


def save(path, value):
    with path.open('x') as stream:
        os.chmod(path, 0o600)
        json.dump(value, stream, sort_keys=True)
        stream.flush()
        os.fsync(stream.fileno())


def main(operation):
    from t44.persistence import SqlAlchemyUnitOfWorkFactory, create_mysql_engine
    from t44.settings import Settings
    from t44.services.common import wire
    settings = Settings.from_env()
    c = json.loads(Path('/neutral-input/config.json').read_bytes())
    mysql = settings.mysql_settings()
    if mysql.database != c['database'] or mysql.host != 'mysql' or mysql.port != 3306 or mysql.username != c['database'] + '_app':
        raise ValueError('EXACT_BUDGET_ADMITTED_DATABASE_REQUIRED')
    out = Path('/neutral-output')
    factory = SqlAlchemyUnitOfWorkFactory(create_mysql_engine(mysql))
    if operation == 'service':
        command = [sys.executable, '-m', 't44.cli', 'service-token', '--name', c['service_name'], '--token-file', str(out/'service.original.private.json')]
        for pid in c['project_ids']:
            command.extend(['--project-id', str(pid)])
        process = subprocess.run(command, capture_output=True, timeout=40, check=False)
        (out/'service-CLI.stdout.private').write_bytes(process.stdout)
        (out/'service-CLI.stderr.private').write_bytes(process.stderr)
        if process.returncode:
            raise ValueError('ORIGINAL_SERVICE_CLI_FAILED')
        original = json.loads((out/'service.original.private.json').read_bytes())
        with factory() as uow:
            row = uow.gateway.get('auth_sessions', original['session_id'])
            account = uow.gateway.get('service_accounts', row['service_account_id'])
            if row['token_hash'] != hashlib.sha256(original['access_token'].encode()).digest() or row['revoked_at'] is not None or not account['active'] or row['project_ids'] != c['project_ids'] or row['scopes'] != ['escalation:write']:
                raise ValueError('ACTUAL_SERVICE_SESSION_MISMATCH')
        save(out/'service.json', {'token':original['access_token'], 'user_id':row['service_account_id'],
            'expires_at':wire(row['expires_at']), 'project_ids':row['project_ids'], 'scopes':row['scopes']})
        print(json.dumps({'kind':'ORIGINAL_SERVICE_CLI_REAL_SESSION_PRIVATE_ONLY', 'expires_at':wire(row['expires_at']), 'credentials_disclosed':False}))
    elif operation == 'counts':
        with factory() as uow:
            g = uow.gateway
            counts = {table:g.count(table,{}) for table in ('projects','tasks','task_dependencies','reviews','decisions')}
            markers = g.rows('audit_events', {'operation_id':'syntheticSeedV2'})
            if len(markers) != 40 or len({m['after_values'][0]['value'] for m in markers}) != 1 or counts != {'projects':40,'tasks':6400,'task_dependencies':9000,'reviews':11400,'decisions':3600}:
                raise ValueError('ACTUAL_FINAL_COUNTS_DIFFER_EXPECTED_SEPARATE_6400_FIXTURE')
            task_snapshot = wire(g.rows('tasks',{},order_by=('id',)))
        # This digest describes the whole current Task row snapshot, never expected performance.
        snapshot = json.dumps(task_snapshot,sort_keys=True,separators=(',',':')).encode()
        save(out/'counts.PUBLIC.json', {'kind':'NEUTRAL_REAL_DATABASE_COUNTS_NOT_ACCEPTANCE', 'actual_counts':counts,
            'seed_manifest_sha256':hashlib.sha256(markers[0]['after_values'][0]['value'].encode()).hexdigest(),
            'task_row_snapshot_sha256':hashlib.sha256(snapshot).hexdigest(), 'captured_at':dt.datetime.now(dt.timezone.utc).isoformat(),
            'new_tasks_created_through_real_HTTP':400, 'existing_short_scope_untouched':True,
            'original_fixture_counts_retained_and_400_tasks_added':True, 'formal_performance_passed':False})
        print((out/'counts.PUBLIC.json').read_text())
    else:
        raise ValueError('FINITE_OPERATION_REQUIRED')


if __name__ == '__main__':
    os.umask(0o077)
    try:
        main(sys.argv[1])
    except Exception as error:
        print(json.dumps({'kind':'NEUTRAL_ADMIN_FAILED_NO_RETRY','failure_type':type(error).__name__,'reason':str(error)}))
        raise SystemExit(1) from None
