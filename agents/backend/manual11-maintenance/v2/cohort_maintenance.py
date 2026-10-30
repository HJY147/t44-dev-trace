"""APP-local existing-cohort maintenance. No SSH, DB, seed, packet generation or benchmark."""
import argparse
import fcntl
import hashlib
import importlib.util
import json
import os
import re
import signal
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

SOURCE = '90b734f65ce6ee9f5c217e885bc7ea4857e32b48'
OPS = ['login', 'readonly-inventory', 'unblock-existing-owned', 'readonly-audit', 'final-inventory']
BASIS = 'Restore original cohort after completed MANUAL11 BLOCK/UNBLOCK cycle'
OWNER_MODULE_HASHES = {'host_runner.py':'ee72bcb22ae9a95d9333b91921b9aa91767abbe96c92e751bc804df4c954f67d',
                       'runtime_support.py':'bec01e4038ef4ca5d6ba6d048e96fb8c7cb32933f705fd65a6995d24d9753170'}


class Stop(Exception):
    def __init__(self, code, category='GUARD'):
        super().__init__(code)
        self.code, self.category = code, category


def need(value, code):
    if not value:
        raise Stop(code)


def now():
    return datetime.now(timezone.utc).isoformat()


def canonical(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False)+'\n').encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read(path, limit=32*1024*1024):
    path = Path(path)
    need(path.is_file() and not path.is_symlink() and path.stat().st_size <= limit, 'BOUNDED_REGULAR_INPUT_REQUIRED')
    return path.read_bytes()


def put(path, raw):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())


def load_module(name, file):
    spec = importlib.util.spec_from_file_location(name, file)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def inventory(old, accounts):
    need(old['identity']['git_commit'] == SOURCE, 'EXACT90B_PACKET_REQUIRED')
    need(sha(canonical({k:v for k,v in old.items() if k != 'binding_sha256'})) == old['binding_sha256'], 'ORIGINAL_PACKET_BINDING_REQUIRED')
    for role in ('manager', 'developer', 'reviewer'):
        account = accounts[role]
        need(set(('username', 'password', 'user_id')) <= set(account), 'ORIGINAL_ACCOUNTS_CONTRACT_REQUIRED')
        need(isinstance(account['username'], str) and account['username'] and isinstance(account['password'], str) and account['password'], 'ORIGINAL_ACCOUNT_CREDENTIALS_REQUIRED')
        need(type(account['user_id']) is int and account['user_id'] == old['sessions'][role]['user_id'], 'ORIGINAL_ACCOUNT_SUBJECT_REQUIRED')
    rows = old['inventory']['clients']
    need(len(rows) == 400 and {r['client_id'] for r in rows} == set(range(400)), 'EXACT400_ORIGINAL_CLIENTS_REQUIRED')
    items, ids = [], []
    for row in rows:
        pid = row['project_id']
        need(type(pid) is int and pid > 0, 'ORIGINAL_POSITIVE_PROJECT_ID_REQUIRED')
        for key in ('transition_task', 'escalation_task'):
            task = row[key]
            need(type(task['id']) is int and task['id'] > 0 and task['project_id'] == pid, 'ORIGINAL_TASK_SCOPE_REQUIRED')
            ids.append(task['id'])
        need(row['transition_task']['owner_id'] == accounts['developer']['user_id'], 'ORIGINAL_TRANSITION_OWNER_REQUIRED')
        items.append((pid, row['transition_task']['id'], row['escalation_task']['id']))
    need(len(set(ids)) == 800 and len({p for p,_,_ in items}) == 40, 'ORIGINAL_DISJOINT800_AND40PROJECTS_REQUIRED')
    return sorted(items), sorted(ids)


