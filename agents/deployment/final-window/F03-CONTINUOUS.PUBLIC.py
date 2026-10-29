"""APP launcher only; installed pinned ops executes fixed F preparation, never QA or VM lifecycle."""
import argparse
import hashlib
import json
import os
import subprocess
import time
from pathlib import Path

ROOT=Path('/root/t44-final-20261029')
OPS=ROOT/'ops01'
TOOLS=OPS/'deployment/cloud-reuse'
CODE=OPS/'agents/backend/neutral-final-20261029'
PROFILE=ROOT/'source-profile.root-approved.PUBLIC.json'
PROFILE_SHA='ce3975d1fb5e6f219467fa61cdd0386a182851145993a2a4cf5300688a5cbe5c'
BUNDLE='1ddafb7aaa1c552172cc5a0c0f48881412a8fa1fabbb400037854f4bba77a6a2'
CODE_SHA='023063c342854c7b2bea107774007fcd89973a4d0ab85f5841db31a6a8cb2a5e'


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--package',type=Path)
    p.add_argument('--app-ip',required=True)
    p.add_argument('--run-id',default='r30finalf03')
    p.add_argument('--output',type=Path,default=ROOT/'F03')
    p.add_argument('--after-phase',action='store_true')
    p.add_argument('--cost-approval',type=Path,required=True)
    p.add_argument('--cost-approval-sha256',required=True)
    args=p.parse_args();os.umask(0o077)
    if sha(PROFILE)!=PROFILE_SHA or sha(CODE/'code-manifest.PUBLIC.json')!=CODE_SHA:
        raise ValueError('APPROVED_PROFILE_OR_EXACT18_CHANGED')
    package=args.package
    if package is None:
        candidates=[ROOT/'boot01/backend-bundle-manifest.json',*list((ROOT/'boot01').glob('*/backend-bundle-manifest.json'))]
        candidates=[x.parent for x in candidates if x.is_file() and sha(x)==BUNDLE and (x.parent/'images.tar.gz').is_file()]
        if len(candidates)!=1:raise ValueError('PASS_EXACT_SIX_FILE_PACKAGE_PATH')
        package=candidates[0]
    launcher=ROOT/(args.run_id+'-launcher')
    launcher.mkdir(mode=0o700)
    counter=0
    def run(label,cmd,timeout=600):
        nonlocal counter
        counter+=1
        stdout=launcher/(f'{counter:02d}-'+label+'.stdout.private')
        stderr=launcher/(f'{counter:02d}-'+label+'.stderr.private')
        with stdout.open('xb') as out,stderr.open('xb') as err:
            stdout.chmod(0o600);stderr.chmod(0o600)
            result=subprocess.run(list(map(str,cmd)),stdout=out,stderr=err,check=False,timeout=timeout,
                env={k:v for k,v in os.environ.items() if k in {'PATH','HOME','LANG'}})
        if result.returncode:raise ValueError('F_STEP_FAILED_PREFIX_PRESERVED:'+label)
        return json.loads(stdout.read_bytes())
    if args.after_phase:
        phase=json.loads((args.output/'preparation.PUBLIC.json').read_bytes())
        if phase['status']!='CHOSEN_PHASE_IDLE_NO_SESSIONS_OR_QA' or not phase['phase']['phase_dir'].endswith('/f'):
            raise ValueError('ACTUAL_COMPLETED_F_IDLE_REQUIRED')
    else:
        phase=run('phase',['python3',TOOLS/'final-app-prepare-absolute.py','phase','--package',package,'--bundle-sha256',BUNDLE,
            '--actual-first-boot-utc','2026-10-29T13:45:26Z','--cost-approval',args.cost_approval,'--cost-approval-sha256',args.cost_approval_sha256,'--source-profile',PROFILE,'--source-profile-sha256',PROFILE_SHA,
            '--phase','f','--run-id',args.run_id,'--app-ip',args.app_ip,'--output',args.output],900)
    selected=phase['phase'];directory=Path(selected['phase_dir']);binding=selected['binding_sha256'];budget=phase['budget']
    runtime=args.output/'runtime';gen=args.output/'profile';data=args.output/'F-inputs'
    run('write-F-inputs',['python3',TOOLS/'final-f-plan.py','--producer',CODE,'--source-profile',PROFILE,'--timeplan',args.output/'timeplan.PUBLIC.json',
        '--phase-dir',directory,'--import-receipt',phase['import']['receipt'],'--budget-receipt',budget['budget_receipt'],'--output',data])
    common=['--phase-dir',directory,'--binding-sha256',binding,'--profile-json',gen/'profile.json','--profile-sha256',sha(gen/'profile.json'),
        '--code-dir',CODE,'--code-manifest',CODE/'code-manifest.PUBLIC.json','--code-manifest-sha256',CODE_SHA,'--source-profile',PROFILE,
        '--plan',data/'plan.json','--intent',data/'intent.json','--import-receipt',phase['import']['receipt'],
        '--budget-receipt',budget['budget_receipt'],'--budget-receipt-sha256',budget['budget_receipt_sha256']]
    initialized=run('init-seven',['python3',runtime/'f-init-accounts.py','init-accounts',*common,'--accounts',data/'accounts.init.private.json','--output-dir',args.output/'F-init-accounts'],300)
    accounts=Path(initialized['output'])
    run('F-project',['python3',runtime/'f-http-prepare.py','--phase-dir',directory,'--binding-sha256',binding,
        '--code-dir',CODE,'--code-manifest-sha256',CODE_SHA,'--source-profile',PROFILE,'--plan',data/'plan.json',
        '--accounts',accounts,'--service',data/'empty-service-stage.json','--import-receipt',phase['import']['receipt'],
        '--ca',directory/'tls/ca.pem','--output-dir',args.output/'F-http'],240)
    project=args.output/'F-http/output/result/project-and-members.private.json'
    service=run('F-services',['python3',TOOLS/'final-f-services.py','--admin-file',runtime/'r30-neutral-admin.py','--admin-sha256',sha(runtime/'r30-neutral-admin.py'),
        *common,'--project-receipt',project,'--project-receipt-sha256',sha(project),'--output-dir',args.output/'F-services'],240)
    proof=Path(service['output']);normal=proof.parent/'service.original.private.json'
    token=directory/'scheduler-secrets/scheduler-token.json'
    with token.open('xb') as target:target.write(normal.read_bytes())
    token.chmod(0o600);os.chown(token,10001,10001)
    run('scheduler-start',['python3',gen/'generation.py','scheduler-start','--phase-dir',directory,'--binding-sha256',binding,
        '--budget-receipt',budget['budget_receipt'],'--budget-receipt-sha256',budget['budget_receipt_sha256']],180)
    humans=args.output/'F-http/output/result/human-sessions.private.json'
    environment=run('F-private-env',['python3',TOOLS/'final-f-environment.py','--plan',data/'plan.json','--accounts',accounts,
        '--human-sessions',humans,'--human-sessions-sha256',sha(humans),'--service-proof',proof,'--service-proof-sha256',sha(proof),
        '--output',args.output/'functional-environment.private.json'],90)
    result={'status':'F_FIXTURE_PREPARED_NOT_QA_STARTED','source_sha':'356f29983c904e949245aedfad464efc1bf7b63d',
        'environment':environment,'phase':selected,'budget':budget,'timeplan':str(args.output/'timeplan.PUBLIC.json'),
        'runtime':str(runtime),'ca_file':str(directory/'tls/ca.pem'),'launcher_private_logs':str(launcher),
        'F_operator_capabilities':['scheduler_restart','mq_stop','mq_start','api_restart','api_ready_wait']}
    (launcher/'F-ready.PUBLIC.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    (launcher/'F-ready.PUBLIC.json').chmod(0o600)
    print(json.dumps(result),flush=True)
    subprocess.run(['python3',str(TOOLS/'F03-TRANSPORT-APP.PUBLIC.py'),'--f-dir',str(args.output),'--load-ip','172.21.182.244'],check=True)


if __name__=='__main__':main()
