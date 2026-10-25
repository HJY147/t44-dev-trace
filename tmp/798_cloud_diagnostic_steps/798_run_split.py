"""Run exact source935 S1/S2 inside separately scoped one-off containers."""

import hashlib
import json
import os
import socket
import subprocess
from pathlib import Path

ROOT = Path('/root/t44-r9')
PHASE = ROOT / 'campaign-935/p'
SOURCE = '935ab5b93bea788672c2b4a088c79cfeed848954'
BINDING = '770d774b715265ba517ea550aab5d001ecd8c04c58f3beb9cc558e752170ca06'
PYTHON_IMAGE = 't44-official-python:6a0e06f5ba0b373d051aabd3fffb9b873f27f9a2a3a14bcbe37dee6f0e3bbc70'
PYTHON_IDS = {'sha256:4f3baf081863a4580b5608699d9a7a8af2d89c3e87abbb60089b630b9102b2a1',
              'sha256:3c4d812a6efe003770aafbdba65f9c1960ba8234ab23a133934205a70bdcda77'}


def save(path, data, uid=None, mode=0o600):
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, mode)
    with os.fdopen(descriptor, 'wb') as stream:
        stream.write(data)
    if uid is not None:
        os.chown(path, uid, uid)


def main():
    assert os.geteuid() == 0 and socket.gethostname().split('.')[0] == 'i-bp13uag4r4u9r2hge0mt'
    assert hashlib.sha256((PHASE / 'binding.json').read_bytes()).hexdigest() == BINDING
    binding = json.loads((PHASE / 'binding.json').read_text())
    for name, digest in binding['file_hashes'].items():
        assert hashlib.sha256((PHASE / name).read_bytes()).hexdigest() == digest
    assert binding['source_sha'] == SOURCE and binding['database'] == 't44c_r9diag935_p'
    environment = {key: value for key, value in os.environ.items()
                   if not key.startswith(('MYSQL_', 'RABBITMQ_', 'COMPOSE_', 'T44_', 'DOCKER_'))
                   and key not in {'DATABASE_URL', 'AMQP_URL'}}
    docker = ['docker', '--context', 'default']
    subprocess.run(['systemctl', 'is-active', '--quiet', binding['timer_unit']],
                   check=True, timeout=15, env=environment)
    ca = PHASE / 'tls/ca.pem'
    assert hashlib.sha256(ca.read_bytes()).hexdigest() == binding['tls']['ca_sha256']
    image = subprocess.check_output(docker + ['image', 'inspect', '--format', '{{.Id}}', PYTHON_IMAGE],
                                    env=environment, timeout=15).decode().strip()
    assert image in PYTHON_IDS
    network = binding['project'] + '_edge'
    labels = json.loads(subprocess.check_output(docker + ['network', 'inspect', '--format', '{{json .Labels}}', network],
                                                env=environment, timeout=15))
    assert labels['com.docker.compose.project'] == binding['project']
    assert labels['com.docker.compose.network'] == 'edge'
    directory = ROOT / 'diag801-split-02'
    directory.mkdir(mode=0o700)
    for name in ('s1', 's2', 'inputs', 'receipts'):
        (directory / name).mkdir(mode=0o700)
    for name in ('s1', 's2'):
        os.chown(directory / name, 10001, 10001)
    original = json.loads((PHASE / 'fixture-bootstrap-01/accounts.private.json').read_text())
    accounts = {role: {'username': original[key]['username'], 'password': original[key]['password'],
                       'user_id': original[key]['id']}
                for key, role in (('m', 'manager'), ('d', 'developer'), ('r', 'reviewer'))}
    identities = {role: {key: value[key] for key in ('username', 'user_id')}
                  for role, value in accounts.items()}
    save(directory / 'inputs/identities.private.json', json.dumps(identities).encode(), 10001)
    save(directory / 'inputs/accounts.private.json', json.dumps(accounts).encode(), 10001)
    save(directory / 'inputs/ca.pem', ca.read_bytes(), 10001)

    def run(name, argv, status_path, accepted_images):
        try:
            result = subprocess.run(argv, capture_output=True, check=False, timeout=600, env=environment)
        except subprocess.TimeoutExpired as error:
            save(directory / ('receipts/' + name + '.stdout'), error.stdout or b'')
            save(directory / ('receipts/' + name + '.stderr'), error.stderr or b'')
            raw = subprocess.check_output(docker + ['inspect', '--format', '{{json .Image}}\t{{json .Config.Labels}}', name],
                                           env=environment, timeout=15).decode().strip()
            current_image, current_labels = [json.loads(part) for part in raw.split('\t')]
            assert current_image in accepted_images
            assert current_labels['io.t44.diag.owner'] == 'root-split-02'
            subprocess.run(docker + ['stop', '--time', '15', name], capture_output=True,
                           check=True, timeout=30, env=environment)
            raise RuntimeError('Owned one-off timed out; prefix retained') from None
        save(directory / ('receipts/' + name + '.stdout'), result.stdout)
        save(directory / ('receipts/' + name + '.stderr'), result.stderr)
        if status_path.is_file():
            for line in status_path.read_text().splitlines():
                row = json.loads(line)
                print(json.dumps({key: value for key, value in row.items() if key != 'results'}), flush=True)
        if result.returncode:
            raise RuntimeError('One-off preparation failed: ' + name)
        return [json.loads(line) for line in status_path.read_text().splitlines()]

    s1_name = 't44-diag801-s1-02'
    s1 = docker + ['compose', '--env-file', str(PHASE / 'application.env'), '--file', str(PHASE / 'compose.json'),
                  '--project-name', binding['project'], '--profile', 'operations', 'run', '--rm', '--no-deps', '-T',
                  '--name', s1_name, '--label', 'io.t44.diag.owner=root-split-02', '--entrypoint', 'python',
                  '--env', 'T44_DIAG_ALLOW=source935-development-only', '--env', 'T44_DIAG_PRODUCT_SHA=' + SOURCE,
                  '--volume', str(ROOT / 'tools801-s1-02') + ':/opt/diag801:ro',
                  '--volume', str(directory / 'inputs/identities.private.json') + ':/run/identities.json:ro',
                  '--volume', str(directory / 's1') + ':/diag-output',
                  'admin', '-B', '/opt/diag801/801_stage1.py', '--identities', '/run/identities.json',
                  '--output-dir', '/diag-output/candidate-01', '--host', 'mysql', '--port', '3306',
                  '--user', binding['database'] + '_app', '--slots', '400']
    s1_rows = run(s1_name, s1, directory / 's1/candidate-01/status.public.jsonl',
                  {binding['image_ids']['backend'], binding['config_ids']['backend']})
    final = s1_rows[-1]
    assert final['kind'] == 'stage1-complete-not-acceptance' and final['diagnostic_valid'] is True
    candidate = directory / 's1/candidate-01/candidate.private.json'
    assert hashlib.sha256(candidate.read_bytes()).hexdigest() == final['candidate_sha256']
    s2_name = 't44-diag801-s2-02'
    s2 = docker + ['run', '--rm', '--name', s2_name, '--label', 'io.t44.diag.owner=root-split-02',
                  '--network', network, '--read-only', '--user', '10001:10001', '--cap-drop', 'ALL',
                  '--security-opt', 'no-new-privileges:true', '--pids-limit', '1024', '--memory', '2g',
                  '--volume', str(ROOT / 'tools801-s2-02') + ':/opt/diag801:ro',
                  '--volume', str(directory / 'inputs/accounts.private.json') + ':/run/accounts.json:ro',
                  '--volume', str(candidate) + ':/run/candidate.json:ro',
                  '--volume', str(directory / 'inputs/ca.pem') + ':/run/ca.pem:ro',
                  '--volume', str(directory / 's2') + ':/diag-output',
                  PYTHON_IMAGE, 'python', '-B', '/opt/diag801/801_stage2.py', '--accounts', '/run/accounts.json',
                  '--candidate', '/run/candidate.json', '--candidate-sha256', final['candidate_sha256'],
                  '--ca', '/run/ca.pem', '--ca-sha256', binding['tls']['ca_sha256'],
                  '--url', 'https://172.21.182.245:18445', '--output-dir', '/diag-output/session-01']
    rows = run(s2_name, s2, directory / 's2/session-01/status.public.jsonl', PYTHON_IDS)
    assert rows[-1]['diagnostic_valid'] is True
    baseline = docker + ['run', '--rm', '--name', 't44-diag801-baseline-02',
                         '--label', 'io.t44.diag.owner=root-split-02', '--network', network,
                         '--read-only', '--user', '10001:10001', '--cap-drop', 'ALL',
                         '--security-opt', 'no-new-privileges:true', '--pids-limit', '1024', '--memory', '2g',
                         '--volume', str(ROOT / 'tools801-s2-02') + ':/opt/diag801:ro',
                         '--volume', str(directory / 's2/session-01/session.private.json') + ':/run/session.json:ro',
                         '--volume', str(directory / 'inputs/ca.pem') + ':/run/ca.pem:ro',
                         '--volume', str(directory / 's2') + ':/diag-output',
                         PYTHON_IMAGE, 'python', '-B', '/opt/diag801/801_http.py',
                         '--packet', '/run/session.json', '--ca', '/run/ca.pem',
                         '--output', '/diag-output/baseline-01.public.jsonl',
                         '--updated-packet', '/diag-output/session-after-baseline.private.json',
                         '--clients', '1', '--cycles', '20', '--seconds', '45']
    baseline_rows = run('t44-diag801-baseline-02', baseline, directory / 's2/baseline-01.public.jsonl', PYTHON_IDS)
    assert baseline_rows[0]['failed_clients'] == 0
    assert json.loads((directory / 's2/session-after-baseline.private.json').read_text())['resumable'] is True
    print(json.dumps({'kind': 'split-development-fixture-complete', 'formal_acceptance': False,
                      'private_packet_path': str(directory / 's2/session-after-baseline.private.json'),
                      'password_or_session_printed': False}))


if __name__ == '__main__':
    os.umask(0o077)
    try:
        main()
    except (OSError, ValueError, RuntimeError, KeyError, TypeError, AssertionError,
            subprocess.SubprocessError) as error:
        print(json.dumps({'success': False, 'stage': 'split-diag801', 'error_class': type(error).__name__,
                          'partial_state_preserved': True}), flush=True)
        raise SystemExit(1) from None
