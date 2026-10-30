"""Single synthetic HTTP operation SQL trace; no load or latency measurement."""
import importlib
import json
import sys
from pathlib import Path
from sqlalchemy import event
fixture=importlib.import_module('tmp.backend.contracts.conftest')
http=importlib.import_module('tmp.backend.contracts.986_http')
gen=fixture.application.__wrapped__();client,factory=next(gen)
try:
 tokens,pid,iid=http.setup_project(client)
 statements=[]
 engine=factory._sessions.kw['bind']
 @event.listens_for(engine,'before_cursor_execute')
 def capture(conn,cursor,statement,params,context,many):
  statements.append(' '.join(statement.split()))
 task=http.create_task(client,tokens,pid,iid)
 claims=[s for s in statements if s.upper().startswith('SELECT') and 'FROM idempotency_requests' in s]
 scope_reads=[s for s in claims if 'idempotency_requests.idempotency_key =' in s]
 assert len(scope_reads)==int(sys.argv[2]),scope_reads
 assert task['id']>0
 Path(sys.argv[1]).write_text(json.dumps({'scope':'single synthetic SQLite HTTP createTask; statement-shape evidence only; not MySQL concurrency or performance','scope_preselects':len(scope_reads),'idempotency_selects':len(claims),'statements_without_parameters':statements},indent=2)+'\n')
finally:
 try:next(gen)
 except StopIteration:pass
