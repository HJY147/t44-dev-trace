"""Socket-only synthetic MySQL correctness checks for exact Runtime claim candidate."""
import concurrent.futures,datetime,hashlib,importlib.util,json,subprocess,threading,time,uuid,sys
from pathlib import Path
import t44

import pymysql
from sqlalchemy import create_engine,event
from t44.persistence import SqlAlchemyUnitOfWorkFactory
from t44.persistence.engine import initialize_mysql_session
from t44.persistence.schema import ddl_text
from t44.persistence.seed import seed_demo
from t44.services.common import Call
from t44.services.identity import issue_session
from t44.services.errors import Rejected
from t44.settings import Settings
ROOT=Path('/Users/yang/Desktop/nothing/软件开发大作业');RT=ROOT/'.agent-worktrees/.runtime';BIN=RT/'mysql-8.4/mysql-8.4.11-macos15-arm64/bin';HERE=Path(__file__).parent
CAND=ROOT/'.agent-worktrees/backend-common-latency-20261031/backend/t44/services/runtime.py'
MODE=sys.argv[1];DATA=RT/('locked-native-20261031-'+MODE);SOCKET='/tmp/t44-locked-native-20261031-'+MODE+'.sock'
if MODE.startswith('baseline'):CAND=Path(__file__).resolve().parents[3]/'backend/t44/services/runtime.py'
def main():
 assert not DATA.exists() and not Path(SOCKET).exists();DATA.mkdir(mode=0o700)
 log=(RT/('claim-native-'+MODE+'.private.log')).open('ab');engine=None;server=None;out={'scope':'owned local socket-only MySQL correctness, not SUT/HTTP/performance acceptance','checks':{},'runtime_sha256':hashlib.sha256(CAND.read_bytes()).hexdigest(),'ddl_sha256':hashlib.sha256(ddl_text().encode()).hexdigest()}
 try:
  subprocess.run([str(BIN/'mysqld'),'--no-defaults','--initialize-insecure','--datadir='+str(DATA)],stdout=log,stderr=log,check=True,timeout=90)
  server=subprocess.Popen([str(BIN/'mysqld'),'--no-defaults','--datadir='+str(DATA),'--skip-networking','--mysqlx=OFF','--socket='+SOCKET,'--pid-file='+str(DATA/'server.pid'),'--innodb-buffer-pool-size=128M','--max-connections=64'],stdout=log,stderr=log)
  for _ in range(100):
   if subprocess.run([str(BIN/'mysql'),'--no-defaults','--socket='+SOCKET,'-uroot','-e','SELECT 1'],capture_output=True).returncode==0:break
   time.sleep(.1)
  c=pymysql.connect(unix_socket=SOCKET,user='root',autocommit=True)
  with c.cursor()as q:q.execute('CREATE DATABASE claim_candidate');q.execute('SELECT VERSION(),@@transaction_isolation,@@innodb_flush_log_at_trx_commit,@@sync_binlog');out['server']=q.fetchone()
  c.close()
  engine=create_engine('mysql+pymysql://root@localhost/claim_candidate',connect_args={'unix_socket':SOCKET},pool_size=32,max_overflow=0,isolation_level='READ COMMITTED',pool_reset_on_return='rollback');event.listen(engine,'connect',initialize_mysql_session,insert=True)
  errors=[]
  def on_error(ctx):
   original=ctx.original_exception;errors.append({'exception':type(original).__name__,'errno':original.args[0] if original.args else None})
  event.listen(engine,'handle_error',on_error);factory=SqlAlchemyUnitOfWorkFactory(engine)
  with engine.connect()as con:
   for s in '\n'.join(x for x in ddl_text().splitlines()if not x.lstrip().startswith('--')).split(';'):
    if s.strip():con.exec_driver_sql(s)
   con.commit();out['effective_isolation']=con.exec_driver_sql('SELECT @@transaction_isolation').scalar()
  seed_demo(factory,projects=1,tasks=10,dependencies=0,records=20,anchor_at=datetime.datetime.now(datetime.timezone.utc))
  import os,importlib
  from fastapi.testclient import TestClient
  from t44.api import create_app
  from t44 import diagnostics as diag
  from sqlalchemy import select,func
  http=importlib.import_module('tmp.backend.contracts.986_http')
  with factory() as u:
   task=u.gateway.rows('tasks',{'state':2},limit=1)[0]
   ses=issue_session(u.gateway,user_id=task['owner_id'],clock=datetime.datetime.now(datetime.timezone.utc),ttl=3600)
  token=ses['access_token'];pid=task['project_id'];iid=task['iteration_id']
  os.environ.pop('T44_REQUEST_DIAGNOSTICS',None);client=TestClient(create_app(factory=factory,settings=Settings()))
  probe=pymysql.connect(unix_socket=SOCKET,user='root',database='claim_candidate',autocommit=True)
  def metrics():
   with probe.cursor() as q:
    q.execute("SELECT NAME,COUNT,STATUS FROM information_schema.INNODB_METRICS WHERE NAME='index_page_splits'")
    metric=q.fetchone();assert metric and metric[2]=='enabled',metric
    q.execute("SHOW GLOBAL STATUS WHERE Variable_name IN ('Innodb_os_log_written','Innodb_redo_log_current_lsn','Innodb_buffer_pool_pages_flushed','Innodb_data_written')")
    return {'index_page_splits':int(metric[1]),**{k:int(v)for k,v in q.fetchall()}}
  def storage():
   with probe.cursor() as q:
    q.execute("SELECT COUNT(*),COALESCE(SUM(status=1),0),COALESCE(SUM(status=2),0),COALESCE(SUM(JSON_STORAGE_SIZE(response_body)),0),COALESCE(AVG(JSON_STORAGE_SIZE(response_body)),0) FROM idempotency_requests")
    n,pending,done,size,mean=q.fetchone()
    q.execute("SELECT DATA_LENGTH,INDEX_LENGTH,TABLE_ROWS,ROW_FORMAT FROM information_schema.TABLES WHERE TABLE_SCHEMA='claim_candidate' AND TABLE_NAME='idempotency_requests'")
    table=q.fetchone()
    q.execute("SELECT index_name,stat_name,stat_value FROM mysql.innodb_index_stats WHERE database_name='claim_candidate' AND table_name='idempotency_requests' AND stat_name IN ('size','n_leaf_pages') ORDER BY index_name,stat_name")
    return {'rows':n,'pending':int(pending),'complete':int(done),'response_binary_json_total_bytes':int(size),'response_binary_json_mean_bytes':str(mean),'table_stats':table,'persistent_index_stats':q.fetchall()}
  with probe.cursor() as q:
   q.execute("SET GLOBAL innodb_monitor_enable='index_page_splits'")
   q.execute('ANALYZE TABLE idempotency_requests');q.fetchall()
  out['storage_before']=storage();out['metrics_before']=metrics();observations=[];pending_context={}
  def before(conn,cursor,statement,parameters,ctx,many):
   node=getattr(getattr(ctx,'compiled',None),'statement',None)
   if getattr(getattr(node,'table',None),'name',None)=='idempotency_requests' and (getattr(node,'is_insert',False) or getattr(node,'is_update',False)):
    kind='INSERT_pending' if node.is_insert else 'UPDATE_complete'
    pending_context[id(ctx)]=(kind,metrics())
  def after(conn,cursor,statement,parameters,ctx,many):
   if id(ctx) in pending_context:
    kind,b= pending_context.pop(id(ctx));a=metrics()
    observations.append({'operation':kind,'deltas':{k:a[k]-b[k]for k in b}})
  event.listen(engine,'before_cursor_execute',before);event.listen(engine,'after_cursor_execute',after)
  rows=[]
  for phase in ['transitionTask']:
   for i in range(64):
    kw={'project_id':pid}
    if phase!='validateContractPayload':kw['task_id']=task['id']
    if phase=='validateContractPayload':kw['body']={'category':1,'payload':{'title':'Synthetic','owner_id':task['owner_id'],'iteration_id':iid,'plan':http.PLAN,'dependency_task_ids':[]}}
    if phase=='transitionTask':kw['body']={'expected_version':task['version'],'action':2 if i%2==0 else 3,'evidence':http.EVIDENCE,**({'reason':'Synthetic','responsibility_stage':1} if i%2==0 else {'basis':'Synthetic'})}
    started=time.perf_counter_ns();r=http.request(client,phase,token=token,expect=200,**kw);wall=time.perf_counter_ns()-started
    rows.append({'phase':phase,'client_wall_ns':wall,'server_timing':r.headers['server-timing']})
    if phase=='transitionTask':task=r.json()['data']['task']
  out['http_requests']=rows
  event.remove(engine,'before_cursor_execute',before);event.remove(engine,'after_cursor_execute',after)
  out['metrics_after_measured']=metrics()
  out['statement_observations']=observations
  out['storage_after_before_analyze']=storage()
  with probe.cursor() as q:q.execute('ANALYZE TABLE idempotency_requests');q.fetchall()
  out['storage_after_analyze']=storage();probe.close()
  assert out['storage_before']['rows']==0
  assert out['storage_after_analyze']['complete']==64 and out['storage_after_analyze']['pending']==0
  assert sum(r['operation']=='INSERT_pending'for r in observations)==64
  assert sum(r['operation']=='UPDATE_complete'for r in observations)==64
  assert out['storage_after_analyze']['response_binary_json_total_bytes']>0
  out['operation_delta_sums']={kind:{key:sum(r['deltas'][key] for r in observations if r['operation']==kind)for key in observations[0]['deltas']}for kind in ['INSERT_pending','UPDATE_complete']}
  out['http_total_requests']=64;out['diagnostics_enabled']=False
  out['driver_errors']=errors;assert not errors
  out['status']='SINGLE_IMPLEMENTATION_64_COMPLETE_LIFECYCLES_OBSERVED_NOT_PERFORMANCE_AB'
 finally:
  if engine:engine.dispose()
  if server:
   stopped=subprocess.run([str(BIN/'mysqladmin'),'--no-defaults','--socket='+SOCKET,'-uroot','shutdown'],capture_output=True);server.wait(timeout=30);out['owned_server_shutdown_exit']=stopped.returncode;out['socket_absent']=not Path(SOCKET).exists()
  (HERE/(MODE+'.PUBLIC.json')).write_text(json.dumps(out,indent=2,default=str)+'\n')
if __name__=='__main__':main()
