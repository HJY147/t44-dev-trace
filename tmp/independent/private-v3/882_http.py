"""Black-box cases. All fixtures use public HTTP plus neutral account initialization."""
import concurrent.futures
import copy
import json
import threading
import uuid

def run(h, S):
    C, E, P = S.check, S.EVIDENCE, S.plan
    cases = []
    def case(name):
        def register(fn):
            cases.append((name, fn))
            return fn
        return register

    @case('F01-authentication-and-38-operation-boundary')
    def auth():
        f = h.fixture()
        for op_id in S.OPS:
            if op_id == 'login':
                h.request(op_id, auth=False, body={'username': 'iv3_absent_' + S.key(),
                    'password': 'synthetic-invalid'}, expected=401, code='INVALID_CREDENTIALS')
            else:
                h.request(op_id, auth=False, ids={'project_id': f['p'], 'task_id': 4294967295,
                    'iteration_id': f['i'], 'user_id': h.users['a'], 'dependency_id': 4294967295,
                    'assessment_id': 4294967295, 'notification_id': 4294967295},
                    body={} if 'requestBody' in S.OPS[op_id][2] else None,
                    expected=401, code='AUTH_REQUIRED')
        me = h.data('getMe', expected=200)
        C(me['id'] == h.users['m'], 'Me must report the authenticated actual user')
        dictionaries = h.data('getDictionaries', expected=200)
        C({x['value'] for x in dictionaries['task_states']} == set(range(1, 8)), 'Seven state dictionary')
        C({x['value'] for x in dictionaries['transition_actions']} == set(range(1, 10)), 'Nine action dictionary')
        # Use a distinct session so the main test actor remains usable.
        d = h.data('login', body=h.credentials['o'], auth=False, expected=200)
        h.tokens['revoked'] = d['access_token']; h.rec.secrets.append(d['access_token'])
        h.request('logout', actor='revoked', expected=200)
        h.request('getMe', actor='revoked', expected=401, code='TOKEN_REVOKED')

    @case('F02-project-isolation-current-qualification-and-service-scope')
    def isolation():
        f = h.fixture(); t = h.task(f)
        v = h.request('getTask', actor='o', ids=h.ids(f, t), expected=403, code='PROJECT_ACCESS_DENIED')
        C(v['current_version'] is None and v['current_state'] is None, 'No cross-project version/state disclosure')
        h.audit(v, 2, 'PROJECT_ACCESS_DENIED')
        h.request('getTask', ids=h.ids(f, 4294967295), expected=404, code='RESOURCE_NOT_FOUND')
        h.request('getTask', ids=h.ids(f, t), actor='a', expected=200)
        # Remove a non-owner reviewer; historical success must not bypass current project qualification.
        members = h.data('listProjectMembers', ids=h.ids(f), expected=200)['items']
        mr = next(x for x in members if x['user']['id'] == h.users['r'])
        ik = S.key(); body = {'username': h.credentials['o']['username'], 'roles': [3], 'reason': 'Synthetic join'}
        success = h.request('addProjectMember', actor='n', ids=h.ids(f), body=body, idem=ik, expected=201)
        h.request('removeProjectMember', ids=h.ids(f, user_id=h.users['r']), body={
            'expected_version': mr['version'], 'reason': 'Synthetic revoke'}, expected=200)
        h.request('listTaskReviews', actor='r', ids=h.ids(f, t), expected=403, code='PROJECT_ACCESS_DENIED')
        # Service privileges do not grant ordinary human project reads.
        svc = h.service(f['p'])
        h.request('getMe', actor=svc, expected=403, code='ACTION_FORBIDDEN')
        h.request('createEscalation', actor='m', ids=h.ids(f, t), body={
            'expected_version': t['version'], 'schedule_version': t['schedule_version'],
            'rule_version': 1, 'scan_run_id': str(uuid.uuid4())}, expected=403, code='SERVICE_SCOPE_REQUIRED')
        C(success['data']['user']['id'] == h.users['o'], 'Exact username join targets actual initialized account')

    @case('F03-input-contract-and-readonly-validation')
    def input_contract():
        f = h.fixture(); t = h.task(f)
        good = {'title': "O'Reilly SQL discussion SELECT", 'iteration_id': f['i'],
                'owner_id': h.users['a'], 'plan': P(), 'dependency_task_ids': []}
        h.request('createTask', ids=h.ids(f), body=good, expected=201)
        for field, bad in [('owner_id', True), ('owner_id', str(h.users['a'])),
                           ('state', 6), ('actor_id', h.users['m']), ('title', '')]:
            body = copy.deepcopy(good); body[field] = bad
            h.request('createTask', ids=h.ids(f), body=body, expected=422, code='PARAMETER_INVALID')
        # JSON 1.0 integer semantics use actual IDs represented as floating JSON numerals.
        body = copy.deepcopy(good); body['owner_id'] = float(h.users['a'])
        h.request('createTask', ids=h.ids(f), body=body, expected=201)
        h.request('createTask', ids=h.ids(f), raw=b'{"title":', expected=400, code='INVALID_JSON')
        h.request('createTask', ids=h.ids(f), raw=b'{' + b' ' * (1024 * 1024 + 1),
                  expected=413, code='PAYLOAD_TOO_LARGE')
        h.request('listTasks', ids=h.ids(f), query={'sort': 'id DESC; DROP TABLE tasks'},
                  expected=400, code='SECURITY_INPUT_REJECTED')
        h.request('listTasks', ids=h.ids(f), query={'page': 0}, expected=422, code='PARAMETER_INVALID')
        for bad in ['0999-01-01T00:00:00Z', '0001-01-01T00:00:00Z',
                    '2026-02-30T00:00:00Z', '2026-10-24T00:00:00+00:00',
                    '2026-10-24T00:00:00.1234567Z']:
            payload = copy.deepcopy(good); payload['plan']['planned_start'] = bad
            h.request('validateContractPayload', ids=h.ids(f), body={'category': 1, 'payload': payload},
                      expected=422, code='CONTRACT_INVALID')
        for low, high in [('1000-01-01T00:00:00Z', '1000-01-02T00:00:00Z'),
                          ('9999-12-30T00:00:00Z', '9999-12-31T23:59:59.999999Z')]:
            payload = copy.deepcopy(good); payload['plan'].update(planned_start=low, planned_end=high)
            h.request('validateContractPayload', ids=h.ids(f), body={'category': 1, 'payload': payload}, expected=200)
        reverse = copy.deepcopy(good); reverse['plan']['planned_end'] = reverse['plan']['planned_start']
        h.request('validateContractPayload', ids=h.ids(f), body={'category': 1, 'payload': reverse},
                  expected=422, code='TIME_RANGE_INVALID')
        h.request('validateContractPayload', ids=h.ids(f), body={
            'category': 2, 'task_id': t['id'], 'payload': {'expected_version': t['version'], 'action': 1}}, expected=200)
        h.request('validateContractPayload', ids=h.ids(f), body={
            'category': 3, 'task_id': t['id'], 'payload': h.assessment_body(t)}, expected=200)
        h.unchanged(f, t)

    @case('F04-blocked-provenance-four-return-states')
    def blocked():
        for target, actor in [(1, 'm'), (2, 'a'), (4, 'r'), (5, 'm')]:
            f = h.fixture(); t = h.task(f)
            if target == 2: t = h.trans(f, t, 1, actor='a')
            elif target == 4: t = h.to_review(f, t)
            elif target == 5: t = h.to_ready(f, t)
            old = copy.deepcopy(t)
            t = h.trans(f, t, 2, actor=actor, reason='Synthetic dependency blocker', responsibility_stage=5, evidence=E)
            C(t['state'] == 3 and t['blocked_from_state'] == target, 'Block must retain actual prior state')
            C(t['version'] == old['version'] + 1, 'Block increments task version exactly once')
            C(all(t[x] == old[x] for x in ('schedule_version', 'delivery_cycle', 'review_cycle')),
              'Block preserves independent counters')
            bad = {'expected_version': t['version'], 'action': 3, 'basis': 'Synthetic resolution',
                   'evidence': E, 'target_state': 6}
            h.request('transitionTask', actor=actor, ids=h.ids(f, t), body=bad,
                      expected=422, code='PARAMETER_INVALID'); h.unchanged(f, t)
            t = h.trans(f, t, 3, actor=actor, basis='Synthetic resolved evidence', evidence=E)
            C(t['state'] == target and t['blocked_from_state'] is None and t['block_reason'] is None,
              'Unblock returns only to server-recorded prior state and clears active blocker')

    @case('F05-role-ownership-illegal-state-and-rejection-audit')
    def roles():
        f = h.fixture(); t = h.task(f)
        for actor in ('m', 'b', 'r'):
            v = h.request('transitionTask', actor=actor, ids=h.ids(f, t),
                          body={'expected_version': t['version'], 'action': 1}, expected=403, code='ACTION_FORBIDDEN')
            h.audit(v, 2, 'ACTION_FORBIDDEN'); h.unchanged(f, t)
        t = h.trans(f, t, 1, actor='a')
        bad = {'expected_version': t['version'], 'action': 1}
        v = h.request('transitionTask', actor='a', ids=h.ids(f, t), body=bad, expected=409, code='STATE_CONFLICT')
        h.audit(v, 2, 'STATE_CONFLICT'); h.unchanged(f, t)
        # Direct develop->deliver is structurally valid but outside the state graph.
        v = h.request('transitionTask', ids=h.ids(f, t), body={
            'expected_version': t['version'], 'action': 7, 'assessment_id': 4294967295,
            'assessment_version': 1, 'release_version': 'synthetic', 'reason': 'Attempt forbidden jump',
            'evidence': E}, expected=409, code='STATE_CONFLICT')
        h.audit(v, 2, 'STATE_CONFLICT'); h.unchanged(f, t)
        h.request('changeTaskAssignment', ids=h.ids(f, t), body={'expected_version': t['version'],
            'owner_id': h.users['b'], 'reason': 'Forbidden after start', 'evidence': E},
            expected=409, code='ASSIGNMENT_EDIT_LOCKED'); h.unchanged(f, t)
        h.request('addTaskDependency', ids=h.ids(f, t), body={'expected_version': t['version'],
            'depends_on_task_id': h.task(f)['id'], 'reason': 'Forbidden after start'},
            expected=409, code='DEPENDENCY_EDIT_LOCKED'); h.unchanged(f, t)

    @case('F06-dependency-self-cycle-start-and-rollback-provenance')
    def dependencies():
        f = h.fixture(); a = h.task(f); b = h.task(f)
        h.request('addTaskDependency', ids=h.ids(f, a), body={'expected_version': a['version'],
            'depends_on_task_id': a['id'], 'reason': 'Self edge'}, expected=422, code='DEPENDENCY_SELF_REFERENCE')
        h.unchanged(f, a)
        h.request('addTaskDependency', ids=h.ids(f, a), body={'expected_version': a['version'],
            'depends_on_task_id': b['id'], 'reason': 'Synthetic predecessor'}, expected=201)
        a = h.get(f, a)
        h.request('addTaskDependency', ids=h.ids(f, b), body={'expected_version': b['version'],
            'depends_on_task_id': a['id'], 'reason': 'Cycle edge'}, expected=409, code='DEPENDENCY_CYCLE')
        h.unchanged(f, b)
        h.request('transitionTask', actor='a', ids=h.ids(f, a), body={
            'expected_version': a['version'], 'action': 1}, expected=409, code='DEPENDENCIES_UNSATISFIED')
        h.unchanged(f, a)
        deps = h.data('listTaskDependencies', ids=h.ids(f, a), expected=200)['items']
        C(len(deps) == 1, 'Exactly one legitimate dependency edge')
        h.request('removeTaskDependency', ids=h.ids(f, a, dependency_id=deps[0]['id']), body={
            'expected_version': a['version'], 'reason': 'Synthetic predecessor removed'}, expected=200)
        a = h.get(f, a); C(not h.data('listTaskDependencies', ids=h.ids(f, a), expected=200)['items'], 'Removal persists')
        # A delivered predecessor later rolling back must not silently rewrite downstream state.
        up, assess = h.delivered(f, b)
        down = h.task(f, deps=[up['id']]); down = h.trans(f, down, 1, actor='a')
        down = h.trans(f, down, 2, actor='a', reason='Synthetic pause', responsibility_stage=2, evidence=E)
        h.trans(f, up, 8, assessment_id=assess['id'], rollback_plan_version=assess['rollback_plan_version'],
                target_version=assess['rollback_plan']['target_version'], impact='Synthetic', reason='Synthetic', evidence=E)
        h.unchanged(f, down)
        h.request('transitionTask', actor='a', ids=h.ids(f, down), body={
            'expected_version': down['version'], 'action': 3, 'basis': 'Attempt restart', 'evidence': E},
            expected=409, code='DEPENDENCIES_UNSATISFIED'); h.unchanged(f, down)

    @case('F07-review-evidence-self-review-and-new-review-cycle')
    def review():
        f = h.fixture(); t = h.to_review(f, h.task(f))
        h.data('getReviewTemplate', ids=h.ids(f), expected=200)
        h.request('createTaskReview', actor='a', ids=h.ids(f, t), body=h.review_body(t),
                  expected=403, code='ACTION_FORBIDDEN'); h.unchanged(f, t)
        bad = h.review_body(t); bad['checklist'][0]['evidence'] = []
        h.request('createTaskReview', actor='r', ids=h.ids(f, t), body=bad,
                  expected=422, code=['PARAMETER_INVALID', 'EVIDENCE_REQUIRED']); h.unchanged(f, t)
        # Exact classification for empty evidence has overlapping schema/business descriptions;
        # acceptance still requires rejection, valid code and zero state mutation.
        h.rec.event({'kind': 'spec_classification_blocker', 'id': 'B-SPEC-01',
                     'scope': 'Exact 422 subclass for evidence caught by Schema and semantic guard'})
        duplicate = h.review_body(t); duplicate['checklist'][1] = copy.deepcopy(duplicate['checklist'][0])
        h.request('createTaskReview', actor='r', ids=h.ids(f, t), body=duplicate,
                  expected=422, code='PARAMETER_INVALID')
        prior = h.data('createTaskReview', actor='r', ids=h.ids(f, t), body=h.review_body(t), expected=201)
        t = prior['task']
        d = h.data('createTaskReview', actor='r', ids=h.ids(f, t), body=h.review_body(t, verdict=2), expected=201)
        C(d['task']['state'] == 4, 'Publishing review alone cannot change task state')
        t = h.trans(f, d['task'], 6, actor='r', review_id=d['review']['id'], review_version=1,
                    reason='Synthetic rejected review')
        C(t['review_cycle'] == 2 and t['approved_review_id'] is None and t['artifact_revision'] is None,
          'Rejected review opens a new review cycle and clears old evidence approvals')
        t = h.trans(f, t, 4, actor='a', artifact_revision=S.REVISION, evidence=E)
        h.request('transitionTask', actor='r', ids=h.ids(f, t), body={'expected_version': t['version'],
            'action': 5, 'review_id': prior['review']['id'], 'review_version': 1},
            expected=409, code='REVIEW_BASELINE_MISMATCH'); h.unchanged(f, t)
        t = h.to_ready(f, t)
        reviews = h.data('listTaskReviews', ids=h.ids(f, t), expected=200)['items']
        C(len(reviews) == 3, 'All immutable review records remain queryable across review cycles')

    @case('F08-release-assessment-approval-replan-invalidation-and-seven-states')
    def release():
        f = h.fixture(); t = h.to_ready(f, h.task(f))
        d = h.data('createReleaseAssessment', ids=h.ids(f, t), body=h.assessment_body(t), expected=201)
        t, a = d['task'], d['assessment']
        h.request('transitionTask', ids=h.ids(f, t), body={'expected_version': t['version'], 'action': 7,
            'assessment_id': a['id'], 'assessment_version': a['version'], 'release_version': 'synthetic',
            'reason': 'Unreviewed plan must not release', 'evidence': E},
            expected=409, code='RELEASE_APPROVAL_REQUIRED'); h.unchanged(f, t)
        body = {'expected_version': t['version'], 'expected_assessment_version': a['version'],
                'verdict': 1, 'reason': 'Synthetic approval', 'evidence': E}
        h.request('reviewReleaseAssessment', ids=h.ids(f, t, assessment_id=a['id']), body=body,
                  expected=403, code='ACTION_FORBIDDEN'); h.unchanged(f, t)
        d = h.data('reviewReleaseAssessment', actor='r', ids=h.ids(f, t, assessment_id=a['id']),
                   body=body, expected=200); t, a = d['task'], d['assessment']
        review_id = t['approved_review_id']
        d = h.data('changeTaskPlan', ids=h.ids(f, t), body={'expected_version': t['version'],
            'plan': P(end=86400 * 7), 'reason': 'Synthetic later plan', 'evidence': E}, expected=200)
        t = d['task']
        C(t['state'] == 5 and t['approved_review_id'] == review_id and t['approved_assessment_id'] is None,
          'Replan preserves code review and ready state while invalidating release approval')
        h.request('transitionTask', ids=h.ids(f, t), body={'expected_version': t['version'], 'action': 7,
            'assessment_id': a['id'], 'assessment_version': a['version'], 'release_version': 'synthetic',
            'reason': 'Old schedule approval', 'evidence': E}, expected=409, code='ASSESSMENT_BASELINE_MISMATCH')
        t, a2 = h.assessed(f, t)
        C(a2['rollback_plan_version'] == a['rollback_plan_version'] + 1, 'Rollback plan versions remain monotonic')
        t = h.trans(f, t, 7, assessment_id=a2['id'], assessment_version=a2['version'],
                    release_version='synthetic-release', reason='Synthetic manager decision', evidence=E)
        C(t['state'] == 6, 'Approved delivery is state 6')
        t = h.trans(f, t, 8, assessment_id=a2['id'], rollback_plan_version=a2['rollback_plan_version'],
                    target_version=a2['rollback_plan']['target_version'], impact='Synthetic impact',
                    reason='Synthetic rollback decision', evidence=E)
        C(t['state'] == 7, 'Rollback retains task in state 7')
        old = copy.deepcopy(t)
        t = h.trans(f, t, 9, new_plan=P(end=86400 * 8), reason='Synthetic rework decision', evidence=E)
        C(t['state'] == 2 and t['delivery_cycle'] == old['delivery_cycle'] + 1 and
          t['schedule_version'] == old['schedule_version'] + 1 and t['review_cycle'] == 1,
          'Rework starts new delivery and schedule cycles with review cycle reset')
        C(t['approved_review_id'] is None and t['approved_assessment_id'] is None, 'Rework clears prior approvals')
        decisions = h.data('listTaskDecisions', ids=h.ids(f, t), expected=200)['items']
        C({d['type'] for d in decisions} == {1, 2, 3}, 'Delivery rollback and rework decisions retained')
        C(all(d['decided_by'] == h.users['m'] for d in decisions), 'Actual synthetic manager ID supplies decision provenance')
        changes = h.sql('SELECT from_version,to_version,before_plan,after_plan FROM schedule_changes WHERE task_id=' + str(t['id']))
        C(len(changes) == 2, 'Replan and rework each have full persistent schedule diff')
        C(all(r['to_version'] == r['from_version'] + 1 and r['before_plan'] != r['after_plan'] for r in changes),
          'Schedule differences carry distinct before/after snapshots and consecutive schedule versions')
        h.data('listReleaseAssessments', ids=h.ids(f, t), expected=200)
        h.data('listProjectAuditEvents', ids=h.ids(f), expected=200)

    @case('F09-idempotency-snapshot-path-scope-and-persistent-provenance')
    def replay():
        f = h.fixture(); t = h.task(f); k = S.key()
        body = {'expected_version': t['version'], 'owner_id': h.users['b'], 'reason': 'Synthetic transfer', 'evidence': E}
        first = h.request('changeTaskAssignment', ids=h.ids(f, t), body=body, idem=k, expected=200)
        now = first['data']['task']
        # A newer successful task operation makes replay data observably historical.
        now = h.trans(f, now, 2, reason='Synthetic blocker', responsibility_stage=1, evidence=E)
        replay = h.request('changeTaskAssignment', ids=h.ids(f, t), body=copy.deepcopy(body), idem=k, expected=200)
        C(replay['data'] == first['data'] and replay['meta']['replayed'], 'Successful retry returns original business snapshot')
        C(replay['meta']['original_request_id'] == first['meta']['request_id'] and
          replay['meta']['request_id'] != first['meta']['request_id'], 'Replay current ID differs and original result ID is preserved')
        C(h.get(f, t) == now, 'Historical replay must not overwrite latest authoritative task')
        changed = copy.deepcopy(body); changed['reason'] = 'Different content'
        h.request('changeTaskAssignment', ids=h.ids(f, t), body=changed, idem=k,
                  expected=409, code='IDEMPOTENCY_CONTENT_CONFLICT')
        other = h.task(f)
        h.request('changeTaskAssignment', ids=h.ids(f, other), body=body, idem=k,
                  expected=409, code='IDEMPOTENCY_CONTENT_CONFLICT'); h.unchanged(f, other)
        rows = h.sql("SELECT status,response_request_id,response_body FROM idempotency_requests WHERE actor_kind=1 AND actor_id=" +
                     str(h.users['m']) + " AND operation_id='changeTaskAssignment' AND idempotency_key='" + k + "'")
        C(len(rows) == 1 and rows[0]['status'] == 2 and rows[0]['response_request_id'] == first['meta']['request_id'],
          'Completed idempotency row persists actual response-generating request ID')
        h.audit(first, 1)
        # Rejected business results must be replayable too, without retrying invalid state transitions.
        k2 = S.key(); b2 = {'expected_version': now['version'], 'action': 1}
        rejected = h.request('transitionTask', actor='b', ids=h.ids(f, now), body=b2, idem=k2,
                             expected=409, code='STATE_CONFLICT')
        h.audit(rejected, 2, 'STATE_CONFLICT')
        again = h.request('transitionTask', actor='b', ids=h.ids(f, now), body=b2, idem=k2,
                          expected=409, code='STATE_CONFLICT')
        C(again['audit_id'] == rejected['audit_id'], 'Rejected retry returns same durable rejection audit')

    @case('C01-same-task-two-keys-one-version-CAS')
    def cas():
        f = h.fixture(); t = h.task(f); barrier = threading.Barrier(2)
        def call(_):
            barrier.wait()
            return h.request('transitionTask', actor='a', ids=h.ids(f, t), body={
                'expected_version': t['version'], 'action': 1}, expected=[200, 409])
        with concurrent.futures.ThreadPoolExecutor(2) as ex: values = list(ex.map(call, range(2)))
        C(sum('data' in x for x in values) == 1, 'Two different keys holding same version permit one success')
        loser = next(x for x in values if 'code' in x)
        C(loser['code'] == 'VERSION_CONFLICT', 'CAS loser is VERSION_CONFLICT')
        winner = next(x for x in values if 'data' in x)
        h.audit(winner, 1); h.audit(loser, 2, 'VERSION_CONFLICT')
        current = h.get(f, t)
        C(current['version'] == t['version'] + 1 and current['state'] == 2, 'One durable version increment and one state transition')

    @case('C02-same-key-concurrent-replay-or-in-progress')
    def same_key():
        f = h.fixture(); t = h.task(f); barrier = threading.Barrier(2); k = S.key()
        body = {'expected_version': t['version'], 'action': 1}
        def call(_):
            barrier.wait()
            return h.request('transitionTask', actor='a', ids=h.ids(f, t), body=body, idem=k, expected=[200, 409])
        with concurrent.futures.ThreadPoolExecutor(2) as ex: values = list(ex.map(call, range(2)))
        C(any('data' in x for x in values), 'At least one original same-key request completes')
        C(all('data' in x or x['code'] == 'IDEMPOTENCY_IN_PROGRESS' for x in values), 'Concurrent same-key request never becomes stale-version failure')
        for value in values:
            if 'data' in value:
                C(value['data']['task']['version'] == t['version'] + 1, 'Same-key success snapshot version is unique')
        final = h.request('transitionTask', actor='a', ids=h.ids(f, t), body=body, idem=k, expected=200)
        C(final['meta']['replayed'], 'Later same-key request is a replay')
        C(h.get(f, t)['version'] == t['version'] + 1, 'Same-key concurrency mutates task once')

    @case('C03-two-direction-dependency-race')
    def graph_race():
        f = h.fixture(); a = h.task(f); b = h.task(f); barrier = threading.Barrier(2)
        def call(pair):
            x, y = pair; barrier.wait()
            return h.request('addTaskDependency', ids=h.ids(f, x), body={'expected_version': x['version'],
                'depends_on_task_id': y['id'], 'reason': 'Concurrent opposite edge'}, expected=[201, 409])
        with concurrent.futures.ThreadPoolExecutor(2) as ex: values = list(ex.map(call, [(a, b), (b, a)]))
        C(sum('data' in x for x in values) == 1, 'Concurrent opposite edges cannot both commit')
        C(next(x['code'] for x in values if 'code' in x) == 'DEPENDENCY_CYCLE', 'Graph race loser rejects resulting cycle')
        edges = h.sql('SELECT task_id,depends_on_task_id FROM task_dependencies WHERE project_id=' + str(f['p']))
        C(len(edges) == 1, 'Durable graph contains only one edge')

    @case('V01-create-and-transfer-require-current-iteration-capacity')
    def capacity_assignment():
        f = h.fixture(capacities=('a',))
        h.request('createTask', ids=h.ids(f), body={'title': 'Missing capacity', 'iteration_id': f['i'],
            'owner_id': h.users['b'], 'plan': P(), 'dependency_task_ids': []}, expected=422, code='CAPACITY_REFERENCE_INVALID')
        t = h.task(f)
        body = {'expected_version': t['version'], 'owner_id': h.users['b'], 'reason': 'Missing capacity', 'evidence': E}
        v = h.request('changeTaskAssignment', ids=h.ids(f, t), body=body, expected=422, code='CAPACITY_REFERENCE_INVALID')
        h.audit(v, 2, 'CAPACITY_REFERENCE_INVALID'); h.unchanged(f, t)
        h.iteration_change(f, ('a', 'b'))
        v = h.request('changeTaskAssignment', ids=h.ids(f, t), body=body, expected=200)
        C(v['data']['task']['owner_id'] == h.users['b'], 'Supplementing iteration capacity permits original legal pending transfer')
        h.iteration_change(f, ('b',))
        C({x['user_id'] for x in f['iteration']['plan']['capacity']} == {h.users['b']},
          'Legal transfer then original-owner capacity removal can both commit')

    @case('V02-state-1-through-5-capacity-protection-atomic-rejection')
    def capacity_states():
        for state in (1, 2, 3, 4, 5):
            f = h.fixture(); t = h.task(f)
            if state == 2: t = h.trans(f, t, 1, actor='a')
            elif state == 3: t = h.trans(f, t, 2, reason='Synthetic', responsibility_stage=1, evidence=E)
            elif state == 4: t = h.to_review(f, t)
            elif state == 5: t = h.to_ready(f, t)
            before = copy.deepcopy(f['iteration'])
            before_diffs = h.sql('SELECT id FROM schedule_changes WHERE iteration_id=' + str(f['i']))
            v, body = h.iteration_change(f, ('b',), expected=422)
            C(v['code'] == 'CAPACITY_REFERENCE_INVALID', 'Every in-flight state protects owner capacity')
            h.audit(v, 2, 'CAPACITY_REFERENCE_INVALID'); h.unchanged(f, t)
            its = h.data('listIterations', ids=h.ids(f), expected=200)['items']
            C(next(x for x in its if x['id'] == f['i']) == before, 'Rejected capacity change preserves full iteration/version/plan_version')
            C(h.sql('SELECT id FROM schedule_changes WHERE iteration_id=' + str(f['i'])) == before_diffs,
              'Rejected capacity change cannot leave a schedule difference')

    @case('V03-delivered-and-rolled-capacity-removal-member-protection-rework')
    def terminal_capacity():
        for state in (6, 7):
            f = h.fixture(); t = h.task(f)
            t, a = h.delivered(f, t) if state == 6 else h.rolled(f, t)
            h.iteration_change(f, ('b',))
            C(t['owner_id'] not in {x['user_id'] for x in f['iteration']['plan']['capacity']},
              'Terminal owner may leave iteration capacity')
            if state == 7:
                members = h.data('listProjectMembers', ids=h.ids(f), expected=200)['items']
                owner = next(x for x in members if x['user']['id'] == h.users['a'])
                h.request('changeProjectMember', ids=h.ids(f, user_id=h.users['a']), body={
                    'expected_version': owner['version'], 'roles': [3], 'reason': 'Attempt remove developer role'},
                    expected=409, code='MEMBER_IN_USE')
                h.request('removeProjectMember', ids=h.ids(f, user_id=h.users['a']), body={
                    'expected_version': owner['version'], 'reason': 'Attempt remove rolled owner'}, expected=409, code='MEMBER_IN_USE')
                decisions = h.sql('SELECT id FROM decisions WHERE task_id=' + str(t['id']))
                diffs = h.sql('SELECT id FROM schedule_changes WHERE task_id=' + str(t['id']))
                body = {'expected_version': t['version'], 'action': 9, 'new_plan': P(),
                        'reason': 'Synthetic rework', 'evidence': E}
                v = h.request('transitionTask', ids=h.ids(f, t), body=body, expected=422, code='CAPACITY_REFERENCE_INVALID')
                h.audit(v, 2, 'CAPACITY_REFERENCE_INVALID'); h.unchanged(f, t)
                C(h.sql('SELECT id FROM decisions WHERE task_id=' + str(t['id'])) == decisions and
                  h.sql('SELECT id FROM schedule_changes WHERE task_id=' + str(t['id'])) == diffs,
                  'Rejected rework creates no decision or plan diff')
                h.iteration_change(f, ('a', 'b'))
                t = h.request('transitionTask', ids=h.ids(f, t), body=body, expected=200)['data']['task']
                C(t['state'] == 2, 'Restored effective capacity permits unchanged valid rework request with a fresh key')

    @case('V04-capacity-race-create-transfer-rework')
    def capacity_races():
        for operation in ('create', 'transfer', 'rework'):
            for repetition in range(3):
                f = h.fixture(); t = h.task(f) if operation != 'create' else None
                if operation == 'rework':
                    t, _ = h.rolled(f, t)
                removed, kept = ('b', 'a') if operation in ('create', 'transfer') else ('a', 'b')
                barrier = threading.Barrier(2)
                def removal():
                    barrier.wait()
                    return h.iteration_change(f, (kept,), expected=[200, 422])[0]
                def activation():
                    barrier.wait()
                    if operation == 'create':
                        return h.request('createTask', ids=h.ids(f), body={'title': 'Capacity race',
                            'iteration_id': f['i'], 'owner_id': h.users[removed], 'plan': P(), 'dependency_task_ids': []}, expected=[201, 422])
                    if operation == 'transfer':
                        return h.request('changeTaskAssignment', ids=h.ids(f, t), body={'expected_version': t['version'],
                            'owner_id': h.users[removed], 'reason': 'Capacity race', 'evidence': E}, expected=[200, 422])
                    return h.request('transitionTask', ids=h.ids(f, t), body={'expected_version': t['version'],
                        'action': 9, 'new_plan': P(), 'reason': 'Capacity race', 'evidence': E}, expected=[200, 422])
                with concurrent.futures.ThreadPoolExecutor(2) as ex:
                    a, b = ex.submit(removal), ex.submit(activation)
                    values = [a.result(), b.result()]
                C(sum('data' in x for x in values) == 1, 'Competing activation/removal of same target capacity cannot both commit')
                loser = next(x for x in values if 'code' in x)
                C(loser['code'] == 'CAPACITY_REFERENCE_INVALID', 'Capacity race rejects against current protected owner/capacity')
                iterations = h.data('listIterations', ids=h.ids(f), expected=200)['items']
                capacity = next(x for x in iterations if x['id'] == f['i'])['plan']['capacity']
                owner_set = {x['user_id'] for x in capacity}
                tasks = h.data('listTasks', ids=h.ids(f), expected=200)['items']
                C(all(x['owner_id'] in owner_set for x in tasks if x['state'] in range(1, 6)),
                  'Committed in-flight tasks all retain effective iteration capacity')

    @case('V05-old-success-replay-after-capacity-removal')
    def capacity_replay():
        f = h.fixture(); t = h.task(f); k = S.key()
        original = {'expected_version': t['version'], 'owner_id': h.users['b'],
                    'reason': 'Synthetic transfer B', 'evidence': E}
        first = h.request('changeTaskAssignment', ids=h.ids(f, t), body=original, idem=k, expected=200)
        t2 = first['data']['task']
        latest = h.data('changeTaskAssignment', ids=h.ids(f, t2), body={'expected_version': t2['version'],
            'owner_id': h.users['a'], 'reason': 'Synthetic transfer back A', 'evidence': E}, expected=200)['task']
        h.iteration_change(f, ('a',))
        replay = h.request('changeTaskAssignment', ids=h.ids(f, t), body=original, idem=k, expected=200)
        C(replay['data'] == first['data'] and replay['meta']['replayed'],
          'Old success is replayed before new capacity guard despite later target capacity removal')
        C(replay['meta']['original_request_id'] == first['meta']['request_id'], 'Capacity-era replay has original result provenance')
        h.unchanged(f, latest)

    @case('V06-block-origin-and-owner-role-error-precedence')
    def capacity_block_origin():
        f = h.fixture(); t = h.task(f)
        h.request('changeTaskAssignment', ids=h.ids(f, t), body={'expected_version': t['version'],
            'owner_id': h.users['r'], 'reason': 'Reviewer has no developer role or capacity', 'evidence': E},
            expected=422, code='OWNER_NOT_PROJECT_DEVELOPER'); h.unchanged(f, t)
        t = h.trans(f, t, 2, reason='Pending blocker', responsibility_stage=1, evidence=E)
        t = h.data('changeTaskAssignment', ids=h.ids(f, t), body={'expected_version': t['version'],
            'owner_id': h.users['b'], 'reason': 'Allowed pending-origin blocker transfer', 'evidence': E}, expected=200)['task']
        C(t['state'] == 3 and t['blocked_from_state'] == 1 and t['owner_id'] == h.users['b'],
          'Pending-origin blocked task retains provenance across allowed transfer')
        t = h.trans(f, t, 3, basis='Synthetic resolution', evidence=E)
        t = h.trans(f, t, 1, actor='b')
        t = h.trans(f, t, 2, actor='b', reason='Development blocker', responsibility_stage=2, evidence=E)
        h.request('changeTaskAssignment', ids=h.ids(f, t), body={'expected_version': t['version'],
            'owner_id': h.users['a'], 'reason': 'Disallowed development-origin transfer', 'evidence': E},
            expected=409, code='ASSIGNMENT_EDIT_LOCKED'); h.unchanged(f, t)

    @case('V07-unrelated-safe-capacity-change-and-create-both-commit')
    def safe_race():
        f = h.fixture(); barrier = threading.Barrier(2)
        def change():
            barrier.wait(); return h.iteration_change(f, ('a',), expected=200)[0]
        def create():
            barrier.wait(); return h.task(f, who='a')
        with concurrent.futures.ThreadPoolExecutor(2) as ex:
            x, y = ex.submit(change), ex.submit(create)
            changed, t = x.result(), y.result()
        C(changed['data']['plan']['capacity'][0]['user_id'] == h.users['a'] and t['owner_id'] == h.users['a'],
          'Removing unused B capacity and creating an A task are independently safe and may both commit')

    @case('F10-pagination-determinism-and-member-last-manager-boundary')
    def lists():
        f = h.fixture(); ts = [h.task(f) for _ in range(4)]
        a = h.data('listTasks', ids=h.ids(f), query={'page': 1, 'page_size': 2}, expected=200)
        b = h.data('listTasks', ids=h.ids(f), query={'page': 2, 'page_size': 2}, expected=200)
        C(a['total'] == 4 and not ({x['id'] for x in a['items']} & {x['id'] for x in b['items']}),
          'Stable pagination carries total and disjoint page contents')
        h.data('listProjects', expected=200); h.data('getProject', ids=h.ids(f), expected=200)
        members = h.data('listProjectMembers', ids=h.ids(f), expected=200)['items']
        n = next(x for x in members if x['user']['id'] == h.users['n'])
        h.request('removeProjectMember', ids=h.ids(f, user_id=h.users['n']), body={
            'expected_version': n['version'], 'reason': 'Remove second manager'}, expected=200)
        m = next(x for x in members if x['user']['id'] == h.users['m'])
        h.request('removeProjectMember', ids=h.ids(f, user_id=h.users['m']), body={
            'expected_version': m['version'], 'reason': 'Attempt last manager removal'}, expected=409, code='LAST_MANAGER')
        h.request('addProjectMember', ids=h.ids(f), body={'username': 'iv3_missing_' + S.key(),
            'roles': [2], 'reason': 'Unknown initialized account'}, expected=422, code='ACCOUNT_NOT_INITIALIZED')

    @case('F11-escalation-ledger-dedup-recipients-read-handle')
    def escalation():
        f = h.fixture(); s = h.service(f['p'])
        rules = h.data('getEscalationRules', ids=h.ids(f), expected=200)
        # The schema freezes rule.version; the test uses the actually declared version.
        version = rules['version']
        t = h.task(f, timing=P(start=-86400 * 3, end=-3600))
        def call(t, **extra):
            return h.request('createEscalation', actor=s, ids=h.ids(f, t), expected=202, body={
                'expected_version': t['version'], 'schedule_version': t['schedule_version'],
                'rule_version': version, 'scan_run_id': str(uuid.uuid4()), **extra})
        first = call(t); event = first['data']['event']
        C(first['data']['created'] and event['level'] == 2, 'First overdue call creates only current highest level')
        C(set(event['recipient_ids']) == {h.users['a'], h.users['m'], h.users['n']},
          'Overdue event snapshots owner and all active managers without duplication')
        current = h.get(f, t)
        C(current['escalation_count'] == t['escalation_count'] + 1 and current['version'] == t['version'] + 1,
          'New event increments task version and escalation count atomically once')
        again = call(current)
        C(not again['data']['created'] and again['data']['event']['id'] == event['id'],
          'Same schedule/level with fresh key returns original business event')
        h.unchanged(f, current)
        rows = h.sql('SELECT event_id FROM escalation_events WHERE task_id=' + str(t['id']))
        C(len(rows) == 1, 'Exactly one durable escalation ledger')
        outbox_id = rows[0]['event_id']
        def notices():
            rows = h.sql('SELECT id,recipient_id,fallback,version,read_at,handled_at FROM notifications WHERE event_id=' + str(outbox_id))
            return rows if len(rows) == 3 else None
        ns = h.wait(notices, seconds=60)
        C({x['recipient_id'] for x in ns} == set(event['recipient_ids']), 'Durable notices reach full recipient snapshot')
        page = h.data('listMyNotifications', actor='a', query={'project_id': f['p']}, expected=200)
        n = next(x for x in page['items'] if x['event_id'] == outbox_id)
        h.request('markNotificationRead', actor='b', ids=h.ids(f, notification_id=n['id']),
                  body={'expected_version': n['version']}, expected=403, code='ACTION_FORBIDDEN')
        read = h.data('markNotificationRead', actor='a', ids=h.ids(f, notification_id=n['id']),
                      body={'expected_version': n['version']}, expected=200)
        C(read['read_at'] is not None and read['handled_at'] is None, 'Read is distinct from handling')
        handled = h.data('handleNotification', actor='a', ids=h.ids(f, notification_id=n['id']), body={
            'expected_version': read['version'], 'note': 'Synthetic disposition', 'evidence': E}, expected=200)
        C(handled['handled_at'] is not None, 'Handling records separate completion')
        h.unchanged(f, current)
        history = h.data('listEscalations', ids=h.ids(f), query={'task_id': t['id']}, expected=200)['items']
        C(len(history) == 1 and history[0]['handled_count'] == 1, 'Escalation history reflects distinct handled recipient count')

    @case('F12-all-body-operations-malformed-json-and-payload-limit')
    def general_body_errors():
        f = h.fixture(); t = h.task(f); svc = h.service(f['p'])
        ids = h.ids(f, t, iteration_id=f['i'], user_id=h.users['b'], dependency_id=4294967295,
                    assessment_id=4294967295, notification_id=4294967295)
        for op_id, (_, _, op) in S.OPS.items():
            if 'requestBody' not in op: continue
            actor = svc if op_id == 'createEscalation' else 'm'
            h.request(op_id, actor=actor, ids=ids, raw=b'{"incomplete":',
                      expected=400, code='INVALID_JSON', auth=op_id != 'login')
            h.request(op_id, actor=actor, ids=ids, raw=b'{' + b' ' * (1024 * 1024 + 1),
                      expected=413, code='PAYLOAD_TOO_LARGE', auth=op_id != 'login')
        h.unchanged(f, t)

    @case('F13-paginated-operations-parameter-boundaries')
    def pagination_errors():
        f = h.fixture(); t = h.task(f)
        ids = h.ids(f, t)
        for op_id, (_, _, op) in S.OPS.items():
            parameters = [S.CONTRACT['components']['parameters'][p['$ref'].split('/')[-1]]
                          if '$ref' in p else p for p in op.get('parameters', [])]
            if any(p.get('name') == 'page_size' for p in parameters):
                h.request(op_id, ids=ids, query={'page_size': 101}, expected=422, code='PARAMETER_INVALID')
                h.request(op_id, ids=ids, query={'page': 0}, expected=422, code='PARAMETER_INVALID')

    @case('F14-frozen-storage-types-password-and-token-observation')
    def storage():
        expected = json.loads((S.HERE / 'storage-expectations.json').read_text())
        rows = h.sql('SELECT TABLE_NAME AS table_name,COLUMN_NAME AS column_name,COLUMN_TYPE AS column_type,'
                     'IS_NULLABLE AS is_nullable,COLUMN_KEY AS column_key,EXTRA AS extra '
                     'FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=DATABASE() ORDER BY TABLE_NAME,ORDINAL_POSITION')
        actual = {(r['table_name'], r['column_name']): r for r in rows}
        for table, columns in expected.items():
            for col in columns:
                r = actual.get((table, col['name']))
                C(r is not None, 'Frozen table/column exists: ' + table + '.' + col['name'])
                C(r['column_type'].lower() == col['type'], 'Frozen minimal SQL type matches: ' + table + '.' + col['name'])
                C(r['is_nullable'] == col['nullable'], 'Frozen nullability matches: ' + table + '.' + col['name'])
                if col['name'] == 'id':
                    C(r['column_key'] == 'PRI' and 'auto_increment' in r['extra'], 'Every frozen table has unified unsigned auto-increment primary key')
        C(sum(len(v) for v in expected.values()) == 226 and len(expected) == 18, 'Frozen storage set is 18 tables / 226 columns')
        user_sql = ','.join(str(v) for v in h.users.values())
        hashes = h.sql('SELECT id,password_hash FROM users WHERE id IN (' + user_sql + ')')
        C(all(r['password_hash'].startswith('$argon2id$') for r in hashes), 'Initialized accounts contain Argon2id encodings only')
        sessions = h.sql('SELECT HEX(token_hash) AS digest FROM auth_sessions WHERE user_id IN (' + user_sql + ')')
        stored = {r['digest'].lower() for r in sessions}
        C(all(S.hashlib.sha256(v.encode()).hexdigest() in stored for k, v in h.tokens.items() if k in h.users),
          'Human tokens are durably stored as SHA256 digest rather than reversible bearer text')
        # This SELECT observation does not execute or validate the private hash-only write boundary.

    @case('F15-short-service-session-expiry')
    def service_expiry():
        import time
        f = h.fixture(); t = h.task(f)
        svc = h.service(f['p'], label='expired_service', ttl=60)
        # Thirteen bounded sleeps are an explicit TTL wait, not performance measurement.
        for _ in range(13): time.sleep(5)
        h.request('createEscalation', actor=svc, ids=h.ids(f, t), body={
            'expected_version': t['version'], 'schedule_version': t['schedule_version'],
            'rule_version': 1, 'scan_run_id': str(uuid.uuid4())}, expected=401, code='TOKEN_EXPIRED')
        h.unchanged(f, t)

    @case('F16-escalation-windows-terminal-and-version-guards')
    def escalation_windows():
        f = h.fixture(); svc = h.service(f['p'], label='window_service')
        for end, level in [(3600, 1), (-172800, 3)]:
            t = h.task(f, timing=P(start=-259200, end=end))
            d = h.data('createEscalation', actor=svc, ids=h.ids(f, t), expected=202, body={
                'expected_version': t['version'], 'schedule_version': t['schedule_version'],
                'rule_version': 1, 'scan_run_id': str(uuid.uuid4())})
            C(d['created'] and d['event']['level'] == level, 'Current highest eligible window is selected without catch-up event flood')
            expected_people = {h.users['a']} if level == 1 else {h.users['a'], h.users['m'], h.users['n']}
            C(set(d['event']['recipient_ids']) == expected_people, 'Window-specific owner/manager recipient snapshot')
            rows = h.sql('SELECT level FROM escalation_events WHERE task_id=' + str(t['id']))
            C(len(rows) == 1 and rows[0]['level'] == level, 'First severe detection does not backfill lower upgrade levels')
            latest = h.get(f, t)
            for field, bad, code in [('expected_version', t['version'], 'VERSION_CONFLICT'),
                                      ('schedule_version', latest['schedule_version'] + 1, 'SCHEDULE_VERSION_CONFLICT'),
                                      ('rule_version', 2, 'RULE_VERSION_CONFLICT')]:
                b = {'expected_version': latest['version'], 'schedule_version': latest['schedule_version'],
                     'rule_version': 1, 'scan_run_id': str(uuid.uuid4())}; b[field] = bad
                h.request('createEscalation', actor=svc, ids=h.ids(f, t), body=b, expected=409, code=code)
                h.unchanged(f, latest)
        for timing in [P(end=86400 * 5), P(planned_start='9999-12-30T00:00:00Z', planned_end='9999-12-31T23:59:59.999999Z')]:
            t = h.task(f, timing=timing)
            h.request('createEscalation', actor=svc, ids=h.ids(f, t), body={
                'expected_version': t['version'], 'schedule_version': t['schedule_version'],
                'rule_version': 1, 'scan_run_id': str(uuid.uuid4())}, expected=409, code='NOT_ELIGIBLE_FOR_ESCALATION')
            h.unchanged(f, t)
        terminal, _ = h.delivered(f, h.task(f))
        h.request('createEscalation', actor=svc, ids=h.ids(f, terminal), body={
            'expected_version': terminal['version'], 'schedule_version': terminal['schedule_version'],
            'rule_version': 1, 'scan_run_id': str(uuid.uuid4())}, expected=409, code='NOT_ELIGIBLE_FOR_ESCALATION')
        h.unchanged(f, terminal)

    for name, fn in cases:
        h.rec.run(name, fn)
    return [name for name, _ in cases]
