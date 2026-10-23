#!/usr/bin/env python3
"""Continuation of original frozen950 pending recipes; never imports SUT source.

Earlier completed case methods are not selected. Reaching states is fixture setup
for the distinct unexecuted matrices. All old freezes/runs remain unmodified.
"""
from pathlib import Path
import copy
import csv
import datetime as dt
import io
import json
import math
import os
import runpy
import secrets
import sys
import time

HERE=Path(__file__).resolve().parent
P=runpy.run_path(str(HERE/'939_runtime-adapter.py'),run_name='pending_independent_parent')
Blocked=P['Blocked'];EVIDENCE=P['EVIDENCE'];ARTIFACT=P['ARTIFACT'];OPS=P['OPS'];plan=P['plan']

def quote(value):
    return "'"+str(value).replace("'","''")+"'"

class Pending(P['RuntimeAdapter']):
    def audit(self,sql):
        value=super().audit(sql)
        if isinstance(value,dict) and 'unparsed' in value:
            text=value['unparsed']
            return list(csv.DictReader(io.StringIO(text),delimiter='\t')) if text.strip() else []
        return value

    def scalar(self,sql):
        rows=self.audit(sql)
        assert isinstance(rows,list) and len(rows)==1,'Read-only scalar needs exactly one actual row'
        return int(next(iter(rows[0].values())))

    def call(self,name,*args,**kw):
        result=super().call(name,*args,**kw)
        status,value,_=result
        audit_id=value.get('audit_id') if status>=300 else value.get('data',{}).get('audit_id')
        if audit_id is not None:
            rows=self.audit('SELECT id,operation_id,outcome,request_id FROM audit_events WHERE id='+str(int(audit_id)))
            assert len(rows)==1 and rows[0]['operation_id']==name,'Returned audit reference does not identify actual operation'
            assert int(rows[0]['outcome'])==(1 if status<300 else 2),'Actual durable audit outcome differs'
            request_id=value.get('request_id') or value.get('meta',{}).get('original_request_id') or value.get('meta',{}).get('request_id')
            assert rows[0]['request_id']==request_id,'Durable audit request identity differs'
            self.log('actual_audit_verified',operation=name,audit_id=audit_id,outcome=int(rows[0]['outcome']),request_id=request_id)
        return result

    def mutation(self,name,*args,**kw):
        if 'expected' not in kw:
            allowed=[int(s) for s in OPS[name][2]['responses'] if s.startswith('2')]
            assert len(allowed)==1
            kw['expected']=allowed[0]
        return super().mutation(name,*args,**kw)

    def advance(self,t,state,owner='developer_a',start_key=None):
        tid=t['id'];assessment=None
        if state>=2:
            self.call('transitionTask',owner,params={'task_id':tid},body={'expected_version':t['version'],'action':1},key=start_key,expected=200)
        if state>=4:
            self.transition(tid,4,owner,artifact_revision=ARTIFACT,evidence=EVIDENCE)
        if state>=5:
            r=self.publish_review(tid)['review']
            self.transition(tid,5,'reviewer',review_id=r['id'],review_version=r['version'])
        if state>=6:
            assessment=self.assessment(tid)
            self.transition(tid,7,'manager',assessment_id=assessment['id'],assessment_version=assessment['version'],release_version='synthetic-pending-v2',reason='Synthetic continuation fixture decision',evidence=EVIDENCE)
        if state>=7:self.rollback(t,assessment)
        return assessment

    def member(self,uid):
        return next(x for x in self.data('listProjectMembers',query={'page_size':100},expected=200)['items'] if x['user']['id']==uid)

    def iteration_current(self,iid):
        return next(x for x in self.data('listIterations',query={'page_size':100},expected=200)['items'] if x['id']==iid)

    def unchanged_counts(self,tid):
        return {table:self.scalar('SELECT COUNT(*) AS n FROM '+table+' WHERE task_id='+str(tid)) for table in ['task_dependencies','reviews','release_assessments','decisions','schedule_changes']}

    def life02(self):
        for state,valid,wrong in [(1,'manager','developer_b'),(2,'developer_a','manager'),(4,'reviewer','developer_a'),(5,'manager','reviewer')]:
            t=self.new_task();self.advance(t,state) if state!=1 else None
            tid=t['id'];before=self.task(tid);counts=self.unchanged_counts(tid)
            body={'expected_version':before['version'],'action':2,'reason':'Synthetic phase-specific blocker','responsibility_stage':5,'evidence':EVIDENCE}
            self.call('transitionTask',wrong,params={'task_id':tid},body=body,expected=403,code='ACTION_FORBIDDEN')
            self.call('transitionTask',valid,params={'task_id':tid},body={**body,'evidence':[]},expected=422,code='PARAMETER_INVALID')
            self.assert_unchanged(before,tid)
            blocked=self.data('transitionTask',valid,params={'task_id':tid},body=body,expected=200)['task']
            assert blocked['state']==3 and blocked['blocked_from_state']==state and blocked['version']==before['version']+1
            ub={'expected_version':blocked['version'],'action':3,'basis':'Synthetic independent unblock basis','evidence':EVIDENCE}
            self.call('transitionTask',wrong,params={'task_id':tid},body=ub,expected=403,code='ACTION_FORBIDDEN')
            self.call('transitionTask',valid,params={'task_id':tid},body={**ub,'target_state':2},expected=422,code='PARAMETER_INVALID')
            self.call('transitionTask',valid,params={'task_id':tid},body={**ub,'evidence':[]},expected=422,code='PARAMETER_INVALID')
            self.assert_unchanged(blocked,tid)
            after=self.data('transitionTask',valid,params={'task_id':tid},body=ub,expected=200)['task']
            assert after['state']==state and after['version']==before['version']+2 and after['blocked_from_state'] is None
            for k in ['review_cycle','delivery_cycle','schedule_version','artifact_revision','approved_review_id','approved_assessment_id','approved_assessment_version','plan','owner_id']:
                assert after[k]==before[k],'Block/unblock changed '+k
            assert self.unchanged_counts(tid)==counts,'Block/unblock rewrote prior evidence records'
            self.log('pending_life02_phase',source_state=state,before=before,blocked=blocked,after=after)

    def dep01(self):
        predecessor=self.new_task();downstream=self.new_task(deps=[predecessor['id']]);tid=downstream['id']
        self.call('transitionTask','developer_a',params={'task_id':tid},body={'expected_version':downstream['version'],'action':1},expected=409,code='DEPENDENCIES_UNSATISFIED')
        self.assert_unchanged(downstream,tid)
        assessment=self.advance(predecessor,6)
        deps=self.data('listTaskDependencies',params={'task_id':tid},expected=200)
        self.transition(tid,1);started=self.task(tid);assert started['state']==2
        self.rollback(predecessor,assessment)
        self.assert_unchanged(started,tid)
        self.transition(tid,2,reason='Synthetic predecessor rolled back',responsibility_stage=5,evidence=EVIDENCE)
        blocked=self.task(tid);assert blocked['blocked_from_state']==2
        self.call('transitionTask','developer_a',params={'task_id':tid},body={'expected_version':blocked['version'],'action':3,'basis':'Synthetic attempted unblock','evidence':EVIDENCE},expected=409,code='DEPENDENCIES_UNSATISFIED')
        self.assert_unchanged(blocked,tid)
        self.log('pending_dep01',predecessor_id=predecessor['id'],downstream_id=tid,dependency_page_when_delivered=deps,after_predecessor_rollback=started,blocked=blocked)

    def staff02(self):
        matrix=[(s,None) for s in [1,2,4,5,6,7]]+[(3,s) for s in [1,2,4,5]]
        for state,blocked_from in matrix:
            i=self.new_iteration([self.ids['developer_a'],self.ids['developer_b']]);t=self.new_task(iteration=i['id']);source=blocked_from or state
            self.advance(t,source) if source!=1 else None
            if state==3:
                actor={1:'manager',2:'developer_a',4:'reviewer',5:'manager'}[source]
                self.transition(t['id'],2,actor,reason='Synthetic staffing blocked phase',responsibility_stage=5,evidence=EVIDENCE)
            task_before=self.task(t['id']);before=self.iteration_current(i['id']);diff_count=self.scalar('SELECT COUNT(*) AS n FROM schedule_changes WHERE iteration_id='+str(i['id']))
            pl=copy.deepcopy(before['plan']);pl['capacity']=[x for x in pl['capacity'] if x['user_id']!=self.ids['developer_a']]
            body={'expected_version':before['version'],'plan':pl,'reason':'Synthetic state-specific capacity removal','evidence':EVIDENCE}
            if state not in [6,7]:
                self.call('changeIteration',params={'iteration_id':i['id']},body=body,expected=422,code='CAPACITY_REFERENCE_INVALID')
                assert self.iteration_current(i['id'])==before
                assert self.scalar('SELECT COUNT(*) AS n FROM schedule_changes WHERE iteration_id='+str(i['id']))==diff_count
                pl=copy.deepcopy(before['plan'])
                next(x for x in pl['capacity'] if x['user_id']==self.ids['developer_b'])['available_hours']=39.75
                changed=self.data('changeIteration',params={'iteration_id':i['id']},body={**body,'plan':pl,'reason':'Synthetic unrelated member hours change'},expected=200)
                assert {x['user_id'] for x in changed['plan']['capacity']}=={self.ids['developer_a'],self.ids['developer_b']}
            else:
                changed=self.data('changeIteration',params={'iteration_id':i['id']},body=body,expected=200)
                assert {x['user_id'] for x in changed['plan']['capacity']}=={self.ids['developer_b']}
            assert changed['version']==before['version']+1 and changed['plan_version']==before['plan_version']+1
            self.assert_unchanged(task_before,t['id'])
            rows=self.audit('SELECT capacity FROM iterations WHERE id='+str(i['id']))
            assert len(rows)==1
            stored_capacity=json.loads(rows[0]['capacity'])
            assert {int(x['user_id']) for x in stored_capacity}=={x['user_id'] for x in changed['plan']['capacity']}
            self.log('pending_staff02_state',state=state,blocked_from=blocked_from,iteration_before=before,iteration_after=changed,task=task_before)

    def idem01(self):
        t=self.new_task();tid=t['id'];key=self.prefix+'-old-success-'+secrets.token_hex(4)
        body={'expected_version':t['version'],'action':1}
        first=self.call('transitionTask','developer_a',params={'task_id':tid},body=body,key=key,expected=200)[1]
        self.transition(tid,2,reason='Synthetic newer committed change',responsibility_stage=5,evidence=EVIDENCE)
        newer=self.task(tid);audit_before=self.scalar('SELECT COUNT(*) AS n FROM audit_events WHERE task_id='+str(tid)+' AND outcome=1')
        replay=self.call('transitionTask','developer_a',params={'task_id':tid},body=body,key=key,expected=200)[1]
        assert replay['data']==first['data'] and replay['meta']['replayed'] is True
        assert replay['meta']['original_request_id']==first['meta']['request_id'] and replay['meta']['request_id']!=first['meta']['request_id']
        self.assert_unchanged(newer,tid)
        assert self.scalar('SELECT COUNT(*) AS n FROM audit_events WHERE task_id='+str(tid)+' AND outcome=1')==audit_before
        self.call('transitionTask','developer_a',params={'task_id':tid},body={**body,'expected_version':newer['version']},key=key,expected=409,code='IDEMPOTENCY_CONTENT_CONFLICT')
        other=self.new_task()
        self.call('transitionTask','developer_a',params={'task_id':other['id']},body={'expected_version':other['version'],'action':1},key=key,expected=409,code='IDEMPOTENCY_CONTENT_CONFLICT')
        self.assert_unchanged(other,other['id'])
        b=self.new_task(owner=self.ids['developer_b'])
        self.data('transitionTask','developer_b',params={'task_id':b['id']},body={'expected_version':b['version'],'action':1},key=key,expected=200)
        # Same actor's other operation is proven with two permitted manager writes.
        manager_key=self.prefix+'-manager-operation-'+secrets.token_hex(4)
        c=self.new_task();cb={'expected_version':c['version'],'action':2,'reason':'Synthetic manager scope','responsibility_stage':5,'evidence':EVIDENCE}
        self.data('transitionTask',params={'task_id':c['id']},body=cb,key=manager_key,expected=200)
        created=self.data('createTask',body={'title':self.prefix+'-other-operation-manager','description':'Synthetic operation scope','iteration_id':self.ids['iteration_id'],'owner_id':self.ids['developer_a'],'plan':plan(),'dependency_task_ids':[]},key=manager_key,expected=201)
        records=self.audit('SELECT actor_id,operation_id,status,response_status,response_request_id,HEX(request_hash) AS request_hash FROM idempotency_requests WHERE idempotency_key='+quote(key)+' ORDER BY actor_id,operation_id')
        original=next(r for r in records if int(r['actor_id'])==self.ids['developer_a'] and r['operation_id']=='transitionTask')
        assert int(original['status'])==2 and int(original['response_status'])==200 and original['response_request_id']==first['meta']['request_id'] and len(original['request_hash'])==64
        assert any(int(r['actor_id'])==self.ids['developer_b'] and r['operation_id']=='transitionTask' for r in records)
        self.log('pending_idem01',task_id=tid,newer_task=newer,original_request_id=first['meta']['request_id'],replay_request_id=replay['meta']['request_id'],scope_records=records,manager_other_operation_task_id=created['task']['id'])

    def auth02_remaining(self):
        for state in [7,6]:
            label='owner_'+str(state);uid=self.init_user(label,[2]);i=self.new_iteration([uid]);t=self.new_task(owner=uid,iteration=i['id']);start_key=self.prefix+'-membership-replay-'+str(state)
            self.advance(t,state,owner=label,start_key=start_key);member=self.member(uid);task_before=self.task(t['id'])
            before_i=self.iteration_current(i['id']);pl=copy.deepcopy(before_i['plan']);pl['capacity']=[]
            # Avoid an empty-capacity schema ambiguity: keep an unrelated active developer.
            pl['capacity']=[{'user_id':self.ids['developer_b'],'available_hours':40}]
            self.data('changeIteration',params={'iteration_id':i['id']},body={'expected_version':before_i['version'],'plan':pl,'reason':'Synthetic remove delivered/rolled-back capacity before membership check','evidence':EVIDENCE},expected=200)
            if state==7:
                self.call('changeProjectMember',params={'user_id':uid},body={'expected_version':member['version'],'roles':[3],'reason':'Synthetic active rolled-back developer protection'},expected=409,code='MEMBER_IN_USE')
                self.call('removeProjectMember',params={'user_id':uid},body={'expected_version':member['version'],'reason':'Synthetic rolled-back owner removal'},expected=409,code='MEMBER_IN_USE')
                assert self.member(uid)==member
            else:
                self.data('removeProjectMember',params={'user_id':uid},body={'expected_version':member['version'],'reason':'Synthetic otherwise unused delivered owner removal'},expected=200)
                self.call('getTask',label,params={'task_id':t['id']},expected=403,code='PROJECT_ACCESS_DENIED')
                self.call('transitionTask',label,params={'task_id':t['id']},body={'expected_version':t['version'],'action':1},key=start_key,expected=403,code='PROJECT_ACCESS_DENIED')
            self.assert_unchanged(task_before,t['id'])
            self.log('pending_auth02_owner',state=state,user_id=uid,task_id=t['id'],removed=state==6)

    def page01_tasks(self):
        i=self.new_iteration([self.ids['developer_a']]);end=dt.datetime.now(dt.timezone.utc)+dt.timedelta(days=6)
        tasks=[self.new_task(iteration=i['id'],end=end) for _ in range(205)];ids=[t['id'] for t in tasks]
        assert len(set(ids))==205
        sql=self.audit('SELECT id FROM tasks WHERE project_id='+str(self.ids['project_id'])+' AND iteration_id='+str(i['id'])+' ORDER BY id')
        assert [int(x['id']) for x in sql]==ids
        for size in [1,20,100]:
            found=[]
            for page in range(1,math.ceil(205/size)+1):
                r=self.data('listTasks',query={'iteration_id':i['id'],'page_size':size,'page':page,'sort':'id'},expected=200)
                assert r['total']==205 and r['page_size']==size and r['page']==page
                found.extend(t['id'] for t in r['items'])
            assert found==ids and len(set(found))==205
        for sort in ['planned_end','updated_at']:
            found=[];values=[]
            for page in [1,2,3]:
                r=self.data('listTasks',query={'iteration_id':i['id'],'page_size':100,'page':page,'sort':sort},expected=200)
                found.extend(t['id'] for t in r['items']);values.extend((t['plan']['planned_end'] if sort=='planned_end' else t['updated_at'],t['id']) for t in r['items'])
            assert found==ids and values==sorted(values),'Sort/id tie-break is not stable'
        for size in [0,101]:self.call('listTasks',query={'page_size':size},expected=422,code='PARAMETER_INVALID')
        self.call('listTasks','outsider',query={'iteration_id':i['id']},expected=403,code='PROJECT_ACCESS_DENIED')
        empty=self.data('listTasks',query={'owner_id':2147483646},expected=200);assert empty['total']==0 and empty['items']==[]
        self.log('pending_page01_tasks',iteration_id=i['id'],ids=ids,rows=205,planned_end_tie=True,scope='task pagination only; >100 project members/other record families remain unexecuted')

    def notice_remaining_and_row_replay(self):
        uid=self.init_user('notice_manager',[1]);self.control(['scheduler-scope','--project-id',str(self.ids['project_id'])])
        t=self.new_task(end=dt.datetime.now(dt.timezone.utc)-dt.timedelta(hours=2));tid=t['id']
        deadline=time.monotonic()+105;by_actor={}
        actors=['manager','manager_b','developer_a','notice_manager']
        while time.monotonic()<deadline:
            by_actor={a:[n for n in self.data('listMyNotifications',a,query={'project_id':self.ids['project_id'],'page_size':100},expected=200)['items'] if n['task_id']==tid] for a in actors}
            if all(len(v)==1 for v in by_actor.values()):break
            time.sleep(2)
        if not all(len(v)==1 for v in by_actor.values()):raise Blocked('Actual scheduler/MQ recipient notices not all reached bounded observation; no invented SLA')
        before=self.task(tid);n=by_actor['notice_manager'][0];nid=n['id'];read_key=self.prefix+'-notice-old-read'
        for name,body in [('markNotificationRead',{'expected_version':n['version']}),('handleNotification',{'expected_version':n['version'],'note':'Synthetic other-recipient attempt','evidence':EVIDENCE})]:
            self.call(name,'developer_a',params={'notification_id':nid},body=body,expected=403,code='ACTION_FORBIDDEN')
        read=self.data('markNotificationRead','notice_manager',params={'notification_id':nid},body={'expected_version':n['version']},key=read_key,expected=200)
        assert read['read_at'] and read['handled_at'] is None
        handled=self.data('handleNotification','notice_manager',params={'notification_id':nid},body={'expected_version':read['version'],'note':'Synthetic independent recipient handling','evidence':EVIDENCE},expected=200)
        assert handled['handled_at'] and handled['read_at']==read['read_at'];self.assert_unchanged(before,tid)
        self.notice_fixture=(tid,by_actor,handled,before)
        m=self.member(uid)
        self.data('removeProjectMember',params={'user_id':uid},body={'expected_version':m['version'],'reason':'Synthetic former recipient membership gate'},expected=200)
        self.call('listMyNotifications','notice_manager',query={'project_id':self.ids['project_id']},expected=403,code='PROJECT_ACCESS_DENIED')
        self.call('markNotificationRead','notice_manager',params={'notification_id':nid},body={'expected_version':n['version']},key=read_key,expected=403,code='PROJECT_ACCESS_DENIED')
        self.call('handleNotification','notice_manager',params={'notification_id':nid},body={'expected_version':handled['version'],'note':'Synthetic former recipient retry','evidence':EVIDENCE},expected=403,code='PROJECT_ACCESS_DENIED')
        personal=self.data('listMyNotifications','notice_manager',query={'page_size':100},expected=200)
        assert nid not in {v['id'] for v in personal['items']},'Former member personal list retained protected notice'
        rows=self.audit('SELECT id,recipient_id,version,read_at,handled_at FROM notifications WHERE task_id='+str(tid)+' ORDER BY recipient_id')
        assert len(rows)==4 and {int(x['recipient_id']) for x in rows}=={self.ids['manager_id'],self.ids['manager_b'],self.ids['developer_a'],uid}
        self.assert_unchanged(before,tid)
        self.log('pending_notice01_remaining',task_id=tid,removed_recipient_id=uid,notification_rows=rows)

    def mq_row_replay(self):
        if not hasattr(self,'notice_fixture'):raise Blocked('Actual notice fixture not established; no fabricated event IDs')
        try:import pika
        except ImportError as e:raise Blocked('Neutral locked runtime missing pika') from e
        tid,by_actor,handled,before=self.notice_fixture
        topology=self.context.get('mq_transport',{})
        if (topology.get('exchange'),topology.get('queue'),topology.get('routing_key'))!=('t44.events','t44.notifications','t44.notifications'):raise Blocked('Neutral transport not bound')
        rows=self.audit('SELECT o.id,o.schema_version,o.event_type FROM outbox_events o JOIN escalation_events e ON o.id=e.event_id WHERE e.task_id='+str(tid)+' AND e.project_id='+str(self.ids['project_id']))
        assert len(rows)==1
        wrapper={'event_id':int(rows[0]['id']),'schema_version':int(rows[0]['schema_version']),'event_type':int(rows[0]['event_type'])}
        baseline=self.audit('SELECT id,recipient_id,version,read_at,handled_at FROM notifications WHERE task_id='+str(tid)+' ORDER BY recipient_id')
        connection=pika.BlockingConnection(pika.URLParameters(self.context['amqp_url']))
        try:
            channel=connection.channel();state=channel.queue_declare(queue=topology['queue'],passive=True).method
            if state.consumer_count<1:raise Blocked('No actual broker consumer at row-replay point')
            channel.confirm_delivery()
            for _ in range(2):
                channel.basic_publish(exchange=topology['exchange'],routing_key=topology['routing_key'],body=json.dumps(wrapper,separators=(',',':')).encode(),properties=pika.BasicProperties(content_type='application/json',delivery_mode=2,message_id=str(wrapper['event_id']),type='t44.event.v1'),mandatory=True)
            deadline=time.monotonic()+15
            while time.monotonic()<deadline:
                state=channel.queue_declare(queue=topology['queue'],passive=True).method
                if state.message_count==0:break
                time.sleep(.5)
            if state.message_count:raise Blocked('Constructed actual-row replays not drained from ready queue in bounded window')
        finally:connection.close()
        time.sleep(8)
        after=self.audit('SELECT id,recipient_id,version,read_at,handled_at FROM notifications WHERE task_id='+str(tid)+' ORDER BY recipient_id')
        assert after==baseline,'Actual-row wrapper replay duplicated/reset notices or changed removed recipient snapshot'
        self.assert_unchanged(before,tid)
        self.log('pending_mq_row_replay',actual_wrapper=wrapper,published_count=2,broker_confirmed=True,actual_consumer_count=state.consumer_count,ready_queue_count=state.message_count,notification_rows_unchanged=True,scope='Tester reconstructed neutral3-field wrapper from actual outbox row. Does not prove original publisher capture, commit-before-ACK, ambiguous confirm/fallback race or late original after fallback. Earlier safe-capture BLOCKED remains.')

