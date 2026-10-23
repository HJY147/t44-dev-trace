#!/usr/bin/env python3
"""Frozen real-service fault probes. Uses only neutral leased controls + HTTP + read-only audit."""
from __future__ import annotations
import datetime as dt
import json
import time


def run(h):
    from __main__ import Blocked,EVIDENCE,plan
    selected=h.context.get('independent_fault_case','scan20')
    def recover():
        text=h.control(['recover'])
        try:value=json.loads(text)
        except json.JSONDecodeError:raise Blocked('Recovery control output is not a structured recovery receipt; tester must verify recovery_completed')
        # Accept explicit receipt only, never infer success from finally or exit0 alone.
        values=[value]
        if isinstance(value,dict):values.extend(v for v in value.values() if isinstance(v,dict))
        if not any(v.get('recovery_completed') is True for v in values if isinstance(v,dict)):
            raise Blocked('Neutral recovery receipt lacks recovery_completed=true')
        h.log('recovery_receipt',receipt=value)
    def fault(service,action='stop',seconds=120):
        if service not in ('mysql','rabbitmq','api','consumer','scheduler','web'):raise ValueError('Unapprovedservice')
        if action not in ('stop','pause') or not 1<=seconds<=120:raise ValueError('Unapprovedleasedaction')
        h.control(['fault','--service',service,'--action',action,'--lease-seconds',str(seconds)])
    def wait_until(check,seconds,description):
        deadline=time.monotonic()+seconds
        last=None
        while time.monotonic()<deadline:
            last=check()
            if last:return last
            time.sleep(2)
        raise Blocked('Observationdeadline reached for '+description+'; no undocumented SLA invented; preserve partial observations')
    def page(name,who='manager',query=None):
        return h.data(name,who,query={'page_size':100,**(query or {})},expected=200)['items']
    def event_for(tid):return page('listEscalations',query={'task_id':tid})
    def scanner_scope():
        h.control(['scheduler-scope','--project-id',str(h.ids['project_id'])])
    def scan20():
        scanner_scope()
        tasks=[h.new_task(end=dt.datetime.now(dt.timezone.utc)-dt.timedelta(hours=2)) for _ in range(20)]
        for t in tasks[:5]:h.transition(t['id'],2,'manager',reason='Synthetic overdue blocked item',responsibility_stage=5,evidence=EVIDENCE)
        before={t['id']:h.task(t['id']) for t in tasks}
        def all_events():
            events={t['id']:event_for(t['id']) for t in tasks}
            return events if all(events.values()) else None
        events=wait_until(all_events,150,'actual scheduler20event coverage over two60second intervals')
        expected_recipients={h.ids['manager_id'],h.ids['manager_b'],h.ids['developer_a']}
        for tid,items in events.items():
            assert len(items)==1 and items[0]['level']==2,'First overdue scan mustcreateonlylevel2 once'
            assert set(items[0]['recipient_ids'])==expected_recipients,'Recipient snapshot mismatch'
            after=h.task(tid);assert after['escalation_count']==before[tid]['escalation_count']+1
            assert after['version']==before[tid]['version']+1 and after['state']==before[tid]['state']
        ids=','.join(str(t['id']) for t in tasks)
        h.audit('SELECT id,HEX(run_key) AS run_key,status,last_task_id,scanned_count,created_count,duplicate_count,started_at,heartbeat_at,finished_at FROM scan_runs ORDER BY id')
        h.audit('SELECT task_id,schedule_version,level,event_id FROM escalation_events WHERE task_id IN ('+ids+') ORDER BY task_id')
        # Real scheduler restart, then a whole scanning interval; old observations are not treated as evidence of retry.
        fault('scheduler',seconds=2)
        recover()
        time.sleep(65)
        for tid,original in events.items():
            current=event_for(tid);assert [(x['id'],x['level']) for x in current]==[(x['id'],x['level']) for x in original], 'Rescan/restart duplicated event'
            after=h.task(tid);assert after['escalation_count']==before[tid]['escalation_count']+1
        h.audit('SELECT id,HEX(run_key) AS run_key,status,last_task_id,scanned_count,created_count,duplicate_count,started_at,finished_at FROM scan_runs ORDER BY id')
        # Cursor-interruption injection is a separate condition. A clean restart must not be called interruption recovery.
        h.phase_artifact={'scan20_task_ids':[t['id'] for t in tasks],'proved':'actual20events,recipientsets,repeatinterval+processrestart,noAPIduplicate','not_proved':['crash during mid-batch cursor advancement','selectivecommitfailure','all transaction races']}
    def mq_fallback():
        scanner_scope()
        fault('rabbitmq',seconds=120)
        try:
            tasks=[h.new_task(end=dt.datetime.now(dt.timezone.utc)-dt.timedelta(hours=2)) for _ in range(20)]
            tids={t['id'] for t in tasks}
            def all_todos():
                notices=page('listMyNotifications')
                selected_notices=[n for n in notices if n['task_id'] in tids]
                return selected_notices if len(selected_notices)==20 and all(n['fallback'] for n in selected_notices) else None
            notices=wait_until(all_todos,105,'MQdownmarkedfallbacktodos')
            first=notices[0];tid=first['task_id'];task_before=h.task(tid)
            read=h.data('markNotificationRead',params={'notification_id':first['id']},body={'expected_version':first['version']},expected=200)
            assert read['read_at'] is not None and read['handled_at'] is None
            handled=h.data('handleNotification',params={'notification_id':first['id']},body={'expected_version':read['version'],'note':'Synthetic independent handling record','evidence':EVIDENCE},expected=200)
            assert handled['handled_at'] is not None and handled['read_at']==read['read_at']
            assert h.task(tid)==task_before,'Notification changedtaskstate/version'
            before_ids={n['id'] for n in notices}
        finally:recover()
        time.sleep(10)
        after=[n for n in page('listMyNotifications') if n['task_id'] in tids]
        assert {n['id'] for n in after}==before_ids,'Recovery duplicated fallbacknotifications'
        keep=next(n for n in after if n['id']==first['id']);assert keep['read_at']==read['read_at'] and keep['handled_at']==handled['handled_at']
        fresh=h.new_task(end=dt.datetime.now(dt.timezone.utc)-dt.timedelta(hours=2))
        normal=wait_until(lambda:[n for n in page('listMyNotifications') if n['task_id']==fresh['id']],100,'newnormalMQnotificationafterrecovery')
        assert len(normal)==1 and normal[0]['fallback'] is False,'New event not normalMQ afterrecovery'
        h.audit('SELECT id,event_type,task_id,status,attempts,confirmed_at,fallback_at,last_error_code FROM outbox_events WHERE task_id IN ('+','.join(str(t) for t in sorted(tids|{fresh['id']}))+') ORDER BY id')
        h.phase_artifact={'mq_fallback_task_ids':sorted(tids),'not_proved':['ambiguouspublisherconfirm','lateoriginalMQdelivery afterfallback','consumer/fallbacksimultaneouscommit']}
    def committed_restart():
        t=h.new_task();h.transition(t['id'],1);before=h.task(t['id'])
        h.audit('SELECT id,task_id,operation_id,outcome,reason_code,request_id FROM audit_events WHERE task_id='+str(t['id'])+' ORDER BY id')
        fault('api',seconds=2)
        recover()
        deadline=time.monotonic()+45
        while True:
            try:after=h.task(t['id']);break
            except AssertionError:
                if time.monotonic()>=deadline:raise
                time.sleep(1)
        assert after==before,'Committed data lost afterAPIrestart'
        h.audit('SELECT id,task_id,operation_id,outcome,reason_code,request_id FROM audit_events WHERE task_id='+str(t['id'])+' ORDER BY id')
        h.phase_artifact={'restart_task_id':t['id'],'not_proved':['transactionabortbeforecommit','lostcommitack','audit-onlyfailure']}
    def db_down():
        t=h.new_task();before=h.task(t['id']);fault('mysql',seconds=15)
        try:
            status,value,_=h.call('getTask',params={'task_id':t['id']},expected=503)
            assert value['code'] in ('DEPENDENCY_UNAVAILABLE','AUDIT_UNAVAILABLE')
            assert value['audit_id'] is None,'Database outage falselyclaimedpersistedaudit'
        finally:recover()
        assert h.task(t['id'])==before
    def duplicate_message():
        topology=h.context.get('independent_mq_topology')
        if not topology or not topology.get('queue'):raise Blocked('Neutralactualqueue/routingmetadata required; do not guess productqueue names')
        try:import pika
        except ImportError as e:raise Blocked('Lockedruntime lacks pika') from e
        scanner_scope();fault('consumer',seconds=120)
        captured=None;connection=None
        try:
            t=h.new_task(end=dt.datetime.now(dt.timezone.utc)-dt.timedelta(hours=2))
            wait_until(lambda:event_for(t['id']),90,'actualscheduler eventbeforeMQcapture')
            connection=pika.BlockingConnection(pika.URLParameters(h.context['amqp_url']));channel=connection.channel()
            deadline=time.monotonic()+15
            while time.monotonic()<deadline:
                method,properties,body=channel.basic_get(queue=topology['queue'],auto_ack=False)
                if not method:time.sleep(.5);continue
                try:payload=json.loads(body)
                except Exception:payload={}
                if str(t['id']) in json.dumps(payload) and ('escalation' in json.dumps(payload) or topology.get('event_match_confirmed_by_tester')):
                    captured=(properties,body);channel.basic_nack(delivery_tag=method.delivery_tag,requeue=True);break
                channel.basic_nack(delivery_tag=method.delivery_tag,requeue=True)
                raise Blocked('Actualqueuemessageidentification requires neutralwrappermetadata; no guessedbusinesspayload')
            if not captured:raise Blocked('No safelyidentifiableoriginalMQmessagecaptured')
        finally:
            if connection:connection.close()
            recover()
        notice=wait_until(lambda:[n for n in page('listMyNotifications') if n['task_id']==t['id']],30,'originalnotification')
        n=notice[0];read=h.data('markNotificationRead',params={'notification_id':n['id']},body={'expected_version':n['version']},expected=200)
        connection=pika.BlockingConnection(pika.URLParameters(h.context['amqp_url']))
        try:
            channel=connection.channel();channel.confirm_delivery()
            channel.basic_publish(exchange='',routing_key=topology['queue'],body=captured[1],properties=captured[0],mandatory=True)
        finally:connection.close()
        time.sleep(5)
        after=[x for x in page('listMyNotifications') if x['task_id']==t['id']]
        assert len(after)==1 and after[0]['id']==n['id'] and after[0]['read_at']==read['read_at'],'DuplicateMQ reset/duplicatednotice'
    mapping={'scan20':('SCAN-01-SUBSET',scan20),'mq-fallback':('MQ-01-SUBSET',mq_fallback),'api-restart':('TX-01-RESTART-SUBSET',committed_restart),'db-down':('TX-01-DBDOWN-SUBSET',db_down),'mq-duplicate':('MQ-01-DUPLICATE-SUBSET',duplicate_message)}
    if selected not in mapping:raise Blocked('Select one frozen fault case perboundedjob')
    case,fn=mapping[selected]
    h.run(case,fn)
