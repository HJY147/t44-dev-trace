"""Strict TLS and testable real-readback loops; contains no database credentials."""
import copy
import hashlib
import http.client
import ipaddress
import json
import socket
import ssl
import urllib.parse
import uuid
import fcntl
import os
import re
import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone

MATERIAL_LOCK_FD = None


def setup_material_job(auth, *, temp=Path('/tmp'), proc=Path('/proc')):
    """A same-schema flock and persistent public PID/PGID identity, before writes."""
    global MATERIAL_LOCK_FD
    required(len(sys.argv) == 3 and sys.argv[1] == auth['packet_nonce']
             and re.fullmatch('[0-9a-f]{64}', sys.argv[2]), 'EXPLICIT_UNIQUE_PROCESS_MARKER')
    marker = sys.argv[1]
    lock_name = hashlib.sha256(auth['database'].encode()).hexdigest()
    lock = temp / ('t44-manual-material-' + lock_name + '.lock')
    MATERIAL_LOCK_FD = os.open(lock, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    fcntl.flock(MATERIAL_LOCK_FD, fcntl.LOCK_EX | fcntl.LOCK_NB)
    fields = (proc / 'self/stat').read_text().rsplit(')', 1)[1].split()
    state = {'marker': marker, 'code_sha256': sys.argv[2], 'pid': os.getpid(),
             'pgid': os.getpgrp(), 'start_ticks': fields[19], 'lock_path': str(lock),
             'started_at': datetime.now(timezone.utc).isoformat(),
             'run_id': auth['new_packet_run_id'], 'process_exit_proven': False}
    path = temp / ('t44-manual-material-' + marker + '.PUBLIC.json')
    descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    with os.fdopen(descriptor, 'w') as stream:
        json.dump(state, stream, sort_keys=True)
    return state


def required(value, code):
    if not value:
        raise ValueError(code)


class PinnedHTTPSConnection(http.client.HTTPSConnection):
    def __init__(self, origin, connect_ip, ca, *, connector=socket.create_connection,
                 context_factory=ssl.create_default_context):
        target = urllib.parse.urlsplit(origin)
        required(target.scheme == 'https' and target.hostname and not target.username
                 and not target.password and not target.query and not target.fragment
                 and target.path in ['', '/'], 'ORIGINAL_STRICT_HTTPS_TARGET')
        address = ipaddress.ip_address(connect_ip)
        required(address.is_private and not address.is_loopback and not address.is_unspecified
                 and not address.is_multicast, 'EXPLICIT_PRIVATE_CONNECT_IP_REQUIRED')
        context = context_factory(cafile=str(ca))
        required(context.verify_mode == ssl.CERT_REQUIRED and context.check_hostname is True,
                 'CERTIFICATE_AND_ORIGIN_HOSTNAME_VERIFICATION_REQUIRED')
        super().__init__(target.hostname, target.port or 443, timeout=20, context=context)
        self.connect_ip, self.connector = str(address), connector

    def connect(self):
        required(not self._tunnel_host, 'NO_UNAPPROVED_HTTP_TUNNEL')
        raw = self.connector((self.connect_ip, self.port), timeout=self.timeout,
                             source_address=self.source_address)
        try:
            # TCP uses connect_ip. SNI, Host, and certificate hostname use original origin.
            self.sock = self._context.wrap_socket(raw, server_hostname=self.host)
        except BaseException:
            raw.close()
            raise


class PinnedAPI:
    def __init__(self, origin, connect_ip, ca, *, connection_type=PinnedHTTPSConnection):
        self.requests = []
        self.connection = connection_type(origin, connect_ip, ca)
        # This live TLS handshake occurs before any session issuance by runtime().
        self.connection.connect()

    def request(self, path, token=None, body=None):
        headers = {'Accept': 'application/json', 'X-Request-ID': str(uuid.uuid4())}
        if token:
            headers['Authorization'] = 'Bearer ' + token
        data = None
        if body is not None:
            required(path == '/auth/login', 'ONLY_HUMAN_LOGIN_HTTP_WRITE_ALLOWED')
            headers.update({'Content-Type': 'application/json', 'Idempotency-Key': str(uuid.uuid4())})
            data = json.dumps(body).encode()
        before = datetime.now(timezone.utc).isoformat()
        self.connection.request('POST' if body is not None else 'GET', '/api/v1' + path, data, headers)
        response = self.connection.getresponse()
        raw = response.read(2 * 1024 * 1024 + 1)
        required(len(raw) <= 2 * 1024 * 1024, 'BOUNDED_HTTP_READBACK')
        self.requests.append({'path': path, 'status': response.status,
                              'response_sha256': hashlib.sha256(raw).hexdigest(), 'started_at': before,
                              'observed_at': datetime.now(timezone.utc).isoformat()})
        required(response.status == 200, 'REAL_HTTP_READBACK_REJECTED_' + str(response.status))
        value = json.loads(raw)
        required('data' in value, 'REAL_HTTP_ENVELOPE')
        return value['data'], value.get('meta')

    def pages(self, path, token):
        result, page = [], 1
        while page <= 1000:
            value, _ = self.request(path + ('&' if '?' in path else '?') + f'page={page}&page_size=100', token)
            result.extend(value['items'])
            if len(result) == value['total']:
                return result
            required(value['items'] and len(result) < value['total'], 'FINITE_PAGINATION_READBACK')
            page += 1
        raise ValueError('FINITE_PAGINATION_CAP')

    def close(self):
        self.connection.close()


def role_scope(api, role, token, original_ids):
    projects = api.pages('/projects', token)
    required(sorted(x['id'] for x in projects) == original_ids, 'REAL_ROLE_PROJECT_SCOPE_' + role)
    expected = {'manager': 1, 'developer': 2, 'reviewer': 3}[role]
    roles_by_project = {}
    for project in projects:
        values = project.get('my_roles')
        required(isinstance(values, list) and all(type(x) is int and x in [1, 2, 3] for x in values)
                 and expected in values, 'REAL_PROJECT_ROLE_' + role)
        roles_by_project[str(project['id'])] = values
    return original_ids, roles_by_project


def current_inventory(api, previous, sessions, frozen_rules, select_window, *, clock=None):
    clock = clock or (lambda: datetime.now(timezone.utc))
    inventory, groups, rule_versions = copy.deepcopy(previous), {}, set()
    for client in inventory['clients']:
        groups.setdefault(client['project_id'], []).append(client)
    for pid, clients in groups.items():
        token = sessions['manager']['token']
        tasks = {x['id']: x for x in api.pages(f'/projects/{pid}/tasks', token)}
        events = {x['id']: x for x in api.pages(f'/projects/{pid}/escalations', token)}
        members = api.pages(f'/projects/{pid}/members', token)
        rules, _ = api.request(f'/projects/{pid}/escalation-rules', token)
        required(rules == frozen_rules.snapshot(), 'ACTUAL_FROZEN_RULES_READBACK')
        rule_versions.add(rules['version'])
        managers = sorted(x['user']['id'] for x in members if x['active'] and 1 in x['roles'])
        for client in clients:
            client['transition_task'] = tasks[client['transition_task']['id']]
            client['escalation_task'] = tasks[client['escalation_task']['id']]
            client['escalation_event'] = events[client['escalation_event']['id']]
            client['project_manager_ids'] = managers
            edges = api.pages(f"/projects/{pid}/tasks/{client['transition_task']['id']}/dependencies", token)
            required(not edges, 'ORIGINAL_EMPTY_TRANSITION_DEPENDENCIES_CHANGED')
            task, event = client['escalation_task'], client['escalation_event']
            at = clock()
            end = datetime.fromisoformat(task['plan']['planned_end'].replace('Z', '+00:00'))
            selected = [select_window(point, end, frozen_rules) for point in [at, at + timedelta(seconds=900)]]
            required(all(x is not None and x.level == event['level'] for x in selected),
                     'ACTUAL_STABLE_ESCALATION_LEVEL_NOT_ELIGIBLE')
    required(len(rule_versions) == 1, 'ONE_ACTUAL_CURRENT_RULE_VERSION')
    inventory['rule_version'] = rule_versions.pop()
    inventory['captured_at'] = clock().isoformat().replace('+00:00', 'Z')
    return inventory
