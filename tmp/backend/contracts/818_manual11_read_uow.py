"""Live invalidation between validation and read, using real SQLite persistence."""
from datetime import timedelta
from importlib import import_module
from uuid import uuid4

import pytest
from t44.services.common import Call

_http = import_module('.986_http', __package__)


@pytest.mark.parametrize('change,expected', [
    ('session', 'TOKEN_REVOKED'),
    ('expiry', 'TOKEN_EXPIRED'),
    ('identity', 'TOKEN_REVOKED'),
    ('membership', 'PROJECT_ACCESS_DENIED'),
])
def test_invalidation_during_validation_is_still_checked(application, change, expected):
    client, factory = application
    tokens, pid, iid = _http.setup_project(client)
    task = _http.create_task(client, tokens, pid, iid)
    runtime = client.app.state.runtime
    call = Call('getTask', str(uuid4()), tokens['manager'],
                path={'project_id': pid, 'task_id': task['id']})

    def invalidate(c):
        assert c.actor and c.membership  # initial authentication precedes validation
        with factory() as uow:
            g = uow.gateway
            if change == 'session':
                g.update('auth_sessions', {'id': c.actor['id']}, {'revoked_at': c.clock})
            elif change == 'expiry':
                g.update('auth_sessions', {'id': c.actor['id']},
                         {'expires_at': c.clock - timedelta(seconds=1)})
            elif change == 'identity':
                g.update('users', {'id': c.actor_id}, {'active': 0})
            else:
                g.update('project_members', {'id': c.membership['id']}, {'active': 0})

    status, result, replayed, original = runtime.execute(call, invalidate)
    assert status in (401, 403)
    assert result['code'] == expected
    assert result['audit_id'] is not None
    assert replayed is False and original is None


def test_get_auth_failure_precedes_validation(application):
    client, _ = application
    call = Call('getTask', str(uuid4()), 'x' * 40,
                path={'project_id': 1, 'task_id': 1})
    def forbidden(c):
        pytest.fail('validation ran before authentication')
    status, result, _, _ = client.app.state.runtime.execute(call, forbidden)
    assert status == 401 and result['code'] == 'AUTH_REQUIRED'
