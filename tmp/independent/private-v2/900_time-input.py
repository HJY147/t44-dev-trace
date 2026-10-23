#!/usr/bin/env python3
"""Only unexecuted frozen TIME01 write/readback and INPUT01 value boundaries.
No old full case methods or previous readonly boundary samples are rerun.
"""
from pathlib import Path
import copy
import datetime as dt
import json
import os
import runpy
import sys

HERE=Path(__file__).resolve().parent
P=runpy.run_path(str(HERE/'913_pending-subconditions.py'),run_name='own_time_input_parent')
Blocked=P['Blocked'];plan=P['plan']

class TimeInput(P['Pending']):
    def payload(self):
        return {'title':self.prefix+'-time-input','description':'Synthetic original frozen boundary fixture','iteration_id':self.ids['iteration_id'],'owner_id':self.ids['developer_a'],'plan':plan(),'dependency_task_ids':[]}

    def count(self):return self.scalar('SELECT COUNT(*) AS n FROM tasks WHERE project_id='+str(self.ids['project_id']))

    def valid_time_write(self,label,start,end):
        body=self.payload();body['plan']['planned_start']=start;body['plan']['planned_end']=end
        t=self.data('createTask',body=body,expected=201)['task']
        parse=lambda value:dt.datetime.fromisoformat(value.replace('Z','+00:00'))
        assert parse(t['plan']['planned_start'])==parse(start) and parse(t['plan']['planned_end'])==parse(end)
        rows=self.audit('SELECT planned_start,planned_end FROM tasks WHERE id='+str(t['id'])+' AND project_id='+str(self.ids['project_id']))
        assert len(rows)==1
        for field,expected in [('planned_start',start),('planned_end',end)]:
            stored=dt.datetime.fromisoformat(rows[0][field]);wanted=dt.datetime.fromisoformat(expected.replace('Z','+00:00')).replace(tzinfo=None)
            assert stored==wanted,'Stored UTC boundary/microseconds differ from accepted input'
        self.log('time_write_readback',label=label,task_id=t['id'],request_start=start,request_end=end,SQL=rows,scope='Actual createTask write and SELECT readback; earlier readonly validation evidence remains separate')

    def invalid_time_write(self,label,start,end,code):
        body=self.payload();body['plan']['planned_start']=start;body['plan']['planned_end']=end;before=self.count()
        self.call('createTask',body=body,expected=422,code=code)
        assert self.count()==before,'Rejected time boundary created a task'
        self.log('time_invalid_write',label=label,created_tasks=0)

    def body_invalid(self,label,mutate,expected=422,code='PARAMETER_INVALID'):
        body=self.payload();mutate(body);before=self.count()
        self.call('createTask',body=body,expected=expected,code=code)
        assert self.count()==before,'Rejected input boundary created a task'
        self.log('input_invalid_value',label=label,created_tasks=0)

    def numeric_integer_and_direct_override(self):
        body=self.payload();body['iteration_id']=float(body['iteration_id']);body['owner_id']=float(body['owner_id'])
        t=self.data('createTask',body=body,expected=201)['task']
        assert t['iteration_id']==self.ids['iteration_id'] and t['owner_id']==self.ids['developer_a']
        for label,extra in [('bool_version',{'expected_version':True,'action':1}),('string_version',{'expected_version':str(t['version']),'action':1}),('target_state',{'expected_version':t['version'],'action':1,'target_state':2})]:
            before=self.task(t['id'])
            self.call('transitionTask','developer_a',params={'task_id':t['id']},body=extra,expected=422,code='PARAMETER_INVALID')
            self.assert_unchanged(before,t['id']);self.log('input_transition_invalid',label=label,task_id=t['id'])
        started=self.data('transitionTask','developer_a',params={'task_id':t['id']},body={'expected_version':float(t['version']),'action':1.0},expected=200)['task']
        assert started['state']==2 and started['version']==t['version']+1
        self.log('input_integer_numeric',task_id=t['id'],body_numeric_integer_ids_accepted=True,body_numeric_integer_version_action_accepted=True,bool_and_string_rejected=True,target_state_rejected=True)

    def normal_quote(self):
        body=self.payload();body['title']="O'Brien SELECT statement is ordinary task prose";body['description']="Synthetic explanation: SQL discussion and apostrophe aren't selector injection"
        t=self.data('createTask',body=body,expected=201)['task'];assert t['title']==body['title']
        rows=self.audit('SELECT title,description FROM tasks WHERE id='+str(t['id']))
        assert rows==[{'title':body['title'],'description':body['description']}]
        self.log('input_normal_quote',task_id=t['id'],accepted_and_stored_exact=True)

