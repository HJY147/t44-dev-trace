"""APP: seal prepared F input with original790 and serve one bounded opaque transfer."""
import argparse
import base64
import contextlib
import datetime
import hashlib
import io
import json
import os
import runpy
import subprocess
import sys
from pathlib import Path

BASE=Path('/root/t44-final-20261029')
OPS=BASE/'ops01'


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def save(path,obj):
    with path.open('x') as out:json.dump(obj,out,sort_keys=True,indent=2);out.write('\n')
    path.chmod(0o600)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--f-dir',type=Path,default=BASE/'P03')
    p.add_argument('--load-ip',required=True)
    p.add_argument('--load-public-key',type=Path,default=BASE/'load-public.pem')
    args=p.parse_args();os.umask(0o077)
    f=args.f_dir;clock=json.loads((f/'timeplan.PUBLIC.json').read_bytes())
    phase=f/'campaign/p';binding_file=phase/'binding.json';binding=json.loads(binding_file.read_bytes())
    env=f/'P-packet/output/packet/inputs/session.private.json'
    if sha(args.load_public_key)!='1752c101a1182690a1d320b000d3259fea92eb90b45edf8005ff701319d17b12':raise ValueError('EXACT_EXISTING_LOAD_PUBLIC_KEY_REQUIRED')
    tools=f/'transport-tools'
    subprocess.run(['python3',str(OPS/'deployment/cloud-reuse/final-transport-profile.py'),'--timeplan',str(f/'timeplan.PUBLIC.json'),
        '--timeplan-sha256',sha(f/'timeplan.PUBLIC.json'),'--output',str(tools)],check=True,capture_output=True,timeout=20)
    if not hasattr(datetime,'UTC'):datetime.UTC=datetime.timezone.utc
    sys.path.insert(0,str(tools))
    sys.argv=[str(tools/'five_files.py'),'pack','--input-dir',str(env.parent),'--output-dir',str(f/'transport-five'),
        '--cost-stop-utc',clock['cost_stop_utc'],'--gen-binding-sha256',sha(binding_file)]
    with contextlib.redirect_stdout(io.StringIO()):runpy.run_path(str(tools/'five_files.py'),run_name='__main__')
    control=f/'transport-five/control.json';reference=f/'transport-five/session-reference.json';mirror=f/'transport-five/mirror.json'
    if not hasattr(datetime,'UTC'):datetime.UTC=datetime.timezone.utc
    sys.path.insert(0,str(tools))
    sys.argv=[str(tools/'policy_790.py'),'--cost-stop-utc',clock['cost_stop_utc'],'seal','--public-key-file',str(args.load_public_key),
        '--public-key-sha256',sha(args.load_public_key),'--binding-sha256',sha(binding_file),'--control',str(control),'--control-sha256',sha(control),
        '--session',str(reference),'--packet-sha256',sha(reference),'--mirror',str(mirror),'--mirror-sha256',sha(mirror),'--ca',str(phase/'tls/ca.pem'),'--ca-sha256',sha(phase/'tls/ca.pem'),'--output-dir',str(f/'transport-sealed-01')]
    capture=io.StringIO()
    with contextlib.redirect_stdout(capture):runpy.run_path(str(tools/'policy_790.py'),run_name='__main__')
    receipt=json.loads(capture.getvalue());save(f/'transport-seal.PUBLIC.json',receipt)
    source=f/'transport-sealed-01/transfer.public.jsonl'
    config={'schema':'r30-neutral-opaque-relay-v1','root_admit_transport':True,'source_sha':binding['source_sha'],'run_id':clock['run_id'],
        'app_ip':binding['app_private_ip'],'load_ip':args.load_ip,'port':18450,'cost_stop_utc':clock['cost_stop_utc'],
        'binding_file':str(binding_file),'binding_sha256':sha(binding_file),'source_file':str(source),'bytes':source.stat().st_size,'sha256':sha(source),
        'certificate_file':str(phase/'tls/server/server.pem'),'certificate_sha256':binding['tls']['server_certificate_sha256'],
        'private_key_file':str(phase/'tls/server/server.key'),'ca_file':None,'ca_sha256':sha(phase/'tls/ca.pem'),'output_file':None,
        'attempt_marker':str(f/'relay-APP-attempt.original.PUBLIC.json')}
    save(f/'relay.APP.original.private.json',config)
    incoming=BASE/(clock['run_id']+'-transfer')
    load=dict(config,certificate_file=None,private_key_file=None,binding_file=None,source_file=None,
        ca_file=str(incoming/'ca.pem'),output_file=str(incoming/'transfer.original.jsonl'),attempt_marker=str(incoming/'fetch-attempt.original.PUBLIC.json'))
    bootstrap={'timeplan_b64':base64.b64encode((f/'timeplan.PUBLIC.json').read_bytes()).decode(),'timeplan_sha256':sha(f/'timeplan.PUBLIC.json'),
        'ca_b64':base64.b64encode((phase/'tls/ca.pem').read_bytes()).decode(),'ca_sha256':sha(phase/'tls/ca.pem'),
        'incoming':str(incoming),'load_config':load,'public_record_sha256':receipt['public_record_sha256'],'f_environment_sha256':sha(env),'gen_binding_sha256':sha(binding_file),'neutral_binding_sha256':json.loads(env.read_bytes())['binding_sha256']}
    save(f/'LOAD-bootstrap.original.PUBLIC.json',bootstrap)
    print(json.dumps({'status':'SEALED_P_FIVE_INPUTS_NOT_QA_STARTED','bootstrap':str(f/'LOAD-bootstrap.original.PUBLIC.json'),'sha256':sha(f/'LOAD-bootstrap.original.PUBLIC.json')}),flush=True)
    sys.argv=[str(tools/'opaque_tls.py'),'serve','--config',str(f/'relay.APP.original.private.json')]
    runpy.run_path(str(tools/'opaque_tls.py'),run_name='__main__')


if __name__=='__main__':main()
