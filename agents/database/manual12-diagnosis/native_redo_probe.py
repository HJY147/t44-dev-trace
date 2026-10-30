"""Controlled local original-claim redo-capacity comparison; never accesses cloud."""
import concurrent.futures,json,math,os,platform,subprocess,threading,time,uuid
from datetime import datetime,timezone
from pathlib import Path
import pymysql
from sqlalchemy import create_engine,event
from t44.persistence import SqlAlchemyUnitOfWorkFactory
from t44.persistence.engine import initialize_mysql_session
from t44.persistence.schema import TABLES,ddl_text,DDL_SHA256
from t44.services.runtime import Runtime
from t44.services.identity import issue_session
from t44.services.common import Call
from t44.settings import Settings
ROOT=Path('/Users/yang/Desktop/nothing/软件开发大作业/.agent-worktrees/.runtime');BIN=ROOT/'mysql-8.4/mysql-8.4.11-macos15-arm64/bin';DATA=ROOT/'manual12-digest-mysql-v2';SOCKET='/tmp/t44-manual12-digest.sock';SOURCE_DB='manual12_claim';HERE=Path(__file__).parent
CLIENTS=64;WARMUP=20;DURATION=180;DATABASES=['manual12_redo100','manual12_redo1024'];CAPACITIES=[104857600,1073741824]
DIGESTS=['78ceeee04e3c5f9d92f1e2375cb142031ccd5252a477e2b768ebad7d110cf45c','f2b9be5f0f32ca7507e4ddf133cd2fad0993a1c26fde9caa6f067b1af2b7603c','3e67fa9d38d82054e7fc01fe3ee8844dc76faaaefbd74d213a2af42e60e95520']
FIELDS=['Com_commit','Com_rollback','Threads_connected','Threads_running','Innodb_row_lock_waits','Innodb_row_lock_time','Innodb_buffer_pool_bytes_dirty','Innodb_buffer_pool_pages_dirty','Innodb_buffer_pool_wait_free','Innodb_data_reads','Innodb_data_writes','Innodb_data_read','Innodb_data_written','Innodb_data_fsyncs','Innodb_log_waits','Innodb_os_log_fsyncs','Innodb_os_log_written','Innodb_redo_log_current_lsn','Innodb_redo_log_checkpoint_lsn','Innodb_redo_log_capacity_resized']
def client(db=None):return pymysql.connect(unix_socket=SOCKET,user='root',database=db,autocommit=True)
def start(cap):
 log=(ROOT/'manual12-redo-server.log').open('ab');p=subprocess.Popen([str(BIN/'mysqld'),'--no-defaults','--datadir='+str(DATA),'--skip-networking','--mysqlx=OFF','--socket='+SOCKET,'--pid-file='+str(DATA/'server.pid'),'--innodb-buffer-pool-size=1G','--max-connections=384','--innodb-redo-log-capacity='+str(cap)],stdout=log,stderr=subprocess.STDOUT)
 for _ in range(200):
  try:
   c=client();c.close();return p
  except pymysql.Error:time.sleep(.1)
 raise RuntimeError('OWN_LOCAL_SERVER_NOT_READY')
def stop(p):
 subprocess.run([str(BIN/'mysqladmin'),'--no-defaults','--socket='+SOCKET,'-uroot','shutdown'],capture_output=True,check=True);p.wait(timeout=60)
def engine(db):
 e=create_engine('mysql+pymysql://root@localhost/'+db,connect_args={'unix_socket':SOCKET},pool_size=320,max_overflow=0,pool_pre_ping=True,pool_reset_on_return='rollback',isolation_level='READ COMMITTED');event.listen(e,'connect',initialize_mysql_session,insert=True);return e
