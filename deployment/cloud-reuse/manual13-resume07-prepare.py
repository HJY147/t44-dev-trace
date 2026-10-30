"""One explicit APP-local recovery/preparation chain; never runs benchmark or cloud lifecycle."""
import argparse
import hashlib
import importlib.util
import json
import os
import re
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

SOURCE = '90b734f65ce6ee9f5c217e885bc7ea4857e32b48'
LAYOUT = '1036b48b46a448abd0567133535b53475d2c6bbf428c064e6c38c544db291adb'
PROJECT = 't44-cloud-r30finalp09-p'
DATABASE = 't44c_r30finalp09_p'
HELPER_SHA = {'cohort_maintenance.py': 'be486ee976308000e5323321f20f91e26a562c494ad402fe0714996cfb61823a'}
OLD_SHA = {'backend/authorization.TEMPLATE.json': 'b1a943ddc37839b06846d3efd7931863684b8c6f7a775c3f67a4aa291edd4fb7', 'backend/host_runner.py': 'ee72bcb22ae9a95d9333b91921b9aa91767abbe96c92e751bc804df4c954f67d', 'backend/refresh_runtime.py': 'a2cc1f7b0142a8b2093fcc76c91dd2230950b236d5af8104d2673e56e6bc61d5', 'backend/refresh_core.py': 'fa238ec771d71ea2986823c6f2837e36c4838f34052431e2a855f4e7355b0070', 'backend/process_guard.py': 'd2e225b6816d2adb9a2aa7c399c53f0dc4ecdb8ad375fb39c864416a660b3708', 'backend/runtime_support.py': 'bec01e4038ef4ca5d6ba6d048e96fb8c7cb32933f705fd65a6995d24d9753170', 'deployment/rotate_scheduler_token.py': '47640ba975f210b9ca7e7f66e718711f42766093bf6a0e3749f0f60ae210fe8f', 'deployment/prepare_next_manual.py': 'e0fb1832a35857b0f3b5dc394bf4ad31a81a3b0b83747e46b92d04b825e2970a', 'deployment/P09-existing-containers.PUBLIC.json': 'a5d5fe7a71064bff89b5bded39fdcdfeb7315b7879df8b2ef57e23c2a049230e', 'deployment/resume_existing_p09.py': '7a2047fa097161ec7587070c4f5af3eaf52c3df05a7fb2984e56405bc7a8c698', 'deployment/cms_five_transport.py': '466fa0b7ce4d00d1cf5ab1209bdaff0ee266279210971cc76145d677af51ab26'}

PROBE = r'''import hashlib,json,sys
from sqlalchemy import text,bindparam
from t44.settings import Settings
from t44.persistence import create_mysql_engine
v=json.load(sys.stdin);ids=v['ids'];transition=set(v['transition'])
service_id=v['service_id'];namespace=v['namespace']
assert type(service_id)is int and service_id>0 and namespace=='t44-cloud-r30finalp09-p'
assert len(ids)==800 and len(set(ids))==800 and len(transition)==400 and all(type(i)is int and i>0 for i in ids)
e=create_mysql_engine(Settings.from_env().mysql_settings());assert e.url.database=='t44c_r30finalp09_p'
try:
 with e.connect() as c:
  indexes=[list(r) for r in c.exec_driver_sql('SELECT TABLE_NAME,INDEX_NAME,SEQ_IN_INDEX,COLUMN_NAME,NON_UNIQUE,COLLATION,SUB_PART,INDEX_TYPE,IS_VISIBLE FROM INFORMATION_SCHEMA.STATISTICS WHERE TABLE_SCHEMA=DATABASE() ORDER BY TABLE_NAME,INDEX_NAME,SEQ_IN_INDEX')]
  counts={t:c.exec_driver_sql('SELECT COUNT(*) FROM `'+t+'`').scalar_one() for t in ('projects','tasks','task_dependencies','reviews','decisions')}
  rows=c.execute(text('SELECT id,state,blocked_from_state FROM tasks WHERE id IN :ids').bindparams(bindparam('ids',expanding=True)),{'ids':ids}).all()
  service=c.execute(text('SELECT id,active,name FROM service_accounts WHERE id=:service_id'),{'service_id':service_id}).one_or_none()
 found=sorted(r[0]for r in rows);tr=[r for r in rows if r[0]in transition]
 target=[r for r in indexes if r[0]=='outbox_events'and r[1]=='ix_outbox_confirmed_recovery']
 canon=lambda x:json.dumps(x,separators=(',',':'),ensure_ascii=True).encode()
 service_public={'id':None if service is None else service[0],'active':service is not None and bool(service[1]),'scope_match':service is not None and service[2].startswith(namespace)}
 print(json.dumps({'service_account':service_public,'index_layout_sha256':hashlib.sha256(canon(indexes)).hexdigest(),'target_index':target,'counts':counts,'original800_count':len(found),'original800_sha256':hashlib.sha256(canon(found)+b'\n').hexdigest(),'transition400_count':len(tr),'transition_state2':sum(r[1]==2 and r[2]is None for r in tr),'transition_state3_from2':sum(r[1]==3 and r[2]==2 for r in tr)}))
finally:e.dispose()
'''


