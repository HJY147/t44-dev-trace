#!/usr/bin/env python3
"""Only previously unexecuted frozen MQ02 fanout and MQ01 row replay.

Does not retry R6's completed cases or reinterpret original-message capture.
The prior count0 stop remains in R6. Subscription count is recorded, never used
as evidence that a basic-get/polling consumer cannot exist.
"""
from pathlib import Path
import datetime as dt
import json
import os
import runpy
import sys
import time

HERE=Path(__file__).resolve().parent
P=runpy.run_path(str(HERE/'913_pending-subconditions.py'),run_name='independent_recipient_parent')
Blocked=P['Blocked'];EVIDENCE=P['EVIDENCE']

class RecipientReplay(P['Pending']):
    def fanout(self):
        # Setup's two managers plus99 newly initialized managers =101 managers.
        manager_ids={self.ids['manager_id'],self.ids['manager_b']}
        for n in range(99):manager_ids.add(self.init_user('fanout_manager_'+str(n).zfill(3),[1]))
        assert len(manager_ids)==101
        recipients=manager_ids|{self.ids['developer_a']};assert len(recipients)==102
        self.control(['scheduler-scope','--project-id',str(self.ids['project_id'])])
        tasks=[self.new_task(end=dt.datetime.now(dt.timezone.utc)-dt.timedelta(hours=2)) for _ in range(20)]
        tids={t['id'] for t in tasks};sql_ids=','.join(map(str,sorted(tids)))
        deadline=time.monotonic()+110;events=[]
        while time.monotonic()<deadline:
            events=[e for e in self.data('listEscalations',query={'page_size':100},expected=200)['items'] if e['task_id'] in tids]
            if len(events)==20:break
            time.sleep(2)
        if len(events)!=20:raise Blocked('Actual20 scheduler events not all observed in bounded window; no invented delivery SLA')
        assert {e['task_id'] for e in events}==tids
        for e in events:assert e['level']==2 and set(e['recipient_ids'])==recipients and len(e['recipient_ids'])==102
        outbox=self.audit('SELECT o.task_id,o.recipients FROM outbox_events o JOIN escalation_events e ON o.id=e.event_id WHERE o.task_id IN ('+sql_ids+') ORDER BY o.task_id')
        assert len(outbox)==20
        for row in outbox:
            actual=json.loads(row['recipients']);assert len(actual)==102 and set(actual)==recipients
        deadline=time.monotonic()+70;counts=[]
        while time.monotonic()<deadline:
            counts=self.audit('SELECT task_id,COUNT(*) AS n,COUNT(DISTINCT recipient_id) AS users FROM notifications WHERE task_id IN ('+sql_ids+') GROUP BY task_id ORDER BY task_id')
            if len(counts)==20 and all(int(r['n'])==102 and int(r['users'])==102 for r in counts):break
            time.sleep(2)
        if len(counts)!=20 or not all(int(r['n'])==102 and int(r['users'])==102 for r in counts):raise Blocked('All102 recipient notifications per20 actual events not yet reached observation window')
        rows=self.audit('SELECT recipient_id,COUNT(*) AS n FROM notifications WHERE task_id IN ('+sql_ids+') GROUP BY recipient_id ORDER BY recipient_id')
        assert {int(r['recipient_id']) for r in rows}==recipients and all(int(r['n'])==20 for r in rows)
        duplicates=self.audit('SELECT event_id,recipient_id,COUNT(*) AS n FROM notifications WHERE task_id IN ('+sql_ids+') GROUP BY event_id,recipient_id HAVING COUNT(*)>1')
        assert duplicates==[]
        notices=[n for n in self.data('listMyNotifications',query={'project_id':self.ids['project_id'],'page_size':100},expected=200)['items'] if n['task_id'] in tids]
        assert len(notices)==20 and all(n['fallback'] is False for n in notices)
        for t in tasks:
            after=self.task(t['id']);assert after['state']==t['state'] and after['version']==t['version']+1 and after['escalation_count']==t['escalation_count']+1
        self.recipient_fixture={'task_ids':tids,'manager_ids':manager_ids,'recipients':recipients,'events':events,'notices':notices}
        self.log('mq02_fanout_observed',actual_managers=101,actual_recipients=102,actual_events=20,actual_notifications=2040,recipient_ids=sorted(recipients),event_ids=[e['id'] for e in events],task_ids=sorted(tids),nested_api_recipient_sets_verified=True,SQL_recipient_sets_verified=True,scope='All101 manager+owner fanout subset only. Does not assert duplicate/fallback simultaneous commit, ambiguous confirm, consumer commit-before-ACK, all-user UI rendering or delivery SLA.')

    def row_replay(self):
        if not hasattr(self,'recipient_fixture'):raise Blocked('Actual fanout event fixture not established; no fabricated ID')
        try:import pika
        except ImportError as e:raise Blocked('Neutral runtime missing real AMQP client') from e
        f=self.recipient_fixture;notice=f['notices'][0];tid=notice['task_id'];before=self.task(tid)
        read=self.data('markNotificationRead',params={'notification_id':notice['id']},body={'expected_version':notice['version']},expected=200)
        handled=self.data('handleNotification',params={'notification_id':notice['id']},body={'expected_version':read['version'],'note':'Synthetic row replay read/handled preservation fixture','evidence':EVIDENCE},expected=200)
        assert read['read_at'] and read['handled_at'] is None and handled['read_at']==read['read_at'] and handled['handled_at']
        rows=self.audit('SELECT o.id,o.schema_version,o.event_type FROM outbox_events o JOIN escalation_events e ON o.id=e.event_id WHERE e.task_id='+str(tid)+' AND e.project_id='+str(self.ids['project_id']))
        assert len(rows)==1
        wrapper={'event_id':int(rows[0]['id']),'schema_version':int(rows[0]['schema_version']),'event_type':int(rows[0]['event_type'])}
        baseline=self.audit('SELECT id,recipient_id,version,read_at,handled_at FROM notifications WHERE task_id='+str(tid)+' ORDER BY recipient_id')
        assert len(baseline)==102
        transport=self.context.get('mq_transport',{})
        if (transport.get('exchange'),transport.get('queue'),transport.get('routing_key'))!=('t44.events','t44.notifications','t44.notifications'):raise Blocked('Neutral actual transport binding missing')
        connection=pika.BlockingConnection(pika.URLParameters(self.context['amqp_url']))
        states=[]
        try:
            channel=connection.channel();q=channel.queue_declare(queue=transport['queue'],passive=True).method
            states.append({'ready_messages':q.message_count,'subscription_consumers':q.consumer_count,'point':'before'})
            channel.confirm_delivery()
            for _ in range(2):
                channel.basic_publish(exchange=transport['exchange'],routing_key=transport['routing_key'],body=json.dumps(wrapper,separators=(',',':')).encode(),properties=pika.BasicProperties(content_type='application/json',delivery_mode=2,message_id=str(wrapper['event_id']),type='t44.event.v1'),mandatory=True)
            deadline=time.monotonic()+20
            while time.monotonic()<deadline:
                q=channel.queue_declare(queue=transport['queue'],passive=True).method
                states.append({'ready_messages':q.message_count,'subscription_consumers':q.consumer_count,'point':'after-publish'})
                if q.message_count==0:break
                time.sleep(.5)
            if q.message_count:raise Blocked('Actual-row messages remain ready beyond observation window; no delivery SLA invented')
        finally:connection.close()
        time.sleep(8)
        after=self.audit('SELECT id,recipient_id,version,read_at,handled_at FROM notifications WHERE task_id='+str(tid)+' ORDER BY recipient_id')
        assert after==baseline,'Actual-row replay duplicated/reset existing recipient notifications'
        self.assert_unchanged(before,tid)
        self.log('mq01_row_replay_observed',wrapper=wrapper,published_count=2,publisher_confirmed=True,broker_queue_observations=states,notification_rows=102,notification_rows_unchanged=True,read_at=read['read_at'],handled_at=handled['handled_at'],scope='Tester reconstructed neutral wrapper from actual row. Ready-queue drain/unchanged SQL are observed; original product publisher bytes, consumer ACK ordering, crash cutpoints, ambiguous confirm and fallback race are not established. R5 original safe capture and R6 subscription-count stop retained unchanged.')

