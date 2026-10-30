from pathlib import Path
import importlib.util,hashlib,json,tempfile,types,copy,ast,sys
D=Path(__file__).resolve().parents[2]/'agents/deployment/final-window'
def module(n,p):s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
f=module('facts',D/'P09-FACTS-CHECK.PUBLIC.py');g=module('commands',D/'P09-USER-COMMANDS.PUBLIC.py');now=f.epoch('2026-10-30T04:00:00Z');g.time.time=lambda:now
app={'kind':'USER_EXECUTED_APP_P09_TOOL_PREPARATION_ONLY','observed_utc':'2026-10-30T03:59:00Z','actual_APP_resume_boot_utc':'2026-10-30T03:40:00Z','NTP_synchronized':'yes','private_ip':'172.21.182.245','profile_sha256':'346d19344281b9e02046a27cf9d24f07ebceb9c8f920105a981d7bfdc056ac1f','actual90b_public_file_shas':{'source-manifest.json':f.SM,'backend-bundle-manifest.json':f.BUNDLE},'backend_alias':'t44-backend:src-'+f.SOURCE,'active_P08_units':'','fresh_window_frozen':False,'tool_derivation':{'status':'P09_TOOLS_PREPARED_ONLY','tools':{'P09-CONTINUOUS-fast10-cap50.PUBLIC.py':'a'*64}}}
files={f.T+'/P09-USER-TRANSPORT-LOAD.PUBLIC.py':{'sha256':'d1ed953dc7c0dd9d048dc3318c27015d3f71968499ba7d17dcd1841422d84601'},f.T+'/P09-SPLUS1-EXEC.PUBLIC.py':{'sha256':'b1e43bc0737f92a341d3e4e7f49d6b4798619d023c6879e5ec031cdb53df6387'},f.T+'/final-transport-profile05.py':{'sha256':'a5425e961f486c78253a6ba319030c86b4057056622882086e686a642e61bc8a'},f.R+'/ops01/qa-public/ENTRY_PERF_753.sh':{'sha256':f.ENTRY},f.R+'/ops01/qa-public/ADAPTER_753.py':{'sha256':f.ADAPTER}}
probe={'uid':10001,'python':'3.12.15','cpu_max':'800000 100000','memory_max':'8589934592','pids_max':'2048','nofile':[4096,4096],'affinity_cpus':16,'t44_absent':True,'business_env_absent':True}
load={'kind':'USER_LOAD_P09_FACTS_ONLY','observed_utc':'2026-10-30T03:59:10Z','actual_LOAD_resume_boot_utc':'2026-10-30T03:41:00Z','NTP_synchronized':'yes','private_ip':'172.21.182.244','actual_image_id':f.IMAGE,'image_descriptor_layers_match':True,'runtime_probe':probe,'active_QA_containers':[],'active_T44_units':'','public_files':files,'PRIVATE_or_plaintext_key_contents_read':False,'QA_or_SUT_requests':0}
for n,h in f.QA_REQUIRED.items():load['public_files'][f.R+'/QA753P07/public/'+n]={'sha256':h}
assert not f.check(app,load,now)['errors'];assert f.check(app,load,now+70)['fresh_for_APP_admission_now'];assert not f.check(app,load,now+70.001)['fresh_for_APP_admission_now']
for key,value in [('NTP_synchronized','no'),('private_ip','172.21.182.245'),('active_QA_containers',[{'name':'qa753-p-old'}]),('actual_image_id','sha256:'+'0'*64)]:
 bad=copy.deepcopy(load);bad[key]=value;assert f.check(app,bad,now)['errors']
