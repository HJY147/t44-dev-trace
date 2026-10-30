"""APP-local original-container recovery and new neutral material; never a benchmark grant."""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import secrets
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
TOTAL_DEADLINE = None


def module(name):
    spec = importlib.util.spec_from_file_location(name, HERE / (name + '.py'))
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


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
    return value


def command(argv, timeout=20, allow_not_found=False):
    if TOTAL_DEADLINE is not None:
        timeout = min(timeout, TOTAL_DEADLINE - time.monotonic())
        need(timeout > 0, 'TOTAL_PREPARATION1800_DEADLINE_EXCEEDED')
    result = subprocess.run(list(map(str, argv)), capture_output=True, timeout=timeout, check=False)
    missing_unit = allow_not_found and result.returncode == 1 and b'LoadState=not-found' in result.stdout.splitlines()
    need(result.returncode == 0 or missing_unit, 'CHILD_FAILED_NO_PRIVATE_OUTPUT')
    return result.stdout


def show(unit):
    raw = command(['systemctl', 'show', unit, '--property=Id,LoadState,ActiveState,SubState,UnitFileState,Triggers,NextElapseUSecRealtime,LastTriggerUSec'], allow_not_found=True)
    row = dict(line.split('=', 1) for line in raw.decode().splitlines() if '=' in line)
    need(row.get('LoadState') in {'loaded', 'not-found'}, 'UNIT_STATE_UNKNOWN')
    need(row.get('ActiveState') in {'inactive', 'failed', 'active'}, 'UNIT_TRANSITION_OR_UNKNOWN')
    return row


