"""Local-only user-paste generator. Inputs are actual public facts and separately approved documents."""
import argparse,base64,datetime,hashlib,importlib.util,json,re,time,uuid,zlib
from pathlib import Path
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('p08facts',HERE/'P08-FACTS-CHECK.PUBLIC.py');f=importlib.util.module_from_spec(spec);spec.loader.exec_module(f)
R=f.R;T=f.T;W=R+'/QA753P08';P08='r30finalp08'
def raw(p):
 p=Path(p)
 if p.is_symlink() or p.stat().st_size>2000000:raise ValueError('BOUNDED_ORIGINAL_INPUT_REQUIRED')
 return p.read_bytes()
def sha(b):return hashlib.sha256(b).hexdigest()
def obj(p):return json.loads(raw(p))
def need(v,c):
 if not v:raise ValueError(c)
def encoded(v):return (json.dumps(v,sort_keys=True,indent=2)+'\n').encode()
def shell(payload,body):
 compressed=zlib.compress(json.dumps(payload,separators=(',',':')).encode(),9)
 header="umask 077\npython3 -B - <<'USER_P08_COMMAND'\nimport base64,datetime,hashlib,json,os,subprocess,time,zlib\nfrom pathlib import Path\n"
 header+="blob=base64.b64decode("+repr(base64.b64encode(compressed).decode())+");assert hashlib.sha256(blob).hexdigest()=="+repr(sha(compressed))+"\nD=json.loads(zlib.decompress(blob));os.umask(0o077)\n"
 header+="def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()\ndef put(p,b):\n p=Path(p)\n with p.open('xb') as out:out.write(b)\n p.chmod(0o600)\ndef original(item):\n b=base64.b64decode(item['b64']);assert hashlib.sha256(b).hexdigest()==item['sha256'];return b\nassert os.geteuid()==0\nassert subprocess.run(['timedatectl','show','--property=NTPSynchronized','--value'],capture_output=True,check=True).stdout.strip()==b'yes'\n"
 return header+body+"\nUSER_P08_COMMAND\n"
def blob(b):return {'b64':base64.b64encode(b).decode(),'sha256':sha(b)}
def check_target(target,approval,receipt):
 tr=obj(target);ar=obj(approval);ir=obj(receipt)
 expected={'git_commit':f.SOURCE,'source_manifest_sha256':f.SM,'backend_bundle_manifest_sha256':f.BUNDLE,'sut_image_config_digest':'sha256:47c3383fedcdaa882257ccf2338bfd93fe4d7f67c1bf69b6fda25e3bb159e07a','load_runtime_image_config_digest':f.IMAGE,'runtime_sha256':'81e04666cf05c2932397c5d39521ef881602f3046342e2d4d5605a694e5829bf','openapi_sha256':'6f07cb53a7d9314240ba93ec490325d3c63dca7e4d077021047e216e7b26f478'}
 need(all(tr.get(k)==v for k,v in expected.items()),'EXACT_QA90B_TARGET_REQUIRED');need(tr['backend_import_receipt_sha256']==sha(raw(receipt)),'NEW_IMPORT_RECEIPT_SHA_REQUIRED');need(ir['source_sha']==f.SOURCE and ir['bundle_manifest_sha256']==f.BUNDLE and ir['source_manifest_sha256']==f.SM,'ACTUAL_NEW90B_IMPORT_REQUIRED')
 need(ar.get('approved') is True and ar.get('supports_source')==f.SOURCE and ar.get('target_profile_sha256')==sha(raw(target)) and ar.get('qa_adapter_sha256')==f.ADAPTER,'INDEPENDENT_QA_TARGET_APPROVAL_REQUIRED')
