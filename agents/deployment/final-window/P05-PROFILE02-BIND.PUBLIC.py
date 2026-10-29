"""Create a new P05 launcher bound to the exact additive projection profile; no execution."""
import argparse,ast,hashlib,json
from pathlib import Path
OLD='e78a66a24afc87c636e90eadcba7934c0405abdae4321d69278d7cee14ee57c7';NEW='346d19344281b9e02046a27cf9d24f07ebceb9c8f920105a981d7bfdc056ac1f'
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--new-source-profile',type=Path,required=True);a=p.parse_args()
assert hashlib.sha256(a.new_source_profile.read_bytes()).hexdigest()==NEW
base=Path('/root/t44-final-20261029/ops01/deployment/cloud-reuse');original=base/'P05-CONTINUOUS.PUBLIC.py';text=original.read_text();tree=ast.parse(text)
node=next(n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='PROFILE' for t in n.targets));preimage=ast.get_source_segment(text,node.value)
assert text.count(preimage)==1 and text.count(OLD)==1
text=text.replace(preimage,'Path('+repr(str(a.new_source_profile))+')').replace(OLD,NEW);ast.parse(text,feature_version=(3,10));dest=base/'P05-CONTINUOUS-profile02.PUBLIC.py'
with dest.open('x') as out:out.write(text)
dest.chmod(0o600)
print(json.dumps({'status':'NEW_P05_PROFILE02_LAUNCHER_CREATED_NOT_STARTED','original_sha256':hashlib.sha256(original.read_bytes()).hexdigest(),'new_launcher':str(dest),'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'source_profile_sha256':NEW}))
