"""Read only bounded public APP state and process ownership; never read private logs or credentials."""
import hashlib,json,subprocess,datetime,time
from pathlib import Path
R=Path('/root/t44-final-20261029')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
report={'kind':'APP_FINAL_PUBLIC_STATUS_ONLY','private_file_contents_read':False,'units':{},'files':{},'owned_running':[]}
report['observed_utc']=datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
report['observed_kernel_boot_utc']=datetime.datetime.fromtimestamp(time.time()-float(Path('/proc/uptime').read_text().split()[0]),datetime.timezone.utc).isoformat()
report['observed_uptime_seconds']=float(Path('/proc/uptime').read_text().split()[0])
report['old_cutoff_utc']='2026-10-29T17:58:00Z'
report['old_P_latest_freeze_utc']='2026-10-29T17:13:00Z'
report['old_window_reuse_authorized']=False
report['public_attempt_directories']={n:(R/n).is_dir() for n in ['F02','F03','P03','r30finalf03-launcher','r30finalp03-launcher']}
for unit in ['t44-final-f02-prepare','t44-final-f03-continuous-v2','t44-final-f03-continuous','t44-final-f03-transport-v2','t44-final-p03-continuous']:
 q=subprocess.run(['systemctl','show',unit,'--property=ActiveState,SubState,Result,ExecMainStatus,ExecMainCode,ExecMainStartTimestamp,ExecMainExitTimestamp'],capture_output=True,check=False,timeout=10)
 report['units'][unit]={'returncode':q.returncode,'properties':dict(x.split('=',1) for x in q.stdout.decode().splitlines() if '=' in x)}
for rel in ['F03/timeplan.PUBLIC.json','F03/campaign/f/binding.json','P03/timeplan.PUBLIC.json','F02/preparation.PUBLIC.json','F03/preparation.PUBLIC.json','r30finalf03-launcher/F-ready.PUBLIC.json','F03/transport-seal.PUBLIC.json','F03/LOAD-bootstrap.original.PUBLIC.json','P03/preparation.PUBLIC.json','P03/LOAD-bootstrap.original.PUBLIC.json']:
 p=R/rel
 if not p.is_file():report['files'][rel]={'exists':False};continue
 if p.is_symlink() or p.stat().st_size>200000:raise ValueError('UNEXPECTED_PUBLIC_OBJECT')
 v=json.loads(p.read_bytes());record={'exists':True,'bytes':p.stat().st_size,'sha256':sha(p),'status':v.get('status')}
 if 'phase' in v:record['phase']=v['phase']
 if rel.endswith('timeplan.PUBLIC.json'):record['clock']={k:v.get(k) for k in ['run_id','actual_first_boot_utc','t0_utc','start_utc','end_utc','stop_utc','cost_stop_utc','absolute_cost_cutoff_utc']}
 if rel.endswith('binding.json'):record['binding']={k:v.get(k) for k in ['phase','project','database','stop_utc','timer_unit','source_sha']}
 if 'steps' in v:record['steps']=[{'label':x['label'],'returncode':x['returncode']} for x in v['steps']]
 if 'timeplan' in v:record['timeplan']=v['timeplan']
 report['files'][rel]=record
q=subprocess.run(['docker','--context','default','ps','--format','{{json .}}','--filter','label=com.docker.compose.project'],check=True,capture_output=True,timeout=20)
for line in q.stdout.decode().splitlines():
 row=json.loads(line)
 if 'r30finalf02' in row.get('Names','') or 'r30finalf03' in row.get('Names','') or 'r30finalp03' in row.get('Names',''):report['owned_running'].append({k:row.get(k) for k in ['ID','Names','Image','Status','Ports']})
print(json.dumps(report,sort_keys=True))
