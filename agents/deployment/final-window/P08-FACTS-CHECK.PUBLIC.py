"""Local automatic comparison of user-returned public APP/LOAD facts; no cloud or QA execution."""
import argparse,datetime,hashlib,json,re
from pathlib import Path
R='/root/t44-final-20261029';T=R+'/ops01/deployment/cloud-reuse'
IMAGE='sha256:4f3baf081863a4580b5608699d9a7a8af2d89c3e87abbb60089b630b9102b2a1';SOURCE='90b734f65ce6ee9f5c217e885bc7ea4857e32b48'
SM='501cda41825b84a5d036a702c7e6e7a4750f73614433378ee8cb7b32b590df2e';BUNDLE='72962423358660cf206c4651681b0994f61dc911867805ac5043615db8830b8c'
ENTRY='747e6ca90dbd02fa5629f67b94b167e0fe82006590ac71122af509be43ff79ca';ADAPTER='15b91449627218b011fff0768b1f84fe2e9274ec06c0486fd28f2ae9dce03f5d'
def epoch(s):
 d=datetime.datetime.fromisoformat(s.replace('Z','+00:00'))
 if d.tzinfo is None or d.utcoffset()!=datetime.timedelta(0):raise ValueError('EXPLICIT_UTC_REQUIRED')
 return d.timestamp()
def load_facts(p):
 raw=Path(p).read_bytes();v=json.loads(raw)
 if 'public_facts' in v:
  facts=v['public_facts'];original=(json.dumps(facts,sort_keys=True,indent=2)+'\n').encode()
  if hashlib.sha256(original).hexdigest()!=v['sha256']:raise ValueError('USER_ORIGINAL_FACTS_SHA_MISMATCH')
  return facts,v['sha256']
 return v,hashlib.sha256(raw).hexdigest()
def check(app,load,now=None):
 now=datetime.datetime.now(datetime.timezone.utc).timestamp() if now is None else now;errors=[]
 def need(ok,code):
  if not ok:errors.append(code)
 need(app.get('kind')=='USER_EXECUTED_APP_P08_TOOL_PREPARATION_ONLY','APP_FACT_SCHEMA');need(load.get('kind')=='USER_LOAD_P08_FACTS_ONLY','LOAD_FACT_SCHEMA')
 for role,v,key in [('APP',app,'actual_APP_resume_boot_utc'),('LOAD',load,'actual_LOAD_resume_boot_utc')]:
  try:
   observed=epoch(v['observed_utc']);boot=epoch(v[key]);need(boot<=observed<=now+5,role+'_BOOT_OBSERVATION_ORDER')
  except (KeyError,ValueError,TypeError):errors.append(role+'_UTC_FACTS_INVALID')
  need(v.get('NTP_synchronized')=='yes',role+'_NTP_NOT_SYNCED')
 need(app.get('private_ip')=='172.21.182.245','APP_PRIVATE_IP_CHANGED');need(load.get('private_ip')=='172.21.182.244','LOAD_PRIVATE_IP_CHANGED')
 need(app.get('profile_sha256')=='346d19344281b9e02046a27cf9d24f07ebceb9c8f920105a981d7bfdc056ac1f','APP_PROFILE_CHANGED')
 refs=app.get('actual90b_public_file_shas',{});need(refs.get('source-manifest.json')==SM and refs.get('backend-bundle-manifest.json')==BUNDLE,'APP_90B_MANIFESTS_CHANGED')
 need(app.get('backend_alias')=='t44-backend:src-'+SOURCE,'APP_ALIAS_CHANGED');need(not app.get('active_P07_units'),'OLD_APP_P07_ACTIVE');need(app.get('fresh_window_frozen') is False,'P08_ALREADY_FROZEN')
 tools=app.get('tool_derivation',{});need(tools.get('status','').startswith('P08_TOOLS_PREPARED'),'P08_TOOLS_NOT_DERIVED');need(bool(re.fullmatch('[0-9a-f]{64}',tools.get('tools',{}).get('P08-CONTINUOUS-fast10-cap50.PUBLIC.py',''))),'CAP50_LAUNCHER_PIN_MISSING')
 need(load.get('actual_image_id')==IMAGE and load.get('image_descriptor_layers_match') is True,'LOAD_IMAGE_IDENTITY_CHANGED');need(load.get('active_QA_containers')==[],'LOAD_QA_ACTIVE');need(not load.get('active_T44_units'),'LOAD_T44_ACTOR_UNITS_REVIEW_REQUIRED');need(load.get('PRIVATE_or_key_contents_read') is False and load.get('QA_or_SUT_requests')==0,'LOAD_FACTS_SCOPE_INVALID')
 probe=load.get('runtime_probe') or {}
 for k,val in {'uid':10001,'cpu_max':'800000 100000','memory_max':'8589934592','pids_max':'2048','nofile':[4096,4096],'t44_absent':True,'business_env_absent':True}.items():need(probe.get(k)==val,'LOAD_LIMIT_'+k)
 need(probe.get('python','').startswith('3.12.'),'LOAD_PYTHON_VERSION');need(isinstance(probe.get('affinity_cpus'),int) and probe.get('affinity_cpus',0)>=8,'LOAD_AFFINITY')
 files=load.get('public_files',{})
 for name,pin in [('ENTRY_PERF_753.sh',ENTRY),('ADAPTER_753.py',ADAPTER)]:need(any(Path(path).name==name and row.get('sha256')==pin for path,row in files.items()),'LOAD_PUBLIC_'+name)
 for name,pin in [('final-transport-profile05.py','a5425e961f486c78253a6ba319030c86b4057056622882086e686a642e61bc8a'),('P08-USER-TRANSPORT-LOAD.PUBLIC.py','d1ed953dc7c0dd9d048dc3318c27015d3f71968499ba7d17dcd1841422d84601'),('P08-SPLUS1-EXEC.PUBLIC.py','7cba1f0cd9925ba92da12849e4789af8378d1fe870698be02be292017796bb02')]:need(files.get(T+'/'+name,{}).get('sha256')==pin,'LOAD_TOOL_'+name)
 age=None
 try:age=now-epoch(load['observed_utc'])
 except (KeyError,ValueError,TypeError):pass
 return {'status':'PUBLIC_FACTS_MATCH_NOT_QA_OR_EXECUTION_APPROVAL' if not errors else 'BLOCKED','errors':errors,'LOAD_age_seconds':age,'fresh_for_APP_admission_now':age is not None and 0<=age<=120,'root_review_and_new_fee_required':True,'QA_or_cloud_actions':0}
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--app',type=Path,required=True);p.add_argument('--load',type=Path,required=True);a=p.parse_args();app,ah=load_facts(a.app);load,lh=load_facts(a.load);report=check(app,load);report.update(app_original_sha256=ah,load_original_sha256=lh);print(json.dumps(report,sort_keys=True));raise SystemExit(bool(report['errors']))
if __name__=='__main__':main()