bad=copy.deepcopy(load);bad['runtime_probe']['memory_max']='max';assert 'LOAD_LIMIT_memory_max' in f.check(app,bad,now)['errors']
fee={'root_approved':True,'remaining_budget_CNY':50,'historical_APP_first_boot_utc':'2026-10-29T13:45:26Z','resume_observed_utc':'2026-10-30T03:40:00Z','actual_APP_resume_boot_utc':app['actual_APP_resume_boot_utc'],'actual_LOAD_resume_boot_utc':load['actual_LOAD_resume_boot_utc'],'absolute_cost_cutoff_utc':'2026-10-30T05:00:00Z'}
platform={'verification_scope':'CREATED_SCHEDULED_CONFIGURATION_ONLY','platform_task_created':True,'schedule_enabled':True,'task_execution_id':'exec-synthetic123','configured_stopped_mode':'StopCharging','configured_force_stop':False,'target_instance_ids':['i-appsynthetic123','i-loadsynthetic123'],'actual_trigger_observed':False,'platform_permissions_fully_validated':False,'known_warning':'synthetic generic permission warning retained','APP_instance_id':'i-appsynthetic123','LOAD_instance_id':'i-loadsynthetic123','root_verified':True,'APP_stop_retains_disks':True,'LOAD_stop_retains_disks':True,'stop_utc':fee['absolute_cost_cutoff_utc'],'hourly_APP_CNY':12.436,'hourly_LOAD_CNY':3.1405}
def write(p,v):p.write_text(json.dumps(v));return p
def heredoc_syntax(s):assert len(s.encode())<=16384;ast.parse(s.split("<<'USER_P09_COMMAND'\n",1)[1].rsplit('\nUSER_P09_COMMAND',1)[0],feature_version=(3,10))
with tempfile.TemporaryDirectory() as tmp:
 r=Path(tmp);a=types.SimpleNamespace(app_facts=write(r/'app.json',app),load_facts=write(r/'load.json',load),fee=write(r/'fee.json',fee),platform_proof=write(r/'platform.json',platform));s=g.freeze(a);heredoc_syntax(s)
 old=copy.deepcopy(fee);old['resume_observed_utc']='2026-10-29T17:29:00Z';write(a.fee,old)
 try:g.freeze(a);raise AssertionError('expired cost origin accepted')
 except ValueError:pass
 write(a.fee,fee);bad=copy.deepcopy(platform);bad['LOAD_stop_retains_disks']=False;write(a.platform_proof,bad)
 try:g.freeze(a);raise AssertionError('unverified platform stop accepted')
 except ValueError:pass
 for key,value in [('target_instance_ids',['i-othersynthetic123','i-loadsynthetic123']),('configured_force_stop',True),('schedule_enabled',False)]:
  bad=copy.deepcopy(platform);bad[key]=value;write(a.platform_proof,bad)
  try:g.freeze(a);raise AssertionError('invalid scheduled config accepted:'+key)
  except ValueError:pass
 # Exercise original S+1 helper boundary using an exec spy only; no subprocess/cloud/QA calls.
 m=module('splus',D/'P09-SPLUS1-EXEC.PUBLIC.py');entry=r/'entry.sh';entry.write_text('#!/bin/sh\nexit 0\n');grant={'allow':True,'run_id':'r30finalp09','clients':400,'warmup_seconds':60,'steady_seconds':600,'window_start_utc':'2026-10-30T04:10:00Z','window_end_utc':'2026-10-30T04:23:00Z','cost_stop_utc':'2026-10-30T04:30:00Z'};gp=write(r/'grant.json',grant);calls=[];m.os.execv=lambda *args:calls.append(args)
 sys.argv=['x','execute','--entry',str(entry),'--entry-sha256',hashlib.sha256(entry.read_bytes()).hexdigest(),'--workspace',str(r),'--grant-file',str(gp),'--grant-sha256',hashlib.sha256(gp.read_bytes()).hexdigest()]
 start=f.epoch(grant['window_start_utc'])
 for offset,allowed in [(0.999,False),(1,True),(19.999,True),(20,False)]:
  m.time.time=lambda:start+offset;before=len(calls)
  try:m.main();assert allowed
  except ValueError:assert not allowed
  assert (len(calls)>before)==allowed
print('LOCAL SYNTHETIC BOUNDARIES PASSED (scheduled-created configuration accepted with not-triggered and permission-warning preserved): valid facts;120s/120.001 freshness; NTP/IP/activeQA/image/memory negatives; fresh fee script AST<=16KiB; stale fee/unverified platform/OOS target-force-enabled refusal; S+1 edges0.999/1/19.999/20 via exec spy. No cloud, Docker, HTTP or QA executed.')

