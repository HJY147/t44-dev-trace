"""Independent offline review. All subjects and data are synthetic; no sockets."""
import copy, hashlib, importlib.util, json, subprocess, tempfile, unittest
from pathlib import Path

def load(name, path):
 s=importlib.util.spec_from_file_location(name,path); m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
SUBJECT='0b941a6df0f6fa9117bf52dd1dbaae649d2874f6'
_tmp=tempfile.TemporaryDirectory(prefix='p18-independent-source-')
def source_file(name,expected):
 raw=subprocess.check_output(['git','show',SUBJECT+':agents/backend/direct-p18-bootstrap/'+name])
 assert hashlib.sha256(raw).hexdigest()==expected
 path=Path(_tmp.name)/name;path.write_bytes(raw);return path
b=load('subject',source_file('bootstrap.py','c7e77a5f6d0c2a3c2cf4792ff599e84124387d932307196704cf10b5dfdfd42c'))
r=load('support',source_file('runtime_support.py','ebbf9a15b8ea9dd8f4294b6d48aacd9f603b2ab9881cce797e4945f09711b77e'))

def fixture():
 rows=[];tasks={1:{}}
 for i in range(400):
  row={'client_id':i,'project_id':1,'transition_task':{'id':i+1},'escalation_task':{'id':i+401}}
  rows.append(row)
  for tid in (i+1,i+401):tasks[1][tid]={'id':tid,'project_id':1,'owner_id':2,'state':2,'version':7,'schedule_version':1,'blocked_from_state':None}
 old={'inventory':{'clients':rows},'identity':{},'environment':{'origin':'https://synthetic.invalid','ca_sha256':'synthetic'},'counts':{},'sessions':{x:{'user_id':j} for x,j in [('manager',1),('developer',2),('reviewer',3)]}}
 return old,tasks
class API:
 def __init__(self,tasks):self.tasks=copy.deepcopy(tasks);self.requests=[];self.fail=None;self.bad_read=False
 def pages(self,path,token):
  self.requests.append(('GET',path))
  return list(copy.deepcopy(self.tasks[1]).values()) if path.endswith('/tasks') else []
 def request(self,path,token=None,body=None,**kw):
  self.requests.append(('POST' if body is not None else 'GET',path,body))
  if path=='/auth/login':
   uid={'manager':1,'developer':2,'reviewer':3}[body['username']];return {'user':{'id':uid},'access_token':'synthetic'+str(uid),'expires_at':'2099-01-01T00:00:00Z'},None
  tid=int(path.split('/')[4]);task=self.tasks[1][tid]
  if body is not None:
   if self.fail:raise RuntimeError(self.fail)
   assert body['action']==3 and body['expected_version']==task['version'] and body['basis'] and body['evidence'] and kw['idempotency_key']
   task.update(state=2,version=task['version']+1,blocked_from_state=None)
  value=copy.deepcopy(task)
  if self.bad_read and body is None:value['version']-=1
  return value,None
 def writes(self):return [x for x in self.requests if x[0]=='POST' and x[1]!='/auth/login']
def collect(old,tasks,configure=lambda a:None):
 api=API(tasks);configure(api)
 accounts={r:{'username':r,'password':'synthetic','user_id':v['user_id']} for r,v in old['sessions'].items()}
 result=b.collect(old,accounts,api,lambda:({'user_id':4,'token':'synthetic-service'},b'{}'),lambda s:s,'synthetic-r30posttools18')
 return result[0],api
