"""Compare real SQLAlchemy cleanup on own socket-only synthetic MySQL, no cloud."""
import json,subprocess,time
from pathlib import Path
import pymysql
from sqlalchemy import create_engine,text
from sqlalchemy.exc import IntegrityError
from t44.persistence import SqlAlchemyUnitOfWorkFactory
ROOT=Path('/Users/yang/Desktop/nothing/软件开发大作业/.agent-worktrees/.runtime')
BIN=ROOT/'mysql-8.4/mysql-8.4.11-macos15-arm64/bin';DATA=ROOT/'manual12-digest-mysql-v2';SOCKET='/tmp/t44-manual12-digest.sock'
EVENTS=[]
class TracedConnection(pymysql.connections.Connection):
 def commit(self):EVENTS.append('commit');return super().commit()
 def rollback(self):EVENTS.append('rollback');return super().rollback()
def count():return {k:EVENTS.count(k) for k in ('commit','rollback')}
def run(reset):
 engine=create_engine('mysql+pymysql://',creator=lambda:TracedConnection(unix_socket=SOCKET,user='root',database='manual12_digest'),pool_size=1,max_overflow=0,pool_pre_ping=True,pool_reset_on_return=reset)
 factory=SqlAlchemyUnitOfWorkFactory(engine);r={'reset':reset,'cases':[]}
 with engine.begin() as c:c.exec_driver_sql('CREATE TABLE IF NOT EXISTS probe_rows(id INT PRIMARY KEY,n INT NOT NULL)');c.exec_driver_sql('DELETE FROM probe_rows')
 # Warm up dialect/initial connection before counting per-transaction resets.
 with engine.connect() as c:c.exec_driver_sql('SELECT 1')
 EVENTS.clear()
 with factory() as u:u._require_active().execute(text('INSERT INTO probe_rows VALUES (1,1)'))
 r['cases'].append({'name':'normal_uow_commit','calls':count()});assert EVENTS.count('commit')==1
 EVENTS.clear()
 with engine.connect() as c:c.exec_driver_sql('INSERT INTO probe_rows VALUES (2,2)')
 with engine.connect() as c:visible=c.exec_driver_sql('SELECT COUNT(*) FROM probe_rows WHERE id=2').scalar_one()
 r['cases'].append({'name':'connection_close_without_commit','visible':visible,'calls':count()});assert visible==0
 EVENTS.clear()
 try:
  with factory() as u:
   u._require_active().execute(text('INSERT INTO probe_rows VALUES (3,3)'));raise ValueError('synthetic')
 except ValueError:pass
 with engine.connect() as c:visible=c.exec_driver_sql('SELECT COUNT(*) FROM probe_rows WHERE id=3').scalar_one()
 r['cases'].append({'name':'exception_uow_rollback','visible':visible,'calls':count()});assert visible==0
 EVENTS.clear()
 try:
  with factory() as u:
   u._require_active().execute(text('INSERT INTO probe_rows VALUES (4,4)'));u._require_active().execute(text('INSERT INTO probe_rows VALUES (1,9)'))
 except IntegrityError:pass
 with engine.connect() as c:visible=c.exec_driver_sql('SELECT COUNT(*) FROM probe_rows WHERE id=4').scalar_one()
 r['cases'].append({'name':'integrity_error_uow_rollback','visible':visible,'calls':count()});assert visible==0
 # Document lower-level raw DBAPI safety contract, including candidate's loss.
 EVENTS.clear();raw=engine.raw_connection()
 with raw.cursor() as cur:cur.execute('INSERT INTO probe_rows VALUES (5,5)')
 raw.close()
 with engine.connect() as c:visible=c.exec_driver_sql('SELECT COUNT(*) FROM probe_rows WHERE id=5').scalar_one();c.rollback()
 r['cases'].append({'name':'raw_dbapi_return_without_rollback','visible_on_recheckout':visible,'calls':count(),'safe':visible==0})
 engine.dispose();return r
def main():
 log=(ROOT/'manual12-digest-server-v2.log').open('ab');server=subprocess.Popen([str(BIN/'mysqld'),'--no-defaults','--datadir='+str(DATA),'--skip-networking','--mysqlx=OFF','--socket='+SOCKET,'--pid-file='+str(DATA/'server.pid'),'--innodb-buffer-pool-size=128M'],stdout=log,stderr=subprocess.STDOUT)
 try:
  for _ in range(100):
   if subprocess.run([str(BIN/'mysql'),'--no-defaults','--socket='+SOCKET,'-uroot','-e','SELECT 1'],capture_output=True).returncode==0:break
   time.sleep(.1)
  out={'scope':'isolated local MySQL8.4.11; synthetic rows only','variants':[run('rollback'),run(None)],'production_changed':False}
  p=Path(__file__).with_name('native-pool-result.PUBLIC.json');p.write_text(json.dumps(out,indent=2)+'\n');print(p.read_text())
 finally:
  subprocess.run([str(BIN/'mysqladmin'),'--no-defaults','--socket='+SOCKET,'-uroot','shutdown'],capture_output=True);server.wait(timeout=30)
if __name__=='__main__':main()