def need(value, code):
    if not value:
        raise ValueError(code)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def put(path, value):
    raw = (json.dumps(value, sort_keys=True, indent=2) + '\n').encode()
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())


def regular(path):
    need(path.is_absolute() and path.resolve() == path and path.is_file() and not path.is_symlink(),
         'CANONICAL_REGULAR_INPUT_REQUIRED')
    need(path.stat().st_size <= 32 * 1024 * 1024, 'INPUT_TOO_LARGE')
    return path.read_bytes()


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result



PREVIOUS_PREFIX_SHA256 = 'e485eabd7cc3c436e60545dba885c0e235e0bed3d69c7dd5eb5d4617255a6f7f'

def previous_prefix(path, ids_sha):
    raw = regular(path)
    need(digest(raw) == PREVIOUS_PREFIX_SHA256, 'EXACT_STOPPED06_PUBLIC_PREFIX_REQUIRED')
    value = json.loads(raw)
    row = value['maintenance/receipt.PUBLIC.json']
    check_receipt(row)
    need(row['operation_id'] == 'r30restoretransition06' and row['original_ids_sha256'] == ids_sha,
         'PREVIOUS06_MAINTENANCE_ORIGINAL_IDS_REQUIRED')
    material = value['material06/material/material.PUBLIC.json']
    need(material['packet_run_id'] == 'r30materialresume06' and
         material['material_process_exit_proof']['process_exit_proven'] is True,
         'PREVIOUS06_MATERIAL_EXIT_REQUIRED')
    need(value['continuation.PUBLIC.json']['status'] == 'BLOCKED_PRESERVE_PREFIX_NO_AUTOMATIC_RETRY',
         'STOPPED06_PREFIX_STATUS_REQUIRED')
    return {'source_sha256': digest(raw), 'historical_only': True,
            'maintenance06_completed': True, 'material06_exit_proven_then': True,
            'not_current_process_or_inventory_proof': True}


def inventory(packet):
    clients = packet['inventory']['clients']
    need(len(clients) == 400 and {r['client_id'] for r in clients} == set(range(400)), 'ORIGINAL400_REQUIRED')
    transition = [r['transition_task']['id'] for r in clients]
    ids = sorted([r[k]['id'] for r in clients for k in ('transition_task', 'escalation_task')])
    need(len(set(ids)) == 800 and all(type(i) is int and i > 0 for i in ids), 'ORIGINAL800_UNIQUE_IDS_REQUIRED')
    return {'ids': ids, 'transition': transition}, digest((json.dumps(ids, separators=(',', ':')) + '\n').encode())


def pinned(args):
    need(HELPER_SHA and OLD_SHA, 'FROZEN_TOOL_RELEASE_REQUIRED')
    for relative, expected in OLD_SHA.items():
        directory = args.backend_tools if relative.startswith('backend/') else args.deployment_tools
        need(digest(regular(directory / relative.split('/', 1)[1])) == expected, 'OLD_TOOL_SHA_MISMATCH')
    for filename, expected in HELPER_SHA.items():
        need(digest(regular(args.helper_dir / filename)) == expected, 'MAINTENANCE_HELPER_SHA_MISMATCH')


def maintenance_authorization(packet_raw, ids_sha, operation_id):
    return {'schema': 'manual11-cohort-maintenance-authorization-v2', 'root_approved': True,
        'benchmark_grant_allow': False, 'operations': ['login', 'readonly-inventory', 'unblock-existing-owned', 'readonly-audit', 'final-inventory'],
        'operation_id': operation_id, 'source_sha': SOURCE, 'old_packet_sha256': digest(packet_raw),
        'namespace': PROJECT, 'database': DATABASE, 'original_ids_sha256': ids_sha,
        'require_infrastructure_and_old_controller_guards': True,
        'require_exclusive_no_benchmark_or_other_writer': True}


