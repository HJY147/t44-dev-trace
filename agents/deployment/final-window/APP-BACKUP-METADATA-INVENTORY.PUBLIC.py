"""Read only T44 root directory sizes, Docker metadata and systemd status; never file contents/env."""
import datetime,json,subprocess
from pathlib import Path

def command(argv,timeout=30):
 r=subprocess.run(argv,capture_output=True,check=False,timeout=timeout)
 if r.returncode: return {'returncode':r.returncode}
 return r.stdout.decode(errors='replace')
def docker(*args):return command(['docker','--context','default',*args])
def main():
 report={'kind':'APP_T44_BACKUP_SELECTION_METADATA_ONLY','observed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'directory_sizes':[],'volumes':[],'containers':[],'systemd':{},'private_file_contents_read':False,'backup_or_cleanup_executed':False}
 for p in sorted(Path('/root').iterdir()):
  if not p.name.lower().startswith('t44') or not p.is_dir() or p.is_symlink():continue
  # Size traversal only; no names/contents below QA, credential or data paths are emitted.
  try:
   out=command(['du','-sk','-x','--',str(p)],20)
   report['directory_sizes'].append({'path':str(p),'size_KiB':int(out.split()[0])} if isinstance(out,str) else {'path':str(p),'size_unavailable':out})
  except subprocess.TimeoutExpired:report['directory_sizes'].append({'path':str(p),'size_unavailable':'timeout20s'})
 ids=docker('volume','ls','--quiet')
 if isinstance(ids,str):
  for name in ids.splitlines():
   raw=docker('volume','inspect',name)
   if not isinstance(raw,str):continue
   for v in json.loads(raw):
    project=(v.get('Labels') or {}).get('com.docker.compose.project','')
    if name.lower().startswith('t44') or project.startswith('t44'):report['volumes'].append({k:v.get(k) for k in ['Name','Driver','Mountpoint','CreatedAt','Labels','Scope']})
 ids=docker('ps','--all','--quiet','--no-trunc','--filter','label=com.docker.compose.project')
 if isinstance(ids,str):
  for cid in ids.splitlines():
   raw=docker('inspect',cid)
   if not isinstance(raw,str):continue
   row=json.loads(raw)[0];labels=row['Config'].get('Labels') or {};project=labels.get('com.docker.compose.project','')
   if not project.startswith('t44'):continue
   mounts=[{k:m.get(k) for k in ['Type','Name','Source','Destination','RW','Propagation']} for m in row.get('Mounts',[])]
   report['containers'].append({'id':row['Id'],'name':row['Name'],'compose_project':project,'compose_service':labels.get('com.docker.compose.service'),'image_id':row['Image'],'configured_user':row['Config'].get('User'),'running':row['State']['Running'],'status':row['State']['Status'],'mounts':mounts})
  # Runtime UID and PID only; omit argv, environment and command contents.
  running=[c['id'] for c in report['containers'] if c['running']]
  for cid in running:
   top=docker('top',cid,'-eo','uid,pid')
   for row in report['containers']:
    if row['id']==cid:row['running_UID_PID']=top
 for key,args in {'units':['list-units','--all','--plain','--no-legend','--no-pager','t44*'],'timers':['list-timers','--all','--no-legend','--no-pager','t44*']}.items():report['systemd'][key]=command(['systemctl',*args])
 print(json.dumps(report,sort_keys=True))
if __name__=='__main__':main()
