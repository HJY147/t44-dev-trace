#!/bin/sh
set -eu
python3 -I -B - <<'PY'
from pathlib import Path
import base64,hashlib,json,os,subprocess
repo_path='agents/deployment/opaque-relay-20261029/relay.py'
url='https://api.github.com/repos/HJY147/t44-dev-trace/contents/'+repo_path+'?ref=ad1f183c5ed734fc52f640d8b042f0fc95c3b838'
p=subprocess.run(['curl','--ipv4','--http1.1','--fail','--silent','--show-error','--location','--proto','=https','--proto-redir','=https','--connect-timeout','5','--max-time','20','--max-filesize','100000','--header','Accept: application/vnd.github.raw+json',url],capture_output=True,timeout=25)
assert p.returncode==0,('PUBLIC_CODE_DOWNLOAD_FAILED',p.returncode,hashlib.sha256(p.stderr).hexdigest())
raw=p.stdout;assert len(raw)<=100000
if raw.lstrip().startswith(b'{'):
 record=json.loads(raw);assert record['type']=='file' and record['path']==repo_path and record['size']==18566 and record['encoding']=='base64'
 raw=base64.b64decode(''.join(record['content'].split()),validate=True)
assert len(raw)==18566 and hashlib.sha256(raw).hexdigest()=='0faba87792014ec0b16e18ef08286da234d8744f2d1792f409dccd01e939ea59'
root=Path('/root/t44-r9/opaque-relay-r29-01');root.mkdir(mode=0o700)
fd=os.open(root/'relay.py',os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o444)
with os.fdopen(fd,'wb') as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())
print(json.dumps({'kind':'PUBLIC_RELAY_CODE_INSTALLED_ONLY','path':str(root/'relay.py'),'sha256':'0faba87792014ec0b16e18ef08286da234d8744f2d1792f409dccd01e939ea59','bytes':18566,'APP_LOAD_listener_or_consumer_started':False}))
PY
