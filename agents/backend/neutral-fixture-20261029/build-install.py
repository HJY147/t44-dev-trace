import base64
import hashlib
import json
import zlib
from pathlib import Path

p=Path(__file__).resolve().parent
files={n:hashlib.sha256((p/n).read_bytes()).hexdigest() for n in ('host.py','edge.py','admin.py')}
manifest={'kind':'NEUTRAL_R29_CODE_ONLY','source_sha':'f7cdb5fa3b19f84d8ab0d0b042bf51a5b8484e8f','files':files,'Linux_or_SUT_executed':False}
(p/'code-manifest.PUBLIC.json').write_text(json.dumps(manifest,sort_keys=True)+'\n')
code={n:(p/n).read_text() for n in (*files,'code-manifest.PUBLIC.json')}
blob=base64.b64encode(zlib.compress(json.dumps(code,sort_keys=True,separators=(',',':')).encode(),9)).decode()
installer='''#!/bin/sh
set -eu
umask 077
python3 -I -B - <<'INSTALL_NEUTRAL'
import base64,hashlib,json,os,zlib
from pathlib import Path
BLOB=REPLACE_BLOB
EXPECTED=REPLACE_PINS
raw=zlib.decompress(base64.b64decode(BLOB,validate=True))
rows={n:v.encode() for n,v in json.loads(raw).items()}
assert set(rows)==set(EXPECTED)
for n,b in rows.items():assert hashlib.sha256(b).hexdigest()==EXPECTED[n]
base=Path('/root/t44-r9/neutral-fixture-r29-01')
assert base.parent.resolve()==base.parent and not base.exists() and not base.is_symlink()
base.mkdir(mode=0o700)
code=base/'code';code.mkdir(mode=0o755);code.chmod(0o755)
for n,b in rows.items():
 fd=os.open(code/n,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o444)
 os.fchmod(fd,0o444)
 with os.fdopen(fd,'wb') as f:f.write(b);f.flush();os.fsync(f.fileno())
print(json.dumps({'kind':'NEUTRAL_R29_CODE_INSTALLED_NOT_EXECUTED','code_directory':str(code),'files':EXPECTED,'SUT_requests':0}))
INSTALL_NEUTRAL
'''.replace('REPLACE_BLOB',repr(blob)).replace('REPLACE_PINS',repr({n:hashlib.sha256(v.encode()).hexdigest() for n,v in code.items()}))
assert len(installer.encode())+300<16500
(p/'install.PUBLIC.sh').write_text(installer)
print(json.dumps({'installer_bytes':len(installer.encode()),'installer_SHA256':hashlib.sha256(installer.encode()).hexdigest(),'code_manifest':manifest}))