def main():
    context=json.loads(Path(os.environ['T44_ACCEPTANCE_CONTEXT']).read_text())
    if context.get('product_source_sha')!='4c20f32b71635016815420472b9d4bb4fa850df0':raise Blocked('Exact original SUT missing')
    context['independent_phase']='pending-time-input-boundaries';h=TimeInput(context)
    h.log('time_input_binding',original_H='27c9a0a6af10a21eb475ef42c9e98e13b8334a43',original_manifest_sha256='994309f0f394ed42ee01016f6d737de20089c13a72757a459c470e0d29a981e7',preserved_runs=[39972540073,40003603947,40005729957],completed_case_methods_selected=False,original_assertions_changed=False,product_source_access=False,SQL_write=False)
    if h.run('SETUP',h.setup)!='PASS':return h.finish()
    for label,start,end in [('minimum','1000-01-01T00:00:00Z','1000-01-02T00:00:00.123456Z'),('maximum','9999-12-30T23:59:59.123456Z','9999-12-31T23:59:59.999999Z')]:
        h.run('TIME-01-WRITE-'+label,lambda l=label,s=start,e=end:h.valid_time_write(l,s,e))
    invalid=[('0001','0001-01-01T00:00:00Z','0001-01-02T00:00:00Z','PARAMETER_INVALID'),('0999','0999-01-01T00:00:00Z','0999-01-02T00:00:00Z','PARAMETER_INVALID'),('10000','10000-01-01T00:00:00Z','10000-01-02T00:00:00Z','PARAMETER_INVALID'),('offset','2026-10-30T00:00:00+00:00','2026-10-31T00:00:00Z','PARAMETER_INVALID'),('calendar','2026-02-30T00:00:00Z','2026-03-02T00:00:00Z','PARAMETER_INVALID'),('7microseconds','2026-10-30T00:00:00.1234567Z','2026-10-31T00:00:00Z','PARAMETER_INVALID'),('equal','2026-10-30T00:00:00Z','2026-10-30T00:00:00Z','TIME_RANGE_INVALID'),('reverse','2026-10-31T00:00:00Z','2026-10-30T00:00:00Z','TIME_RANGE_INVALID')]
    for label,start,end,code in invalid:h.run('TIME-01-WRITE-'+label,lambda l=label,s=start,e=end,c=code:h.invalid_time_write(l,s,e,c))
    for label,change in [('bool_owner',lambda b:b.update(owner_id=True)),('string_owner',lambda b:b.update(owner_id=str(b['owner_id']))),('bool_hours',lambda b:b['plan'].update(estimated_hours=True)),('string_hours',lambda b:b['plan'].update(estimated_hours='8')),('nonquarter_hours',lambda b:b['plan'].update(estimated_hours=.1)),('direct_state',lambda b:b.update(state=2))]:h.run('INPUT-01-VALUE-'+label,lambda l=label,m=change:h.body_invalid(l,m))
    h.run('INPUT-01-VALUE-NUL',lambda:h.body_invalid('NUL',lambda b:b.update(title='Synthetic\x00control'),400,'SECURITY_INPUT_REJECTED'))
    h.run('INPUT-01-NUMERIC-INTEGER-AND-TARGET',h.numeric_integer_and_direct_override)
    h.run('INPUT-01-TASK-NORMAL-QUOTE',h.normal_quote)
    return h.finish()

if __name__=='__main__':
    try:sys.exit(main())
    except Blocked as e:print('BLOCKED: '+str(e));sys.exit(2)