g.time.time=lambda:now
with tempfile.TemporaryDirectory() as tmp:
 r=Path(tmp);loadfile=write(r/'load.json',load);ir={'source_sha':f.SOURCE,'bundle_manifest_sha256':f.BUNDLE,'source_manifest_sha256':f.SM};ip=write(r/'import.json',ir)
 target={'git_commit':f.SOURCE,'source_manifest_sha256':f.SM,'backend_bundle_manifest_sha256':f.BUNDLE,'sut_image_config_digest':'sha256:47c3383fedcdaa882257ccf2338bfd93fe4d7f67c1bf69b6fda25e3bb159e07a','load_runtime_image_config_digest':f.IMAGE,'runtime_sha256':'81e04666cf05c2932397c5d39521ef881602f3046342e2d4d5605a694e5829bf','openapi_sha256':'6f07cb53a7d9314240ba93ec490325d3c63dca7e4d077021047e216e7b26f478','backend_import_receipt_sha256':hashlib.sha256(ip.read_bytes()).hexdigest()};tp=write(r/'target.json',target);approval={'approved':True,'supports_source':f.SOURCE,'target_profile_sha256':hashlib.sha256(tp.read_bytes()).hexdigest(),'qa_adapter_sha256':f.ADAPTER};ap=write(r/'approval.json',approval)
 clock={'run_id':'r30finalp09','phase':'p','source_sha':f.SOURCE,'t0_utc':'2026-10-30T04:00:00Z','start_utc':'2026-10-30T04:10:00Z','end_utc':'2026-10-30T04:23:00Z','stop_utc':'2026-10-30T04:25:00Z','cost_stop_utc':'2026-10-30T04:30:00Z','packet_cutoff_utc':'2026-10-30T04:07:30Z'}
 import base64
 cr=json.dumps(clock).encode();boot={'timeplan_b64':base64.b64encode(cr).decode(),'timeplan_sha256':hashlib.sha256(cr).hexdigest()};bp=write(r/'bootstrap.json',boot)
 pinfiles={}
 for n in f.QA_REQUIRED:
  path=f.R+'/QA753P07/public/'+n;h=f.QA_REQUIRED[n];pinfiles[n]={'source':path,'sha256':h}
  load['public_files'][path]={'sha256':h}
 write(loadfile,load);pp=write(r/'pins.json',{'root_reviewed':True,'files':pinfiles});a=types.SimpleNamespace(load_facts=loadfile,bootstrap=bp,qa_target=tp,qa_approval=ap,backend_import_receipt=ip,qa_public_pins=pp)
 prep=g.load_prepare(a);heredoc_syntax(prep)
 bad={**approval,'approved':False};write(ap,bad)
 try:g.load_prepare(a);raise AssertionError('unapproved QA accepted')
 except ValueError:pass
 write(ap,approval);badpins=copy.deepcopy(pinfiles);badpins['capsule_tool.py']['source']=f.R+'/PRIVATE/capsule_tool.py';write(pp,{'root_reviewed':True,'files':badpins})
 try:g.load_prepare(a);raise AssertionError('PRIVATE source accepted')
 except ValueError:pass
 receipt={'status':'PREPARED_DEFAULT_FALSE','run_id':'r30finalp09','supports_source':f.SOURCE,'qa_adapter_sha256':f.ADAPTER,'SUT_requests':0,'environment_sha256':'b'*64}
 grant={**copy.deepcopy(g.GRANT_FIXED),'allow':True,'run_id':'r30finalp09','created_at':'2026-10-30T04:07:00Z','origin':'https://172.21.182.245:26445','window_start_utc':clock['start_utc'],'window_end_utc':clock['end_utc'],'cost_stop_utc':clock['cost_stop_utc'],'environment_sha256':'b'*64,'runtime_sha256':target['runtime_sha256'],'source_sha256':f.SM,'image_digest':target['sut_image_config_digest'],'fixture_sha256':'c'*64}
 default={**grant,'allow':False};default_raw=(json.dumps(default,ensure_ascii=False,separators=(',',':'),sort_keys=True)+'\n').encode();default_info={'original_b64':base64.b64encode(default_raw).decode(),'sha256':hashlib.sha256(default_raw).hexdigest(),'grant':default}
 rp=write(r/'prepare.json',{'prepare':receipt,'splus1_helper':{'path':f.T+'/P09-SPLUS1-EXEC.PUBLIC.py','sha256':'b1e43bc0737f92a341d3e4e7f49d6b4798619d023c6879e5ec031cdb53df6387'},'default_false_grant_original':default_info});gp=write(r/'grant.json',grant);a=types.SimpleNamespace(load_facts=loadfile,grant=gp,prepare_receipt=rp);arm=g.load_arm(a);heredoc_syntax(arm)
 for key in g.GRANT_KEYS:
  truncated=copy.deepcopy(grant);truncated.pop(key);write(gp,truncated)
  try:g.load_arm(a);raise AssertionError('truncated grant accepted:'+key)
  except ValueError:pass
 extra={**grant,'unexpected_extra':'not-original'};write(gp,extra)
 try:g.load_arm(a);raise AssertionError('extra grant field accepted')
 except ValueError:pass
 for key,value in [('origin','https://172.21.182.245:9999'),('created_at','2026-10-30T04:07:01Z'),('fixture_sha256','d'*64),('request_timeout_seconds',14),('postcheck_seconds',39),('permissions',[]),('prohibitions',[]),('limits',{})]:
  changed=copy.deepcopy(grant);changed[key]=value;write(gp,changed)
  try:g.load_arm(a);raise AssertionError('changed grant accepted:'+key)
  except ValueError:pass
 write(gp,grant);bad_info={**default_info,'sha256':'0'*64};write(rp,{'prepare':receipt,'default_false_grant_original':bad_info})
 try:g.load_arm(a);raise AssertionError('wrong original default SHA accepted')
 except ValueError:pass
 write(rp,{'prepare':receipt,'splus1_helper':{'path':f.T+'/P09-SPLUS1-EXEC.PUBLIC.py','sha256':'b1e43bc0737f92a341d3e4e7f49d6b4798619d023c6879e5ec031cdb53df6387'}});dp=r/'default-original.json';dp.write_bytes(default_raw);a.default_false_grant=dp;a.default_false_grant_sha256=hashlib.sha256(default_raw).hexdigest();heredoc_syntax(g.load_arm(a));a.default_false_grant=None;a.default_false_grant_sha256=None
 write(rp,{'prepare':receipt,'splus1_helper':{'path':f.T+'/P09-SPLUS1-EXEC.PUBLIC.py','sha256':'b1e43bc0737f92a341d3e4e7f49d6b4798619d023c6879e5ec031cdb53df6387'},'default_false_grant_original':default_info})
 print('LOCAL COMPLETE-GRANT TESTS PASSED: exact original21 fields with only allow flip accepted; each missing field, extra field, changed origin/created/fixture/timeout/postcheck/limits/permissions/prohibitions and wrong raw SHA rejected; existing CLI plus optional original-default-file recovery validated. No arm executed.')
 grant['allow']=False;write(gp,grant)
 try:g.load_arm(a);raise AssertionError('false grant accepted')
 except ValueError:pass
 grant['allow']=True;write(gp,grant);g.time.time=lambda:f.epoch(clock['start_utc'])-29.999
 try:g.load_arm(a);raise AssertionError('late arm accepted')
 except ValueError:pass
 print('LOCAL GENERATOR TESTS PASSED: LOAD prepare/arm original-approval paths generated and AST<=16KiB; rejects QA approvedfalse, PRIVATE tool source, allowfalse grant and S-29.999 late arm. No generated command executed.')