def retire_old_timer(output, project):
    """Stop only the exact owned timer; never invoke/stop the old controller service."""
    timer = project + '-stop.timer'
    service = project + '-stop.service'
    names = [timer, service, 't44-final-p09-continuous.service']
    before = {name: show(name) for name in names}
    need(all(before[name]['ActiveState'] in {'inactive', 'failed'} for name in names[1:]),
         'OLD_CONTROLLER_ACTIVE_NO_AUTOMATIC_INTERVENTION')
    # Original unit bytes stay untouched. Backups are host-private, never collected.
    backup = output / 'old-units.private'
    backup.mkdir(mode=0o700)
    hashes = {}
    for name in names:
        source = Path('/etc/systemd/system') / name
        if source.is_file() and not source.is_symlink():
            raw = source.read_bytes()
            fd = os.open(backup / name, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(fd, 'wb') as stream:
                stream.write(raw)
            hashes[name] = digest(raw)
    if before[timer]['LoadState'] != 'not-found':
        command(['systemctl', 'disable', '--now', timer])
    after = {name: show(name) for name in names}
    need(after[timer]['ActiveState'] in {'inactive', 'failed'} and
         after[timer].get('UnitFileState') not in {'enabled', 'enabled-runtime'}, 'OLD_TIMER_NOT_RETIRED')
    need(all(after[name]['ActiveState'] in {'inactive', 'failed'} for name in names[1:]), 'OLD_CONTROLLER_BECAME_ACTIVE')
    return put(output / 'old-timer.PUBLIC.json', {'before': before, 'after': after,
               'original_unit_sha256': hashes, 'only_mutated_unit': timer,
               'old_controller_executed': False, 'old_unit_files_preserved': True})


SCAN_CODE = """from t44.persistence import SqlAlchemyUnitOfWorkFactory,create_mysql_engine
from t44.settings import Settings
from t44.services.common import wire
import json
settings=Settings.from_env().mysql_settings()
assert settings.database == 't44c_r30finalp09_p'
f=SqlAlchemyUnitOfWorkFactory(create_mysql_engine(settings))
with f() as u:
 rows=u.gateway.rows('scan_runs',{},order_by=('-id',),limit=4)
print(json.dumps(wire([{k:r.get(k) for k in ['id','status','started_at','heartbeat_at','finished_at','error_code','scanned_count','created_count','duplicate_count']} for r in rows])))
"""


def scan_after_rotation(api, completed, output, seconds=900):
    deadline = time.monotonic() + seconds
    if TOTAL_DEADLINE is not None:
        deadline = min(deadline, TOTAL_DEADLINE)
    threshold = datetime.fromisoformat(completed.replace('Z', '+00:00'))
    while True:
        remaining = deadline - time.monotonic()
        need(remaining > 0, 'NO_SUCCESSFUL_POST_ROTATION_SCAN_WITHIN_BOUND')
        rows = json.loads(command(['docker', '--context', 'default', 'exec', api, 'python', '-B', '-c', SCAN_CODE],
                                  timeout=min(10, remaining)))
        receipt = {'rotation_completed_utc': completed, 'rows': rows,
                   'observed_utc': datetime.now(timezone.utc).isoformat(),
                   'new_scanner_started': False, 'business_event_manually_created': False,
                   'proof_kind': 'existing_persistent_scanner_native_authenticated_runtime_not_HTTP_probe'}
        # Keep every original observation, including failures, without rewriting it.
        put(output / ('scan-' + secrets.token_hex(6) + '.PUBLIC.json'), receipt)
        need(time.monotonic() < deadline, 'NO_SUCCESSFUL_POST_ROTATION_SCAN_WITHIN_BOUND')
        fresh = [r for r in rows if r.get('started_at') and r.get('finished_at') and
                 datetime.fromisoformat(r['started_at'].replace('Z', '+00:00')) >= threshold and
                 datetime.fromisoformat(r['finished_at'].replace('Z', '+00:00')) >= threshold]
        need(not any(r['status'] == 3 or r.get('error_code') is not None for r in fresh),
             'POST_ROTATION_SCAN_REPORTED_FAILURE')
        success = [r for r in fresh if r['status'] == 2 and r.get('error_code') is None and r.get('scanned_count', 0) > 0]
        if success:
            receipt['successful_new_scan_ids'] = [r['id'] for r in success]
            return put(output / 'scanner.PUBLIC.json', receipt)
        time.sleep(min(5, max(0, deadline - time.monotonic())))


def prepare(args):
    global TOTAL_DEADLINE
    TOTAL_DEADLINE = args.deadline_monotonic
    need(0 < TOTAL_DEADLINE - time.monotonic() <= 1800, 'CURRENT_TOTAL_PREPARATION_DEADLINE_REQUIRED')
    need(os.geteuid() == 0, 'APP_ROOT_REQUIRED')
    need(re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,63}', args.material_id), 'NEW_MATERIAL_ID_REQUIRED')
    need(args.output.is_absolute() and args.output.parent.resolve() == args.output.parent and
         not args.output.exists(), 'NEW_CANONICAL_OUTPUT_REQUIRED')
    need(args.backend_tools.is_absolute() and (args.backend_tools / 'host_runner.py').is_file(), 'BACKEND_TOOLS_REQUIRED')
    old_inputs = args.old_inputs
    names = ['session.private.json', 'ca.pem', 'source-manifest.json', 'backend-bundle-manifest.json', 'backend-import-receipt.json']
    need(old_inputs.is_absolute() and old_inputs.resolve() == old_inputs and all((old_inputs / n).is_file() and
         not (old_inputs / n).is_symlink() for n in names), 'ORIGINAL_HOST_FIVE_REQUIRED')
    old_raw = (old_inputs / 'session.private.json').read_bytes()
    old = json.loads(old_raw)
    need(old['run_id'] != args.material_id, 'MATERIAL_ID_MUST_BE_NEW')
    need(args.accounts.is_file() and not args.accounts.is_symlink(), 'ORIGINAL_ACCOUNTS_REQUIRED')
    cms = module('cms_five_transport')
    cms.modern(args.openssl)
    need(cms.sha(cms.read(args.load_cert)) == args.load_cert_sha256, 'PINNED_LOAD_CERT_REQUIRED')
    cms.command(args.openssl, ['x509', '-in', args.load_cert, '-checkend', '0', '-noout'])
    resume = module('resume_existing_p09')
    expected = resume.expected()
    initial = resume.inspect(expected)  # exact original7 IDs/images/resources before mutation
    template = json.loads((args.backend_tools / 'authorization.TEMPLATE.json').read_bytes())
    template.update(root_approved=True, old_packet_sha256=digest(old_raw), new_packet_run_id=args.material_id,
                    packet_nonce=secrets.token_hex(32))
    need(template['namespace'] == resume.PROJECT and template['benchmark_grant_allow'] is False,
         'EXACT_BACKEND_MATERIAL_TEMPLATE_REQUIRED')
    spec = importlib.util.spec_from_file_location('backend_refresh_core', args.backend_tools / 'refresh_core.py')
    backend_core = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(backend_core)
    backend_core.authorization(template, old_raw)  # validate before timer/container mutation
    os.umask(0o077)
    args.output.mkdir(mode=0o700)
    put(args.output / 'initial-containers.PUBLIC.json', {'containers': list(initial.values()), 'historical_receipts_reused_as_live': False})
    retire_old_timer(args.output, resume.PROJECT)
    end = min(time.monotonic() + 300, TOTAL_DEADLINE)
    # Already-running workers are preserved; the existing scanner rereads directory-bound token.
    for roles, healthy in [(['mysql', 'rabbitmq'], True), (['api'], True), (['web', 'tls-gateway'], False)]:
        resume.start(expected, roles)
        resume.wait(expected, roles, healthy, end)
    authorization = args.output / 'authorization.PUBLIC.json'
    put(authorization, template)
    material = args.output / 'material'
    argv = [sys.executable, '-B', args.backend_tools / 'host_runner.py',
            '--api-container', expected['api']['id'], '--expected-api-image-id', expected['api']['image_id'],
            '--discover-maintenance-gateway', '--old-packet', old_inputs / 'session.private.json',
            '--accounts', args.accounts, '--authorization', authorization, '--ca', old_inputs / 'ca.pem',
            '--source-manifest', old_inputs / 'source-manifest.json', '--bundle-manifest', old_inputs / 'backend-bundle-manifest.json',
            '--import-receipt', old_inputs / 'backend-import-receipt.json', '--output', material]
    # host_runner itself preserves private failure prefixes and audits actual process-group exit.
    command(argv, timeout=400)
    public = json.loads((material / 'material.PUBLIC.json').read_bytes())
    need(public.get('status') == 'FRESH_MATERIAL_NOT_BENCHMARK_AUTHORIZATION' and
         public.get('material_process_exit_proof', {}).get('process_exit_proven') is True,
         'FRESH_MATERIAL_AND_TRUE_EXIT_PROOF_REQUIRED')
    rotation = module('rotate_scheduler_token').rotate(material / 'material.PUBLIC.json', args.output / 'scheduler-backup.private')
    completed = datetime.now(timezone.utc).isoformat()
    rotation['rotation_completed_utc'] = completed
    put(args.output / 'rotation.PUBLIC.json', rotation)
    resume.start(expected, ['consumer', 'scheduler'])
    final = resume.wait(expected, ['mysql', 'rabbitmq', 'api', 'consumer', 'scheduler'], True, min(time.monotonic() + 180, TOTAL_DEADLINE))
    put(args.output / 'containers.PUBLIC.json', {'containers': list(final.values()), 'no_recreate_build_pull_seed': True})
    scan_after_rotation(expected['api']['id'], completed, args.output)
    # Seal after recovery; seals original new five bytes only; never read them into stdout.
    cipher = args.output / 'host-five.cms'
    sealed = cms.seal(args.openssl, material / 'inputs', args.load_cert, args.load_cert_sha256, cipher)
    retire_check = {name: show(name) for name in [resume.PROJECT + '-stop.timer', resume.PROJECT + '-stop.service', 't44-final-p09-continuous.service']}
    need(all(x['ActiveState'] in {'inactive', 'failed'} for x in retire_check.values()), 'OLD_UNIT_BECAME_ACTIVE_NO_READY')
    return put(args.output / 'APP-ready.PUBLIC.json', {'status': 'APP_MATERIAL_SEALED_NOT_BENCHMARK_AUTHORIZATION',
               'observed_utc': cms.now(), 'material_id': args.material_id, 'material_sha256': digest((material / 'material.PUBLIC.json').read_bytes()),
               'cipher': str(cipher), 'cipher_sha256': sealed['cipher_sha256'], 'cert_sha256': args.load_cert_sha256,
               'initial_running_workers_preserved': [r for r in ['consumer', 'scheduler'] if initial[r]['running']],
               'scanner_HTTP_success_proven': False, 'post_rotation_persistent_native_scan_success_proven': True,
               'external_writer_absence_proven': False,
               'QA_executed': False, 'seed_or_database_rebuild_executed': False, 'cloud_API_or_network_changed': False})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--deadline-monotonic', type=float, required=True)
    parser.add_argument('--material-id', required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--backend-tools', type=Path, default=Path('/root/t44-manual-input-tools'))
    parser.add_argument('--old-inputs', type=Path, default=Path('/root/t44-final-20261029/P09/P-packet/output/packet/inputs'))
    parser.add_argument('--accounts', type=Path, default=Path('/root/t44-final-20261029/P09/P-accounts/output/accounts.initialized.private.json'))
    parser.add_argument('--load-cert', type=Path, required=True)
    parser.add_argument('--load-cert-sha256', required=True)
    parser.add_argument('--openssl', default='openssl')
    args = parser.parse_args()
    try:
        original_run = subprocess.run
        def bounded_run(*argv, **options):
            remaining = args.deadline_monotonic - time.monotonic()
            need(remaining > 0, 'TOTAL_PREPARATION1800_DEADLINE_EXCEEDED')
            requested = options.get('timeout')
            options['timeout'] = min(remaining, requested) if requested is not None else remaining
            return original_run(*argv, **options)
        subprocess.run = bounded_run
        try:
            print(json.dumps(prepare(args), sort_keys=True))
        finally:
            subprocess.run = original_run
    except Exception as error:
        # Exception text/tracebacks may include private subprocess payload or credentials.
        print(json.dumps({'status': 'APP_PREPARATION_FAILED_PREFIX_PRESERVED', 'error_class': type(error).__name__,
                          'error_code': str(error) if isinstance(error, ValueError) and re.fullmatch('[A-Z0-9_]+', str(error)) else 'DETAILS_WITHHELD',
                          'output': str(args.output), 'QA_executed': False}), file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
