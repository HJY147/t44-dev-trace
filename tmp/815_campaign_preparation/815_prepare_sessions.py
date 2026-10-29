"""Coordinator fixture preparation only; no independent test or cloud action."""

import argparse
import hashlib
import json
import os
import subprocess
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy.engine import make_url

from t44.api import create_app
from t44.persistence import SqlAlchemyUnitOfWorkFactory, create_mysql_engine
from t44.services.common import now
from t44.services.identity import issue_session
from t44.settings import Settings

ROOT = Path('/Users/yang/Desktop/nothing/软件开发大作业')
PRIVATE = ROOT / '.agent-worktrees/.runtime/continuation-20261025'
SOURCE = ROOT / '.agent-worktrees/backend-acceptance-followup-20261025'
COMMIT = '935ab5b93bea788672c2b4a088c79cfeed848954'


def load(path):
    if path.is_symlink() or path.stat().st_mode & 0o077:
        raise ValueError('Explicit private regular input required')
    return json.loads(path.read_text())


def save(path, value):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'w') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')


def run(kind):
    from fastapi.testclient import TestClient

    folder = PRIVATE / ('functional-db-round8' if kind == 'functional' else 'performance-db-round8')
    db = 't44_f816_20261025' if kind == 'functional' else 't44_p816_20261025'
    env = load(folder / 'application-env.json')
    url = make_url(env['DATABASE_URL'])
    assert url.database == url.username == env['T44_DATABASE'] == db
    assert url.drivername == 'mysql+pymysql' and url.host == '127.0.0.1' and url.port == 13306
    report = {'source_sha': COMMIT, 'database': db, 'kind': kind,
              'started_utc': datetime.now(UTC).isoformat(), 'independent_acceptance': False,
              'root_asgi_login_requests': 0, 'direct_fixture_sessions': 0,
              'source_file_sha256': {}}
    for name in ('backend/t44/api.py', 'backend/t44/services/identity.py', 'backend/t44/settings.py'):
        data = (SOURCE / name).read_bytes()
        assert data == subprocess.check_output(['git', 'show', COMMIT + ':' + name], cwd=SOURCE)
        report['source_file_sha256'][name] = hashlib.sha256(data).hexdigest()
    settings = Settings(database_url=env['DATABASE_URL'], session_ttl_seconds=3600)
    engine = create_mysql_engine(settings.mysql_settings())
    factory = SqlAlchemyUnitOfWorkFactory(engine)
    accounts = {}
    try:
        if kind == 'functional':
            identities = load(folder / 'identities.json')
            with TestClient(create_app(factory=factory, settings=settings, notifications=None, escalations=None)) as client:
                for name in ('m', 'd', 'd2', 'r', 'x'):
                    identity = identities[name]
                    response = client.post('/api/v1/auth/login', json={k: identity[k] for k in ('username', 'password')})
                    assert response.status_code == 200, 'Root environment login failed'
                    data = response.json()['data']
                    assert data['user']['id'] == identity['user_id']
                    accounts[name] = {'id': identity['user_id'], 'username': identity['username'], 'password': identity['password'],
                                      'token': data['access_token']}
                    report['root_asgi_login_requests'] += 1
            short = Settings(database_url=env['DATABASE_URL'], session_ttl_seconds=60)
            with TestClient(create_app(factory=factory, settings=short, notifications=None, escalations=None)) as client:
                identity = identities['m']
                response = client.post('/api/v1/auth/login', json={k: identity[k] for k in ('username', 'password')})
                assert response.status_code == 200, 'Root short-TTL login failed'
                data = response.json()['data']
                assert data['user']['id'] == identity['user_id']
                accounts['expired'] = {'id': identity['user_id'], 'username': identity['username'], 'token': data['access_token']}
                report['expired_input_expires_at'] = data['expires_at']
                report['expired_input_ttl_seconds'] = 60
                report['expired_input_note'] = 'Naturally wait beyond actual server expiry before independent admission; no clock or expires_at rewrite, no revocation.'
                report['root_asgi_login_requests'] += 1
        else:
            with factory() as uow:
                for name in ('m', 'd', 'd2', 'r', 'x'):
                    row = uow.gateway.rows('users', {'username': name}, limit=1)
                    assert len(row) == 1 and row[0]['active'] == 1
                    session = issue_session(uow.gateway, clock=now(), ttl=3600, user_id=row[0]['id'])
                    accounts[name] = {'id': row[0]['id'], 'username': name, 'token': session['access_token']}
                    report['direct_fixture_sessions'] += 1
        report['account_ids'] = {k: a['id'] for k, a in accounts.items()}
        report['active_session_ttl_seconds'] = 3600
        save(folder / 'accounts-private.json', accounts)
        report['status'] = 'Prepared genuine fixture sessions; no independent requests or project data reset'
    finally:
        report['checkedout_before_dispose'] = engine.pool.checkedout()
        engine.dispose()
        report['disposed'] = True
        report['ended_utc'] = datetime.now(UTC).isoformat()
        save(folder / 'session-preparation-receipt.json', report)
    print(json.dumps({k: report[k] for k in ('kind', 'database', 'root_asgi_login_requests', 'direct_fixture_sessions', 'status')}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('kind', choices=('functional', 'performance'))
    args = parser.parse_args()
    try:
        run(args.kind)
    except BaseException as error:
        raise RuntimeError('Session preparation failed; inspect only sanitized private receipt; exception=' + type(error).__name__) from None
