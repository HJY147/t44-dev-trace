"""Local-only unpack of complete collector JSONL lines, preserving original public bytes and SHA."""
import argparse,base64,hashlib,json,zlib
from pathlib import Path
NAMES={'preparation.PUBLIC.json','timeplan.PUBLIC.json','backend-import-receipt.PUBLIC.json','LOAD-bootstrap.original.PUBLIC.json'}
def unpack(line,dest):
 v=json.loads(line)
 if v.get('kind')!='USER_P09_PUBLIC_COLLECTOR':raise ValueError('EXACT_P09_COLLECTOR_LINE_REQUIRED')
 decoded={}
 for name,item in v['files'].items():
  if name not in NAMES:raise ValueError('PUBLIC_FILENAME_NOT_WHITELISTED')
  if item.get('status')!='PRESENT':continue
  compressed=base64.b64decode(item['zlib_b64'],validate=True)
  if len(compressed)>8000000 or not 0<=item['bytes']<=8000000:raise ValueError('BOUNDED_PUBLIC_FILE_REQUIRED')
  d=zlib.decompressobj();raw=d.decompress(compressed,8000001)
  if not d.eof or d.unused_data or len(raw)!=item['bytes']or hashlib.sha256(raw).hexdigest()!=item['sha256']:raise ValueError('ORIGINAL_PUBLIC_BYTES_SHA_MISMATCH')
  json.loads(raw);decoded[name]=raw
 if 'timeplan.PUBLIC.json'in decoded and json.loads(decoded['timeplan.PUBLIC.json']).get('run_id')!='r30finalp09':raise ValueError('EXACT_NEW_P09_CLOCK_REQUIRED')
 dest=Path(dest);dest.mkdir(exist_ok=True)
 observation=None
 for name,raw in decoded.items():
  p=dest/name
  if name=='preparation.PUBLIC.json':
   # Preparation progresses between collector rows. Preserve every original;
   # the top-level file remains the first observation, never a rewritten one.
   directory=dest/'preparation-observations'
   if directory.is_symlink():raise ValueError('OBSERVATION_DIRECTORY_SYMLINK_REFUSED')
   directory.mkdir(exist_ok=True)
   version=directory/(hashlib.sha256(raw).hexdigest()+'.json')
   if version.exists():
    if version.is_symlink()or version.read_bytes()!=raw:raise ValueError('EXISTING_OBSERVATION_DIFFERS_NO_OVERWRITE')
   else:
    with version.open('xb')as f:f.write(raw)
   observation=str(version.relative_to(dest))
   if p.exists()and not p.is_symlink():
    first=p.read_bytes();archive=directory/(hashlib.sha256(first).hexdigest()+'.json')
    if not archive.is_file()or archive.is_symlink()or archive.read_bytes()!=first:raise ValueError('FIRST_OBSERVATION_ARCHIVE_MISSING_OR_CHANGED')
    continue
  if p.exists():
   if p.is_symlink()or p.read_bytes()!=raw:raise ValueError('EXISTING_ORIGINAL_DIFFERS_NO_OVERWRITE')
  else:
   with p.open('xb')as f:f.write(raw)
 return {'status':'LOCAL_ORIGINAL_PUBLIC_BYTES_UNPACKED_NOT_EXECUTED','event':v['event'],'files':{n:hashlib.sha256(b).hexdigest()for n,b in decoded.items()},'preparation_observation':observation,'top_level_preparation_policy':'FIRST_OBSERVATION_PRESERVED'}
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--jsonl',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True);a=p.parse_args()
 for line in a.jsonl.read_text().splitlines():
  if line.strip():print(json.dumps(unpack(line,a.output_dir),sort_keys=True))
if __name__=='__main__':main()