def authorization(old, old_raw, auth, accounts):
    items, ids = inventory(old, accounts)
    scope = old['additional_neutral_snapshots']
    need(auth.get('schema') == 'manual11-cohort-maintenance-authorization-v2' and auth.get('root_approved') is True and auth.get('benchmark_grant_allow') is False and auth.get('operations') == OPS, 'DEDICATED_MAINTENANCE_AUTHORIZATION_REQUIRED')
    need(auth['old_packet_sha256'] == sha(old_raw) and auth['source_sha'] == SOURCE and auth['namespace'] == scope['namespace'] and auth['database'] == scope['database'], 'EXACT_ORIGINAL_AUTH_SCOPE_REQUIRED')
    need(re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,63}', auth['operation_id']) and auth['operation_id'] not in (old['run_id'], 'r30materialresume04', 'r30materialresume05', 'r30manualp12'), 'DISTINCT_MAINTENANCE_OPERATION_REQUIRED')
    need(auth.get('require_infrastructure_and_old_controller_guards') is True and auth.get('require_exclusive_no_benchmark_or_other_writer') is True, 'EXCLUSIVE_INFRA_AND_IDLE_ADMISSION_REQUIRED')
    need(auth['original_ids_sha256'] == sha(canonical(ids)), 'EXACT_ORIGINAL800_IDS_REQUIRED')
    return items, ids


class Evidence:
    def __init__(self, output, operation):
        output.mkdir(mode=0o700, parents=False, exist_ok=False)
        self.root, self.operation = output, operation
        self.private = output/'PRIVATE'
        self.private.mkdir(mode=0o700)
        self.progress = output/'progress.PUBLIC.jsonl'
        self.journal = self.private/'events.private.jsonl'
        put(self.journal, b'')
        put(self.progress, b'')
        self.number = 0

    def append(self, path, value):
        fd = os.open(path, os.O_WRONLY | os.O_APPEND | os.O_NOFOLLOW)
        with os.fdopen(fd, 'ab') as stream:
            stream.write(canonical(value)); stream.flush(); os.fsync(stream.fileno())

    def event(self, event, data=None, public=False):
        value = {'event': event, 'at': now(), **(data or {})}
        self.append(self.journal, value)
        if public:
            self.append(self.progress, value)

    def response(self, index, raw):
        put(self.private/f'{index:05d}.response.private.bin', raw)


class API:
    def __init__(self, runtime, old, ca, endpoint, evidence, deadline):
        self.connection = runtime.PinnedHTTPSConnection(old['environment']['origin'], endpoint['connect_ip'], ca, connect_port=endpoint['connect_port'])
        self.evidence, self.deadline, self.calls = evidence, deadline, 0
        self.connection.connect()  # strict TLS handshake, before human login

    def request(self, path, token=None, body=None, key=None):
        if time.monotonic() >= self.deadline:
            raise Stop('MAINTENANCE_DEADLINE_PREFIX_PRESERVED', 'TIMEOUT')
        self.calls += 1
        key = key or str(uuid4())
        method = 'GET' if body is None else 'POST'
        mutation = method == 'POST' and path != '/auth/login'
        record = {'number': self.calls, 'path': path, 'method': method, 'idempotency_key': key,
                  'mutation': mutation, 'body': {'credentials': 'REDACTED'} if path == '/auth/login' else body}
        # Durable prepared action is written before handing any bytes to the socket.
        self.evidence.event('REQUEST_PREPARED', record)
        headers = {'Accept': 'application/json', 'X-Request-ID': key}
        if token:
            headers['Authorization'] = 'Bearer ' + token
        if body is not None:
            headers.update({'Content-Type':'application/json', 'Idempotency-Key':key})
        try:
            self.connection.timeout = min(20, max(.1,self.deadline-time.monotonic()))
            if self.connection.sock:
                self.connection.sock.settimeout(self.connection.timeout)
            self.evidence.event('REQUEST_SENDING', {'number': self.calls, 'mutation': mutation})
            self.connection.request(method, '/api/v1'+path, None if body is None else canonical(body), headers)
            response = self.connection.getresponse()
            raw = response.read(2*1024*1024+1)
            if path != '/auth/login':
                self.evidence.response(self.calls, raw)
            self.evidence.event('RESPONSE_RECEIVED', {'number':self.calls, 'status':response.status, 'response_sha256':sha(raw)})
            need(len(raw) <= 2*1024*1024, 'BOUNDED_HTTP_RESPONSE_REQUIRED')
            envelope = json.loads(raw)
            if path == '/auth/login':
                # Maintenance logs never retain credentials, including in PRIVATE.
                metadata = safe_login_metadata(envelope.get('data', {}))
                request_id = envelope.get('meta', {}).get('request_id')
                metadata['request_id'] = request_id if isinstance(request_id,str) and re.fullmatch('[0-9a-f-]{36}',request_id) else None
                metadata.update(status=response.status,response_sha256=sha(raw),response_bytes=len(raw))
                put(self.evidence.private/f'{self.calls:05d}.login-metadata.private.json',canonical(metadata))
            if response.status != 200 or 'data' not in envelope:
                code = envelope.get('code')
                safe = code if isinstance(code,str) and re.fullmatch('[A-Z0-9_]{1,80}',code) else 'HTTP_REJECTED'
                category = 'UNKNOWN' if safe in {'TRANSACTION_UNCERTAIN','DEPENDENCY_UNAVAILABLE','AUDIT_UNAVAILABLE','INTERNAL_ERROR','IDEMPOTENCY_IN_PROGRESS'} or response.status >= 500 else 'HTTP_REJECTION'
                raise Stop(safe, category)
            return envelope['data']
        except Stop:
            raise
        except BaseException as error:
            partial=getattr(error,'partial',None)
            if isinstance(partial,bytes):
                if path != '/auth/login':
                    put(self.evidence.private/f'{self.calls:05d}.partial-response.private.bin',partial)
                else:
                    self.evidence.event('LOGIN_PARTIAL_RESPONSE_METADATA',{'number':self.calls,'bytes':len(partial),'sha256':sha(partial)})
            if isinstance(error,(KeyboardInterrupt,SystemExit)):
                code = 'INTERRUPTED_OUTCOME_REQUIRES_INSPECTION'
            else:
                code = 'HTTP_OUTCOME_UNKNOWN_STOP_NO_RETRY'
            self.evidence.event('REQUEST_OUTCOME_UNKNOWN', {'number':self.calls,'mutation':mutation,'code':code},public=True)
            raise Stop(code, 'UNKNOWN') from None

    def pages(self, path, token):
        rows, total = [], None
        for page in range(1,1001):
            data = self.request(path+('&' if '?' in path else '?')+f'page={page}&page_size=100',token)
            need(type(data['total']) is int and data['total'] >= 0 and (total is None or data['total']==total), 'LIVE_PAGINATION_COUNT_CHANGED')
            total=data['total']; rows.extend(data['items'])
            if len(rows)==total:
                return rows,total
            need(data['items'] and len(rows)<total, 'FINITE_LIVE_PAGINATION_REQUIRED')
        raise Stop('PAGE_BOUND_EXCEEDED')

    def close(self):
        self.connection.close()


