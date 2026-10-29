"""LOCAL/APP tool derivation only. P08 requires separate user-approved45CNY cost file before cloud start."""
import argparse,ast,hashlib,json,os
from pathlib import Path
R=Path('/root/t44-final-20261029');T=R/'ops01/deployment/cloud-reuse'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,s):
 ast.parse(s,feature_version=(3,10))
 with p.open('x') as f:f.write(s)
 p.chmod(0o600)
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--p07-launcher-sha256',required=True);a=p.parse_args();os.umask(0o077)
 if (R/'P08').exists() or (R/'r30finalp08-launcher').exists():raise ValueError('FIRST_P08_FREEZE_ONLY')
 old=T/'P07-CONTINUOUS-copyfix.PUBLIC.py'
 if sha(old)!=a.p07_launcher_sha256:raise ValueError('EXACT_VALID_PACKET_P07_LAUNCHER_REQUIRED')
 text=old.read_text()
 if "service.original-root-copy.private.json" not in text or "'--service',service_root" not in text or 'boot01/official/source-manifest.json' in text or 'boot01/official/backend-bundle-manifest.json' in text:raise ValueError('EXACT_CANONICAL_SERVICE_AND90B_MANIFEST_FIXES_REQUIRED')
 tree=ast.parse(text);c=next(n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='C' for x in n.targets));code=Path(ast.literal_eval(c.value.args[0]));mf=json.loads((code/'code-manifest.PUBLIC.json').read_bytes())
 if mf['source_sha']!='90b734f65ce6ee9f5c217e885bc7ea4857e32b48' or len(mf['files'])!=18:raise ValueError('EXACT_SAME90B18_REQUIRED')
 for n,h in mf['files'].items():
  if sha(code/n)!=h or (code/n).stat().st_size!=mf['file_sizes'][n]:raise ValueError('PRODUCER_BYTES_CHANGED')
 clock=(T/'final-timeplan-pfast07.py').read_text()
 if clock.count('remaining != 40')!=1 or 'r30finalp07' not in clock:raise ValueError('EXACT_OLD_COST_GATE_AND_RUN_REQUIRED')
 clock=clock.replace('remaining != 40','remaining != 45').replace('r30finalp07','r30finalp08').replace('ROOT_REMAINING40','ROOT_REMAINING45')
 prepare=(T/'final-app-prepare-pfast07.py').read_text().replace('final-timeplan-pfast07.py','final-timeplan-pfast08.py').replace('final-image-bundle-pfast07.py','final-image-bundle-pfast08.py')
 adapter=(T/'final-image-bundle-pfast07.py').read_text()
 if 'r30finalp07' not in adapter:raise ValueError('EXACT_PREVIOUS_FRESH_WINDOW_ADAPTER_REQUIRED')
 adapter=adapter.replace('r30finalp07','r30finalp08')
 # Retain all same-byte service/root-copy and actual90b manifest paths; only change fresh run/output/helper and previous-owned cleanup identity.
 text=text.replace('r30finalp07','r30finalp08').replace("R/'P07'","R/'P08'").replace('final-app-prepare-pfast07.py','final-app-prepare-pfast08.py')
 text=text.replace("R/'P06/campaign/p'","R/'P07/campaign/p'").replace('t44-cloud-r30finalp06-p','t44-cloud-r30finalp07-p').replace('stop-old-P06','stop-old-P07').replace('PREVIOUS_P06','PREVIOUS_P07')
 # Refuse any active previous launcher before stopping the exact P07 container owner.
 marker=" oldphase=R/'P07/campaign/p'"
 gate=''' active=subprocess.run(['systemctl','list-units','--type=service','--state=active','--plain','--no-legend','t44-final-p07*'],capture_output=True,check=True,timeout=10).stdout.decode().strip()
 if active:raise ValueError('ROOT_MUST_STOP_PREVIOUS_P07_ACTOR_LAUNCHER_BEFORE_NEW_PHASE')
'''
 if text.count(marker)!=1:raise ValueError('EXACT_PREVIOUS_P07_OWNER_HANDOFF_REQUIRED')
 text=text.replace(marker,gate+marker)
 outputs={'final-timeplan-pfast08.py':clock,'final-app-prepare-pfast08.py':prepare,'final-image-bundle-pfast08.py':adapter,'P08-CONTINUOUS-fast10.PUBLIC.py':text}
 for n,s in outputs.items():put(T/n,s)
 print(json.dumps({'status':'P08_TOOLS_PREPARED_ONLY_AWAIT_USER45_APPROVAL_NO_CLOUD_START','tools':{n:sha(T/n) for n in outputs},'producer_manifest_sha256':sha(code/'code-manifest.PUBLIC.json'),'source_unchanged':'90b734f65ce6ee9f5c217e885bc7ea4857e32b48','S10_E23_G25_C30':True,'measurement_seconds':780,'old_P07_retained':True,'requires_new_user_approved_budget_CNY':45}))
if __name__=='__main__':main()
