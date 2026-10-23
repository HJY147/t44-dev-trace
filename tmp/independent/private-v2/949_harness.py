#!/usr/bin/env python3
"""Independent frozen blackbox harness. No application imports; execute only after exact SUT binding."""
from __future__ import annotations
import concurrent.futures as cf
import copy
import datetime as dt
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import secrets
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request

HERE = Path(__file__).resolve().parent
CASES = json.loads((HERE / '950_cases.json').read_text())
SPEC = json.loads(CASES['contract_text'])
OPS = {o['operationId']: (method.upper(), path, o) for path, item in SPEC['paths'].items() for method, o in item.items() if isinstance(o, dict) and 'operationId' in o}
EVIDENCE = [{'kind': 2, 'locator': 'synthetic/independent-v2/evidence', 'description': 'Synthetic acceptance evidence; no real production authorization claimed'}]
ARTIFACT = 'b7' * 20
UTC = dt.timezone.utc

class Blocked(Exception): pass
class SetupFailed(Exception): pass

def utc(value):
    return value.astimezone(UTC).isoformat(timespec='microseconds').replace('+00:00', 'Z')

def plan(end=None):
    end = end or dt.datetime.now(UTC) + dt.timedelta(days=7)
    return {'planned_start': utc(end-dt.timedelta(days=1)), 'planned_end': utc(end), 'estimated_hours': 8, 'buffer_hours': 2, 'delay_contingency': 'Manager records a synthetic replanning decision with old/new evidence'}