# Execute collector's real loop with virtual clock/subprocess-only spies, including >180s.
import contextlib,io,base64,zlib
c=module('collector',D/'P09-USER-APP-COLLECT.PUBLIC.py');u=module('unpack',D/'P09-COLLECT-UNPACK.PUBLIC.py')
with tempfile.TemporaryDirectory()as tmp:
 r=Path(tmp);c.R=r;c.F=r/'P09';c.F.mkdir();c.run=lambda argv:b''
 clock={'run_id':'r30finalp09','start_utc':'2026-10-30T04:10:00Z'}
 originals={'preparation.PUBLIC.json':b'{"status":"PREPARING"}\n','timeplan.PUBLIC.json':json.dumps(clock).encode(),'backend-import-receipt.PUBLIC.json':b'{"source_sha":"original"}\n','LOAD-bootstrap.original.PUBLIC.json':b'{"packet":"original"}\n'}
 for n,b in originals.items():
  if n!=c.PUBLIC[3]:(c.F/n).write_bytes(b)
 tick=[0];c.time.monotonic=lambda:tick[0];c.time.time=lambda:now+tick[0]
 def sleep(seconds):
  tick[0]+=seconds
  if tick[0]==365:(c.F/c.PUBLIC[3]).write_text('{') # partial file must not abort observer
  if tick[0]>=366:(c.F/c.PUBLIC[3]).write_bytes(originals[c.PUBLIC[3]])
 c.time.sleep=sleep;sys.argv=['collector','--wait-seconds','600'];out=io.StringIO()
 with contextlib.redirect_stdout(out):c.main()
 lines=out.getvalue().splitlines();assert len(lines)==3 and json.loads(lines[0])['event']=='EARLY_PUBLIC_MATERIAL' and json.loads(lines[-1])['event']=='BOOTSTRAP_READY' and tick[0]==366
 dest=r/'decoded'
 for line in lines:u.unpack(line,dest)
 assert all((dest/n).read_bytes()==b for n,b in originals.items())
 bad=json.loads(lines[-1]);bad['files'][c.PUBLIC[0]]['sha256']='0'*64
 try:u.unpack(json.dumps(bad),r/'bad');raise AssertionError('bad original sha accepted')
 except ValueError:pass
 (c.F/c.PUBLIC[3]).unlink();tick[0]=0;c.time.sleep=lambda seconds:tick.__setitem__(0,tick[0]+seconds);out=io.StringIO();sys.argv=['collector','--wait-seconds','600']
 with contextlib.redirect_stdout(out):c.main()
 assert tick[0]==570 and json.loads(out.getvalue().splitlines()[-1])['event']=='PREPARATION_MARGIN_EXPIRED_NO_OVERRIDE'
 tick[0]=0;out=io.StringIO();sys.argv=['collector','--wait-seconds','20']
 with contextlib.redirect_stdout(out):c.main()
 assert tick[0]==20 and json.loads(out.getvalue().splitlines()[-1])['event']=='WAIT_TIMEOUT_PENDING_NO_RETRY'
 (c.F/c.PUBLIC[3]).write_bytes(originals[c.PUBLIC[3]]);tick[0]=571;out=io.StringIO()
 with contextlib.redirect_stdout(out):c.main()
 assert json.loads(out.getvalue().splitlines()[-1])['event']=='BOOTSTRAP_PRESENT_TOO_LATE_NO_OVERRIDE'
 # truncated first-file JSON is represented pending, never decoded/treated ready.
 (c.F/c.PUBLIC[0]).write_text('{');tick[0]=0;sys.argv=['collector','--wait-seconds','0'];out=io.StringIO()
 with contextlib.redirect_stdout(out):c.main()
 assert json.loads(out.getvalue().splitlines()[0])['files'][c.PUBLIC[0]]['status']=='PENDING_INCOMPLETE_OR_INVALID_JSON'
 assert not any(x in c.FMT for x in ['.Config.Env','.Config.Cmd','.Config.Entrypoint'])
