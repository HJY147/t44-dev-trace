"""Run sequential short diagnostic cohorts on the existing load VM; never formal acceptance."""

import hashlib
import json
import os
import socket
import subprocess
from pathlib import Path

ROOT = Path('/root/t44-r9/diag801-load-01')
IMAGE = 't44-official-python:6a0e06f5ba0b373d051aabd3fffb9b873f27f9a2a3a14bcbe37dee6f0e3bbc70'
IMAGE_IDS = {'sha256:4f3baf081863a4580b5608699d9a7a8af2d89c3e87abbb60089b630b9102b2a1',
             'sha256:3c4d812a6efe003770aafbdba65f9c1960ba8234ab23a133934205a70bdcda77'}


def write(path, value, uid=None):
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, 'wb') as stream:
        stream.write(value)
    if uid is not None:
        os.chown(path, uid, uid)


def main():
    assert os.geteuid() == 0 and socket.gethostname().split('.')[0] == 'i-bp13uag4r4u9r2hge0mu'
    docker = ['docker', '--context', 'default']
    environment = {key: value for key, value in os.environ.items()
                   if not key.startswith(('DOCKER_', 'COMPOSE_', 'T44_', 'MYSQL_', 'RABBITMQ_'))
                   and key not in {'DATABASE_URL', 'AMQP_URL'}}
    actual = subprocess.check_output(docker + ['image', 'inspect', '--format', '{{.Id}}', IMAGE],
                                     env=environment, timeout=15).decode().strip()
    assert actual in IMAGE_IDS
    assert hashlib.sha256((ROOT / 'code/801_http.py').read_bytes()).hexdigest() == 'ef065f56e74e8bb1b6c8289bfe5618cbfe3b130e95dcdfea54e4483b109971d3'
    assert hashlib.sha256((ROOT / 'inputs/ca.pem').read_bytes()).hexdigest() == '21dad4bde10be0359101ce1df77d243ee30c1e123ef74cdc94c2229d88fdbbba'
    runs = ROOT / 'runs'
    runs.mkdir(mode=0o700)
    previous = ROOT / 'inputs/session.private.json'
    for clients in (20, 40, 400):
        directory = runs / ('c' + str(clients))
        directory.mkdir(mode=0o700)
        os.chown(directory, 10001, 10001)
        name = 't44-diag801-load-c' + str(clients)
        argv = docker + ['run', '--rm', '--name', name, '--label', 'io.t44.diag.owner=root-load-matrix-01',
                         '--network', 'bridge', '--read-only', '--user', '10001:10001', '--cap-drop', 'ALL',
                         '--security-opt', 'no-new-privileges:true', '--pids-limit', '1024', '--memory', '4g',
                         '--volume', str(ROOT / 'code') + ':/opt/diag801:ro',
                         '--volume', str(previous) + ':/run/session.json:ro',
                         '--volume', str(ROOT / 'inputs/ca.pem') + ':/run/ca.pem:ro',
                         '--volume', str(directory) + ':/diagnostic',
                         IMAGE, 'python', '-B', '/opt/diag801/801_http.py',
                         '--packet', '/run/session.json', '--ca', '/run/ca.pem',
                         '--output', '/diagnostic/result.public.jsonl',
                         '--updated-packet', '/diagnostic/session.private.json',
                         '--clients', str(clients), '--cycles', '5', '--seconds', '90']
        try:
            result = subprocess.run(argv, capture_output=True, check=False, timeout=180, env=environment)
        except subprocess.TimeoutExpired as error:
            write(ROOT / (name + '.stdout'), error.stdout or b'')
            write(ROOT / (name + '.stderr'), error.stderr or b'')
            identity = subprocess.check_output(docker + ['inspect', '--format', '{{json .Image}}\t{{json .Config.Labels}}', name],
                                               env=environment, timeout=15).decode().strip()
            image, labels = [json.loads(part) for part in identity.split('\t')]
            assert image in IMAGE_IDS and labels['io.t44.diag.owner'] == 'root-load-matrix-01'
            subprocess.run(docker + ['stop', '--time', '15', name], capture_output=True,
                           check=True, timeout=30, env=environment)
            raise RuntimeError('Owned diagnostic client timed out; raw prefix preserved') from None
        write(ROOT / (name + '.stdout'), result.stdout)
        write(ROOT / (name + '.stderr'), result.stderr)
        output = directory / 'result.public.jsonl'
        if output.is_file():
            for line in output.read_text().splitlines():
                row = json.loads(line)
                print(json.dumps({key: value for key, value in row.items() if key != 'results'}), flush=True)
        if result.returncode:
            raise RuntimeError('Diagnostic cohort failed; no retry or next cohort')
        previous = directory / 'session.private.json'
        assert json.loads(previous.read_text())['resumable'] is True
    print(json.dumps({'kind': 'developer-matrix-complete', 'formal_acceptance': False,
                      'cohorts': [20, 40, 400], 'cycles_limit': 5, 'seconds_limit_each': 90}), flush=True)


if __name__ == '__main__':
    os.umask(0o077)
    try:
        main()
    except (OSError, ValueError, RuntimeError, KeyError, TypeError, AssertionError,
            subprocess.SubprocessError) as error:
        print(json.dumps({'success': False, 'stage': 'load-development-matrix',
                          'error_class': type(error).__name__, 'partial_state_preserved': True}), flush=True)
        raise SystemExit(1) from None
