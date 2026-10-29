"""Neutral fixture setup through real HTTP. Never imports tester or application source."""
import concurrent.futures
import datetime as dt
import hashlib
import http.client
import json
import os
import ssl
import sys
import time
import urllib.parse
import uuid
from pathlib import Path

UTC = dt.timezone.utc


def stamp(value):
    return value.astimezone(UTC).isoformat(timespec='microseconds').replace('+00:00', 'Z')


def parsed(value):
    return dt.datetime.fromisoformat(value.replace('Z', '+00:00'))


def save(path, value):
    with path.open('x') as stream:
        os.chmod(path, 0o600)
        json.dump(value, stream, sort_keys=True)
        stream.flush()
        os.fsync(stream.fileno())


def choose_escalations(tasks, excluded, stop, count=10):
    # Level 3 is open-ended; neither current clock nor the whole future window crosses it.
    eligible = [t for t in tasks if t['id'] not in excluded and t['state'] in (1, 2, 3, 4, 5)
                and parsed(t['plan']['planned_end']) < stop - dt.timedelta(days=1, minutes=1)]
    eligible.sort(key=lambda row: row['id'])
    if len(eligible) < count:
        raise ValueError('INSUFFICIENT_DISJOINT_STABLE_LEVEL3_TASKS')
    return eligible[:count]


class Client:
    def __init__(self, origin, ca, output, deadline):
        target = urllib.parse.urlsplit(origin)
        if target.scheme != 'https' or target.path not in ('', '/') or target.username:
            raise ValueError('EXPLICIT_HTTPS_ORIGIN_REQUIRED')
        self.target, self.ca, self.output, self.deadline = target, ca, output, deadline
        self.number = 0
        self.connection = None

    def request(self, path, token=None, body=None, method=None):
        left = self.deadline - time.monotonic()
        if left <= 0:
            raise TimeoutError('NEUTRAL_PREPARATION_DEADLINE')
        self.number += 1
        identifier = f'{uuid.uuid4()}'
        method = method or ('POST' if body is not None else 'GET')
        headers = {'Accept': 'application/json', 'X-Request-ID': identifier}
        if token:
            headers['Authorization'] = 'Bearer ' + token
        payload = None if body is None else json.dumps(body, separators=(',', ':')).encode()
        if payload is not None:
            headers['Content-Type'] = 'application/json'
            headers['Idempotency-Key'] = identifier
        # Credentials are never copied into command lines, public logs or request evidence.
        record = {'request_id': identifier, 'path': path, 'method': method, 'started_at': stamp(dt.datetime.now(UTC))}
        try:
            if self.connection is None:
                self.connection = http.client.HTTPSConnection(self.target.hostname, self.target.port or 443,
                    timeout=min(20, left), context=ssl.create_default_context(cafile=str(self.ca)))
            self.connection.timeout = min(20, left)
            self.connection.request(method, '/api/v1' + path, body=payload, headers=headers)
            response = self.connection.getresponse()
            raw = response.read(1024 * 1024 + 1)
            if len(raw) > 1024 * 1024:
                raise ValueError('RESPONSE_SIZE_CAP')
            record.update(status=response.status, response_bytes=len(raw), response_sha256=hashlib.sha256(raw).hexdigest())
            result = json.loads(raw)
            # Full successful non-login data stays private, preserving 0/null.
            if path != '/auth/login':
                record['response'] = result
            if response.status not in (200, 201, 202) or 'data' not in result:
                raise ValueError('REAL_HTTP_PREPARATION_REJECTED')
            return result['data']
        except Exception as error:
            record['failure_type'] = type(error).__name__
            raise
        finally:
            record['finished_at'] = stamp(dt.datetime.now(UTC))
            save(self.output / (identifier + '.private.json'), record)

    def close(self):
        if self.connection:
            self.connection.close()


def all_pages(client, path, token):
    result, page = [], 1
    while True:
        separator = '&' if '?' in path else '?'
        row = client.request(path + separator + f'page={page}&page_size=100', token)
        result.extend(row['items'])
        if len(result) == row['total']:
            return result
        if not row['items'] or len(result) > row['total'] or page > 1000:
            raise ValueError('INCONSISTENT_FINITE_PAGE')
        page += 1


