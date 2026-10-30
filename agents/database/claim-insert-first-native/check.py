"""Socket-only synthetic MySQL correctness checks for exact Runtime claim candidate."""
import concurrent.futures,datetime,hashlib,importlib.util,json,subprocess,threading,time,uuid,sys
from pathlib import Path
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
CAND=ROOT/'.agent-worktrees/backend-claim-insert-first-20261031/backend/t44/services/runtime.py'
MODE=sys.argv[1];DATA=RT/('claim-native-20261031-'+MODE);SOCKET='/tmp/t44-claim-native-20261031-'+MODE+'.sock'
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
  spec=importlib.util.spec_from_file_location('t44.services.claim_candidate',CAND);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);runtime=mod.Runtime(factory,Settings(),None)
  with factory()as u:session=issue_session(u.gateway,user_id=2,clock=datetime.datetime.now(datetime.timezone.utc),ttl=3600)
  token=session['access_token']
  def call(key=None,body=None,tok=token):return Call('createProject',str(uuid.uuid4()),tok,body=body or {'name':'synthetic'},key=key or str(uuid.uuid4()))
  def prepare(c):return runtime.prepare(c,lambda _:None)
  def reject(c,code):
   try:prepare(c)
   except Rejected as e:assert e.code==code;return
   raise AssertionError('expected '+code)
  key=str(uuid.uuid4());barrier=threading.Barrier(16)
  def same(_):
   c=call(key);barrier.wait()
   try:prepare(c);return ('claimed',c)
   except Rejected as e:return(e.code,c)
   except Exception as e:return(type(e).__name__,c)
  with concurrent.futures.ThreadPoolExecutor(max_workers=16)as ex:results=list(ex.map(same,range(16)))
  out['same_key_outcomes']={k:sum(kind==k for kind,_ in results)for k,_ in results};out['driver_errors']=errors
  if any(kind not in ['claimed','IDEMPOTENCY_IN_PROGRESS']for kind,_ in results):
   out['status']='NATIVE_MYSQL_RC_SAME_KEY_FAILED';print(json.dumps(out,default=str));return
  assert sum(x[0]=='claimed'for x in results)==1 and sum(x[0]=='IDEMPOTENCY_IN_PROGRESS'for x in results)==15;owned=next(c for kind,c in results if kind=='claimed');out['checks']['same_key_16_one_owner']=True
  with factory()as u:runtime.complete(u.gateway,owned,201,{'data':{'id':1}})
  replay=prepare(call(key));assert replay['status']==2 and replay['response_status']==201;out['checks']['completed_replay']=True
  reject(call(key,{'name':'changed'}),'IDEMPOTENCY_CONTENT_CONFLICT');out['checks']['hash_conflict']=True
  barrier=threading.Barrier(16)
  def different(i):
   c=call('shared-prefix-'+str(i));barrier.wait();assert prepare(c)is None
   return c.idem['id']
  with concurrent.futures.ThreadPoolExecutor(max_workers=16)as ex:ids=list(ex.map(different,range(16)))
  assert len(set(ids))==16;out['checks']['different_keys_same_prefix_16']=True
  old=call();prepare(old)
  with factory()as u:u.gateway.update('idempotency_requests',{'id':old.idem['id']},{'lease_until':old.clock-datetime.timedelta(seconds=1)})
  newer=call(old.key);assert prepare(newer)is None and newer.idem['owner_token']!=old.idem['owner_token']
  try:
   with factory()as u:runtime.complete(u.gateway,old,201,{'data':{'id':2}})
   raise AssertionError('stale owner completed')
  except Rejected as e:assert e.code=='IDEMPOTENCY_IN_PROGRESS'
  with factory()as u:runtime.complete(u.gateway,newer,201,{'data':{'id':3}})
  out['checks']['expired_lease_owner_fencing']=True
  rollback=call()
  try:
   with factory()as u:
    from t44.services.identity import authenticate
    authenticate(u.gateway,rollback);runtime._claim(u.gateway,rollback);raise ValueError('synthetic abort')
  except ValueError:pass
  with factory()as u:assert not u.gateway.rows('idempotency_requests',{'idempotency_key':rollback.key})
  out['checks']['insert_transaction_rollback']=True
  revoked=call()
  with factory()as u:u.gateway.update('auth_sessions',{'id':session['session_id']},{'revoked_at':datetime.datetime.now(datetime.timezone.utc)})
  reject(revoked,'TOKEN_REVOKED');out['checks']['revocation_before_claim']=True
  with factory()as u:
   assert not u.gateway.rows('idempotency_requests',{'idempotency_key':revoked.key})
   expired=issue_session(u.gateway,user_id=2,clock=datetime.datetime.now(datetime.timezone.utc)-datetime.timedelta(hours=2),ttl=1)
   sid=u.gateway.insert('service_accounts',{'name':'claim-synthetic','active':1,'created_at':datetime.datetime.now(datetime.timezone.utc)})
   svc=issue_session(u.gateway,service_account_id=sid,clock=datetime.datetime.now(datetime.timezone.utc),ttl=3600,project_ids=[1],scopes=['escalation:write'])
  reject(call(tok=expired['access_token']),'TOKEN_EXPIRED');out['checks']['expired_before_claim']=True
  s=Call('createEscalation',str(uuid.uuid4()),svc['access_token'],path={'project_id':1},body={'synthetic':True},key=str(uuid.uuid4()));assert prepare(s)is None;out['checks']['service_scope_claim']=True
  bad=Call('createEscalation',str(uuid.uuid4()),token,path={'project_id':1},key=str(uuid.uuid4()));reject(bad,'TOKEN_REVOKED');out['checks']['revoked_human_before_service_scope']=True
  out['status']='NATIVE_MYSQL_RC_CLAIM_CORRECTNESS_PASS';print(json.dumps(out,default=str))
 finally:
  if engine:engine.dispose()
  if server:
   p=subprocess.run([str(BIN/'mysqladmin'),'--no-defaults','--socket='+SOCKET,'-uroot','shutdown'],capture_output=True);server.wait(timeout=30);out['owned_server_shutdown_exit']=p.returncode;out['socket_absent']=not Path(SOCKET).exists()
  (HERE/(MODE+'.PUBLIC.json')).write_text(json.dumps(out,indent=2,default=str)+'\n')
if __name__=='__main__':main()
