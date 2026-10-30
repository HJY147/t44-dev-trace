from pathlib import Path
import importlib.util,hashlib,json,tempfile,types,copy,ast,sys
D=Path(__file__).resolve().parents[1]
def module(n,p):s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
f=module('facts',D/'P08-FACTS-CHECK.PUBLIC.py');g=module('commands',D/'P08-USER-COMMANDS.PUBLIC.py');now=f.epoch('2026-10-30T04:00:00Z');g.time.time=lambda:now
app={'kind':'USER_EXECUTED_APP_P08_TOOL_PREPARATION_ONLY','observed_utc':'2026-10-30T03:59:00Z','actual_APP_resume_boot_utc':'2026-10-30T03:40:00Z','NTP_synchronized':'yes','private_ip':'172.21.182.245','profile_sha256':'346d19344281b9e02046a27cf9d24f07ebceb9c8f920105a981d7bfdc056ac1f','actual90b_public_file_shas':{'source-manifest.json':f.SM,'backend-bundle-manifest.json':f.BUNDLE},'backend_alias':'t44-backend:src-'+f.SOURCE,'active_P07_units':'','fresh_window_frozen':False,'tool_derivation':{'status':'P08_TOOLS_PREPARED_ONLY','tools':{'P08-CONTINUOUS-fast10-cap50.PUBLIC.py':'a'*64}}}
files={f.T+'/P08-USER-TRANSPORT-LOAD.PUBLIC.py':{'sha256':'d1ed953dc7c0dd9d048dc3318c27015d3f71968499ba7d17dcd1841422d84601'},f.T+'/P08-SPLUS1-EXEC.PUBLIC.py':{'sha256':'7cba1f0cd9925ba92da12849e4789af8378d1fe870698be02be292017796bb02'},f.T+'/final-transport-profile05.py':{'sha256':'a5425e961f486c78253a6ba319030c86b4057056622882086e686a642e61bc8a'},f.R+'/ops01/qa-public/ENTRY_PERF_753.sh':{'sha256':f.ENTRY},f.R+'/ops01/qa-public/ADAPTER_753.py':{'sha256':f.ADAPTER}}
probe={'uid':10001,'python':'3.12.15','cpu_max':'800000 100000','memory_max':'8589934592','pids_max':'2048','nofile':[4096,4096],'affinity_cpus':16,'t44_absent':True,'business_env_absent':True}
load={'kind':'USER_LOAD_P08_FACTS_ONLY','observed_utc':'2026-10-30T03:59:10Z','actual_LOAD_resume_boot_utc':'2026-10-30T03:41:00Z','NTP_synchronized':'yes','private_ip':'172.21.182.244','actual_image_id':f.IMAGE,'image_descriptor_layers_match':True,'runtime_probe':probe,'active_QA_containers':[],'active_T44_units':'','public_files':files,'PRIVATE_or_key_contents_read':False,'QA_or_SUT_requests':0}
assert not f.check(app,load,now)['errors'];assert f.check(app,load,now+70)['fresh_for_APP_admission_now'];assert not f.check(app,load,now+70.001)['fresh_for_APP_admission_now']
for key,value in [('NTP_synchronized','no'),('private_ip','172.21.182.245'),('active_QA_containers',[{'name':'qa753-p-old'}]),('actual_image_id','sha256:'+'0'*64)]:
 bad=copy.deepcopy(load);bad[key]=value;assert f.check(app,bad,now)['errors']
