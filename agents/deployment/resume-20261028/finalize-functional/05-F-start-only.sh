set -eu
python3 - <<'PYFSTART'
import hashlib,json,os,subprocess,time
from pathlib import Path
GEN=Path('/root/t44-r9/resume-20261028-02/resume-profile/generation.py')
PHASE=Path('/root/t44-r9/campaign-r28functional-01/f')
BINDING='be1975a7625eae32bf8aaae7e1f2de7d7aef8b20968aa5552320b22202258a9f'
SOURCE='a12e9e70b963bacafda3242bb6d82e53ee912ff1'
STOP=1793183400.0
OUT=Path('/root/t44-r9/resume-20261028-02/F-runtime-01')
def sha(raw):return hashlib.sha256(raw).hexdigest()
def read(path):
 fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW)
 with os.fdopen(fd,'rb') as stream:return stream.read()
def write(path,raw):
 fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
 with os.fdopen(fd,'wb') as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())
def call(label,argv,starting):
 remaining=STOP-time.time()
 print(json.dumps({'step':label,'remaining_seconds':remaining}),flush=True)
 if starting and remaining<600:raise ValueError('FROZEN_WINDOW_LESS_THAN_600_SECONDS_NO_NEW_START')
 result=subprocess.run(argv,capture_output=True,check=False,timeout=min(360,max(1,remaining)) if starting else 200)
 write(OUT/(label+'.stdout'),result.stdout);write(OUT/(label+'.stderr'),result.stderr)
 if result.returncode:raise ValueError('ORIGINAL_STEP_FAILED_PREFIX_PRESERVED:'+label)
 value=json.loads(result.stdout)
 if value.get('success') is not True:raise ValueError('ORIGINAL_SUCCESS_RECEIPT_REQUIRED:'+label)
 row={'step':label,'stdout_sha256':sha(result.stdout),'stdout_bytes':len(result.stdout),'receipt_id':value.get('receipt_id'),'action':value.get('action'),'success':True}
 print(json.dumps(row),flush=True);steps.append(row)
 return value
os.umask(0o077)
assert sha(read(GEN))=='4672a5838879ab1fde599c45d464906600373fdb38da654e21879881204d11a8'
raw=read(PHASE/'binding.json');assert sha(raw)==BINDING
binding=json.loads(raw)
assert binding['source_sha']==SOURCE and binding['project']=='t44-cloud-r28funcgen01-f' and binding['database']=='t44c_r28funcgen01_f' and binding['api_workers']==4 and binding['entrypoint']=='t44.api:app' and binding['profiling'] is False and binding['stop_utc']=='2026-10-28T10:30:00Z'
OUT.mkdir(mode=0o700);steps=[]
for action in ['arm','config','infra','migrate','idle']:
 argv=['/usr/bin/python3',str(GEN),action,'--phase-dir',str(PHASE),'--binding-sha256',BINDING]
 if action=='migrate':argv+=['--database','t44c_r28funcgen01_f']
 value=call('F-'+action,argv,True)
resources=value['resources'];present={row['role']:row for row in resources if not row.get('absent')}
expected={'mysql','rabbitmq','api','consumer','web','tls-gateway'}
assert expected<=set(present) and all(present[r]['state']['Running'] is True and present[r]['restart_count']==0 for r in expected)
summary={'kind':'actual-F-five-actions-complete-not-admission','source_sha':SOURCE,'binding_sha256':BINDING,'steps':steps,'host_https':value['host_https'],'resources':[{'role':r['role'],'container_id':r.get('container_id'),'image_id':r.get('image_id'),'Running':r.get('state',{}).get('Running'),'absent':r.get('absent',False)} for r in resources],'accounts_or_business_data_created_by_script':False,'performance_or_acceptance_verdict':None}
raw=(json.dumps(summary,separators=(',',':'))+'\n').encode();write(OUT/'startup-summary.PUBLIC.json',raw)
print(json.dumps(summary),flush=True)
print(json.dumps({'startup_summary_sha256':sha(raw),'output_dir':str(OUT),'next':'separate runtime-neutral snapshot after actual running'}),flush=True)
PYFSTART
