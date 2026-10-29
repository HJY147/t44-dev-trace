"""Root's bounded orchestration of reviewed neutral producers; no tester source access."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone

ROOT = Path('/root/t44-r30/r30window01')
SOURCE = '0bffe0c535e5897890aebf30879fdd3839dc52d6'
CODE_SHA = '66ab164258803a8a62edfc3dbc713837431ce8b649664ab8de4c5a48a2359606'
S = '2026-10-29T10:20:00Z'
E = '2026-10-29T10:33:00Z'
G = '2026-10-29T10:35:00Z'
C = '2026-10-29T10:40:00Z'
CUTOFF = '2026-10-29T10:17:30Z'
PYTHON = 'sha256:4f3baf081863a4580b5608699d9a7a8af2d89c3e87abbb60089b630b9102b2a1'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def now():
    return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')


def wait_until(value):
    """Schedule first collection/assembly; never edit an existing packet or clock."""
    target = datetime.fromisoformat(value.replace('Z', '+00:00')).timestamp()
    while target > time.time():
        time.sleep(max(0, min(1, target - time.time())))


def save(path, value, uid=None):
    with path.open('x') as stream:
        json.dump(value, stream, sort_keys=True)
        stream.write('\n')
    path.chmod(0o600)
    if uid is not None:
        os.chown(path, uid, uid)
    return path


class Run:
    def __init__(self, args):
        if os.geteuid() != 0 or not args.root_actual_chain_reviewed:
            raise ValueError('ROOT_REVIEWED_ACTUAL_IMPORT_REQUIRED')
        self.args = args
        self.out = ROOT / 'materials-01'
        self.out.mkdir(mode=0o700)
        self.ops = ROOT / 'ops'
        self.code = self.ops / 'producer'
        self.profile = self.ops / 'profile'
        self.phase = args.phase
        self.binding = json.loads((self.phase / 'binding.json').read_bytes())
        self.bind_sha = sha(self.phase / 'binding.json')
        if self.binding['source_sha'] != SOURCE or self.binding['project'] != 't44-cloud-r30window01-p' or self.binding['stop_utc'] != G:
            raise ValueError('EXACT_NEW_PHASE_REQUIRED')
        if sha(self.code / 'code-manifest.PUBLIC.json') != CODE_SHA:
            raise ValueError('FINAL_PRODUCER_MANIFEST_REQUIRED')
        manifest = json.loads((self.code / 'code-manifest.PUBLIC.json').read_bytes())
        for name, expected in manifest['files'].items():
            path = self.code / name
            if path.is_symlink() or not path.is_file() or sha(path) != expected or path.stat().st_size != manifest['file_sizes'][name]:
                raise ValueError('FROZEN_PUBLIC_PRODUCER_BYTES_REQUIRED')
            path.chmod(0o644)
        self.code.chmod(0o755)
        (self.code / 'code-manifest.PUBLIC.json').chmod(0o644)
        self.import_path = args.import_receipt
        self.load = json.loads(args.load_readiness.read_bytes())
        if not (self.load['role'] == 'orchestration-readiness' and self.load['running_observed'] is True and self.load['is_actual_driver'] is False and self.load['core_imported'] is False and self.load['SUT_requests'] == 0 and self.load['image_config'] == PYTHON):
            raise ValueError('ACTUAL_LOAD_STANDBY_RECEIPT_REQUIRED')
        self.index = 0

    def command(self, label, argv, timeout=180):
        remaining = (datetime.fromisoformat(CUTOFF.replace('Z', '+00:00')) - datetime.now(timezone.utc)).total_seconds()
        if remaining <= 5:
            raise ValueError('FIXED_PACKET_CUTOFF_REACHED')
        self.index += 1
        prefix = self.out / (f'{self.index:02d}-' + label)
        with Path(str(prefix) + '.stdout.private').open('xb') as stdout, Path(str(prefix) + '.stderr.private').open('xb') as stderr:
            result = subprocess.run([str(x) for x in argv], stdout=stdout, stderr=stderr, timeout=min(timeout, remaining - 2), check=False)
        save(Path(str(prefix) + '.PUBLIC.json'), {'label': label, 'exit_code': result.returncode, 'completed_at': now()})
        if result.returncode:
            raise ValueError('STEP_FAILED_PREFIX_PRESERVED:' + label)

    def roles(self, label, scheduler=False):
        raw = subprocess.check_output(['docker', 'ps', '--no-trunc', '--filter', 'label=com.docker.compose.project=' + self.binding['project'], '--format', '{{json .}}'], timeout=15)
        rows = [json.loads(line) for line in raw.splitlines()]
        observed = {}
        for row in rows:
            details = json.loads(subprocess.check_output(['docker', 'inspect', '--format', '{{json .State}}', row['ID']], timeout=10))
            labels = json.loads(subprocess.check_output(['docker', 'inspect', '--format', '{{json .Config.Labels}}', row['ID']], timeout=10))
            service = labels['com.docker.compose.service']
            if details['Running'] and not details.get('Restarting'):
                observed[service] = {'id': row['ID'], 'state': details, 'project': labels['com.docker.compose.project']}
        required = {'mysql', 'rabbitmq', 'api', 'consumer', 'web', 'tls-gateway'} | ({'scheduler'} if scheduler else set())
        if not required <= set(observed):
            raise ValueError('ACTUAL_APP_ROLES_NOT_RUNNING')
        if scheduler and set(observed) != required:
            raise ValueError('UNEXPECTED_NAMESPACE_SERVICE_PRESERVE_AND_STOP')
        path = save(self.out / (label + '.PUBLIC.json'), {'utc': now(), 'observed': observed, 'required': sorted(required), 'other_persistent_services': sorted(set(observed) - required)})
        roles = {('rabbit' if key == 'rabbitmq' else key): {'required': True, 'running_observed': True, 'receipt_sha256': sha(path)} for key in required}
        roles['scheduler'] = roles.get('scheduler', {'required': True, 'running_observed': False, 'receipt_sha256': None})
        roles['load'] = {'required': True, 'running_observed': True, 'receipt_sha256': sha(self.args.load_readiness)}
        return roles, path

    def wrapper(self, mode, plan, intent, label, accounts=None):
        args = ['python3', self.ops / 'r30-neutral-admin.py', mode, '--phase-dir', self.phase, '--binding-sha256', self.bind_sha,
                '--profile-json', self.profile / 'profile.json', '--profile-sha256', sha(self.profile / 'profile.json'),
                '--code-dir', self.code, '--code-manifest', self.code / 'code-manifest.PUBLIC.json', '--code-manifest-sha256', CODE_SHA,
                '--plan', plan, '--intent', intent, '--import-receipt', self.import_path,
                '--budget-receipt', self.args.probe, '--budget-receipt-sha256', sha(self.args.probe), '--output-dir', self.out / label]
        if accounts:
            args += ['--accounts', accounts]
        self.command(label, args)
        return self.out / label / 'output'

    def intent(self, plan, operation, label, empty=False):
        return save(self.out / (label + '.intent.json'), {'run_id': plan['run_id'], 'namespace': plan['namespace'], 'database': plan['target']['database'], 'binding_sha256': self.bind_sha, 'operation': operation, 'project_ids': plan['authorized_project_ids'], 'purpose': 'material_preparation', 'empty_scope_observed': empty})

    def container(self, label, paths, script, options, image, network='none', timeout=180):
        inputs = self.out / (label + '-inputs')
        outputs = self.out / (label + '-output')
        inputs.mkdir(mode=0o700); outputs.mkdir(mode=0o700)
        for name, source in paths.items():
            shutil.copyfile(source, inputs / name)
            (inputs / name).chmod(0o600); os.chown(inputs / name, 10001, 10001)
        for path in (inputs, outputs):
            os.chown(path, 10001, 10001)
        name = self.binding['project'] + '-neutral-' + label
        argv = ['docker', 'run', '--rm', '--pull=never', '--restart=no', '--name', name, '--network', network, '--user', '10001:10001', '--cpus', '2', '--memory', '1g', '--pids-limit', '128', '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges', '--read-only', '--tmpfs', '/tmp:rw,nosuid,nodev,size=32m', '-v', str(self.code) + ':/neutral-code:ro', '-v', str(inputs) + ':/neutral-input:ro', '-v', str(outputs) + ':/neutral-output', '--entrypoint', 'python', image, '-B', '/neutral-code/' + script, *options]
        try:
            self.command(label, argv, timeout)
        except subprocess.TimeoutExpired:
            # Fixed new name belongs only to this orchestration, never reuse it.
            subprocess.run(['docker', 'stop', '--time', '3', name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=15, check=False)
            raise
        return outputs

    def main(self):
        roles, observed = self.roles('before-seed')
        plan = json.loads((self.code / 'plan.template.PUBLIC.json').read_bytes())
        ready_at = now()
        plan.update(status='ACTUAL_ROOT_ADMITTED_MATERIAL_PREPARATION', root_admit_preparation=True, run_id='r30window01', namespace=self.binding['project'], runtime_roles=roles, allowed_writes=['init-user', 'seed_demo'], service_name=self.binding['project'] + '-materials')
        plan['source'].update(actual_loaded_receipt_sha256=sha(self.import_path), actual_loaded_receipt_path=str(self.import_path), actual_loaded_observed_at=datetime.fromtimestamp(self.import_path.stat().st_mtime, timezone.utc).isoformat().replace('+00:00', 'Z'), actual_loaded_full_chain_reviewed_by_root=True)
        plan['target'].update(compose_project=self.binding['project'], database=self.binding['database'], mysql_user=self.binding['database'] + '_app', binding_sha256=self.bind_sha, origin='https://' + self.binding['app_private_ip'] + ':' + str(self.binding['tls_port']), connect_ip=self.binding['app_private_ip'], ca_sha256=sha(self.phase / 'tls/ca.pem'))
        plan['window'] = {'start_utc': S, 'end_utc': E, 'stop_utc': G}
        plan['seed'].update(seed=20261029, anchor_utc=ready_at)
        plan['gen_binding'] = {'path': '/neutral-input/binding.json', 'sha256': self.bind_sha, 'original_host_path': str(self.phase / 'binding.json')}
        plan['lifecycle'] = {'t0_utc': '2026-10-29T10:00:00Z', 'cost_stop_utc': C, 'packet_cutoff_utc': CUTOFF}
        plan['budget']['actual_admission_receipt_sha256'] = sha(self.args.probe)
        for key, path in [('source', self.import_path), ('images', self.import_path), ('transfer', self.args.load_readiness), ('preflight', observed)]:
            plan['readiness'][key] = {'sha256': sha(path), 'completed_at': ready_at}
        plan['readiness'].update(all_ready_at=ready_at, admin_preserves_image_pythonpath=True)
        seed_plan = save(self.out / 'seed-plan.json', plan)
        first = self.wrapper('counts', seed_plan, self.intent(plan, 'read', 'empty-count'), 'empty-count')
        counts = json.loads((first / 'result/counts.json').read_bytes())
        if any(counts['actual_fixture_counts'].values()):
            raise ValueError('ACTUAL_DATABASE_NOT_EMPTY')
        accounts = save(self.out / 'accounts-input.private.json', {r: {'username': 'synthetic-' + r, 'password': None, 'user_id': None} for r in ('manager', 'developer', 'reviewer')})
        initialized = self.wrapper('init-accounts', seed_plan, self.intent(plan, 'init-user', 'init'), 'init', accounts)
        self.wrapper('seed', seed_plan, self.intent(plan, 'seed_demo', 'seed', True), 'seed')
        baseline = self.wrapper('counts', seed_plan, self.intent(plan, 'read', 'baseline'), 'baseline')
        scoped = self.container('scope', {'seed-plan.json': seed_plan, 'counts.json': baseline / 'result/counts.json'}, 'stage_scope.py', ['--seed-plan', '/neutral-input/seed-plan.json', '--counts', '/neutral-input/counts.json', '--output', '/neutral-output/material-plan.json', *[v for op in ('login', 'service-token', 'createTask', 'transitionTask', 'createEscalation') for v in ('--allow-write', op)]], PYTHON)
        material_path = self.out / 'material-plan.json'
        with material_path.open('xb') as stream:
            stream.write((scoped / 'material-plan.json').read_bytes())
        material_path.chmod(0o600)
        material = json.loads(material_path.read_bytes())
        service = self.wrapper('service', material_path, self.intent(material, 'service-token', 'service'), 'service')
        original = service / 'result/original-service.json'
        target = self.phase / 'scheduler-secrets/scheduler-token.json'
        with target.open('xb') as stream:
            stream.write(original.read_bytes())
        target.chmod(0o600); os.chown(target, 10001, 10001)
        self.command('scheduler-start', ['python3', self.profile / 'generation.py', 'scheduler-start', '--phase-dir', self.phase, '--binding-sha256', self.bind_sha, '--budget-receipt', self.args.probe, '--budget-receipt-sha256', sha(self.args.probe)])
        material['runtime_roles'], _ = self.roles('before-human-sessions', True)
        material_path = save(self.out / 'material-plan-scheduler.json', material)
        common = {'plan.json': material_path, 'binding.json': self.phase / 'binding.json', 'backend-import-receipt.json': self.import_path, 'ca.pem': self.phase / 'tls/ca.pem'}
        wait_until('2026-10-29T10:12:30Z')
        http = self.container('http', {**common, 'accounts.json': initialized / 'accounts.initialized.private.json', 'service.json': service / 'result/service.json'}, 'prepare_http.py', ['--plan', '/neutral-input/plan.json', '--binding', '/neutral-input/binding.json', '--import-receipt', '/neutral-input/backend-import-receipt.json', '--ca', '/neutral-input/ca.pem', '--accounts', '/neutral-input/accounts.json', '--service', '/neutral-input/service.json', '--output', '/neutral-output/http', '--root-admit-http-preparation'], PYTHON, self.binding['project'] + '_edge', 330)
        final_counts = self.wrapper('counts', material_path, self.intent(material, 'read', 'final-count'), 'final-count')
        wait_until('2026-10-29T10:15:30Z')
        material['runtime_roles'], writer_proof = self.roles('after-api-current-writers', True)
        material['readiness']['fixture_ready_at'] = now()
        final_plan = save(self.out / 'final-plan.json', material)
        exclusive = save(self.out / 'exclusive.PUBLIC.json', {'run_id': material['run_id'], 'namespace': material['namespace'], 'database': material['target']['database'], 'binding_sha256': self.bind_sha, 'observed_at': now(), 'other_workload_writer_absent': True, 'scheduler_running': True, 'consumer_running': True, 'all_notifications_precreated': False, 'writer_observation_path': str(writer_proof), 'writer_observation_sha256': sha(writer_proof), 'basis': 'new isolated namespace, root exclusive new credentials, only this material controller and observed persistent roles; no benchmark grant issued'})
        backend = self.binding['images']['backend']['alias']
        evidence = self.container('evidence', {**common, 'plan.json': final_plan, 'facts.json': http / 'http/factual-snapshots.json', 'counts.json': final_counts / 'result/counts.json', 'exclusive.json': exclusive}, 'make_evidence.py', ['--plan', '/neutral-input/plan.json', '--facts', '/neutral-input/facts.json', '--counts', '/neutral-input/counts.json', '--exclusive-proof', '/neutral-input/exclusive.json', '--output', '/neutral-output/evidence.json'], backend)
        assembled = self.container('assemble', {**common, 'plan.json': final_plan, 'evidence.json': evidence / 'evidence.json', 'sessions.json': http / 'http/sessions.json', 'counts.json': final_counts / 'result/counts.json'}, 'assemble.py', ['--plan', '/neutral-input/plan.json', '--evidence', '/neutral-input/evidence.json', '--sessions', '/neutral-input/sessions.json', '--counts', '/neutral-input/counts.json', '--ca', '/neutral-input/ca.pem', '--source-manifest', '/neutral-code/source-manifest.json', '--bundle-manifest', '/neutral-code/backend-bundle-manifest.json', '--import-receipt', '/neutral-input/backend-import-receipt.json', '--output', '/neutral-output/new-packet', '--root-admit-new-packet'], backend)
        result = {'status': 'ACTUAL_NEUTRAL_PACKET_CREATED_NOT_BENCHMARK', 'packet_dir': str(assembled / 'new-packet'), 'source_sha': SOURCE, 'created_at': now(), 'grant_allow': False}
        save(self.out / 'complete.PUBLIC.json', result)
        print(json.dumps(result))


if __name__ == '__main__':
    os.umask(0o077)
    parser = argparse.ArgumentParser()
    for name in ('phase', 'probe', 'import-receipt', 'load-readiness'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--root-actual-chain-reviewed', action='store_true')
    arguments = parser.parse_args()
    try:
        Run(arguments).main()
    except Exception as error:
        print(json.dumps({'status': 'MATERIAL_PREPARATION_FAILED_PREFIX_PRESERVED', 'error_type': type(error).__name__, 'benchmark_started': False}), file=sys.stderr)
        raise
