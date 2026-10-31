"""Independent offline mocks. Never invokes SSH/subprocess/SUT."""
import importlib.util,json,tempfile,hashlib
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[3]
s=importlib.util.spec_from_file_location('audited_run',ROOT/'agents/coordinator/direct-p17/run.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
contract=json.loads((ROOT/'records/qa/direct-p17.PUBLIC/CLI_CONTRACT.PUBLIC.json').read_bytes())
results={}
class FakeSSH:
 def __init__(self):self.events=[]
 def run(self,host,argv,**kwargs):
  self.events.append('run:'+host)
  return json.dumps({'done':True,'value':{'exit_code':2}}).encode()
 def get(self,host,remote,local,**kwargs):
  self.events.append('get:'+remote)
  if remote.endswith('.receipt.json'):local.write_text(json.dumps({'cipher_bytes':3,'cipher_sha256':hashlib.sha256(b'abc').hexdigest()}))
  else:local.write_bytes(b'abc')
def init(*args):return {'status':'INIT_DONE','bootstrap_output':'/synthetic'}
with tempfile.TemporaryDirectory() as d,patch.object(m,'initialize',init):
 ssh=FakeSSH()
 v=m.execute(ssh,b'', 'unused',contract,Path(d),notify=lambda x:ssh.events.append('notify:'+str(x.get('status')) if isinstance(x,dict) else x),sleep=lambda _:None)
 results['nonzero_recovers']=v['measurement_wrapper_exit_code']==2
 results['app_stop_notice_before_backup_download']=ssh.events.index('notify:APP_EVIDENCE_RECOVERED_CAN_STOP_APP')<ssh.events.index('get:'+contract['backup_path'])
 results['nonzero_events']=ssh.events
with tempfile.TemporaryDirectory() as d,patch.object(m,'initialize',init),patch.object(m.time,'monotonic',side_effect=[0,2000]):
 ssh=FakeSSH()
 try:m.execute(ssh,b'','unused',contract,Path(d),notify=lambda _:None,sleep=lambda _:None)
 except RuntimeError as e:results['timeout_error']=str(e)
 results['timeout_backup_fetches']=[e for e in ssh.events if '.753backup' in e]
results['run_source_has_READY_check']='READY.PUBLIC.json' in (ROOT/'agents/coordinator/direct-p17/run.py').read_text()
from types import SimpleNamespace
with tempfile.TemporaryDirectory() as d:
 kit=Path('/tmp/t44-direct17-candidate-v2-20261031.tar.gz')
 called=[]
 argv=['run.py','--app-ip','8.8.8.8','--load-ip','1.1.1.1','--kit',str(kit),'--kit-sha256',hashlib.sha256(kit.read_bytes()).hexdigest(),'--identity','/synthetic/key','--known-hosts','/synthetic/pins','--output',str(Path(d)/'new')]
 helper=SimpleNamespace(prepare=lambda *args:None)
 spec=SimpleNamespace(loader=SimpleNamespace(exec_module=lambda mod:None))
 with patch.object(m.sys if hasattr(m,'sys') else __import__('sys'),'argv',argv),patch.object(m.importlib.util,'spec_from_file_location',return_value=spec),patch.object(m.importlib.util,'module_from_spec',return_value=helper),patch.object(m,'execute',side_effect=lambda *a,**k:called.append(True) or {'measurement_wrapper_exit_code':0}):
  results['direct_main_exit']=m.main()
 results['direct_main_reached_execute_while_source_READY_PREPARING']=bool(called)
print(json.dumps(results,indent=2))