def safe_login_metadata(value):
    actor_id=value.get('user', {}).get('id')
    expiry=None
    try:
        parsed=datetime.fromisoformat(value['expires_at'].replace('Z','+00:00'))
        if parsed.utcoffset()==timedelta(0):expiry=parsed.isoformat()
    except (ValueError,KeyError,TypeError,AttributeError):pass
    return {'actor_id':actor_id if type(actor_id) is int else None,'expires_at':expiry}


def guard_transition_horizon(tasks,at=None):
    at=at or datetime.now(timezone.utc)
    cutoff=at+timedelta(seconds=900,days=1)
    for task in tasks:
        try:
            due=datetime.fromisoformat(task['plan']['planned_end'].replace('Z','+00:00'))
            valid=due.utcoffset()==timedelta(0) and due>cutoff
        except (ValueError,TypeError,KeyError,AttributeError):valid=False
        need(valid,'EXISTING_TRANSITION_TASK_NOT_ELIGIBLE')
    return cutoff.isoformat()


def login(api, role, account, evidence):
    value = api.request('/auth/login',body={'username':account['username'],'password':account['password']})
    # Token remains in RAM; only nonsecret actor/expiry evidence is retained.
    evidence.event('ACTUAL_LOGIN_ISSUED',{'role':role,**safe_login_metadata(value)},public=True)
    need(value['user']['id']==account['user_id'],'LIVE_ACCOUNT_SUBJECT_MISMATCH')
    return value['access_token']


def check_task(task,pid,tid,owner=None,restorable=False):
    need(task['id']==tid and task['project_id']==pid,'LIVE_ORIGINAL_TASK_SCOPE_MISMATCH')
    need(owner is None or task['owner_id']==owner,'LIVE_ORIGINAL_OWNER_MISMATCH')
    need(type(task['version']) is int and task['version']>0,'LIVE_VERSION_REQUIRED')
    if restorable:
        need((task['state']==2 and task['blocked_from_state'] is None) or (task['state']==3 and task['blocked_from_state']==2),'LIVE_TASK_STATE_NOT_RESTORABLE')


