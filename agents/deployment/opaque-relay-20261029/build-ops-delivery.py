"""Local-only packaging; neither executes ops nor accesses cloud."""
import ast,base64,hashlib,json,subprocess,zlib
from pathlib import Path
p=Path(__file__).resolve().parent
source=(p/'ops.py').read_bytes();digest=hashlib.sha256(source).hexdigest()
ast.parse(source.decode(),feature_version=(3,10))
payload=base64.b64encode(zlib.compress(source,9)).decode()
text="""#!/bin/sh
set -eu
umask 077
python3 -I -B - <<'INSTALL_OPS_R29'
import base64,hashlib,os,platform,zlib
from pathlib import Path
assert os.geteuid()==0 and platform.system()=='Linux'
base=Path('/root/t44-r9');assert base.is_dir() and base.resolve()==base
raw=zlib.decompress(base64.b64decode('PAYLOAD',validate=True))
assert len(raw)==SOURCE_BYTES and hashlib.sha256(raw).hexdigest()=='SOURCE_SHA'
path=base/'ops-r29-01.py'
fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o444)
with os.fdopen(fd,'wb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
assert path.read_bytes()==raw
print('R29_OPS_INSTALLED_NO_EXECUTION')
INSTALL_OPS_R29
""".replace('PAYLOAD',payload).replace('SOURCE_BYTES',str(len(source))).replace('SOURCE_SHA',digest)
raw=text.encode();(p/'install-ops.PUBLIC.sh').write_bytes(raw)
subprocess.run(['/bin/sh','-n',str(p/'install-ops.PUBLIC.sh')],check=True)
proof={'source_bytes':len(source),'source_sha256':digest,'source_python_3_10_syntax_checked_on_python_3_12':True,'installer_bytes':len(raw),'installer_sha256':hashlib.sha256(raw).hexdigest(),'UI_total_plus_300':len(raw)+300,'entire_base64_UI_plus_300':len(base64.b64encode(raw))+300,'cloud_executed':False,'original_runtime_modified':False}
assert proof['UI_total_plus_300']<=16000 and proof['entire_base64_UI_plus_300']<=16000
(p/'ops-delivery-proof.PUBLIC.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof))