def clock_from_bootstrap(p):
 b=obj(p);clockraw=base64.b64decode(b['timeplan_b64'],validate=True);need(sha(clockraw)==b['timeplan_sha256'],'BOOTSTRAP_CLOCK_SHA');clock=json.loads(clockraw)
 need(clock['run_id']==P08 and clock['phase']=='p' and clock['source_sha']==f.SOURCE,'EXACT_FRESH_P08_BOOTSTRAP')
 t0=f.epoch(clock['t0_utc']);s=f.epoch(clock['start_utc']);e=f.epoch(clock['end_utc']);g=f.epoch(clock['stop_utc']);c=f.epoch(clock['cost_stop_utc'])
 need((s-t0,e-t0,g-t0,c-t0)==(600,1380,1500,1800) and f.epoch(clock['packet_cutoff_utc'])==s-150,'UNCHANGED_P08_RELATIVE_WINDOW')
 return b,clock
def freeze(a):
 app,ah=f.load_facts(a.app_facts);load,lh=f.load_facts(a.load_facts);checked=f.check(app,load,now=time.time());need(not checked['errors'],'APP_LOAD_FACTS_BLOCKED:'+','.join(checked['errors']));need(checked['fresh_for_APP_admission_now'],'LOAD_READY_EXPIRED_RECAPTURE_NO_RETIME')
 fee=obj(a.fee);proof=obj(a.platform_proof);now=time.time();observed=f.epoch(fee['resume_observed_utc']);outer=f.epoch(fee['absolute_cost_cutoff_utc'])
 need(fee.get('root_approved') is True and fee.get('remaining_budget_CNY')==50 and fee['historical_APP_first_boot_utc']=='2026-10-29T13:45:26Z','NEW_ROOT_APPROVED_CAP50_FEE_REQUIRED')
 need(fee['actual_APP_resume_boot_utc']==app['actual_APP_resume_boot_utc'] and fee['actual_LOAD_resume_boot_utc']==load['actual_LOAD_resume_boot_utc'],'FEE_CURRENT_BOOT_FACTS_MUST_MATCH')
 need(observed<=min(f.epoch(app['actual_APP_resume_boot_utc']),f.epoch(load['actual_LOAD_resume_boot_utc']))<=now and outer-now>=2100 and (outer-observed)/3600*15.5765<=47,'NEW_COST_ORIGIN_BUDGET_AND35MIN_RESERVE_REQUIRED')
 need(bool(re.fullmatch(r'i-[a-z0-9]{6,32}',proof.get('APP_instance_id',''))) and bool(re.fullmatch(r'i-[a-z0-9]{6,32}',proof.get('LOAD_instance_id',''))) and proof['APP_instance_id']!=proof['LOAD_instance_id'],'TWO_EXACT_ROOT_VERIFIED_PLATFORM_INSTANCE_IDS_REQUIRED')
 need(proof.get('verification_scope')=='CREATED_SCHEDULED_CONFIGURATION_ONLY' and proof.get('platform_task_created') is True and proof.get('schedule_enabled') is True and bool(re.fullmatch('exec-[a-z0-9]{6,40}',proof.get('task_execution_id',''))) and proof.get('configured_stopped_mode')=='StopCharging' and proof.get('configured_force_stop') is False and set(proof.get('target_instance_ids',[]))=={proof['APP_instance_id'],proof['LOAD_instance_id']},'ROOT_REVIEWED_SCHEDULED_OOS_CONFIGURATION_REQUIRED')
 need(proof.get('root_verified') is True and proof.get('APP_stop_retains_disks') is True and proof.get('LOAD_stop_retains_disks') is True and proof.get('stop_utc')==fee['absolute_cost_cutoff_utc'] and proof.get('hourly_APP_CNY')==12.436 and proof.get('hourly_LOAD_CNY')==3.1405,'REVIEWED_CONFIGURED_STOP_AND_CURRENT_QUOTE_REQUIRED')
 ready={'root_approved':True,'actual_LOAD_ready':True,'observed_utc':load['observed_utc'],'actual_image_id':f.IMAGE,'QA_or_other_writer_started':False,'original_live_python_proof_sha256':lh,'SUT_requests':0,'root_reviewed_original_APP_facts_sha256':ah}
 uid=uuid.uuid4().hex;payload={'fee':blob(raw(a.fee)),'ready':blob(encoded(ready)),'fee_path':R+'/P08-user-current-cost-'+uid+'.PUBLIC.json','ready_path':R+'/P08-user-fresh-LOAD-'+uid+'.PUBLIC.json','launcher':T+'/P08-CONTINUOUS-fast10-cap50.PUBLIC.py','launcher_sha256':app['tool_derivation']['tools']['P08-CONTINUOUS-fast10-cap50.PUBLIC.py']}
 body="""assert not Path('/root/t44-final-20261029/P08').exists() and not Path('/root/t44-final-20261029/r30finalp08-launcher').exists(),'P08_ALREADY_STARTED_DO_NOT_REPLAY'
assert digest(D['launcher'])==D['launcher_sha256'],'APP_LAUNCHER_CHANGED'
ready=json.loads(original(D['ready']));age=time.time()-datetime.datetime.fromisoformat(ready['observed_utc'].replace('Z','+00:00')).timestamp();assert 0<=age<=120,'LOAD_READY_EXPIRED_RECAPTURE'
fee=json.loads(original(D['fee']));assert datetime.datetime.fromisoformat(fee['absolute_cost_cutoff_utc'].replace('Z','+00:00')).timestamp()-time.time()>=2100,'NEW_OUTER_RESERVE_EXPIRED'
put(D['fee_path'],original(D['fee']));put(D['ready_path'],original(D['ready']))
argv=['systemd-run','--unit=t44-final-p08-continuous','--property=Type=exec','--property=UMask=0077','--property=RuntimeMaxSec=2400','--collect','python3','-B',D['launcher'],'--load-ready',D['ready_path'],'--load-ready-sha256',D['ready']['sha256'],'--cost-approval',D['fee_path'],'--cost-approval-sha256',D['fee']['sha256']]
raise SystemExit(subprocess.run(argv,check=False).returncode)"""
 return shell(payload,body)
