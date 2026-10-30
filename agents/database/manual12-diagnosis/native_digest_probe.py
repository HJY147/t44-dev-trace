"""Map static synthetic SQL to actual MySQL 8.4 digests on own socket-only process."""
from pathlib import Path
import json,subprocess,time
ROOT=Path('/Users/yang/Desktop/nothing/软件开发大作业/.agent-worktrees/.runtime')
BINARY=ROOT/'mysql-8.4/mysql-8.4.11-macos15-arm64/bin'
DATA=ROOT/'manual12-digest-mysql-v2'
SOCKET='/tmp/t44-manual12-digest.sock'
STATEMENTS=['COMMIT','ROLLBACK','BEGIN','SAVEPOINT sa_savepoint_1','RELEASE SAVEPOINT sa_savepoint_1','ROLLBACK TO SAVEPOINT sa_savepoint_1','INSERT INTO audit_events (project_id,task_id) VALUES (1,1)','INSERT INTO idempotency_records (project_id) VALUES (1)','INSERT INTO outbox_events (project_id) VALUES (1)','SET NAMES utf8mb4','SELECT 1']
def main():
 log=(ROOT/'manual12-digest-server-v2.log').open('ab')
 server=subprocess.Popen([str(BINARY/'mysqld'),'--no-defaults','--datadir='+str(DATA),'--skip-networking','--mysqlx=OFF','--socket='+SOCKET,'--pid-file='+str(DATA/'server.pid'),'--innodb-buffer-pool-size=128M'],stdout=log,stderr=subprocess.STDOUT)
 client=[str(BINARY/'mysql'),'--no-defaults','--socket='+SOCKET,'-uroot','-N','-B'];rows=[]
 try:
  for _ in range(100):
   if subprocess.run(client+['-e','SELECT 1'],capture_output=True).returncode==0:break
   time.sleep(.1)
  else:raise RuntimeError('OWN_LOCAL_SERVER_NOT_READY')
  subprocess.run(client+['-e','CREATE DATABASE IF NOT EXISTS manual12_digest'],capture_output=True,check=True)
  client += ['--database=manual12_digest']
  shapes=json.loads(Path(__file__).with_name('static-statement-shapes.PUBLIC.json').read_text())
  for sql in STATEMENTS+[x['sql'] for x in shapes]:
   quoted=sql.replace("'","''")
   p=subprocess.run(client+['-e',"SELECT STATEMENT_DIGEST('"+quoted+"'),STATEMENT_DIGEST_TEXT('"+quoted+"')"],capture_output=True,text=True)
   parts=p.stdout.strip().split('\t')
   rows.append({'synthetic_sql':sql,'exit_code':p.returncode,'digest':parts[0] if p.returncode==0 else None,'normalized':parts[1] if p.returncode==0 else None,'error':p.stderr.strip() or None})
  out=Path(__file__).with_name('native-digest-map.PUBLIC.json');out.write_text(json.dumps({'server':'local MySQL8.4.11 skip-networking','source':'static synthetic SQL only','rows':rows},indent=2)+'\n');print(out.read_text())
 finally:
  subprocess.run([str(BINARY/'mysqladmin'),'--no-defaults','--socket='+SOCKET,'-uroot','shutdown'],capture_output=True);server.wait(timeout=30)
if __name__=='__main__':main()
