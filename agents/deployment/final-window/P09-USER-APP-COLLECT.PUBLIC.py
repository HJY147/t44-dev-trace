"""User-run read-only collector: emit early public material, wait boundedly for new bootstrap, never QA."""
import argparse,base64,datetime,hashlib,json,subprocess,time,zlib
from pathlib import Path
R=Path('/root/t44-final-20261029');F=R/'P09';PROJECT='t44-cloud-r30finalp09-p'
PUBLIC=['preparation.PUBLIC.json','timeplan.PUBLIC.json','backend-import-receipt.PUBLIC.json','LOAD-bootstrap.original.PUBLIC.json']
FMT='{"id":{{json .Id}},"image_id":{{json .Image}},"name":{{json .Name}},"project":{{json (index .Config.Labels "com.docker.compose.project")}},"role":{{json (index .Config.Labels "com.docker.compose.service")}},"user":{{json .Config.User}},"running":{{json .State.Running}},"restart_count":{{json .RestartCount}},"OOMKilled":{{json .State.OOMKilled}},"limits":{"NanoCpus":{{json .HostConfig.NanoCpus}},"CpuQuota":{{json .HostConfig.CpuQuota}},"CpuPeriod":{{json .HostConfig.CpuPeriod}},"MemorySwap":{{json .HostConfig.MemorySwap}},"Memory":{{json .HostConfig.Memory}},"PidsLimit":{{json .HostConfig.PidsLimit}},"Ulimits":{{json .HostConfig.Ulimits}}}}'
def run(argv):
 p=subprocess.run(argv,check=False,capture_output=True,timeout=15);return p.stdout if p.returncode==0 else b''
def safe(v):
 if isinstance(v,dict):
  if {'token','access_token','password','private_key','database_url'}&set(v):raise ValueError('CREDENTIAL_BEARING_NEUTRAL_OBJECT_REFUSED')
  for x in v.values():safe(x)
 elif isinstance(v,list):
  for x in v:safe(x)
def read(p):
 if p.is_symlink()or p.stat().st_size>8000000:raise ValueError('BOUNDED_PUBLIC_OR_OWN_NEUTRAL_FACTS_REQUIRED')
 raw=p.read_bytes();return raw,json.loads(raw)
def snapshot(event):
 result={'kind':'USER_P09_PUBLIC_COLLECTOR','event':event,'observed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'files':{},'containers':[],'other_running_T44_projects':[],'DB_readback_records':{},'scope':{'status':'PENDING'},'QA_or_SUT_requests':0,'credentials_or_PRIVATE_cases_read':False,'state_changed':False}
 for name in PUBLIC:
  p=F/name
  if not p.is_file():result['files'][name]={'status':'PENDING_NOT_PRESENT'};continue
  try:raw,v=read(p)
  except (ValueError,OSError):
   result['files'][name]={'status':'PENDING_INCOMPLETE_OR_INVALID_JSON'};continue
  result['files'][name]={'status':'PRESENT','bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'zlib_b64':base64.b64encode(zlib.compress(raw,9)).decode()}
  if name=='timeplan.PUBLIC.json':result['clock']={k:v.get(k)for k in ['run_id','t0_utc','start_utc','end_utc','stop_utc','cost_stop_utc','packet_cutoff_utc','absolute_cost_cutoff_utc']}
  if name=='preparation.PUBLIC.json':result['phase_status']=v.get('status')
 unit=run(['systemctl','show','t44-final-p09-continuous.service','--property=ActiveState,SubState,Result,ExecMainStatus'])
 result['unit']={x.split('=',1)[0]:x.split('=',1)[1]for x in unit.decode().splitlines()if '='in x}
 ids=run(['docker','--context','default','ps','--quiet','--filter','label=com.docker.compose.project'])
 for cid in ids.decode().split():
  raw=run(['docker','--context','default','inspect','--format',FMT,cid])
  if not raw:continue
  row=json.loads(raw);project=row.get('project')or''
  if project==PROJECT:result['containers'].append(row)
  elif project.startswith('t44'):result['other_running_T44_projects'].append({'id':row['id'],'project':project,'name':row['name']})
 expected={'mysql','rabbitmq','api','consumer','scheduler','web','tls-gateway'};result['seven_roles_running']=len(result['containers'])==7 and {x['role']for x in result['containers']}==expected and all(x['running']for x in result['containers'])
 result['external_writer_absence_proven']=False;result['writer_note']='Only APP T44 containers observed; root must separately review LOAD/client writer facts.'
 for label,rel in [('empty','P-empty-counts/output/result/counts.json'),('seeded','P-counts/output/result/counts.json'),('final','P-final-counts/output/result/counts.json')]:
  p=F/rel
  if p.is_file():
   raw,v=read(p);safe(v);result['DB_readback_records'][label]={'sha256':hashlib.sha256(raw).hexdigest(),**{k:v.get(k)for k in ['captured_at','run_id','namespace','database','actual_fixture_counts','raw_counts','project_ids','actual_fixture_sha256']}}
 p=F/'P-http/output/result/factual-snapshots.json'
 if p.is_file():
  raw,v=read(p);safe(v);result['scope']={'status':'ORIGINAL_OWN_NEUTRAL_FACTS','sha256':hashlib.sha256(raw).hexdigest(),'generated_complete_utc':v.get('generated_complete_utc'),'clients':len(v.get('inventory',{}).get('clients',[])),'sessions':{role:{k:x.get(k)for k in ['user_id','project_ids','scopes','expires_at','issued_at','login_request_started_at','response_observed_at']}for role,x in v.get('session_attestations',{}).items()}}
 return result
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--wait-seconds',type=int,default=600);a=p.parse_args()
 if not 0<=a.wait_seconds<=600:raise ValueError('WAIT_MAX600_REQUIRED')
 end=time.monotonic()+a.wait_seconds;early=False;complete_early=False
 while True:
  snap=snapshot('EARLY_PUBLIC_MATERIAL');valid=all(snap['files'][n].get('status')=='PRESENT'for n in PUBLIC[:3]);ready=all(snap['files'][n].get('status')=='PRESENT'for n in PUBLIC)
  if not early or (valid and not complete_early):
   print(json.dumps(snap,sort_keys=True),flush=True);early=True;complete_early=valid
  if ready:
   snap['event']='BOOTSTRAP_READY';clock=snap.get('clock')or{};start=clock.get('start_utc')
   if not start or datetime.datetime.fromisoformat(start.replace('Z','+00:00')).timestamp()-time.time()<=30:snap['event']='BOOTSTRAP_PRESENT_TOO_LATE_NO_OVERRIDE'
   print(json.dumps(snap,sort_keys=True),flush=True);return
  if snap.get('phase_status')=='FAILED_PREFIX_PRESERVED':
   snap['event']='PREPARATION_FAILED_PREFIX_PRESERVED';print(json.dumps(snap,sort_keys=True),flush=True);return
  if time.monotonic()>=end:
   snap['event']='WAIT_TIMEOUT_PENDING_NO_RETRY';print(json.dumps(snap,sort_keys=True),flush=True);return
  clock=snap.get('clock')or{};start=clock.get('start_utc')
  if start and datetime.datetime.fromisoformat(start.replace('Z','+00:00')).timestamp()-time.time()<=30:
   snap['event']='PREPARATION_MARGIN_EXPIRED_NO_OVERRIDE';print(json.dumps(snap,sort_keys=True),flush=True);return
  time.sleep(min(1,max(0,end-time.monotonic())))
if __name__=='__main__':main()
