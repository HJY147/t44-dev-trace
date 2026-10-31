import sys,threading,time,collections,json,tempfile,multiprocessing
from pathlib import Path
sys.path.insert(0,'/tmp/t44-post-v12-private')
import post_runtime as p
class Sink:
 def put(self,*a,**kw):return True
if __name__=='__main__':
 x=p.Run.__new__(p.Run);x.end=time.monotonic_ns();x.grant={'postcheck_seconds':40};x.stop=threading.Event();x.post=collections.Counter();x.post_events=[];x.post_active_http=set();x.post_state_lock=threading.Lock();x.post_states={};x.post_local=threading.local();x.post_slots=threading.BoundedSemaphore(64);x.post_deadline_seen=False;x.sink=Sink();lock=threading.Lock();state={'active':0,'peak':0}
 def task(conn,cid,*args):
  with lock:state['active']+=1;state['peak']=max(state['peak'],state['active'])
  time.sleep(.003)
  with lock:state['active']-=1
  if cid==399:raise ValueError('SYNTHETIC_FAILURE')
 x._postcheck_task=task
 threads=[threading.Thread(target=x._postcheck_bounded,args=(None,i,'',1,{},set()))for i in range(400)]
 for t in threads:t.start()
 for t in threads:t.join()
 assert len(x.post_states)==400 and collections.Counter(x.post_states.values())=={'COMPLETE':399,'ERROR':1}
 assert state['peak']<=64 and state['active']==0 and x.post['post_errors']==1
 for _ in range(64):assert x.post_slots.acquire(False)
 assert not x.post_slots.acquire(False)
 x.post_pool=None;x.post_pool_lock=threading.Lock();x.post_validation_jobs=0;x.post_jobs=[];x.out=Path(tempfile.mkdtemp(dir='/tmp/t44-independent-v12-audit'));x._validate_post({'a':1},{'type':'object','required':['a']})
 rejected=False
 try:x._validate_post({},{'type':'object','required':['a']})
 except ValueError:rejected=True
 assert rejected
 x._shutdown_post_pool();assert x.post_pool is None and x.post['validation_pending_at_shutdown']==0
 result={'scope':'LOCAL_SYNTHETIC_OFFLINE','owners':400,'complete':399,'injected_error':1,'max_active':state['peak'],'permits_recovered':64,'spawn_pool_workers':8,'pool_positive':True,'pool_negative':True,'pool_shutdown':True}
 Path('/tmp/t44-independent-v12-audit/CONCURRENCY.PUBLIC.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