def project_snapshot(api,items,manager):
    groups={}
    for pid,tid,eid in items:
        groups.setdefault(pid,set()).update((tid,eid))
    totals,selected={},{}
    for pid,ids in sorted(groups.items()):
        tasks,total=api.pages(f'/projects/{pid}/tasks',manager)
        indexed={t['id']:t for t in tasks}
        need(len(indexed)==total and ids<=set(indexed),'ORIGINAL800_TASKS_READBACK_REQUIRED')
        totals[str(pid)]=total
        for tid in ids:
            check_task(indexed[tid],pid,tid)
            selected[tid]=indexed[tid]
    need(len(selected)==800,'EXACT_ORIGINAL800_READBACK_REQUIRED')
    return totals,selected


def restore(api,old,items,accounts,evidence,summary):
    developer=login(api,'developer',accounts['developer'],evidence)
    manager=login(api,'manager',accounts['manager'],evidence)
    totals,all_before=project_snapshot(api,items,manager)
    evidence.event('BEFORE800_SNAPSHOT',{'project_totals':totals,'tasks':all_before})
    summary['original800_before']=len(all_before)
    before,expected={},{}
    for pid,tid,_ in items:
        task=api.request(f'/projects/{pid}/tasks/{tid}',developer)
        check_task(task,pid,tid,accounts['developer']['user_id'],True)
        need(task==all_before[tid],'CONCURRENT_CHANGE_DURING_PREFLIGHT')
        before[tid]=task
        evidence.event('TASK_PREFLIGHT',{'project_id':pid,'task_id':tid,'state':task['state'],'version':task['version']},public=True)
    summary['preflight400']=len(before)
    cutoff=guard_transition_horizon(before.values())
    evidence.event('ALL400_TRANSITION_HORIZON_CHECKED',{'required_planned_end_after':cutoff,'count':len(before)},public=True)
    for pid,tid,_ in items:
        task=before[tid]
        if task['state']==2:
            expected[tid]=task['version'];summary['skipped_state2']+=1
            continue
        action_key=str(uuid4())
        marker=f'maintenance/{summary["operation_id"]}/{tid}'
        body={'expected_version':task['version'],'action':3,'basis':BASIS,
              'evidence':[{'kind':2,'locator':marker,'description':'Existing original task restore after completed MANUAL11; no new task'}]}
        evidence.event('UNBLOCK_ACTION_PLANNED',{'task_id':tid,'project_id':pid,'before_version':task['version'],'idempotency_key':action_key,'marker':marker})
        value=api.request(f'/projects/{pid}/tasks/{tid}/transitions',developer,body,key=action_key)
        actual=value['task']
        check_task(actual,pid,tid,accounts['developer']['user_id'],True)
        if not (actual['state']==2 and actual['blocked_from_state'] is None and actual['version']==task['version']+1 and type(value.get('audit_id')) is int):
            raise Stop('UNBLOCK_RESPONSE_OR_AUDIT_MISMATCH','UNKNOWN')
        expected[tid]=actual['version'];summary['unblocked']+=1
        evidence.event('UNBLOCK_CONFIRMED',{'task_id':tid,'project_id':pid,'before_version':task['version'],'after_version':actual['version'],'audit_id':value['audit_id'],'idempotency_key':action_key},public=True)
    for pid,tid,_ in items:
        task=api.request(f'/projects/{pid}/tasks/{tid}',developer)
        check_task(task,pid,tid,accounts['developer']['user_id'],True)
        need(task['state']==2 and task['version']==expected[tid],'FINAL400_STATE_VERSION_MISMATCH')
        summary['final400_state2']+=1
        evidence.event('FINAL_TRANSITION',{'task_id':tid,'project_id':pid,'state':task['state'],'version':task['version']},public=True)
    final_totals,all_after=project_snapshot(api,items,manager)
    need(final_totals==totals and set(all_after)==set(all_before),'ORIGINAL800_OR_PROJECT_TOTALS_CHANGED')
    for pid,tid,eid in items:
        check_task(all_after[tid],pid,tid,accounts['developer']['user_id'],True)
        need(all_after[eid]==all_before[eid],'ESCALATION_TASK_CHANGED_DURING_MAINTENANCE')
        need(all_after[tid]['state']==2 and all_after[tid]['version']==expected[tid],'FINAL800_TRANSITION_MISMATCH')
    evidence.event('AFTER800_SNAPSHOT',{'project_totals':final_totals,'tasks':all_after})
    summary.update(status='COMPLETE_EXISTING400_STATE2_ORIGINAL800_PRESERVED',original800_after=len(all_after),project_task_totals_unchanged=True)


