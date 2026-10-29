#!/usr/bin/env python3
"""0b/v2.4 neutral adapter. No HTTP, cloud, login or benchmark case implementation."""
import argparse,datetime,hashlib,ipaddress,json,os,re,ssl,sys,time,urllib.parse
from pathlib import Path
os.umask(0o077)
TARGET={'git_commit':'0bffe0c535e5897890aebf30879fdd3839dc52d6','source_manifest_sha256':'0c5b0c0e027578b0f62711175beac4680aab8331bfbc4af2547f02398f38cc1b','backend_bundle_manifest_sha256':'b2db2e1c5cf56fa5df4f20f7003d44d6b3b9ab4cd484b45d921c82640295d345','sut_image_config_digest':'sha256:8e3e2a9d1f2d4706072eb0502b041d3db49d32b7a2fc48ac6b39fc2162336845','load_runtime_image_config_digest':'sha256:4f3baf081863a4580b5608699d9a7a8af2d89c3e87abbb60089b630b9102b2a1','runtime_sha256':'81e04666cf05c2932397c5d39521ef881602f3046342e2d4d5605a694e5829bf','openapi_sha256':'6f07cb53a7d9314240ba93ec490325d3c63dca7e4d077021047e216e7b26f478'}
LIMITS={'cpu':8,'memory_bytes':8589934592,'pids':2048,'plain_bytes':10737418240,'compressed_bytes':11811160064,'cipher_bytes':12884901888}
ROLES={'manager','developer','reviewer','service'}
class Stop(Exception):pass
def need(ok,code):
 if not ok:raise Stop(code)
def encoded(v):return json.dumps(v,ensure_ascii=False,separators=(',',':'),sort_keys=True,allow_nan=False).encode()+b'\n'
def sha(v):return hashlib.sha256(v).hexdigest()
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat().replace('+00:00','Z')
def epoch(v):
 need(isinstance(v,str),'UTC_REQUIRED');d=datetime.datetime.fromisoformat(v.replace('Z','+00:00'));need(d.tzinfo is not None and d.utcoffset()==datetime.timedelta(0),'UTC_REQUIRED');return d.timestamp()
def read(p,bound=16*1024*1024):
 p=Path(p);need(p.is_file() and p.stat().st_size<=bound,'INPUT_FILE_BOUND');return p.read_bytes()
def obj(p):return json.loads(read(p))
def write_new(p,value):
 p=Path(p);fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
 with os.fdopen(fd,'wb') as f:f.write(value if isinstance(value,bytes) else encoded(value));f.flush();os.fsync(f.fileno())
def safe_run_id(v):need(isinstance(v,str) and re.fullmatch('[A-Za-z0-9][A-Za-z0-9_-]{0,63}',v) is not None,'SAFE_NEW_RUN_ID_REQUIRED')
def sha_field(v):return isinstance(v,str) and re.fullmatch('[0-9a-f]{64}',v) is not None
def manifest_records(blob):
 """Only declared neutral metadata layouts. Unknown layout blocks, never guesses."""
 v=json.loads(blob)
 if isinstance(v,dict):v=v.get('files',v.get('source_files'))
 if isinstance(v,dict):v=[{'path':k,'sha256':h} for k,h in v.items()]
 need(isinstance(v,list) and len(v)==62,'SOURCE_MANIFEST_EXACT_62_CONTEXT_RECORDS_REQUIRED');out={}
 for row in v:
  path=row.get('path');h=row.get('sha256');need(isinstance(path,str) and path and not path.startswith('/') and '..' not in Path(path).parts and sha_field(h),'SOURCE_MANIFEST_RECORD_REQUIRED');need(path not in out,'DUPLICATE_SOURCE_PATH');out[path]=h
 return out

