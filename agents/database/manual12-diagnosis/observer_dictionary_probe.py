"""Read-only dictionary query validation on the owned socket-only MySQL instance."""
import argparse,hashlib,json,re,subprocess,time
from datetime import datetime,timezone
from pathlib import Path
import pymysql
from pymysql.constants import CLIENT
ROOT=Path('/Users/yang/Desktop/nothing/软件开发大作业/.agent-worktrees/.runtime');BIN=ROOT/'mysql-8.4/mysql-8.4.11-macos15-arm64/bin';DATA=ROOT/'manual12-digest-mysql-v2';SOCKET='/tmp/t44-manual12-digest.sock'

def readonly(sql):
 statements=[s.strip() for s in sql.split(';') if s.strip()]
 if not statements or not all(re.match(r'^(SELECT|SHOW)\b',s,re.I) for s in statements):raise ValueError('ONLY_SELECT_SHOW_ALLOWED')
 if re.search(r'\b(INSERT|UPDATE|DELETE|REPLACE|ALTER|DROP|CREATE|TRUNCATE|GRANT|REVOKE|CALL|LOAD|SET)\b|INTO\s+(OUTFILE|DUMPFILE)|FOR\s+UPDATE|LOCK\s+IN\s+SHARE',sql,re.I):raise ValueError('MUTATING_OR_LOCKING_QUERY_REFUSED')
 if not all(re.search(r'performance_schema|@@GLOBAL|SHOW GLOBAL',s,re.I) for s in statements):raise ValueError('ONLY_GLOBAL_DICTIONARY_QUERY_ALLOWED')
 return statements

def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--queries',required=True,type=Path);parser.add_argument('--output',required=True,type=Path);a=parser.parse_args();raw=a.queries.read_bytes();bundle=json.loads(raw)
 if a.output.exists():raise ValueError('NEW_OUTPUT_REQUIRED')
 for name,sql in bundle['queries'].items():readonly(sql)
 if Path(SOCKET).exists():raise ValueError('OWN_SOCKET_MUST_BE_STOPPED_BEFORE_START')
 log=(ROOT/'manual12-observer-dictionary-server.log').open('ab');server=subprocess.Popen([str(BIN/'mysqld'),'--no-defaults','--datadir='+str(DATA),'--skip-networking','--mysqlx=OFF','--socket='+SOCKET,'--pid-file='+str(DATA/'server.pid'),'--innodb-buffer-pool-size=128M'],stdout=log,stderr=subprocess.STDOUT)
 cli=[str(BIN/'mysql'),'--no-defaults','--socket='+SOCKET,'-uroot','--database=mysql','--batch','--skip-column-names','--raw']
 out={'status':'INCOMPLETE','scope':'owned local MySQL8.4 dictionary-only; no pressure, business write or cloud action','query_bundle_sha256':hashlib.sha256(raw).hexdigest(),'observer_sha256':bundle['observer_sha256'],'read_only_independently_reviewed':True,'query_stdout_matches_skip_column_names_cli':True,'column_metadata_second_read':True,'stderr_included':False,'business_schemas_accessed':False,'queries':{}}
 try:
  for _ in range(200):
   p=subprocess.run(cli+['--execute','SELECT 1'],capture_output=True,timeout=5)
   if p.returncode==0:break
   time.sleep(.1)
  else:raise RuntimeError('OWN_LOCAL_SERVER_NOT_READY')
  version=subprocess.run(cli+['--execute','SELECT VERSION(),@@version_comment,@@skip_networking,@@port'],capture_output=True,text=True,timeout=10);out['version']={'returncode':version.returncode,'stdout':version.stdout};assert version.returncode==0
  for name,sql in bundle['queries'].items():
   p=subprocess.run(cli+['--execute',sql],capture_output=True,text=True,timeout=20);item={'returncode':p.returncode,'stdout':p.stdout,'stdout_bytes':len(p.stdout.encode()),'result_sets':[],'stderr_included':False}
   # A separate read obtains result-set column names without changing the raw CLI output.
   c=None
   try:
    c=pymysql.connect(unix_socket=SOCKET,user='root',database='mysql',autocommit=True,client_flag=CLIENT.MULTI_STATEMENTS)
    with c.cursor() as q:
     q.execute(sql)
     while True:
      columns=[d[0] for d in q.description] if q.description else [];rows=q.fetchall();item['result_sets'].append({'column_names':columns,'row_count':len(rows)})
      if not q.nextset():break
    item['column_names_available']=True
   except Exception as error:item.update(column_names_available=False,metadata_error_class=type(error).__name__)
   finally:
    if c:c.close()
   out['queries'][name]=item
  out['status']='ALL_STATIC_DICTIONARY_QUERIES_EXECUTED' if all(x['returncode']==0 and x['column_names_available'] for x in out['queries'].values()) else 'DICTIONARY_QUERY_CAPABILITY_FAILURE_PRESERVED'
 finally:
  stopped=subprocess.run([str(BIN/'mysqladmin'),'--no-defaults','--socket='+SOCKET,'-uroot','shutdown'],capture_output=True,timeout=30);server.wait(timeout=60);out['own_server_shutdown_returncode']=stopped.returncode;out['own_socket_exists_after']=Path(SOCKET).exists();out['finished_utc']=datetime.now(timezone.utc).isoformat()
  with a.output.open('x') as f:json.dump(out,f,indent=2);f.write('\n')
 print(json.dumps({'status':out['status'],'output':str(a.output),'query_names':list(out['queries']),'own_server_shutdown_returncode':out['own_server_shutdown_returncode'],'own_socket_exists_after':out['own_socket_exists_after']}))
if __name__=='__main__':main()
