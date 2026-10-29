"""Root-only new diagnostic fixture orchestration; secrets never leave explicit private files."""

import hashlib
import json
import os
import socket
import subprocess
from pathlib import Path

PHASE = Path('/root/t44-r9/campaign-935/p')
ROOT = Path('/root/t44-r9')
BINDING = '770d774b715265ba517ea550aab5d001ecd8c04c58f3beb9cc558e752170ca06'
SOURCE = '935ab5b93bea788672c2b4a088c79cfeed848954'
TOOLS = ROOT / 'tools801-01'


def save(path, data, owner=None):
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, 'wb') as stream:
        stream.write(data)
    if owner is not None:
        os.chown(path, owner, owner)


def main():
    assert os.geteuid() == 0 and socket.gethostname().split('.')[0] == 'i-bp13uag4r4u9r2hge0mt'
    assert PHASE.resolve() == PHASE
    assert hashlib.sha256((PHASE / 'binding.json').read_bytes()).hexdigest() == BINDING
    binding = json.loads((PHASE / 'binding.json').read_text())
    assert binding['source_sha'] == SOURCE and binding['database'] == 't44c_r9diag935_p'
    for name, digest in binding['file_hashes'].items():
        assert hashlib.sha256((PHASE / name).read_bytes()).hexdigest() == digest
    ca = PHASE / 'tls/ca.pem'
    assert hashlib.sha256(ca.read_bytes()).hexdigest() == binding['tls']['ca_sha256']
    environment = {key: value for key, value in os.environ.items()
                   if not key.startswith(('MYSQL_', 'RABBITMQ_', 'COMPOSE_', 'T44_', 'DOCKER_'))
                   and key not in {'DATABASE_URL', 'AMQP_URL'}}
    subprocess.run(['systemctl', 'is-active', '--quiet', binding['timer_unit']],
                   check=True, timeout=15, env=environment)
    inputs, outputs, receipts = (ROOT / name for name in
                                ('diag801-input-01', 'diag801-output-01', 'diag801-receipts-01'))
    for directory in (inputs, outputs, receipts):
        directory.mkdir(mode=0o700)
    os.chown(outputs, 10001, 10001)
    original = json.loads((PHASE / 'fixture-bootstrap-01/accounts.private.json').read_text())
    accounts = {role: {'username': original[key]['username'], 'password': original[key]['password'],
                       'user_id': original[key]['id']}
                for key, role in (('m', 'manager'), ('d', 'developer'), ('r', 'reviewer'))}
    save(inputs / 'accounts.private.json', json.dumps(accounts).encode(), 10001)
    save(inputs / 'ca.pem', ca.read_bytes(), 10001)
    command = ['docker', '--context', 'default', 'compose', '--env-file', str(PHASE / 'application.env'),
               '--file', str(PHASE / 'compose.json'), '--project-name', binding['project'],
               '--profile', 'operations', 'run', '--rm', '--no-deps', '-T', '--entrypoint', 'python',
               '--env', 'T44_DIAG_ALLOW=source935-development-only', '--env', 'T44_DIAG_PRODUCT_SHA=' + SOURCE,
               '--volume', str(TOOLS) + ':/opt/diag801:ro',
               '--volume', str(inputs / 'accounts.private.json') + ':/run/diag801-accounts.json:ro',
               '--volume', str(inputs / 'ca.pem') + ':/run/diag801-ca.pem:ro',
               '--volume', str(outputs) + ':/diagnostic',
               'admin', '/opt/diag801/801_prepare.py', '--accounts', '/run/diag801-accounts.json',
               '--url', 'https://172.21.182.245:18445', '--ca', '/run/diag801-ca.pem',
               '--host', 'mysql', '--port', '3306', '--user', binding['database'] + '_app', '--slots', '400']

    def run(label, arguments):
        name = 't44-diag801-' + label
        index = command.index('admin')
        argv = command[:index] + ['--name', name] + command[index:] + arguments
        try:
            result = subprocess.run(argv, capture_output=True, check=False,
                                    timeout=600, env=environment)
        except subprocess.TimeoutExpired as error:
            save(receipts / (label + '.stdout'), error.stdout or b'')
            save(receipts / (label + '.stderr'), error.stderr or b'')
            inspect = subprocess.run(['docker', '--context', 'default', 'inspect', '--format',
                                      '{{json .Image}}\t{{json .Config.Labels}}', name],
                                     capture_output=True, check=True, timeout=15, env=environment)
            image, labels = [json.loads(part) for part in inspect.stdout.decode().strip().split('\t')]
            assert image in {binding['image_ids']['backend'], binding['config_ids']['backend']}
            assert labels['com.docker.compose.project'] == binding['project']
            assert labels['com.docker.compose.service'] == 'admin'
            subprocess.run(['docker', '--context', 'default', 'stop', '--time', '15', name],
                           check=True, capture_output=True, timeout=30, env=environment)
            raise RuntimeError('Owned fixture timed out; raw prefix preserved') from None
        save(receipts / (label + '.stdout'), result.stdout)
        save(receipts / (label + '.stderr'), result.stderr)
        public = outputs / label / 'status.public.jsonl'
        if public.is_file():
            print(public.read_text(), end='', flush=True)
        if result.returncode:
            raise RuntimeError('Explicit fresh fixture operation failed: ' + label)

    run('inspection-01', ['--output-dir', '/diagnostic/inspection-01', '--inspect-only'])
    rows = [json.loads(line) for line in (outputs / 'inspection-01/status.public.jsonl').read_text().splitlines()]
    profiles = [row for row in rows if row['kind'] == 'actual-readonly-candidate-profile']
    assert len(profiles) == 1 and profiles[0]['sufficient_observed'] is True
    run('prepare-01', ['--output-dir', '/diagnostic/prepare-01'])
    print(json.dumps({'kind': 'root-development-fixture-ready', 'source': SOURCE,
                      'private_packet_path': str(outputs / 'prepare-01/session.private.json'),
                      'password_or_session_printed': False, 'formal_acceptance': False}))


if __name__ == '__main__':
    os.umask(0o077)
    try:
        main()
    except (OSError, ValueError, RuntimeError, KeyError, TypeError, AssertionError,
            subprocess.SubprocessError) as error:
        print(json.dumps({'success': False, 'stage': 'fresh-diag801', 'error_class': type(error).__name__,
                          'partial_state_preserved': True}), flush=True)
        raise SystemExit(1) from None
