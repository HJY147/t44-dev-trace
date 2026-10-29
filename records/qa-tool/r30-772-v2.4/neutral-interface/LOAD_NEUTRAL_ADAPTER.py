#!/usr/bin/env python3
"""Public neutral-input/authorization adapter. No benchmark cases/assertions."""
import argparse,datetime,hashlib,json,os,platform,re,ssl,sys,time
from pathlib import Path
os.umask(0o077)
BASE=Path('/private');PUBLIC=BASE/'public';EXPECTED_LOAD_IMAGE='sha256:4f3baf081863a4580b5608699d9a7a8af2d89c3e87abbb60089b630b9102b2a1'
FROZEN_RUNTIME_SHA='745f4d8b369729fab59a59bfbba17f0baace8541d7b627a43bbe117c09dea085'
SUT_GIT='f7cdb5fa3b19f84d8ab0d0b042bf51a5b8484e8f'
SUT_SOURCE_MANIFEST='3368534aececbb5441225e7859338aa3079b6e41798e38673bd8f337f8993577'
SUT_SOURCE_PROOF='b208b86abe657570b3125944274e45f1ecd806537985bea1c34b7deea8e5d5d6'
SUT_IMAGE='sha256:a7d3dde54efda1405bbd7d9f5f5b7c5a6439f1afd1dc8c50b2ed8b37625fa5da'
OPENAPI_SHA='6f07cb53a7d9314240ba93ec490325d3c63dca7e4d077021047e216e7b26f478'
class NeutralFailure(Exception):pass
def need(ok,code):
 if not ok:raise NeutralFailure(code)
def utc(t=None):return datetime.datetime.fromtimestamp(time.time() if t is None else t,datetime.timezone.utc).isoformat().replace('+00:00','Z')
def epoch(value):
 d=datetime.datetime.fromisoformat(value.replace('Z','+00:00'));need(d.tzinfo is not None and d.utcoffset()==datetime.timedelta(0),'UTC_REQUIRED');return d.timestamp()
def rawjson(path):
 p=Path(path);need(p.is_file() and p.stat().st_size<=16*1024*1024,'NEUTRAL_FILE_BOUND');return json.loads(p.read_bytes())