bad=copy.deepcopy(load);bad['runtime_probe']['memory_max']='max';assert 'LOAD_LIMIT_memory_max' in f.check(app,bad,now)['errors']
fee={'root_approved':True,'remaining_budget_CNY':50,'historical_APP_first_boot_utc':'2026-10-29T13:45:26Z','resume_observed_utc':'2026-10-30T03:40:00Z','actual_APP_resume_boot_utc':app['actual_APP_resume_boot_utc'],'actual_LOAD_resume_boot_utc':load['actual_LOAD_resume_boot_utc'],'absolute_cost_cutoff_utc':'2026-10-30T05:00:00Z'}
platform={'APP_instance_id':'i-appsynthetic123','LOAD_instance_id':'i-loadsynthetic123','root_verified':True,'APP_stop_retains_disks':True,'LOAD_stop_retains_disks':True,'stop_utc':fee['absolute_cost_cutoff_utc'],'hourly_APP_CNY':12.436,'hourly_LOAD_CNY':3.1405}
def write(p,v):p.write_text(json.dumps(v));return p
def heredoc_syntax(s):assert len(s.encode())<=16384;ast.parse(s.split("<<'USER_P08_COMMAND'\n",1)[1].rsplit('\nUSER_P08_COMMAND',1)[0],feature_version=(3,10))
with tempfile.TemporaryDirectory() as tmp:
 r=Path(tmp);a=types.SimpleNamespace(app_facts=write(r/'app.json',app),load_facts=write(r/'load.json',load),fee=write(r/'fee.json',fee),platform_proof=write(r/'platform.json',platform));s=g.freeze(a);heredoc_syntax(s)
 old=copy.deepcopy(fee);old['resume_observed_utc']='2026-10-29T17:29:00Z';write(a.fee,old)
 try:g.freeze(a);raise AssertionError('expired cost origin accepted')
 except ValueError:pass
 write(a.fee,fee);bad=copy.deepcopy(platform);bad['LOAD_stop_retains_disks']=False;write(a.platform_proof,bad)
 try:g.freeze(a);raise AssertionError('unverified platform stop accepted')
 except ValueError:pass
 # Exercise original S+1 helper boundary using an exec spy only; no subprocess/cloud/QA calls.
 m=module('splus',D/'P08-SPLUS1-EXEC.PUBLIC.py');entry=r/'entry.sh';entry.write_text('#!/bin/sh\nexit 0\n');grant={'allow':True,'run_id':'r30finalp08','clients':400,'warmup_seconds':60,'steady_seconds':600,'window_start_utc':'2026-10-30T04:10:00Z','window_end_utc':'2026-10-30T04:23:00Z','cost_stop_utc':'2026-10-30T04:30:00Z'};gp=write(r/'grant.json',grant);calls=[];m.os.execv=lambda *args:calls.append(args)
 sys.argv=['x','execute','--entry',str(entry),'--entry-sha256',hashlib.sha256(entry.read_bytes()).hexdigest(),'--workspace',str(r),'--grant-file',str(gp),'--grant-sha256',hashlib.sha256(gp.read_bytes()).hexdigest()]
 start=f.epoch(grant['window_start_utc'])
 for offset,allowed in [(0.999,False),(1,True),(19.999,True),(20,False)]:
  m.time.time=lambda:start+offset;before=len(calls)
  try:m.main();assert allowed
  except ValueError:assert not allowed
  assert (len(calls)>before)==allowed
print('LOCAL SYNTHETIC BOUNDARIES PASSED: valid facts;120s/120.001 freshness; NTP/IP/activeQA/image/memory negatives; fresh fee script AST<=16KiB; stale fee/unverified platform refusal; S+1 edges0.999/1/19.999/20 via exec spy. No cloud, Docker, HTTP or QA executed.')

