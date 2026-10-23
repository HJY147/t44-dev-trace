"""Read-only proof after the one admitted runner has actually exited."""
import collections
import hashlib
import importlib.util
import json
import os
import subprocess
from datetime import datetime
from pathlib import Path

os.umask(0o077)
PROJECT = Path('/Users/yang/Desktop/nothing/软件开发大作业')
WORK = PROJECT / '.agent-worktrees/deployment-bounded-demo'
AUDIT = PROJECT / '.agent-worktrees/.runtime/native-demo-20261023/bounded-retest-20261023'
SPEC = importlib.util.spec_from_file_location('bounded_retest_post', WORK / 'deployment/native/application.py')
appmod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(appmod)
run = Path(json.loads((AUDIT / 'run.json').read_text())['run_dir'])
app = appmod.Application(PROJECT, run)
driver = json.loads((AUDIT / 'serve-driver-receipt.json').read_text())
assert driver['external_driver_wait_confirmed_runner_exit']
summary = json.loads((AUDIT / 'serve.stdout').read_text())
receipts = [json.loads(p.read_text()) for p in (run / 'receipts').glob('*.json')]
cycles = [v for v in receipts if v['action'] == 'application_cycle']
assert len(cycles) == 1
cycle = cycles[0]
owner = json.loads((run / 'state/serve-owner.json').read_text())
observations = []
for path in (run / 'state').glob('*.json'):
    value = json.loads(path.read_text())
    if 'pid' in value:
        observations.append({'record': path.name, 'pid': value['pid'],
                             'absent': appmod.process_identity(value['pid']) is None})
children = json.loads((run / 'state/api-children.json').read_text())
for group in ('workers', 'tracker'):
    for record in children[group]:
        observations.append({'record': 'api-' + group, 'pid': record['pid'],
                             'absent': appmod.process_identity(record['pid']) is None})
broker_absence = {role: app.broker.owner(role)[1] is None for role in ('rabbit', 'epmd')}
new_ports = {}
for port in (18088, 5178, 25674, 35674, 24369):
    result = subprocess.run(['/usr/sbin/lsof', '-nP', '-a', f'-iTCP:{port}', '-sTCP:LISTEN', '-Fp'],
                            capture_output=True, text=True, check=False)
    if result.returncode not in (0, 1) or result.stderr:
        raise RuntimeError('OWN_PORT_OBSERVATION_FAILED')
    new_ports[str(port)] = {'unbound': not result.stdout.strip(), 'lsof_exit_code': result.returncode}
start = datetime.fromisoformat(summary['started_at_utc']).replace(tzinfo=None)
end = datetime.fromisoformat(summary['at_utc']).replace(tzinfo=None)
scans = app.select('SELECT id,status,rule_hash,started_at,finished_at,scanned_count,created_count,'
                   'duplicate_count,error_code FROM scan_runs WHERE started_at>=%s AND started_at<=%s ORDER BY id',
                   (start, end))
service_ids = [r['session_id'] for r in receipts if r['action'] == 'service_credential']
user_id = json.loads((run / 'state/user-session.json').read_text())['session_id']
session_ids = sorted(set(service_ids + [user_id]))
sessions = app.select('SELECT id,actor_kind,project_ids,scopes,created_at,expires_at,revoked_at '
                      'FROM auth_sessions WHERE id IN (' + ','.join(['%s'] * len(session_ids)) + ') ORDER BY id', session_ids)
new_outbox = app.select('SELECT COUNT(*) AS count FROM outbox_events WHERE created_at>=%s AND created_at<=%s',
                        (start, end))[0]['count']
data_counts = app.select('SELECT (SELECT COUNT(*) FROM projects) AS projects,(SELECT COUNT(*) FROM tasks) AS tasks')[0]
appmod.verify_copy(app.binding, app.source)
protected = json.loads((AUDIT / 'protected-comparison.json').read_text())
proof = {'summary': summary, 'driver': driver, 'owner': owner, 'cycle': cycle, 'scans': scans,
         'sessions': sessions, 'service_session_ids': service_ids,
         'spawn_counts': dict(collections.Counter(r['role'] for r in receipts if r['action'] == 'spawn')),
         'post_stop': {'at_utc': appmod.utc(), 'all_recorded_including_runner_absent': all(r['absent'] for r in observations),
                       'observations': observations},
         'api_worker_count': len(children['workers']), 'broker_absence': broker_absence,
         'new_ports': new_ports, 'protected': protected, 'new_outbox_events': new_outbox,
         'data_counts': data_counts, 'source_files_verified': len(app.binding['source_files']),
         'controller_sha256': hashlib.sha256((WORK / 'deployment/native/application.py').read_bytes()).hexdigest()}
appmod.private_write(AUDIT / 'post-run-proof.json', appmod.json_bytes(proof))
print(json.dumps({'run': run.name, 'driver_exit': driver['actual_exit_code'], 'summary_success': summary['success'],
                  'cleanup_success': summary['cleanup_success'], 'scan_count_actual': len(scans),
                  'all_owned_sessions_revoked': all(s['revoked_at'] is not None for s in sessions),
                  'spawn_counts': proof['spawn_counts'], 'all_recorded_pids_absent': proof['post_stop']['all_recorded_including_runner_absent'],
                  'broker_absence': broker_absence, 'new_ports_closed': all(v['unbound'] for v in new_ports.values()),
                  'protected9_exact_match': protected['all9_exact_match'], 'new_outbox_events': new_outbox,
                  'source_files_verified': proof['source_files_verified']}))
