import base64,hashlib,io,json,subprocess,sys,tarfile
from pathlib import Path
N=120717
H='8002f6fd51e189382798a3d60d62bf11bbd51891c0b70f92425fd2fc11aed94f'
def need(ok):
 if not ok: raise ValueError('PUBLIC_INSTALL_BUNDLE_REFUSED')
b=Path(sys.argv[1]).read_bytes()
need(len(b)<=1048576)
if b.lstrip().startswith(b'{'):
 j=json.loads(b);need(j.get('encoding')=='base64' and j.get('size')==N)
 b=base64.b64decode(''.join(j['content'].split()),validate=True)
need(len(b)==N and hashlib.sha256(b).hexdigest()==H)
with tarfile.open(fileobj=io.BytesIO(b),mode='r:gz') as t:
 rows=t.getmembers();need(len(rows)==25 and len({r.name for r in rows})==25)
 d={}
 for r in rows:
  need(r.isfile() and not r.name.startswith('/') and '..' not in r.name.split('/') and 0<=r.size<=300000)
  d[r.name]=t.extractfile(r).read(r.size+1);need(len(d[r.name])==r.size)
m=json.loads(d.pop('bundle.PUBLIC.json'));need(m.get('install_only') is True and set(d)==set(m['files']))
for name,r in m['files'].items():
 need(len(d[name])==r['bytes'] and hashlib.sha256(d[name]).hexdigest()==r['sha256'])
steps=m['install_steps'];need(len(steps)==17 and len(set(steps))==17 and set(steps)<=set(d))
for name in steps: subprocess.run(['bash'],input=d[name],check=True)
print(json.dumps({'PUBLIC_install_complete':True,'steps':17,'targets':m['install_targets'],'services_or_callbacks_started':False}))