def validate(packet,files,run_id,now=None,execution=False):
 now=time.time() if now is None else now;safe_run_id(run_id)
 need(packet.get('schema')=='NEUTRAL_772_INPUTS_V2_0B_V24','NEW_NEUTRAL_SCHEMA_REQUIRED');need(packet['run_id']==run_id,'RUN_ID_BINDING')
 need(sha_field(packet['packet_nonce']),'NEW_PACKET_NONCE_REQUIRED');need(packet['binding_sha256']==sha(encoded({k:v for k,v in packet.items() if k!='binding_sha256'})),'NEUTRAL_BINDING_SHA256')
 created=epoch(packet['created_at']);need(now-300<=created<=now+5,'FRESH_PACKET_REQUIRED');window=packet['window'];start=epoch(window['start_utc']);end=epoch(window['end_utc']);cost=epoch(window['cost_stop_utc'])
 need(780<=end-start<=900 and end<=cost-90,'FINITE_WINDOW_BEFORE_COST_STOP');need(start>=created-20 and start<=created+600,'EXPLICIT_FRESH_START_REQUIRED')
 if execution:need(start<=now<start+20,'ACTUAL_START_WINDOW')
 else:need(now<start+20,'PREPARATION_START_WINDOW_ALREADY_PASSED')
 identity=packet['identity']
 for k,v in TARGET.items():need(identity.get(k)==v,'TARGET_'+k.upper())
 need(sha(files['source_manifest'])==TARGET['source_manifest_sha256'],'SOURCE_MANIFEST_BYTES');need(sha(files['backend_bundle_manifest'])==TARGET['backend_bundle_manifest_sha256'],'BACKEND_BUNDLE_MANIFEST_BYTES')
 expected=manifest_records(files['source_manifest']);proof=json.loads(files['backend_import_receipt']);need(proof.get('kind')=='r30-backend-import-receipt-v1','ACTUAL_IMPORT_RECEIPT_KIND')
 for key,target_key in [('source_sha','git_commit'),('bundle_manifest_sha256','backend_bundle_manifest_sha256'),('source_manifest_sha256','source_manifest_sha256')]:need(proof.get(key)==TARGET[target_key],'ACTUAL_IMPORT_RECEIPT_'+key.upper())
 need(type(proof.get('full_runtime_files')) is int and proof['full_runtime_files']==60,'ACTUAL_IMPORT_EXACT_60_FILES');need(proof.get('business_services_started') is False and proof.get('volumes_modified') is False,'IMPORT_RECEIPT_NONBUSINESS_BOUNDARY');need(isinstance(proof.get('identity'),dict) and proof['identity'] and isinstance(proof.get('package_resolution'),(dict,list)) and proof['package_resolution'],'ACTUAL_IDENTITY_AND_PACKAGE_RESOLUTION_REQUIRED')
 def scalars(value):
  if isinstance(value,dict):return [item for child in value.values() for item in scalars(child)]
  if isinstance(value,list):return [item for child in value for item in scalars(child)]
  return [value]
 need(any(v in (TARGET['sut_image_config_digest'],TARGET['sut_image_config_digest'][7:]) for v in scalars(proof['identity'])),'ACTUAL_CONFIG_ID_PRESENT_IN_IDENTITY');reference=packet['loaded_receipt_reference'];need(isinstance(reference['original_path'],str) and reference['original_path'].startswith('/'),'ACTUAL_RECEIPT_ORIGINAL_PATH_REQUIRED');need(created-3600<=epoch(reference['observed_at'])<=now+5,'ACTUAL_LOADED_RECEIPT_OBSERVATION_FRESHNESS');need(packet['loaded_receipt_sha256']==reference['sha256']==sha(files['backend_import_receipt']),'ACTUAL_IMPORT_RECEIPT_BYTES_BINDING')
 env=packet['environment'];origin=urllib.parse.urlsplit(env['origin']);need(origin.scheme=='https' and origin.hostname and not origin.username and not origin.password and not origin.query and not origin.fragment and origin.path in ('','/'),'STRICT_HTTPS_ORIGIN')
 need(ipaddress.ip_address(env['connect_ip']).is_private,'REAL_PRIVATE_CONNECT_IP');need(sha(files['ca'])==env['ca_sha256'],'CA_BYTES_BINDING');context=ssl.create_default_context(cadata=files['ca'].decode());context.minimum_version=ssl.TLSVersion.TLSv1_2
 sessions=packet['sessions'];need(set(sessions)==ROLES,'FOUR_REAL_ROLES_REQUIRED')
 for role,v in sessions.items():
  need(isinstance(v['token'],str) and len(v['token'])>=16,'ACTUAL_EXISTING_SESSION_TOKEN_REQUIRED');need(type(v['user_id']) is int and v['user_id']>0 and isinstance(v['project_ids'],list) and all(type(x) is int and x>0 for x in v['project_ids']) and isinstance(v['scopes'],list),'ACTUAL_SESSION_METADATA');need(epoch(v['expires_at'])>end,'ACTUAL_SESSION_EXPIRY_COVERS_WHOLE_WINDOW')
 need('escalation:write' in sessions['service']['scopes'],'SERVICE_SCOPE')
 inv=packet['inventory'];need(inv['schema']=='772-inventory-v1' and isinstance(inv['clients'],list) and len(inv['clients'])==400,'INVENTORY_400');need(epoch(inv['captured_at'])>=created-600 and epoch(inv['captured_at'])<=now+5,'CURRENT_INVENTORY_CAPTURE');need(type(inv['rule_version']) is int and inv['rule_version']>0,'RULE_VERSION');need({x['client_id'] for x in inv['clients']}==set(range(400)),'CLIENT_IDS')
 ids=[];projects=set()
 for item in inv['clients']:
  task=item['transition_task'];escal=item['escalation_task'];event=item['escalation_event'];pid=item['project_id'];projects.add(pid);ids.extend([task['id'],escal['id']]);need(type(pid) is int and pid>0 and all(type(n) is int and n>0 for n in ids[-2:]),'TASK_PROJECT_IDS');need(task['project_id']==pid==escal['project_id']==event['project_id'],'PROJECT_BINDING');need(task['state']==2 and task['owner_id']==sessions['developer']['user_id'],'MUTABLE_TASK_ELIGIBILITY');need(epoch(task['plan']['planned_end'])>end+86400,'TASK_NOT_DUE_IN_WHOLE_WINDOW');need(escal['state'] not in (6,7) and event['task_id']==escal['id'] and event['schedule_version']==escal['schedule_version'] and event['rule_version']==inv['rule_version'],'CURRENT_EXISTING_EVENT');need(isinstance(item['project_manager_ids'],list) and item['project_manager_ids'],'MANAGER_SNAPSHOT')
  for role in ROLES:need(pid in sessions[role]['project_ids'],'SESSION_PROJECT_MEMBERSHIP')
 need(len(set(ids))==800 and len(projects)>=35,'EXCLUSIVE_800_AND_PROJECT_SPREAD');need(sha_field(packet['fixture_sha256']),'FIXTURE_HASH');counts=packet['counts'];need(all(type(counts.get(k)) is int and counts[k]>=0 for k in ['projects','tasks','dependencies','reviews','decisions']),'DECLARED_COUNTS_REQUIRED')
 return {'sessions':4,'inventory_entries':400,'distinct_task_ids':800,'projects':len(projects),'actual_import_receipt_runtime_files':60,'actual_import_chain_scope':'STRUCTURE_AND_RAW_SHA_BINDING_ONLY_REQUIRES_ROOT_FULL_CHAIN_REVIEW','actual_session_expiry_covers_entire_window':True,'fixture_counts_scope':'DECLARED_ONLY_NOT_DATABASE_COUNT_ACCEPTANCE'}

