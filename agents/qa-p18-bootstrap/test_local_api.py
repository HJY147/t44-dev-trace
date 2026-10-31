"""Actual frozen FastAPI/Runtime/Workflow with local SQLite, synthetic seeded data."""
import sys, uuid, unittest
from datetime import datetime,UTC,timedelta
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from t44.persistence.schema import metadata,TABLES
from t44.persistence import SqlAlchemyUnitOfWorkFactory
from t44.api import create_app
from t44.services.identity import token_digest
from t44.services.common import task_model
from test_independent import b,fixture

class LocalAPI(unittest.TestCase):
 def setUp(self):
  self.engine=create_engine('sqlite://',connect_args={'check_same_thread':False},poolclass=StaticPool)
  metadata.create_all(self.engine);self.factory=SqlAlchemyUnitOfWorkFactory(self.engine)
  self.token='independent-synthetic-token-00000000000000000';self.at=datetime.now(UTC)
  with self.factory() as u:
   g=u.gateway
   def row(name,**kw):
    values={}
    for c in TABLES[name].c:
     if c.name in kw:continue
     if c.nullable:values[c.name]=None
     elif c.server_default is not None:continue
     elif c.name=='id':continue
     elif 'DATETIME' in str(c.type):values[c.name]=self.at
     elif 'INT' in str(c.type):values[c.name]=1
     elif 'JSON' in str(c.type):values[c.name]=[]
     elif 'BINARY' in str(c.type):values[c.name]=b'0'*16
     else:values[c.name]='synthetic'
    return g.insert(name,{**values,**kw})
   row('users',id=2,username='synthetic',active=1)
   row('projects',id=1,created_by=2)
   row('project_members',id=1,project_id=1,user_id=2,roles_mask=2,active=1)
   row('iterations',id=1,project_id=1,planned_start=self.at,planned_end=self.at+timedelta(days=1))
   row('tasks',id=1,project_id=1,iteration_id=1,owner_id=2,state=3,blocked_from_state=2,version=7,
    planned_start=self.at,planned_end=self.at+timedelta(days=1),estimated_quarters=4,buffer_quarters=0)
   row('tasks',id=2,project_id=1,iteration_id=1,owner_id=2,state=1,version=1,
    planned_start=self.at,planned_end=self.at+timedelta(days=1),estimated_quarters=4,buffer_quarters=0)
   row('auth_sessions',id=1,actor_kind=1,user_id=2,service_account_id=None,token_hash=token_digest(self.token),expires_at=self.at+timedelta(hours=1),revoked_at=None,project_ids=[],scopes=[])
  self.client=TestClient(create_app(factory=self.factory,notifications=None,escalations=None))
 def tearDown(self):self.client.close();self.engine.dispose()
 def post(self,version=7):
  return self.client.post('/api/v1/projects/1/tasks/1/transitions',headers={'Authorization':'Bearer '+self.token,'Idempotency-Key':str(uuid.uuid4())},json={'action':3,'expected_version':version,'basis':'合成初始化','evidence':[{'kind':2,'locator':'synthetic/local','description':'合成证据'}]})
 def test_unblock_and_block_frozen_first_action(self):
  p=self.post();self.assertEqual(p.status_code,200,p.text)
  r=self.client.get('/api/v1/projects/1/tasks/1',headers={'Authorization':'Bearer '+self.token});self.assertEqual(r.status_code,200,r.text);self.assertEqual((r.json()['data']['state'],r.json()['data']['version']),(2,8))
  p=self.client.post('/api/v1/projects/1/tasks/1/transitions',headers={'Authorization':'Bearer '+self.token,'Idempotency-Key':str(uuid.uuid4())},json={'action':2,'expected_version':8,'reason':'合成测量首动作','responsibility_stage':2,'evidence':[{'kind':2,'locator':'synthetic/local','description':'合成'}]});self.assertEqual(p.status_code,200,p.text)
 def test_cas_denial(self):
  p=self.post(6);self.assertEqual((p.status_code,p.json()['code']),(409,'VERSION_CONFLICT'))
 def test_permission_denial(self):
  with self.factory() as u:u.gateway.update('project_members',{'id':1},{'roles_mask':1})
  p=self.post();self.assertEqual((p.status_code,p.json()['code']),(403,'ACTION_FORBIDDEN'))
 def test_dependency_denial(self):
  with self.factory() as u:u.gateway.insert('task_dependencies',{'project_id':1,'task_id':1,'depends_on_task_id':2,'created_by':2,'created_at':self.at})
  p=self.post();self.assertEqual((p.status_code,p.json()['code']),(409,'DEPENDENCIES_UNSATISFIED'))
 def test_bootstrap_real_api_request_path(self):
  old,tasks=fixture()
  with self.factory() as u:tasks[1][1]=task_model(u.gateway.get('tasks',1))
  outer=self
  class Adapter:
   def __init__(self):self.calls=[]
   def request(self,path,token=None,body=None,**kw):
    self.calls.append(path);h={'Authorization':'Bearer '+token}
    if body is not None:h['Idempotency-Key']=kw['idempotency_key']
    v=outer.client.request('POST' if body is not None else 'GET','/api/v1'+path,headers=h,json=body)
    if v.status_code!=200:raise ValueError(v.text)
    return v.json()['data'],v.json().get('meta')
  adapter=Adapter();value=b.normalize_transition_tasks(old,{'developer':{'user_id':2,'token':self.token}},tasks,adapter,'synthetic-r30posttools18')
  self.assertEqual(value['unblocked'],1);self.assertEqual(tasks[1][1]['version'],8);self.assertEqual(len(adapter.calls),2)
if __name__=='__main__':unittest.main(verbosity=2)