def inspect_previous(api,old,items,accounts,evidence,summary,previous):
    need(previous.is_dir() and not previous.is_symlink(),'ORIGINAL_MAINTENANCE_PREFIX_REQUIRED')
    meta=json.loads(read(previous/'guard.PUBLIC.json'))
    need(meta['old_packet_sha256']==summary['old_packet_sha256'],'RECOVERY_SAME_PACKET_REQUIRED')
    raw=read(previous/'PRIVATE'/'events.private.jsonl')
    # A kill may leave one trailing incomplete journal line: retain it, do not invent completion.
    lines=raw.splitlines();events=[]
    for i,line in enumerate(lines):
        try:events.append(json.loads(line))
        except ValueError:
            need(i==len(lines)-1 and not raw.endswith(b'\n'),'CORRUPT_PRIOR_JOURNAL')
            summary['prior_incomplete_tail']=True
    planned={r['task_id']:r for r in events if r['event']=='UNBLOCK_ACTION_PLANNED'}
    confirmed={r['task_id']:r for r in events if r['event']=='UNBLOCK_CONFIRMED'}
    manager=login(api,'manager',accounts['manager'],evidence)
    totals,tasks=project_snapshot(api,items,manager)
    findings=[]
    for tid,plan in planned.items():
        task=tasks[tid];check_task(task,plan['project_id'],tid,accounts['developer']['user_id'],True)
        if tid in confirmed:
            status='PREVIOUS_RESPONSE_CONFIRMED' if task['state']==2 and task['version']==confirmed[tid]['after_version'] else 'STATE_DIVERGED_COORDINATOR_REQUIRED'
        else:
            rows,_=api.pages(f'/projects/{plan["project_id"]}/audit-events?task_id={tid}&outcome=1',manager)
            matches=[r for r in rows if r.get('operation_id')=='transitionTask' and r.get('actor_id')==accounts['developer']['user_id'] and r.get('actor_kind')==1 and r.get('project_id')==plan['project_id'] and r.get('task_id')==tid and r.get('outcome')==1 and r.get('expected_version')==plan['before_version'] and any(e.get('locator')==plan['marker'] for e in r.get('evidence',[]))]
            if len(matches)==1 and task['state']==2 and task['version']==plan['before_version']+1:
                status='UNKNOWN_POST_COMMIT_PROVEN_BY_AUDIT_AND_READBACK'
            elif task['state']==3 and task['version']==plan['before_version'] and not matches:
                status='UNCHANGED_READBACK_NOT_PROOF_OF_NO_COMMIT_NO_RETRY'
            else:status='AMBIGUOUS_OUTCOME_COORDINATOR_REQUIRED'
        findings.append({'task_id':tid,'project_id':plan['project_id'],'classification':status,'state':task['state'],'version':task['version']})
    evidence.event('RECOVERY_INSPECTION',{'findings':findings,'project_totals':totals},public=True)
    summary.update(status='READONLY_RECOVERY_INSPECTED_COORDINATOR_DECISION_REQUIRED',original800_after=len(tasks),recovery_findings=findings,automatic_resume=False)


def controller_idle(unit,runner=None):
    runner=runner or subprocess.run
    result=runner(['systemctl','show',unit,'--property=Id,LoadState,ActiveState'],capture_output=True,timeout=10,check=False)
    try:
        pairs=[line.split('=',1) for line in result.stdout.decode().splitlines()]
        valid=all(len(pair)==2 for pair in pairs)
        row=dict(pairs) if valid else {}
        valid=valid and len(pairs)==len(row)==3 and set(row)=={'Id','LoadState','ActiveState'} and row['Id']==unit
        stderr=result.stderr.strip()
        missing=(row.get('LoadState')=='not-found' and row.get('ActiveState')=='inactive'
                 and result.returncode in (0,1) and stderr in (b'',f'Unit {unit} could not be found.'.encode()))
        loaded=(row.get('LoadState')=='loaded' and row.get('ActiveState') in ('inactive','failed')
                and result.returncode==0 and stderr==b'')
    except (ValueError,UnicodeDecodeError,AttributeError):
        valid=missing=loaded=False
    need(valid and (missing or loaded),'OLD_CONTROLLER_NOT_PROVEN_INACTIVE')
    return {**row,'ReturnCode':result.returncode}