def installed(runtime):
 runtime=Path(runtime);need(runtime.is_file() and sha(runtime.read_bytes())==TARGET['runtime_sha256'],'EXACT_V24_RUNTIME_INSTALL');need(sha(read(runtime.parent/'openapi.json'))==TARGET['openapi_sha256'],'FROZEN_OPENAPI_INSTALL')
def packet_files(folder):
 folder=Path(folder);return obj(folder/'inputs/session.private.json'),{'ca':read(folder/'inputs/ca.pem'),'source_manifest':read(folder/'inputs/source-manifest.json'),'backend_bundle_manifest':read(folder/'inputs/backend-bundle-manifest.json'),'backend_import_receipt':read(folder/'inputs/backend-import-receipt.json')}
def grant_for(env,packet,env_bytes,allow=False):
 return {'schema':'772-grant-v1','allow':allow,'run_id':env['run_id'],'created_at':packet['created_at'],'window_start_utc':packet['window']['start_utc'],'window_end_utc':packet['window']['end_utc'],'cost_stop_utc':packet['window']['cost_stop_utc'],'origin':env['origin'],'environment_sha256':sha(env_bytes),'runtime_sha256':TARGET['runtime_sha256'],'source_sha256':TARGET['source_manifest_sha256'],'image_digest':TARGET['sut_image_config_digest'],'fixture_sha256':packet['fixture_sha256'],'backend_bundle_manifest_sha256':TARGET['backend_bundle_manifest_sha256'],'backend_import_receipt_sha256':packet['loaded_receipt_sha256'],'backend_import_receipt_reference':packet['loaded_receipt_reference'],'neutral_binding_sha256':packet['binding_sha256'],'load_runtime_image_config_digest':TARGET['load_runtime_image_config_digest'],'clients':400,'warmup_seconds':60,'steady_seconds':600,'request_timeout_seconds':15,'postcheck_seconds':40,'limits':LIMITS,'permissions':['linux-preflight','one-cohort','read-postconditions'],'prohibitions':['cloud-control','install','login','session-extension','request-retry','restart','successor-run']}
def environment_for(args,packet,work,output):
 identity={'source_sha256':TARGET['source_manifest_sha256'],'source_git_commit':TARGET['git_commit'],'backend_bundle_manifest_sha256':TARGET['backend_bundle_manifest_sha256'],'image_digest':TARGET['sut_image_config_digest'],'load_runtime_image_config_digest':TARGET['load_runtime_image_config_digest'],'fixture_sha256':packet['fixture_sha256'],'openapi_sha256':TARGET['openapi_sha256'],'backend_import_receipt_sha256':packet['loaded_receipt_sha256'],'backend_import_receipt_reference':packet['loaded_receipt_reference'],'neutral_binding_sha256':packet['binding_sha256']}
 env={'schema':'772-env-v1','run_id':args.run_id,'created_at':packet['created_at'],'origin':packet['environment']['origin'],'connect_ip':packet['environment']['connect_ip'],'ca_file':str(work/'ca'),'sessions_file':str(work/'sessions.json'),'inventory_file':str(work/'inventory.json'),'output_dir':str(output),'identity':identity,'declared_fixture_counts':packet['counts']}
 return env