def validate_original_five(args, packet_raw, packet, ids_sha):
    need(packet['identity']['git_commit'] == SOURCE, 'ORIGINAL90B_SOURCE_REQUIRED')
    for filename, expected in (
            ('source-manifest.json', packet['identity']['source_manifest_sha256']),
            ('backend-bundle-manifest.json', packet['identity']['backend_bundle_manifest_sha256']),
            ('backend-import-receipt.json', packet['loaded_receipt_sha256'])):
        raw = regular(args.packet.parent / filename)
        need(digest(raw) == expected, 'ORIGINAL_MANIFEST_OR_IMPORT_SHA_MISMATCH')
        json.loads(raw)
    # The frozen owner's pure validator checks packet binding, original subjects,
    # all800 IDs/40 projects and maintenance authorization before any live mutation.
    helper = load(args.helper_dir / 'cohort_maintenance.py', 'preflight_frozen_maintenance')
    helper.authorization(packet, packet_raw,
                         maintenance_authorization(packet_raw, ids_sha, args.maintenance_id),
                         json.loads(regular(args.accounts)))


def check_probe(row, ids_sha, before=None, restored=False):
    shape = [['outbox_events', 'ix_outbox_confirmed_recovery', i + 1, column, 1, 'A', None, 'BTREE', 'YES']
             for i, column in enumerate(('status', 'event_type', 'id', 'confirmed_at'))]
    need(row['index_layout_sha256'] == LAYOUT and row['target_index'] == shape, 'EXACT_ALREADY_APPLIED_INDEX_REQUIRED_NO_DDL')
    need(row['original800_count'] == 800 and row['original800_sha256'] == ids_sha and row['transition400_count'] == 400,
         'ORIGINAL800_ID_CONSERVATION_REQUIRED')
    need(row['transition_state2'] + row['transition_state3_from2'] == 400, 'NONRESTORABLE_TRANSITION_STATE')
    if before is not None:
        need(row['counts'] == before['counts'], 'BUSINESS_TABLE_TOTALS_CHANGED')
    if restored:
        need(row['transition_state2'] == 400 and row['transition_state3_from2'] == 0, 'RESTORED400_STATE2_REQUIRED')



def check_original_counts(row, packet):
    expected = {table: packet['counts'][field] for field, table in {
        'projects': 'projects', 'tasks': 'tasks', 'dependencies': 'task_dependencies',
        'reviews': 'reviews', 'decisions': 'decisions'}.items()}
    need(row['counts'] == expected, 'ORIGINAL_PACKET_BUSINESS_COUNTS_CHANGED_BEFORE_MAINTENANCE')


def check_original_service(row, packet):
    expected = packet['sessions']['service']['user_id']
    require_row = {'id': expected, 'active': True, 'scope_match': True}
    need(type(expected) is int and expected > 0 and row.get('service_account') == require_row,
         'EXISTING_SERVICE_ACCOUNT_SCOPE_BEFORE_MAINTENANCE')


def check_receipt(row):
    need(row.get('status') == 'COMPLETE_EXISTING400_STATE2_ORIGINAL800_PRESERVED' and
         all(row.get(k) == value for k, value in {'preflight400': 400, 'final400_state2': 400,
             'original800_before': 800, 'original800_after': 800, 'project_task_totals_unchanged': True,
             'new_tasks': 0, 'seed_calls': 0, 'exit_code': 0}.items()), 'MAINTENANCE_COMPLETION_REQUIRED')


def check_material(row, before):
    need(row.get('status') == 'FRESH_MATERIAL_NOT_BENCHMARK_AUTHORIZATION' and row.get('new_tasks') == 0 and
         row.get('seed_calls') == 0 and row.get('original_task_ids_preserved') is True and
         row.get('material_process_exit_proof', {}).get('process_exit_proven') is True, 'FRESH_MATERIAL_PROOF_REQUIRED')
    expected = {k: before['counts'][v] for k, v in {'projects': 'projects', 'tasks': 'tasks',
                'dependencies': 'task_dependencies', 'reviews': 'reviews', 'decisions': 'decisions'}.items()}
    need(row.get('counts') == expected, 'MATERIAL_BUSINESS_COUNTS_CHANGED')
    sessions = row.get('session_attestations', {})
    need(set(sessions) == {'manager', 'developer', 'reviewer', 'service'}, 'FOUR_SESSION_ATTESTATIONS_REQUIRED')
    now = datetime.now(timezone.utc).timestamp()  # noqa: UP017
    need(all(datetime.fromisoformat(v['expires_at'].replace('Z', '+00:00')).timestamp() - now >= 900
             for v in sessions.values()), 'NEW_SESSION_REMAINING_BELOW900_SECONDS')


