"""Zero-Docker source transition preflight; never issues sessions or writes outputs."""
import argparse
import json
from pathlib import Path
import refresh_core as core
import host_runner

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for name in ['old-packet','authorization','ca','source-manifest','bundle-manifest','import-receipt']:
  p.add_argument('--'+name,type=Path,required=True)
 args=p.parse_args();auth=json.loads(host_runner.read(args.authorization));old_raw=host_runner.read(args.old_packet)
 old=core.authorization(auth,old_raw)
 files={name:host_runner.read(getattr(args,key)) for name,key in [('ca.pem','ca'),('source-manifest.json','source_manifest'),('backend-bundle-manifest.json','bundle_manifest'),('backend-import-receipt.json','import_receipt')]}
 core.validate_new_source(auth,old,files)
 print(json.dumps({'status':'LOCAL_SOURCE_CHAIN_ONLY_CURRENT_HOST_SESSIONS_SCAN_QA_PENDING','new_source':core.SOURCE,'old_packet_sha256':core.sha(old_raw),'new_material':auth['new_packet_run_id'],'Docker_calls':0,'SUT_calls':0,'sessions_issued':False}))
if __name__=='__main__':
 try:main()
 except Exception:
  print(json.dumps({'status':'REFUSED_NO_CREDENTIALS_OR_PRIVATE_EXCEPTION_EXPORTED'}));raise SystemExit(2)
