"""Resume original F05 after pre-SUT projection metadata refusal; never recreate phase/accounts/T0."""
import argparse,hashlib,json,os,subprocess
from pathlib import Path
R=Path('/root/t44-final-20261029');F=R/'F05';T=R/'ops01/deployment/cloud-reuse';OLD='e78a66a24afc87c636e90eadcba7934c0405abdae4321d69278d7cee14ee57c7';NEW='346d19344281b9e02046a27cf9d24f07ebceb9c8f920105a981d7bfdc056ac1f'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def save(p,v):
 with p.open('x') as o:json.dump(v,o,sort_keys=True,indent=2);o.write('\n')
 p.chmod(0o600)
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--new-source-profile',type=Path,required=True);p.add_argument('--code-dir',type=Path,required=True);p.add_argument('--code-manifest-sha256',required=True);p.add_argument('--package',type=Path,required=True);a=p.parse_args();os.umask(0o077)
 if sha(a.new_source_profile)!=NEW or sha(a.code_dir/'code-manifest.PUBLIC.json')!=a.code_manifest_sha256:raise ValueError('EXACT_NEW_PROFILE_AND_EXISTING_CODE_PIN_REQUIRED')
 profile=read(a.new_source_profile);plan=read(F/'F-inputs/plan.json');prep=read(F/'preparation.PUBLIC.json');selected=prep['phase'];d=Path(selected['phase_dir']);binding=selected['binding_sha256'];budget=prep['budget'];gen=F/'profile'
 if (profile['source_sha']!='90b734f65ce6ee9f5c217e885bc7ea4857e32b48' or profile['load_python_identity_projection_sha256']!='ce562c117428face0b421e06b33c361b291cab26d8d3a51d24484dbd0841da2a' or plan['source_profile']['sha256']!=OLD or prep['status']!='CHOSEN_PHASE_IDLE_NO_SESSIONS_OR_QA' or sha(d/'binding.json')!=binding or sha(a.package/'source-manifest.json')!=profile['source_manifest_sha256']):raise ValueError('SAME_F05_ORIGINAL_PHASE_ACTORS_AND_ACTUAL_BUILD_REQUIRED')
 if (F/'F-http/output/result').exists() or (F/'F-http/logs/http.stdout.private').exists() or (F/'F-http/logs/http.stderr.private').exists():raise ValueError('NOT_PROVEN_BEFORE_FIRST_HTTP_NO_AUTOMATIC_REPLAY')
 if sha(F/'F-http/logs/runtime.stderr.private')!='1cd23da0c7c71002e21bce322e669d194910697e8497fe94d76b0dfe65716204':raise ValueError('EXACT_RECORDED_PRE_SUT_REFUSAL_REQUIRED')
 original_init=read(R/'r30finalf05-launcher/07-init-seven.stdout.private');accounts=Path(original_init['output'])
 if len(read(accounts))!=7:raise ValueError('ORIGINAL_SEVEN_INITIALIZED_ACTORS_REQUIRED')
 launcher=R/'r30finalf05-resume02-launcher';launcher.mkdir(mode=0o700);i=0
 def run(label,argv,cap=300):
  nonlocal i;i+=1;so=launcher/(f'{i:02d}-'+label+'.stdout.private');se=launcher/(f'{i:02d}-'+label+'.stderr.private')
  with so.open('xb') as out,se.open('xb') as err:v=subprocess.run(list(map(str,argv)),stdout=out,stderr=err,check=False,timeout=cap)
  if v.returncode:raise ValueError('RESUME_STEP_FAILED_PREFIX_PRESERVED:'+label)
  return read(so)
 runtime=F/'runtime02';data=F/'F-inputs02';data.mkdir(mode=0o700)
 run('derive-runtime02',['python3',T/'final-runtime-profile.py','--source-profile',a.new_source_profile,'--source-profile-sha256',NEW,'--source-manifest',a.package/'source-manifest.json','--gen-profile',gen,'--gen-profile-sha256',sha(gen/'profile.json'),'--output',runtime])
 plan['source_profile']['sha256']=NEW;save(data/'plan.json',plan);save(data/'intent.json',read(F/'F-inputs/intent.json'));save(data/'empty-service-stage.json',{})
 common=['--phase-dir',d,'--binding-sha256',binding,'--profile-json',gen/'profile.json','--profile-sha256',sha(gen/'profile.json'),'--code-dir',a.code_dir,'--code-manifest',a.code_dir/'code-manifest.PUBLIC.json','--code-manifest-sha256',a.code_manifest_sha256,'--source-profile',a.new_source_profile,'--plan',data/'plan.json','--intent',data/'intent.json','--import-receipt',prep['import']['receipt'],'--budget-receipt',budget['budget_receipt'],'--budget-receipt-sha256',budget['budget_receipt_sha256']]
 run('F-project02',['python3',runtime/'f-http-prepare.py','--phase-dir',d,'--binding-sha256',binding,'--code-dir',a.code_dir,'--code-manifest-sha256',a.code_manifest_sha256,'--source-profile',a.new_source_profile,'--plan',data/'plan.json','--accounts',accounts,'--service',data/'empty-service-stage.json','--import-receipt',prep['import']['receipt'],'--ca',d/'tls/ca.pem','--output-dir',F/'F-http02'],240)
 project=F/'F-http02/output/result/project-and-members.private.json'
 service=run('F-services02',['python3',T/'final-f-services.py','--admin-file',runtime/'r30-neutral-admin.py','--admin-sha256',sha(runtime/'r30-neutral-admin.py'),*common,'--project-receipt',project,'--project-receipt-sha256',sha(project),'--output-dir',F/'F-services02'],240)
 proof=Path(service['output']);normal=proof.parent/'service.original.private.json';token=d/'scheduler-secrets/scheduler-token.json'
 with token.open('xb') as target:target.write(normal.read_bytes())
 token.chmod(0o600);os.chown(token,10001,10001)
 run('scheduler-start',['python3',gen/'generation.py','scheduler-start','--phase-dir',d,'--binding-sha256',binding,'--budget-receipt',budget['budget_receipt'],'--budget-receipt-sha256',budget['budget_receipt_sha256']],180)
 humans=F/'F-http02/output/result/human-sessions.private.json'
 environment=run('F-private-env',['python3',T/'final-f-environment.py','--plan',data/'plan.json','--accounts',accounts,'--human-sessions',humans,'--human-sessions-sha256',sha(humans),'--service-proof',proof,'--service-proof-sha256',sha(proof),'--output',F/'functional-environment.private.json'],90)
 result={'status':'F05_RESUMED_AFTER_PRE_SUT_METADATA_FIX_NOT_QA_STARTED','source_sha':profile['source_sha'],'source_profile_sha256':NEW,'old_source_profile_sha256':OLD,'original_T0_G_C_preserved':True,'original_seven_actors_reused':True,'environment':environment,'phase':selected,'budget':budget,'timeplan':str(F/'timeplan.PUBLIC.json'),'runtime':str(runtime),'ca_file':str(d/'tls/ca.pem')}
 save(launcher/'F-ready.PUBLIC.json',result);print(json.dumps(result),flush=True)
 subprocess.run(['python3',str(T/'F05-TRANSPORT-APP.PUBLIC.py'),'--f-dir',str(F),'--load-ip','172.21.182.244','--load-public-key',str(R/'ops01/qa-public/load-public.pem')],check=True)
if __name__=='__main__':main()
