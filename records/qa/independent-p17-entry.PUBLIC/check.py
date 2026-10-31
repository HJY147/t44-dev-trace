"""Independent offline entry audit; only synthetic fixtures and public archive bytes."""
import hashlib,importlib.util,json,pathlib,tarfile,tempfile,unittest.mock as mock,sys
ROOT=pathlib.Path(__file__).resolve().parents[3]
ENTRY=ROOT/'agents/coordinator/direct-p17'
def load(name):
 s=importlib.util.spec_from_file_location(name,ENTRY/(name+'.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
r=load('run');results=[]
def check(name,fn):
 fn();results.append(name)
def fail(fn):
 try:fn()
 except (ValueError,RuntimeError,SystemExit,FileNotFoundError):return
 raise AssertionError('expected refusal')
check('PREPARING require_ready refuses',lambda:fail(lambda:r.require_ready('0'*64)))
for mod,args in [('run',['--app-ip','8.8.8.8','--load-ip','1.1.1.1','--kit','/nonexistent','--kit-sha256','0'*64,'--identity','/none','--known-hosts','/none','--output','/none']),('after_boot',['--app-ip','8.8.8.8','--load-ip','1.1.1.1'])]:
 m=load(mod)
 with mock.patch.object(sys,'argv',[mod]+args),mock.patch('subprocess.run',side_effect=AssertionError('process before gate')),mock.patch('subprocess.check_output',side_effect=AssertionError('process before gate')):
  check(mod+' CLI refuses before subprocess',lambda:fail(m.main))
class SSH:
 def __init__(self,done=True,rc=2,corrupt=False):self.done=done;self.rc=rc;self.corrupt=corrupt;self.gets=[]
 def run(self,*a,**kw):return json.dumps({'done':self.done,'value':{'exit_code':self.rc}}).encode()
 def get(self,host,remote,local,**kw):
  self.gets.append(remote);data=b'synthetic sealed bytes';local.write_bytes(json.dumps({'cipher_bytes':len(data),'cipher_sha256':hashlib.sha256(data).hexdigest()}).encode() if remote.endswith('.json') else data+b'x'*self.corrupt)
c={'backup_path':'/mock/r30posttools17.753backup','backup_receipt_path':'/mock/r30posttools17.753backup.receipt.json'}
with tempfile.TemporaryDirectory() as d:
 p=pathlib.Path(d);notices=[];s=SSH(done=False)
 assert r.recover_after_failure(s,c,p,notices.append) is None and not s.gets
 results.append('unknown producer: zero downloads and no stop claim')
 s=SSH();v=r.recover_after_failure(s,c,p,notices.append);assert v['measurement_wrapper_exit_code']==2 and v['automatic_vm_shutdown'] is False and v['performance_pass_claimed'] is False
 results.append('nonzero exited producer: sealed download verified and both-stop notice')
 s=SSH(corrupt=True);check('corrupt archive refuses successful recovery',lambda:fail(lambda:r.recover_after_failure(s,c,p,notices.append)))
 check('noninteger exit proof refuses',lambda:fail(lambda:r.recover_backup(s,c,p,{'done':True,'value':{'exit_code':'0'}},notices.append)))
archive=pathlib.Path(sys.argv[1]);raw=archive.read_bytes();assert len(raw)==173353 and hashlib.sha256(raw).hexdigest()=='42a4fa69527c475f4374f3f57ad8ed88c16ff0bb4e95303acb311ef2ee2ceba3'
with tarfile.open(archive) as t:
 members=t.getmembers();manifest=json.load(t.extractfile('MANIFEST.PUBLIC.json'));assert len(manifest['files'])==62
 assert len(set(x.name for x in members))==len(members)
 assert set(x.name for x in members)==set(manifest['files'])|{'MANIFEST.PUBLIC.json'}
 for x in members:
  assert x.isfile() and not pathlib.PurePosixPath(x.name).is_absolute() and '..' not in pathlib.PurePosixPath(x.name).parts
  if x.name=='MANIFEST.PUBLIC.json':continue
  b=t.extractfile(x).read();v=manifest['files'][x.name];assert len(b)==v['bytes'] and hashlib.sha256(b).hexdigest()==v['sha256']
  parts=x.name.split('/');base={'backend':'agents/backend/fast-bootstrap','deployment':'agents/deployment/direct-start','qa':'records/qa/direct-p17.PUBLIC','coordinator':'agents/coordinator/direct-p17'}.get(parts[0])
  if x.name in ('deployment/RUN.PUBLIC.json','deployment/PERSISTENCE.PUBLIC.json'):base='agents/deployment/direct-p17'
  if x.name=='coordinator/ssh/update_ssh_addresses.py':local=ROOT/'agents/coordinator/manualp15-preparation/ssh/update_ssh_addresses.py'
  elif x.name=='coordinator/manual13-observe.py':local=ROOT/'agents/coordinator/manualp15-preparation/coordinator/manual13-observe.py'
  elif base:local=ROOT/base/pathlib.Path(*parts[1:])
  else:continue
  if local.exists() and x.name not in ('qa/DELIVERY_MANIFEST.PUBLIC.json','qa/FRESH_RUN_BINDING.PUBLIC.json'):assert local.read_bytes()==b,x.name
 results.append('archive exact pinned bytes SHA; 62 payload; regular unique safe paths; every payload bytes/SHA; mapped neutral execution/CLI contract byte equality; DELIVERY_MANIFEST and FRESH_RUN_BINDING metadata hash-only')
print(json.dumps({'status':'OFFLINE_CHECKS_PASS','checks':results,'real_connections':0,'linux_runtime_verified':False,'archive_sha256':hashlib.sha256(raw).hexdigest()},indent=2))
