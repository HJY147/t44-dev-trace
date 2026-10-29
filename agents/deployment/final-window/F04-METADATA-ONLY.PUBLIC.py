"""APP own-fixture projection only: no token/password output and no session changes."""
import base64,datetime,hashlib,json
from pathlib import Path
R=Path('/root/t44-final-20261029/F04')
def raw(p):
 if p.is_symlink() or p.stat().st_size>2000000:raise ValueError('BOUNDED_ORIGINAL_ONLY')
 return p.read_bytes()
def sha(p):return hashlib.sha256(raw(p)).hexdigest()
def read(p):return json.loads(raw(p))
e=R/'functional-environment.private.json';env=read(e)
if sha(e)!='6aebd9c54e15f146608d8aabb73d8829c862680340385ed79ccffdb174e63853':raise ValueError('ORIGINAL_F04_ENV_SHA_REQUIRED')
clock=read(R/'timeplan.PUBLIC.json');phase=read(R/'preparation.PUBLIC.json');proofp=R/'F-services/output/result/f-service-proof.private.json';proof=read(proofp)
now=datetime.datetime.now(datetime.timezone.utc);stop=datetime.datetime.fromisoformat(clock['stop_utc'].replace('Z','+00:00'))
public={'kind':'F04_OWN_FIXTURE_METADATA_ONLY_NO_QA','observed_utc':now.isoformat(),'original_environment_sha256':sha(e),'identity':env['identity'],'run_id':env['run_id'],'project_id':env['project_id'],'origin':env['origin'],'original_max_seconds':env['max_seconds'],'stop_utc':clock['stop_utc'],'cost_stop_utc':clock['cost_stop_utc'],'dispatch_max_seconds_cap':max(0,min(env['max_seconds'],int((stop-now).total_seconds())-180)),'sessions':{},'service_original_proof_sha256':sha(proofp),'service_db_readback':{},'contains_tokens_or_passwords':False,'sessions_changed':False}
for label,row in env['sessions'].items():
 public['sessions'][label]={k:row.get(k) for k in ['user_id','username','expires_at','project_ids','scopes']}
for label,row in proof['sessions'].items():
 p=proofp.parent/row['original_file'];original=read(p)
 if sha(p)!=row['original_sha256'] or original['session_id']!=row['session_id'] or original['expires_at']!=row['expires_at']:raise ValueError('ACTUAL_ORIGINAL_SERVICE_RECEIPT_MISMATCH')
 public['service_db_readback'][label]={k:row[k] for k in ['original_sha256','session_id','expires_at','project_ids','scopes','ttl_seconds','actual_DB_readback']}
receipt=Path(phase['import']['receipt']);ca=R/'campaign/f/tls/ca.pem'
public['backend_import_receipt']={'path':str(receipt),'sha256':sha(receipt),'original_b64':base64.b64encode(raw(receipt)).decode()}
public['public_ca']={'sha256':sha(ca),'original_b64':base64.b64encode(raw(ca)).decode()}
print(json.dumps(public,sort_keys=True))
