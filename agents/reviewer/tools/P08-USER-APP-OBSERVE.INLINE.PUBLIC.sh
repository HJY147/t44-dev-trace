umask 077
python3 -B - <<'P08_READ_ONLY'
import base64,datetime,hashlib,json,os,stat,subprocess,zlib
from pathlib import Path
R=Path('/root/t44-final-20261029');P=R/'P08';PROJECT='t44-cloud-r30finalp08-p'
def docker(*args):
 r=subprocess.run(['docker','--context','default',*args],capture_output=True,text=True,timeout=8)
 if r.returncode:raise RuntimeError('DOCKER_READ_FAILED:'+str(r.returncode))
 return r.stdout
report={'kind':'USER_P08_READ_ONLY_OBSERVATION','observed_utc':datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),'project':PROJECT,'cloud_or_SUT_or_QA_actions':0,'PUBLIC_files':{},'missing_PUBLIC_files':[],'database_SQL_executed':False}
ids=docker('ps','-aq','--no-trunc','--filter','label=com.docker.compose.project='+PROJECT).split()
fmt='{"Id":{{json .Id}},"Name":{{json .Name}},"Image":{{json .Image}},"project":{{json (index .Config.Labels "com.docker.compose.project")}},"role":{{json (index .Config.Labels "com.docker.compose.service")}},"status":{{json .State.Status}},"running":{{json .State.Running}},"restarting":{{json .State.Restarting}},"exit_code":{{json .State.ExitCode}},"oom":{{json .State.OOMKilled}},"pid":{{json .State.Pid}},"NanoCpus":{{json .HostConfig.NanoCpus}},"Memory":{{json .HostConfig.Memory}},"MemorySwap":{{json .HostConfig.MemorySwap}},"PidsLimit":{{json .HostConfig.PidsLimit}},"networks":{{json .NetworkSettings.Networks}},"cmd":{{json .Config.Cmd}}}'
rows=[json.loads(x) for x in docker('inspect','--format',fmt,*ids).splitlines()] if ids else []
for row in rows:
 cmd=row.pop('cmd') or [];row['configured_API_workers']=None
 if row['role']=='api' and '--workers' in cmd:row['configured_API_workers']=int(cmd[cmd.index('--workers')+1])
report['containers']=rows
roles=[x['role'] for x in rows];expected={'mysql','rabbitmq','api','consumer','scheduler','web','tls-gateway'}
report['seven_roles_exact']=len(rows)==7 and set(roles)==expected and len(set(roles))==7
running=docker('ps','-q','--no-trunc').split();other=[]
short='{"Id":{{json .Id}},"Name":{{json .Name}},"project":{{json (index .Config.Labels "com.docker.compose.project")}}}'
for line in (docker('inspect','--format',short,*running).splitlines() if running else []):
 x=json.loads(line)
 if ((x.get('project') or '').startswith('t44') or x['Name'].lstrip('/').startswith('t44')) and x.get('project')!=PROJECT:other.append(x)
report['other_T44_running']=other;report['no_other_T44_running']=not other
active=[x['Id'] for x in rows if x['running']]
try:report['resource_usage']=[json.loads(x) for x in docker('stats','--no-stream','--format','{{json .}}',*active).splitlines()] if active else []
except (RuntimeError,subprocess.TimeoutExpired):report['resource_usage']='UNAVAILABLE_READ_TIMEOUT_OR_ERROR'
for row in rows:
 if row['role']!='api' or not row['running']:continue
 try:
  top=docker('top',row['Id'],'-eo','uid,pid,ppid,args').splitlines()[1:];proc=[]
  for line in top:
   fields=line.split(None,3)
   if len(fields)!=4:continue
   uid,pid,ppid,args=fields
   kind='tracker' if 'multiprocessing.resource_tracker' in args else 'spawn_worker' if 'multiprocessing.spawn' in args or '--multiprocessing-fork' in args else 'uvicorn_parent' if 'uvicorn' in args else 'other'
   proc.append({'uid':uid,'pid':pid,'ppid':ppid,'kind':kind})
  report['API_processes']=proc;report['observed_spawn_workers']=sum(x['kind']=='spawn_worker' for x in proc)
 except (RuntimeError,subprocess.TimeoutExpired):report['API_processes']='UNAVAILABLE_READ_TIMEOUT_OR_ERROR'
def collect(label,p):
 p=Path(p)
 if not p.exists():report['missing_PUBLIC_files'].append(label);return None
 if not p.is_absolute() or p.resolve()!=p or not p.is_relative_to(R) or not stat.S_ISREG(p.lstat().st_mode) or p.stat().st_size>1048576:raise ValueError('PUBLIC_FILE_PATH_OR_BOUND:'+label)
 b=p.read_bytes();report['PUBLIC_files'][label]={'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'encoding':'zlib+base64','zlib_b64':base64.b64encode(zlib.compress(b,9)).decode()}
 return json.loads(b)
collect('timeplan',P/'timeplan.PUBLIC.json')
prep=collect('preparation',P/'preparation.PUBLIC.json')
collect('LOAD_bootstrap',P/'LOAD-bootstrap.original.PUBLIC.json')
receipt=(prep or {}).get('import',{}).get('receipt')
if receipt and ('PUBLIC' in Path(receipt).name or Path(receipt).name=='backend-import-receipt.json'):collect('backend_import_receipt',receipt)
else:collect('backend_import_receipt',P/'P-packet/output/packet/inputs/backend-import-receipt.json')
report['already_PUBLIC_counts']={k:v for k,v in (prep or {}).items() if 'count' in k.lower() and isinstance(v,dict) and all(type(x) is int for x in v.values())}
report['actors_note']='No PRIVATE account/session files or SQL read; only any existing PUBLIC preparation bytes are collected.'
report['finished_utc']=datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
print(json.dumps(report,sort_keys=True,separators=(',',':')))
P08_READ_ONLY