def with_total_subprocess_budget(function):
    """Cap imported helpers' subprocess.run timeouts within this CLI invocation."""
    def run(self, *args, **kwargs):
        original = subprocess.run
        def bounded(*argv, **options):
            remaining = self.deadline - time.monotonic()
            need(remaining > 0, 'TOTAL_PREPARATION1800_DEADLINE_EXCEEDED')
            requested = options.get('timeout')
            options['timeout'] = min(remaining, requested) if requested is not None else remaining
            return original(*argv, **options)
        subprocess.run = bounded
        try:
            return function(self, *args, **kwargs)
        finally:
            subprocess.run = original
    return run


class Pipeline:
    def __init__(self, args):
        self.args, self.index = args, 0
        self.deadline = time.monotonic() + 1800

    def child(self, label, argv, timeout, stdin=None):
        timeout = min(timeout, self.deadline - time.monotonic())
        need(timeout > 0, 'TOTAL_PREPARATION1800_DEADLINE_EXCEEDED')
        self.index += 1
        stem = self.args.output / (f'{self.index:02d}-' + label)
        receipt = {'step': label, 'status': 'INCOMPLETE', 'retry': False}
        process = None
        try:
            with Path(str(stem) + '.stdout.private').open('xb') as out, Path(str(stem) + '.stderr.private').open('xb') as err:
                process = subprocess.Popen(list(map(str, argv)), stdin=subprocess.PIPE if stdin else subprocess.DEVNULL,
                                           stdout=out, stderr=err, start_new_session=True)
                process.communicate(input=stdin, timeout=timeout)
            need(process.returncode == 0, 'CHILD_FAILED_OR_UNKNOWN_NO_RETRY')
            receipt.update(status='CHILD_EXIT0', exit_code=0)
        except BaseException:
            if process is not None and process.poll() is None:
                os.killpg(process.pid, signal.SIGTERM)
                try:
                    process.wait(timeout=15)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait(timeout=10)
            receipt.update(status='BLOCKED_PARTIAL_OR_UNKNOWN_NO_RETRY', exit_code=None if process is None else process.returncode)
            raise
        finally:
            put(Path(str(stem) + '.PUBLIC.json'), receipt)
        return Path(str(stem) + '.stdout.private').read_bytes()

    def probe(self, api, ids, name):
        row = json.loads(self.child(name, ['docker', '--context', 'default', 'exec', '-i', api, 'python', '-B', '-c', PROBE],
                                    30, json.dumps(ids).encode()))
        put(self.args.output / (name + '.PUBLIC.json'), row)
        return row

    @with_total_subprocess_budget
    def run(self):
        a = self.args
        need(a.authorize_existing_task_restoration and a.ack_exclusive_no_benchmark_or_other_writer and os.geteuid() == 0, 'EXPLICIT_ROOT_TASK_RESTORATION_AUTHORIZATION_REQUIRED')
        need(a.output.is_absolute() and a.output.parent.resolve() == a.output.parent and not a.output.exists(),
             'NEW_EXCLUSIVE_OUTPUT_REQUIRED')
        for value in (a.maintenance_id, a.material_id):
            need(re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,63}', value), 'NEW_OPERATION_ID_REQUIRED')
        need(a.maintenance_id != a.material_id and a.material_id == 'r30materialresume07' and
             a.maintenance_id == 'r30restoretransition07', 'EXACT_MAINTENANCE07_AND_MATERIAL07_REQUIRED')
        pinned(a)
        packet_raw = regular(a.packet)
        packet = json.loads(packet_raw)
        need(a.packet.name == 'session.private.json' and a.ca == a.packet.parent / 'ca.pem', 'ORIGINAL_HOST_FIVE_CA_REQUIRED')
        regular(a.accounts)
        need(digest(regular(a.ca)) == packet['environment']['ca_sha256'], 'ORIGINAL_CA_SHA_REQUIRED')
        need(packet['run_id'] != a.material_id, 'NEW_MATERIAL_ID_REQUIRED')
        ids, ids_sha = inventory(packet)
        previous = previous_prefix(a.previous_prefix, ids_sha)
        ids.update(service_id=packet['sessions']['service']['user_id'], namespace=PROJECT)
        validate_original_five(a, packet_raw, packet, ids_sha)
        cms = load(a.deployment_tools / 'cms_five_transport.py', 'resume_cms')
        need(digest(regular(a.load_cert)) == a.load_cert_sha256, 'PINNED_RECIPIENT_CERT_REQUIRED')
        cms.modern(a.openssl)
        cms.command(a.openssl, ['x509', '-in', a.load_cert, '-checkend', '1800', '-noout'])
        cms.command(a.openssl, ['x509', '-in', a.ca, '-checkend', '1800', '-noout'])
        os.umask(0o077)
        a.output.mkdir(mode=0o700)
        summary = {'status': 'INCOMPLETE', 'maintenance_id': a.maintenance_id, 'material_id': a.material_id,
                   'QA_executed': False, 'benchmark_started': False, 'seed_or_ddl_executed': False, 'retry': False,
                   'stage': 'original-seven-inspection', 'owned_worker_state': 'NOT_YET_OBSERVED'}
        try:
            prep = load(a.deployment_tools / 'prepare_next_manual.py', 'resume_original_prepare')
            resume = load(a.deployment_tools / 'resume_existing_p09.py', 'resume_original_seven')
            expected = resume.expected()
            initial = resume.inspect(expected)
            running_workers = [role for role in ('consumer', 'scheduler') if initial[role]['running']]
            summary['owned_worker_state'] = 'INITIAL_RUNNING' if running_workers else 'INITIAL_STOPPED'
            need(not running_workers or a.authorize_owned_worker_stop, 'EXPLICIT_OWNED_WORKER_STOP_AUTHORIZATION_REQUIRED')
            put(a.output / 'previous06-history.PUBLIC.json', previous)
            put(a.output / 'original-seven.PUBLIC.json', {'containers': list(initial.values())})
            bootstrap = a.output / 'bootstrap'
            bootstrap.mkdir(mode=0o700)
            summary['stage'] = 'retire-old-timer'
            prep.retire_old_timer(bootstrap, resume.PROJECT)
            if running_workers:
                summary.update(stage='stop-owned-consumer-scheduler', owned_worker_state='STOP_REQUESTED_OUTCOME_UNKNOWN')
                self.child('stop-owned-workers', ['docker', '--context', 'default', 'stop', '--time', '20',
                           *[expected[role]['id'] for role in running_workers]], 50)
            stopped = resume.inspect(expected)
            put(a.output / 'owned-workers-after-stop.PUBLIC.json', {'containers': list(stopped.values()),
                'stop_requested_roles': running_workers, 'only_original_owned_workers_may_be_stopped': True})
            need(not stopped['consumer']['running'] and not stopped['scheduler']['running'], 'OWNED_WORKERS_NOT_PROVEN_STOPPED')
            summary.update(stage='start-original-infra', owned_worker_state='CONFIRMED_STOPPED')
            # Only original container start; no recreate/build/pull/DDL/seed.
            import time
            end = min(time.monotonic() + 300, self.deadline)
            for roles, healthy in ((['mysql', 'rabbitmq'], True), (['api'], True), (['web', 'tls-gateway'], False)):
                resume.start(expected, roles)
                resume.wait(expected, roles, healthy, end)
            summary['stage'] = 'index-and-inventory-preflight'
            before = self.probe(expected['api']['id'], ids, 'before-maintenance')
            check_probe(before, ids_sha)
            check_original_counts(before, packet)
            check_original_service(before, packet)
            if before['transition_state2'] == 400 and before['transition_state3_from2'] == 0:
                # Current guarded readback, not old success alone, permits no restore operation.
                check_probe(before, ids_sha, restored=True)
                put(a.output / 'maintenance-skipped.PUBLIC.json', {
                    'status': 'CURRENT400_ALREADY_STATE2_NO_RESTORE_HTTP',
                    'historical_prefix_sha256': previous['source_sha256'],
                    'original800_ids_sha256': ids_sha, 'maintenance_http_requests': 0,
                    'current_qualification_still_required_by_material_tool': True})
                summary['maintenance_executed'] = False
            else:
                authorization = maintenance_authorization(packet_raw, ids_sha, a.maintenance_id)
                auth_file = a.output / 'maintenance-authorization.PUBLIC.json'
                put(auth_file, authorization)
                maintenance = a.output / 'maintenance'
                summary['stage'] = 'restore-existing-transition-cohort'
                self.child('restore-existing-transition-cohort', [sys.executable, '-B', a.helper_dir / 'cohort_maintenance.py',
                    '--mode', 'apply', '--root-admit-maintenance', '--old-packet', a.packet, '--accounts', a.accounts,
                    '--authorization', auth_file, '--ca', a.ca, '--output', maintenance, '--backend-tools', a.backend_tools,
                    '--api-container', expected['api']['id'], '--expected-api-image-id', expected['api']['image_id']], 330)
                check_receipt(json.loads(regular(maintenance / 'receipt.PUBLIC.json')))
                summary['stage'] = 'maintenance-readback'
                after = self.probe(expected['api']['id'], ids, 'after-maintenance')
                check_probe(after, ids_sha, before, restored=True)
                summary['maintenance_executed'] = True
            # Original chain already includes token rotation, workers, scan and CMS: exactly once.
            material_output = a.output / 'material07'
            summary.update(stage='original-prepare-material07-full-chain', owned_worker_state='ORIGINAL_CHAIN_MAY_START_WORKERS')
            self.child('original-prepare-material07-full-chain', [sys.executable, '-B', a.deployment_tools / 'prepare_next_manual.py',
                '--material-id', a.material_id, '--output', material_output, '--backend-tools', a.backend_tools,
                '--old-inputs', a.packet.parent, '--accounts', a.accounts, '--load-cert', a.load_cert,
                '--load-cert-sha256', a.load_cert_sha256, '--openssl', a.openssl, '--deadline-monotonic', str(self.deadline)], 1800)
            summary['stage'] = 'material07-final-proof'
            material = json.loads(regular(material_output / 'material/material.PUBLIC.json'))
            check_material(material, before)
            final = self.probe(expected['api']['id'], ids, 'after-material07')
            check_probe(final, ids_sha, before, restored=True)
            ready = json.loads(regular(material_output / 'APP-ready.PUBLIC.json'))
            need(ready['status'] == 'APP_MATERIAL_SEALED_NOT_BENCHMARK_AUTHORIZATION', 'ORIGINAL_READY_CHAIN_REQUIRED')
            seven = resume.inspect(expected)
            put(a.output / 'final-seven.PUBLIC.json', {'containers': list(seven.values())})
            need(all(row['running'] and row.get('health') in (None, 'healthy') for row in seven.values()),
                 'FINAL_SEVEN_RUNNING_AND_CONFIGURED_HEALTHCHECKS_REQUIRED')
            summary.update(stage='complete', owned_worker_state='ALL_SEVEN_RUNNING_CONFIGURED_HEALTHCHECKS_PASSED')
            summary.update(status='PREPARATION_COMPLETE_NOT_FORMAL_ADMISSION', material_ready=str(material_output / 'APP-ready.PUBLIC.json'),
                           applied_index_layout_sha256=LAYOUT, original800_ids_sha256=ids_sha,
                           old04_overwritten=False, formal_p13_prepared_or_executed=False)
            return summary
        except BaseException:
            summary['status'] = 'BLOCKED_PRESERVE_PREFIX_NO_AUTOMATIC_RETRY'
            raise
        finally:
            put(a.output / 'continuation.PUBLIC.json', summary)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ('backend-tools', 'deployment-tools', 'helper-dir', 'packet', 'accounts', 'ca', 'load-cert', 'output', 'previous-prefix'):
        parser.add_argument('--' + key, type=Path, required=True)
    for key in ('maintenance-id', 'material-id', 'load-cert-sha256'):
        parser.add_argument('--' + key, required=True)
    parser.add_argument('--authorize-existing-task-restoration', action='store_true')
    parser.add_argument('--authorize-owned-worker-stop', action='store_true')
    parser.add_argument('--ack-exclusive-no-benchmark-or-other-writer', action='store_true')
    parser.add_argument('--openssl', default='openssl')
    args = parser.parse_args()
    try:
        print(json.dumps(Pipeline(args).run(), sort_keys=True))
        return 0
    except BaseException as error:
        # Neither private child output nor traceback/error body is printed.
        print(json.dumps({'status': 'BLOCKED_NO_RETRY', 'error_class': type(error).__name__, 'output': str(args.output)}))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
