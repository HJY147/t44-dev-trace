"""Prepare one exact new synthetic diagnostic database using the original product CLI."""

import hashlib
import json
import os
import secrets
import stat
import subprocess
from pathlib import Path

PHASE = Path('/root/t44-r9/campaign-935/p')
BINDING_SHA = '770d774b715265ba517ea550aab5d001ecd8c04c58f3beb9cc558e752170ca06'
SOURCE = '935ab5b93bea788672c2b4a088c79cfeed848954'
DATABASE = 't44c_r9diag935_p'
OUTPUT = PHASE / 'fixture-bootstrap-01'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, data):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(data)


def save(path, value):
    write(path, (json.dumps(value, indent=2) + '\n').encode())


def main():
    if os.geteuid() != 0 or PHASE.resolve() != PHASE:
        raise ValueError('Exact root-owned cloud phase required')
    binding_path = PHASE / 'binding.json'
    if sha(binding_path) != BINDING_SHA:
        raise ValueError('Exact prepared binding required')
    binding = json.loads(binding_path.read_text())
    if binding['source_sha'] != SOURCE or binding['database'] != DATABASE or binding['phase'] != 'p':
        raise ValueError('Exact source935 diagnostic schema required')
    for name, expected in binding['file_hashes'].items():
        path = PHASE / name
        if path.resolve() != path or sha(path) != expected:
            raise ValueError('Prepared phase changed')
    if stat.S_IMODE((PHASE / 'application.env').stat().st_mode) != 0o600:
        raise ValueError('Private phase environment required')
    environment = {k: v for k, v in os.environ.items()
                   if not k.startswith(('MYSQL_', 'RABBITMQ_', 'COMPOSE_', 'T44_', 'DOCKER_'))
                   and k not in {'DATABASE_URL', 'AMQP_URL'}}
    compose = ['docker', '--context', 'default', 'compose', '--env-file', str(PHASE / 'application.env'),
               '--file', str(PHASE / 'compose.json'), '--project-name', binding['project'],
               '--profile', 'operations', 'run', '--rm', '--no-deps', '-T']
    inspect = subprocess.run(['docker', '--context', 'default', 'image', 'inspect', '--format', '{{.Id}}',
                              't44-backend:src-' + SOURCE], check=True, capture_output=True,
                             timeout=15, env=environment)
    if inspect.stdout.decode().strip() != binding['image_ids']['backend']:
        raise ValueError('Proven application image identity changed')
    subprocess.run(['systemctl', 'is-active', '--quiet', binding['timer_unit']],
                   check=True, timeout=15, env=environment)
    OUTPUT.mkdir(mode=0o700)

    def call(name, arguments, data=None, cap=120):
        try:
            result = subprocess.run(compose + arguments, input=data, capture_output=True, timeout=cap,
                                    check=False, env=environment)
        except subprocess.TimeoutExpired as error:
            write(OUTPUT / (name + '.stdout'), error.stdout or b'')
            write(OUTPUT / (name + '.stderr'), error.stderr or b'')
            raise RuntimeError('Product operation timed out; raw prefix retained: ' + name) from None
        write(OUTPUT / (name + '.stdout'), result.stdout)
        write(OUTPUT / (name + '.stderr'), result.stderr)
        if result.returncode:
            raise RuntimeError('Product operation failed; private raw output retained: ' + name)
        return json.loads(result.stdout)

    query = """
import json
from sqlalchemy import text
from t44.settings import Settings
from t44.persistence import create_mysql_engine, SqlAlchemyUnitOfWorkFactory
settings=Settings.from_env().mysql_settings()
assert settings.database == 't44c_r9diag935_p'
engine=create_mysql_engine(settings)
with engine.connect() as connection:
    assert connection.execute(text('SELECT DATABASE()')).scalar_one() == 't44c_r9diag935_p'
factory=SqlAlchemyUnitOfWorkFactory(engine)
with factory() as unit:
    names=('users','projects','tasks','reviews','decisions','task_dependencies')
    counts={name:unit.gateway.count(name) for name in names}
    projects=unit.gateway.rows('projects', columns=('id',), limit=40)
print(json.dumps({'counts':counts,'project_ids':[row['id'] for row in projects]}))
engine.dispose()
"""
    before = call('00-empty-database', ['--entrypoint', 'python', 'admin', '-c', query])
    if any(before['counts'].values()):
        raise ValueError('Fresh empty synthetic database required; no existing data altered')
    credentials = {role: {'username': username, 'password': secrets.token_urlsafe(32)}
                   for role, username in [('m', 'synthetic-manager'), ('d', 'synthetic-developer'),
                                          ('r', 'synthetic-reviewer')]}
    save(OUTPUT / 'credentials-reserved.private.json', credentials)
    for index, (role, account) in enumerate(credentials.items(), 1):
        result = call(f'0{index}-init-{role}',
                      ['admin', 'init-user', '--username', account['username'], '--display-name',
                       '[synthetic] ' + account['username'], '--password-stdin'],
                      (account['password'] + '\n').encode())
        if type(result.get('user_id')) is not int or result['user_id'] <= 0:
            raise ValueError('Actual positive product user identifier required')
        account['id'] = result['user_id']
    if len({account['id'] for account in credentials.values()}) != 3:
        raise ValueError('Three distinct real synthetic actors required')
    save(OUTPUT / 'accounts.private.json', credentials)
    seed = call('04-seed', ['admin', 'seed-demo', '--projects', '40', '--tasks', '6000',
                            '--dependencies', '9000', '--records', '15000'], cap=600)
    after = call('05-actual-counts', ['--entrypoint', 'python', 'admin', '-c', query])
    counts = after['counts']
    if (counts['users'] != 3 or counts['projects'] != 40 or counts['tasks'] != 6000
            or counts['task_dependencies'] != 9000 or counts['reviews'] + counts['decisions'] != 15000
            or len(after['project_ids']) != 40 or seed['manifest']['version'] != 1):
        raise ValueError('Actual source935 synthetic scale mismatch')
    receipt = {'success': True, 'source_sha': SOURCE, 'database': DATABASE, 'counts': counts,
               'project_ids': after['project_ids'], 'seed': seed,
               'account_ids': {role: value['id'] for role, value in credentials.items()},
               'private_accounts': str(OUTPUT / 'accounts.private.json'),
               'api_or_scheduler_started': False, 'test_or_performance_verdict': None}
    save(OUTPUT / 'result.json', receipt)
    print(json.dumps({key: value for key, value in receipt.items() if key != 'seed'}))


if __name__ == '__main__':
    os.umask(0o077)
    try:
        main()
    except (OSError, ValueError, RuntimeError, KeyError, TypeError, AssertionError,
            subprocess.SubprocessError) as error:
        print(json.dumps({'success': False, 'stage': 'source935-synthetic-bootstrap',
                          'error_class': type(error).__name__, 'partial_outputs_preserved': True}))
        raise SystemExit(1) from None