def setup():
 p=start(CAPACITIES[0]);e=None
 try:
  e=engine(SOURCE_DB);factory=SqlAlchemyUnitOfWorkFactory(e)
  with factory() as u:token=issue_session(u.gateway,user_id=2,clock=datetime.now(timezone.utc),ttl=3600)['access_token']
  c=client();checks=[]
  try:
   with c.cursor() as q:
    statements='\n'.join(x for x in ddl_text().splitlines() if not x.lstrip().startswith('--')).split(';')
    for db in DATABASES:
     q.execute('CREATE DATABASE '+db);q.execute('USE '+db)
     for s in statements:
      if s.strip():q.execute(s)
     q.execute('SET FOREIGN_KEY_CHECKS=0')
     try:
      for table in TABLES:q.execute('INSERT INTO `'+table+'` SELECT * FROM `'+SOURCE_DB+'`.`'+table+'`')
     finally:q.execute('SET FOREIGN_KEY_CHECKS=1')
     q.execute('CHECKSUM TABLE idempotency_requests EXTENDED');checksum=q.fetchone()[1];q.execute('SELECT COUNT(*),MIN(id),MAX(id) FROM idempotency_requests');counts=q.fetchone();checks.append(dict(database=db,rows=counts[0],min_id=counts[1],max_id=counts[2],checksum=checksum))
   assert checks[0]['rows']==checks[1]['rows'] and checks[0]['checksum']==checks[1]['checksum']
  finally:c.close()
  return token,checks
 finally:
  if e:e.dispose()
  stop(p)
def snapshot(db):
 c=client(db)
 try:
  with c.cursor() as q:
   q.execute('SHOW GLOBAL STATUS');status={k:int(v) for k,v in q.fetchall() if k in FIELDS and str(v).isdigit()}
   q.execute('SELECT STORAGE_ENGINES FROM performance_schema.log_status');innodb=json.loads(q.fetchone()[0]).get('InnoDB')
   q.execute("SELECT EVENT_NAME,COUNT_STAR,SUM_TIMER_WAIT FROM performance_schema.events_waits_summary_global_by_event_name WHERE COUNT_STAR>0 AND (EVENT_NAME LIKE 'wait/io/file/innodb/%' OR EVENT_NAME LIKE 'wait/synch/%/innodb/%') ORDER BY SUM_TIMER_WAIT DESC LIMIT 20");waits=[dict(event=x,count=n,timer_ps=t) for x,n,t in q.fetchall()]
   q.execute('SELECT DIGEST,COUNT_STAR,SUM_TIMER_WAIT FROM performance_schema.events_statements_summary_by_digest WHERE SCHEMA_NAME=%s AND DIGEST IN (%s,%s,%s)',(db,*DIGESTS));digests=[dict(digest=h,count=n,timer_ps=t) for h,n,t in q.fetchall()]
   q.execute('SELECT @@innodb_redo_log_capacity,@@innodb_flush_log_at_trx_commit,@@sync_binlog,@@innodb_buffer_pool_size,@@innodb_autoinc_lock_mode,@@max_connections');config=dict(zip(['redo_capacity','flush_at_commit','sync_binlog','buffer_pool_size','autoinc_lock_mode','max_connections'],q.fetchone()))
  return dict(monotonic=time.monotonic(),utc=datetime.now(timezone.utc).isoformat(),status=status,innodb_log=innodb,waits=waits,digests=digests,config=config)
 finally:c.close()
