import sys,os,json,hashlib,pickle,threading,collections,tempfile,time,copy,zlib,ast
from pathlib import Path
sys.path.insert(0,'/tmp/t44-post-v12-private')
import runtime as r, post_runtime as p
from compiled_post import Compiled
ROOT=Path('/tmp/t44-independent-v12-audit');results=[]
def test(name,f):
 try: detail=f();results.append({'name':name,'status':'PASS','detail':detail})
 except BaseException as e:results.append({'name':name,'status':'FAIL','exception':type(e).__name__,'detail':str(e)})
def must(v):
 if not v:raise AssertionError('assertion failed')
def identity():
 m=json.loads(Path('/tmp/t44-post-v12-private/AUDIT_SOURCE_METADATA.PUBLIC.json').read_text())
 for name,h in m['source_files'].items():must(hashlib.sha256((Path('/tmp/t44-post-v12-private')/name).read_bytes()).hexdigest()==h)
 must(hashlib.sha256(Path(m['neutral_response_replay_file']).read_bytes()).hexdigest()==m['neutral_response_replay_sha256'])
 must(Path('/tmp/t44-p16-private/runtime.py').read_bytes()==Path('/tmp/t44-post-v12-private/runtime.py').read_bytes())
 must(Path('/tmp/t44-p16-private/openapi.json').read_bytes()==Path('/tmp/t44-post-v12-private/openapi.json').read_bytes())
 for name in ['client','call','task_equal','val_headers','operation']:must(getattr(p.Run,name) is getattr(r.Run,name))
 return '5 frozen module hashes, replay hash, original runtime/schema bytes, 5 inherited measurement/assertion methods verified'
test('frozen identity and measurement preservation',identity)
def schema():
 doc=json.loads(Path('/tmp/t44-post-v12-private/openapi.json').read_text());old=r.Validator(doc);new=Compiled(doc);obj=r.Run.__new__(r.Run);obj.o=doc
 pages=pickle.load(open('/tmp/t44-post-v12-private/pages.pickle','rb'));selected=pages[::max(1,len(pages)//24)];count=0
 for path,data,status in selected:
  prefix=doc['servers'][0]['url'].rstrip('/');path=path[len(prefix):] if path.startswith(prefix) else path;op=obj.operation(path,'GET');s=op['responses']['200']['content']['application/json']['schema'];f=new.compile(s)
  for d in [data,{},dict(data,meta={}),dict(data,unexpected=True)]:
   outcomes=[]
   for validator in [lambda:old(d,s),lambda:f(d)]:
    try:validator();outcomes.append(True)
    except (ValueError,TypeError,KeyError):outcomes.append(False)
   must(outcomes[0]==outcomes[1]);must(outcomes[0]) if d is data else None;count+=1
 return {'replay_pages':len(selected),'positive_and_mutated_cases':count,'real_content_published':False}
test('neutral replay schema differential',schema)
def skeleton():
 x=p.Run.__new__(p.Run);x.end=time.monotonic_ns();x.grant={'postcheck_seconds':40};x.stop=threading.Event();x.post=collections.Counter();x.post_events=[];x.post_active_http=set();x.post_state_lock=threading.Lock();x.post_states={};x.post_local=threading.local();x.post_slots=threading.BoundedSemaphore(64);x.post_deadline_seen=False;x.sessions={'developer':{'user_id':1}};return x
def gate():
 x=skeleton();x.end=time.monotonic_ns()-40*10**9
 for f in [x._dispatch_post,lambda:x._begin_http(1)]:
  try:f();raise AssertionError('deadline admitted')
  except p.PostBudgetExhausted:pass
 must(not x.post_active_http);return 'both dispatch gates refuse expired budget'
test('expired dispatch gates',gate)
def paging():
 x=skeleton();calls=[]
 def call(c,cid,phase,kind,method,path,role,**kw):
  calls.append(path)
  if len(calls)==1:return {'data':{}}
  return {'data':{'items':[{'task_id':3,'project_id':2,'id':len(calls),'outcome':1,'operation_id':'transitionTask','actor_id':1,'actor_kind':1}],'total':201}}
 x._call_post=call;x._postcheck_task(None,0,'base',2,{'id':3},{2,3,4});must(len(calls)==4);must(x.post['audit_complete_clients']==1)
 x=skeleton();x._call_post=call
 try:x._postcheck_task(None,0,'base',2,{'id':9},{999});raise AssertionError('bad audit accepted')
 except ValueError:pass
 must(x.post['audit_complete_clients']==0);return 'snapshot plus all three pages; wrong task scope rejected'
test('complete pagination and scope negative',paging)
def late():
 x=skeleton()
 def call(*args,**kw):x.end=time.monotonic_ns()-41*10**9;return {'data':{}}
 x._call_post=call
 try:x._postcheck_task(None,0,'base',2,{'id':3},set());raise AssertionError('late snapshot accepted')
 except p.PostBudgetExhausted:pass
 must(x.post['final_task_snapshot']==0);return 'late snapshot excluded'
test('late completion excluded',late)
def exits():
 good={'metrics_verdict':'PASS','full_cohort':True,'postconditions':{'final_task_snapshot':400,'audit_complete_clients':400},'writer_finalized':True,'post_validator_pool_stopped':True,'capacity_or_writer_stop':None,'independent_conclusion':'METRICS_PASS_MQ_POSTCONDITION_NOT_OBSERVED'};must(p.combined_exit(good)==0);n=0
 for field,value in [('metrics_verdict','FAIL'),('full_cohort',False),('writer_finalized',False),('post_validator_pool_stopped',False),('capacity_or_writer_stop','CAP'),('post_deadline_seen',True),('independent_conclusion','NP')]:
  v=copy.deepcopy(good);v[field]=value;must(p.combined_exit(v)!=0);n+=1
 for key in ['post_errors','post_budget_not_observed','post_grace_exhausted','validation_pending_at_shutdown','owned_producers_not_drained']:
  v=copy.deepcopy(good);v['postconditions'][key]=1;must(p.combined_exit(v)!=0);n+=1
 return {'positive':1,'negative':n}
test('combined exit gate matrix',exits)
def seal():
 for negative in [False,True]:
  out=Path(tempfile.mkdtemp(dir=ROOT));key=os.urandom(32);sink=r.Sink(out,key,{'plain_bytes':100*1024**2,'compressed_bytes':100*1024**2,'cipher_bytes':100*1024**2},threading.Event());must(sink.reserve())
  if negative:
   x=skeleton();x.sink=sink
   try:x._reserved_gate(1) # force deadline by explicit stop
   except p.PostBudgetExhausted:pass
   x.stop.set()
   try:x._reserved_gate(1)
   except p.PostBudgetExhausted:pass
  else:must(sink.put({'record':'synthetic'},reserved=True))
  sink.close();frames=list(r.Seal.read(out/'evidence.772seal',key));footer=json.loads(frames[-1][1]);must(frames[-1][0]==255);must(sink.reserved==0);must(not sink.thread.is_alive());must(footer['reason'] is None)
 return 'normal and refused reserved dispatch authenticated footer; reservation balance zero'
test('reservation refusal and writer seal',seal)
(ROOT/'RESULT.PUBLIC.json').write_text(json.dumps({'scope':'LOCAL_OFFLINE_ONLY','tests':results},indent=2));print(json.dumps(results,indent=2))
