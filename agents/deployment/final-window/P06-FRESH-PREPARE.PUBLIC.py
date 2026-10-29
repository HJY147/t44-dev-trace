"""Fresh P06 only: clone reviewed fast10 tools; preserve failed P05 and every frozen timeplan."""
import argparse,ast,hashlib,json,os
from pathlib import Path
T=Path('/root/t44-final-20261029/ops01/deployment/cloud-reuse');R=T.parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,s):
 ast.parse(s,feature_version=(3,10))
 with p.open('x') as f:f.write(s)
 p.chmod(0o600)
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--p05-launcher-sha256',required=True);a=p.parse_args();os.umask(0o077)
 if (R/'P06').exists() or (R/'r30finalp06-launcher').exists():raise ValueError('FRESH_P06_ONLY')
 old=T/'P05-CONTINUOUS-fast10.PUBLIC.py'
 if sha(old)!=a.p05_launcher_sha256 or sha(T/'final-image-bundle.py')!='7d6ea9d8990ef2200ac73e062ade9962035247513ad46a5554114f0596618b9e':raise ValueError('REVIEWED_PREIMAGES_REQUIRED')
 adapter=(T/'final-image-bundle.py').read_text();needle='    parent.deadline(args.stop_utc, datetime.now(timezone.utc))  # noqa: UP017 -- APP Python3.10'
 if adapter.count(needle)!=1:raise ValueError('EXACT_LEGACY_GATE_REQUIRED')
 patch='''    if args.run_id != "r30finalp06":raise ValueError("FRESH_P06_ONLY")
    stop=datetime.strptime(args.stop_utc,"%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    cost=datetime.strptime(args.cost_stop_utc,"%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    if (cost-stop).total_seconds()!=300 or not 600<=(stop-datetime.now(timezone.utc)).total_seconds()<=43200:raise ValueError("P06_ORIGINAL600_AND_C_G300_REQUIRED")'''
 adapter=adapter.replace(needle,patch)
 clock=(T/'final-timeplan-pfast05.py').read_text().replace('if args.phase != "p":','if args.phase != "p" or args.run_id != "r30finalp06":')
 prepare=(T/'final-app-prepare-pfast05.py').read_text().replace('final-timeplan-pfast05.py','final-timeplan-pfast06.py').replace('HERE / "final-image-bundle.py"','HERE / "final-image-bundle-pfast06.py"')
 launcher=old.read_text().replace('r30finalp05','r30finalp06').replace("R/'P05'","R/'P06'").replace('final-app-prepare-pfast05.py','final-app-prepare-pfast06.py')
 outputs={'final-image-bundle-pfast06.py':adapter,'final-timeplan-pfast06.py':clock,'final-app-prepare-pfast06.py':prepare,'P06-CONTINUOUS-fast10.PUBLIC.py':launcher}
 for n,s in outputs.items():put(T/n,s)
 print(json.dumps({'status':'FRESH_P06_PREPARED_NOT_STARTED','tools':{n:sha(T/n) for n in outputs},'P05_retained':True,'measurement_seconds':780,'S10_E23_G25_C30':True}))
if __name__=='__main__':main()