def main():
    context=json.loads(Path(os.environ['T44_ACCEPTANCE_CONTEXT']).read_text())
    if context.get('product_source_sha')!='4c20f32b71635016815420472b9d4bb4fa850df0':raise Blocked('Exact frozen SUT missing')
    context['independent_phase']='pending-blackbox-subconditions'
    h=Pending(context)
    h.log('pending_binding',original_manifest_sha256='994309f0f394ed42ee01016f6d737de20089c13a72757a459c470e0d29a981e7',original_H='27c9a0a6af10a21eb475ef42c9e98e13b8334a43',H3='99906b1fb1ef376cc819c1a3af9558906331f8c0',H4='2e1917e2e9e1c307bd0fab0ed74ee61de15a71d7',preserved_runs=[39972540073,39998518039],original_assertions_changed=False,source_imported=False,sql_write=False)
    if h.run('SETUP',h.setup)!='PASS':return h.finish()
    for name,fn in [('LIFE-02',h.life02),('DEP-01',h.dep01),('STAFF-02',h.staff02),('IDEM-01',h.idem01),('AUTH-02-REMAINING',h.auth02_remaining),('PAGE-01-TASK-SUBSET',h.page01_tasks),('NOTICE-01-REMAINING',h.notice_remaining_and_row_replay),('MQ-01-ACTUAL-ROW-REPLAY-SUBSET',h.mq_row_replay)]:h.run(name,fn)
    return h.finish()

if __name__=='__main__':
    try:sys.exit(main())
    except Blocked as e:print('BLOCKED: '+str(e));sys.exit(2)
