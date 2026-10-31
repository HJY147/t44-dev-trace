"""Socket-only synthetic MySQL correctness checks for exact Runtime claim candidate."""
import concurrent.futures,datetime,hashlib,importlib.util,json,subprocess,threading,time,uuid,sys
from pathlib import Path
import t44
t44.__path__.append(str(Path("/Users/yang/Desktop/nothing/软件开发大作业/.agent-worktrees/backend-common-latency-20261031/backend/t44")))
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
  queries={'commit':'COMMIT','rollback':'ROLLBACK','select_literal':'SELECT 1','begin':'BEGIN','start_transaction':'START TRANSACTION','savepoint':'SAVEPOINT sa_savepoint_1','release_savepoint':'RELEASE SAVEPOINT sa_savepoint_1','set_names':'SET NAMES utf8mb4','set_isolation':'SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED','select_version':'SELECT VERSION()'}
  mapped={}
  with engine.connect() as con:
   for label,sql in queries.items():
    dg,txt=con.exec_driver_sql('SELECT STATEMENT_DIGEST(%s),STATEMENT_DIGEST_TEXT(%s)',(sql,sql)).one()
    mapped[label]={'mysql_statement_digest':dg.lower(),'sha256_digest_text':hashlib.sha256(txt.encode()).hexdigest(),'sha256_lowercase_digest':hashlib.sha256(dg.lower().encode()).hexdigest()}
  targets={r['digest_hash']for phase in ['early','late']for r in __import__('json').loads((HERE/'P13_IO_DELTAS.PUBLIC.json').read_text())[phase]['common_top20_digest_deltas']}
  out['candidate_mappings']=mapped;out['matches']=[{'operation':name,'method':k,'digest_hash':v}for name,row in mapped.items()for k,v in row.items()if v in targets]
  out['status']='CHEAP_TRUSTED_STATEMENT_DIGEST_MAPPING_FINISHED'
 finally:
  if engine:engine.dispose()
  if server:
   stopped=subprocess.run([str(BIN/'mysqladmin'),'--no-defaults','--socket='+SOCKET,'-uroot','shutdown'],capture_output=True);server.wait(timeout=30);out['owned_server_shutdown_exit']=stopped.returncode;out['socket_absent']=not Path(SOCKET).exists()
  (HERE/(MODE+'.PUBLIC.json')).write_text(json.dumps(out,indent=2,default=str)+'\n')
if __name__=='__main__':main()
