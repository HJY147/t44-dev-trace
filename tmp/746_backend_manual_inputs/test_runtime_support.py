import copy
from datetime import timedelta
import json
import os
from pathlib import Path
import ssl
import tempfile
import types
import unittest
from unittest.mock import patch

from test_refresh import HERE, fixture, load, host

support = load('manual_support_test', HERE / 'runtime_support.py')
guard = load('manual_guard_test', HERE / 'process_guard.py')


class FakeConnection:
    responder = None
    def __init__(self, *args):
        self.sent = []; self.connected = False
    def connect(self):
        self.connected = True
    def request(self, method, path, body, headers):
        assert self.connected
        self.sent.append((method, path, body, headers))
    def getresponse(self):
        value = self.responder(self.sent[-1])
        return types.SimpleNamespace(status=200, read=lambda limit: json.dumps({'data': value, 'meta': {'server_time': 'actual-fake-clock'}}).encode())
    def close(self):
        self.connected = False


class SupportTests(unittest.TestCase):
    def test_maintenance_tcp_port_keeps_original_host_header_sni_and_benchmark_origin(self):
        calls, sent = [], []
        raw = types.SimpleNamespace(close=lambda: None, sendall=lambda data: sent.append(data))
        context = types.SimpleNamespace(verify_mode=ssl.CERT_REQUIRED, check_hostname=True,
                   wrap_socket=lambda sock, server_hostname: calls.append(('SNI', server_hostname)) or raw)
        connection = support.PinnedHTTPSConnection('https://synthetic.example:26445', '192.168.96.4',
                        '/fake/ca', connect_port=8443,
                        connector=lambda address, **kw: calls.append(('TCP', address)) or raw,
                        context_factory=lambda **kw: context)
        connection.connect(); connection.request('GET', '/api/v1/projects')
        self.assertEqual(calls, [('TCP', ('192.168.96.4', 8443)), ('SNI', 'synthetic.example')])
        self.assertEqual(connection.port, 26445)
        self.assertIn(b'Host: synthetic.example:26445', b''.join(sent))

    def test_maintenance_endpoint_requires_actual_same_owner_shared_network_and_port_mapping(self):
        args = types.SimpleNamespace(api_container='api-test', maintenance_gateway_container='gateway-test',
                                     maintenance_connect_ip='192.168.96.4', maintenance_connect_port=8443)
        auth = {'namespace': 't44-cloud-r30finalp09-p'}
        original = {'environment': {'origin': 'https://172.21.182.245:26445', 'connect_ip': '172.21.182.245'}}
        before = copy.deepcopy(original)
        gateway = {'id': '8' * 64, 'running': True,
                   'labels': {'com.docker.compose.project': auth['namespace'], 'com.docker.compose.service': 'tls-gateway'},
                   'networks': {'application': {'IPAddress': '192.168.96.4', 'NetworkID': 'network-1'}},
                   'ports': {'8443/tcp': [{'HostPort': '26445'}]}}
        def command(argv, **kw):
            if 'ps' in argv:
                return types.SimpleNamespace(stdout=(gateway['id'] + '\n').encode())
            value = gateway if argv[-1] == 'gateway-test' else {
                'application': {'IPAddress': '192.168.96.2', 'NetworkID': 'network-1'}}
            return types.SimpleNamespace(stdout=json.dumps(value).encode())
        with patch.object(host.subprocess, 'run', side_effect=command):
            value = host.maintenance_endpoint(args, auth, original)
            self.assertEqual(value['connect_port'], 8443)
            self.assertEqual(original, before)
            gateway['labels']['com.docker.compose.project'] = 'unrelated'
            with self.assertRaisesRegex(ValueError, 'SAME_OWNER'):
                host.maintenance_endpoint(args, auth, original)
            gateway['labels']['com.docker.compose.project'] = auth['namespace']
            gateway['networks']['application']['NetworkID'] = 'different'
            with self.assertRaisesRegex(ValueError, 'SHARED_API_GATEWAY'):
                host.maintenance_endpoint(args, auth, original)

    def test_tcp_ip_and_tls_sni_are_distinct_and_strict(self):
        calls = []
        raw = types.SimpleNamespace(close=lambda: calls.append('closed'))
        context = types.SimpleNamespace(verify_mode=ssl.CERT_REQUIRED, check_hostname=True,
                   wrap_socket=lambda sock, server_hostname: calls.append(('SNI', server_hostname)) or raw)
        connection = support.PinnedHTTPSConnection('https://synthetic.example:26445', '172.21.182.245',
                        '/fake/ca', connector=lambda address, **kw: calls.append(('TCP', address)) or raw,
                        context_factory=lambda **kw: context)
        connection.connect()
        self.assertEqual(calls, [('TCP', ('172.21.182.245', 26445)), ('SNI', 'synthetic.example')])
        with self.assertRaisesRegex(ValueError, 'HOSTNAME_VERIFICATION'):
            support.PinnedHTTPSConnection('https://synthetic.example', '172.21.182.245', '/fake/ca',
                 context_factory=lambda **kw: types.SimpleNamespace(verify_mode=ssl.CERT_REQUIRED, check_hostname=False))

    def test_certificate_failure_propagates_and_closes_raw_socket(self):
        closed = []
        raw = types.SimpleNamespace(close=lambda: closed.append(True))
        def reject(*args, **kwargs):
            raise ssl.SSLCertVerificationError('synthetic rejection')
        context = types.SimpleNamespace(verify_mode=ssl.CERT_REQUIRED, check_hostname=True, wrap_socket=reject)
        connection = support.PinnedHTTPSConnection('https://synthetic.example', '172.21.182.245', '/fake/ca',
            connector=lambda *a, **kw: raw, context_factory=lambda **kw: context)
        with self.assertRaises(ssl.SSLCertVerificationError):
            connection.connect()
        self.assertEqual(closed, [True])

    def test_actual_project_my_roles_not_old_label(self):
        ids = list(range(1, 41))
        projects = [{'id': pid, 'my_roles': [2]} for pid in ids]
        FakeConnection.responder = staticmethod(lambda request: {'items': projects, 'total': len(projects)})
        api = support.PinnedAPI('unused', 'unused', 'unused', connection_type=FakeConnection)
        scope, observed = support.role_scope(api, 'developer', 'synthetic-token', ids)
        self.assertEqual(scope, ids); self.assertEqual(observed['17'], [2])
        projects[16]['my_roles'] = [1]
        with self.assertRaisesRegex(ValueError, 'REAL_PROJECT_ROLE_developer'):
            support.role_scope(api, 'developer', 'synthetic-token', ids)
        self.assertTrue(all(x[0] == 'GET' for x in api.connection.sent))

    def test_current_readback_loop_uses_realistic_http_responses_for_same800_ids(self):
        old, _, sessions, inventory, _, _, now, _ = fixture()
        previous = copy.deepcopy(inventory)
        groups = {}
        for client in inventory['clients']:
            client['transition_task']['version'] = 7
            client['escalation_task']['plan'] = {'planned_end': (now - timedelta(days=2)).isoformat()}
            client['escalation_event']['level'] = 3
            groups.setdefault(client['project_id'], []).append(client)
        bad_edges = [False]
        def responder(request):
            method, full_path, *_ = request
            self.assertEqual(method, 'GET')
            path = full_path.split('?', 1)[0].removeprefix('/api/v1')
            parts = path.strip('/').split('/'); pid = int(parts[1]); clients = groups[pid]
            if path.endswith('/escalation-rules'):
                return {'version': 1}
            if path.endswith('/dependencies'):
                items = [{'predecessor_id': 999}] if bad_edges[0] else []
            elif path.endswith('/tasks'):
                items = [x[k] for x in clients for k in ['transition_task', 'escalation_task']]
            elif path.endswith('/escalations'):
                items = [x['escalation_event'] for x in clients]
            elif path.endswith('/members'):
                items = [{'user': {'id': 1}, 'active': True, 'roles': [1]}]
            else:
                raise AssertionError(path)
            return {'items': items, 'total': len(items)}
        FakeConnection.responder = staticmethod(responder)
        api = support.PinnedAPI('unused', 'unused', 'unused', connection_type=FakeConnection)
        rules = types.SimpleNamespace(snapshot=lambda: {'version': 1})
        actual = support.current_inventory(api, previous, sessions, rules,
                   lambda *args: types.SimpleNamespace(level=3), clock=lambda: now)
        self.assertEqual(actual['clients'][0]['transition_task']['version'], 7)
        self.assertEqual(len(actual['clients']), 400)
        self.assertEqual(len(api.requests), 560)
        self.assertEqual(previous, old['inventory'])
        bad_edges[0] = True
        with self.assertRaisesRegex(ValueError, 'DEPENDENCIES_CHANGED'):
            support.current_inventory(api, previous, sessions, rules,
                lambda *args: types.SimpleNamespace(level=3), clock=lambda: now)

    def test_process_guard_refuses_active_or_unproven_and_detects_orphan_group(self):
        marker, code = 'a' * 64, 'b' * 64
        with tempfile.TemporaryDirectory() as folder:
            temp = Path(folder); proc = temp / 'proc'; proc.mkdir()
            self.assertFalse(guard.audit(marker, code, proc=proc, temp=temp)['process_exit_proven'])
            lock = temp / 'lock'; lock.write_bytes(b'')
            state = {'marker': marker, 'code_sha256': code, 'pid': 17, 'pgid': 18,
                     'start_ticks': '100', 'lock_path': str(lock)}
            (temp / ('t44-manual-material-' + marker + '.PUBLIC.json')).write_text(json.dumps(state))
            child = proc / '19'; child.mkdir()
            fields = ['S', '1', '18'] + ['0'] * 16 + ['110'] + ['0'] * 4
            (child / 'stat').write_text('19 (orphan service cli) ' + ' '.join(fields))
            self.assertEqual(guard.audit(marker, code, proc=proc, temp=temp)['status'], 'MATERIAL_GROUP_STILL_ACTIVE')
            fields[0] = 'Z'; (child / 'stat').write_text('19 (orphan service cli) ' + ' '.join(fields))
            self.assertTrue(guard.audit(marker, code, proc=proc, temp=temp)['process_exit_proven'])

    def test_same_database_material_lock_refuses_concurrent_refresh(self):
        _, auth, *_ = fixture()
        with tempfile.TemporaryDirectory() as folder:
            temp = Path(folder); proc = temp / 'proc'; (proc / 'self').mkdir(parents=True)
            fields = ['S', '1', '18'] + ['0'] * 16 + ['100'] + ['0'] * 4
            (proc / 'self/stat').write_text('17 (material process) ' + ' '.join(fields))
            with patch.object(support.sys, 'argv', ['-c', auth['packet_nonce'], 'c' * 64]):
                support.setup_material_job(auth, temp=temp, proc=proc)
            first = support.MATERIAL_LOCK_FD
            try:
                changed = {**auth, 'packet_nonce': 'd' * 64}
                with patch.object(support.sys, 'argv', ['-c', changed['packet_nonce'], 'c' * 64]):
                    with self.assertRaises(BlockingIOError):
                        support.setup_material_job(changed, temp=temp, proc=proc)
                os.close(support.MATERIAL_LOCK_FD)
            finally:
                os.close(first)


if __name__ == '__main__':
    unittest.main()
