"""Offline fake-API checks. Does not connect, create tokens or modify product tests."""
import importlib.util
import json
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location('maintenance', Path(__file__).with_name('restore_transition_cohort.py'))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class Fake:
    def __init__(self, bad=None):
        self.tasks = {i: {'id': i, 'project_id': 1, 'owner_id': 7, 'state': 3 if i <= 138 else 2,
                          'blocked_from_state': 2 if i <= 138 else None, 'version': 99}
                      for i in range(1, 401)}
        if bad == 'state':
            self.tasks[400]['state'] = 4
        if bad == 'owner':
            self.tasks[400]['owner_id'] = 8
        self.calls, self.posts = [], []

    def request(self, path, token=None, body=None):
        self.calls.append(path)
        if path == '/auth/login':
            return {'user': {'id': 7}, 'access_token': 'fake-secret', 'expires_at': '2099-01-01T00:00:00Z'}
        tid = int(path.split('/')[4])
        if body:
            self.posts.append((tid, body))
            assert body['expected_version'] == self.tasks[tid]['version']
            assert body['action'] == 3 and body['basis'] == m.BASIS and body['evidence'] == m.EVIDENCE
            self.tasks[tid].update(state=2, blocked_from_state=None, version=100)
            return {'task': dict(self.tasks[tid]), 'audit_id': tid}
        return dict(self.tasks[tid])


class Checks(unittest.TestCase):
    def run_fake(self, bad=None):
        api = Fake(bad)
        summary = {'unblocked': 0, 'skipped_state2': 0, 'preflight_gets': 0, 'final_state2_gets': 0}
        rows = []
        return api, summary, rows

    def test_original400_only138_unblock_and_final400(self):
        api, summary, rows = self.run_fake()
        m.restore(api, [(1, i) for i in range(1,401)], {'user_id': 7, 'username':'dev', 'password':'fake-password'}, rows.append, summary)
        self.assertEqual(summary['unblocked'], 138)
        self.assertEqual(summary['skipped_state2'], 262)
        self.assertEqual(summary['final_state2_gets'], 400)
        self.assertEqual(len(api.calls),939)
        self.assertEqual(summary['status'], 'COMPLETE_EXISTING_400_STATE2')
        self.assertEqual(len(rows),938)
        self.assertNotIn('fake-secret', json.dumps(rows))
        self.assertNotIn('fake-password', json.dumps(rows))
        self.assertTrue(all(t['state'] == 2 for t in api.tasks.values()))

    def test_bad_last_state_or_owner_prevents_every_write(self):
        for bad in ('state','owner'):
            with self.subTest(bad=bad):
                api, summary, rows = self.run_fake(bad)
                with self.assertRaises(m.Refused):
                    m.restore(api, [(1,i) for i in range(1,401)], {'user_id':7,'username':'dev','password':'fake'}, rows.append,summary)
                self.assertEqual(api.posts,[])
                self.assertTrue(summary['login_issued'])

    def test_unknown_write_not_retried(self):
        api, summary, rows = self.run_fake()
        original = api.request
        def unknown(path, token=None, body=None):
            if body and path != '/auth/login':
                api.posts.append((1,body))
                raise m.Refused('HTTP_OUTCOME_UNKNOWN_STOP_NO_RETRY')
            return original(path, token, body)
        api.request = unknown
        with self.assertRaisesRegex(m.Refused, 'HTTP_OUTCOME_UNKNOWN'):
            m.restore(api, [(1,i) for i in range(1,401)], {'user_id':7,'username':'dev','password':'fake'},rows.append,summary)
        self.assertEqual(len(api.posts),1)
        self.assertEqual(summary['unblocked'],0)

    def test_targets_exact400_unique_scope(self):
        api=Fake()
        packet={'environment':{'origin':'https://'+m.HOST},'sessions':{'developer':{'user_id':7}},'inventory':{'clients':[{'project_id':1,'transition_task':t} for t in api.tasks.values()]}}
        self.assertEqual(len(m.targets(packet,{'user_id':7})),400)
        packet['inventory']['clients'][-1] = packet['inventory']['clients'][0]
        with self.assertRaisesRegex(m.Refused,'DUPLICATE'):
            m.targets(packet,{'user_id':7})


if __name__ == '__main__':
    unittest.main()
