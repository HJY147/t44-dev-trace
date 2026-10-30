"""Original source90b prepare/claim fragment on synthetic accumulated local MySQL only."""
import concurrent.futures,hashlib,json,subprocess,threading,time,uuid
from datetime import datetime,timezone,timedelta
from pathlib import Path
import pymysql
from sqlalchemy import create_engine,event,text
from t44.persistence import SqlAlchemyUnitOfWorkFactory
from t44.persistence.engine import initialize_mysql_session
from t44.persistence.schema import ddl_text
from t44.persistence.seed import seed_demo
from t44.services.runtime import Runtime
from t44.services.identity import issue_session
from t44.services.common import Call
from t44.settings import Settings
ROOT=Path('/Users/yang/Desktop/nothing/软件开发大作业/.agent-worktrees/.runtime');BIN=ROOT/'mysql-8.4/mysql-8.4.11-macos15-arm64/bin';DATA=ROOT/'manual12-digest-mysql-v2';SOCKET='/tmp/t44-manual12-digest.sock';DB='manual12_claim';HERE=Path(__file__).parent
LOCAL=threading.local();DURATIONS=[];GUARD=threading.Lock()
def snapshot():
 c=pymysql.connect(unix_socket=SOCKET,user='root',database=DB,autocommit=True)
 try:
  with c.cursor() as q:
   q.execute("SHOW GLOBAL STATUS WHERE Variable_name REGEXP '^(Innodb_(row_lock|log_wait|os_log|data_fsync|redo_log|buffer_pool_wait)|Threads_running|Threads_connected)'");status={k:v for k,v in q.fetchall()}
   q.execute("SELECT EVENT_NAME,COUNT_STAR,SUM_TIMER_WAIT FROM performance_schema.events_waits_summary_global_by_event_name WHERE COUNT_STAR>0 AND (EVENT_NAME LIKE 'wait/io/file/innodb/%' OR EVENT_NAME LIKE 'wait/synch/%/innodb/%') ORDER BY SUM_TIMER_WAIT DESC LIMIT 20");waits=[dict(event=x,count=n,timer_ps=t) for x,n,t in q.fetchall()]
   q.execute("SELECT DIGEST,COUNT_STAR,SUM_TIMER_WAIT,SUM_ROWS_EXAMINED FROM performance_schema.events_statements_summary_by_digest WHERE SCHEMA_NAME=%s ORDER BY SUM_TIMER_WAIT DESC LIMIT 15",(DB,));digests=[dict(digest=h,count=n,timer_ps=t,rows_examined=r) for h,n,t,r in q.fetchall()]
   q.execute("SELECT @@innodb_autoinc_lock_mode,@@innodb_redo_log_capacity,@@innodb_flush_log_at_trx_commit,@@sync_binlog,@@innodb_buffer_pool_size,@@max_connections");config=dict(zip(['autoinc_lock_mode','redo_capacity','flush_at_commit','sync_binlog','buffer_pool_size','max_connections'],q.fetchone()))
   q.execute('SELECT STORAGE_ENGINES FROM performance_schema.log_status');storage=json.loads(q.fetchone()[0])
  return dict(status=status,waits=waits,digests=digests,config=config,innodb_log=storage.get('InnoDB'))
 finally:c.close()
def percentile(a,p=.95):
 a=sorted(a);return a[max(0,__import__('math').ceil(len(a)*p)-1)]
