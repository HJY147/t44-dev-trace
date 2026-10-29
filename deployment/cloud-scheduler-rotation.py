"""One reviewed exact-C scheduler lifecycle stage; never print or export tokens."""

import argparse
import hashlib
import json
import os
import runpy
import subprocess
import sys
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path('/opt/t44-c-0dfb55c')
RUNTIME = Path('/run/t44-delivery/tls-C')
HELPER = Path('/run/t44-delivery/tls-delivery-extended.py')
HELPER_SHA = 'ea1b5873efb359e2e4e4adb8f020bfeab3da8f20e7661ae7bb7a5d883ac121d9'
SOURCE = '0dfb55c2191200d947c5423fd9ee74bb0812cc5a'
STOPPED = RUNTIME / 'reviewed-scheduler-stopped.json'
ROTATED = RUNTIME / 'reviewed-scheduler-rotation-success.json'


def save(path, raw):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())


def main():
    os.umask(0o077)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=['stop', 'rotate', 'start'])
    args = parser.parse_args()
    stage = args.stage
    receipt = {'stage': stage, 'actual_exit_code': None, 'state_requires_observation': True}
    try:
        if os.geteuid() != 0 or HELPER.is_symlink() or hashlib.sha256(HELPER.read_bytes()).hexdigest() != HELPER_SHA:
            raise ValueError('ROOT_OR_HELPER_REJECTED')
        tls = runpy.run_path(str(HELPER))
        values = tls['check_source'](ROOT)
        if values['MYSQL_DATABASE'] != 't44':
            raise ValueError('DATABASE_REJECTED')
        tls['validate_runtime'](RUNTIME, tls['private_ip'](Path('/run/t44-delivery/private-network.env')))
        if time.time() + 300 >= datetime(2026, 10, 24, 10, 28, tzinfo=UTC).timestamp():
            raise ValueError('WINDOW_REJECTED')
        env = {k: v for k, v in os.environ.items() if not k.startswith(('DOCKER_', 'COMPOSE_')) and k not in values}
        env.update(values)
        base = ['docker', '--context', 'default', 'compose', '--project-name', values['COMPOSE_PROJECT_NAME'],
                '--env-file', str(ROOT / '.env'), '-f', str(ROOT / 'compose.yaml'), '-f', str(RUNTIME / 'overlay.json')]

        def run(arguments, cap):
            return subprocess.run([*base, *arguments], env=env, capture_output=True, check=True, timeout=cap)

        def stopped():
            return 'scheduler' not in run(['ps', '--services', '--status', 'running'], 10).stdout.decode().splitlines()

        if stage == 'stop':
            if STOPPED.exists() or ROTATED.exists():
                raise ValueError('ATTEMPT_ALREADY_EXISTS')
            action = ['stop', '--timeout', '30', 'scheduler']
        elif stage == 'rotate':
            marker = json.loads(tls['private_file'](STOPPED))
            if marker != {'source': SOURCE, 'scheduler_stopped': True} or ROTATED.exists() or not stopped():
                raise ValueError('STOPPED_STATE_REQUIRED')
            action = ['--profile', 'operations', 'run', '--rm', '-T', '--pull', 'never', '--no-deps',
                      '-e', 'T44_SESSION_TTL_SECONDS=5400', 'credential-admin', '--name', 'scheduler',
                      *[v for p in range(1, 41) for v in ('--project-id', str(p))], '--rotate']
        else:
            marker = json.loads(tls['private_file'](ROTATED))
            if marker['source'] != SOURCE or marker['project_ids'] != list(range(1, 41)) or not stopped():
                raise ValueError('CONFIRMED_ROTATION_REQUIRED')
            if datetime.fromisoformat(marker['expires_at'].replace('Z', '+00:00')) <= datetime(2026, 10, 24, 10, 10, tzinfo=UTC):
                raise ValueError('EXPIRY_TOO_EARLY')
            action = ['up', '-d', '--no-deps', '--no-build', '--pull', 'never', '--wait', '--wait-timeout', '120', 'scheduler']
        stem = RUNTIME / ('scheduler-' + stage + '-' + uuid.uuid4().hex)
        try:
            result = run(action, 150)
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
            save(Path(str(stem) + '.stdout'), exc.stdout or b'')
            save(Path(str(stem) + '.stderr'), exc.stderr or b'')
            raise
        save(Path(str(stem) + '.stdout'), result.stdout)
        save(Path(str(stem) + '.stderr'), result.stderr)
        if stage == 'stop':
            if not stopped():
                raise ValueError('STOP_NOT_CONFIRMED')
            save(STOPPED, json.dumps({'source': SOURCE, 'scheduler_stopped': True}).encode())
        elif stage == 'rotate':
            item = json.loads(result.stdout)
            expected = {'session_id', 'expires_at', 'credential_written', 'rotated',
                        'previous_session_revoked', 'previous_session_already_inactive'}
            if (not isinstance(item, dict) or set(item) != expected or type(item['session_id']) is not int
                    or item['session_id'] <= 0 or item['credential_written'] is not True or item['rotated'] is not True
                    or not (item['previous_session_revoked'] is True or item['previous_session_already_inactive'] is True)
                    or datetime.fromisoformat(item['expires_at'].replace('Z', '+00:00')) <= datetime(2026, 10, 24, 10, 10, tzinfo=UTC)):
                raise ValueError('ROTATION_NOT_CONFIRMED')
            save(ROTATED, json.dumps({'source': SOURCE, 'project_ids': list(range(1, 41)), **item}).encode())
            receipt.update(session_id=item['session_id'], expires_at=item['expires_at'],
                           previous_session_revoked=item['previous_session_revoked'],
                           previous_session_already_inactive=item['previous_session_already_inactive'])
        receipt.update(actual_exit_code=0, state_requires_observation=False)
        print(json.dumps(receipt))
        return 0
    except (OSError, ValueError, TypeError, KeyError, subprocess.SubprocessError):
        print(json.dumps(receipt))
        return 1


if __name__ == '__main__':
    sys.exit(main())
