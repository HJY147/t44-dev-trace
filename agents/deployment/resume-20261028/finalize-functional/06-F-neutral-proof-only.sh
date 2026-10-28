set -eu
python3 - <<'PYFNEUTRAL'
START_PAYLOAD='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'
import base64,gzip,hashlib,json,os,subprocess,time
from pathlib import Path
PHASE=Path('/root/t44-r9/campaign-r28functional-01/f')
GEN=Path('/root/t44-r9/resume-20261028-02/resume-profile/generation.py')
OUT=Path('/root/t44-r9/resume-20261028-02/F-neutral-runtime-01')
BINDING='be1975a7625eae32bf8aaae7e1f2de7d7aef8b20968aa5552320b22202258a9f'
SOURCE='a12e9e70b963bacafda3242bb6d82e53ee912ff1'
START_SHA='1297a0155bc9682685cc012129641181014084387f36a8fa37d16c436313404e'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def read(path):
 fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW)
 with os.fdopen(fd,'rb') as stream:return stream.read()
def write(path,raw):
 fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
 with os.fdopen(fd,'wb') as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())
START_BYTES=gzip.decompress(base64.b64decode(START_PAYLOAD,validate=True))
assert len(START_BYTES)==9786 and sha(START_BYTES)==START_SHA
records=[json.loads(row) for row in START_BYTES.splitlines() if row.strip()]
actual=[r for r in records if r.get('success') is True]
assert [r['action'] for r in actual]==['persistent_timer_armed','config','infra','migrate','idle']
initial=actual[-1];assert initial['source_sha']==SOURCE and initial['host_https']['status']==401 and initial['host_https']['strict_CA_and_IP_verified'] is True
assert actual[0]['timer']=='t44-cloud-r28funcgen01-f-stop.timer' and actual[0]['stop_utc']=='2026-10-28T10:30:00Z'
assert sha(read(GEN))=='4672a5838879ab1fde599c45d464906600373fdb38da654e21879881204d11a8'
bindingraw=read(PHASE/'binding.json');assert sha(bindingraw)==BINDING;binding=json.loads(bindingraw)
assert binding['source_sha']==SOURCE and binding['database']=='t44c_r28funcgen01_f' and binding['project']=='t44-cloud-r28funcgen01-f' and binding['api_workers']==4 and binding['entrypoint']=='t44.api:app' and binding['profiling'] is False
assert time.time()<1793183400.0
statusraw=subprocess.run(['/usr/bin/python3',str(GEN),'status','--phase-dir',str(PHASE),'--binding-sha256',BINDING],capture_output=True,check=True,timeout=30).stdout
status=json.loads(statusraw);assert status['success'] is True and status['source_sha']==SOURCE
present={r['role']:r for r in status['resources'] if not r.get('absent')};initial_present={r['role']:r for r in initial['resources'] if not r.get('absent')}
needed={'mysql','rabbitmq','api','consumer','web','tls-gateway'}
assert needed<=set(present)
assert all(present[r]['state']['Running'] is True and present[r]['restart_count']==0 and present[r]['container_id']==initial_present[r]['container_id'] for r in needed)
api=present['api'];assert api['image_id']=='sha256:475a1dd0240ad89519403e2c4ee4859fa68314e63879a8349e8ac4143926b39d'
config=json.loads(subprocess.run(['docker','--context','default','inspect','--format','{{json .Config}}',api['container_id']],capture_output=True,check=True,timeout=15).stdout)
cmd=config['Cmd'];assert 't44.api:app' in cmd and cmd[cmd.index('--workers')+1]=='4'
ttls=[v.split('=',1)[1] for v in config['Env'] if v.startswith('T44_SESSION_TTL_SECONDS=')]
assert len(ttls)==1 and ttls[0].isdigit();ttl=int(ttls[0]);assert 60<=ttl<=86400
del config
ca=read(PHASE/'tls/ca.pem');assert sha(ca)=='de9b2e80a650b3e502652a6f81790d2acb50be1c9ed9170dfa8b74429111243b'
selected=[{'role':r['role'],'container_id':r['container_id'],'image_id':r['image_id'],'Running':r['state']['Running'],'Pid':r['state']['Pid'],'restart_count':r['restart_count']} for r in present.values()]
proof={'kind':'actual-new-F-runtime-neutral-evidence-public','source_sha':SOURCE,'binding_sha256':BINDING,'original_start_receipt_sha256':START_SHA,'original_start_actions':[{'action':r['action'],'receipt_id':r['receipt_id'],'utc':r['utc']} for r in actual],'current_status_stdout_sha256':sha(statusraw),'current_resources':selected,'actual_api_cmd':cmd,'actual_main_http_session_ttl_seconds':ttl,'config_Env_disclosed':False,'host_https_at_original_idle':initial['host_https'],'no_accounts_sessions_business_seed_or_SUTgrant_by_this_script':True}
proofraw=(json.dumps(proof,separators=(',',':'))+'\n').encode()
identity={'source_sha':SOURCE,'source_archive_sha256':binding['source_archive_sha256'],'image_digest':api['image_id'],'runtime_identity':binding['project']+'/api/'+api['container_id'],'base_url':'https://'+binding['app_private_ip']+':'+str(binding['tls_port'])+'/api/v1','pinned_ip':binding['app_private_ip'],'ca_sha256':sha(ca),'isolated_resource_ids':['docker:'+binding['project']+'/'+r['role']+'/'+r['container_id'] for r in present.values()],'main_http_session_ttl_seconds':ttl,'worker_count':4,'schema_name':binding['database'],'project_name':binding['project'],'phase_dir':str(PHASE),'prepared_binding_sha256':BINDING,'planned_stop_utc':binding['stop_utc'],'prepared_receipt_sha256':'ba4801d81c266856f54ea972539dbf4e9b38e769c2bc4cdc564a40e594da76a9','runtime_receipt_sha256':sha(proofraw),'lifecycle_status':'running'}
neutral={'kind':'ROOT_NEUTRAL_NEW_F_RUNTIME_PUBLIC','sut_identity':identity,'ca_pem_b64':base64.b64encode(ca).decode(),'runtime_receipt_path':str(OUT/'runtime-receipt.PUBLIC.json'),'original_start_receipt_sha256':START_SHA,'auth_store_resource_id':'mysql:'+present['mysql']['container_id']+'/schema:'+binding['database'],'absent_roles':[r['role'] for r in status['resources'] if r.get('absent')],'worker_count_basis':'actual Config.Cmd --workers=4; child process PIDs not enumerated','no_account_session_scope_provider_or_rootgrant_in_this_file':True,'actual_identity_only_not_execution_admission':True}
neutralraw=(json.dumps(neutral,separators=(',',':'))+'\n').encode()
os.umask(0o077);OUT.mkdir(mode=0o700)
write(OUT/'root-start.PUBLIC.jsonl',START_BYTES);write(OUT/'current-status.PUBLIC.json',statusraw);write(OUT/'runtime-receipt.PUBLIC.json',proofraw);write(OUT/'neutral-identity.PUBLIC.json',neutralraw)
print(json.dumps(neutral),flush=True)
print(json.dumps({'neutral_bytes':len(neutralraw),'neutral_sha256':sha(neutralraw),'runtime_receipt_bytes':len(proofraw),'runtime_receipt_sha256':sha(proofraw),'output_dir':str(OUT),'frozen_code_binding_and_original_receipts_changed':False}),flush=True)
PYFNEUTRAL
