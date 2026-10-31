"""Exercise the multi-host controller without SSH, servers or private test tools."""
import hashlib,importlib.util,io,json,subprocess,sys,tarfile,tempfile
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('coordinator_direct',HERE/'run.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
CONTRACT=json.loads((HERE.parents[2]/'records/qa/direct-p16.PUBLIC/CLI_CONTRACT.PUBLIC.json').read_bytes())
CONTRACT['direct_shell_sha256']='a'*64
class FakeSSH:
 def __init__(self,fail_app=False,bad_backup=False):self.calls=[];self.fail_app=fail_app;self.bad_backup=bad_backup
 def run(self,host,argv,data=None,timeout=180):
  self.calls.append((host,argv,data))
  if any(str(x).endswith('/deployment/start.py')for x in argv):
   if self.fail_app:raise RuntimeError('INJECTED_INITIALIZATION_FAILURE')
   return json.dumps({'status':'INIT_DONE','bootstrap_output':m.REMOTE+'/init/bootstrap'}).encode()
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
 with tempfile.TemporaryDirectory()as tmp:
  for name,label in [('data.txt','valid'),('../escape','unsafe')]:
   raw=archive(name);target=Path(tmp)/label
   code=m.INSTALL.replace("'/root/t44-direct-p16'",repr(str(target)))
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
 print('ALL 5 CONTROLLER CHECK GROUPS PASS; actual SSH/VM calls=0')
if __name__=='__main__':main()
