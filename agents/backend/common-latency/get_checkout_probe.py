"""One synthetic SQLite GET statement/checkout/commit count; no load or latency claims."""
import importlib
import json
import sys
from collections import Counter
from pathlib import Path
from sqlalchemy import event
fixture=importlib.import_module('tmp.backend.contracts.conftest');http=importlib.import_module('tmp.backend.contracts.986_http')
gen=fixture.application.__wrapped__();client,factory=next(gen)
try:
 tokens,pid,iid=http.setup_project(client);task=http.create_task(client,tokens,pid,iid)
 engine=factory._sessions.kw['bind'];counts=Counter()
 @event.listens_for(engine,'before_cursor_execute')
 def sql(conn,cursor,statement,params,context,many):counts[statement.split()[0].upper()]+=1
 event.listen(engine,'checkout',lambda *a:counts.update(['CHECKOUT']))
 event.listen(engine,'commit',lambda *a:counts.update(['COMMIT']))
 http.request(client,'getTask',token=tokens['manager'],project_id=pid,task_id=task['id'],expect=200)
 assert counts==Counter(SELECT=9,CHECKOUT=int(sys.argv[2]),COMMIT=int(sys.argv[2]))
 Path(sys.argv[1]).write_text(json.dumps({'scope':__doc__,'counts':dict(counts)},indent=2)+'\n')
finally:
 try:next(gen)
 except StopIteration:pass
