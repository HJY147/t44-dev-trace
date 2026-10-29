"""LOAD: consume only public bootstrap, fetch/open original790; does not read QA cases or execute QA."""
import argparse
import base64
import datetime
import hashlib
import json
import os
import runpy
import subprocess
import sys
from pathlib import Path

BASE=Path('/root/t44-final-20261029')


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--bootstrap',type=Path,required=True);p.add_argument('--bootstrap-sha256',required=True)
    args=p.parse_args();os.umask(0o077)
    if sha(args.bootstrap)!=args.bootstrap_sha256:raise ValueError('ORIGINAL_PUBLIC_BOOTSTRAP_SHA_REQUIRED')
    data=json.loads(args.bootstrap.read_bytes());incoming=Path(data['incoming']);incoming.mkdir(mode=0o700)
    for key,name in [('timeplan','timeplan.PUBLIC.json'),('ca','ca.pem')]:
        raw=base64.b64decode(data[key+'_b64'],validate=True)
        if hashlib.sha256(raw).hexdigest()!=data[key+'_sha256']:raise ValueError('PUBLIC_ORIGINAL_BYTES_CHANGED')
        with (incoming/name).open('xb') as output:output.write(raw)
        (incoming/name).chmod(0o600)
    clock=json.loads((incoming/'timeplan.PUBLIC.json').read_bytes());tools=incoming/'tools'
    subprocess.run(['python3',str(BASE/'ops01/deployment/cloud-reuse/final-transport-profile.py'),'--timeplan',str(incoming/'timeplan.PUBLIC.json'),
        '--timeplan-sha256',data['timeplan_sha256'],'--output',str(tools)],check=True,capture_output=True,timeout=20)
    config=incoming/'relay.LOAD.original.private.json'
    with config.open('x') as output:json.dump(data['load_config'],output)
    config.chmod(0o600);sys.path.insert(0,str(tools))
    if not hasattr(datetime,'UTC'):datetime.UTC=datetime.timezone.utc
    sys.argv=[str(tools/'opaque_tls.py'),'fetch','--config',str(config)]
    runpy.run_path(str(tools/'opaque_tls.py'),run_name='__main__')
    sys.argv=[str(tools/'policy_790.py'),'--cost-stop-utc',clock['cost_stop_utc'],'open','--private-key',
        '/root/t44-r9/r29-load-key-01/load-only-private.pem','--transfer-file',str(incoming/'transfer.original.jsonl'),
        '--public-record-sha256',data['public_record_sha256'],'--output-dir',str(incoming/'opened')]
    runpy.run_path(str(tools/'policy_790.py'),run_name='__main__')
    sys.argv=[str(tools/'five_files.py'),'extract','--input-dir',str(incoming/'opened'),'--output-dir',str(incoming/'extracted'),
        '--cost-stop-utc',clock['cost_stop_utc'],'--gen-binding-sha256',data['gen_binding_sha256'],'--neutral-binding-sha256',data['neutral_binding_sha256']]
    runpy.run_path(str(tools/'five_files.py'),run_name='__main__')
    env=incoming/'extracted/inputs/session.private.json'
    if sha(env)!=data['f_environment_sha256']:raise ValueError('ORIGINAL_F_ENV_BYTES_CHANGED')
    print(json.dumps({'status':'P_FIVE_OPENED_ORIGINAL_NOT_QA_STARTED','environment':str(env),'environment_sha256':sha(env),
        'ca':str(incoming/'ca.pem'),'neutral_opened_dir':str(incoming/'extracted'),'requires':'root invoke original ENTRY_PERF_753 prepare then review new grant; QA execute remains root authorization'}))


if __name__=='__main__':main()