g.time.time=lambda:now
with tempfile.TemporaryDirectory() as tmp:
 r=Path(tmp);loadfile=write(r/'load.json',load);ir={'source_sha':f.SOURCE,'bundle_manifest_sha256':f.BUNDLE,'source_manifest_sha256':f.SM};ip=write(r/'import.json',ir)
 target={'git_commit':f.SOURCE,'source_manifest_sha256':f.SM,'backend_bundle_manifest_sha256':f.BUNDLE,'sut_image_config_digest':'sha256:47c3383fedcdaa882257ccf2338bfd93fe4d7f67c1bf69b6fda25e3bb159e07a','load_runtime_image_config_digest':f.IMAGE,'runtime_sha256':'81e04666cf05c2932397c5d39521ef881602f3046342e2d4d5605a694e5829bf','openapi_sha256':'6f07cb53a7d9314240ba93ec490325d3c63dca7e4d077021047e216e7b26f478','backend_import_receipt_sha256':hashlib.sha256(ip.read_bytes()).hexdigest()};tp=write(r/'target.json',target);approval={'approved':True,'supports_source':f.SOURCE,'target_profile_sha256':hashlib.sha256(tp.read_bytes()).hexdigest(),'qa_adapter_sha256':f.ADAPTER};ap=write(r/'approval.json',approval)
 clock={'run_id':'r30finalp08','phase':'p','source_sha':f.SOURCE,'t0_utc':'2026-10-30T04:00:00Z','start_utc':'2026-10-30T04:10:00Z','end_utc':'2026-10-30T04:23:00Z','stop_utc':'2026-10-30T04:25:00Z','cost_stop_utc':'2026-10-30T04:30:00Z','packet_cutoff_utc':'2026-10-30T04:07:30Z'}
 import base64
 cr=json.dumps(clock).encode();boot={'timeplan_b64':base64.b64encode(cr).decode(),'timeplan_sha256':hashlib.sha256(cr).hexdigest()};bp=write(r/'bootstrap.json',boot)
 pinfiles={}
 for n in ['ADAPTER_753.py','ENTRY_PERF_753.sh','INSTALL_753.sh','capsule_tool.py','tool-manifest.json','tools.753capsule','transport-key.rsa-oaep-sha256']:
  path=f.R+'/QA753P07/public/'+n;h={'ADAPTER_753.py':f.ADAPTER,'ENTRY_PERF_753.sh':f.ENTRY,'transport-key.rsa-oaep-sha256':'19609563d296299deb7aa0a04a95abbe32ecbae7e7cf5161728e0866a6fc61f5'}.get(n,'e'*64);pinfiles[n]={'source':path,'sha256':h}
  if n!='transport-key.rsa-oaep-sha256':load['public_files'][path]={'sha256':h}
 write(loadfile,load);pp=write(r/'pins.json',{'root_reviewed':True,'files':pinfiles});a=types.SimpleNamespace(load_facts=loadfile,bootstrap=bp,qa_target=tp,qa_approval=ap,backend_import_receipt=ip,qa_public_pins=pp)
 prep=g.load_prepare(a);heredoc_syntax(prep)
 bad={**approval,'approved':False};write(ap,bad)
 try:g.load_prepare(a);raise AssertionError('unapproved QA accepted')
 except ValueError:pass
 write(ap,approval);badpins=copy.deepcopy(pinfiles);badpins['capsule_tool.py']['source']=f.R+'/PRIVATE/capsule_tool.py';write(pp,{'root_reviewed':True,'files':badpins})
 try:g.load_prepare(a);raise AssertionError('PRIVATE source accepted')
 except ValueError:pass
 receipt={'status':'PREPARED_DEFAULT_FALSE','run_id':'r30finalp08','supports_source':f.SOURCE,'qa_adapter_sha256':f.ADAPTER,'SUT_requests':0,'environment_sha256':'b'*64};rp=write(r/'prepare.json',{'prepare':receipt})
 grant={'schema':'772-grant-v1','allow':True,'run_id':'r30finalp08','clients':400,'warmup_seconds':60,'steady_seconds':600,'window_start_utc':clock['start_utc'],'window_end_utc':clock['end_utc'],'cost_stop_utc':clock['cost_stop_utc'],'environment_sha256':'b'*64,'runtime_sha256':target['runtime_sha256'],'source_sha256':f.SM,'image_digest':target['sut_image_config_digest']};gp=write(r/'grant.json',grant);a=types.SimpleNamespace(load_facts=loadfile,grant=gp,prepare_receipt=rp);arm=g.load_arm(a);heredoc_syntax(arm)
 grant['allow']=False;write(gp,grant)
 try:g.load_arm(a);raise AssertionError('false grant accepted')
 except ValueError:pass
 grant['allow']=True;write(gp,grant);g.time.time=lambda:f.epoch(clock['start_utc'])-29.999
 try:g.load_arm(a);raise AssertionError('late arm accepted')
 except ValueError:pass
 print('LOCAL GENERATOR TESTS PASSED: LOAD prepare/arm original-approval paths generated and AST<=16KiB; rejects QA approvedfalse, PRIVATE tool source, allowfalse grant and S-29.999 late arm. No generated command executed.')
