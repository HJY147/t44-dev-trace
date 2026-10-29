from pathlib import Path
import hashlib,json,zlib,base64
p=Path(__file__).resolve().parent
s=(p/'host.py').read_text()
a=s.index("    output = DEST/'output'\n")
b=s.index("    spec=importlib.util.spec_from_file_location",a)
prefix='''    output=DEST/'output'
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
'''
s=s[:a]+prefix+s[b:]
s=s.replace("'-I','-B','/neutral-code/admin.py',operation]", "'-B','/neutral-code/admin.py',operation]")
s=s.replace("admin('01-service','service')", "admin('01b-service','service')")
s=s.replace("'NEUTRAL_HOST_PREP_FAILED_PREFIX_PRESERVED'", "'NEUTRAL_IMPORT_REPAIR_CONTINUATION_FAILED_PREFIX_PRESERVED'")
(p/'resume-import-01.py').write_text(s)
raw=s.encode();blob=base64.b64encode(zlib.compress(raw,9)).decode()
script="""#!/bin/sh
set -eu
umask 077
python3 -I -B - <<'INSTALL_RESUME_NEUTRAL'
import base64,hashlib,os,zlib,subprocess
from pathlib import Path
raw=zlib.decompress(base64.b64decode(REPLACE_BLOB,validate=True))
assert hashlib.sha256(raw).hexdigest()==REPLACE_SHA
path=Path('/root/t44-r9/neutral-fixture-r29-01/code/resume-import-01.py')
assert path.parent.resolve()==path.parent
fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o444)
os.fchmod(fd,0o444)
with os.fdopen(fd,'wb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
subprocess.run(['systemd-run','--unit=t44-r29-neutral-import-repair-01','--property=Type=exec','--property=RuntimeMaxSec=600','--property=TimeoutStopSec=20','--property=KillMode=control-group','--property=UMask=0077','--property=StandardOutput=append:/root/t44-r9/neutral-import-repair-r29.stdout.private','--property=StandardError=append:/root/t44-r9/neutral-import-repair-r29.stderr.private','python3','-I','-B',str(path),'--cost-stop-utc','2026-10-29T04:56:19.801Z','--root-admit-http-preparation','--root-confirm-original-short-finished'],check=True,timeout=15)
print('SINGLE_IMPORT_REPAIR_CONTINUATION_DISPATCHED_NOT_READY')
INSTALL_RESUME_NEUTRAL
""".replace('REPLACE_BLOB',repr(blob)).replace('REPLACE_SHA',repr(hashlib.sha256(raw).hexdigest()))
assert len(script.encode())+300<16500
(p/'resume-import-launch.PUBLIC.sh').write_text(script)
print(json.dumps({'resume_python_bytes':len(raw),'resume_python_sha256':hashlib.sha256(raw).hexdigest(),'UI_bytes':len(script.encode()),'UI_sha256':hashlib.sha256(script.encode()).hexdigest(),'executes_original_host_main':False}))
