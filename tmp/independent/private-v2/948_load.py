#!/usr/bin/env python3
"""Frozen representative preparation and formal 400-VU driver. Never run during design."""
from __future__ import annotations
import concurrent.futures as cf
import copy
import datetime as dt
import gzip
import http.client
import json
from pathlib import Path
import secrets
import ssl
import struct
import threading
import time
import urllib.parse

# Raw trace.log is gzip-compressed binary: magic T44V2P1\n then repeated little-endian
# <QIIHBB: relative start microseconds, HTTP elapsed microseconds, sequence, VU, class, verdict
# followed by <H: HTTP status. class1=transition,2=query,3=validation,4=escalation.
# verdict0=validsuccess,1=transport,2=HTTP/business,3=schema,4=fixture/preparation.
RECORD=struct.Struct('<QIIHBBH')


def prepare(h):
    """Legal API-only construction; may take hours and is not a formal run."""
    fixture={'version':1,'prepared_by':'independent-v2-frozen-driver','product_source_sha':h.product_sha,'projects':[],'task_count':6000,'dependency_count':9000,'review_decision_count':15000,'state_mix':'3600 delivered,2400 pending;1950 delivered through second cycle','construction':'40x150;225 DAG edges perproject, lowerindex predecessors;90 delivered perproject;first1950 delivered tasks rollback/rework/review/deliver again'}
    completed_second=0
    original=copy.deepcopy(h.ids)
    for project_index in range(40):
        p=h.data('createProject',body={'name':h.prefix+'-load-'+str(project_index),'description':'Independent representative synthetic performance dataset'},expected=201)
        h.ids['project_id']=p['id']
        for label,roles in [('developer_a',[2]),('developer_b',[2]),('reviewer',[3])]:
            h.data('addProjectMember',body={'username':h.actor[label]['username'],'roles':roles,'reason':'Independent load fixture'},expected=201)
        it=h.new_iteration([h.ids['developer_a'],h.ids['developer_b']]);h.ids['iteration_id']=it['id']
        tasks=[h.new_task() for _ in range(150)]
        edges=[]
        for distance in (1,2):
            for index in range(distance,150):
                if len(edges)==225:break
                h.mutation('addTaskDependency',tasks[index]['id'],{'depends_on_task_id':tasks[index-distance]['id'],'reason':'Independent acyclic performance graph'})
                edges.append((tasks[index]['id'],tasks[index-distance]['id']))
            if len(edges)==225:break
        for t in tasks[:90]:
            a=h.deliver(t)
            if completed_second<1950:
                h.rollback(t,a)
                h.transition(t['id'],9,'manager',new_plan=__import__('sys').modules['__main__'].plan(),reason='Independent representative second cycle',evidence=__import__('sys').modules['__main__'].EVIDENCE)
                h.transition(t['id'],4,artifact_revision=__import__('sys').modules['__main__'].ARTIFACT,evidence=__import__('sys').modules['__main__'].EVIDENCE)
                rev=h.publish_review(t['id'])['review']
                h.transition(t['id'],5,'reviewer',review_id=rev['id'],review_version=rev['version'])
                a2=h.assessment(t['id'])
                h.transition(t['id'],7,'manager',assessment_id=a2['id'],assessment_version=a2['version'],release_version='synthetic-load-second',reason='Independent fixture second delivery',evidence=__import__('sys').modules['__main__'].EVIDENCE)
                completed_second+=1
        fixture['projects'].append({'project_id':p['id'],'iteration_id':it['id'],'task_ids':[t['id'] for t in tasks],'writable_task_ids':[t['id'] for t in tasks[90:]],'dependency_edges':len(edges)})
    h.ids=original
    ids=','.join(str(p['project_id']) for p in fixture['projects'])
    h.audit('SELECT COUNT(*) AS projects FROM projects WHERE id IN ('+ids+')')
    for table in ['tasks','task_dependencies','reviews','decisions']:
        h.audit('SELECT COUNT(*) AS n FROM '+table+' WHERE project_id IN ('+ids+')')
    h.phase_artifact={'load_fixture':fixture,'preparation_only':True,'formal_performance_executed':False}


