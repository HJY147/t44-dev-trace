"""APP-only neutral preparation. Root must separately admit after the original short run."""
import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import os
import platform
import subprocess
import time
from pathlib import Path
from types import SimpleNamespace

B = Path('/root/t44-r9')
T = B/'p790-r29-01'
P = B/'campaign-r29-01/p'
DEST = B/'neutral-fixture-r29-01'
SOURCE = 'f7cdb5fa3b19f84d8ab0d0b042bf51a5b8484e8f'
KEY_SHA = '1752c101a1182690a1d320b000d3259fea92eb90b45edf8005ff701319d17b12'
MANIFEST = 'a5510d962deee65ace91a3fa7cf93d0c720e1cb08e4b841220b75e9cc082e590'


def sha(path):
    if path.resolve() != path or path.is_symlink():
        raise ValueError('CANONICAL_EXACT_PATH_REQUIRED')
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    data = value if isinstance(value,bytes) else (json.dumps(value,sort_keys=True)+'\n').encode()
    fd = os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'wb') as f:
        f.write(data);f.flush();os.fsync(f.fileno())


def main(args):
    if os.geteuid()!=0 or platform.system()!='Linux' or not args.root_admit_http_preparation or not args.root_confirm_original_short_finished:
        raise ValueError('EXPLICIT_ROOT_ADMISSION_AFTER_SHORT_FINISHED_ONLY')
    stop = dt.datetime.fromisoformat(args.cost_stop_utc.replace('Z','+00:00'))
    left = (stop-dt.datetime.now(dt.timezone.utc)).total_seconds()
    if not 1200 < left <= 3600:
        raise ValueError('MINIMUM_PREPARATION_AND_FORMAL_WINDOW_REQUIRED')
    summary = json.loads((B/'r29-app-prep-01/complete.PUBLIC.json').read_bytes())
    binding = json.loads((P/'binding.json').read_bytes())
    if sha(P/'binding.json')!=summary['binding_sha256'] or binding['source_sha']!=SOURCE or sha(T/'manifest.json')!=MANIFEST:
        raise ValueError('ACTUAL_CURRENT_F7_BINDING_AND_TOOLS_REQUIRED')
    manifest = json.loads((T/'manifest.json').read_bytes())
    for name,wanted in manifest['files'].items():
        if sha(T/name)!=wanted['sha256']:
            raise ValueError('ORIGINAL_P64_TOOL_PIN_CHANGED')
    tools = Path(__file__).resolve().parent
    pins = json.loads((tools/'code-manifest.PUBLIC.json').read_bytes())
    for name,wanted in pins['files'].items():
        if sha(tools/name)!=wanted:
            raise ValueError('NEUTRAL_SOURCE_PIN_CHANGED')
    fixture = Path(summary['bootstrap_output_dir'])
    candidate = json.loads((fixture/'split790-r29-01/s1/candidate-01/candidate.private.json').read_bytes())
    excluded = sorted({s[key]['id'] for s in candidate['slots'] for key in ('transition','escalation')})
    if len(excluded)!=882:
        raise ValueError('ACTUAL_ORIGINAL441_PAIR_SCOPE_REQUIRED')
    # No import or read of independent test source, cases, keys, PRIVATE or runtime capsule.
    output=DEST/'output'
    inputs=DEST/'inputs'
    if not output.is_dir() or not inputs.is_dir():
        raise ValueError('EXISTING_PREPARATION_PREFIX_REQUIRED')
    failure=output/'01-service.stdout.private'
    if sha(failure)!='e860274a73bdba7e1e6978dfca7044da789f456f5faa8ead8eea00fdbae159a3':
        raise ValueError('EXACT_OBSERVED_FIRST_IMPORT_FAILURE_REQUIRED')
    observed=json.loads(failure.read_bytes())
    if observed!={'kind':'NEUTRAL_ADMIN_FAILED_NO_RETRY','failure_type':'ModuleNotFoundError','reason':"No module named 't44'"}:
        raise ValueError('NO_OTHER_FAILURE_RESUME_ALLOWED')
    for name in ('service.original.private.json','service.json','service-CLI.stdout.private','http','01b-service.argv.private.json','02-real-http-only.argv.private.json','sealed-neutral'):
        if (output/name).exists() or (output/name).is_symlink():
            raise ValueError('FIRST_SERVICE_WAS_NEVER_CALLED_AND_EDGE_UNSTARTED_REQUIRED')
    config=json.loads((inputs/'config.json').read_bytes())
    if config['source_sha']!=SOURCE or config['binding_sha256']!=summary['binding_sha256'] or config['database']!=binding['database'] or config['cost_stop_utc']!=args.cost_stop_utc or config['exclude_short_task_ids']!=excluded or config['project_ids']!=candidate['project_ids'] or config['origin']!=f"https://{binding['app_private_ip']}:{binding['tls_port']}" or config.get('admit_real_HTTP_fixture_preparation') is not True or config.get('original_short_diagnostic_finished') is not True:
        raise ValueError('ORIGINAL_INPUTS_MUST_STILL_MATCH_ACTUAL_BINDING')
    if sha(inputs/'accounts.private.json')!=sha(fixture/'accounts.private.json') or sha(inputs/'ca.pem')!=sha(P/'tls/ca.pem'):
        raise ValueError('ORIGINAL_PRIVATE_INPUT_BYTES_UNCHANGED_REQUIRED')
    save(output/'01b-root-import-repair-admission.PUBLIC.json',{'root_authorized_one_continuation':True,'root_confirmed_original_short_finished':True,'cost_stop_utc':args.cost_stop_utc,'original_01_failure_sha256':sha(failure),'config_sha256':sha(inputs/'config.json'),'change':'Remove -I only from data-only admin Python so original /app/backend PYTHONPATH is honored; source-free edge retains -I','original_files_overwritten':False,'automatic_retry':False})
    spec=importlib.util.spec_from_file_location('neutral_budget',T/'790_budget.py')
    budget=importlib.util.module_from_spec(spec);spec.loader.exec_module(budget)
    guard=SimpleNamespace(phase_dir=P,binding_sha256=summary['binding_sha256'],
        budget_receipt=Path(summary['budget_receipt']),budget_receipt_sha256=summary['budget_receipt_sha256'],
        scope_bridge_dir=B/'scope-bridge-v3-01')
    deadline=time.monotonic()+min(600,left-1000)

    def invoke(label,argv,cap):
        timeout=min(cap,deadline-time.monotonic())
        if timeout<=0:raise TimeoutError('ROOT_NEUTRAL_PREP_ABSOLUTE_LIMIT')
        save(output/(label+'.argv.private.json'),{'argv':list(map(str,argv)),'retry':False})
        with (output/(label+'.stdout.private')).open('xb') as out,(output/(label+'.stderr.private')).open('xb') as err:
            try:
                q=subprocess.run(list(map(str,argv)),stdout=out,stderr=err,timeout=timeout,check=False)
            except subprocess.TimeoutExpired:
                name=argv[argv.index('--name')+1] if '--name' in argv else None
                if name:
                    info=subprocess.run(['docker','--context','default','inspect','--format','{{json .}}',name],capture_output=True,text=True,timeout=5)
                    if info.returncode==0:
                        row=json.loads(info.stdout)
                        if row['Config']['Labels'].get('io.t44.neutral.owner')==binding['project'] and row['Image'] in {binding['image_ids']['backend'],binding['image_ids']['python']}:
                            subprocess.run(['docker','--context','default','stop','--time','10',name],capture_output=True,timeout=20,check=False)
                raise
        save(output/(label+'.exit.PUBLIC.json'),{'returncode':q.returncode,
            'stdout_sha256':sha(output/(label+'.stdout.private')),'stderr_sha256':sha(output/(label+'.stderr.private'))})
        if q.returncode:raise ValueError('STEP_FAILED_PREFIX_PRESERVED_'+label)

    def admin(label,operation):
        name=binding['project']+'-neutral-'+label
        command=['docker','--context','default','compose','--env-file',str(P/'application.env'),'--file',str(P/'compose.json'),
            '--project-name',binding['project'],'--profile','operations','run','--rm','--no-deps','-T','--name',name,
            '--label','io.t44.neutral.owner='+binding['project'],'--entrypoint','python',
            '--env','T44_SESSION_TTL_SECONDS=3600','--volume',str(tools)+':/neutral-code:ro',
            '--volume',str(inputs)+':/neutral-input:ro','--volume',str(output)+':/neutral-output','admin',
            '-B','/neutral-code/admin.py',operation]
        # Every direct SQL/CLI path: phase operation lock -> actual budget/identity -> SQL -> release.
        with budget.admitted(guard,binding,args.cost_stop_utc) as proof:
            save(output/(label+'.budget.PUBLIC.json'),proof)
            invoke(label,command,90)

    admin('01b-service','service')
    actual=subprocess.check_output(['docker','image','inspect','--format','{{.Id}}',binding['images']['python']['alias']],text=True,timeout=10).strip()
    if actual!=binding['image_ids']['python']:
        raise ValueError('ACTUAL_SOURCE_FREE_PYTHON_IMAGE_CHANGED')
    name=binding['project']+'-neutral-http'
    argv=['docker','--context','default','run','--rm','--name',name,'--restart=no','--network',binding['project']+'_edge',
        '--cpus','2','--memory','1g','--memory-swap','1g','--pids-limit','128','--user','10001:10001',
        '--cap-drop','ALL','--security-opt','no-new-privileges','--read-only','--tmpfs','/tmp:rw,nosuid,nodev,size=32m',
        '--label','io.t44.neutral.owner='+binding['project'],'--volume',str(tools)+':/neutral-code:ro',
        '--volume',str(inputs)+':/neutral-input:ro','--volume',str(output)+':/neutral-output','--entrypoint','python',
        actual,'-I','-B','/neutral-code/edge.py','/neutral-input/config.json','/neutral-output/http']
    invoke('02-real-http-only',argv,380)
    admin('03-readonly-final-counts','counts')
    counts=json.loads((output/'counts.PUBLIC.json').read_bytes())
    payload={'schema':'NEUTRAL_772_INPUTS_V1','source_sha':SOURCE,'binding_sha256':summary['binding_sha256'],
        'sessions':json.loads((output/'http/sessions.json').read_bytes()),
        'inventory':json.loads((output/'http/inventory.json').read_bytes()),
        'additional_neutral_snapshots':json.loads((output/'http/additional-neutral-snapshots.json').read_bytes()),
        'counts':counts,'fixture_sha256':hashlib.sha256((output/'counts.PUBLIC.json').read_bytes()).hexdigest()}
    save(output/'neutral-inputs.private.json',payload)
    public=B/'r29-ops-app-01/public.pem'
    if sha(public)!=KEY_SHA:raise ValueError('ACTUAL_FRESH_LOAD_KEY_REQUIRED')
    seal=['python3','-I','-B',T/'transport/790_transfer.py','seal','--public-key-file',public,'--public-key-sha256',KEY_SHA,
        '--binding-sha256',summary['binding_sha256'],'--control',inputs/'config.json','--control-sha256',sha(inputs/'config.json'),
        '--session',output/'neutral-inputs.private.json','--packet-sha256',sha(output/'neutral-inputs.private.json'),
        '--ca',inputs/'ca.pem','--ca-sha256',sha(inputs/'ca.pem'),'--output-dir',output/'sealed-neutral']
    invoke('04-seal-to-original-load',seal,60)
    result={'kind':'NEUTRAL_FIXTURE_INPUTS_SEALED_NOT_PERFORMANCE','source_sha':SOURCE,
        'binding_sha256':summary['binding_sha256'],'actual_counts':counts['actual_counts'],'fixture_sha256':payload['fixture_sha256'],
        'opaque_transfer_path':str(output/'sealed-neutral/transfer.public.jsonl'),
        'opaque_transfer_bytes':(output/'sealed-neutral/transfer.public.jsonl').stat().st_size,
        'opaque_transfer_sha256':sha(output/'sealed-neutral/transfer.public.jsonl'),
        'all_credentials_remain_private_on_original_APP_or_encrypted_to_LOAD':True,
        'independent_runtime_or_case_read':False,'formal_performance_started':False}
    save(output/'complete.PUBLIC.json',result)
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cost-stop-utc',required=True)
    parser.add_argument('--root-admit-http-preparation',action='store_true',required=True)
    parser.add_argument('--root-confirm-original-short-finished',action='store_true',required=True)
    args=parser.parse_args()
    os.umask(0o077)
    try:print(json.dumps(main(args),sort_keys=True))
    except Exception as error:
        print(json.dumps({'kind':'NEUTRAL_IMPORT_REPAIR_CONTINUATION_FAILED_PREFIX_PRESERVED','failure_type':type(error).__name__,'reason':str(error),'retry':False}))
        raise SystemExit(1) from None
