"""Invoke existing fixed F04 operator for one pinned neutral request; print public response only."""
import argparse,hashlib,json,subprocess
from pathlib import Path
R=Path('/root/t44-final-20261029');F=R/'F04';T=R/'ops01/deployment/cloud-reuse'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--request-file',type=Path,required=True);p.add_argument('--request-sha256',required=True);a=p.parse_args()
 if sha(a.request_file)!=a.request_sha256:raise ValueError('ORIGINAL_REQUEST_SHA_REQUIRED')
 prep=json.loads((F/'preparation.PUBLIC.json').read_bytes());phase=prep['phase'];budget=prep['budget'];clock=F/'timeplan.PUBLIC.json';profile=F/'profile/profile.json';source=R/'source-profile.root-approved.PUBLIC.json'
 if (phase['phase_dir']!=str(F/'campaign/f') or prep['timeplan']['run_id']!='r30finalf04' or prep['timeplan']['absolute_cost_cutoff_utc']!='2026-10-29T19:30:00Z' or sha(source)!='ce3975d1fb5e6f219467fa61cdd0386a182851145993a2a4cf5300688a5cbe5c'):raise ValueError('EXACT_CURRENT_F04_CONTEXT_REQUIRED')
 row=json.loads(a.request_file.read_bytes());request_id=row['request_id']
 if row['run_id']!='r30finalf04' or a.request_file.name!=request_id+'.request.json':raise ValueError('EXACT_F04_REQUEST_NAME_REQUIRED')
 cmd=['python3',str(T/'final-f-operator.py'),'--phase-dir',phase['phase_dir'],'--binding-sha256',phase['binding_sha256'],'--gen-profile',str(profile),'--gen-profile-sha256',sha(profile),'--source-profile',str(source),'--source-profile-sha256',sha(source),'--request-file',str(a.request_file),'--request-sha256',a.request_sha256,'--evidence-dir',str(F/('operator-'+request_id)),'--budget-receipt',budget['budget_receipt'],'--budget-receipt-sha256',budget['budget_receipt_sha256'],'--timeplan',str(clock),'--timeplan-sha256',sha(clock),'--f-started-utc','2026-10-29T17:50:58.757650Z','--cost-cutoff-utc','2026-10-29T19:30:00Z']
 result=subprocess.run(cmd,capture_output=True,check=False,timeout=185)
 if result.returncode:print(json.dumps({'status':'OPERATOR_PROCESS_NONZERO','returncode':result.returncode}));raise SystemExit(result.returncode)
 receipt=json.loads(result.stdout);response=Path(receipt['path'])
 if sha(response)!=receipt['sha256']:raise ValueError('ORIGINAL_PUBLIC_RESPONSE_SHA_REQUIRED')
 print(json.dumps({'receipt':receipt,'response':json.loads(response.read_bytes())},sort_keys=True))
if __name__=='__main__':main()
