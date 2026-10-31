import copy, importlib.util
from pathlib import Path
p=Path(__file__).parent
s=importlib.util.spec_from_file_location('bootstrap',p/'bootstrap.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b)
def fixture():
 rows=[];tasks={1:{}}
 for i in range(400):
  t={'id':i+1,'project_id':1,'owner_id':2,'state':3 if i%2 else 2,'blocked_from_state':2 if i%2 else None,'version':2086}
  rows.append({'project_id':1,'transition_task':{'id':i+1}});tasks[1][i+1]=t
 return {'inventory':{'clients':rows}},tasks
class API:
 def __init__(self,t,fail=False):self.t=copy.deepcopy(t);self.writes=0;self.fail=fail
 def request(self,path,token,body=None,**kw):
  task=self.t[1][int(path.split('/')[4])]
  if body:
   self.writes+=1
   assert body['action']==3 and body['expected_version']==task['version'] and token=='developer' and kw['idempotency_key'].startswith('p18-unblock-')
   if self.fail:raise ValueError('VERSION_CONFLICT')
   task.update(state=2,blocked_from_state=None,version=task['version']+1)
  return copy.deepcopy(task),{}
sessions={'developer':{'user_id':2,'token':'developer'}}
old,tasks=fixture();api=API(tasks)
r=b.normalize_transition_tasks(old,sessions,tasks,api,'r30posttools18');assert r['unblocked']==200
r=b.normalize_transition_tasks(old,sessions,tasks,api,'r30posttools19');assert r['unblocked']==0 and api.writes==200
for key,value in [('state',4),('owner_id',9),('blocked_from_state',1)]:
 old,t=fixture();t[1][400][key]=value;api=API(t)
 try:b.normalize_transition_tasks(old,sessions,t,api,'r30posttools18');raise AssertionError('must reject')
 except ValueError:assert api.writes==0
old,t=fixture();api=API(t,True)
try:b.normalize_transition_tasks(old,sessions,t,api,'r30posttools18');raise AssertionError('must reject')
except ValueError:assert api.writes==1
print('PASS mixed400, repeat, all-precheck invalid state/owner/from-state, ambiguous write no retry')