def digest(v):
    return hashlib.sha256(json.dumps(v, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()

class Harness:
    def __init__(self, context):
        self.context = context
        self.product_sha = context.get('product_source_sha', '')
        if not re.fullmatch('[0-9a-f]{40}', self.product_sha): raise Blocked('Missing immutable product_source_sha')
        self.base = context['api_base_url'].rstrip('/')
        if not self.base.endswith('/api/v1'): self.base += '/api/v1'
        self.out = Path(context['harness_output_directory'])
        self.out.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.out.chmod(0o700)
        self.events = self.out/'events.jsonl'
        self.lock = threading.RLock()
        self.secrets = []
        self.results = []
        self.coverage = set()
        self.positive = set()
        self.canonical = {}
        self.prefix = 'iav2_'+secrets.token_hex(4)
        self.actor = {}
        try:
            from jsonschema import Draft202012Validator, FormatChecker
        except ImportError as e: raise Blocked('Locked runtime must contain jsonschema with Draft202012Validator') from e
        self.validator = Draft202012Validator
        self.format_checker = FormatChecker()
        self.ids = {}
        self.http_aggregates = {}
        self.phase = context.get('independent_phase') or os.environ.get('T44_INDEPENDENT_PHASE','blackbox')

    def redact(self, value):
        if isinstance(value, dict):
            return {k: ('<redacted>' if re.search(r'password|token|authorization|credential|secret|cookie', k, re.I) else self.redact(v)) for k,v in value.items()}
        if isinstance(value, list): return [self.redact(x) for x in value]
        if isinstance(value, str):
            for sec in self.secrets:
                if sec: value = value.replace(sec, '<redacted>')
            return value
        return value

    def log(self, kind, **data):
        record = {'time': utc(dt.datetime.now(UTC)), 'kind': kind, 'product_sha': self.product_sha, **data}
        with self.lock:
            if kind=='http' and self.phase=='performance' and data.get('status',500)<300:
                name=data['operation'];a=self.http_aggregates.setdefault(name,{'count':0,'sum_ms':0.0,'hash_chain':'0'*64})
                a['count']+=1;a['sum_ms']+=data.get('elapsed_ms',0.0)
                a['hash_chain']=hashlib.sha256((a['hash_chain']+json.dumps(self.redact(record),sort_keys=True,separators=(',',':'))).encode()).hexdigest()
                return
            with self.events.open('a', encoding='utf-8') as f: f.write(json.dumps(self.redact(record), ensure_ascii=False, separators=(',', ':'))+'\n')

    def control(self, args, stdin='', timeout=160):
        py = self.context.get('python')
        ctl = self.context.get('control_cli')
        if not py or not ctl: raise Blocked('Neutral control_cli/python missing')
        env = dict(os.environ)
        if self.context.get('control_state'): env['T44_ACCEPTANCE_STATE'] = self.context['control_state']
        r = subprocess.run([py, ctl, *args], input=stdin, text=True, capture_output=True, timeout=timeout, env=env)
        # stdout may contain initialized session credentials; never emit raw control output.
        self.log('control', argv=[str(x) for x in args], exit_code=r.returncode, stdout_sha256=hashlib.sha256(r.stdout.encode()).hexdigest(), stderr_sha256=hashlib.sha256(r.stderr.encode()).hexdigest())
        if r.returncode: raise Blocked('Neutral control failed: '+str(args[:2])+' exit '+str(r.returncode))
        return r.stdout

    def audit(self, sql):
        if not re.match(r'^\s*(SELECT|SHOW|EXPLAIN)\b', sql, re.I): raise ValueError('SELECT/SHOW/EXPLAIN only')
        out = self.control(['audit-sql'], stdin=sql+'\n')
        self.log('readonly_sql', sql=sql, output=out)
        try: return json.loads(out)
        except json.JSONDecodeError: return {'unparsed': out}

    def validate(self, schema, value):
        full = {'$schema': 'https://json-schema.org/draft/2020-12/schema', 'components': SPEC['components'], **schema}
        issues = sorted(self.validator(full, format_checker=self.format_checker).iter_errors(value), key=lambda e: str(list(e.absolute_path)))
        assert not issues, 'Response Schema mismatch: '+ '; '.join(str(list(e.absolute_path))+': '+e.message[:240] for e in issues[:8])

    def call(self, name, who='manager', params=None, body=None, expected=None, code=None, key=None, raw=None, token_override=None, query=None, check_schema=True):
        method, path, op = OPS[name]
        params = {**self.ids, **(params or {})}
        for k,v in params.items(): path = path.replace('{'+k+'}', urllib.parse.quote(str(v), safe=''))
        if '{' in path: raise SetupFailed('Unbound path: '+path)
        url = self.base+path
        if query: url += '?'+urllib.parse.urlencode(query)
        headers = {'Accept':'application/json','X-Request-ID':self.prefix+'-'+secrets.token_hex(8)}
        token = self.actor.get(who,{}).get('access_token') if token_override is None else token_override
        if token: headers['Authorization'] = 'Bearer '+token
        has_idem = any(p.get('$ref','').endswith('/IdempotencyKey') for p in op.get('parameters',[]))
        if has_idem: headers['Idempotency-Key'] = key or self.prefix+'-'+secrets.token_hex(12)
        data = raw if raw is not None else (json.dumps(body, ensure_ascii=False, separators=(',',':')).encode() if body is not None else None)
        if data is not None: headers['Content-Type']='application/json'
        request = urllib.request.Request(url, data=data, headers=headers, method=method)
        started = time.perf_counter()
        try:
            with urllib.request.urlopen(request, timeout=35) as response:
                status, response_headers, payload = response.status, dict(response.headers), response.read()
        except urllib.error.HTTPError as e: status, response_headers, payload = e.code, dict(e.headers), e.read()
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            self.log('transport_error', operation=name, request_id=headers['X-Request-ID'], elapsed_ms=(time.perf_counter()-started)*1000, error=type(e).__name__)
            raise AssertionError('HTTP transport failed: '+type(e).__name__) from e
        elapsed = (time.perf_counter()-started)*1000
        try: value=json.loads(payload)
        except Exception as e:
            self.log('non_json_response', operation=name, status=status, payload_sha256=hashlib.sha256(payload).hexdigest(), elapsed_ms=elapsed)
            raise AssertionError('Expected JSON contract response; status='+str(status)) from e
        self.log('http', operation=name, method=method, path=path, query=query, actor=who, status=status, request_id=headers['X-Request-ID'], body_sha256=hashlib.sha256(data or b'').hexdigest(), idempotency_key=headers.get('Idempotency-Key'), response=value, elapsed_ms=elapsed, retry_after=response_headers.get('Retry-After'))
        if str(status) not in op['responses']: raise AssertionError('Undeclared HTTP '+str(status)+' for '+name)
        if check_schema: self.validate(op['responses'][str(status)]['content']['application/json']['schema'], value)
        if expected is not None: assert status in (expected if isinstance(expected,(list,tuple,set)) else [expected]), name+' expected '+str(expected)+' got '+str(status)+' '+str(value.get('code'))
        if code: assert value.get('code')==code, name+' expected '+code+' got '+str(value.get('code'))
        if status<300:
            self.positive.add(name)
            if name != 'login':
                self.canonical[name]={'who':who,'params':copy.deepcopy(params),'body':copy.deepcopy(body),'query':copy.deepcopy(query),'key':headers.get('Idempotency-Key')}
        else:
            self.coverage.add((name,value.get('code')))
            if status<500:assert value.get('audit_id') is not None, 'Ordinary rejection lacks durable-audit reference'
            if value.get('code')=='AUDIT_UNAVAILABLE':assert value.get('audit_id') is None, 'Unavailable audit falselyclaimsID'
            assert not any(sec and sec.encode() in payload for sec in self.secrets), 'Credential leaked in error'
            if status in (401,403):
                assert value.get('current_version') is None and value.get('current_state') is None, 'Unauthorized resource version leak'
        return status,value,response_headers

    def data(self,*a,**kw): return self.call(*a,**kw)[1]['data']
    def task(self, tid): return self.data('getTask',params={'task_id':tid})
    def mutation(self,name,tid,body,who='manager',**kw):
        current=self.task(tid)
        body={'expected_version':current['version'],**body}
        return self.data(name,who,params={'task_id':tid},body=body,expected=kw.pop('expected',200),**kw)
    def transition(self,tid,action,who='developer_a',**extra):
        return self.mutation('transitionTask',tid,{'action':action,**extra},who)

    def run(self,case,fn):
        before=time.monotonic()
        try:
            fn(); outcome='PASS'; detail='All executed frozen assertions passed'
        except Blocked as e: outcome='BLOCKED'; detail=str(e)
        except SetupFailed as e: outcome='SETUP_FAILED'; detail=str(e)
        except AssertionError as e: outcome='FAIL'; detail=str(e)
        except Exception as e: outcome='HARNESS_ERROR'; detail=type(e).__name__+': '+str(e)[:500]
        self.results.append({'case_id':case,'outcome':outcome,'detail':self.redact(detail),'elapsed_s':time.monotonic()-before})
        self.log('case',**self.results[-1])
        return outcome

    def init_user(self, label, roles):
        username=self.prefix+'_'+label
        password='Iv2!'+secrets.token_urlsafe(25)
        self.secrets.append(password)
        self.control(['init-user','--username',username,'--display-name','Synthetic independent '+label],password+'\n')
        login=self.data('login',who='none',body={'username':username,'password':password},expected=200,token_override='')
        self.secrets.append(login['access_token'])
        self.actor[label]={**login,'username':username,'password':password}
        if roles:
            self.data('addProjectMember',body={'username':username,'roles':roles,'reason':'Synthetic independent fixture'},expected=201)
        return login['user']['id']

    def setup(self):
        credentials=json.loads(Path(self.context['manager_credentials_file']).read_text())
        if isinstance(credentials.get('credentials'),dict): credentials={**credentials,**credentials['credentials']}
        username=credentials.get('username')
        password=credentials.get('password')
        if password:self.secrets.append(password)
        token=credentials.get('access_token') or credentials.get('token')
        if isinstance(credentials.get('session'),dict): token=token or credentials['session'].get('access_token') or credentials['session'].get('token')
        if username and password:
            auth=self.data('login',who='none',body={'username':username,'password':password},expected=200,token_override='')
        elif token:
            self.secrets.append(token);self.actor['manager']={'access_token':token}
            user=self.data('getMe',expected=200);auth={'access_token':token,'user':user}
        else: raise Blocked('manager_credentials_file lacks supported username/password or access_token keys')
        self.actor['manager']={**auth,'username':username,'password':password}
        self.secrets.append(auth['access_token'])
        self.data('getMe',expected=200)
        dictionaries=self.data('getDictionaries',expected=200)
        assert {x['value'] for x in dictionaries['task_states']}==set(range(1,8))
        p=self.data('createProject',body={'name':self.prefix,'description':"O'Brien's normal SQL discussion SELECT is valid text"},expected=201)
        self.ids['project_id']=p['id']
        self.ids['manager_id']=auth['user']['id']
        self.data('listProjects',expected=200)
        self.data('getProject',expected=200)
        for label,roles in [('developer_a',[2]),('developer_b',[2]),('reviewer',[3]),('manager_b',[1]),('outsider',[])]: self.ids[label]=self.init_user(label,roles)
        self.data('listProjectMembers',expected=200)
        self.iteration=self.new_iteration([self.ids['developer_a'],self.ids['developer_b']])
        self.ids['iteration_id']=self.iteration['id']
        self.data('listIterations',expected=200)
        self.template=self.data('getReviewTemplate',expected=200)
        self.rules=self.data('getEscalationRules',expected=200)
        self.data('listEscalations',expected=200)
        self.data('listMyNotifications',expected=200)
        self.data('listProjectAuditEvents',expected=200)

    def new_iteration(self,owners):
        pl=plan(); payload={'name':self.prefix+'-I','planned_start':pl['planned_start'],'planned_end':pl['planned_end'],'capacity':[{'user_id':i,'available_hours':40} for i in owners],'buffer_hours':2,'delay_contingency':'Synthetic test contingency'}
        return self.data('createIteration',body=payload,expected=201)

    def new_task(self,owner=None,deps=None,iteration=None,end=None):
        return self.data('createTask',body={'title':self.prefix+'-T-'+secrets.token_hex(3),'description':'Synthetic independent task','iteration_id':iteration or self.ids['iteration_id'],'owner_id':owner or self.ids['developer_a'],'plan':plan(end),'dependency_task_ids':deps or []},expected=201)

    def to_review(self,t):
        tid=t['id'];self.transition(tid,1);self.transition(tid,4,artifact_revision=ARTIFACT,evidence=EVIDENCE)
        return self.task(tid)

    def review_payload(self,t,verdict=1):
        return {'expected_version':t['version'],'template_version':self.template['version'],'artifact_revision':ARTIFACT,'sections':[{'section_id':x['section_id'],'content':'Independent synthetic evidence for '+x['section_id'],'evidence':EVIDENCE} for x in self.template['sections']],'checklist':[{'item_id':x['item_id'],'judgment':1 if verdict==1 else 2,'rationale':'Synthetic controlled acceptance judgment','evidence':EVIDENCE} for x in self.template['items']],'verdict':verdict}

    def publish_review(self,tid,verdict=1):
        return self.data('createTaskReview','reviewer',params={'task_id':tid},body=self.review_payload(self.task(tid),verdict),expected=201)

    def to_release(self,t):
        self.to_review(t);review=self.publish_review(t['id'])['review'];self.transition(t['id'],5,'reviewer',review_id=review['id'],review_version=review['version'])
        return self.task(t['id'])

    def assessment_payload(self,t):
        return {'expected_version':t['version'],'risks':[{'perspective':p,'severity':2,'risk':'Synthetic risk '+str(p),'mitigation':'Synthetic mitigation','evidence':EVIDENCE} for p in range(1,5)],'rollback_plan':{'target_version':'synthetic-previous','trigger':'Synthetic acceptance failure','steps':['Record synthetic decision','Verify synthetic target'],'impact':'Synthetic no customer impact','verification':'Read synthetic history and state','responsible_user_id':self.ids['manager_id'],'evidence':EVIDENCE}}

    def assessment(self,tid,approve=True):
        a=self.data('createReleaseAssessment',params={'task_id':tid},body=self.assessment_payload(self.task(tid)),expected=201)['assessment']
        if approve:
            a=self.data('reviewReleaseAssessment','reviewer',params={'task_id':tid,'assessment_id':a['id']},body={'expected_version':self.task(tid)['version'],'expected_assessment_version':a['version'],'verdict':1,'reason':'Synthetic independent assessment review','evidence':EVIDENCE},expected=200)['assessment']
        return a

    def deliver(self,t):
        self.to_release(t);a=self.assessment(t['id'])
        self.transition(t['id'],7,'manager',assessment_id=a['id'],assessment_version=a['version'],release_version='synthetic-current',reason='Synthetic manager acceptance fixture decision',evidence=EVIDENCE)
        return a

    def rollback(self,t,a):
        self.transition(t['id'],8,'manager',reason='Synthetic rollback exercise',impact='Synthetic only',target_version=a['rollback_plan']['target_version'],assessment_id=a['id'],rollback_plan_version=a['rollback_plan_version'],evidence=EVIDENCE)

    def assert_unchanged(self,before,tid): assert self.task(tid)==before, 'Rejected request mutated task'

    def core_lifecycle(self):
        t=self.new_task();tid=t['id'];start=self.transition(tid,1)['task'];assert start['state']==2 and start['version']==t['version']+1
        blocked=self.transition(tid,2,reason='Synthetic blocker',responsibility_stage=5,evidence=EVIDENCE)['task'];assert blocked['state']==3 and blocked['blocked_from_state']==2
        unblocked=self.transition(tid,3,basis='Synthetic dependency proof',evidence=EVIDENCE)['task'];assert unblocked['state']==2 and unblocked['review_cycle']==1
        self.transition(tid,4,artifact_revision=ARTIFACT,evidence=EVIDENCE)
        reject=self.publish_review(tid,2)['review'];self.transition(tid,6,'reviewer',review_id=reject['id'],review_version=reject['version'],reason='Synthetic review rejection')
        assert self.task(tid)['review_cycle']==2
        self.transition(tid,4,artifact_revision=ARTIFACT,evidence=EVIDENCE)
        approve=self.publish_review(tid)['review'];self.transition(tid,5,'reviewer',review_id=approve['id'],review_version=approve['version'])
        a=self.assessment(tid);self.transition(tid,7,'manager',assessment_id=a['id'],assessment_version=a['version'],release_version='synthetic-v2',reason='Synthetic fixture decision',evidence=EVIDENCE)
        self.rollback(t,a);before=self.task(tid);assert before['state']==7
        self.transition(tid,9,'manager',new_plan=plan(),reason='Synthetic manager rework decision',evidence=EVIDENCE)
        after=self.task(tid);assert after['state']==2 and after['delivery_cycle']==before['delivery_cycle']+1 and after['schedule_version']==before['schedule_version']+1 and after['review_cycle']==1
        assert after['approved_review_id'] is None and after['approved_assessment_id'] is None
        for name in ['listTaskReviews','listReleaseAssessments','listTaskDecisions','listTaskDependencies']: self.data(name,params={'task_id':tid},expected=200)
        self.log('lifecycle_snapshots',before_rework=before,after_rework=after)

    def dependencies(self):
        a,b=self.new_task(),self.new_task();tid=a['id']
        before=self.task(tid)
        self.call('addTaskDependency',params={'task_id':tid},body={'expected_version':before['version'],'depends_on_task_id':tid,'reason':'Synthetic self edge'},expected=422,code='DEPENDENCY_SELF_REFERENCE');self.assert_unchanged(before,tid)
        m=self.mutation('addTaskDependency',tid,{'depends_on_task_id':b['id'],'reason':'Synthetic edge'})
        self.call('transitionTask','developer_a',params={'task_id':tid},body={'expected_version':self.task(tid)['version'],'action':1},expected=409,code='DEPENDENCIES_UNSATISFIED')
        bb=self.task(b['id']);self.call('addTaskDependency',params={'task_id':b['id']},body={'expected_version':bb['version'],'depends_on_task_id':tid,'reason':'Synthetic cycle'},expected=409,code='DEPENDENCY_CYCLE');self.assert_unchanged(bb,b['id'])
        self.data('removeTaskDependency',params={'task_id':tid,'dependency_id':m['dependency']['id']},body={'expected_version':self.task(tid)['version'],'reason':'Synthetic remove'},expected=200)
        self.transition(tid,1);before=self.task(tid)
        self.call('addTaskDependency',params={'task_id':tid},body={'expected_version':before['version'],'depends_on_task_id':b['id'],'reason':'Synthetic locked'},expected=409,code='DEPENDENCY_EDIT_LOCKED');self.assert_unchanged(before,tid)
        self.call('changeTaskAssignment',params={'task_id':tid},body={'expected_version':before['version'],'owner_id':self.ids['developer_b'],'reason':'Synthetic locked','evidence':EVIDENCE},expected=409,code='ASSIGNMENT_EDIT_LOCKED');self.assert_unchanged(before,tid)

    def staffing(self):
        i=self.new_iteration([self.ids['developer_a']]);t=self.new_task(iteration=i['id']);before=copy.deepcopy(t)
        body={'expected_version':t['version'],'owner_id':self.ids['developer_b'],'reason':'Synthetic staffing','evidence':EVIDENCE}
        self.call('changeTaskAssignment',params={'task_id':t['id']},body=body,expected=422,code='CAPACITY_REFERENCE_INVALID');self.assert_unchanged(before,t['id'])
        invalid={**body,'owner_id':self.ids['reviewer']}
        self.call('changeTaskAssignment',params={'task_id':t['id']},body=invalid,expected=422,code='OWNER_NOT_PROJECT_DEVELOPER')
        ip=copy.deepcopy(i['plan']);ip['capacity'].append({'user_id':self.ids['developer_b'],'available_hours':40})
        i=self.data('changeIteration',params={'iteration_id':i['id']},body={'expected_version':i['version'],'plan':ip,'reason':'Synthetic add capacity','evidence':EVIDENCE},expected=200)
        key=self.prefix+'-staffing-replay-key'
        result=self.call('changeTaskAssignment',params={'task_id':t['id']},body=body,key=key,expected=200)[1]
        assert result['data']['task']['owner_id']==self.ids['developer_b']
        ip=copy.deepcopy(i['plan']);ip['capacity']=[x for x in ip['capacity'] if x['user_id']!=self.ids['developer_b']]
        self.call('changeIteration',params={'iteration_id':i['id']},body={'expected_version':i['version'],'plan':ip,'reason':'Synthetic forbidden removal','evidence':EVIDENCE},expected=422,code='CAPACITY_REFERENCE_INVALID')
        replay=self.call('changeTaskAssignment',params={'task_id':t['id']},body=body,key=key,expected=200)[1]
        assert replay['data']==result['data'] and replay['meta']['replayed'] is True and replay['meta']['original_request_id']==result['meta']['request_id']
        assert replay['meta']['request_id']!=result['meta']['request_id']

    def staffing_rework(self):
        i=self.new_iteration([self.ids['developer_a'],self.ids['developer_b']]);t=self.new_task(iteration=i['id']);a=self.deliver(t);self.rollback(t,a)
        ip=copy.deepcopy(i['plan']);ip['capacity']=[x for x in ip['capacity'] if x['user_id']!=self.ids['developer_a']]
        i=self.data('changeIteration',params={'iteration_id':i['id']},body={'expected_version':i['version'],'plan':ip,'reason':'Synthetic rolledback capacity removal','evidence':EVIDENCE},expected=200)
        before=self.task(t['id']);body={'expected_version':before['version'],'action':9,'new_plan':plan(),'reason':'Synthetic rework without staffing','evidence':EVIDENCE}
        self.call('transitionTask',params={'task_id':t['id']},body=body,expected=422,code='CAPACITY_REFERENCE_INVALID');self.assert_unchanged(before,t['id'])
        self.audit('SELECT id,task_id,type,delivery_cycle FROM decisions WHERE task_id='+str(t['id']))
        ip['capacity'].append({'user_id':self.ids['developer_a'],'available_hours':40})
        self.data('changeIteration',params={'iteration_id':i['id']},body={'expected_version':i['version'],'plan':ip,'reason':'Synthetic restore staffing','evidence':EVIDENCE},expected=200)
        after=self.transition(t['id'],9,'manager',new_plan=body['new_plan'],reason=body['reason'],evidence=EVIDENCE)['task']
        assert after['delivery_cycle']==before['delivery_cycle']+1 and after['schedule_version']==before['schedule_version']+1

    def race_cas(self):
        for repeat in range(CASES['thresholds']['race_repetitions']):
            t=self.new_task();barrier=threading.Barrier(2)
            def send(n):
                barrier.wait(timeout=10)
                return self.call('transitionTask','developer_a',params={'task_id':t['id']},body={'expected_version':t['version'],'action':1},expected=[200,409])
            with cf.ThreadPoolExecutor(max_workers=2) as pool: results=list(pool.map(send,range(2)))
            assert sorted(r[0] for r in results)==[200,409], 'CAS not exactly one winner'
            assert next(r[1] for r in results if r[0]==409)['code']=='VERSION_CONFLICT'
            after=self.task(t['id']);assert after['version']==t['version']+1 and after['state']==2
            self.log('cas_round',repeat=repeat,task_id=t['id'],before=t,after=after)

    def review_negative(self):
        t=self.new_task();self.to_review(t);tid=t['id'];before=self.task(tid);body=self.review_payload(before)
        self.call('createTaskReview','developer_a',params={'task_id':tid},body=body,expected=403,code='ACTION_FORBIDDEN');self.assert_unchanged(before,tid)
        for mutation in ['section_duplicate','item_duplicate','required_na','missing_evidence']:
            bad=copy.deepcopy(body)
            if mutation=='section_duplicate':bad['sections'][1]['section_id']=bad['sections'][0]['section_id']
            elif mutation=='item_duplicate':bad['checklist'][1]['item_id']=bad['checklist'][0]['item_id']
            elif mutation=='required_na':bad['checklist'][0]['judgment']=4
            else:bad['checklist'][0]['evidence']=[]
            self.call('createTaskReview','reviewer',params={'task_id':tid},body=bad,expected=422)
            self.assert_unchanged(before,tid)
        review=self.publish_review(tid,2)['review'];before=self.task(tid)
        self.call('transitionTask','reviewer',params={'task_id':tid},body={'expected_version':before['version'],'action':5,'review_id':review['id'],'review_version':review['version']},expected=409,code='REVIEW_NOT_PASSED');self.assert_unchanged(before,tid)

    def read_only_validation(self):
        t=self.new_task();before=copy.deepcopy(t)
        for category,payload in [(1,{'title':'Synthetic validation','iteration_id':self.ids['iteration_id'],'owner_id':self.ids['developer_a'],'plan':plan(),'dependency_task_ids':[]}), (2,{'action':7,'expected_version':1,'assessment_id':1,'assessment_version':1,'release_version':'synthetic','reason':'Synthetic','evidence':EVIDENCE}), (3,self.assessment_payload(t))]:
            body={'category':category,'payload':payload}
            if category!=1:body['task_id']=t['id']
            result=self.data('validateContractPayload',body=body,expected=200)
            assert result['business_guards_executed'] is False
        self.assert_unchanged(before,t['id'])
        payload={'title':'Synthetic UTC','iteration_id':self.ids['iteration_id'],'owner_id':self.ids['developer_a'],'plan':plan(),'dependency_task_ids':[]}
        for start,end,valid in [('1000-01-01T00:00:00Z','1000-01-02T00:00:00Z',True),('9999-12-30T23:59:59.999999Z','9999-12-31T23:59:59.999999Z',True),('0999-01-01T00:00:00Z','0999-01-02T00:00:00Z',False),('2026-02-30T00:00:00Z','2026-03-02T00:00:00Z',False),('2026-10-01T00:00:00+00:00','2026-10-02T00:00:00Z',False),('2026-10-01T00:00:00.1234567Z','2026-10-02T00:00:00Z',False)]:
            payload['plan']['planned_start']=start;payload['plan']['planned_end']=end
            self.call('validateContractPayload',body={'category':1,'payload':copy.deepcopy(payload)},expected=200 if valid else 422)

    def membership_and_scope(self):
        # Fresh unused member permits real successful role change/removal without corrupting active-owner fixtures.
        uid=self.init_user('temporary',[3])
        members=self.data('listProjectMembers',query={'page_size':100},expected=200)['items']
        member=next(x for x in members if x['user']['id']==uid)
        changed=self.data('changeProjectMember',params={'user_id':uid},body={'expected_version':member['version'],'roles':[2,3],'reason':'Synthetic role change'},expected=200)
        assert changed['version']==member['version']+1 and set(changed['roles'])=={2,3}
        removed=self.data('removeProjectMember',params={'user_id':uid},body={'expected_version':changed['version'],'reason':'Synthetic removal'},expected=200)
        self.call('getProject','temporary',expected=403,code='PROJECT_ACCESS_DENIED')
        # Dedicated session is revoked without invalidating outsider used by the project-isolation sweep.
        self.data('logout','temporary',expected=200)
        self.call('getMe','temporary',expected=401,code='TOKEN_REVOKED')
        q=self.data('createProject','outsider',body={'name':self.prefix+'-foreign','description':'Foreign sentinel project'},expected=201)
        self.call('getProject',params={'project_id':q['id']},expected=403,code='PROJECT_ACCESS_DENIED')
        me=self.actor['outsider']['user']['id']
        qm=self.data('listProjectMembers','outsider',params={'project_id':q['id']},expected=200)['items'][0]
        for name,body in [('changeProjectMember',{'expected_version':qm['version'],'roles':[2],'reason':'Synthetic last manager guard'}),('removeProjectMember',{'expected_version':qm['version'],'reason':'Synthetic last manager guard'})]:
            self.call(name,'outsider',params={'project_id':q['id'],'user_id':me},body=body,expected=409,code='LAST_MANAGER')
        self.call('addProjectMember',body={'username':self.prefix+'_never_initialized','roles':[2],'reason':'Synthetic missing account'},expected=422,code='ACCOUNT_NOT_INITIALIZED')
        self.call('listTasks',query={'sort':"id UNION SELECT 1"},expected=400,code='SECURITY_INPUT_REJECTED')
        self.call('listTasks',query={'page':0},expected=422,code='PARAMETER_INVALID')
        self.data('listTasks',expected=200)

    def release_plan_guard(self):
        t=self.new_task();self.to_release(t);tid=t['id'];a=self.assessment(tid,False)
        before=self.task(tid)
        self.call('reviewReleaseAssessment',params={'task_id':tid,'assessment_id':a['id']},body={'expected_version':before['version'],'expected_assessment_version':a['version'],'verdict':1,'reason':'Synthetic self-review attempt','evidence':EVIDENCE},expected=403,code='ACTION_FORBIDDEN')
        self.assert_unchanged(before,tid)
        delivery={'expected_version':before['version'],'action':7,'assessment_id':a['id'],'assessment_version':a['version'],'release_version':'synthetic','reason':'Synthetic unapproved attempt','evidence':EVIDENCE}
        self.call('transitionTask',params={'task_id':tid},body=delivery,expected=409,code='RELEASE_APPROVAL_REQUIRED');self.assert_unchanged(before,tid)
        approved=self.data('reviewReleaseAssessment','reviewer',params={'task_id':tid,'assessment_id':a['id']},body={'expected_version':before['version'],'expected_assessment_version':a['version'],'verdict':1,'reason':'Synthetic independent review','evidence':EVIDENCE},expected=200)['assessment']
        before=self.task(tid)
        changed=self.mutation('changeTaskPlan',tid,{'plan':plan(),'reason':'Synthetic planned change','evidence':EVIDENCE})['task']
        assert changed['schedule_version']==before['schedule_version']+1 and changed['approved_review_id']==before['approved_review_id'] and changed['approved_assessment_id'] is None
        delivery.update(expected_version=changed['version'],assessment_version=approved['version'])
        stale=self.call('transitionTask',params={'task_id':tid},body=delivery,expected=409)[1]
        assert stale['code'] in ('ASSESSMENT_BASELINE_MISMATCH','RELEASE_APPROVAL_REQUIRED'), 'Oldassessment delivery not rejected by baseline/approval guard'
        self.log('spec_ambiguity_observation',note='Reschedule invalidates both assessmentbaseline and currentapproval; no unstated errorprecedenceinvented',actual_code=stale['code'])
        self.assert_unchanged(changed,tid)
        current=self.assessment(tid)
        self.transition(tid,7,'manager',assessment_id=current['id'],assessment_version=current['version'],release_version='synthetic-replanned',reason='Synthetic current-baseline fixture',evidence=EVIDENCE)

    def staffing_races(self):
        for mode in ['create','assignment','rework']:
            for repeat in range(CASES['thresholds']['race_repetitions']):
                i=self.new_iteration([self.ids['developer_a'],self.ids['developer_b']])
                t=None
                if mode=='assignment':t=self.new_task(iteration=i['id'])
                if mode=='rework':
                    t=self.new_task(iteration=i['id']);a=self.deliver(t);self.rollback(t,a)
                target=self.ids['developer_b'] if mode in ['create','assignment'] else self.ids['developer_a']
                change=copy.deepcopy(i['plan']);change['capacity']=[x for x in change['capacity'] if x['user_id']!=target]
                barrier=threading.Barrier(2)
                def remove():
                    barrier.wait(timeout=10)
                    return self.call('changeIteration',params={'iteration_id':i['id']},body={'expected_version':i['version'],'plan':change,'reason':'Synthetic capacity race','evidence':EVIDENCE},expected=[200,422])
                def activate():
                    barrier.wait(timeout=10)
                    if mode=='create':
                        return self.call('createTask',body={'title':'Synthetic create staffing race','iteration_id':i['id'],'owner_id':target,'plan':plan(),'dependency_task_ids':[]},expected=[201,422])
                    body={'expected_version':self.task(t['id'])['version']}
                    if mode=='assignment':
                        return self.call('changeTaskAssignment',params={'task_id':t['id']},body={**body,'owner_id':target,'reason':'Synthetic race','evidence':EVIDENCE},expected=[200,422])
                    return self.call('transitionTask',params={'task_id':t['id']},body={**body,'action':9,'new_plan':plan(),'reason':'Synthetic race rework','evidence':EVIDENCE},expected=[200,422])
                with cf.ThreadPoolExecutor(max_workers=2) as pool:
                    rf=pool.submit(remove);af=pool.submit(activate);r,a=rf.result(),af.result()
                assert (r[0]==200)!=(a[0]<300),'Unsafe double-success or unexplained double-rejection in capacity race'
                loser=r if r[0]>=300 else a
                assert loser[1]['code']=='CAPACITY_REFERENCE_INVALID'
                items=self.data('listIterations',query={'page_size':100},expected=200)['items']
                # Many iterations exist; read actual current iteration through paginated lists, never silently use only first100.
                page_no=1
                while not any(x['id']==i['id'] for x in items):
                    page_no+=1;more=self.data('listIterations',query={'page':page_no,'page_size':100},expected=200)['items']
                    assert more,'Iteration disappeared during race';items.extend(more)
                latest=next(x for x in items if x['id']==i['id'])
                tasks=self.data('listTasks',query={'iteration_id':i['id'],'page_size':100},expected=200)['items']
                owners={x['user_id'] for x in latest['plan']['capacity']}
                assert all(x['owner_id'] in owners for x in tasks if x['state'] in [1,2,3,4,5]),'Committed activeowner lacks capacity'
                self.log('staffing_race',mode=mode,repeat=repeat,iteration=latest,tasks=tasks,remove_status=r[0],activation_status=a[0])
        i=self.new_iteration([self.ids['developer_a'],self.ids['developer_b']]);t=self.new_task(iteration=i['id'])
        self.mutation('changeTaskAssignment',t['id'],{'owner_id':self.ids['developer_b'],'reason':'Synthetic legal ordered assignment','evidence':EVIDENCE})
        p=copy.deepcopy(i['plan']);p['capacity']=[x for x in p['capacity'] if x['user_id']!=self.ids['developer_a']]
        self.data('changeIteration',params={'iteration_id':i['id']},body={'expected_version':i['version'],'plan':p,'reason':'Synthetic legal ordered removal','evidence':EVIDENCE},expected=200)

    def common_branch_sweep(self):
        # Each canonical path is a real successful positive fixture. No random impossible endpoint/error Cartesian product.
        fixtures=copy.deepcopy(self.canonical)
        for name,fixture in fixtures.items():
            op=OPS[name][2];declared={x['code'] for x in op['x-error-cases']}
            args={k:v for k,v in fixture.items() if v is not None}
            self.call(name,**args,token_override='',expected=401,code='AUTH_REQUIRED')
            if 'INVALID_JSON' in declared:self.call(name,**args,raw=b'{"unterminated":',expected=400,code='INVALID_JSON')
            if 'PAYLOAD_TOO_LARGE' in declared:self.call(name,**args,raw=b'{"oversized":"'+b'X'*(1048576+1)+b'"}',expected=413,code='PAYLOAD_TOO_LARGE')
            if 'PARAMETER_INVALID' in declared:
                if fixture.get('body') is not None:
                    bad=copy.deepcopy(args);bad['body']={**(bad['body'] if isinstance(bad['body'],dict) else {}),'actor_id':self.ids['manager_id']}
                    self.call(name,**bad,expected=422,code='PARAMETER_INVALID')
                elif any((p.get('in')=='query' or p.get('$ref','').endswith('/Page')) for p in op.get('parameters',[])):
                    bad=copy.deepcopy(args);bad['query']={'page':0};self.call(name,**bad,expected=422,code='PARAMETER_INVALID')
            if 'PROJECT_ACCESS_DENIED' in declared:
                outsider='outsider' if fixture.get('params',{}).get('project_id')==self.ids['project_id'] else 'developer_a'
                self.call(name,**{**args,'who':outsider},expected=403,code='PROJECT_ACCESS_DENIED')

    def storage_snapshot(self):
        self.audit('SELECT VERSION() AS mysql_version, @@session.time_zone AS utc_zone, @@session.transaction_isolation AS isolation_level, @@session.sql_mode AS sql_mode')
        self.audit('SELECT TABLE_NAME,COLUMN_NAME,COLUMN_TYPE,IS_NULLABLE,COLUMN_DEFAULT,EXTRA FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=DATABASE() ORDER BY TABLE_NAME,ORDINAL_POSITION')
        self.audit('SELECT TABLE_NAME,CONSTRAINT_NAME,CONSTRAINT_TYPE FROM information_schema.TABLE_CONSTRAINTS WHERE TABLE_SCHEMA=DATABASE() ORDER BY TABLE_NAME,CONSTRAINT_NAME')
        for name in ['tasks','task_dependencies','reviews','decisions']:self.audit('SHOW CREATE TABLE '+name)
        self.audit('SELECT task_id,schedule_version,level,COUNT(*) AS n FROM escalation_events GROUP BY task_id,schedule_version,level HAVING COUNT(*)>1')
        self.audit('SELECT event_id,recipient_id,COUNT(*) AS n FROM notifications GROUP BY event_id,recipient_id HAVING COUNT(*)>1')

    def finish(self):
        known={r['case_id'] for r in self.results}
        for s in CASES['scenarios']:
            if s['id'] not in known:self.results.append({'case_id':s['id'],'outcome':'NOT_RUN','detail':'Frozen scenario needs separate phase/explicit execution; no implied coverage'})
        branches=[]
        for op in CASES['operations']:
            for e in op['errors']:
                reached=(op['operation_id'],e['code']) in self.coverage
                branches.append({'case_id':e['case_id'],'outcome':'OBSERVED_SCHEMA_VALID' if reached else (e['reachability'] if e['reachability'].startswith(('UNREACHABLE','SPEC_')) else 'NOT_RUN'),'note':'Observed code alone does not establish all semantic/audit assertions'})
        result={'operator':'independent AI','product_source_sha':self.product_sha,'frozen_cases_sha256':hashlib.sha256((HERE/'950_cases.json').read_bytes()).hexdigest(),'overall':'NOT_ACCEPTED_UNTIL_ALL_MANDATORY_PHASES_VERIFIED','results':self.results,'positive_operations':sorted(self.positive),'missing_positive_operations':sorted(set(OPS)-self.positive),'operation_error_observations':branches,'finished_at':utc(dt.datetime.now(UTC)),'phase_artifact':getattr(self,'phase_artifact',{}),'preparation_http_aggregates':self.http_aggregates}
        (self.out/'results.json').write_text(json.dumps(self.redact(result),ensure_ascii=False,indent=2)+'\n')
        counts={status:sum(r['outcome']==status for r in self.results) for status in sorted({r['outcome'] for r in self.results})}
        (self.out/'report.md').write_text('# Independent v2 private execution record\n\nOperator: AI. Product '+self.product_sha+'\n\n'+json.dumps(counts)+'\n\nNo overall pass: unexecuted mandatory cases and separate storage/fault/UI/performance/whitebox phases remain. Developer self-report is not substituted for observations. This private record is not published acceptance. See encrypted results/events for exact attempts.\n')
        self.log('finished',counts=counts,positive_operations=len(self.positive))
        return 1 if any(r['outcome'] in ('FAIL','HARNESS_ERROR','SETUP_FAILED') for r in self.results) else 2


def load_module(filename,name):
    spec=importlib.util.spec_from_file_location(name,HERE/filename)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


def main():
    path=os.environ.get('T44_ACCEPTANCE_CONTEXT')
    if not path: raise Blocked('No SUT context supplied; design-only harness does not execute')
    context=json.loads(Path(path).read_text())
    mode=context.get('independent_phase') or os.environ.get('T44_INDEPENDENT_PHASE','blackbox')
    h=Harness(context)
    if h.run('SETUP',h.setup)!='PASS':return h.finish()
    if mode=='blackbox':
        for name,fn in [('LIFE-01',h.core_lifecycle),('DEP-02',h.dependencies),('STAFF-01',h.staffing),('STAFF-03',h.staffing_rework),('CAS-01',h.race_cas),('REV-01',h.review_negative),('TIME-01',h.read_only_validation),('AUTH-02-SUBSET',h.membership_and_scope),('REL-01',h.release_plan_guard),('STAFF-04',h.staffing_races),('INPUT-01',h.common_branch_sweep),('DB-01-OBSERVE',h.storage_snapshot)]:h.run(name,fn)
    elif mode=='fault':h.run('FAULT-DRIVER',lambda:load_module('947_faults.py','independent_faults').run(h))
    elif mode=='performance':h.run('PERF-DRIVER',lambda:load_module('948_load.py','independent_load').run(h))
    else:h.run('PHASE',lambda:(_ for _ in ()).throw(Blocked('Unknown/unauthorized phase '+mode)))
    return h.finish()

if __name__=='__main__':
    try:sys.exit(main())
    except Blocked as e:print('BLOCKED: '+str(e));sys.exit(2)
