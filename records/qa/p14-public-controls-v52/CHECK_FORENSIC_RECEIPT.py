#!/usr/bin/env python3
"""Public ciphertext transfer check only, without any decryption or acceptance claim."""
import argparse,hashlib,json
from pathlib import Path

def main():
 p=argparse.ArgumentParser();p.add_argument('cipher');p.add_argument('receipt');a=p.parse_args();f=Path(a.cipher);r=json.loads(Path(a.receipt).read_bytes())
 if not f.name.endswith('.forensic.753backup') or r.get('purpose')!='FORENSIC_ONLY' or r.get('run_id')!='r30manualp14' or r.get('backup_file')!=f.name or any(r.get(k) is not False for k in ['writer_complete_asserted','cohort_complete_asserted','acceptance_pass_asserted']):raise ValueError('FORENSIC_RECEIPT_REQUIRED')
 h=hashlib.sha256()
 with f.open('rb') as source:
  for b in iter(lambda:source.read(1024**2),b''):h.update(b)
 if f.stat().st_size!=r['cipher_bytes'] or h.hexdigest()!=r['cipher_sha256']:raise ValueError('CIPHER_SIZE_OR_SHA')
 print(json.dumps({'status':'FORENSIC_CIPHER_TRANSFER_MATCHES_RECEIPT_ONLY','authenticated_decrypt_verified':False,'measurement_complete_asserted':False,'acceptance_pass_asserted':False}))
if __name__=='__main__':main()