def p95(a):return sorted(a)[max(0,math.ceil(len(a)*.95)-1)] if a else None
def phase(db,cap,token):
 server=start(cap);e=None;stopped=threading.Event();sampler=None;sample_errors=[];samples=[];insert_times=[];lock=threading.Lock();begin=None
 try:
  c=client(db)
  with c.cursor() as q:q.execute("UPDATE performance_schema.setup_instruments SET ENABLED='YES',TIMED='YES' WHERE NAME LIKE 'wait/synch/%/innodb/%'")
  c.close();e=engine(db);factory=SqlAlchemyUnitOfWorkFactory(e);runtime=Runtime(factory,Settings(),None)
  def before(_con,_cur,sql,_params,ctx,_many):
   if sql.startswith('INSERT INTO idempotency_requests'):ctx.probe_started=time.perf_counter()
  def after(_con,_cur,sql,_params,ctx,_many):
   if hasattr(ctx,'probe_started') and begin is not None and ctx.probe_started>=begin+WARMUP:
    with lock:insert_times.append((time.perf_counter()-ctx.probe_started)*1000)
  event.listen(e,'before_cursor_execute',before);event.listen(e,'after_cursor_execute',after)
  initial=snapshot(db);assert initial['config']['redo_capacity']==cap and initial['config']['flush_at_commit']==initial['config']['sync_binlog']==1
  def observe():
   while not stopped.is_set():
    try:samples.append(snapshot(db))
    except Exception as error:sample_errors.append(type(error).__name__)
    stopped.wait(2)
  barrier=threading.Barrier(CLIENTS+1);errors=[]
  def worker(i):
   barrier.wait();latencies=[];warmup_count=0
   while time.perf_counter()<begin+WARMUP+DURATION:
    call=Call('transitionTask',str(uuid.uuid4()),token,path={'project_id':1,'task_id':1},body={'expected_version':1,'action':2},key=str(uuid.uuid4()));at=time.perf_counter()
    try:
     assert runtime.prepare(call,lambda _c:None) is None
     with factory() as u:runtime.complete(u.gateway,call,200,{'data':{'synthetic':True,'padding':'x'*512}})
     if at>=begin+WARMUP:latencies.append((time.perf_counter()-at)*1000)
     else:warmup_count+=1
    except Exception as error:
     with lock:errors.append(type(error).__name__)
     break
   return warmup_count,latencies
  with concurrent.futures.ThreadPoolExecutor(max_workers=CLIENTS) as pool:
   futures=[pool.submit(worker,i) for i in range(CLIENTS)];begin=time.perf_counter();sampler=threading.Thread(target=observe);sampler.start();barrier.wait();rows=[f.result() for f in futures]
  stopped.set();sampler.join();samples.append(snapshot(db));latencies=[n for _,a in rows for n in a]
  for s in samples:assert s['config']==initial['config']
  result=dict(database=db,redo_capacity=cap,clients=CLIENTS,warmup_seconds=WARMUP,measurement_seconds=DURATION,warmup_operations=sum(x for x,_ in rows),measured_operations=len(latencies),errors=errors,sample_errors=sample_errors,sample_interval_seconds=2,insert_client_mean_ms=sum(insert_times)/len(insert_times) if insert_times else None,insert_client_p95_ms=p95(insert_times),fragment_client_p95_ms=p95(latencies),initial=initial,samples=samples)
  (HERE/('redo-'+str(cap)+'.PUBLIC.json')).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ['initial','samples']}),flush=True);return result
 finally:
  stopped.set()
  if sampler:sampler.join()
  if e:e.dispose()
  stop(server)
def main():
 token,checks=setup();print(json.dumps({'stage':'CLONES_IDENTICAL','checks':checks}),flush=True)
 out={'source':'90b734f65ce6ee9f5c217e885bc7ea4857e32b48','ddl_sha256':DDL_SHA256,'scope':'local synthetic original prepare/claim plus complete fragment; not HTTP/cloud performance','initial_clones':checks,'hardware':{'machine':platform.machine(),'cpu_count':os.cpu_count()},'fixed_order':['100MiB','1GiB'],'phases':[],'limitations':['fixed AB order, OS cache and monotonically appended rows may affect results','own buffer pool1GiB, local hardware differs from cloud8GiB and64CPU','no complete audit/outbox main transaction or HTTP route is simulated','samples include observer overhead, missing events are not zero','initial clone copies use local setup-only foreign-key disable restored before workload; original frozen constraints remain active during all measured operations']}
 for db,cap in zip(DATABASES,CAPACITIES):
  result=phase(db,cap,token);out['phases'].append({k:v for k,v in result.items() if k not in ['initial','samples']});(HERE/'native-redo-comparison.PUBLIC.json').write_text(json.dumps(out,indent=2)+'\n')
 print(json.dumps({'stage':'COMPARISON_COMPLETE','phases':out['phases']}),flush=True)
if __name__=='__main__':main()