print('LOCAL COLLECTOR REAL-LOOP PASSED: early flush JSONL; ready at virtual366s (>180,<600); partially-written bootstrap at365 handled; both original lines unpack byteexact; badSHA, missing/timeout, S-30 expiry, late bootstrap, truncated JSON rejected/pending. Docker/systemctl spies only, no cloud or QA.')
# Pure derivation function is executed against fixture bytes; actual disk preimage pins remain unchanged in delivery.
d=module('derive',D/'P09-DERIVE-TOOLS.PUBLIC.py')
with tempfile.TemporaryDirectory()as tmp:
 r=Path(tmp);d.R=r;d.T=r/'tools';d.T.mkdir();d.PINS={}
 for name in ['P08-CONTINUOUS-fast10-cap50.PUBLIC.py','final-app-prepare-pfast08-cap50.py','final-image-bundle-pfast08-cap50.py','final-timeplan-pfast08-cap50.py']:
  text="from pathlib import Path\nR=Path('/root/t44-final-20261029')\nrun='r30finalp08'\noutput=R/'P08'\nhelper='final-app-prepare-pfast08-cap50.py'\nprevious=R/'P07/campaign/p'\nproject='t44-cloud-r30finalp07-p'\nunit='t44-final-p07*'\n"
  (d.T/name).write_text(text);d.PINS[name]=hashlib.sha256(text.encode()).hexdigest()
 out=d.derive();assert len(out['tools'])==4
 launcher=(d.T/'P09-CONTINUOUS-fast10-cap50.PUBLIC.py').read_text();assert "previous=R/'P08/campaign/p'" in launcher and "output=R/'P09'"in launcher and 't44-final-p08*'in launcher
 assert d.derive()==out # tool staging idempotence only, no freeze replay
 (d.R/'P09').mkdir()
 try:d.derive();raise AssertionError('new attempt replay accepted')
 except ValueError:pass
