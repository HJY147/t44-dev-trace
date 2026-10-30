from pathlib import Path
import copy,importlib.util,json,types
D=Path(__file__).resolve().parents[2]/'agents/deployment/manual-handoff';s=importlib.util.spec_from_file_location('resume',D/'resume_existing_p09.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);exp=m.expected();state={role:{**copy.deepcopy(row),'running':False,'health':'starting'}for role,row in exp.items()};calls=[];starts=[]
def run(argv,**kwargs):
 calls.append(argv)
 if argv[0]=='systemctl':return types.SimpleNamespace(returncode=3,stdout=b'')
 assert argv[:3]==['docker','--context','default'];action=argv[3]
 if action=='ps':return types.SimpleNamespace(returncode=0,stdout=('\n'.join(x['id']for x in state.values())).encode())
 if action=='inspect':return types.SimpleNamespace(returncode=0,stdout=('\n'.join(json.dumps(x)for x in state.values())).encode())
 assert action=='start'
 for cid in argv[4:]:
  role=next(r for r,x in exp.items()if x['id']==cid);starts.append(role);state[role].update(running=True,health='healthy')
 return types.SimpleNamespace(returncode=0,stdout=b'')
m.subprocess.run=run
r=m.resume('infra');assert starts==['mysql','rabbitmq','api','web','tls-gateway']and not state['consumer']['running']and not state['scheduler']['running']
before=len(starts)
try:m.resume('workers');raise AssertionError('unrefreshed workers accepted')
except ValueError:pass
assert len(starts)==before
m.resume('workers',ack=True);assert starts[-2:]==['consumer','scheduler'];assert all(x['running']for x in state.values())
before=len(starts);m.resume('workers',ack=True);assert len(starts)==before # already-running exact IDs are observed, not restarted
for key,value in [('project','t44-other-project'),('image_id','sha256:'+'0'*64),('id','f'*64),('limits',{})]:
 old=copy.deepcopy(state['api']);state['api'][key]=value;before=len(starts)
 try:m.resume('infra');raise AssertionError('identity mismatch accepted:'+key)
 except ValueError:pass
 assert len(starts)==before;state['api']=old
for argv in calls:
 if argv[0]=='docker':assert argv[3]in {'ps','inspect','start'}
assert '.Config.Env'not in m.FMT and '.Config.Cmd'not in m.FMT
print(json.dumps({'status':'LOCAL_CLI_SPY_RESUME_SEQUENCE_AND_NEGATIVES_PASSED','order':starts,'containers_expected':7,'rejected':['other project','wrong image','wrong ID','changed resources','workers before service/token acknowledgement'],'no_recreate_build_pull_seed_controller':True,'cloud_Docker_or_private_read_executed':False},sort_keys=True))