def encoded(value):return json.dumps(value,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode()+b'\n'
def write_new(path,value):
 p=Path(path);fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
 with os.fdopen(fd,'wb') as f:f.write(value if isinstance(value,bytes) else encoded(value))
def public_report(name,value):
 PUBLIC.mkdir(parents=True,exist_ok=True,mode=0o700);tmp=PUBLIC/(name+'.new');tmp.write_bytes(encoded(value));tmp.chmod(0o600);os.replace(tmp,PUBLIC/name);print(json.dumps(value,separators=(',',':')),flush=True)
def capabilities():
 cg={}
 for n in ('cpu.max','memory.max','pids.max'):
  p=Path('/sys/fs/cgroup')/n;cg[n]=p.read_text().strip() if p.is_file() else None
 ok=sys.version_info[:2]==(3,12) and platform.system()=='Linux' and platform.machine() in ('x86_64','amd64')
 try:
  quota,period=cg['cpu.max'].split();ok=ok and quota!='max' and int(quota)/int(period)<=8 and cg['memory.max']!='max' and int(cg['memory.max'])<=8*1024**3 and cg['pids.max']!='max' and int(cg['pids.max'])<=2048
 except (AttributeError,ValueError,TypeError):ok=False
 value={'schema':'772-public-linux-capabilities-v1','status':'PASS' if ok else 'NP','observed_utc':utc(),'python':sys.version,'platform':platform.system(),'architecture':platform.machine(),'ssl':ssl.OPENSSL_VERSION,'cpu_count':os.cpu_count(),'cgroup':cg,'monotonic_seconds':time.monotonic(),'expected_load_python_image_id':EXPECTED_LOAD_IMAGE,'sut_requests':0,'private_input_reads':0,'benchmark_preflight':'NOT_RUN','scope':'PUBLIC_PLATFORM_CHECK_ONLY'};public_report('linux-capabilities.json',value);need(ok,'LINUX_AMD64_PYTHON312_CGROUP_REQUIRED');return value
def window(cost_stop):
 start=time.time();end=min(start+900,epoch(cost_stop)-90);need(end-start>=780,'INSUFFICIENT_FULL_WINDOW_BEFORE_COST_STOP');return start,end
def load_packet(packet,origin_override=None):
 p=Path(packet);extras={}
 if p.is_dir() and (p/'inputs/session.private.json').is_file():
  v=rawjson(p/'inputs/session.private.json');ca=(p/'inputs/ca.pem').read_text()
 elif p.is_dir():
  env=rawjson(p/'environment.json');env['origin']=origin_override or env['origin'];return env,rawjson(p/'sessions.json'),rawjson(p/'inventory.json'),(p/'ca.pem').read_text(),extras
 else:v=rawjson(p);ca=v.get('ca_pem')
 schema=v.get('schema',v.get('kind'))
 if schema=='NEUTRAL_772_INPUTS_V1':
  need(v['source_sha']==SUT_GIT,'NEUTRAL_GIT_IDENTITY_MISMATCH');additional=v.get('additional_neutral_snapshots',{});candidate=v.get('environment',{});origin=origin_override or candidate.get('origin') or v.get('origin')
  if not origin and isinstance(additional,dict):origin=additional.get('origin')
  need(isinstance(origin,str),'EXPLICIT_NEUTRAL_HTTPS_ORIGIN_REQUIRED');identity={'source_sha256':SUT_SOURCE_MANIFEST,'source_git_commit':SUT_GIT,'source_files_proof_sha256':SUT_SOURCE_PROOF,'image_digest':SUT_IMAGE,'fixture_sha256':v['fixture_sha256'],'neutral_binding_sha256':v['binding_sha256'],'openapi_sha256':OPENAPI_SHA};env={'origin':origin,'connect_ip':'172.21.182.245','identity':identity,'declared_fixture_counts':v['counts']};extras={'additional_neutral_snapshots':additional,'counts':v['counts'],'source_sha':v['source_sha'],'binding_sha256':v['binding_sha256'],'input_schema':schema};inventory=v['inventory']
  if isinstance(inventory,dict) and 'schema' not in inventory:inventory=dict(inventory,schema='772-inventory-v1')
  return env,v['sessions'],inventory,ca,extras
 need(schema=='772-neutral-v1','NEUTRAL_PACKET_SCHEMA');env=v['environment'];env['origin']=origin_override or env['origin'];return env,v['sessions'],v['inventory'],ca,extras
def validate_neutral(env,sessions,inventory,end):
 need(set(sessions)=={'manager','developer','reviewer','service'},'FOUR_SESSION_ROLES_REQUIRED')
 expiries={}
 for role,v in sessions.items():
  need(isinstance(v['token'],str) and len(v['token'])>=16,'REAL_SESSION_TOKEN_REQUIRED');need(epoch(v['expires_at'])>end,'ACTUAL_SESSION_EXPIRES_BEFORE_NEW_WINDOW_END');need(type(v['user_id']) is int and v['user_id']>0 and isinstance(v['project_ids'],list) and isinstance(v['scopes'],list),'SESSION_METADATA_REQUIRED');expiries[role]=v['expires_at']
 need('escalation:write' in sessions['service']['scopes'],'SERVICE_SCOPE_REQUIRED');need(inventory.get('schema')=='772-inventory-v1' and len(inventory['clients'])==400,'NEUTRAL_INVENTORY_400_REQUIRED');items=inventory['clients'];need({x['client_id'] for x in items}==set(range(400)),'CLIENT_IDS_REQUIRED');ids=[x[k]['id'] for x in items for k in ('transition_task','escalation_task')];need(len(set(ids))==800,'DISTINCT_800_TASKS_REQUIRED');projects={x['project_id'] for x in items};need(len(projects)>=35,'PROJECT_SPREAD_REQUIRED')
 for x in items:
  need(all(k in x for k in ('project_manager_ids','escalation_event')),'NEUTRAL_EVENT_MEMBERSHIP_SNAPSHOT_REQUIRED')
  for role in sessions:need(x['project_id'] in sessions[role]['project_ids'],'SESSION_PROJECT_SCOPE_REQUIRED')
 identity=env['identity']
 for k in ('source_sha256','fixture_sha256'):need(re.fullmatch('[0-9a-f]{64}',identity[k]) is not None,'IMMUTABLE_SHA256_REQUIRED')
 need(re.fullmatch('sha256:[0-9a-f]{64}',identity['image_digest']) is not None,'SUT_IMAGE_DIGEST_REQUIRED');need(identity['openapi_sha256']==OPENAPI_SHA,'FROZEN_OPENAPI_IDENTITY_REQUIRED');need(env['origin'].startswith('https://'),'HTTPS_ORIGIN_REQUIRED')
 return {'sessions':4,'inventory_entries':400,'distinct_task_ids':800,'projects':len(projects),'actual_session_expires_at':expiries,'sut_identity':identity}
def prepare(args):
 capabilities();start,end=window(args.cost_stop);env,sessions,inventory,ca,extras=load_packet(args.neutral_opened_dir or args.packet,args.origin);summary=validate_neutral(env,sessions,inventory,end);need(isinstance(ca,str) and 'BEGIN CERTIFICATE' in ca,'TRUSTED_CA_PEM_REQUIRED');work=BASE/'authorization'/args.run_id;work.parent.mkdir(mode=0o700,parents=True,exist_ok=True);need(not work.exists(),'PREPARATION_DIRECTORY_ALREADY_EXISTS');work.mkdir(mode=0o700)
 write_new(work/'neutral-extra.json',extras);write_new(work/'sessions.json',sessions);write_new(work/'inventory.json',inventory);write_new(work/'ca.pem',ca.encode());output=BASE/'results'/args.run_id;output.parent.mkdir(mode=0o700,parents=True,exist_ok=True);need(not output.exists(),'RUN_OUTPUT_ALREADY_EXISTS')
 environment={'schema':'772-env-v1','run_id':args.run_id,'created_at':utc(),'origin':env['origin'],'connect_ip':env['connect_ip'],'ca_file':str(work/'ca.pem'),'sessions_file':str(work/'sessions.json'),'inventory_file':str(work/'inventory.json'),'output_dir':str(output),'grant_file':str(work/'grant.json'),'identity':env['identity'],'declared_fixture_counts':env.get('declared_fixture_counts')};write_new(work/'environment.json',environment);write_new(work/'grant.default-false.json',{'schema':'772-grant-v1','allow':False,'run_id':args.run_id,'created_at':utc(),'reason':'PENDING_EXPLICIT_ONE_TIME_AUTHORIZATION'});write_new(work/'adapter.json',{'cost_stop_utc':args.cost_stop,'prepared_at':utc()})
 public_report('neutral-preparation.json',{'schema':'772-neutral-preparation-v1','status':'READY_PENDING_GRANT','run_id':args.run_id,'observed_utc':utc(),'prospective_window_end_utc':utc(end),'cost_stop_utc':args.cost_stop,'default_grant_allow':False,'sut_requests':0,'private_source_read':False,'summary':summary})
def execute(args):
 need(args.authorize_once==args.run_id,'EXPLICIT_ONE_TIME_RUN_AUTHORIZATION_REQUIRED');capabilities();work=BASE/'authorization'/args.run_id;adapter=rawjson(work/'adapter.json');need(adapter['cost_stop_utc']==args.cost_stop,'IMMUTABLE_COST_STOP_REQUIRED');env=rawjson(work/'environment.json');sessions=rawjson(work/'sessions.json');inventory=rawjson(work/'inventory.json');start,end=window(args.cost_stop);summary=validate_neutral(env,sessions,inventory,end);need(not (work/'grant.json').exists() and not (work/'grant.consumed').exists(),'ONE_TIME_GRANT_ALREADY_EXISTS');manifest={'benchmark':'772-v1','runtime_sha256':FROZEN_RUNTIME_SHA}
 grant={'schema':'772-grant-v1','allow':True,'run_id':args.run_id,'created_at':utc(start),'window_start_utc':utc(start),'window_end_utc':utc(end),'origin':env['origin'],'environment_sha256':hashlib.sha256((work/'environment.json').read_bytes()).hexdigest(),'runtime_sha256':manifest['runtime_sha256'],'source_sha256':env['identity']['source_sha256'],'image_digest':env['identity']['image_digest'],'fixture_sha256':env['identity']['fixture_sha256'],'warmup_seconds':60,'steady_seconds':600,'clients':400,'request_timeout_seconds':15,'postcheck_seconds':40,'limits':{'cpu':8,'memory_bytes':8589934592,'pids':2048,'plain_bytes':10737418240,'compressed_bytes':11811160064,'cipher_bytes':12884901888},'permissions':['linux-preflight','one-cohort','read-postconditions'],'prohibitions':['cloud-control','install','login','session-extension','request-retry','restart','successor-run']};write_new(work/'grant.json',grant)
 public_report('launch-receipt.json',{'schema':'772-launch-receipt-v1','status':'EXPLICIT_SINGLE_GRANT_WRITTEN','run_id':args.run_id,'created_at':grant['created_at'],'window_start_utc':grant['window_start_utc'],'window_end_utc':grant['window_end_utc'],'window_seconds':end-start,'cost_stop_utc':args.cost_stop,'runtime_sha256':manifest['runtime_sha256'],'environment_sha256':grant['environment_sha256'],'sut_identity':env['identity'],'session_expiry_covers_new_window':True,'warmup_seconds':60,'steady_seconds':600,'clients':400,'postconditions':'SEPARATE_FROM_METRICS','runtime_preflight_and_cohort':'ABOUT_TO_EXECUTE_ONCE'})
 runtime=BASE/'runtime/runtime.py';need(runtime.is_file(),'PRIVATE_RUNTIME_INSTALL_REQUIRED');os.execv(sys.executable,[sys.executable,str(runtime),'run',str(work/'environment.json'),str(work/'grant.json')])
def main():
 ap=argparse.ArgumentParser();ap.add_argument('mode',choices=['capabilities','prepare','execute']);ap.add_argument('--packet');ap.add_argument('--neutral-opened-dir');ap.add_argument('--origin');ap.add_argument('--run-id');ap.add_argument('--authorize-once');ap.add_argument('--cost-stop',default='2026-10-29T04:56:19Z');args=ap.parse_args()
 try:
  if args.mode=='capabilities':capabilities();return
  need(args.run_id is not None and re.fullmatch('[A-Za-z0-9][A-Za-z0-9_-]{0,63}',args.run_id) is not None,'SAFE_NEW_RUN_ID_REQUIRED')
  if args.mode=='prepare':need(args.packet is not None or args.neutral_opened_dir is not None,'NEUTRAL_PACKET_PATH_REQUIRED');prepare(args)
  else:execute(args)
 except NeutralFailure as exc:public_report('adapter-stop.json',{'schema':'772-adapter-stop-v1','status':'NP','reason':str(exc),'mode':args.mode,'run_id':args.run_id,'observed_utc':utc(),'sut_request_by_adapter':0});raise SystemExit(2)
 except Exception as exc:public_report('adapter-stop.json',{'schema':'772-adapter-stop-v1','status':'NP','reason':'NEUTRAL_ADAPTER_INPUT_OR_IO_FAILURE','exception_type':type(exc).__name__,'mode':args.mode,'run_id':args.run_id,'observed_utc':utc(),'sut_request_by_adapter':0});raise SystemExit(2)
if __name__=='__main__':main()