print('LOCAL DERIVER REAL-FUNCTION PASSED using explicit fixture pins: 4 tools, exact previousowner P08, helper/run/output P09, idempotent same-byte staging and attempt replay refusal. Actual deployed4 preimage hashes remain authoritative; cloud bytes not fetched/executed.')
# Complete neutral receipt flow: collector lines→raw bootstrap/import→generator→defaultgrant diff→arm.
# Reuse actual generator functions with synthetic public inputs; original QA entry not invoked.
with tempfile.TemporaryDirectory()as tmp:
 r=Path(tmp);g.time.time=lambda:now
 clock={'run_id':'r30finalp09','phase':'p','source_sha':f.SOURCE,'t0_utc':'2026-10-30T04:00:00Z','start_utc':'2026-10-30T04:10:00Z','end_utc':'2026-10-30T04:23:00Z','stop_utc':'2026-10-30T04:25:00Z','cost_stop_utc':'2026-10-30T04:30:00Z','packet_cutoff_utc':'2026-10-30T04:07:30Z'}
 cr=json.dumps(clock).encode();boot={'timeplan_b64':base64.b64encode(cr).decode(),'timeplan_sha256':g.sha(cr)};receipt={'source_sha':f.SOURCE,'source_manifest_sha256':f.SM,'bundle_manifest_sha256':f.BUNDLE}
 rawfiles={'preparation.PUBLIC.json':b'{"status":"READY"}','timeplan.PUBLIC.json':cr,'backend-import-receipt.PUBLIC.json':json.dumps(receipt).encode(),'LOAD-bootstrap.original.PUBLIC.json':json.dumps(boot).encode()}
 def record(event,names):return {'kind':'USER_P09_PUBLIC_COLLECTOR','event':event,'files':{n:{'status':'PRESENT','bytes':len(rawfiles[n]),'sha256':g.sha(rawfiles[n]),'zlib_b64':base64.b64encode(zlib.compress(rawfiles[n])).decode()}for n in names}}
 dest=r/'unpacked';u.unpack(json.dumps(record('EARLY_PUBLIC_MATERIAL',list(rawfiles)[:3])),dest);u.unpack(json.dumps(record('BOOTSTRAP_READY',rawfiles)),dest)
 target={'git_commit':f.SOURCE,'source_manifest_sha256':f.SM,'backend_bundle_manifest_sha256':f.BUNDLE,'sut_image_config_digest':'sha256:47c3383fedcdaa882257ccf2338bfd93fe4d7f67c1bf69b6fda25e3bb159e07a','load_runtime_image_config_digest':f.IMAGE,'runtime_sha256':'81e04666cf05c2932397c5d39521ef881602f3046342e2d4d5605a694e5829bf','openapi_sha256':'6f07cb53a7d9314240ba93ec490325d3c63dca7e4d077021047e216e7b26f478','backend_import_receipt_sha256':g.sha(rawfiles['backend-import-receipt.PUBLIC.json'])}
 tp=write(r/'target',target);ap=write(r/'approval',{'approved':True,'supports_source':f.SOURCE,'target_profile_sha256':g.sha(tp.read_bytes()),'qa_adapter_sha256':f.ADAPTER});lp=write(r/'load',load);pins=write(r/'pins',{'root_reviewed':True,'files':{n:{'source':f.R+'/QA753P07/public/'+n,'sha256':h}for n,h in f.QA_REQUIRED.items()}})
 a=types.SimpleNamespace(load_facts=lp,bootstrap=dest/'LOAD-bootstrap.original.PUBLIC.json',qa_target=tp,qa_approval=ap,backend_import_receipt=dest/'backend-import-receipt.PUBLIC.json',qa_public_pins=pins)
 script=g.load_prepare(a);heredoc_syntax(script);assert 'splus1_helper'in script and 'P09-SPLUS1' not in script # names are inside pinned compressed payload
 payload=json.loads(zlib.decompress(base64.b64decode(script.split('blob=base64.b64decode(',1)[1].split(');assert',1)[0].strip("'"))));assert g.sha(g.original(payload['splus1'])) if hasattr(g,'original')else payload['splus1']['sha256']=='b1e43bc0737f92a341d3e4e7f49d6b4798619d023c6879e5ec031cdb53df6387'
 # Fields returned by original prepare remain exact original neutral schema, no adapter execution simulated as pass.
 pr={'status':'PREPARED_DEFAULT_FALSE','run_id':'r30finalp09','supports_source':f.SOURCE,'qa_adapter_sha256':f.ADAPTER,'SUT_requests':0,'environment_sha256':'b'*64}
 grant={**copy.deepcopy(g.GRANT_FIXED),'allow':False,'run_id':'r30finalp09','created_at':'2026-10-30T04:07:00Z','origin':'https://172.21.182.245:26445','window_start_utc':clock['start_utc'],'window_end_utc':clock['end_utc'],'cost_stop_utc':clock['cost_stop_utc'],'environment_sha256':'b'*64,'runtime_sha256':target['runtime_sha256'],'source_sha256':f.SM,'image_digest':target['sut_image_config_digest'],'fixture_sha256':'c'*64};dr=json.dumps(grant).encode();returned={'prepare':pr,'default_false_grant_original':{'original_b64':base64.b64encode(dr).decode(),'sha256':g.sha(dr)},'splus1_helper':{'path':f.T+'/P09-SPLUS1-EXEC.PUBLIC.py','sha256':payload['splus1']['sha256']}}
 rp=write(r/'prepared',returned);gp=write(r/'grant',{**grant,'allow':True});arm=g.load_arm(types.SimpleNamespace(load_facts=lp,grant=gp,prepare_receipt=rp));heredoc_syntax(arm)
 returned['splus1_helper']['sha256']='0'*64;write(rp,returned)
 try:g.load_arm(types.SimpleNamespace(load_facts=lp,grant=gp,prepare_receipt=rp));raise AssertionError('prepare helper tamper accepted')
 except ValueError:pass