class Synthetic(unittest.TestCase):
 def test_all_developing_zero_write(self):
  old,t=fixture();v,a=collect(old,t);self.assertEqual(a.writes(),[]);self.assertEqual(len(v['inventory']['clients']),400);self.assertEqual(v['environment'],old['environment']);self.assertEqual(v['transition_initialization']['already_developing'],400)
 def test_mixed_authoritative(self):
  old,t=fixture()
  for i in range(1,401,2):t[1][i].update(state=3,blocked_from_state=2)
  v,a=collect(old,t);self.assertEqual(len(a.writes()),200)
  for row in v['inventory']['clients']:
   task=row['transition_task'];self.assertEqual(task['state'],2);self.assertEqual(task['version'],8 if task['id']%2 else 7)
  for i,x in enumerate(a.requests):
   if x in a.writes():self.assertEqual(a.requests[i+1][:2],('GET',x[1].removesuffix('/transitions')))
 def test_all_blocked(self):
  old,t=fixture()
  for i in range(1,401):t[1][i].update(state=3,blocked_from_state=2)
  v,a=collect(old,t);self.assertEqual(len(a.writes()),400)
 def test_preflight_all_before_write(self):
  for change in ('owner','state','from','project','missing','duplicate'):
   with self.subTest(change=change):
    old,t=fixture();t[1][1].update(state=3,blocked_from_state=2)
    if change=='owner':t[1][400]['owner_id']=999
    if change=='state':t[1][400]['state']=6
    if change=='from':t[1][400].update(state=3,blocked_from_state=4)
    if change=='project':t[1][400]['project_id']=9
    if change=='missing':del t[1][800]
    if change=='duplicate':old['inventory']['clients'][-1]['escalation_task']['id']=1
    a=API(t);accounts={r:{'username':r,'password':'synthetic','user_id':v['user_id']} for r,v in old['sessions'].items()}
    with self.assertRaises((ValueError,KeyError)):b.collect(old,accounts,a,lambda:({},b'{}'),lambda s:s,'synthetic')
    self.assertEqual(a.writes(),[])
 def test_rejection_ambiguity_no_retry(self):
  for reason in ('VERSION_CONFLICT','ACTION_FORBIDDEN','DEPENDENCIES_UNSATISFIED','CONNECTION_LOST_AFTER_WRITE'):
   old,t=fixture();t[1][1].update(state=3,blocked_from_state=2);a=API(t);a.fail=reason
   with self.assertRaises(RuntimeError):b.normalize_transition_tasks(old,{'developer':{'user_id':2,'token':'synthetic'}},t,a,'synthetic')
   self.assertEqual(len(a.writes()),1)
 def test_readback_refused(self):
  old,t=fixture();t[1][1].update(state=3,blocked_from_state=2);a=API(t);a.bad_read=True
  with self.assertRaisesRegex(ValueError,'AUTHORITATIVE'):b.normalize_transition_tasks(old,{'developer':{'user_id':2,'token':'synthetic'}},t,a,'synthetic')
  self.assertEqual(len(a.writes()),1)
 def test_exclusive_write(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'old';b.exclusive_write(p,b'old')
   with self.assertRaises(FileExistsError):b.exclusive_write(p,b'new')
   self.assertEqual(p.read_bytes(),b'old')
 def test_chinese_binding(self):
  value={'中文':'原资源'};self.assertEqual(json.loads(b.canonical(value)),value);self.assertIn('原资源'.encode(),b.canonical(value))

class HostFailure(unittest.TestCase):
 def invoke(self,d,returncode):
  from unittest.mock import patch
  import sys
  folder=Path(d);old,_=fixture();old['binding_sha256']=b.sha(b.canonical(old))
  receipt={'source_sha':b.SOURCE,'source_manifest_sha256':b.SOURCE_MANIFEST,'bundle_manifest_sha256':b.BUNDLE_MANIFEST,'identity':{'success':True,'config_id':b.CONFIG}}
  for name,value in [('old',old),('accounts',{}),('receipt',receipt)]: (folder/name).write_bytes(b.canonical(value))
  for name in ('ca','support'):(folder/name).write_text('synthetic')
  args=['subject','--old-packet',str(folder/'old'),'--accounts',str(folder/'accounts'),'--ca',str(folder/'ca'),'--runtime-support',str(folder/'support'),'--import-receipt',str(folder/'receipt'),'--output',str(folder/'output'),'--api-container','synthetic','--run-id','synthetic-r30posttools18']
  outcome=subprocess.CompletedProcess([],returncode,b'',b'synthetic')
  with patch.object(sys,'argv',args),patch.object(b.os,'geteuid',return_value=0),patch.object(b.subprocess,'run',return_value=outcome) as call:
   with self.assertRaises(ValueError):b.main()
   self.assertEqual(call.call_count,1)
  return folder/'output'
 def test_failed_runtime_no_direct(self):
  with tempfile.TemporaryDirectory() as d:
   output=self.invoke(d,1);self.assertTrue((output/'FAILED.PUBLIC.json').exists());self.assertFalse((output/'current-inputs.private.json').exists());self.assertFalse((output/'bootstrap.PUBLIC.json').exists())
 def test_invalid_success_payload_no_direct(self):
  with tempfile.TemporaryDirectory() as d:
   output=self.invoke(d,0);self.assertTrue((output/'FAILED.PUBLIC.json').exists());self.assertFalse((output/'bootstrap.PUBLIC.json').exists())

class TLSAndWrites(unittest.TestCase):
 def test_tls_identity_offline(self):
  import ssl
  class Context:
   verify_mode=ssl.CERT_REQUIRED;check_hostname=True
   def wrap_socket(self,raw,server_hostname):self.hostname=server_hostname;return raw
  c=Context();calls=[]
  conn=r.PinnedHTTPSConnection('https://original.synthetic.invalid','10.20.30.40',Path('/synthetic/ca'),connector=lambda addr,**kw:calls.append(addr) or object(),context_factory=lambda **kw:c,connect_port=8443)
  conn.connect();self.assertEqual(c.hostname,'original.synthetic.invalid');self.assertEqual(conn.host,'original.synthetic.invalid');self.assertEqual(calls,[('10.20.30.40',8443)])
 def test_unsafe_origin_and_verification(self):
  for origin in ('http://synthetic.invalid','https://user:pass@synthetic.invalid','https://synthetic.invalid/path'):
   with self.assertRaises(ValueError):r.PinnedHTTPSConnection(origin,'10.0.0.2',Path('synthetic'))
 def test_unapproved_write_prevented(self):
  class Connection:
   def __init__(self,*args,**kw):pass
   def connect(self):pass
   def request(self,*args,**kw):raise AssertionError('must reject before transport')
  api=r.PinnedAPI('https://synthetic.invalid','10.0.0.2',Path('synthetic'),connection_type=Connection)
  for path,body in [('/projects/1/tasks/1/transitions',{'action':2}),('/projects/1/tasks/1',{'state':2})]:
   with self.assertRaises(ValueError):api.request(path,'synthetic',body,idempotency_key='synthetic')

if __name__=='__main__':unittest.main(verbosity=2)