def run(configuration, output):
    c = json.loads(configuration.read_bytes())
    if c.get('admit_real_HTTP_fixture_preparation') is not True or c.get('original_short_diagnostic_finished') is not True:
        raise ValueError('SEPARATE_ROOT_PREPARATION_ADMISSION_REQUIRED')
    output.mkdir(mode=0o700)
    records = output / 'requests'
    records.mkdir(mode=0o700)
    stop = parsed(c['cost_stop_utc'])
    now = dt.datetime.now(UTC)
    duration = (stop - now).total_seconds()
    if not 1200 < duration <= 3600:
        raise ValueError('NEED_TIME_FOR_SETUP_AND_SEPARATE_660_SECOND_RUN')
    deadline = time.monotonic() + min(360, duration - 1000)
    accounts = json.loads(Path(c['accounts_file']).read_bytes())
    service = json.loads(Path(c['service_file']).read_bytes())
    client = Client(c['origin'], Path(c['ca_file']), records, deadline)
    sessions = {'service': service}
    for role in ('manager', 'developer', 'reviewer'):
        account = accounts[role]
        response = client.request('/auth/login', body={'username': account['username'], 'password': account['password']})
        if response['user']['id'] != account['user_id'] or parsed(response['expires_at']) <= stop:
            raise ValueError('ACTUAL_IDENTITY_OR_FULL_WINDOW_EXPIRY')
        sessions[role] = {'token': response['access_token'], 'user_id': response['user']['id'],
            'expires_at': response['expires_at'], 'project_ids': [], 'scopes': []}
    projects = all_pages(client, '/projects', sessions['manager']['token'])
    if len(projects) != 40:
        raise ValueError('ACTUAL_FORTY_PROJECTS_REQUIRED')
    ids = sorted(p['id'] for p in projects)
    for role in ('manager', 'developer', 'reviewer'):
        sessions[role]['project_ids'] = ids
    if sorted(service['project_ids']) != ids or service['scopes'] != ['escalation:write'] or parsed(service['expires_at']) <= stop:
        raise ValueError('ACTUAL_SCOPED_SERVICE_SESSION_REQUIRED')
    excluded = set(c['exclude_short_task_ids'])
    if len(excluded) != 882:
        raise ValueError('ORIGINAL_441_PAIRS_MUST_STAY_UNTOUCHED')
    future = stop + dt.timedelta(days=2)

    def project_setup(pid):
        api = Client(c['origin'], Path(c['ca_file']), records, deadline)
        manager, developer = sessions['manager']['token'], sessions['developer']['token']
        try:
            members = all_pages(api, f'/projects/{pid}/members', manager)
            managers = sorted(m['user']['id'] for m in members if 1 in m['roles'] and m['active'])
            for role, role_id in (('manager', 1), ('developer', 2), ('reviewer', 3)):
                if not any(m['user']['id'] == sessions[role]['user_id'] and role_id in m['roles'] and m['active'] for m in members):
                    raise ValueError('ACTUAL_MEMBERSHIP_ROLE_REQUIRED')
            iterations = all_pages(api, f'/projects/{pid}/iterations', manager)
            iters = [r for r in iterations if any(x['user_id'] == sessions['developer']['user_id'] for x in r['plan']['capacity'])
                     and parsed(r['plan']['planned_end']) >= future]
            if not iters:
                raise ValueError('REAL_CAPACITY_ITERATION_REQUIRED')
            iteration = min(iters, key=lambda row: row['id'])
            tasks = all_pages(api, f'/projects/{pid}/tasks', manager)
            rules = api.request(f'/projects/{pid}/escalation-rules', manager)
            escs = choose_escalations(tasks, excluded, now, 10)
            result = []
            for local, escalation in enumerate(escs):
                created = api.request(f'/projects/{pid}/tasks', manager, {
                    'title': f'[synthetic neutral r29] {pid}-{local}', 'description': 'Separate benchmark-exclusive API-created fixture',
                    'iteration_id': iteration['id'], 'owner_id': sessions['developer']['user_id'], 'dependency_task_ids': [],
                    'plan': {'planned_start': stamp(now), 'planned_end': stamp(future), 'estimated_hours': 1,
                        'buffer_hours': 0.25, 'delay_contingency': '[synthetic] preserve audit and replan via manager'}})['task']
                transition = api.request(f"/projects/{pid}/tasks/{created['id']}/transitions", developer,
                    {'expected_version': created['version'], 'action': 1})['task']
                event = api.request(f"/internal/projects/{pid}/tasks/{escalation['id']}/escalations", service['token'],
                    {'expected_version': escalation['version'], 'schedule_version': escalation['schedule_version'],
                        'rule_version': rules['version'], 'scan_run_id': str(uuid.uuid4())})
                actual_escalation = api.request(f"/projects/{pid}/tasks/{escalation['id']}", manager)
                actual_transition = api.request(f"/projects/{pid}/tasks/{transition['id']}", developer)
                if actual_transition['state'] != 2 or actual_transition['owner_id'] != sessions['developer']['user_id'] or event['event']['level'] != 3:
                    raise ValueError('REAL_POST_PREPARATION_SNAPSHOT_REQUIRED')
                # Read the existing event once more; delivery disposition may change asynchronously.
                existing = all_pages(api, f"/projects/{pid}/escalations?task_id={escalation['id']}&level=3", manager)
                matches = [e for e in existing if e['id'] == event['event']['id']]
                if len(matches) != 1:
                    raise ValueError('EXISTING_EVENT_SNAPSHOT_REQUIRED')
                result.append({'project_id': pid, 'transition_task': actual_transition, 'escalation_task': actual_escalation,
                    'escalation_event': matches[0], 'project_manager_ids': managers})
            return rules['version'], result, {'project_id':pid, 'members':members, 'iteration':iteration,
                'new_task_dependencies':[], 'original_task_count':len(tasks)}
        finally:
            api.close()

    # Finite setup concurrency is distinct from the independently owned 400-client test.
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        rows = list(pool.map(project_setup, ids))
    client.close()
    if len({version for version, _, _ in rows}) != 1:
        raise ValueError('ONE_CURRENT_RULE_VERSION_REQUIRED')
    clients = [item for _, items, _ in rows for item in items]
    for index, item in enumerate(clients):
        item['client_id'] = index
    all_ids = [item[k]['id'] for item in clients for k in ('transition_task', 'escalation_task')]
    if len(clients) != 400 or len(set(all_ids)) != 800 or excluded.intersection(all_ids):
        raise ValueError('EXACT_DISJOINT_400_CLIENT_INVENTORY_REQUIRED')
    save(output / 'sessions.json', sessions)
    save(output / 'inventory.json', {'schema':'772-inventory-v1', 'captured_at':stamp(dt.datetime.now(UTC)),
        'rule_version':rows[0][0], 'clients':clients})
    save(output / 'additional-neutral-snapshots.json', {'projects':[p for _, _, p in rows],
        'benchmark_exclusive':True, 'preparation_actor':'AI coordinator using authorized real business APIs'})
    return {'kind':'NEUTRAL_FIXTURE_HTTP_PREPARED_NOT_PERFORMANCE', 'clients':400, 'new_tasks':400,
        'actual_HTTP_requests':len(list(records.glob('*.private.json'))), 'raw_private_evidence':str(records),
        'sessions_sha256':hashlib.sha256((output/'sessions.json').read_bytes()).hexdigest(),
        'inventory_sha256':hashlib.sha256((output/'inventory.json').read_bytes()).hexdigest(),
        'actual_final_database_counts_verified':False, 'formal_performance_passed':False}


if __name__ == '__main__':
    os.umask(0o077)
    try:
        print(json.dumps(run(Path(sys.argv[1]), Path(sys.argv[2])), sort_keys=True))
    except Exception as error:
        print(json.dumps({'kind':'NEUTRAL_FIXTURE_FAILED_PREFIX_PRESERVED', 'failure_type':type(error).__name__,
            'reason':str(error), 'automatic_retry':False, 'formal_performance_passed':False}))
        raise SystemExit(1) from None
