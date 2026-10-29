"""Resume exact unprepared P05 at derive; original frozen clock and measurement gates preserved."""
import argparse,ast,datetime,hashlib,json,os,subprocess,time
from pathlib import Path
R=Path('/root/t44-final-20261029');F=R/'P05';T=R/'ops01/deployment/cloud-reuse';PS='346d19344281b9e02046a27cf9d24f07ebceb9c8f920105a981d7bfdc056ac1f'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def save(p,v):
 with p.open('x') as f:json.dump(v,f,sort_keys=True,indent=2);f.write('\n')
 p.chmod(0o600)
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--launcher-sha256',required=True);p.add_argument('--load-ready',type=Path,required=True);p.add_argument('--load-ready-sha256',required=True);p.add_argument('--cost-approval',type=Path,required=True);p.add_argument('--cost-approval-sha256',required=True);a=p.parse_args();os.umask(0o077)
 launcher=T/'P05-CONTINUOUS-fast10.PUBLIC.py'
 if sha(launcher)!=a.launcher_sha256:raise ValueError('ROOT_PINNED_FAILED_LAUNCHER_REQUIRED')
 admitted=time.time()
 if sha(a.load_ready)!=a.load_ready_sha256 or sha(a.cost_approval)!=a.cost_approval_sha256:raise ValueError('ORIGINAL_FRESH_READY_AND_COST_SHA_REQUIRED')
 ready=read(a.load_ready)
 if ready.get('root_approved') is not True or ready.get('actual_LOAD_ready') is not True or ready.get('QA_or_other_writer_started') is not False or ready.get('actual_image_id')!='sha256:4f3baf081863a4580b5608699d9a7a8af2d89c3e87abbb60089b630b9102b2a1' or not 0<=admitted-datetime.datetime.fromisoformat(ready['observed_utc'].replace('Z','+00:00')).timestamp()<=120:raise ValueError('FRESH_LOAD_READY_AT_RESUME_ADMISSION_REQUIRED')
 text=launcher.read_text();tree=ast.parse(text)
 # Existing source-derived launcher stores actual profile/package as safe Path literals.
 def literal_assignment(name):
  n=next(n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id==name for t in n.targets))
  if not isinstance(n.value,ast.Call) or n.value.func.id!='Path':raise ValueError('FIXED_PATH_LITERAL_REQUIRED:'+name)
  return Path(ast.literal_eval(n.value.args[0]))
 source=literal_assignment('PROFILE');profile=read(source)
 if sha(source)!=PS:raise ValueError('EXACT_CURRENT_SOURCE_PROFILE_REQUIRED')
 # Take exact package argument from already failed original phase argv's launcher literal.
 paths=[Path(n.args[0].value) for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='Path' and len(n.args)==1 and isinstance(n.args[0],ast.Constant) and isinstance(n.args[0].value,str)]
 packages=[p for p in paths if (p/'backend-bundle-manifest.json').is_file() and sha(p/'backend-bundle-manifest.json')==profile['backend_bundle_manifest_sha256']]
 if len(set(packages))!=1:raise ValueError('EXACT_EXISTING_NEW90B_PACKAGE_REQUIRED')
 package=packages[0];clock=read(F/'timeplan.PUBLIC.json');failed=read(F/'preparation.PUBLIC.json')
 if (clock['run_id']!='r30finalp05' or clock['t0_utc']!='2026-10-29T18:44:30Z' or clock['start_utc']!='2026-10-29T18:54:30Z' or clock['stop_utc']!='2026-10-29T19:09:30Z' or clock['cost_stop_utc']!='2026-10-29T19:14:30Z' or [(x['label'],x['returncode']) for x in failed['steps']]!=[('verify',0),('stop-F',0),('prove-loaded',0),('freeze-time',0),('derive',1)]):raise ValueError('EXACT_FAILED_BEFORE_DERIVE_FROZEN_P05_REQUIRED')
 if any((F/n).exists() for n in ['profile','runtime','campaign','P-inputs']):raise ValueError('PARTIAL_DERIVE_OR_ACTORS_NEED_SEPARATE_AUDIT')
 cutoff=datetime.datetime.fromisoformat(clock['packet_cutoff_utc'].replace('Z','+00:00')).timestamp()
 if cutoff-__import__('time').time()<120:raise ValueError('INSUFFICIENT_ORIGINAL_PACKET_PREPARATION_TIME')
 original=T/'final-image-bundle.py'
 if sha(original)!=read(package/'backend-bundle-manifest.json')['tool_sha256']:raise ValueError('ACTUAL_ORIGINAL_BUILD_HELPER_PIN_REQUIRED')
 s=original.read_text();needle='    parent.deadline(args.stop_utc, datetime.now(timezone.utc))  # noqa: UP017 -- APP Python3.10'
 if s.count(needle)!=1:raise ValueError('EXACT_LEGACY_DERIVE_GATE_PREIMAGE_REQUIRED')
 patch='''    if args.run_id != "r30finalp05" or args.stop_utc != "2026-10-29T19:09:30Z" or args.cost_stop_utc != "2026-10-29T19:14:30Z":raise ValueError("EXACT_ALREADY_FROZEN_P05_ONLY")
    remaining=(datetime.strptime(args.stop_utc,"%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)-datetime.now(timezone.utc)).total_seconds()
    if not 600 <= remaining <= 43200:raise ValueError("ORIGINAL_GEN600_RESERVE_REQUIRED")'''
 adapter=T/'final-image-bundle-p05-resume02.py'
 with adapter.open('x') as f:f.write(s.replace(needle,patch))
 adapter.chmod(0o600);logs=F/'resume-phase02-commands';logs.mkdir(mode=0o700);i=0
 def run(label,argv,cap=240):
  nonlocal i;i+=1;out=logs/(f'{i:02d}-'+label+'.stdout.private');err=logs/(f'{i:02d}-'+label+'.stderr.private')
  timeout=min(cap,cutoff-__import__('time').time())
  if timeout<1:raise ValueError('ORIGINAL_PACKET_CUTOFF_EXPIRED')
  with out.open('xb') as so,err.open('xb') as se:v=subprocess.run(list(map(str,argv)),stdout=so,stderr=se,check=False,timeout=timeout)
  if v.returncode:raise ValueError('P05_RESUME_PHASE_FAILED_PREFIX:'+label)
  return read(out)
 run('derive',[ 'python3',adapter,'derive','--package',package,'--manifest-sha256',profile['backend_bundle_manifest_sha256'],'--run-id','r30finalp05','--stop-utc',clock['stop_utc'],'--cost-stop-utc',clock['cost_stop_utc'],'--output',F/'profile'])
 run('derive-wrappers',['python3',T/'final-runtime-profile-pfast05.py','--source-profile',source,'--source-profile-sha256',PS,'--source-manifest',package/'source-manifest.json','--gen-profile',F/'profile','--gen-profile-sha256',sha(F/'profile/profile.json'),'--output',F/'runtime'])
 prepared=run('GEN-prepare',['python3',F/'profile/generation.py','prepare','--factory',F/'profile/factory.py','--source-package',package,'--upgrade-binding',package/'backend-bundle-manifest.json','--upgrade-binding-sha256',profile['backend_bundle_manifest_sha256'],'--source-manifest-sha256',profile['source_manifest_sha256'],'--original-proof',R.parent/'t44-r9/proof-v2-01/proof.jsonl','--image-proof',F/'profile/image-proof.py','--run-id','r30finalp05','--app-ip','172.21.182.245','--stop-utc',clock['stop_utc'],'--f-tls-port','26443','--f-http-port','18580','--p-tls-port','26445','--p-http-port','18581','--p-workers','64','--p-pool-size','5','--p-max-overflow','0','--output',F/'campaign'])
 selected=prepared['phases']['p'];gen=['python3',F/'profile/generation.py'];common=['--phase-dir',selected['phase_dir'],'--binding-sha256',selected['binding_sha256']];budget=None
 for action in ['arm','config','infra','probe-budget','migrate','idle']:
  extra=['--database',selected['database']] if action=='migrate' else []
  if action in {'migrate','idle'}:extra+=['--budget-receipt',budget['budget_receipt'],'--budget-receipt-sha256',budget['budget_receipt_sha256']]
  result=run(action,[*gen,action,*common,*extra])
  if action=='probe-budget':budget=result
 observation=read(F/'commands/03-prove-loaded.stdout.private');phase={'status':'CHOSEN_PHASE_IDLE_NO_SESSIONS_OR_QA','phase':selected,'budget':budget,'timeplan':clock,'import':observation,'original_failed_preparation_preserved':True}
 save(F/'preparation-resume02.PUBLIC.json',phase)
 # Continue unchanged fixed account/seed/service/HTTP/packet chain from its first unperformed stage.
 begin=text.index(" phase=run('phase',");end=text.index(" b=phase['phase']",begin)
 continued=text[:begin]+" phase=read(out/'preparation-resume02.PUBLIC.json')\n"+text[end:]
 continued=continued.replace("R/'r30finalp05-launcher'","R/'r30finalp05-resume02-launcher'")
 # Equivalent to original launcher checking LOAD readiness before its phase preparation, using real admission time, never retiming the receipt.
 age="time.time()-datetime.fromisoformat(ready['observed_utc'].replace('Z','+00:00')).timestamp()"
 if continued.count(age)!=1:raise ValueError('EXACT_PRE_PHASE_READY_CHECK_REQUIRED')
 continued=continued.replace(age,repr(admitted)+"-datetime.fromisoformat(ready['observed_utc'].replace('Z','+00:00')).timestamp()")
 dest=T/'P05-CONTINUOUS-resume02.PUBLIC.py';ast.parse(continued,feature_version=(3,10))
 with dest.open('x') as f:f.write(continued)
 dest.chmod(0o600)
 print(json.dumps({'status':'P05_ORIGINAL_WINDOW_PHASE_RESUMED_TO_IDLE','new_continuation':str(dest),'sha256':sha(dest),'original_T0_G_C_unchanged':True}),flush=True)
 subprocess.run(['python3','-B',str(dest),'--load-ready',str(a.load_ready),'--load-ready-sha256',a.load_ready_sha256,'--cost-approval',str(a.cost_approval),'--cost-approval-sha256',a.cost_approval_sha256],check=True)
if __name__=='__main__':main()
