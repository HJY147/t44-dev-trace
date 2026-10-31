"""Exercise the multi-host controller without SSH, servers or private test tools."""
import hashlib,importlib.util,io,json,subprocess,sys,tarfile,tempfile
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('coordinator_direct',HERE/'run.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
CONTRACT=json.loads((HERE.parents[2]/'records/qa/direct-p18.PUBLIC/CLI_CONTRACT.PUBLIC.json').read_bytes())
CONTRACT['direct_shell_sha256']='a'*64
class FakeSSH:
 def __init__(self,fail_app=False,bad_backup=False):self.calls=[];self.fail_app=fail_app;self.bad_backup=bad_backup
 def run(self,host,argv,data=None,timeout=180):
  self.calls.append((host,argv,data))
  if any(str(x).endswith('/deployment/start.py')for x in argv):
   if self.fail_app:raise RuntimeError('INJECTED_INITIALIZATION_FAILURE')
   return json.dumps({'status':'INIT_DONE','bootstrap_output':m.REMOTE+'/app-init/bootstrap'}).encode()
  if any('wrapper-exit.PUBLIC.json' in str(x)for x in argv):return b'{"done":true,"value":{"exit_code":1}}'
  if any(str(x).endswith('OBSERVE_DIRECT.py')for x in argv):return b'{"phase":{"phase":"FINISHED","clients_started":400}}'
  return b'{}'
 def get(self,host,remote,local,timeout=600):
  self.calls.append((host,['get',remote],None))
  if remote.endswith('recipient.PUBLIC.pem'):data=b'SYNTHETIC_PUBLIC_CERT_ONLY'
  elif remote.endswith('inputs.753cms'):data=b'SYNTHETIC_ENCRYPTED_INPUTS_ONLY'
  elif remote.endswith('.753backup'):data=b'SYNTHETIC_ENCRYPTED_BACKUP_ONLY'
  elif remote.endswith('.753backup.receipt.json'):
   raw=b'SYNTHETIC_ENCRYPTED_BACKUP_ONLY';data=json.dumps({'cipher_bytes':len(raw),'cipher_sha256':('b'*64 if self.bad_backup else hashlib.sha256(raw).hexdigest())}).encode()
  else:data=b'{}'
  local.write_bytes(data)
def must_fail(fn):
 try:fn()
 except (RuntimeError,FileExistsError,ValueError):return
 raise AssertionError('Expected rejection')
def archive(name='data.txt'):
 values={name:b'public-test-data'};manifest={'files':{name:{'bytes':len(values[name]),'sha256':hashlib.sha256(values[name]).hexdigest()}}}
 values['MANIFEST.PUBLIC.json']=json.dumps(manifest).encode();buf=io.BytesIO()
 with tarfile.open(fileobj=buf,mode='w:gz')as t:
  for n,b in values.items():
   i=tarfile.TarInfo(n);i.size=len(b);t.addfile(i,io.BytesIO(b))
 return buf.getvalue()
def main():
 with tempfile.TemporaryDirectory(prefix='t44-direct-controller-')as tmp:
  root=Path(tmp)
  ssh=FakeSSH();result=m.execute(ssh,b'public-kit','f'*64,CONTRACT,root,notify=lambda x:None,sleep=lambda x:None)
  assert result['status']=='EVIDENCE_RECOVERED_CAN_STOP_BOTH_SERVERS' and result['performance_pass_claimed']is False
  assert json.loads((root/'wrapper-exit.PUBLIC.json').read_bytes())['exit_code']==1
  downloaded=[c[1][1]for c in ssh.calls if c[1][0]=='get']
  assert not any(x.endswith(('current-inputs.private.json','load-only-private.pem'))for x in downloaded)
  assert len([c for c in ssh.calls if any(str(x).endswith('/coordinator/launch.py')for x in c[1])])==1
  print('PASS full controller graph; NP still downloads; no plaintext/keys copied')
 with tempfile.TemporaryDirectory()as tmp:
  ssh=FakeSSH(fail_app=True);must_fail(lambda:m.execute(ssh,b'kit','f'*64,CONTRACT,Path(tmp),notify=lambda x:None))
  assert not any(any(str(x).endswith('/coordinator/launch.py')for x in c[1])for c in ssh.calls)
  print('PASS initialization failure never dispatches or retries')
 with tempfile.TemporaryDirectory()as tmp:
  must_fail(lambda:m.execute(FakeSSH(bad_backup=True),b'kit','f'*64,CONTRACT,Path(tmp),notify=lambda x:None))
  assert not (Path(tmp)/'RECOVERY.PUBLIC.json').exists()
  print('PASS wrong backup digest cannot claim recovered/safe stop')
 class OptionalFailure(FakeSSH):
  def __init__(self):super().__init__();self.polls=0
  def run(self,host,argv,data=None,timeout=180):
   if any('wrapper-exit.PUBLIC.json'in str(x)for x in argv):
    self.polls+=1
    if self.polls==1:return b'{"done":false,"value":null}'
   if any(str(x).endswith('OBSERVE_DIRECT.py')for x in argv):raise RuntimeError('OPTIONAL_OBSERVER_UNAVAILABLE')
   return super().run(host,argv,data,timeout)
 with tempfile.TemporaryDirectory()as tmp:
  ssh=OptionalFailure();result=m.execute(ssh,b'kit','f'*64,CONTRACT,Path(tmp),notify=lambda x:None,sleep=lambda x:None)
  assert result['status']=='EVIDENCE_RECOVERED_CAN_STOP_BOTH_SERVERS'and ssh.polls==2
  print('PASS missing optional observation cannot abandon active run or final backup')
 with tempfile.TemporaryDirectory()as tmp:
  for name,label in [('data.txt','valid'),('../escape','unsafe')]:
   raw=archive(name);target=Path(tmp)/label
   code=m.INSTALL.replace(repr(m.REMOTE),repr(str(target)))
   run=subprocess.run([sys.executable,'-c',code,hashlib.sha256(raw).hexdigest()],input=raw,capture_output=True)
   assert (run.returncode==0)==(label=='valid')
  assert not (Path(tmp)/'unsafe/escape').exists()
  print('PASS actual archive install/hash roundtrip and traversal refusal')
 spec=importlib.util.spec_from_file_location('direct_launch',HERE/'launch.py');launch=importlib.util.module_from_spec(spec);spec.loader.exec_module(launch)
 with tempfile.TemporaryDirectory()as tmp:
  root=Path(tmp);w=root/'w';(w/'public').mkdir(parents=True);shell=w/'public/DIRECT_PRESSURE.sh';shell.write_text('# synthetic public script\n');inp=root/'session.private.json';inp.write_text('{}');channel=root/'controller'
  argv=['launch','--workspace',str(w),'--inputs',str(inp),'--channel',str(channel),'--shell-sha256',hashlib.sha256(shell.read_bytes()).hexdigest()]
  with patch.object(sys,'argv',argv),patch.object(launch.subprocess,'Popen')as pop:
   pop.return_value.pid=123;launch.main();must_fail(launch.main);assert pop.call_count==1
  print('PASS once-only detached launch; controller outside sealed workspace')
 good={'run':m.RUN,'source':'bcec3326b40814fdb1922bbfea7c29473b47ba47'}
 m.validate_contract(good,CONTRACT)
 for target,key,bad in [('contract','run_id','r30directp16'),('contract','workspace','/root/old-consumed'),('contract','backup_receipt_path','/root/old.receipt'),('contract','download_backup_even_on_nonzero_exit',False),('manifest','source','wrong-source')]:
  c=dict(CONTRACT);v=dict(good)
  (c if target=='contract' else v)[key]=bad
  must_fail(lambda:m.validate_contract(v,c))
 print('PASS exact new run/workspace/source/backup contract; 5 stale or incomplete contracts refused')
 assert result['measurement_wrapper_exit_code']==1
 print('PASS measurement NP remains nonzero status after evidence recovery')
 with tempfile.TemporaryDirectory() as tmp:
  here=Path(tmp);(here/'run.py').write_text('synthetic source')
  ready=here/'READY.PUBLIC.json'
  ready.write_text(json.dumps({'status':'PREPARING_DO_NOT_START_SERVERS'}))
  with patch.object(m,'__file__',str(here/'run.py')):
   must_fail(lambda:m.require_ready('a'*64))
   ready.write_text(json.dumps({'status':'READY_FOR_USER_BOOT','archive_sha256':'a'*64,'local_files_sha256':{'run.py':hashlib.sha256((here/'run.py').read_bytes()).hexdigest()}}))
   m.require_ready('a'*64)
   must_fail(lambda:m.require_ready('b'*64))
   (here/'run.py').write_text('changed')
   must_fail(lambda:m.require_ready('a'*64))
 print('PASS shared READY gate refuses pending, archive mismatch and changed local source')
 with tempfile.TemporaryDirectory()as tmp:
  ssh=FakeSSH();r=m.recover_after_failure(ssh,CONTRACT,Path(tmp),notify=lambda x:None)
  assert r['status']=='EVIDENCE_RECOVERED_CAN_STOP_BOTH_SERVERS'and r['measurement_wrapper_exit_code']==1
  assert not any(any('launch.py'in str(x) for x in c[1])for c in ssh.calls)
  assert r['backup_path'].endswith('.fallback.753backup')
 class StillRunning(FakeSSH):
  def run(self,host,argv,data=None,timeout=180):
   if any('wrapper-exit.PUBLIC.json'in str(x)for x in argv):return b'{"done":false,"value":null}'
   raise AssertionError('No other remote action allowed when producer exit unknown')
 with tempfile.TemporaryDirectory()as tmp:
  ssh=StillRunning();assert m.recover_after_failure(ssh,CONTRACT,Path(tmp),notify=lambda x:None)is None
  assert not(Path(tmp)/'RECOVERY.PUBLIC.json').exists()
 with tempfile.TemporaryDirectory()as tmp:
  must_fail(lambda:m.recover_after_failure(FakeSSH(bad_backup=True),CONTRACT,Path(tmp),notify=lambda x:None))
  assert not(Path(tmp)/'RECOVERY.PUBLIC.json').exists()
 print('PASS failure recovery only fetches sealed evidence after wrapper exit; active/unknown not sealed; digest mismatch refuses stop claim')
 argv=['run','--app-ip','8.8.8.8','--load-ip','1.1.1.1','--kit','/does-not-exist','--kit-sha256','a'*64,'--identity','/does-not-exist','--known-hosts','/does-not-exist','--output','/does-not-exist']
 with patch.object(sys,'argv',argv),patch.object(m.SSH,'run')as net:
  must_fail(m.main);net.assert_not_called()
 print('PASS direct CLI also refuses PREPARING before any SSH')
 print('ALL 11 CONTROLLER CHECK GROUPS PASS; actual SSH/VM calls=0')
if __name__=='__main__':main()
