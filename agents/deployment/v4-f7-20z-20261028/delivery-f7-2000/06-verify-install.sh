python3 - <<'PY'
REMOTE_ROOT='/root/t44-r9/v4-code-20261028-03'
MANIFEST_SHA='60c234aca7b0eded3382ef209b079d5ac45ebe55d8d93e1ba7d10b7b4d6060f3'
MANIFEST_BYTES=1943
SOURCE='f7cdb5fa3b19f84d8ab0d0b042bf51a5b8484e8f'
STOP='2026-10-28T20:00:00Z'
import hashlib,json,os,stat,zlib
from pathlib import Path
root=Path(REMOTE_ROOT)
def sha(raw): return hashlib.sha256(raw).hexdigest()
def checked(path,expected,n):
 fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW)
 with os.fdopen(fd,'rb') as f:
  s=os.fstat(f.fileno())
  if not stat.S_ISREG(s.st_mode) or s.st_uid!=os.geteuid() or stat.S_IMODE(s.st_mode)!=0o600 or s.st_nlink!=1: raise ValueError('EXACT_OWNED_PRIVATE_FILE_REQUIRED')
  raw=f.read(n+1)
 if len(raw)!=n or sha(raw)!=expected: raise ValueError('EXACT_BYTES_SHA_REQUIRED')
 return raw
def write(path,raw):
 fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
 with os.fdopen(fd,'wb') as f: f.write(raw);f.flush();os.fsync(f.fileno())
if root.resolve()!=root or not root.is_dir(): raise ValueError('CANONICAL_NEW_ROOT_REQUIRED')
manifest=json.loads(checked(root/'manifest.PUBLIC.json',MANIFEST_SHA,MANIFEST_BYTES))
if manifest['source_sha']!=SOURCE or manifest['stop_utc']!=STOP: raise ValueError('SOURCE_WINDOW_REQUIRED')
rows=manifest['parts']
if set(p.name for p in (root/'parts').iterdir())!={r['path'] for r in rows}: raise ValueError('EXACT_PART_SET_REQUIRED')
joined=b''
for i,row in enumerate(rows):
 if row['path']!=f'{i:03}.bin' or not 0<row['bytes']<=7500: raise ValueError('EXACT_ORDER_BOUNDED_PART_REQUIRED')
 joined+=checked(root/'parts'/row['path'],row['sha256'],row['bytes'])
if len(joined)!=manifest['gzip_bytes'] or sha(joined)!=manifest['gzip_sha256']: raise ValueError('WHOLE_TRANSPORT_REQUIRED')
dec=zlib.decompressobj(31);raw=dec.decompress(joined,1048577)
if not dec.eof or dec.unused_data or dec.unconsumed_tail or len(raw)>1048576 or sha(raw)!=manifest['payload_sha256']: raise ValueError('BOUNDED_COMPLETE_GZIP_REQUIRED')
payload=json.loads(raw);files=payload['files']
allowed={'profile.json','backend-upgrade.py','generation.py','resource-stream.py','source-artifact-receive.py','mysql-budget.py'}
if payload['kind']!='v4-public-code-transport' or set(files)!=allowed or set(manifest['files'])!=allowed: raise ValueError('LITERAL_SIX_FILE_SET_REQUIRED')
for name,text in files.items():
 data=text.encode();item=manifest['files'][name]
 if len(data)!=item['bytes'] or sha(data)!=item['sha256']: raise ValueError('EXACT_PUBLIC_CODE_REQUIRED')
 if name.endswith('.py'): compile(text,name,'exec')
profile=json.loads(files['profile.json'])
if profile['kind']!='explicit-new-source-time-pool-profile-v4' or profile['source_sha']!=SOURCE or profile['stop_utc']!=STOP or profile['source_file_count']!=manifest['source_file_count']: raise ValueError('EXACT_V4_PROFILE_REQUIRED')
if set(profile['derived_files'])!=allowed-{'profile.json'}: raise ValueError('EXACT_V4_DERIVED_SET_REQUIRED')
for name,item in profile['derived_files'].items():
 if item!=manifest['files'][name]: raise ValueError('PROFILE_CODE_CHAIN_REQUIRED')
target=root/'profile';target.mkdir(mode=0o700)
for name,text in sorted(files.items()): write(target/name,text.encode())
print(json.dumps({'success':True,'profile_dir':str(target),'source_sha':SOURCE,'stop_utc':STOP,'files':manifest['files'],'SUT_or_services_started':False}))
PY
