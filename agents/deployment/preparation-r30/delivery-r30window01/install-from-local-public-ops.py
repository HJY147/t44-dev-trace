import base64,gzip,hashlib,io,json,os,pathlib,sys,tarfile
base=pathlib.Path('/root/t44-r30/r30window01/ops')
assert base.parent.resolve()==base.parent
base.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
base.mkdir(mode=0o700)
archive=pathlib.Path(sys.argv[1])
blob=archive.read_bytes()
assert len(blob)==78319 and hashlib.sha256(blob).hexdigest()=='894b4b50b957bde282eda8d7f10bf7d48c68dba28ed56ececcf0195d30c0c2cf'
raw=gzip.decompress(blob)
assert len(raw)==327680 and hashlib.sha256(raw).hexdigest()=='712d238423105059eb5032c594c74934d77c21dffeba0e179cc7df6d5fff4574'
files={}
with tarfile.open(fileobj=io.BytesIO(raw),mode='r:') as archive:
 for m in archive.getmembers():
  path=pathlib.PurePosixPath(m.name)
  assert m.isfile() and not path.is_absolute() and '..' not in path.parts and str(path)==m.name and m.name not in files and m.size<=262144
  files[m.name]=archive.extractfile(m).read()
assert len(files)==29 and hashlib.sha256(files['bundle-manifest.PUBLIC.json']).hexdigest()=='97318c29dab1a32bef641588917b816c2c56b48597cb68b62d86b200c30604e6'
manifest=json.loads(files['bundle-manifest.PUBLIC.json'])
assert set(files)==set(manifest['files'])|{'bundle-manifest.PUBLIC.json'}
for name,want in manifest['files'].items():
 assert len(files[name])==want['bytes'] and hashlib.sha256(files[name]).hexdigest()==want['sha256']
for name,content in files.items():
 target=base/name
 target.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
 fd=os.open(target,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
 with os.fdopen(fd,'wb') as f:f.write(content);f.flush();os.fsync(f.fileno())
print(json.dumps({'kind':'R30_PUBLIC_OPS_INSTALLED_NOT_RUN','path':str(base),'bundle_sha256':'894b4b50b957bde282eda8d7f10bf7d48c68dba28ed56ececcf0195d30c0c2cf','files':29,'SUT_services_started':False,'sessions_issued':False}))