def build_parser():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--mode',choices=['apply','inspect'],required=True)
    for name in ('old-packet','accounts','authorization','ca','output'):
        p.add_argument('--'+name,required=True,type=Path)
    p.add_argument('--backend-tools',type=Path,default=Path(__file__).resolve().parent)
    p.add_argument('--api-container',required=True)
    p.add_argument('--expected-api-image-id',required=True)
    p.add_argument('--root-admit-maintenance',action='store_true')
    p.add_argument('--previous',type=Path)
    return p


def main(argv=None):
    args=build_parser().parse_args(argv)
    os.umask(0o077)
    need(args.root_admit_maintenance and os.geteuid()==0,'EXPLICIT_APP_HOST_ROOT_MAINTENANCE_REQUIRED')
    need(args.mode=='inspect' if args.previous else args.mode=='apply','INSPECT_PREVIOUS_REQUIRED_NO_AUTOMATIC_RESUME')
    raw=read(args.old_packet);old=json.loads(raw);accounts=json.loads(read(args.accounts));auth=json.loads(read(args.authorization))
    items,ids=authorization(old,raw,auth,accounts)
    need(sha(read(args.ca))==old['environment']['ca_sha256'],'ORIGINAL_CA_SHA_REQUIRED')
    need(args.output.is_absolute() and args.output.parent.resolve()==args.output.parent and not args.output.exists(),'NEW_CANONICAL_OUTPUT_REQUIRED')
    evidence=Evidence(args.output,auth['operation_id'])
    summary={'schema':'manual11-cohort-maintenance-receipt-v2','status':'INCOMPLETE','operation_id':auth['operation_id'],'old_packet_sha256':sha(raw),'original_ids_sha256':sha(canonical(ids)),'started_at':now(),'mode':args.mode,'new_tasks':0,'seed_calls':0,'benchmark_started':False,'material05_generated':False,'automatic_resume':False,'unblocked':0,'skipped_state2':0,'preflight400':0,'final400_state2':0}
    lock=None;api=None;exit_code=1
    deadline=time.monotonic()+300
    put(args.output/'guard.PUBLIC.json',canonical({**summary,'namespace':auth['namespace'],'database':auth['database'],'api_container':args.api_container,'expected_api_image_id':args.expected_api_image_id,'pid':os.getpid(),'authorization_sha256':sha(read(args.authorization))}))
    def interrupted(_signum,_frame):
        raise Stop('INTERRUPTED_OUTCOME_REQUIRES_INSPECTION','UNKNOWN')
    prior={s:signal.signal(s,interrupted) for s in (signal.SIGINT,signal.SIGTERM)}
    try:
        need(re.fullmatch('[A-Za-z0-9][A-Za-z0-9_-]{0,127}',auth['namespace']),'OWNED_LOCK_NAMESPACE_REQUIRED')
        lock=os.open('/run/lock/t44-cohort-'+auth['namespace']+'.lock',os.O_RDWR|os.O_CREAT|os.O_NOFOLLOW,0o600)
        try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:raise Stop('MAINTENANCE_ALREADY_ACTIVE') from None
        for name,expected_hash in OWNER_MODULE_HASHES.items():
            need(sha(read(args.backend_tools/name))==expected_hash,'PINNED_OWNER_MODULE_BYTES_REQUIRED')
        evidence.event('OWNER_MODULE_BYTES_CHECKED',{'sha256':OWNER_MODULE_HASHES},public=True)
        host=load_module('cohort_host_runner',args.backend_tools/'host_runner.py')
        runtime=load_module('cohort_runtime_support',args.backend_tools/'runtime_support.py')
        controller_states = {}
        for unit in (auth['namespace']+'-stop.service','t44-final-p09-continuous.service'):
            controller_states[unit]=controller_idle(unit)
        evidence.event('OLD_CONTROLLERS_IDLE',controller_states,public=True)
        host.inspect_api(args.api_container,auth['namespace'],args.expected_api_image_id)
        gateway_args=argparse.Namespace(api_container=args.api_container,discover_maintenance_gateway=True,maintenance_gateway_container=None,maintenance_connect_ip=None,maintenance_connect_port=None)
        endpoint=host.maintenance_endpoint(gateway_args,auth,old)
        need(endpoint is not None,'DYNAMIC_SAME_OWNER_GATEWAY_REQUIRED')
        evidence.event('ACTUAL_OWNER_AND_GATEWAY',{'endpoint':endpoint},public=True)
        api=API(runtime,old,args.ca,endpoint,evidence,deadline)
        if args.mode=='apply':restore(api,old,items,accounts,evidence,summary)
        else:inspect_previous(api,old,items,accounts,evidence,summary,args.previous)
        exit_code=0 if args.mode=='apply' else 4
    except Stop as error:
        summary.update(error_code=error.code,error_category=error.category)
        exit_code={'GUARD':2,'HTTP_REJECTION':3,'UNKNOWN':4,'TIMEOUT':5}.get(error.category,1)
    except BaseException:
        summary.update(error_code='UNCLASSIFIED_FAILURE_PREFIX_PRESERVED',error_category='UNKNOWN')
        exit_code=4
    finally:
        if api:
            summary['http_requests']=api.calls
            try:api.close()
            except Exception:pass
        summary.update(finished_at=now(),exit_code=exit_code,foreground_execution_finished=True)
        evidence.event('FOREGROUND_COMPLETE',{'status':summary['status'],'exit_code':exit_code},public=True)
        put(args.output/'receipt.PUBLIC.json',canonical(summary))
        if lock is not None:os.close(lock)
        for sig,handler in prior.items():signal.signal(sig,handler)
        # Never print raw exceptions, account objects, HTTP bodies or token values.
        print(json.dumps({'status':summary['status'],'error_code':summary.get('error_code'),'exit_code':exit_code,'receipt':str(args.output/'receipt.PUBLIC.json')}))
    return exit_code