def load_prepare(a):
 load,lh=f.load_facts(a.load_facts);b,clock=clock_from_bootstrap(a.bootstrap);check_target(a.qa_target,a.qa_approval,a.backend_import_receipt);pins=obj(a.qa_public_pins)
 need(pins.get('root_reviewed') is True,'QA_PUBLIC_TOOL_PINS_ROOT_REVIEW_REQUIRED');names={'ADAPTER_753.py','ENTRY_PERF_753.sh','INSTALL_753.sh','capsule_tool.py','tool-manifest.json','tools.753capsule','transport-key.rsa-oaep-sha256'};need(set(pins['files'])==names,'EXACT_QA_PUBLIC_TOOL_SET_REQUIRED')
 for n,item in pins['files'].items():
  need(Path(item['source']).name==n and ('/public/' in item['source'] or item['source'].startswith(R+'/ops01/qa-public/')),'PUBLIC_TOOL_SOURCE_ONLY')
  if n=='transport-key.rsa-oaep-sha256':need(item['sha256']=='19609563d296299deb7aa0a04a95abbe32ecbae7e7cf5161728e0866a6fc61f5','ORIGINAL_PUBLIC_WRAPPED_TRANSPORT_KEY_REQUIRED')
  else:need(load.get('public_files',{}).get(item['source'],{}).get('sha256')==item['sha256'],'QA_TOOL_NOT_IN_USER_FACTS:'+n)
 need(pins['files']['ADAPTER_753.py']['sha256']==f.ADAPTER and pins['files']['ENTRY_PERF_753.sh']['sha256']==f.ENTRY,'ORIGINAL_ENTRY_ADAPTER_REQUIRED')
 need(time.time()<f.epoch(clock['start_utc'])-30,'S_MINUS30_PREPARE_MARGIN_ALREADY_MISSED')
 uid=uuid.uuid4().hex;payload={'bootstrap':blob(raw(a.bootstrap)),'target':blob(raw(a.qa_target)),'approval':blob(raw(a.qa_approval)),'public_files':pins['files'],'workspace':W,'bootstrap_path':R+'/P08-user-bootstrap-'+uid+'.PUBLIC.json','driver':T+'/P08-USER-TRANSPORT-LOAD.PUBLIC.py','driver_sha256':'d1ed953dc7c0dd9d048dc3318c27015d3f71968499ba7d17dcd1841422d84601','transport_profile':T+'/final-transport-profile05.py','transport_profile_sha256':'a5425e961f486c78253a6ba319030c86b4057056622882086e686a642e61bc8a','start_utc':clock['start_utc']}
 body="""assert time.time()<datetime.datetime.fromisoformat(D['start_utc'].replace('Z','+00:00')).timestamp()-30,'PREPARATION_LATE_NO_OVERRIDE'
W=Path(D['workspace']);assert not W.exists() and not Path('/root/t44-final-20261029/r30finalp08-transfer').exists(),'EXISTING_P08_WORKSPACE_OR_TRANSFER_NO_REPLAY'
assert digest(D['driver'])==D['driver_sha256'] and digest(D['transport_profile'])==D['transport_profile_sha256'],'ORIGINAL_790_TRANSPORT_TOOLS_CHANGED'
W.mkdir(mode=0o700);(W/'public').mkdir(mode=0o700)
for n,item in D['public_files'].items():
 source=Path(item['source']);assert not source.is_symlink() and digest(source)==item['sha256'],'PUBLIC_QA_TOOL_CHANGED';put(W/'public'/n,source.read_bytes())
put(W/'public/TARGET_PROFILE_753.json',original(D['target']));put(W/'public/APPROVAL_753.json',original(D['approval']));put(D['bootstrap_path'],original(D['bootstrap']))
def step(label,argv):
 r=subprocess.run(argv,check=False,capture_output=True,timeout=120);put(W/(label+'.stdout.PUBLIC.json'),r.stdout);put(W/(label+'.stderr.private'),r.stderr)
 if r.returncode:raise ValueError('ORIGINAL_'+label.upper()+'_FAILED_PREFIX_PRESERVED')
 return r.stdout
step('install',['/bin/sh',str(W/'public/INSTALL_753.sh'),str(W),'/root/t44-r9/r29-load-key-01/load-only-private.pem'])
step('transport',['python3','-B',D['driver'],'--bootstrap',D['bootstrap_path'],'--bootstrap-sha256',D['bootstrap']['sha256']])
result=step('prepare',['/bin/sh',str(W/'public/ENTRY_PERF_753.sh'),'prepare',str(W),'r30finalp08','/root/t44-final-20261029/r30finalp08-transfer/extracted'])
prepared=json.loads(result);assert prepared.get('status')=='PREPARED_DEFAULT_FALSE' and prepared.get('SUT_requests')==0,'QA_PREPARE_DID_NOT_PASS'
print(json.dumps({'status':'P08_PREPARED_DEFAULT_FALSE_NOT_AUTHORIZED','prepare':prepared,'prepare_raw_sha256':hashlib.sha256(result).hexdigest(),'workspace':str(W),'QA_or_SUT_requests':0},sort_keys=True))"""
 return shell(payload,body)