print('LOCAL RECEIPT CHAIN PASSED: two original JSONL rows→byteexact import/bootstrap→LOADprepare generation embedding helper→original21-field default diff→SPLUS1 arm generation; helper tamper blocked. Only generators executed, no generated cloud/INSTALL/790/QA command executed.')
# Execute real generated boot guard prefixes (not cloud commands), same/changed btime.
import datetime
for fn,expected_key in [(g.freeze,'actual_APP_resume_boot_utc'),(g.load_prepare,'expected_LOAD_boot_utc')]:
 body=next(x for x in fn.__code__.co_consts if isinstance(x,str)and 'CURRENT_'in x and 'current_boot='in x)
 prefix=body[:body.index("assert not Path(")]if fn==g.freeze else body[:body.index('assert time.time()')]
 class Proc:
  def read_text(self):return 'cpu 0\nbtime '+str(int(f.epoch('2026-10-30T03:40:00Z')))+'\n'
 def pathonly(name):assert name=='/proc/stat';return Proc()
 for seconds,allowed in [(0,True),(1,False)]:
  expected=datetime.datetime.fromtimestamp(f.epoch('2026-10-30T03:40:00Z')+seconds,datetime.timezone.utc).isoformat();dd={'fee':{'actual_APP_resume_boot_utc':expected},'expected_LOAD_boot_utc':expected}
  ns={'D':dd,'Path':pathonly,'datetime':datetime,'json':json,'original':lambda item:json.dumps(item).encode()}
  try:exec(prefix,ns);assert allowed
  except AssertionError as e:
   if allowed:raise
   assert 'CURRENT_'in str(e)
 assert body.index('current_boot=')<body.index('put(')