def invoke_before_material(*,backend_tools,old_inputs,accounts,authorization,output,api_container,expected_api_image_id):
    """Deployment-owned sequence hook: call only after infra/old-controller guards, before host_runner."""
    try:
        result=subprocess.run([sys.executable,'-B',str(Path(backend_tools)/'cohort_maintenance.py'),'--mode','apply','--root-admit-maintenance','--backend-tools',str(backend_tools),'--old-packet',str(Path(old_inputs)/'session.private.json'),'--accounts',str(accounts),'--authorization',str(authorization),'--ca',str(Path(old_inputs)/'ca.pem'),'--output',str(output),'--api-container',api_container,'--expected-api-image-id',expected_api_image_id],capture_output=True,timeout=330,check=False)
    except subprocess.TimeoutExpired as error:
        if not Path(output).exists():Path(output).mkdir(mode=0o700)
        put(Path(output)/'invoke.stdout.private.bin',error.stdout or b'')
        put(Path(output)/'invoke.stderr.private.bin',error.stderr or b'')
        raise Stop('MAINTENANCE_TIMEOUT_PREFIX_PRESERVED_NO_MATERIAL','UNKNOWN') from None
    if not Path(output).exists():Path(output).mkdir(mode=0o700)
    put(Path(output)/'invoke.stdout.private.bin',result.stdout)
    put(Path(output)/'invoke.stderr.private.bin',result.stderr)
    need(result.returncode==0,'COHORT_MAINTENANCE_FAILED_MATERIAL_NOT_ALLOWED')
    receipt=json.loads(read(Path(output)/'receipt.PUBLIC.json'))
    need(receipt['status']=='COMPLETE_EXISTING400_STATE2_ORIGINAL800_PRESERVED' and receipt['final400_state2']==400 and receipt['original800_before']==receipt['original800_after']==800 and receipt['project_task_totals_unchanged'] is True,'COHORT_RECEIPT_REQUIRED_BEFORE_MATERIAL')
    return receipt


if __name__=='__main__':
    try:sys.exit(main())
    except Stop as error:
        print(json.dumps({'status':'PRE_EXECUTION_REFUSED','error_code':error.code}));sys.exit(2)
    except Exception:
        print(json.dumps({'status':'PRE_EXECUTION_REFUSED','error_code':'INPUT_FAILURE_NO_CREDENTIALS_PRINTED'}));sys.exit(2)