def run(h):
    from __main__ import Blocked,EVIDENCE,plan,utc
    config=h.context.get('independent_performance',{})
    if config.get('mode')=='prepare':
        h.run('PERF-PREPARE',lambda:prepare(h));return
    fixture_path=config.get('fixture_file')
    if not fixture_path:raise Blocked('Performance requires tester-owned representative fixture file from separate frozen preparation phase')
    f=json.loads(Path(fixture_path).read_text())
    fixture=f.get('load_fixture') or f.get('phase_artifact',{}).get('load_fixture') or f
    if fixture.get('product_source_sha')!=h.product_sha:raise Blocked('Performance fixture is bound to a different product SHA')
    if len(fixture.get('projects',[]))!=40:raise Blocked('Representative dataset40projects not established')
    project_ids=','.join(str(p['project_id']) for p in fixture['projects'])
    h.audit('SELECT COUNT(*) AS task_n FROM tasks WHERE project_id IN ('+project_ids+')')
    h.audit('SELECT COUNT(*) AS dependency_n FROM task_dependencies WHERE project_id IN ('+project_ids+')')
    h.audit('SELECT (SELECT COUNT(*) FROM reviews WHERE project_id IN ('+project_ids+'))+(SELECT COUNT(*) FROM decisions WHERE project_id IN ('+project_ids+')) AS review_decision_n')
    # SQL outputs and statement semantics are inspected by tester. Unparsed SQL is never guessed as a count.
    if config.get('dataset_counts_independently_verified') is not True:raise Blocked('Tester must first verify actual read-only dataset counts and reachability; manifest claims do not suffice')
    kind=config.get('run_kind')
    if kind not in ('mixed','transition','validation','escalation'):raise Blocked('One explicitly selected mixed/transition/validation/escalation formal run per job is required')
    if not config.get('server_resource_telemetry_file'):raise Blocked('Formal run requires real server CPU/RAM/network/DB resource telemetry binding')
    telemetry=Path(config['server_resource_telemetry_file'])
    if not telemetry.is_file():raise Blocked('Server resource telemetry source missing')
    endpoints=[{'project_id':p['project_id'],'task_id':t} for p in fixture['projects'] for t in p['writable_task_ids']]
    if len(endpoints)<400:raise Blocked('Need400disjoint legally writable tasks')
    endpoints=endpoints[:400]
    service=None
    if kind in ('mixed','escalation'):
        service_file=h.context.get('independent_service_credentials_file')
        if not service_file:raise Blocked('Need real escalation-scoped service credentials on all measured projects')
        if not config.get('scan_run_id'):raise Blocked('Need an actual persisted scan_run_id observed in neutral read-only SQL; no guessed UUID')
        service=json.loads(Path(service_file).read_text())
        service=service.get('access_token') or service.get('token')
        if not service:raise Blocked('Service credential file lacks token')
        h.secrets.append(service)
    threshold=h.context.get('formal_run_parameters',{})
    for field,expected in [('concurrent_users',400),('steady_seconds',600),('warmup_seconds',60)]:
        if field in threshold and threshold[field]!=expected:raise Blocked('Frozen performance threshold cannot be changed: '+field)
    # Warm-up executes the same400VUclosedloop, excludes every warm-up sample from formal percentile/throughput.
    class_ids={'transition':1,'query':2,'validation':3,'escalation':4}
    samples={i:[] for i in range(1,5)};counts={i:0 for i in range(1,5)};errors=[];lock=threading.RLock();active=0;max_active=0;barrier=threading.Barrier(401)
    url=urllib.parse.urlparse(h.base);prefix=url.path.rstrip('/');start_time=[None];steady_start=[None];warm_done=[False];trace=h.out/'trace.log'
    raw=gzip.open(trace,'wb',compresslevel=6);raw.write(b'T44V2P1\n')
    monitor=[];stop_monitor=threading.Event()
    def resource_monitor():
        while not stop_monitor.wait(1):
            item={'at_monotonic':time.monotonic(),'active_virtual_users':active}
            for fname in ['/proc/loadavg','/proc/meminfo','/proc/stat','/proc/net/dev']:
                try:item[fname]=Path(fname).read_text()[:12000]
                except OSError:item[fname]='unavailable'
            with lock:monitor.append(item)
    def worker(vu):
        nonlocal active,max_active
        ep=endpoints[vu]
        task=h.data('getTask',params=ep,expected=200)
        if task['state'] not in (1,3) or (task['state']==3 and task['blocked_from_state']!=1):raise Blocked('Loadtasknotlegallypending/blockable')
        conn=(http.client.HTTPSConnection(url.hostname,url.port,timeout=30,context=ssl.create_default_context()) if url.scheme=='https' else http.client.HTTPConnection(url.hostname,url.port,timeout=30))
        seq=0
        barrier.wait(timeout=120)
        with lock:active+=1;max_active=max(max_active,active)
        try:
            while time.monotonic()<steady_start[0]+600:
                if kind=='mixed':opkind=('transition','query','validation','escalation')[seq%4]
                else:opkind=kind
                if opkind=='transition':
                    action=2 if task['state']==1 else 3
                    payload={'expected_version':task['version'],'action':action}
                    if action==2:payload.update(reason='Independent formal synthetic block',responsibility_stage=1,evidence=EVIDENCE)
                    else:payload.update(basis='Independent formal synthetic release',evidence=EVIDENCE)
                    method='POST';path=f"/projects/{ep['project_id']}/tasks/{ep['task_id']}/transitions";operation='transitionTask';token=h.actor['manager']['access_token']
                elif opkind=='query':
                    method='GET';path=f"/projects/{ep['project_id']}/tasks/{ep['task_id']}";operation='getTask';payload=None;token=h.actor['manager']['access_token']
                elif opkind=='validation':
                    method='POST';path=f"/projects/{ep['project_id']}/contract-validations";operation='validateContractPayload';token=h.actor['manager']['access_token']
                    category=seq%3+1
                    if category==1:payload={'category':1,'payload':{'title':'Independent formal registration validation','iteration_id':task['iteration_id'],'owner_id':task['owner_id'],'plan':plan(),'dependency_task_ids':[]}}
                    elif category==2:payload={'category':2,'task_id':ep['task_id'],'payload':{'action':1,'expected_version':task['version']}}
                    else:payload={'category':3,'task_id':ep['task_id'],'payload':h.assessment_payload(task)}
                else:
                    # Each measurement is a new durable business event; preparation is a real extra write, never hidden as a replay.
                    pp=plan(dt.datetime.now(dt.timezone.utc)-dt.timedelta(hours=2))
                    mutation=h.data('changeTaskPlan',params=ep,body={'expected_version':task['version'],'plan':pp,'reason':'Independent next formal escalation schedule','evidence':EVIDENCE},expected=200)
                    task=mutation['task']
                    method='POST';path=f"/internal/projects/{ep['project_id']}/tasks/{ep['task_id']}/escalations";operation='createEscalation';token=service
                    payload={'expected_version':task['version'],'schedule_version':task['schedule_version'],'rule_version':h.rules['version'],'scan_run_id':config.get('scan_run_id','00000000-0000-4000-8000-000000000001')}
                headers={'Authorization':'Bearer '+token,'Accept':'application/json','X-Request-ID':h.prefix+f'-P-{vu}-{seq}'}
                if method=='POST':headers['Content-Type']='application/json'
                if operation not in ('getTask','validateContractPayload'):headers['Idempotency-Key']=h.prefix+f'-formal-{kind}-{vu}-{seq}'
                body=json.dumps(payload,separators=(',',':')).encode() if payload is not None else None
                began=time.monotonic();status=0;verdict=0;value={}
                try:
                    conn.request(method,prefix+path,body=body,headers=headers);response=conn.getresponse();status=response.status;value=json.loads(response.read())
                    ended=time.monotonic()
                    if status not in (200,202):verdict=2
                    else:
                        try:h.validate(__import__('__main__').OPS[operation][2]['responses'][str(status)]['content']['application/json']['schema'],value)
                        except AssertionError:verdict=3
                    if verdict==0:
                        if operation=='transitionTask':task=value['data']['task']
                        elif operation=='getTask':task=value['data']
                        elif operation=='createEscalation':
                            if value['data']['created'] is not True:verdict=2
                            task={**task,'version':value['data']['task_version']}
                except Exception:
                    ended=time.monotonic();verdict=1;conn.close()
                cid=class_ids[opkind]
                if began>=steady_start[0] and began<steady_start[0]+600:
                    us=int((ended-began)*1_000_000)
                    with lock:
                        samples[cid].append(us);counts[cid]+=1
                        raw.write(RECORD.pack(int((began-steady_start[0])*1_000_000),us,seq,vu,cid,verdict,status))
                        if verdict:errors.append({'vu':vu,'sequence':seq,'class':opkind,'status':status,'verdict':verdict,'code':value.get('code')})
                if verdict:raise AssertionError('Formal request failed; no retries/reducedthresholds')
                seq+=1
        finally:
            conn.close()
            with lock:active-=1
    monitor_thread=threading.Thread(target=resource_monitor,daemon=True);monitor_thread.start()
    pool=cf.ThreadPoolExecutor(max_workers=400);futures=[pool.submit(worker,i) for i in range(400)]
    start_time[0]=time.monotonic();steady_start[0]=start_time[0]+60
    try:
        barrier.wait(timeout=120)
        # Timestamp is set before barrier release; excludes setup and gives all400VUs same full warm-up/steady endpoints.
        actual_start=time.monotonic();steady_start[0]=actual_start+60
        cf.wait(futures,timeout=720)
        worker_errors=[]
        for future in futures:
            if not future.done():worker_errors.append('worker_timeout')
            else:
                try:future.result()
                except Exception as exc:worker_errors.append(type(exc).__name__+': '+str(exc)[:240])
    finally:
        stop_monitor.set();pool.shutdown(wait=True,cancel_futures=True);raw.close()
    summary={}
    for cid,values in samples.items():
        if not values:continue
        ordered=sorted(values);p95=ordered[max(0,__import__('math').ceil(.95*len(ordered))-1)]/1000
        summary[cid]={'requests':len(values),'p95_ms_nearest_rank':p95,'throughput_per_min':len(values)/10,'min_ms':min(values)/1000,'max_ms':max(values)/1000}
    h.phase_artifact={'formal_run_kind':kind,'virtual_users':400,'maximum_active_vus':max_active,'steady_seconds':600,'warmup_seconds':60,'summary':summary,'unexpected_failures':errors,'worker_errors':worker_errors,'raw_trace_format':'gzip T44V2P1 newline then struct<QIIHBBH; timing_microseconds,sequence,VU,class,verdict,status','client_resource_samples':monitor,'server_resource_telemetry_sha256':__import__('hashlib').sha256(telemetry.read_bytes()).hexdigest(),'fixture_sha256':__import__('hashlib').sha256(Path(fixture_path).read_bytes()).hexdigest(),'warning':'One formal run cannot alone satisfy all four mandatory runs. Extra prepareplan writes are separatefrommeasuredclass.'}
    assert max_active==400,'400concurrentVUs not reached'
    assert not errors and not worker_errors,'Formal business/transport/schema/worker failures occurred'
    assert all(x['p95_ms_nearest_rank']<=270 for x in summary.values()),'P95 exceeds270ms'
    assert sum(counts.values())/10>=1000,'Throughputbelow1000/min'
    assert trace.stat().st_size<=20*1024*1024,'Evidence archiveperfilecapacity inadequate; preserve raw evidence and request largerneutralarchive'
