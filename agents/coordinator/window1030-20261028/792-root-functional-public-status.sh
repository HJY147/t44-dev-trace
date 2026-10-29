python3 -I -B - <<'PUBLIC_STATUS'
from pathlib import Path
import json,hashlib,os,stat
r=Path('/root/t44-r9/independent-v11-r28-01/functional-r28-02');f=r/'single-functional-r01/PUBLIC';d=r/'disk/PUBLIC'
out=[]
def one(p,limit=16000):
 fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW)
 with os.fdopen(fd,'rb') as x:
  a=os.fstat(x.fileno());assert stat.S_ISREG(a.st_mode) and a.st_size<=limit;b=x.read(limit+1)
 return {'file':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'value':json.loads(b)}
for p in [f/'controller-failed.PUBLIC.json',f/'bootstrap-failed.PUBLIC.json',f/'final.PUBLIC.json',d/'launch.receipt.PUBLIC.json',d/'functional-capsule-final.PUBLIC.json']:
 if p.exists():out.append(one(p))
for p in sorted((d/'handoff').glob('*.request.PUBLIC.json')):
 out.append(one(p))
for p in sorted((d/'runtime').glob('*.PUBLIC.json')):
 v=one(p);x=v.pop('value');v['public_status_selected']={k:x[k] for k in ['phase','state','status','exit_code','reason','stop_reason','request_count','requests','root_grant_sha256','admission','admitted','kind','utc'] if k in x};out.append(v)
result={'kind':'ROOT_FIXED_PUBLIC_ONLY_FUNCTIONAL_STATUS','source_or_private_case_read':False,'items':out,'network_policy_receipt_exists':(f/'network-policy.PUBLIC.json').exists(),'execution_reserved_exists':(f/'execution-reserved.PUBLIC.json').exists()}
b=json.dumps(result,separators=(',',':')).encode()
assert len(b)<=19000,'PUBLIC summary cap; no private read'
print(b.decode())
PUBLIC_STATUS
