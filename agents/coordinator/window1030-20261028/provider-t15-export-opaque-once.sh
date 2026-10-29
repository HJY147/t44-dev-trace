set -eu
python3 -B - <<'OPAQUE_EXPORT'
from pathlib import Path
import os,json,hashlib,base64,stat
root=Path('/root/t44-r9/campaign-r28functional-01/f/provider-t15-hostreceipts-01')
r=json.loads((root/'result.PUBLIC.json').read_bytes())
p=Path('/root/t44-r9/campaign-r28functional-01/f/provider-t15-output-01/material01/functional-material.T44FENV1')
assert r['sealed_host_file']==str(p)
f=os.open(p,os.O_RDONLY|os.O_NOFOLLOW)
with os.fdopen(f,'rb') as x:
 i=os.fstat(x.fileno());assert stat.S_ISREG(i.st_mode) and 0<i.st_size<=1100000;b=x.read(1100001)
h=hashlib.sha256(b).hexdigest();assert h==r['sealed_sha256'] and len(b)==r['sealed_bytes'] and b.startswith(b'T44FENV1')
a=[b[i:i+11800] for i in range(0,len(b),11800)];assert 1<=len(a)<=4
out=root/'opaque-transfer01';out.mkdir(mode=0o700)
def save(p,b):
 f=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
 with os.fdopen(f,'wb') as x:x.write(b);x.flush();os.fsync(x.fileno())
meta={'kind':'ROOT_T15_OPAQUE_ONLY_TRANSFER','bytes':len(b),'sha256':h,'parts':len(a),'recipient_public_key_sha256':'cf8c47e702fe9355f457a2e49b5594a761b9a9666ce135f8df023cb25cee3205','source_sha':'a12e9e70b963bacafda3242bb6d82e53ee912ff1','plaintext_read_or_credentials_printed':False}
for n,v in enumerate(a):
 part={'index':n,'parts':len(a),'bytes':len(v),'sha256':hashlib.sha256(v).hexdigest(),'data':base64.b64encode(v).decode()}
 save(out/('part-'+str(n)+'.OPAQUE.json'),json.dumps(part,separators=(',',':')).encode())
print(json.dumps({'metadata':meta,'first_opaque_part':json.loads((out/'part-0.OPAQUE.json').read_bytes())},separators=(',',':')),flush=True)
OPAQUE_EXPORT
