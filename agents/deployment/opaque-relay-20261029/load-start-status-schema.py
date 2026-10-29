"""Narrow LOAD start wrapper: recognize original resource status schema without invented success."""
import argparse,base64,hashlib,importlib.util,json,os,socket,subprocess,time,zlib
from pathlib import Path
OP=Path('/root/t44-r9/ops-r29-01.py')
assert hashlib.sha256(OP.read_bytes()).hexdigest()=='ca9a2953a847c03f4e644c3204412b0234703469722c67392006c111cff3571f'
spec=importlib.util.spec_from_file_location('ops29',OP);o=importlib.util.module_from_spec(spec);spec.loader.exec_module(o)
B,T,P,R,A,L,K,MAN,PRO,REL,SOURCE = (getattr(o,name) for name in ('B','T','P','R','A','L','K','MAN','PRO','REL','SOURCE'))
need,checked,cost,obj,step,one,write,relay_module,start_unit = (getattr(o,name) for name in ('need','checked','cost','obj','step','one','write','relay_module','start_unit'))
def load_start(c):
    manifest = checked();cost(c,960)
    need(c['kind'] == 'R29_S1_AND_APP_RELAY_READY_NO_S2' and c['source_sha'] == SOURCE,'EXACT_S1_PUBLIC_BRIDGE')
    own = obj(L/'resource-ready.PUBLIC.json')
    for name in ('binding_sha256','key_sha256','cost_stop_utc','app_ip','load_ip','mirror_binding_sha256'):
        need(c[name] == own[name],'OWN_LOAD_RESOURCE_CORRELATION')
    mirror = Path(own['mirror_dir'])
    status = one(step(L,'04b-mirror-status-observe',['python3','-I','-B',mirror/'controller.py','status','--directory',mirror,'--binding-sha256',own['mirror_binding_sha256']]),lambda row: row.get('action') == 'status' and row.get('unit') == obj(mirror/'binding.json')['unit'])
    need(status['observed_before_pid'] and status['observed_before_pid'] == status['observed_after_pid'] and status.get('progress',{}).get('raw_bytes_observed'),'LIVE_RESOURCE_BYTES_BEFORE_SESSION')
    image = step(L,'05-python-image',['docker','--context','default','image','inspect','--format','{{.Id}}',c['python_image']]).decode().strip()
    need(image == c['python_image_id'],'ACTUAL_LOAD_PYTHON_IMAGE')
    load = {'kind':'P790_F7_LOAD_CONFIGURATION_V4','source_sha':SOURCE,'binding_sha256':c['binding_sha256'],'ca_sha256':c['ca_sha256'],'control_sha256':c['control_sha256'],'expected_host':socket.gethostname().split('.')[0],'key_sha256':c['key_sha256'],'manifest_sha256':MAN,'mirror_binding_sha256':own['mirror_binding_sha256'],'mirror_dir':own['mirror_dir'],'namespace':c['namespace'],'private_key':str(K/'load-only-private.pem'),'python_image':c['python_image'],'python_image_id':c['python_image_id'],'root_grant_sha256':c['root_grant_sha256'],'tools_dir':str(T),'transfer_sha256':c['transfer_sha256'],'work_dir':str(L/'pressure-input')}
    load_path = L/'LOAD-configuration.PUBLIC.json';load_sha = write(load_path,load)
    relay = {name:c[name] for name in ('source_sha','binding_sha256','root_grant_sha256','key_sha256','nonce','app_ip','load_ip','cost_stop_utc')}
    relay.update({'kind':'T44_OPAQUE_RELAY_LOAD_V1','port':18447,'expires_at':c['cost_stop_utc'],'output_dir':str(L/'relay-load-state'),'ca_file':str(L/'opened-resource-only/inputs/ca.pem'),'ca_sha256':c['ca_sha256'],'load_configuration':str(load_path),'load_configuration_sha256':load_sha,'receiver_sha256':manifest['files']['790_receive.py']['sha256'],'consumer_sha256':manifest['files']['790_consumer.py']['sha256'],'max_wait_seconds':420})
    relay_path = L/'relay-LOAD.PUBLIC.json';relay_sha = write(relay_path,relay)
    relay_module().configure(str(relay_path),relay_sha,'LOAD')
    start_unit(L,'06-relay-load','t44-r29-relay-load-01',['python3','-I','-B',OP,'load-wait','--configuration',relay_path,'--configuration-sha256',relay_sha],min(1000,int(cost(c))))
    for _ in range(60):
        if (L/'LOAD-ready.PUBLIC.json').exists():break
        time.sleep(.1)
    ready = obj(L/'LOAD-ready.PUBLIC.json')
    pid = subprocess.check_output(['systemctl','show','t44-r29-relay-load-01','--property=MainPID','--value'],text=True,timeout=3).strip()
    need(str(ready['pid']) == pid and ready['nonce'] == c['nonce'],'ACTUAL_LOAD_POLL_PID')
    return ready
if __name__ == '__main__':
 os.umask(0o077)
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--public-input-zlib-b64',required=True);a=p.parse_args()
 try:
  d=zlib.decompressobj();raw=d.decompress(base64.b64decode(a.public_input_zlib_b64,validate=True),25001);need(d.eof and not d.unused_data and len(raw)<=25000,'BOUNDED_PUBLIC_INPUT');o.emit(load_start(json.loads(raw)))
 except Exception as error:
  o.emit({'kind':'R29_LOAD_START_FAILED_NO_RETRY','error_type':type(error).__name__,'reason':str(error),'partial_state_preserved':True});raise SystemExit(1) from None
