"""One-shot HTTPS maintenance of original400tasks; no database or benchmark access."""
import argparse
import hashlib
import http.client
import json
import os
import socket
import ssl
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

ORIGIN = '172.21.182.245'
HOST = ORIGIN + ':26445'
CONNECT = ('192.168.96.4', 8443)
BASIS = 'Restore original transition cohort after completed MANUAL11 BLOCK/UNBLOCK cycle'
EVIDENCE = [{'kind': 2, 'locator': 'MANUAL11/PUBLIC/INDEPENDENT_REPORT.PUBLIC.md',
             'description': 'Maintenance restores existing owned blocked tasks to recorded prior state'}]


class Refused(Exception):
    pass


def need(value, code):
    if not value:
        raise Refused(code)


def stamp():
    return datetime.now(timezone.utc).isoformat()


class TLS(http.client.HTTPSConnection):
    def connect(self):
        sock = socket.create_connection(CONNECT, self.timeout)
        try:
            self.sock = self._context.wrap_socket(sock, server_hostname=ORIGIN)
        except BaseException:
            sock.close()
            raise


class API:
    def __init__(self, ca, journal, deadline):
        self.connection = TLS(ORIGIN, 26445, context=ssl.create_default_context(cafile=str(ca)), timeout=15)
        self.journal, self.deadline, self.calls = journal, deadline, 0

    def request(self, path, token=None, body=None):
        need(time.monotonic() < self.deadline, 'MAINTENANCE_DEADLINE')
        self.calls += 1
        key = str(uuid4())
        method = 'GET' if body is None else 'POST'
        headers = {'Host': HOST, 'Accept': 'application/json', 'X-Request-ID': key}
        if token:
            headers['Authorization'] = 'Bearer ' + token
        if body is not None:
            headers.update({'Content-Type': 'application/json', 'Idempotency-Key': key})
        rec = {'request_number': self.calls, 'client_request_id': key, 'method': method,
               'path': path, 'started_at': stamp()}
        try:
            self.connection.timeout = min(15, max(.1, self.deadline-time.monotonic()))
            if self.connection.sock:
                self.connection.sock.settimeout(self.connection.timeout)
            self.connection.request(method, '/api/v1' + path,
                                    body=None if body is None else json.dumps(body).encode(), headers=headers)
            response = self.connection.getresponse()
            raw = response.read(1048577)
            rec['status'] = response.status
            need(len(raw) <= 1048576, 'RESPONSE_SIZE_LIMIT')
            envelope = json.loads(raw)
            rec['server_request_id'] = envelope.get('meta', {}).get('request_id', envelope.get('request_id'))
            if response.status != 200 or 'data' not in envelope:
                code = envelope.get('code', 'HTTP_REJECTED')
                rec['error_code'] = code if isinstance(code, str) else 'HTTP_REJECTED'
                raise Refused(rec['error_code'])
            return envelope['data']
        except Refused:
            raise
        except Exception:
            rec['error_code'] = 'HTTP_OUTCOME_UNKNOWN_STOP_NO_RETRY'
            raise Refused(rec['error_code']) from None
        finally:
            rec['finished_at'] = stamp()
            self.journal.write(json.dumps(rec, sort_keys=True) + '\n')
            self.journal.flush()
            os.fsync(self.journal.fileno())

    def close(self):
        self.connection.close()


def targets(packet, account):
    developer = account['user_id']
    need(type(developer) is int and developer > 0, 'DEVELOPER_ID_REQUIRED')
    need(packet['environment']['origin'] == 'https://' + HOST, 'PACKET_ORIGIN_MISMATCH')
    need(packet['sessions']['developer']['user_id'] == developer, 'DEVELOPER_PACKET_ID_MISMATCH')
    rows = packet['inventory']['clients']
    need(len(rows) == 400, 'EXACT_ORIGINAL_400_REQUIRED')
    result = []
    for row in rows:
        pid, task = row['project_id'], row['transition_task']
        tid = task['id']
        need(type(pid) is int and pid > 0 and type(tid) is int and tid > 0, 'POSITIVE_IDS_REQUIRED')
        need(task['project_id'] == pid and task['owner_id'] == developer, 'PACKET_TASK_SCOPE_MISMATCH')
        result.append((pid, tid))
    need(len({tid for _, tid in result}) == 400, 'DUPLICATE_ORIGINAL_TASK_ID')
    return result


def check_task(task, pid, tid, developer):
    need(task['id'] == tid and task['project_id'] == pid and task['owner_id'] == developer,
         'LIVE_TASK_SCOPE_MISMATCH')
    need(type(task['version']) is int and task['version'] > 0, 'LIVE_VERSION_REQUIRED')
    need(task['state'] == 2 or (task['state'] == 3 and task['blocked_from_state'] == 2),
         'LIVE_TASK_STATE_NOT_RESTORABLE')