print('LOCAL GENERATED BOOT-GUARD PREFIXES PASSED: same btime accepts, changed APP/LOAD btime rejects before any put/stop/dispatch. No generated lifecycle or QA command executed.')
# Real collector subprocess wrapper shares S-30 deadline, catches timeout; immediate line precedes subprocess.
c=module('collector_timeout',D/'P09-USER-APP-COLLECT.PUBLIC.py')
with tempfile.TemporaryDirectory()as tmp:
 c.F=Path(tmp);tick=[0];c.time.monotonic=lambda:tick[0];c.time.time=lambda:now+tick[0];c.time.sleep=lambda seconds:tick.__setitem__(0,tick[0]+seconds)
 clock={'run_id':'r30finalp09','start_utc':datetime.datetime.fromtimestamp(now+38,datetime.timezone.utc).isoformat()}
 for n,v in [('preparation.PUBLIC.json',{'status':'PREPARING'}),('timeplan.PUBLIC.json',clock),('backend-import-receipt.PUBLIC.json',{})]:(c.F/n).write_text(json.dumps(v))
 for rel in ['P-counts/output/result/counts.json','P-http/output/result/factual-snapshots.json']:
  p=c.F/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('{')
 out=io.StringIO();calls=[];original_run=c.subprocess.run
 def timeout(argv,**kwargs):
  assert out.getvalue().splitlines() and json.loads(out.getvalue().splitlines()[0])['event']=='EARLY_PUBLIC_MATERIAL'
  calls.append((argv,kwargs['timeout']));tick[0]+=kwargs['timeout'];raise c.subprocess.TimeoutExpired(argv,kwargs['timeout'])
 c.subprocess.run=timeout;sys.argv=['collector','--wait-seconds','600']
 try:
  with contextlib.redirect_stdout(out):c.main()
 finally:c.subprocess.run=original_run
 rows=[json.loads(x)for x in out.getvalue().splitlines()];assert tick[0]==8 and [x[1]for x in calls]==[5,3]
 assert rows[-1]['event']=='PREPARATION_MARGIN_EXPIRED_NO_OVERRIDE';assert rows[-1]['metadata_status']=='UNKNOWN_PARTIAL'
 assert rows[-1]['DB_readback_records']['seeded']['status']=='PENDING_INCOMPLETE_OR_REFUSED_NEUTRAL_JSON'and rows[-1]['scope']['status']=='PENDING_INCOMPLETE_OR_REFUSED_NEUTRAL_JSON'
 assert all(x[0][:4]!=['docker','--context','default','inspect']or '--format'in x[0]for x in calls)
print('LOCAL SHARED DEADLINE REAL-WRAPPER PASSED: PUBLIC flush precedes subprocess; timeout5+3 exhausts shared S-30 8s budget and records UNKNOWN; no uncaught TimeoutExpired, no134s serial inspections; truncated DB/scope pending. Pure subprocess spies only.')
