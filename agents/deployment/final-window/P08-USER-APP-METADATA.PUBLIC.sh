python3 -B - <<'P08_USER_METADATA'
import base64,datetime,hashlib,json,subprocess,zlib
from pathlib import Path
F=Path('/root/t44-final-20261029/P08');PROJECT='t44-cloud-r30finalp08-p'
def run(argv):
 r=subprocess.run(argv,check=False,capture_output=True,timeout=20)
 return r.stdout if r.returncode==0 else None
def original(p):
 if p.is_symlink() or p.stat().st_size>8000000:raise ValueError('BOUNDED_OWN_NEUTRAL_FILE_REQUIRED')
 raw=p.read_bytes();return raw,json.loads(raw)
def no_credentials(v):
 if isinstance(v,dict):
  if {'token','access_token','password','private_key','database_url'}&set(v):raise ValueError('CREDENTIAL_BEARING_OBJECT_NOT_ALLOWED')
  for x in v.values():no_credentials(x)
 elif isinstance(v,list):
  for x in v:no_credentials(x)
report={'kind':'USER_P08_APP_OWN_NEUTRAL_METADATA_ONLY','observed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'project':PROJECT,'containers':[],'other_running_T44_projects':[],'neutral_DB_readback_records':{},'session_scope_record':{'status':'PENDING_NOT_PRESENT'},'bootstrap':{'status':'PENDING_NOT_PRESENT'},'state_changed':False,'QA_or_SUT_requests':0,'credential_files_opened':False}
ids=run(['docker','--context','default','ps','--quiet','--filter','label=com.docker.compose.project'])
if ids:
 for cid in ids.decode().split():
  raw=run(['docker','--context','default','inspect',cid])
  if raw is None:continue
  row=json.loads(raw)[0];labels=row.get('Config',{}).get('Labels') or {};project=labels.get('com.docker.compose.project','')
  if not project.startswith('t44'):continue
  if project!=PROJECT:
   report['other_running_T44_projects'].append({'project':project,'id':row['Id'],'name':row['Name']});continue
  state=row['State'];host=row['HostConfig'];report['containers'].append({'id':row['Id'],'image_id':row['Image'],'name':row['Name'],'role':labels.get('com.docker.compose.service'),'configured_user':row['Config'].get('User'),'running':state['Running'],'restart_count':row['RestartCount'],'OOMKilled':state.get('OOMKilled'),'health':state.get('Health',{}).get('Status'),'limits':{k:host.get(k)for k in ['NanoCpus','CpuQuota','CpuPeriod','Memory','MemorySwap','PidsLimit','Ulimits']}})
roles={r['role']for r in report['containers']};expected={'mysql','rabbitmq','api','consumer','web','tls-gateway','scheduler'}
report['seven_roles_running']=roles==expected and len(report['containers'])==7 and all(r['running']for r in report['containers'])
report['other_APP_T44_container_writer_observed']=bool(report['other_running_T44_projects']);report['external_writer_absence_proven']=False
report['writer_scope_note']='This observes only current APP T44 containers/units; external-client writer absence requires separate root-reviewed LOAD facts.'
units=run(['systemctl','list-units','--type=service','--state=active','--plain','--no-legend','t44-final-*']);report['active_T44_units']=units.decode().strip() if units else ''
for label,path in [('empty','P-empty-counts/output/result/counts.json'),('seeded','P-counts/output/result/counts.json'),('final','P-final-counts/output/result/counts.json')]:
 p=F/path
 if not p.is_file():report['neutral_DB_readback_records'][label]={'status':'PENDING_NOT_PRESENT'};continue
 raw,v=original(p);no_credentials(v);report['neutral_DB_readback_records'][label]={'status':'ORIGINAL_RECORDED_DB_READBACK_NOT_NEW_SQL_QUERY','bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),**{k:v.get(k)for k in ['captured_at','run_id','namespace','database','binding_sha256','actual_fixture_counts','raw_counts','project_ids','actual_fixture_sha256']}}
p=F/'P-http/output/result/factual-snapshots.json'
if p.is_file():
 raw,v=original(p);no_credentials(v);report['session_scope_record']={'status':'OWN_RECORDED_HTTP_FACTS_NOT_CREDENTIALS','sha256':hashlib.sha256(raw).hexdigest(),'generated_complete_utc':v.get('generated_complete_utc'),'inventory_client_count':len(v.get('inventory',{}).get('clients',[])),'sessions':{role:{k:row.get(k)for k in ['user_id','project_ids','scopes','expires_at','issued_at','login_request_started_at','response_observed_at']}for role,row in v.get('session_attestations',{}).items()}}
p=F/'LOAD-bootstrap.original.PUBLIC.json'
if p.is_file():
 raw,v=original(p);report['bootstrap']={'status':'PRESENT_ORIGINAL_PUBLIC_BYTES','bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'zlib_b64':base64.b64encode(zlib.compress(raw,9)).decode()}
print(json.dumps(report,sort_keys=True))
P08_USER_METADATA