def load_arm(a):
 load,lh=f.load_facts(a.load_facts);g=obj(a.grant);pr=obj(a.prepare_receipt);pr=pr.get('prepare',pr)
 need(pr.get('status')=='PREPARED_DEFAULT_FALSE' and pr.get('run_id')==P08 and pr.get('supports_source')==f.SOURCE and pr.get('qa_adapter_sha256')==f.ADAPTER and pr.get('SUT_requests')==0,'ACTUAL_QA_PREPARE_RECEIPT_REQUIRED')
 need(g.get('schema')=='772-grant-v1' and g.get('runtime_sha256')=='81e04666cf05c2932397c5d39521ef881602f3046342e2d4d5605a694e5829bf' and g.get('source_sha256')==f.SM and g.get('image_digest')=='sha256:47c3383fedcdaa882257ccf2338bfd93fe4d7f67c1bf69b6fda25e3bb159e07a','ORIGINAL_GRANT_SCHEMA_AND_IDENTITY_REQUIRED')
 need(g.get('allow') is True and g.get('run_id')==P08 and g.get('environment_sha256')==pr.get('environment_sha256') and (g.get('clients'),g.get('warmup_seconds'),g.get('steady_seconds'))==(400,60,600),'INDEPENDENT_EXACT_SINGLE_ALLOW_TRUE_GRANT_REQUIRED')
 start=f.epoch(g['window_start_utc']);need(time.time()<start-30 and f.epoch(g['window_end_utc'])-start==780,'ARM_S_MINUS30_REQUIRED_NO_LATE_OVERRIDE')
 helper=T+'/P08-SPLUS1-EXEC.PUBLIC.py';pin='7cba1f0cd9925ba92da12849e4789af8378d1fe870698be02be292017796bb02';need(load['public_files'].get(helper,{}).get('sha256')==pin,'SPLUS1_TOOL_NOT_IN_USER_FACTS')
 target=datetime.datetime.fromtimestamp(start+1,datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC');payload={'grant':blob(raw(a.grant)),'grant_path':W+'/root-approved-P08.grant.PUBLIC.json','entry':W+'/public/ENTRY_PERF_753.sh','entry_sha256':f.ENTRY,'helper':helper,'helper_sha256':pin,'workspace':W,'start_epoch':start,'target':target}
 body="""assert time.time()<D['start_epoch']-30,'TOO_LATE_TO_ARM_NO_OVERRIDE'
assert digest(D['entry'])==D['entry_sha256'] and digest(D['helper'])==D['helper_sha256'],'ORIGINAL_EXECUTION_TOOLS_CHANGED'
assert not Path('/root/t44-final-20261029/QA753P08/results/r30finalp08').exists(),'P08_ALREADY_EXECUTED_NO_REPLAY'
put(D['grant_path'],original(D['grant']))
base=['python3','-B',D['helper'],'execute','--entry',D['entry'],'--entry-sha256',D['entry_sha256'],'--workspace',D['workspace'],'--grant-file',D['grant_path'],'--grant-sha256',D['grant']['sha256'],'--run-id','r30finalp08']
argv=['systemd-run','--unit=qa753-p08-user-splus1','--on-calendar='+D['target'],'--timer-property=AccuracySec=1s','--timer-property=RandomizedDelaySec=0','--property=Type=exec','--collect',*base]
r=subprocess.run(argv,check=False);assert r.returncode==0,'TIMER_ARM_NOT_PROVEN'
print(json.dumps({'status':'P08_SINGLE_SPLUS1_TIMER_ARMED_NOT_YET_MEASUREMENT_RESULT','execute_at':D['target'],'grant_sha256':D['grant']['sha256']}))"""
 return shell(payload,body)
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['freeze','load-prepare','load-arm']);p.add_argument('--output',type=Path,required=True);p.add_argument('--root-reviewed-facts',action='store_true')
 for n in ['app-facts','load-facts','fee','platform-proof','bootstrap','qa-target','qa-approval','backend-import-receipt','qa-public-pins','grant','prepare-receipt']:p.add_argument('--'+n,type=Path)
 a=p.parse_args();need(a.root_reviewed_facts,'EXPLICIT_ROOT_REVIEW_OF_USER_FACTS_REQUIRED');required={'freeze':['app_facts','load_facts','fee','platform_proof'],'load-prepare':['load_facts','bootstrap','qa_target','qa_approval','backend_import_receipt','qa_public_pins'],'load-arm':['load_facts','grant','prepare_receipt']}[a.action]
 need(all(getattr(a,k) is not None for k in required),'MISSING_ACTUAL_DYNAMIC_INPUTS:'+','.join(required));s={'freeze':freeze,'load-prepare':load_prepare,'load-arm':load_arm}[a.action](a);need(len(s.encode())<=16384,'USER_PASTE_EXCEEDS16K')
 with a.output.open('x') as out:out.write(s)
 print(json.dumps({'status':'LOCAL_USER_COMMAND_WRITTEN_NOT_EXECUTED','action':a.action,'file':str(a.output),'bytes':len(s.encode()),'sha256':sha(s.encode())}))
if __name__=='__main__':main()
