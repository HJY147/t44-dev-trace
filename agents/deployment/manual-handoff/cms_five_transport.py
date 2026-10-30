"""User-run standard OpenSSL3 CMS AES256-GCM transport; private data never printed."""
import argparse,datetime,hashlib,io,json,os,stat,subprocess,tarfile
from pathlib import Path
NAMES={'session.private.json','ca.pem','source-manifest.json','backend-bundle-manifest.json','backend-import-receipt.json'}
CAP=4*1024*1024
def sha(b):return hashlib.sha256(b).hexdigest()
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def need(v,c):
 if not v:raise ValueError(c)
def read(p,cap=CAP):
 p=Path(p);need(p.is_absolute()and p.resolve()==p,'CANONICAL_FILE_REQUIRED')
 fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW)
 with os.fdopen(fd,'rb')as f:
  st=os.fstat(f.fileno());need(stat.S_ISREG(st.st_mode)and st.st_nlink==1 and st.st_size<=cap,'BOUNDED_REGULAR_FILE_REQUIRED');raw=f.read(cap+1);after=os.fstat(f.fileno())
 need((st.st_ino,st.st_size,st.st_mtime_ns)==(after.st_ino,after.st_size,after.st_mtime_ns)and len(raw)==st.st_size,'STABLE_FILE_REQUIRED');return raw
def put(p,b):
 p=Path(p);need(p.is_absolute()and p.parent.resolve()==p.parent,'CANONICAL_NEW_OUTPUT_REQUIRED')
 fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
 with os.fdopen(fd,'wb')as f:f.write(b)
def command(binary,args,input=None):
 try:p=subprocess.run([binary,*map(str,args)],input=input,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=False,timeout=60)
 except (OSError,subprocess.TimeoutExpired):raise ValueError('OPENSSL_UNAVAILABLE_OR_TIMEOUT')from None
 need(p.returncode==0,'OPENSSL_OPERATION_FAILED_NO_PRIVATE_OUTPUT');return p.stdout
def modern(binary):need(command(binary,['version']).startswith(b'OpenSSL 3.'),'OPENSSL3_CMS_GCM_REQUIRED_NO_CBC_FALLBACK')
def cert(binary,key,output):
 modern(binary);need(not Path(output).exists(),'CERT_OUTPUT_EXISTS_NO_OVERWRITE')
 # Key is opened only by the original LOAD-local openssl process, never read/exported by Python.
 raw=command(binary,['req','-new','-x509','-sha256','-key',key,'-days','1','-subj','/CN=T44-LOAD-file-recipient-only','-addext','basicConstraints=critical,CA:FALSE','-addext','keyUsage=critical,keyEncipherment','-addext','extendedKeyUsage=emailProtection'])
 put(output,raw);return {'status':'PUBLIC_FILE_RECIPIENT_CERT_CREATED','cert_sha256':sha(raw),'cert':str(output),'private_key_exported':False,'TLS_or_access_rights_changed':False,'created_utc':now()}
def seal(binary,inputs,certificate,cert_sha,output):
 modern(binary);cert_raw=read(certificate);need(sha(cert_raw)==cert_sha,'PINNED_LOAD_PUBLIC_CERT_SHA_REQUIRED')
 command(binary,['x509','-in',certificate,'-checkend','0','-noout'])
 directory=Path(inputs);need(directory.is_absolute()and directory.resolve()==directory and not directory.is_symlink(),'CANONICAL_HOST_FIVE_DIRECTORY_REQUIRED');need({p.name for p in directory.iterdir()}==NAMES,'EXACT_HOST_FIVE_REQUIRED')
 files={n:read(directory/n)for n in NAMES};need(sum(map(len,files.values()))<=CAP,'FIVE_CAP4M_REQUIRED')
 manifest={'schema':'cms-five-byte-preservation-v1','files':{n:{'bytes':len(b),'sha256':sha(b)}for n,b in files.items()}}
 buffer=io.BytesIO()
 with tarfile.open(fileobj=buffer,mode='w')as t:
  for name,b in sorted(files.items()):
   member=tarfile.TarInfo('inputs/'+name);member.size=len(b);member.mode=0o600;member.mtime=0;t.addfile(member,io.BytesIO(b))
 plain=buffer.getvalue();cipher=command(binary,['cms','-encrypt','-binary','-aes-256-gcm','-outform','DER','-recip',certificate,'-keyopt','rsa_padding_mode:oaep','-keyopt','rsa_oaep_md:sha256'],plain)
 out=Path(output);need(not out.exists()and not Path(str(out)+'.PUBLIC.json').exists(),'CIPHER_OR_RECEIPT_EXISTS_NO_OVERWRITE');put(out,cipher)
 receipt={'status':'SEALED_HOST_FIVE_CMS_ONLY_NOT_QA','created_utc':now(),'algorithm':'OpenSSL CMS AuthEnvelopedData AES-256-GCM RSA-OAEP-SHA256','cert_sha256':cert_sha,'cipher_sha256':sha(cipher),'cipher_bytes':len(cipher),'plain_tar_sha256':sha(plain),**manifest,'private_contents_printed':False,'original_packet_bytes_changed':False}
 put(str(out)+'.PUBLIC.json',(json.dumps(receipt,sort_keys=True,indent=2)+'\n').encode());return receipt
