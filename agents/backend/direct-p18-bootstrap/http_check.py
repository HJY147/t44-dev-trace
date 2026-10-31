import importlib.util, pathlib, copy
ROOT=pathlib.Path(__file__).resolve().parents[3]
def load(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
b=load('b',pathlib.Path(__file__).with_name('bootstrap.py'));h=load('h',ROOT/'tmp/backend/contracts/986_http.py');c=load('c',ROOT/'tmp/backend/contracts/conftest.py')
g=c.application.__wrapped__();client,factory=next(g)
try:
 tokens,pid,iid=h.setup_project(client);t=h.create_task(client,tokens,pid,iid);t=h.transition(client,tokens['developer'],pid,t,1)
 def block(t):return h.transition(client,tokens['developer'],pid,t,2,reason='Synthetic previous cohort',responsibility_stage=2,evidence=h.EVIDENCE)
 t=block(t)
 assert h.transition(client,tokens['developer'],pid,t,2,expect=409,reason='duplicate',responsibility_stage=2,evidence=h.EVIDENCE).json()['code']=='STATE_CONFLICT'
 class API:
  def request(self,path,token,body=None,**kw):
   response=client.request('POST' if body else 'GET','/api/v1'+path,json=body,headers={'Authorization':'Bearer '+token, 'Idempotency-Key':kw.get('idempotency_key','unused-key-123456')})
   assert response.status_code==200,response.text
   return response.json()['data'],response.json()['meta']
 def normalize(t,run):
  ts={pid:{t['id']:copy.deepcopy(t)}};rows=[{'project_id':pid,'transition_task':{'id':t['id']}}]
  for i in range(399):
   tid=10000+i;ts[pid][tid]=dict(t,id=tid,state=2);rows.append({'project_id':pid,'transition_task':{'id':tid}})
  r=b.normalize_transition_tasks({'inventory':{'clients':rows}},{'developer':{'user_id':2,'token':tokens['developer']}},ts,API(),run)
  assert r['unblocked']==1
  return ts[pid][t['id']]
 t=normalize(t,'round1');t=block(t);t=normalize(t,'round2');assert t['state']==2
 blocked=block(t)
 stale=dict(blocked,version=blocked['version']-1)
 assert h.transition(client,tokens['developer'],pid,stale,3,expect=409,basis='x',evidence=h.EVIDENCE).json()['code']=='VERSION_CONFLICT'
 assert h.transition(client,tokens['manager'],pid,blocked,3,expect=403,basis='x',evidence=h.EVIDENCE).json()['code']=='ACTION_FORBIDDEN'
 predecessor=h.create_task(client,tokens,pid,iid)
 from datetime import datetime,UTC
 with factory() as uow:
  uow.gateway.insert('task_dependencies',{'project_id':pid,'task_id':blocked['id'],'depends_on_task_id':predecessor['id'],'created_by':1,'created_at':datetime.now(UTC)})
  uow.commit()
 assert h.transition(client,tokens['developer'],pid,blocked,3,expect=409,basis='x',evidence=h.EVIDENCE).json()['code']=='DEPENDENCIES_UNSATISFIED'
 print('PASS actual SQLite/TestClient state3 duplicate BLOCK409, legal normalization UNBLOCK, next BLOCK, repeated normalization, manager403, stale CAS409, seeded dependency guard409; 398 state2 synthetic no-op rows')
finally:
 try:next(g)
 except StopIteration:pass
