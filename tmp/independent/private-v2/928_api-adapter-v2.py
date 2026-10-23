#!/usr/bin/env python3
"""Preserve all original expectations; choose exact frozen success status for fixture helper.

Run39969411769 correctly returned201 for addTaskDependency; the independent generic
mutation fixture had defaulted to200. This adapter derives the single successstatus
from the already frozen operation schema, without accepting a wider status set.
Additional service-API execution implements only pre-SUT frozen AUTH/SCAN/NOTICE recipes.
"""
from pathlib import Path
import datetime as dt
import json
import os
import runpy
import secrets
import sys
import time

HERE=Path(__file__).resolve().parent
PREVIOUS=runpy.run_path(str(HERE/'939_runtime-adapter.py'),run_name='independent_adapter_v1')
OPS=PREVIOUS['OPS'];Blocked=PREVIOUS['Blocked'];EVIDENCE=PREVIOUS['EVIDENCE']

class AdapterV2(PREVIOUS['RuntimeAdapter']):
    def mutation(self,name,*args,**kwargs):
        if 'expected' not in kwargs:
            allowed=[int(status) for status in OPS[name][2]['responses'] if status.startswith('2')]
            assert len(allowed)==1,'Frozen operation does not have a single successstatus'
            kwargs['expected']=allowed[0]
        return super().mutation(name,*args,**kwargs)

    def service_api(self):
        self.control(['scheduler-scope','--project-id',str(self.ids['project_id'])])
        warm=self.new_task(end=dt.datetime.now(dt.timezone.utc)-dt.timedelta(hours=2))
        deadline=time.monotonic()+100;events=[]
        while time.monotonic()<deadline:
            events=self.data('listEscalations',query={'task_id':warm['id'],'page_size':100},expected=200)['items']
            if events:break
            time.sleep(2)
        if not events:raise Blocked('No actual scheduler scan_run_id available; no guessed UUID used')
        run_id=events[0]['scan_run_id']
        issued_at=time.monotonic()
        raw=self.control(['service-credential','--project-id',str(self.ids['project_id']),'--ttl-seconds','60'])
        try:credential=json.loads(raw)
        except json.JSONDecodeError as exc:raise Blocked('Neutral service-credential response is not documented JSON') from exc
        def find_token(value):
            if isinstance(value,dict):
                for key,item in value.items():
                    if key in ('access_token','token') and isinstance(item,str):return item
                for item in value.values():
                    found=find_token(item)
                    if found:return found
            return None
        token=find_token(credential)
        if not token:raise Blocked('Neutral service-credential JSON has no actual token/access_token field')
        self.secrets.append(token);self.actor['service']={'access_token':token}
        t=self.new_task(end=dt.datetime.now(dt.timezone.utc)-dt.timedelta(hours=2));before=self.task(t['id'])
        body={'expected_version':before['version'],'schedule_version':before['schedule_version'],'rule_version':self.rules['version'],'scan_run_id':run_id}
        self.call('createEscalation','manager',params={'task_id':t['id']},body=body,expected=403,code='SERVICE_SCOPE_REQUIRED')
        self.assert_unchanged(before,t['id'])
        key=self.prefix+'-service-positive-'+secrets.token_hex(6)
        first=self.call('createEscalation','service',params={'task_id':t['id']},body=body,key=key,expected=202)[1]
        after=self.task(t['id']);assert first['data']['created'] is True
        assert after['version']==before['version']+1 and after['escalation_count']==before['escalation_count']+1
        assert set(first['data']['event']['recipient_ids'])=={self.ids['manager_id'],self.ids['manager_b'],self.ids['developer_a']}
        replay=self.call('createEscalation','service',params={'task_id':t['id']},body=body,key=key,expected=202)[1]
        assert replay['data']==first['data'] and replay['meta']['replayed'] and replay['meta']['original_request_id']==first['meta']['request_id']
        current={**body,'expected_version':after['version']}
        duplicate=self.data('createEscalation','service',params={'task_id':t['id']},body=current,expected=202)
        assert duplicate['created'] is False and duplicate['event']['id']==first['data']['event']['id']
        self.assert_unchanged(after,t['id'])
        wrong_rule={**current,'rule_version':self.rules['version']+1}
        self.call('createEscalation','service',params={'task_id':t['id']},body=wrong_rule,expected=409,code='RULE_VERSION_CONFLICT')
        self.assert_unchanged(after,t['id'])
        deadline=time.monotonic()+30;notices=[]
        while time.monotonic()<deadline:
            notices=[n for n in self.data('listMyNotifications',query={'project_id':self.ids['project_id'],'page_size':100},expected=200)['items'] if n['task_id']==t['id']]
            if notices:break
            time.sleep(1)
        if not notices:raise Blocked('Actual MQ notification not observed in bounded window; no undocumented delivery SLA invented')
        notice=notices[0]
        read=self.data('markNotificationRead',params={'notification_id':notice['id']},body={'expected_version':notice['version']},expected=200)
        assert read['read_at'] and read['handled_at'] is None
        handled=self.data('handleNotification',params={'notification_id':notice['id']},body={'expected_version':read['version'],'note':'Independent synthetic actual handling','evidence':EVIDENCE},expected=200)
        assert handled['handled_at'] and handled['read_at']==read['read_at'];self.assert_unchanged(after,t['id'])
        remaining=issued_at+65-time.monotonic()
        if remaining>0:time.sleep(remaining)
        self.call('createEscalation','service',params={'task_id':t['id']},body=current,expected=401,code='TOKEN_EXPIRED')
        self.assert_unchanged(after,t['id'])
        self.log('service_case_complete',task_id=t['id'],event_id=first['data']['event']['id'],actual_scan_run_id=run_id,synthetic_service_expiry_observed=True)

    def finish(self):
        if self.phase=='blackbox' and not getattr(self,'service_case_attempted',False) and 'developer_a' in self.actor and hasattr(self,'rules'):
            self.service_case_attempted=True
            self.run('AUTH-SCAN-NOTICE-SERVICE-SUBSET',self.service_api)
        return super().finish()

PREVIOUS['run_adapter'].__globals__['RuntimeAdapter']=AdapterV2
if __name__=='__main__':
    try:sys.exit(PREVIOUS['run_adapter']())
    except Blocked as exc:print('BLOCKED: '+str(exc));sys.exit(2)
