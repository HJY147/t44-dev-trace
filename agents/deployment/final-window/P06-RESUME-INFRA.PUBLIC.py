"""Resume original P06 infra after owned stop; never refreeze, recreate actors or extend deadlines."""
import argparse,ast,datetime,hashlib,json,os,subprocess,time
from pathlib import Path
R=Path('/root/t44-final-20261029');F=R/'P06';T=R/'ops01/deployment/cloud-reuse'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def save(p,v):
 with p.open('x') as f:json.dump(v,f,sort_keys=True,indent=2);f.write('\n')
 p.chmod(0o600)
def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ['launcher-sha256','load-ready-sha256','cost-approval-sha256']:p.add_argument('--'+n,required=True)
 for n in ['load-ready','cost-approval']:p.add_argument('--'+n,type=Path,required=True)
 a=p.parse_args();os.umask(0o077);launcher=T/'P06-CONTINUOUS-fast10.PUBLIC.py'
 if sha(launcher)!=a.launcher_sha256 or sha(a.load_ready)!=a.load_ready_sha256 or sha(a.cost_approval)!=a.cost_approval_sha256:raise ValueError('ROOT_PINNED_ORIGINAL_INPUTS_REQUIRED')
 admitted=time.time();ready=read(a.load_ready)
 if ready.get('actual_LOAD_ready') is not True or ready.get('root_approved') is not True or ready.get('QA_or_other_writer_started') is not False or ready.get('actual_image_id')!='sha256:4f3baf081863a4580b5608699d9a7a8af2d89c3e87abbb60089b630b9102b2a1' or not 0<=admitted-datetime.datetime.fromisoformat(ready['observed_utc'].replace('Z','+00:00')).timestamp()<=120:raise ValueError('ACTUAL_FRESH_LOAD_READY_REQUIRED')
 clock=read(F/'timeplan.PUBLIC.json');failed=read(F/'preparation.PUBLIC.json')
 expected=[('verify',0),('stop-F',0),('prove-loaded',0),('freeze-time',0),('derive',0),('derive-wrappers',0),('GEN-prepare',0),('arm',0),('config',0),('infra',1),('failure-owned-stop',0)]
 if [(s['label'],s['returncode']) for s in failed['steps']]!=expected or clock['run_id']!='r30finalp06' or clock['t0_utc']!='2026-10-29T18:54:02Z' or clock['start_utc']!='2026-10-29T19:04:02Z' or clock['stop_utc']!='2026-10-29T19:19:02Z' or clock['cost_stop_utc']!='2026-10-29T19:24:02Z':raise ValueError('EXACT_P06_FAILURE_PREFIX_AND_ORIGINAL_WINDOW_REQUIRED')
 if any((F/n).exists() for n in ['P-inputs','P-accounts','P-seed','P-http']):raise ValueError('ACTORS_OR_FIXTURE_ALREADY_STARTED_NO_REPLAY')
 genstep=next(s for s in failed['steps'] if s['label']=='GEN-prepare');original=Path(genstep['stdout']['path'])
 if sha(original)!=genstep['stdout']['sha256']:raise ValueError('ORIGINAL_GEN_PREPARE_SHA_REQUIRED')
 selected=read(original)['phases']['p'];d=Path(selected['phase_dir']);binding=selected['binding_sha256']
 if sha(d/'binding.json')!=binding:raise ValueError('EXACT_ORIGINAL_P06_BINDING_REQUIRED')
 cutoff=datetime.datetime.fromisoformat(clock['packet_cutoff_utc'].replace('Z','+00:00')).timestamp()
 if cutoff-time.time()<120:raise ValueError('ORIGINAL_PACKET_CUTOFF_INSUFFICIENT')
 logs=F/'resume-infra02-commands';logs.mkdir(mode=0o700);i=0
 def run(action,argv):
  nonlocal i;i+=1;out=logs/(f'{i:02d}-'+action+'.stdout.private');err=logs/(f'{i:02d}-'+action+'.stderr.private')
  timeout=min(240,cutoff-time.time())
  if timeout<1:raise ValueError('ORIGINAL_PACKET_CUTOFF_EXPIRED')
  with out.open('xb') as so,err.open('xb') as se:v=subprocess.run(list(map(str,argv)),stdout=so,stderr=se,check=False,timeout=timeout)
  if v.returncode:raise ValueError('OWNED_P06_INFRA_RESUME_FAILED_PREFIX:'+action)
  return read(out)
 gen=['python3',F/'profile/generation.py'];common=['--phase-dir',d,'--binding-sha256',binding];budget=None
 for action in ['infra','probe-budget','migrate','idle']:
  extra=['--database',selected['database']] if action=='migrate' else []
  if action in {'migrate','idle'}:extra+=['--budget-receipt',budget['budget_receipt'],'--budget-receipt-sha256',budget['budget_receipt_sha256']]
  v=run(action,[*gen,action,*common,*extra])
  if action=='probe-budget':budget=v
 prove=next(s for s in failed['steps'] if s['label']=='prove-loaded');p=Path(prove['stdout']['path'])
 if sha(p)!=prove['stdout']['sha256']:raise ValueError('ORIGINAL_IMPORT_OBSERVATION_SHA_REQUIRED')
 phase={'status':'CHOSEN_PHASE_IDLE_NO_SESSIONS_OR_QA','phase':selected,'budget':budget,'timeplan':clock,'import':read(p),'original_failed_preparation_preserved':True};save(F/'preparation-resume02.PUBLIC.json',phase)
 text=launcher.read_text();begin=text.index(" phase=run('phase',");end=text.index(" b=phase['phase']",begin);text=text[:begin]+" phase=read(out/'preparation-resume02.PUBLIC.json')\n"+text[end:];text=text.replace("R/'r30finalp06-launcher'","R/'r30finalp06-resume02-launcher'")
 age="time.time()-datetime.fromisoformat(ready['observed_utc'].replace('Z','+00:00')).timestamp()"
 if text.count(age)!=1:raise ValueError('EXACT_PRE_PHASE_READY_CHECK_REQUIRED')
 text=text.replace(age,repr(admitted)+"-datetime.fromisoformat(ready['observed_utc'].replace('Z','+00:00')).timestamp()")
 dest=T/'P06-CONTINUOUS-resume02.PUBLIC.py';ast.parse(text,feature_version=(3,10))
 with dest.open('x') as f:f.write(text)
 dest.chmod(0o600)
 print(json.dumps({'status':'P06_ORIGINAL_PHASE_IDLE_RESUMED_NO_RETIME','continuation':str(dest),'sha256':sha(dest)}),flush=True)
 subprocess.run(['python3','-B',str(dest),'--load-ready',str(a.load_ready),'--load-ready-sha256',a.load_ready_sha256,'--cost-approval',str(a.cost_approval),'--cost-approval-sha256',a.cost_approval_sha256],check=True)
if __name__=='__main__':main()