def main():
    context=json.loads(Path(os.environ['T44_ACCEPTANCE_CONTEXT']).read_text())
    if context.get('product_source_sha')!='4c20f32b71635016815420472b9d4bb4fa850df0':raise Blocked('Exact SUT4c not bound')
    context['independent_phase']='pending-recipient-and-row-replay'
    h=RecipientReplay(context)
    h.log('recipient_replay_binding',original_H='27c9a0a6af10a21eb475ef42c9e98e13b8334a43',original_manifest_sha256='994309f0f394ed42ee01016f6d737de20089c13a72757a459c470e0d29a981e7',H5='bfe81d546c812f3708eb1346e34df7690c8e0020',preserved_original_capture_run=39998518039,preserved_count_precondition_run=40003603947,completed_case_methods_selected=False,original_assertions_changed=False,source_accessed=False,SQL_write=False)
    if h.run('SETUP',h.setup)!='PASS':return h.finish()
    h.run('MQ-02-101-MANAGER-FANOUT-SUBSET',h.fanout)
    h.run('MQ-01-ACTUAL-ROW-REPLAY-SUBSET',h.row_replay)
    return h.finish()

if __name__=='__main__':
    try:sys.exit(main())
    except Blocked as e:print('BLOCKED: '+str(e));sys.exit(2)
