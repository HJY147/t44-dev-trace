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
 for name,raw in decoded.items():
  p=dest/name
  if p.exists():
   if p.is_symlink()or p.read_bytes()!=raw:raise ValueError('EXISTING_ORIGINAL_DIFFERS_NO_OVERWRITE')
  else:
   with p.open('xb')as f:f.write(raw)
 return {'status':'LOCAL_ORIGINAL_PUBLIC_BYTES_UNPACKED_NOT_EXECUTED','event':v['event'],'files':{n:hashlib.sha256(b).hexdigest()for n,b in decoded.items()}}
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--jsonl',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True);a=p.parse_args()
 for line in a.jsonl.read_text().splitlines():
  if line.strip():print(json.dumps(unpack(line,a.output_dir),sort_keys=True))
if __name__=='__main__':main()
