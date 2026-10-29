"""Fresh P07 sidecars with explicit G25/C30 checks; old P06 is never retimed or reused."""
import argparse,ast,hashlib,json,os
from pathlib import Path
R=Path('/root/t44-final-20261029');T=R/'ops01/deployment/cloud-reuse'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,s):
 ast.parse(s,feature_version=(3,10))
 with p.open('x') as f:f.write(s)
 p.chmod(0o600)
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--p06-launcher-sha256',required=True);a=p.parse_args();os.umask(0o077)
 if (R/'P07').exists() or (R/'r30finalp07-launcher').exists():raise ValueError('FIRST_P07_FREEZE_ONLY')
 old=T/'P06-CONTINUOUS-fast10.PUBLIC.py'
 if sha(old)!=a.p06_launcher_sha256:raise ValueError('ROOT_PINNED_ORIGINAL_P06_LAUNCHER_REQUIRED')
 text=old.read_text();tree=ast.parse(text);node=next(n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='C' for x in n.targets));code=Path(ast.literal_eval(node.value.args[0]));mf=json.loads((code/'code-manifest.PUBLIC.json').read_bytes())
 if mf['source_sha']!='90b734f65ce6ee9f5c217e885bc7ea4857e32b48' or len(mf['files'])!=18:raise ValueError('EXACT90B18_REQUIRED')
 for n,h in mf['files'].items():
  if sha(code/n)!=h or (code/n).stat().st_size!=mf['file_sizes'][n]:raise ValueError('PRODUCER_BYTES_CHANGED')
 guard=(code/'guard.py').read_text()
 if 'stop == t0 + timedelta(minutes=25)' not in guard or 'cost == t0 + timedelta(minutes=30)' not in guard:raise ValueError('REVIEWED_FAST_PRODUCER_G25_C30_REQUIRED')
 runtime=(T/'final-runtime-profile.py').read_text();needle='    f_http = http'
 if runtime.count(needle)!=1:raise ValueError('EXACT_RUNTIME_TEMPLATE_REQUIRED')
 runtime=runtime.replace(needle,'    http = replace(http, "stop != t0 + 35 * 60", "stop != t0 + 25 * 60")\n    http = replace(http, "cost != t0 + 40 * 60", "cost != t0 + 30 * 60")\n'+needle)
 clock=(T/'final-timeplan-pfast06.py').read_text().replace('r30finalp06','r30finalp07');prepare=(T/'final-app-prepare-pfast06.py').read_text().replace('final-timeplan-pfast06.py','final-timeplan-pfast07.py').replace('final-image-bundle-pfast06.py','final-image-bundle-pfast07.py').replace('final-runtime-profile-pfast05.py','final-runtime-profile-pfast07.py')
 adapter=(T/'final-image-bundle-pfast06.py').read_text().replace('r30finalp06','r30finalp07')
 text=text.replace('r30finalp06','r30finalp07').replace("R/'P06'","R/'P07'").replace('final-app-prepare-pfast06.py','final-app-prepare-pfast07.py')
 # Previous P06 chain has failed; stop only its exact containers before any fresh P07 phase.
 insertion=''' oldphase=R/'P06/campaign/p';oldbinding=oldphase/'binding.json'
 if oldbinding.exists():
  pv=read(oldbinding)
  if pv['project']!='t44-cloud-r30finalp06-p' or pv['source_sha']!='90b734f65ce6ee9f5c217e885bc7ea4857e32b48' or sha(oldphase/'controller.py')!=pv['file_hashes']['controller.py']:raise ValueError('EXACT_PREVIOUS_P06_OWNER_REQUIRED')
  run('stop-old-P06',['python3',oldphase/'controller.py','stop','--phase-dir',oldphase,'--binding-sha256',sha(oldbinding)],180)
  if subprocess.run(['docker','--context','default','ps','--quiet','--filter','label=com.docker.compose.project='+pv['project']],capture_output=True,check=True,timeout=20).stdout.strip():raise ValueError('PREVIOUS_P06_RUNNING_REMAINS')
'''
 marker=" f=read(R/'F05/preparation.PUBLIC.json')['phase']"
 if text.count(marker)!=1:raise ValueError('EXACT_F05_HANDOFF_PREIMAGE_REQUIRED')
 text=text.replace(marker,insertion+marker)
 outputs={'final-runtime-profile-pfast07.py':runtime,'final-timeplan-pfast07.py':clock,'final-app-prepare-pfast07.py':prepare,'final-image-bundle-pfast07.py':adapter,'P07-CONTINUOUS-fast10.PUBLIC.py':text}
 for n,s in outputs.items():put(T/n,s)
 print(json.dumps({'status':'FRESH_P07_PREPARED_NOT_FROZEN','tools':{n:sha(T/n) for n in outputs},'producer_manifest_sha256':sha(code/'code-manifest.PUBLIC.json'),'S10_E23_G25_C30':True,'measurement_seconds':780,'old_P06_retained':True}))
if __name__=='__main__':main()
