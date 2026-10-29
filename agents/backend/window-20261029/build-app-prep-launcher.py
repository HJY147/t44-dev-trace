"""Package only the reviewed single-use worker; does not execute it."""

import base64
import gzip
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
raw = (HERE / 'app-prep-once.py').read_bytes()
encoded = base64.b64encode(gzip.compress(raw, mtime=0)).decode()
digest = hashlib.sha256(raw).hexdigest()
text = """#!/bin/sh
set -eu
umask 077
# Root fills the observed current APP private IP and explicitly admits prep.
R29_APP_IP=''
R29_ROOT_ADMIT_PREP=0
python3 -I - "$R29_APP_IP" "$R29_ROOT_ADMIT_PREP" <<'R29_APP_PREP_INSTALL'
import base64,gzip,hashlib,ipaddress,os,platform,subprocess,sys
from pathlib import Path
ip=ipaddress.IPv4Address(sys.argv[1])
assert ip.is_private and not ip.is_loopback and not ip.is_link_local
assert sys.argv[2]=='1', 'EXPLICIT_ROOT_PREP_ADMISSION_REQUIRED'
assert os.geteuid()==0 and platform.system()=='Linux'
base=Path('/root/t44-r9');assert base.is_dir() and base.resolve()==base
raw=gzip.decompress(base64.b64decode('PAYLOAD',validate=True))
assert len(raw)==WORKER_BYTES and hashlib.sha256(raw).hexdigest()=='WORKER_SHA'
path=base/'r29-app-prep-once.py'
fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o444)
with os.fdopen(fd,'wb') as f:
 f.write(raw);f.flush();os.fsync(f.fileno())
assert path.read_bytes()==raw
out=base/'r29-app-prep-unit.stdout.private';err=base/'r29-app-prep-unit.stderr.private'
for log in [out,err]:
 fd=os.open(log,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600);os.close(fd)
subprocess.run(['systemd-run','--unit=t44-r29-app-prep-01','--property=Type=exec','--property=RuntimeMaxSec=1800','--property=TimeoutStopSec=15','--property=KillMode=control-group','--property=UMask=0077','--property=StandardOutput=append:'+str(out),'--property=StandardError=append:'+str(err),'python3','-I',str(path),'--app-ip',str(ip),'--root-admit-prep'],check=True,timeout=20)
print('R29_APP_PREP_WORKER_DISPATCHED_NOT_READY_NO_S1_S2')
R29_APP_PREP_INSTALL
""".replace('PAYLOAD', encoded).replace('WORKER_BYTES', str(len(raw))).replace('WORKER_SHA', digest)
launcher = text.encode()
(HERE / 'app-prep-launch.PUBLIC.sh').write_bytes(launcher)
proof = {'worker_bytes': len(raw), 'worker_sha256': digest, 'launcher_bytes': len(launcher), 'launcher_sha256': hashlib.sha256(launcher).hexdigest(), 'raw_UI_plus_description': len(launcher) + 300, 'base64_entire_command_plus_description': len(base64.b64encode(launcher)) + 300, 'description_allowance': 300, 'unknown_app_ip': None, 'root_prep_admitted_default': False, 'S1_or_S2_or_pressure_grant_authorized': False, 'unit_runtime_max_seconds': 1800, 'cloud_executed': False}
assert proof['raw_UI_plus_description'] < 18000 and proof['base64_entire_command_plus_description'] < 18000
(HERE / 'app-prep-proof.PUBLIC.json').write_text(json.dumps(proof, indent=2) + '\n')
print(json.dumps(proof, indent=2))
