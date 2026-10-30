"""Render product gateway statement shapes without connecting or loading fixture data."""
import json,re
from pathlib import Path
from sqlalchemy import insert,update
from sqlalchemy.dialects.mysql import pymysql
from t44.persistence.schema import TABLES
from t44.persistence.rows import RowsGateway
rows=[]
def record(name,stmt):
 sql=str(stmt.compile(dialect=pymysql.dialect()))
 sql=re.sub(r'%\([^)]+\)s|%s',"'synthetic'",sql)
 rows.append({'name':name,'sql':sql})
values={
'audit_events':['project_id','task_id','attempted_project_id','attempted_task_id','actor_kind','actor_id','request_id','operation_id','outcome','reason_code','expected_version','observed_version','before_values','after_values','evidence','created_at'],
'idempotency_requests':['actor_kind','actor_id','operation_id','idempotency_key','request_hash','status','owner_token','lease_until','created_at'],
'outbox_events':['project_id','task_id','event_type','status','payload','recipients','next_attempt_at','created_at','updated_at']}
for table,names in values.items():record('insert_'+table,insert(TABLES[table]).values({k:'synthetic' for k in names}))
t=TABLES['idempotency_requests'];record('complete_idempotency',update(t).where(t.c.id==1,t.c.status==1,t.c.owner_token=='synthetic').values(status=2,response_status=200,response_body={},response_request_id='synthetic',completed_at='synthetic'))
Path(__file__).with_name('static-statement-shapes.PUBLIC.json').write_text(json.dumps(rows,indent=2)+'\n')
print(json.dumps(rows))
