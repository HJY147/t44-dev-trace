"""Bounded sequential SQLite HTTP diagnostics, not load/MySQL/production attribution."""
import importlib
import json
import os
from collections import Counter
from pathlib import Path
from sqlalchemy import event
os.environ['T44_REQUEST_DIAGNOSTICS']='1'
fixture=importlib.import_module('tmp.backend.contracts.conftest')
http=importlib.import_module('tmp.backend.contracts.986_http')
gen=fixture.application.__wrapped__();client,factory=next(gen)
try:
 tokens,pid,iid=http.setup_project(client);task=http.create_task(client,tokens,pid,iid)
 engine=factory._sessions.kw['bind'];counts=Counter()
 @event.listens_for(engine,'before_cursor_execute')
 def capture(conn,cursor,statement,params,context,many):counts[statement.split()[0].upper()]+=1
 rows=[]
 for phase in ['getTask','validateContractPayload','transitionTask']:
  for i in range(5):
   kwargs={'project_id':pid}
   if phase!='validateContractPayload':kwargs['task_id']=task['id']
   if phase=='validateContractPayload':kwargs['body']={'category':1,'payload':{'title':'Synthetic','owner_id':2,'iteration_id':iid,'plan':http.PLAN,'dependency_task_ids':[]}}
   if phase=='transitionTask':kwargs['body']={'expected_version':task['version'],'action':2 if i%2==0 else 3,'evidence':http.EVIDENCE,**({'reason':'Synthetic','responsibility_stage':1} if i%2==0 else {'basis':'Synthetic'})}
   counts.clear();response=http.request(client,phase,token=tokens['manager'],expect=200,**kwargs)
   if phase=='transitionTask':task=response.json()['data']['task']
   rows.append({'phase':phase,'timing':response.headers['server-timing'],'sql_counts':dict(counts)})
 Path('agents/backend/common-latency/SQLITE_SEGMENTS.PUBLIC.json').write_text(json.dumps({'scope':__doc__,'requests':rows},indent=2)+'\n')
finally:
 try:next(gen)
 except StopIteration:pass
