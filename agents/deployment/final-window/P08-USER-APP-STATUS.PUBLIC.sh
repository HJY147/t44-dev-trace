python3 -B - <<'P08_USER_STATUS'
import base64,datetime,hashlib,json,subprocess,zlib
from pathlib import Path
R=Path('/root/t44-final-20261029/P08')
r=subprocess.run(['systemctl','show','t44-final-p08-continuous.service','--property=ActiveState,SubState,Result,ExecMainStatus,ExecMainCode,ExecMainStartTimestamp,ExecMainExitTimestamp'],capture_output=True,check=False,timeout=10)
report={'kind':'USER_P08_APP_STATUS_PUBLIC_ONLY','observed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'unit_returncode':r.returncode,'unit':dict(x.split('=',1)for x in r.stdout.decode().splitlines()if '='in x),'files':{},'state_changed':False,'QA_or_SUT_requests':0}
for name in ['preparation.PUBLIC.json','timeplan.PUBLIC.json','backend-import-receipt.PUBLIC.json','LOAD-bootstrap.original.PUBLIC.json']:
 p=R/name
 if not p.is_file():report['files'][name]={'status':'PENDING_NOT_PRESENT'};continue
 if p.is_symlink() or p.stat().st_size>2000000:raise ValueError('BOUNDED_ORIGINAL_PUBLIC_FILE_REQUIRED')
 raw=p.read_bytes();v=json.loads(raw);row={'status':'PRESENT_ORIGINAL_BYTES','bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'zlib_b64':base64.b64encode(zlib.compress(raw,9)).decode()}
 if name=='preparation.PUBLIC.json':row['summary']={'status':v.get('status'),'phase':v.get('phase'),'steps':[{'label':x['label'],'returncode':x['returncode']}for x in v.get('steps',[])]}
 if name=='timeplan.PUBLIC.json':row['clock']={k:v.get(k)for k in ['run_id','t0_utc','start_utc','end_utc','stop_utc','cost_stop_utc','packet_cutoff_utc','absolute_cost_cutoff_utc']}
 report['files'][name]=row
print(json.dumps(report,sort_keys=True))
P08_USER_STATUS
