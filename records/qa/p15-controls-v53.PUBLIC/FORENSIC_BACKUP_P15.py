#!/usr/bin/env python3
"""Evidence preservation only; never treats missing result/raw as acceptance."""
import argparse,hashlib,io,json,os,sys,tarfile,time
from pathlib import Path

def digest(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for b in iter(lambda:f.read(1024**2),b''):h.update(b)
 return h.hexdigest()

def main():
 os.umask(0o077);p=argparse.ArgumentParser();p.add_argument('workspace');p.add_argument('output');p.add_argument('--attest-stopped',required=True);a=p.parse_args()
 if a.attest_stopped!='FORENSIC_ONLY_EXITED_ALL_PRODUCERS_AND_WRITERS_STOPPED':raise ValueError('STOP_ATTESTATION_REQUIRED')
 w=Path(a.workspace).resolve();out=Path(a.output).resolve();receipt=Path(str(out)+'.receipt.json')
 if not Path(a.workspace).is_absolute() or not Path(a.output).is_absolute() or not out.name.endswith('.forensic.753backup') or out==w or w in out.parents or out.exists() or receipt.exists() or not out.parent.is_dir():raise ValueError('FRESH_EXTERNAL_FORENSIC_OUTPUT_REQUIRED')
 # Only this isolated container imports installed tool/key; no plaintext stdout.
 sys.path.insert(0,str(w/'private_tools'))
 from runtime import Seal,FRAME
 key=(w/'private_tools/backup.key').read_bytes();s=Seal(out,key,64*1024**3)
 class Stream(io.RawIOBase):
  def __init__(self):self.pos=0;self.hash=hashlib.sha256()
  def writable(self):return True
  def write(self,b):
   for off in range(0,len(b),FRAME):s.frame(b[off:off+FRAME])
   self.hash.update(b);self.pos+=len(b);return len(b)
  def tell(self):return self.pos
 stream=Stream();files=[]
 with tarfile.open(fileobj=stream,mode='w|gz') as tar:
  for folder in ['functional-input','functional-results','runs','results','operator-channel','evidence-neutral']:
   base=w/folder
   if not base.exists():continue
   for path in sorted(base.rglob('*')):
    if not path.is_file() or path.is_symlink():continue
    rel=str(path.relative_to(w));before=path.stat();h=digest(path);tar.add(path,arcname=rel,recursive=False);after=path.stat()
    if (before.st_size,before.st_mtime_ns,before.st_ino)!=(after.st_size,after.st_mtime_ns,after.st_ino):raise ValueError('SOURCE_CHANGED_DURING_FORENSIC_COPY')
    files.append({'path':rel,'bytes':after.st_size,'sha256':h})
  raw=json.dumps({'schema':'753-backup-internal-manifest-v1','files':files},sort_keys=True,separators=(',',':')).encode()+b'\n';info=tarfile.TarInfo('753-internal-manifest.json');info.size=len(raw);info.mode=0o600;tar.addfile(info,io.BytesIO(raw))
 s.close({'kind':'753-backup-complete','compressed_tar_bytes':stream.pos,'compressed_tar_sha256':stream.hash.hexdigest(),'files':len(files),'created_epoch':time.time(),'purpose':'FORENSIC_ONLY_NO_MEASUREMENT_COMPLETENESS_CLAIM'})
 r={'status':'FORENSIC_ONLY_ENCRYPTED_BACKUP_REQUIRES_LOCAL_VERIFY','purpose':'FORENSIC_ONLY','run_id':'r30manualp15','backup_file':out.name,'cipher_bytes':out.stat().st_size,'cipher_sha256':digest(out),'files':len(files),'compressed_tar_sha256':stream.hash.hexdigest(),'writer_complete_asserted':False,'cohort_complete_asserted':False,'acceptance_pass_asserted':False,'operator_stop_attestation':a.attest_stopped}
 with receipt.open('x') as f:f.write(json.dumps(r,sort_keys=True)+'\n');f.flush();os.fsync(f.fileno())
 print(json.dumps(r,sort_keys=True))
if __name__=='__main__':main()
