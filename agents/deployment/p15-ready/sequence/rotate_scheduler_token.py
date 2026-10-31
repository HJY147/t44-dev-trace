"""APP-local byte-exact scheduler token rotation; neutral receipt only, no restart or HTTP."""
import argparse,hashlib,json,os,stat,subprocess,tempfile
from pathlib import Path
HERE=Path(__file__).resolve().parent
SECRETS=Path('/root/t44-final-20261029/P09/campaign/p/scheduler-secrets')
FMT='{"id":{{json .Id}},"image_id":{{json .Image}},"project":{{json (index .Config.Labels "com.docker.compose.project")}},"role":{{json (index .Config.Labels "com.docker.compose.service")}},"user":{{json .Config.User}},"mounts":{{json .Mounts}}}'
def need(v,c):
 if not v:raise ValueError(c)
def sha(b):return hashlib.sha256(b).hexdigest()
def read(p,cap=2000000):
 p=Path(p);need(p.is_absolute()and p.resolve()==p,'CANONICAL_FILE_REQUIRED')
 fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW)
 with os.fdopen(fd,'rb')as f:
  st=os.fstat(f.fileno());need(stat.S_ISREG(st.st_mode)and st.st_nlink==1 and st.st_size<=cap,'BOUNDED_SINGLE_REGULAR_FILE_REQUIRED');raw=f.read(cap+1);after=os.fstat(f.fileno())
 need((st.st_dev,st.st_ino,st.st_size,st.st_mtime_ns)==(after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns)and len(raw)==st.st_size,'STABLE_COMPLETE_FILE_REQUIRED');return raw,st
def fsync_dir(p):
 fd=os.open(p,os.O_RDONLY|os.O_DIRECTORY)
 try:os.fsync(fd)
 finally:os.close(fd)
def exclusive(p,b,uid,gid):
 fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
 with os.fdopen(fd,'wb')as f:
  os.fchown(f.fileno(),uid,gid);os.fchmod(f.fileno(),0o600);f.write(b);f.flush();os.fsync(f.fileno())
def rotate(material_file,backup_dir):
 need(os.geteuid()==0,'APP_ROOT_REQUIRED');material_file=Path(material_file);raw,unused=read(material_file);v=json.loads(raw)
 need(v.get('status')=='FRESH_MATERIAL_NOT_BENCHMARK_AUTHORIZATION'and v.get('material_process_exit_proof',{}).get('process_exit_proven')is True,'SUCCESSFUL_MATERIAL_AND_TRUE_PROCESS_EXIT_PROOF_REQUIRED')
 source=Path(v['service_credential_private_file']);need(source==material_file.parent/'service-cli.original.private.json','EXACT_HOST_RUNNER_SERVICE_FILE_REQUIRED');new,source_st=read(source)
 need(stat.S_IMODE(source_st.st_mode)==0o600 and sha(new)==v['service_cli_original_sha256'],'ORIGINAL_PRIVATE_SERVICE_BYTES_SHA_REQUIRED')
 expected=json.loads((HERE/'P09-existing-containers.PUBLIC.json').read_bytes());scheduler=next(x for x in expected['containers']if x['role']=='scheduler')
 p=subprocess.run(['docker','--context','default','inspect','--format',FMT,scheduler['id']],capture_output=True,check=False,timeout=15);need(p.returncode==0,'SCHEDULER_INSPECT_FAILED');actual=json.loads(p.stdout)
 need(all(actual.get(k)==scheduler[k]for k in ['id','image_id','project','role','user']),'EXACT_ORIGINAL_SCHEDULER_OWNER_IMAGE_REQUIRED')
 mounts=[x for x in actual['mounts']if x.get('Destination')=='/run/t44-secrets'or x.get('Destination','').startswith('/run/t44-secrets/')]
 need(len(mounts)==1 and mounts[0].get('Destination')=='/run/t44-secrets'and mounts[0].get('Type')=='bind'and mounts[0].get('RW')is False and mounts[0].get('Source')==str(SECRETS),'EXACT_READONLY_P09_SECRETS_DIRECTORY_BIND_REQUIRED')
 need(SECRETS.resolve()==SECRETS and SECRETS.is_dir(),'CANONICAL_ORIGINAL_MOUNT_DIRECTORY_REQUIRED');target=SECRETS/'scheduler-token.json';old,st=read(target)
 need(sha(old)!=sha(new),'ALREADY_SAME_ORIGINAL_BYTES_NO_REPEAT_ROTATION')
 backup_dir=Path(backup_dir);need(backup_dir.is_absolute()and backup_dir.parent.resolve()==backup_dir.parent and not backup_dir.exists(),'NEW_ROOT_PRIVATE_BACKUP_DIRECTORY_REQUIRED')
 backup_dir.mkdir(mode=0o700);os.chown(backup_dir,0,0);os.chmod(backup_dir,0o700);backup=backup_dir/'scheduler-token.original.private.json';exclusive(backup,old,0,0);fsync_dir(backup_dir);fsync_dir(backup_dir.parent)
 fd,name=tempfile.mkstemp(prefix='.scheduler-token.rotate-',dir=SECRETS);temporary=Path(name)
 try:
  with os.fdopen(fd,'wb')as f:
   os.fchown(f.fileno(),st.st_uid,st.st_gid);os.fchmod(f.fileno(),0o600);f.write(new);f.flush();os.fsync(f.fileno())
  current,current_st=read(target);need(current==old and (current_st.st_dev,current_st.st_ino,current_st.st_uid,current_st.st_gid)==(st.st_dev,st.st_ino,st.st_uid,st.st_gid),'TOKEN_CHANGED_DURING_ROTATION_NO_REPLACE')
  os.replace(temporary,target);fsync_dir(SECRETS)
 finally:
  if temporary.exists():temporary.unlink()
 reread,new_st=read(target);need(sha(reread)==v['service_cli_original_sha256']and stat.S_IMODE(new_st.st_mode)==0o600 and (new_st.st_uid,new_st.st_gid)==(st.st_uid,st.st_gid),'ATOMIC_ROTATION_READBACK_REQUIRED')
 result={'status':'SCHEDULER_TOKEN_FILE_ATOMICALLY_REPLACED_NOT_SCANNER_USE_PROOF','material_sha256':sha(raw),'scheduler_id':scheduler['id'],'mount_source':str(SECRETS),'old_sha256':sha(old),'new_original_cli_sha256':sha(reread),'uid':new_st.st_uid,'gid':new_st.st_gid,'mode':'0600','old_backup':str(backup),'private_contents_printed':False,'container_restarted':False,'scanner_HTTP_success_proven':False,'business_event_created':False}
 exclusive(backup_dir/'rotation.PUBLIC.json',(json.dumps(result,sort_keys=True,indent=2)+'\n').encode(),0,0);fsync_dir(backup_dir);return result
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--material',type=Path,required=True);p.add_argument('--backup-dir',type=Path,required=True);a=p.parse_args();os.umask(0o077);print(json.dumps(rotate(a.material,a.backup_dir),sort_keys=True))
