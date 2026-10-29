"""Finite resource closure and original APP stop; no QA access or cloud billing claim."""
import argparse,datetime as dt,hashlib,json,os,stat,subprocess,time
from pathlib import Path
B=Path('/root/t44-r9');A=B/'r29-resource-app-01';L=B/'r29-resource-mirror-01';PH=B/'campaign-r29-01/p'
APP_SHA='2c6e0158b51e963a6d8245f93dff2bd95e6d5be3ac0b5c00faa0155c479298e5'
HELPER_SHA='475c534dca91e9eeff9c64320d4b0d1a458faf6418ecc4efd408e9f56fdb3c92'
GEN=B/'r29-code-01/profile/generation.py';GEN_SHA='95802bf9e2a0d263bc00e1f2e5f046c553e29037e3c100eefebf09e81a95acc3'
STOP=dt.datetime.fromisoformat('2026-10-29T04:56:19.801+00:00').timestamp()
def need(ok,code):
 if not ok:raise ValueError(code)
def read(path,cap=100000):
 need(path.is_absolute() and path.resolve()==path,'CANONICAL_FILE')
 with os.fdopen(os.open(path,os.O_RDONLY|os.O_NOFOLLOW),'rb') as f:
  s=os.fstat(f.fileno());need(stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<=cap,'BOUNDED_REGULAR_FILE');raw=f.read(cap+1)
 need(len(raw)==s.st_size,'COMPLETE_FILE');return raw
def sha(path):return hashlib.sha256(read(path)).hexdigest()
def obj(path):return json.loads(read(path))
def digest(path):
 if not path.exists():return {'bytes':None,'sha256':None,'missing':True}
 need(path.resolve()==path,'CANONICAL_RAW');h=hashlib.sha256()
 with os.fdopen(os.open(path,os.O_RDONLY|os.O_NOFOLLOW),'rb') as f:
  a=os.fstat(f.fileno());need(stat.S_ISREG(a.st_mode) and a.st_nlink==1 and a.st_size<=536870912,'RAW_CAP')
  for chunk in iter(lambda:f.read(1048576),b''):h.update(chunk)
  z=os.fstat(f.fileno())
 need((a.st_size,a.st_mtime_ns)==(z.st_size,z.st_mtime_ns),'STABLE_RAW_PREFIX');return {'bytes':z.st_size,'sha256':h.hexdigest(),'missing':False}
def save(path,value):
 raw=value if isinstance(value,bytes) else (json.dumps(value,sort_keys=True)+'\n').encode()
 with os.fdopen(os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600),'wb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
def emit(value):print(json.dumps(value,sort_keys=True),flush=True)
def command(d,label,argv,cap=20):
 save(d/(label+'.command.PUBLIC.json'),{'argv':list(map(str,argv)),'retry':False})
 try:r=subprocess.run(list(map(str,argv)),capture_output=True,timeout=min(cap,max(1,STOP-time.time()-45)))
 except subprocess.TimeoutExpired as e:
  save(d/(label+'.stdout.PUBLIC.json'),e.stdout or b'');save(d/(label+'.stderr.private'),e.stderr or b'');save(d/(label+'.exit.PUBLIC.json'),{'returncode':None,'timed_out':True});raise
 save(d/(label+'.stdout.PUBLIC.json'),r.stdout);save(d/(label+'.stderr.private'),r.stderr)
 save(d/(label+'.exit.PUBLIC.json'),{'returncode':r.returncode,'stdout_sha256':hashlib.sha256(r.stdout).hexdigest(),'stderr_sha256':hashlib.sha256(r.stderr).hexdigest()})
 need(r.returncode==0,'ORIGINAL_COMMAND_FAILED_'+label);return r.stdout

def binding(directory,pin):
 need(sha(directory/'binding.json')==pin and sha(directory/'controller.py')==HELPER_SHA,'RESOURCE_CODE_PIN')
 return obj(directory/'binding.json')
