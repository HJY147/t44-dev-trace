"""User-run pure P09 tool derivation; no fee/boot/deadline invented and no cloud/service action."""
import ast,hashlib,json,os
from pathlib import Path
R=Path('/root/t44-final-20261029');T=R/'ops01/deployment/cloud-reuse'
PINS={'P08-CONTINUOUS-fast10-cap50.PUBLIC.py':'dc811694da339101095b79819c96a07f0edc0b397feb131e2b97b4e343ad2d9d','final-app-prepare-pfast08-cap50.py':'b6c09ab1d2646cffc2cafd4f68be039cf88ec005d5d3a943727cd46a5bdc9843','final-image-bundle-pfast08-cap50.py':'a18ca38623aba2aba1a4a0e12e9698f8ce3bd1309896b7d087ee1a1a843de7bf','final-timeplan-pfast08-cap50.py':'bff1ad2479b65849f01a1670429d8d3198879c5c5b6ac55afc818a37caf9ca01'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def derive():
 if (R/'P09').exists()or(R/'r30finalp09-launcher').exists():raise ValueError('P09_ATTEMPT_EXISTS_NO_REPLAY_OR_RETIME')
 outputs={}
 for n,h in PINS.items():
  if sha(T/n)!=h:raise ValueError('USER_OBSERVED_P08_PREIMAGE_CHANGED:'+n)
  s=(T/n).read_text();name=n.replace('P08','P09').replace('pfast08','pfast09');s=s.replace('r30finalp08','r30finalp09').replace("R/'P08'","R/'P09'").replace('pfast08','pfast09')
  if n.startswith('P08-'):
   s=s.replace("R/'P07/campaign/p'","R/'P08/campaign/p'").replace('t44-cloud-r30finalp07-p','t44-cloud-r30finalp08-p').replace('t44-final-p07*','t44-final-p08*').replace('stop-old-P07','stop-old-P08').replace('PREVIOUS_P07','PREVIOUS_P08')
  ast.parse(s,feature_version=(3,10));outputs[name]=s.encode()
 for n,b in outputs.items():
  p=T/n
  if p.exists():
   if p.is_symlink()or sha(p)!=hashlib.sha256(b).hexdigest():raise ValueError('EXISTING_P09_TOOL_DIFFERS_NO_OVERWRITE')
  else:
   with p.open('xb')as out:out.write(b)
   p.chmod(0o600)
 return {'status':'P09_TOOLS_PREPARED_ONLY_NO_FEE_OR_FREEZE','tools':{n:sha(T/n)for n in outputs},'new_campaign_internal_cap_CNY':50,'source_unchanged':'90b734f65ce6ee9f5c217e885bc7ea4857e32b48','S10_E23_G25_C30':True,'old_P08_retained':True}
if __name__=='__main__':
 os.umask(0o077);print(json.dumps(derive(),sort_keys=True))