def prepare(args):
 installed(args.runtime_file);packet,files=packet_files(args.neutral_opened_dir);summary=validate(packet,files,args.run_id);base=Path(args.workspace);work=base/'runs'/args.run_id;work.parent.mkdir(mode=0o700,parents=True,exist_ok=True);need(not work.exists(),'FRESH_PREPARATION_DIRECTORY_REQUIRED');output=base/'results'/args.run_id;output.parent.mkdir(mode=0o700,parents=True,exist_ok=True);need(not output.exists(),'FRESH_RESULT_DIRECTORY_REQUIRED');work.mkdir(mode=0o700)
 write_new(work/'packet.private.json',packet)
 for name,data in files.items():write_new(work/name,data)
 write_new(work/'sessions.json',packet['sessions']);write_new(work/'inventory.json',packet['inventory'])
 env=environment_for(args,packet,work,output);env_bytes=encoded(env);write_new(work/'environment.json',env_bytes);write_new(work/'grant.default-false.json',grant_for(env,packet,env_bytes));return {'status':'PREPARED_DEFAULT_FALSE_NOT_ADMITTED','run_id':args.run_id,'environment_sha256':sha(env_bytes),'runtime_sha256':TARGET['runtime_sha256'],'neutral_binding_sha256':packet['binding_sha256'],'backend_import_receipt_sha256':packet['loaded_receipt_sha256'],'backend_import_receipt_reference':packet['loaded_receipt_reference'],'grant_allow':False,'summary':summary,'SUT_requests':0,'actual_guard':'NOT_RUN_REQUIRES_LATER_EXPLICIT_GRANT'}
def execute(args):
 need(args.authorize_once==args.run_id,'EXPLICIT_SINGLE_AUTHORIZATION_REQUIRED');installed(args.runtime_file);work=Path(args.workspace)/'runs'/args.run_id;packet=obj(work/'packet.private.json');files={n:read(work/n) for n in ['ca','source_manifest','backend_bundle_manifest','backend_import_receipt']};validate(packet,files,args.run_id,execution=True);env_bytes=read(work/'environment.json');env=json.loads(env_bytes);need(env==environment_for(args,packet,work,Path(args.workspace)/'results'/args.run_id),'PREPARED_ENV_BINDING');need(obj(work/'sessions.json')==packet['sessions'] and obj(work/'inventory.json')==packet['inventory'],'UNCHANGED_ACTUAL_INPUTS');expected=grant_for(env,packet,env_bytes,True);grant=obj(args.grant_file);need(grant==expected,'EXACT_FRESH_EXTERNAL_GRANT_REQUIRED');need(not (work/'grant.json').exists() and not (work/'grant.consumed').exists(),'GRANT_ALREADY_USED');need(not Path(env['output_dir']).exists(),'RESULT_ALREADY_EXISTS');write_new(work/'grant.json',grant);print(json.dumps({'status':'EXPLICIT_ONCE_ABOUT_TO_CALL_UNCHANGED_CORE','run_id':args.run_id,'runtime_sha256':TARGET['runtime_sha256'],'SUT_requests_by_adapter':0}),flush=True);os.execv(sys.executable,[sys.executable,str(args.runtime_file),'run',str(work/'environment.json'),str(work/'grant.json')])
def main():
 parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['prepare','execute']);parser.add_argument('--workspace',required=True);parser.add_argument('--runtime-file',required=True);parser.add_argument('--run-id',required=True);parser.add_argument('--neutral-opened-dir');parser.add_argument('--grant-file');parser.add_argument('--authorize-once');args=parser.parse_args()
 try:
  safe_run_id(args.run_id)
  if args.mode=='prepare':need(args.neutral_opened_dir is not None,'NEUTRAL_OPENED_DIR_REQUIRED');result=prepare(args)
  else:need(args.grant_file is not None,'EXTERNAL_GRANT_FILE_REQUIRED');execute(args);return
  print(json.dumps(result,separators=(',',':')),flush=True)
 except Stop as exc:print(json.dumps({'status':'BLOCKED','code':str(exc),'run_id':args.run_id,'SUT_requests_by_adapter':0}),flush=True);raise SystemExit(2)
 except Exception as exc:print(json.dumps({'status':'BLOCKED','code':'INPUT_OR_IO_EXCEPTION','exception_type':type(exc).__name__,'run_id':args.run_id,'SUT_requests_by_adapter':0}),flush=True);raise SystemExit(2)
if __name__=='__main__':main()