def unpack_plain(plain,receipt):
 need(sha(plain)==receipt['plain_tar_sha256'],'ORIGINAL_PLAIN_TAR_SHA_REQUIRED');files={}
 with tarfile.open(fileobj=io.BytesIO(plain),mode='r:')as t:
  for m in t.getmembers():
   name=m.name.removeprefix('inputs/')
   need(m.name=='inputs/'+name,'EXACT_INPUTS_PREFIX_REQUIRED')
   need(name in NAMES and m.isfile()and m.size<=CAP and name not in files,'EXACT_FIVE_REGULAR_MEMBERS_ONLY');files[name]=t.extractfile(m).read(CAP+1)
 need(set(files)==NAMES and sum(map(len,files.values()))<=CAP,'EXACT_FIVE_CAP_REQUIRED')
 need({n:{'bytes':len(b),'sha256':sha(b)}for n,b in files.items()}==receipt['files'],'ORIGINAL_FIVE_SHA_REQUIRED');return files
def opened(binary,cipher,receipt_file,certificate,cert_sha,key,output):
 modern(binary);need(sha(read(certificate))==cert_sha,'PINNED_LOAD_PUBLIC_CERT_SHA_REQUIRED');raw=read(cipher,CAP+65536);receipt=json.loads(read(receipt_file))
 need(receipt['cert_sha256']==cert_sha and sha(raw)==receipt['cipher_sha256']and len(raw)==receipt['cipher_bytes'],'ORIGINAL_CIPHER_SHA_REQUIRED')
 out=Path(output);need(out.is_absolute()and out.parent.resolve()==out.parent and not out.exists(),'NEW_CANONICAL_OPENED_DIRECTORY_REQUIRED')
 # stdout is captured to process memory; no unauthenticated plaintext is written if CMS/GCM fails.
 plain=command(binary,['cms','-decrypt','-binary','-inform','DER','-recip',certificate,'-inkey',key],raw);files=unpack_plain(plain,receipt)
 out.mkdir(mode=0o700);(out/'inputs').mkdir(mode=0o700)
 for name,b in files.items():put(out/('inputs/'+name),b)
 result={'status':'ORIGINAL_FIVE_OPENED_LOCALLY_NOT_QA','opened':str(out),'cipher_sha256':sha(raw),'plain_tar_sha256':sha(plain),'cert_sha256':cert_sha,'files':receipt['files'],'private_contents_printed':False,'old790_or_C_used':False}
 put(out/'CMS-transport-receipt.PUBLIC.json',(json.dumps(result,sort_keys=True,indent=2)+'\n').encode());return result
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--openssl',default='openssl');sub=p.add_subparsers(dest='action',required=True)
 c=sub.add_parser('cert');c.add_argument('--key',required=True);c.add_argument('--output',type=Path,required=True)
 s=sub.add_parser('seal');s.add_argument('--inputs',type=Path,required=True);s.add_argument('--cert',type=Path,required=True);s.add_argument('--cert-sha256',required=True);s.add_argument('--output',type=Path,required=True)
 o=sub.add_parser('open');o.add_argument('--cipher',type=Path,required=True);o.add_argument('--receipt',type=Path,required=True);o.add_argument('--cert',type=Path,required=True);o.add_argument('--cert-sha256',required=True);o.add_argument('--key',required=True);o.add_argument('--output',type=Path,required=True)
 a=p.parse_args();os.umask(0o077)
 if a.action=='cert':v=cert(a.openssl,a.key,a.output)
 elif a.action=='seal':v=seal(a.openssl,a.inputs,a.cert,a.cert_sha256,a.output)
 else:v=opened(a.openssl,a.cipher,a.receipt,a.cert,a.cert_sha256,a.key,a.output)
 print(json.dumps(v,sort_keys=True))
if __name__=='__main__':main()
