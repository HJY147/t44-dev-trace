"""User-executed local-file receiver only: original public archive/bootstrap, no INSTALL/790/QA."""
import argparse,base64,hashlib,io,json,os,tarfile
from pathlib import Path,PurePosixPath
PACKAGE_SHA='0b3d4d6ba68dc1fa27930963b9442b0bf8e2c2ae61d2860233e1754f4dbb61a9'
MANIFEST_SHA='676458385bfd64abcba3e4c6c80f4bb773545d28c46061c113670c411df4a27b'
def sha(b):return hashlib.sha256(b).hexdigest()
def validate_archive(raw):
 files={}
 with tarfile.open(fileobj=io.BytesIO(raw),mode='r:gz')as archive:
  for member in archive.getmembers():
   name=PurePosixPath(member.name)
   if name.is_absolute()or'..'in name.parts or str(name)!=member.name:raise ValueError('UNSAFE_ARCHIVE_PATH')
   if member.isdir()and member.name=='public/__pycache__':continue
   if not member.isfile()or len(name.parts)!=2 or name.parts[0]!='public'or member.size>200000:raise ValueError('EXACT_PUBLIC_REGULAR_FILES_ONLY')
   if member.name in files:raise ValueError('DUPLICATE_ARCHIVE_MEMBER')
   files[member.name]=archive.extractfile(member).read()
 manifest_raw=files['public/DELIVERY_MANIFEST.PUBLIC.json']
 if sha(manifest_raw)!=MANIFEST_SHA:raise ValueError('ORIGINAL_MANUAL_MANIFEST_SHA_REQUIRED')
 manifest=json.loads(manifest_raw)
 if set(files)!={'public/'+n for n in manifest['files']}|{'public/DELIVERY_MANIFEST.PUBLIC.json'}:raise ValueError('EXACT_ORIGINAL_PUBLIC_FILE_SET')
 for n,h in manifest['files'].items():
  if sha(files['public/'+n])!=h:raise ValueError('ORIGINAL_PUBLIC_MEMBER_SHA_REQUIRED')
 return files
def receive(meta,bootstrap,parts_dir,workspace):
 if sha(bootstrap)!=meta['bootstrap_sha256']or len(bootstrap)!=meta['bootstrap_bytes']:raise ValueError('ORIGINAL_BOOTSTRAP_SHA_REQUIRED')
 json.loads(bootstrap);raw=b''
 for row in meta['parts']:
  name=row['name']
  if Path(name).name!=name:raise ValueError('PART_BASENAME_ONLY')
  p=Path(parts_dir)/name
  if p.is_symlink()or p.stat().st_size!=row['bytes']:raise ValueError('PART_REGULAR_EXACT_SIZE_REQUIRED')
  b=p.read_bytes()
  if sha(b)!=row['sha256']:raise ValueError('PART_SHA_REQUIRED')
  raw+=b
 if len(raw)!=86788 or sha(raw)!=PACKAGE_SHA or meta['archive_sha256']!=PACKAGE_SHA:raise ValueError('ORIGINAL_MANUAL_PACKAGE_SHA_REQUIRED')
 files=validate_archive(raw);w=Path(workspace)
 if not w.is_absolute()or w.resolve()!=w or w.exists():raise ValueError('NEW_CANONICAL_WORKSPACE_NO_OVERWRITE')
 w.mkdir(mode=0o700);(w/'public').mkdir(mode=0o700)
 def put(p,b):
  with p.open('xb')as out:out.write(b)
  p.chmod(0o600)
 put(w/'MANUAL_TOOL_V4.original.PUBLIC.tar.gz',raw);put(w/'bootstrap.original.PUBLIC.json',bootstrap)
 for name,b in files.items():put(w/name,b)
 receipt={'status':'ORIGINAL_PUBLIC_BUNDLE_AND_BOOTSTRAP_STAGED_ONLY','archive_sha256':sha(raw),'bootstrap_sha256':sha(bootstrap),'workspace':str(w),'files':{n:sha(b)for n,b in files.items()},'INSTALL_790_QA_executed':False,'SUT_requests':0}
 put(w/'transport-receipt.PUBLIC.json',(json.dumps(receipt,sort_keys=True,indent=2)+'\n').encode());return receipt
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--manifest',type=Path,required=True);p.add_argument('--bootstrap',type=Path,required=True);p.add_argument('--parts-dir',type=Path,required=True);p.add_argument('--workspace',type=Path,required=True);a=p.parse_args();os.umask(0o077);print(json.dumps(receive(json.loads(a.manifest.read_bytes()),a.bootstrap.read_bytes(),a.parts_dir,a.workspace),sort_keys=True))
