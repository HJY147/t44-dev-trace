import importlib.util,json,hashlib,tarfile,tempfile,subprocess,sys,copy
from pathlib import Path
ROOT=Path('/Users/yang/Desktop/nothing/软件开发大作业/.agent-worktrees/global-latency-repair-20261031')
OUT=Path(__file__).parent
results=[]
def check(name,fn):
 fn();results.append({'check':name,'pass':True})
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
run=load('entry',ROOT/'agents/coordinator/direct-p18/run.py')
boot=load('producer',ROOT/'agents/backend/direct-p18-bootstrap/bootstrap.py')
sha=lambda b:hashlib.sha256(b).hexdigest()
def identity():
 m=json.loads((ROOT/'records/qa/direct-p18.PUBLIC/tool-manifest.json').read_bytes())
 for n,h in m['files'].items():
  if n.endswith('.key'):continue
  assert sha((Path('/tmp/t44-direct-p18-private')/n).read_bytes())==h,n
 for n in ('runtime.py','post_runtime.py','compiled_post.py','functional.py','openapi.json','backup.py','verify_backup.py','verify_raw.py'):
  assert (Path('/tmp/t44-direct-p18-private')/n).read_bytes()==(Path('/tmp/t44-post-v12-private')/n).read_bytes(),n
 assert (Path('/tmp/t44-post-v12-private/direct_boot.py').read_bytes().replace(b"RUN='r30posttools17'",b"RUN='r30posttools18'"))==Path('/tmp/t44-direct-p18-private/direct_boot.py').read_bytes()
 e=m['effective_runtime'];assert sha(json.dumps(e,sort_keys=True,separators=(',',':')).encode())==m['effective_runtime_binding_sha256']
check('tool-source-hashes-base-post-compiled-unchanged-only-BOOT-RUN-diff',identity)
def gates():
 for script,args in [('after_boot.py',['--app-ip','8.8.8.8','--load-ip','1.1.1.1']),('run.py',['--app-ip','8.8.8.8','--load-ip','1.1.1.1','--kit','/nonexistent','--kit-sha256','0'*64,'--identity','/nonexistent','--known-hosts','/nonexistent','--output','/nonexistent'])]:
  p=subprocess.run([sys.executable,'-B',str(ROOT/'agents/coordinator/direct-p18'/script),*args],capture_output=True)
  assert p.returncode!=0 and b'OFFLINE_PREPARATION_NOT_COMPLETE' in p.stderr
check('both-Mac-CLI-PREPARING-reject-before-key-kit-or-SSH',gates)
def normalization():
 old={'inventory':{'clients':[{'project_id':1,'transition_task':{'id':i}} for i in range(1,401)]}}
 tasks={1:{i:{'id':i,'project_id':1,'owner_id':7,'state':2 if i%2 else 3,'blocked_from_state':2,'version':10} for i in range(1,401)}}
 class API:
  def __init__(self):self.writes=[]
  def request(self,path,token,body=None,**kw):
   i=int(path.split('/')[4]);t=tasks[1][i]
   if body:
    assert t['state']==3 and body['action']==3 and body['expected_version']==10 and body['evidence'] and kw['idempotency_key'] and token=='test'
    self.writes.append(i);return {},{}
   return dict(t,state=2,version=11),{}
 a=API();r=boot.normalize_transition_tasks(old,{'developer':{'user_id':7,'token':'test'}},tasks,a,'test18')
 assert r['checked']==400 and r['http_writes']==200 and a.writes==list(range(2,401,2)) and set(tasks[1])==set(range(1,401))
 tasks[1][400]['state']=4;a=API()
 try:boot.normalize_transition_tasks(old,{'developer':{'user_id':7}},tasks,a,'test18')
 except ValueError:pass
 else:raise AssertionError('invalid state accepted')
 assert not a.writes
check('mixed-400-normalization-state2-no-write-CAS-evidence-fixed-IDs-all-preflight',normalization)
def recovery():
 with tempfile.TemporaryDirectory() as d:
  class SSH:
   def __init__(self):self.calls=[]
   def get(self,host,remote,local,**kw):
    self.calls.append(remote);local.write_bytes(json.dumps({'cipher_bytes':4,'cipher_sha256':sha(b'data')}).encode() if remote.endswith('.json') else b'data')
  s=SSH();contract={'backup_path':'a','backup_receipt_path':'a.json'}
  try:run.recover_backup(s,contract,Path(d),{'done':False},lambda _:None)
  except RuntimeError:pass
  else:raise AssertionError('unproven producer accepted')
  assert not s.calls
  r=run.recover_backup(s,contract,Path(d),{'done':True,'value':{'exit_code':2}},lambda _:None)
  assert r['backup_bytes']==4 and r['measurement_wrapper_exit_code']==2 and not r['automatic_vm_shutdown']
check('unknown-exit-no-download-or-stop-claim-nonzero-exit-backup-verifies',recovery)
def archive():
 p=Path(sys.argv[1]);raw=p.read_bytes()
 with tarfile.open(p) as t:
  m=json.load(t.extractfile('MANIFEST.PUBLIC.json'));members=t.getmembers()
  assert {x.name for x in members}==set(m['files'])|{'MANIFEST.PUBLIC.json'}
  assert len({x.name for x in members})==len(members)
  for x in members:
   assert x.isfile() and not Path(x.name).is_absolute() and '..' not in Path(x.name).parts
   if x.name=='MANIFEST.PUBLIC.json':continue
   b=t.extractfile(x).read();v=m['files'][x.name];assert len(b)==v['bytes'] and sha(b)==v['sha256'],x.name
   mapped={'backend':'agents/backend/direct-p18-bootstrap','deployment':'agents/deployment/direct-p18','qa':'records/qa/direct-p18.PUBLIC','coordinator':'agents/coordinator/direct-p18'}
   folder,name=x.name.split('/',1)
   if folder in mapped and '/' not in name:
    source=ROOT/mapped[folder]/name
    if source.exists():assert b==source.read_bytes(),x.name
  run.validate_contract(m,json.load(t.extractfile('qa/CLI_CONTRACT.PUBLIC.json')))
 results.append({'archive':str(p),'bytes':len(raw),'sha256':sha(raw),'members':len(members)})
check('archive-closed-members-content-hashes-local-source-contract',archive)
(OUT/'CHECKS.PUBLIC.json').write_text(json.dumps({'platform':sys.platform,'cloud_calls':0,'network_calls':0,'results':results},indent=2)+'\n')
print(json.dumps(results,indent=2))