def resource(d,directory,pin,action,label):
 binding(directory,pin)
 raw=command(d,label,['python3','-B',directory/'controller.py',action,'--directory',directory,'--binding-sha256',pin],35)
 row=json.loads(raw);need(row.get('action')==action and row['unit']==obj(directory/'binding.json')['unit'],'ACTUAL_CONTROL_SCHEMA');return row

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['app-seal','load-status','load-stop','app-stop']);p.add_argument('--root-qa-finished',action='store_true');p.add_argument('--app-raw-bytes',type=int);p.add_argument('--app-raw-sha256');a=p.parse_args();os.umask(0o077)
 need(os.geteuid()==0 and B.resolve()==B,'ROOT_OWNED_BASE');side='APP' if a.action.startswith('app') else 'LOAD';d=B/('r29-closure-'+side+'-01');d.mkdir(mode=0o700,exist_ok=True);need(d.resolve()==d,'CANONICAL_RECORDS')
 receipt=d/(a.action+'.receipt.PUBLIC.json');need(not receipt.exists(),'ONE_CLOSURE_ACTION_ONLY')
 v={'action':a.action,'utc':dt.datetime.now(dt.timezone.utc).isoformat(),'cloud_billing_stopped':None,'QA_data_or_unit_accessed':False,'raw_or_volume_deleted':False}
 if a.action=='app-seal':
  need(a.root_qa_finished,'ROOT_MUST_OBSERVE_QA_FINISHED');v['control']=resource(d,A,APP_SHA,'seal','01-app-seal')
  end=min(time.time()+10,STOP-60)
  while not (A/'sealed.json').exists() and time.time()<end:time.sleep(.2)
  sealed=obj(A/'sealed.json') if (A/'sealed.json').exists() else None;v['sealed']=sealed
  v['raw']=digest(A/'raw.jsonl') if sealed is not None else {'bytes':None,'sha256':None,'missing':True}
  v['complete_sealed_bytes_match']=sealed is not None and v['raw']['bytes']==sealed['raw_bytes'] and v['raw']['sha256']==sealed['raw_sha256']
 elif a.action in ('load-status','load-stop'):
  own=obj(B/'r29-ops-load-01/resource-ready.PUBLIC.json');pin=own['mirror_binding_sha256'];need(pin.startswith('9d3699') and own['resource_binding_sha256']==APP_SHA,'LOAD_SCOPE');v['binding_sha256']=pin
  v['status_before']=resource(d,L,pin,'status','02-'+a.action+'-status')
  if a.action=='load-stop':
   need(a.root_qa_finished,'ROOT_MUST_OBSERVE_QA_FINISHED');end=min(time.time()+20,STOP-90)
   while not (L/'mirror-final.json').exists() and time.time()<end:time.sleep(.2)
   before=obj(L/'mirror-final.json') if (L/'mirror-final.json').exists() else None
   v['expected_APP_raw']={'bytes':a.app_raw_bytes,'sha256':a.app_raw_sha256};v['mirror_final_before']=before
   v['raw_before_stop']=digest(L/'app-raw.jsonl') if before is not None else {'bytes':None,'sha256':None,'missing':True}
   v['tail_complete_before_stop']=v['raw_before_stop']['bytes']==a.app_raw_bytes and v['raw_before_stop']['sha256']==a.app_raw_sha256 and before is not None and before.get('transport_complete') is True and a.app_raw_bytes is not None and a.app_raw_sha256 is not None and before['raw_bytes']==a.app_raw_bytes and before['raw_sha256']==a.app_raw_sha256
   v['missing_before_stop']=[] if v['tail_complete_before_stop'] else ['APP_tail_missing; preserve_prefix_and_stop']
   emit({'kind':'RESOURCE_TAIL_BEFORE_STOP',**v})
   v['stop']=resource(d,L,pin,'stop','03-load-mirror-stop')
  v['mirror_final']=obj(L/'mirror-final.json') if (L/'mirror-final.json').exists() else None
  v['raw']=digest(L/'app-raw.jsonl') if v['mirror_final'] is not None or a.action=='load-stop' else {'bytes':None,'sha256':None,'missing':None}
  final=v['mirror_final'];v['complete_exact_APP_tail']=final is not None and final.get('transport_complete') is True and a.app_raw_bytes is not None and a.app_raw_sha256 is not None and v['raw']['bytes']==final['raw_bytes']==a.app_raw_bytes and v['raw']['sha256']==final['raw_sha256']==a.app_raw_sha256
 else:
  need(a.root_qa_finished,'ROOT_MUST_OBSERVE_QA_FINISHED');prep=obj(B/'r29-app-prep-01/complete.PUBLIC.json');pin=prep['binding_sha256'];need(pin.startswith('66372') and sha(PH/'binding.json')==pin and sha(GEN)==GEN_SHA,'APP_GEN_PIN');b=obj(PH/'binding.json');v['phase_binding_sha256']=pin
  v['GEN_stop']=command(d,'04-GEN-stop',['python3','-B',GEN,'stop','--phase-dir',PH,'--binding-sha256',pin],110).decode()
  v['resource_stop']=resource(d,A,APP_SHA,'stop','05-app-resource-stop')
  rows=command(d,'06-owned-compose-ps',['docker','--context','default','ps','--all','--filter','label=com.docker.compose.project='+b['project'],'--format','{{json .}}'])
  v['owned_compose_containers']=[json.loads(x) for x in rows.splitlines() if x.strip()]
  v['owned_compose_still_running']=[r for r in v['owned_compose_containers'] if r.get('State')=='running']
 v['cost_seconds_remaining']=STOP-time.time();save(receipt,v);emit({'kind':'RESOURCE_CLOSURE_RECEIPT','receipt':str(receipt),'receipt_sha256':sha(receipt),**v})
if __name__=='__main__':
 try:main()
 except Exception as e:emit({'kind':'CLOSURE_FAILED_OR_INCOMPLETE_KEEP_PREFIX','error_type':type(e).__name__,'reason':str(e),'cloud_billing_stopped':None,'raw_or_volume_deleted':False});raise SystemExit(1) from None
