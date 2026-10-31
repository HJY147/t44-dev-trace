"""New-source admission around byte-exact original scheduler atomic rotation."""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = 'bcec3326b40814fdb1922bbfea7c29473b47ba47'
IMAGE = 'sha256:479c406502b2e4834a0e8ab9ed3fd35e60df60601a041348b1e4a97825056f0e'

def validate_snapshot(v):
    if not (v.get('root_approved') is True and v.get('source_sha') == SOURCE
            and isinstance(v.get('observed_at'), str) and len(v.get('containers', [])) == 7):
        raise ValueError('CURRENT_APPROVED_SEVEN_REQUIRED')
    rows={r['role']:r for r in v['containers']}
    if set(rows)!={'api','consumer','scheduler','web','tls-gateway','mysql','rabbitmq'}:
        raise ValueError('EXACT_SEVEN_REQUIRED')
    if any(rows[r]['image_id']!=IMAGE for r in ['api','consumer','scheduler']):
        raise ValueError('OLD_APPLICATION_IMAGE_REFUSED')

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--material',type=Path,required=True);p.add_argument('--backup-dir',type=Path,required=True)
    a=p.parse_args();validate_snapshot(json.loads((HERE/'P09-existing-containers.PUBLIC.json').read_bytes()))
    manifest=json.loads((HERE/'MANIFEST.PUBLIC.json').read_bytes());tool=HERE/'rotate_scheduler_token.py'
    if hashlib.sha256(tool.read_bytes()).hexdigest()!=manifest['files'][tool.name]:
        raise ValueError('ORIGINAL_ROTATION_BYTES_REQUIRED')
    spec=importlib.util.spec_from_file_location('original_rotation',tool)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    result=m.rotate(a.material,a.backup_dir)
    result['rotation_completed_utc']=datetime.now(timezone.utc).isoformat()
    m.exclusive(a.backup_dir/'rotation-with-time.PUBLIC.json',(json.dumps(result,sort_keys=True)+'\n').encode(),0,0)
    print(json.dumps(result,sort_keys=True))

if __name__=='__main__':
    main()
