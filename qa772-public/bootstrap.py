#!/usr/bin/env python3
"""Generic opaque-capsule installer. Requires a privately delivered 32-byte key."""
import gzip,hashlib,hmac,io,json,os,struct,sys,tarfile
from pathlib import Path
os.umask(0o077)
MAGIC=b'772-SEAL-v1\x00'
def require(ok,msg):
 if not ok:raise ValueError(msg)
def main():
 if len(sys.argv)!=4:raise SystemExit('bootstrap.py OPAQUE_CAPSULE PRIVATE_KEY NEW_PRIVATE_DIRECTORY')
 capsule,keyfile,dest=map(Path,sys.argv[1:]);require(keyfile.stat().st_mode&0o077==0,'private key permissions');key=keyfile.read_bytes();require(len(key)==32,'32-byte private key required');require(not dest.exists(),'new destination required');payload=bytearray();footer=None
 with capsule.open('rb') as f:
  require(f.read(len(MAGIC))==MAGIC,'capsule format');salt=f.read(32);enc=hmac.digest(key,b'772/enc/'+salt,'sha256');mac=hmac.digest(key,b'772/mac/'+salt,'sha256');chain=hmac.digest(mac,MAGIC+salt,'sha256');require(hmac.compare_digest(f.read(32),chain),'header authentication');seq=0
  while True:
   head=f.read(13)
   if not head:break
   require(len(head)==13,'incomplete frame');kind,num,size=struct.unpack('>BQI',head);require(num==seq and size<=262144,'frame bounds');cipher=f.read(size);tag=f.read(32);require(len(cipher)==size and hmac.compare_digest(tag,hmac.digest(mac,chain+head+cipher,'sha256')),'frame authentication');stream=hashlib.shake_256(enc+salt+struct.pack('>Q',seq)).digest(size);plain=(int.from_bytes(cipher,'big')^int.from_bytes(stream,'big')).to_bytes(size,'big') if size else b'';chain=tag;seq+=1
   if kind==255:require(footer is None,'duplicate footer');footer=json.loads(plain);require(f.read(1)==b'','trailing data');break
   require(kind==1 and footer is None,'frame kind');payload.extend(plain);require(len(payload)<=8*1024*1024,'capsule bound')
 require(footer is not None and footer['payload_sha256']==hashlib.sha256(payload).hexdigest(),'complete capsule required');dest.mkdir(mode=0o700,parents=True)
 with tarfile.open(fileobj=io.BytesIO(payload),mode='r:gz') as tar:
  members=tar.getmembers();require(len(members)<=12,'member count')
  for m in members:require(m.isfile() and '/' not in m.name and m.name not in ('','.','..') and m.size<=2*1024*1024,'safe flat regular files')
  for m in members:
   data=tar.extractfile(m).read();p=dest/m.name;p.write_bytes(data);p.chmod(0o700 if p.suffix=='.py' else 0o600)
 print(json.dumps({'status':'INSTALLED_PRIVATE','capsule_sha256':hashlib.sha256(capsule.read_bytes()).hexdigest(),'file_count':len(members)}))
if __name__=='__main__':main()