def main():
 log=(ROOT/'manual12-claim-server.log').open('ab');server=subprocess.Popen([str(BIN/'mysqld'),'--no-defaults','--datadir='+str(DATA),'--skip-networking','--mysqlx=OFF','--socket='+SOCKET,'--pid-file='+str(DATA/'server.pid'),'--innodb-buffer-pool-size=1G','--max-connections=384'],stdout=log,stderr=subprocess.STDOUT);out={'source':'90b734f65ce6ee9f5c217e885bc7ea4857e32b48','scope':'local socket-only synthetic original prepare/claim fragment, not HTTP/cloud acceptance','samples':[]};engine=None
 try:
  for _ in range(100):
   if subprocess.run([str(BIN/'mysql'),'--no-defaults','--socket='+SOCKET,'-uroot','-e','SELECT 1'],capture_output=True).returncode==0:break
   time.sleep(.1)
  admin=pymysql.connect(unix_socket=SOCKET,user='root',autocommit=True)
  with admin.cursor() as q:
   q.execute('CREATE DATABASE '+DB)
   q.execute("UPDATE performance_schema.setup_instruments SET ENABLED='YES',TIMED='YES' WHERE NAME LIKE 'wait/synch/%/innodb/%'")
  admin.close()
  engine=create_engine('mysql+pymysql://root@localhost/'+DB,connect_args={'unix_socket':SOCKET},pool_size=320,max_overflow=0,pool_pre_ping=True,pool_reset_on_return='rollback',isolation_level='READ COMMITTED');event.listen(engine,'connect',initialize_mysql_session,insert=True);factory=SqlAlchemyUnitOfWorkFactory(engine)
  statements='\n'.join(line for line in ddl_text().splitlines() if not line.lstrip().startswith('--')).split(';')
  with engine.connect() as schema:
   for statement in statements:
    if statement.strip():schema.exec_driver_sql(statement)
   schema.commit()
  seed_demo(factory,projects=1,tasks=10,dependencies=0,records=20,anchor_at=datetime.now(timezone.utc))
  with factory() as u:token=issue_session(u.gateway,user_id=2,clock=datetime.now(timezone.utc),ttl=3600)['access_token']
  runtime=Runtime(factory,Settings(),None)
  def before(_con,_cur,sql,_params,ctx,_many):
   if sql.startswith('INSERT INTO idempotency_requests'):ctx.probe_start=time.perf_counter()
  def after(_con,_cur,sql,_params,ctx,_many):
   if hasattr(ctx,'probe_start'):
    with GUARD:DURATIONS.append((time.perf_counter()-ctx.probe_start)*1000)
  event.listen(engine,'before_cursor_execute',before);event.listen(engine,'after_cursor_execute',after)
  def run_load(existing):
   DURATIONS.clear();before_stats=snapshot();barrier=threading.Barrier(64)
   def worker(i):
    times=[];barrier.wait()
    for _ in range(20):
     call=Call('transitionTask',str(uuid.uuid4()),token,path={'project_id':1,'task_id':1},body={'expected_version':1,'action':2},key=str(uuid.uuid4()))
     start=time.perf_counter();assert runtime.prepare(call,lambda _c:None) is None
     with factory() as u:runtime.complete(u.gateway,call,200,{'data':{'synthetic':True}})
     times.append((time.perf_counter()-start)*1000)
    return times
   at=time.perf_counter()
   with concurrent.futures.ThreadPoolExecutor(max_workers=64) as executor:latencies=[t for group in executor.map(worker,range(64)) for t in group]
   elapsed=time.perf_counter()-at;after_stats=snapshot();out['samples'].append(dict(existing_synthetic_rows=existing,clients=64,operations=1280,seconds=elapsed,fragment_p95_ms=percentile(latencies),insert_mean_ms=sum(DURATIONS)/len(DURATIONS),insert_p95_ms=percentile(DURATIONS),before=before_stats,after=after_stats));(HERE/'native-claim-result.PUBLIC.json').write_text(json.dumps(out,indent=2,default=str)+'\n')
  run_load(0)
  # Synthetic completed records with matching production key/JSON/constraint shape.
  at=datetime.now(timezone.utc).replace(tzinfo=None);response=json.dumps({'synthetic':True,'padding':'x'*512});c=pymysql.connect(unix_socket=SOCKET,user='root',database=DB,autocommit=False)
  with c.cursor() as q:
   sql='INSERT INTO idempotency_requests(actor_kind,actor_id,operation_id,idempotency_key,request_hash,status,owner_token,lease_until,response_status,response_body,response_request_id,created_at,completed_at) VALUES(%s,%s,%s,%s,%s,2,%s,%s,200,%s,%s,%s,%s)'
   for base in range(0,500000,5000):
    q.executemany(sql,[(1,2,'transitionTask',str(uuid.uuid4()),b'x'*32,b'y'*16,at+timedelta(seconds=60),response,str(uuid.uuid4()),at,at) for _ in range(5000)]);c.commit()
  c.close();run_load(501280)
  print(json.dumps({'scope':out['scope'],'samples':[{k:s[k] for k in ['existing_synthetic_rows','clients','operations','seconds','fragment_p95_ms','insert_mean_ms','insert_p95_ms']} for s in out['samples']]}))
 finally:
  if engine:engine.dispose()
  subprocess.run([str(BIN/'mysqladmin'),'--no-defaults','--socket='+SOCKET,'-uroot','shutdown'],capture_output=True);server.wait(timeout=30)
if __name__=='__main__':main()