def restore(api, items, account, emit, summary):
    login = api.request('/auth/login', body={'username': account['username'], 'password': account['password']})
    summary['login_issued'] = True
    need(login['user']['id'] == account['user_id'], 'LOGIN_DEVELOPER_ID_MISMATCH')
    token = login['access_token']
    summary['login_expires_at'] = login['expires_at']
    before, expected = {}, {}
    # Validate every original task before the first mutation; no material/seed creation.
    for pid, tid in items:
        task = api.request(f'/projects/{pid}/tasks/{tid}', token)
        check_task(task, pid, tid, account['user_id'])
        before[tid] = task
        emit({'phase': 'before', 'project_id': pid, 'task_id': tid, 'state': task['state'],
              'blocked_from_state': task['blocked_from_state'], 'version': task['version']})
    summary['preflight_gets'] = len(before)
    for pid, tid in items:
        task = before[tid]
        if task['state'] == 2:
            expected[tid] = task['version']
            summary['skipped_state2'] += 1
            continue
        result = api.request(f'/projects/{pid}/tasks/{tid}/transitions', token,
                             {'expected_version': task['version'], 'action': 3,
                              'basis': BASIS, 'evidence': EVIDENCE})
        actual = result['task']
        check_task(actual, pid, tid, account['user_id'])
        need(actual['state'] == 2 and actual['blocked_from_state'] is None and
             actual['version'] == task['version'] + 1, 'UNBLOCK_RESPONSE_MISMATCH')
        expected[tid] = actual['version']
        summary['unblocked'] += 1
        emit({'phase': 'unblocked', 'project_id': pid, 'task_id': tid, 'before_version': task['version'],
              'after_version': actual['version'], 'state': actual['state'], 'audit_id': result.get('audit_id')})
    for pid, tid in items:
        actual = api.request(f'/projects/{pid}/tasks/{tid}', token)
        check_task(actual, pid, tid, account['user_id'])
        need(actual['state'] == 2 and actual['blocked_from_state'] is None and
             actual['version'] == expected[tid], 'FINAL_READBACK_MISMATCH')
        summary['final_state2_gets'] += 1
        emit({'phase': 'final', 'project_id': pid, 'task_id': tid, 'state': actual['state'],
              'blocked_from_state': actual['blocked_from_state'], 'version': actual['version']})
    summary['status'] = 'COMPLETE_EXISTING_400_STATE2'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('packet', 'accounts', 'ca', 'output'):
        parser.add_argument('--' + name, required=True, type=Path)
    args = parser.parse_args()
    os.umask(0o077)
    # Exclusive output preserves original failed material and previous maintenance evidence.
    args.output.mkdir(mode=0o700, parents=False, exist_ok=False)
    summary = {'schema': 'manual11-existing-cohort-maintenance-v1', 'started_at': stamp(),
               'status': 'INCOMPLETE', 'new_tasks': 0, 'unblocked': 0, 'skipped_state2': 0,
               'preflight_gets': 0, 'final_state2_gets': 0, 'login_issued': False,
               'origin': 'https://' + HOST, 'connect': list(CONNECT), 'retry': False}
    api = None
    code = 1
    try:
        packet_raw = args.packet.read_bytes()
        packet = json.loads(packet_raw)
        accounts = json.loads(args.accounts.read_bytes())
        account = accounts['developer']
        items = targets(packet, account)
        ca_sha = hashlib.sha256(args.ca.read_bytes()).hexdigest()
        need(packet['environment']['ca_sha256'] == ca_sha, 'PACKET_CA_MISMATCH')
        summary.update({'packet_sha256': hashlib.sha256(packet_raw).hexdigest(), 'ca_sha256': ca_sha,
                        'developer_user_id': account['user_id'], 'original_tasks': len(items)})
        with (args.output/'requests.PUBLIC.jsonl').open('x') as journal, (args.output/'states.PUBLIC.jsonl').open('x') as states:
            api = API(args.ca, journal, time.monotonic()+180)
            def emit(row):
                states.write(json.dumps(row, sort_keys=True)+'\n')
                states.flush()
                os.fsync(states.fileno())
            restore(api, items, account, emit, summary)
        code = 0
    except Refused as error:
        summary['error_code'] = str(error)
    except Exception:
        summary['error_code'] = 'INPUT_OR_MAINTENANCE_FAILURE_NO_RETRY'
    finally:
        if api:
            summary['requests'] = api.calls
            api.close()
        summary['finished_at'] = stamp()
        with (args.output/'SUMMARY.PUBLIC.json').open('x') as stream:
            json.dump(summary, stream, sort_keys=True, indent=2)
        print(json.dumps({'status': summary['status'], 'error_code': summary.get('error_code'),
                          'summary': str(args.output/'SUMMARY.PUBLIC.json')}))
    return code


if __name__ == '__main__':
    sys.exit(main())
