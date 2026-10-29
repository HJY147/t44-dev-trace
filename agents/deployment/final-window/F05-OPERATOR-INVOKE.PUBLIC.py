"""One original F05 neutral request, actual QA start, fixed corrected operator; no replay."""
import argparse,hashlib,json,subprocess
from pathlib import Path
R=Path('/root/t44-final-20261029');F=R/'F05';T=R/'ops01/deployment/cloud-reuse'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--request-file',type=Path,required=True);p.add_argument('--request-sha256',required=True);p.add_argument('--f-started-utc',required=True);p.add_argument('--source-profile',type=Path,required=True);a=p.parse_args()
 if sha(a.request_file)!=a.request_sha256 or sha(a.source_profile)!='346d19344281b9e02046a27cf9d24f07ebceb9c8f920105a981d7bfdc056ac1f':raise ValueError('ORIGINAL_F05_REQUEST_AND_CURRENT_PROFILE_SHA_REQUIRED')
 phase=read=json.loads((F/'preparation.PUBLIC.json').read_bytes());b=phase['phase'];budget=phase['budget'];clock=F/'timeplan.PUBLIC.json';plan=json.loads(clock.read_bytes());profile=F/'profile/profile.json'
 if b['phase_dir']!=str(F/'campaign/f') or plan['run_id']!='r30finalf05' or plan['absolute_cost_cutoff_utc']!='2026-10-29T19:30:00Z':raise ValueError('ACTUAL_CURRENT_F05_CONTEXT_REQUIRED')
 row=json.loads(a.request_file.read_bytes());rid=row['request_id']
 if row['run_id']!='r30finalf05' or a.request_file.name!=rid+'.request.json':raise ValueError('ORIGINAL_F05_REQUEST_NAME_REQUIRED')
 operator=T/'final-f-operator05.py'
 if sha(operator)!='ac9ff6d6106b939c6a26d3dfec13bdd6b2b690e37161a4913e5a1f3a862de52a':raise ValueError('EXACT_APPROVED_PRECISION01_OPERATOR_REQUIRED')
 argv=['python3','-B',str(operator),'--phase-dir',b['phase_dir'],'--binding-sha256',b['binding_sha256'],'--gen-profile',str(profile),'--gen-profile-sha256',sha(profile),'--source-profile',str(a.source_profile),'--source-profile-sha256',sha(a.source_profile),'--request-file',str(a.request_file),'--request-sha256',a.request_sha256,'--evidence-dir',str(F/('operator-'+rid)),'--budget-receipt',budget['budget_receipt'],'--budget-receipt-sha256',budget['budget_receipt_sha256'],'--timeplan',str(clock),'--timeplan-sha256',sha(clock),'--f-started-utc',a.f_started_utc,'--cost-cutoff-utc','2026-10-29T19:30:00Z']
 result=subprocess.run(argv,capture_output=True,check=False,timeout=185)
 if result.returncode:print(json.dumps({'status':'OPERATOR_PROCESS_NONZERO','returncode':result.returncode}));raise SystemExit(result.returncode)
 receipt=json.loads(result.stdout);response=Path(receipt['path'])
 if sha(response)!=receipt['sha256']:raise ValueError('ORIGINAL_PUBLIC_RESPONSE_SHA_REQUIRED')
 print(json.dumps({'receipt':receipt,'response':json.loads(response.read_bytes())},sort_keys=True))
if __name__=='__main__':main()
