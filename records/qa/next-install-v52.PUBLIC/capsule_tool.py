#!/usr/bin/env python3
"""Public opaque transport; no product/test cases, keys or target result."""
import argparse,hashlib,hmac,io,json,os,struct,sys,zipfile
from pathlib import Path
MAGIC=b'753-CAPSULE-v1\0';MAX=8*1024**2;FRAME=262144
def check(x,m):
 if not x:raise ValueError(m)
def digest(b):return hashlib.sha256(b).hexdigest()
def keys(key,salt):return hmac.digest(key,b'753/enc/'+salt,'sha256'),hmac.digest(key,b'753/mac/'+salt,'sha256')
def seal(plain,key):
 salt=os.urandom(32);enc,mac=keys(key,salt);chain=hmac.digest(mac,MAGIC+salt,'sha256');out=bytearray(MAGIC+salt+chain)
 for num,off in enumerate(range(0,len(plain),FRAME)):
  p=plain[off:off+FRAME];head=struct.pack('>QI',num,len(p));stream=hashlib.shake_256(enc+salt+struct.pack('>Q',num)).digest(len(p));c=(int.from_bytes(p,'big')^int.from_bytes(stream,'big')).to_bytes(len(p),'big');tag=hmac.digest(mac,chain+head+c,'sha256');out.extend(head+c+tag);chain=tag
 footer=struct.pack('>QI',(len(plain)+FRAME-1)//FRAME,0);out.extend(footer+hmac.digest(mac,chain+footer,'sha256'));return bytes(out)
def unseal(blob,key):
 check(len(blob)<=MAX and blob.startswith(MAGIC),'CAPSULE_BOUND_OR_MAGIC');s=io.BytesIO(blob);s.read(len(MAGIC));salt=s.read(32);enc,mac=keys(key,salt);chain=hmac.digest(mac,MAGIC+salt,'sha256');check(hmac.compare_digest(s.read(32),chain),'HEADER_AUTH');num=0;out=bytearray()
 while True:
  head=s.read(12);check(len(head)==12,'TRUNCATED');n,size=struct.unpack('>QI',head);check(n==num and size<=FRAME,'FRAME');cipher=s.read(size);tag=s.read(32);check(hmac.compare_digest(tag,hmac.digest(mac,chain+head+cipher,'sha256')),'CAPSULE_AUTH')
  if size==0:check(s.read()==b'','TRAILING');return bytes(out)
  stream=hashlib.shake_256(enc+salt+struct.pack('>Q',num)).digest(size);out.extend((int.from_bytes(cipher,'big')^int.from_bytes(stream,'big')).to_bytes(size,'big'));chain=tag;num+=1;check(len(out)<=MAX,'PLAIN_BOUND')
def open_capsule(capsule,keyfile,manifest,dest):
 raw=Path(manifest).read_bytes();m=json.loads(raw);blob=Path(capsule).read_bytes();check(digest(blob)==m['capsule_sha256'],'CIPHER_SHA');key=Path(keyfile).read_bytes();check(len(key)==32,'KEY_LENGTH');plain=unseal(blob,key);check(digest(plain)==m['archive_sha256'],'ARCHIVE_SHA');d=Path(dest);check(not d.exists(),'FRESH_DEST_REQUIRED')
 with zipfile.ZipFile(io.BytesIO(plain))as z:
  check(set(z.namelist())==set(m['files']),'FILE_SET')
  contents={}
  for n,h in m['files'].items():
   check(not n.startswith('/') and '..'not in Path(n).parts and len(Path(n).parts)==1,'SAFE_ENTRY');data=z.read(n);check(digest(data)==h,'FILE_SHA');contents[n]=data
 d.mkdir(mode=0o700,parents=True)
 for n,data in contents.items():p=d/n;p.write_bytes(data);p.chmod(0o600)
 return {'status':'OPAQUE_INSTALLED_NO_SUT_CONTACT','capsule_sha256':m['capsule_sha256'],'archive_sha256':m['archive_sha256'],'file_count':len(contents),'runtime_core_sha256':m['runtime_core_sha256'],'functional_sha256':m['functional_sha256'],'SUT_requests':0}
def main():
 os.umask(0o077);p=argparse.ArgumentParser();p.add_argument('mode',choices=['open']);p.add_argument('--capsule',required=True);p.add_argument('--key-file',required=True);p.add_argument('--manifest',required=True);p.add_argument('--dest',required=True);a=p.parse_args();print(json.dumps(open_capsule(a.capsule,a.key_file,a.manifest,a.dest),separators=(',',':')))
if __name__=='__main__':main()
