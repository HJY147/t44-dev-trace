"""Continue pre-grant APP S1 after preserving real status without host_https; no runtime edits."""
import argparse,base64,datetime as dt,hashlib,http.client,importlib.util,json,os,secrets,ssl,subprocess,time,zlib
from pathlib import Path
OP=Path('/root/t44-r9/ops-r29-01.py')
assert hashlib.sha256(OP.read_bytes()).hexdigest()=='ca9a2953a847c03f4e644c3204412b0234703469722c67392006c111cff3571f'
spec=importlib.util.spec_from_file_location('ops29',OP);o=importlib.util.module_from_spec(spec);spec.loader.exec_module(o)
B,T,P,R,A,L,K,MAN,PRO,REL,SOURCE = (getattr(o,name) for name in ('B','T','P','R','A','L','K','MAN','PRO','REL','SOURCE'))
need,checked,cost,obj,step,one,write,relay_module,start_unit,prepare,sha,now = (getattr(o,name) for name in ('need','checked','cost','obj','step','one','write','relay_module','start_unit','prepare','sha','now'))
def app_after_grant(c):
    checked();need(c.get('root_admit_pressure') is True,'EXPLICIT_ROOT_EXISTING_PRESSURE_ADMISSION')
    resource=obj(A/'resource-bridge.PUBLIC.json');mirror=c['load_resource'];cost(resource,1200)
    for name in ('source_sha','binding_sha256','key_sha256','cost_stop_utc','app_ip','load_ip','resource_binding_sha256','handoff_sha256'):
        need(mirror[name]==resource[name],'SAME_RESOURCE_CORRELATION')
    s,phase,b=prepare()
    command=obj(A/'06-stage1-once.command.private.json')
    old_exit=obj(A/'06-stage1-once.exit.PUBLIC.json')
    need(old_exit['returncode']==1 and sha(A/'06-stage1-once.stdout.private')==old_exit['stdout_sha256'] and sha(A/'06-stage1-once.stderr.private')==old_exit['stderr_sha256'],'PINNED_OLD_IMPORT_FAILURE')
    need(o.raw(A/'06-stage1-once.stdout.private')==b'' and b"ModuleNotFoundError: No module named '790_budget'" in o.raw(A/'06-stage1-once.stderr.private'),'EXACT_IMPORT_FAILURE_BEFORE_MAIN')
    need(not (phase/Path(s['bootstrap_output_dir']).name/'split790-r29-01').exists(),'S1_SPLIT_NEVER_STARTED')
    previous=obj(A/'05-backend-image.exit.PUBLIC.json');need(previous['returncode']==0 and sha(A/'05-backend-image.stdout.private')==previous['stdout_sha256'],'OLD05_ACTUAL_IMAGE_RESULT')
    grant_path=A/'root-pressure-grant.private.json';grant_sha=sha(grant_path);grant=obj(grant_path)
    argv=command['argv'];pairs=dict(zip(argv[5::2],argv[6::2]))
    need(pairs['--root-grant']==str(grant_path) and pairs['--root-grant-sha256']==grant_sha and pairs['--phase-dir']==str(phase) and pairs['--binding-sha256']==s['binding_sha256'] and pairs['--manifest-sha256']==MAN,'SAME_EXPLICIT_ROOT_GRANT_AND_BINDING')
    need(grant['kind']=='ROOT_P_PRESSURE_GRANT_V4' and grant['admitted'] is True and grant['formal_performance_authorized'] is False and grant['binding_sha256']==s['binding_sha256'] and grant['source_sha']==SOURCE,'EXISTING_ROOT_PRESSURE_ONLY')
    need(grant['backend_image_id']==o.raw(A/'05-backend-image.stdout.private').decode().strip(),'EXISTING05_IMAGE_MATCHES_GRANT')
    need(obj(A/'04c-strict-TLS401-observation.PUBLIC.json')['status']==401,'EXISTING04C_REAL401')
    write(A/'06b-root-caller-recovery-admission.PUBLIC.json',{'root_explicit_06b':True,'old_failure_preserved':True,'old_grant_sha256':grant_sha,'only_caller_change':'remove -I; retain -B, original host bytes, same args','original_S1_never_started':True,'utc':now().isoformat()})
    fixture = Path(obj(A/'resource-state.private.json')['fixture'])
    split = 'split790-r29-01'
    args = list(command['argv']);need(args[:5]==['python3','-I','-B',str(T/'790_host.py'),'stage1'],'EXACT_FAILED_CALLER');args.pop(1)
    stage = one(step(A,'06b-stage1-original-cli-no-isolated',args,360),lambda v:v.get('kind') == 'contrast790-s1-host-complete')
    control = fixture/split/'inputs/control.private.json'
    need(sha(control) == stage['control_sha256'],'ACTUAL_S1_CONTROL_SHA')
    transfer = obj(T/'manifest.json')['files']['transport/790_transfer.py']['sha256']
    app = {'kind':'P790_F7_APP_CONFIGURATION_V4','source_sha':SOURCE,'binding_sha256':s['binding_sha256'],'budget_receipt':s['budget_receipt'],'budget_receipt_sha256':s['budget_receipt_sha256'],'ca_sha256':sha(phase/'tls/ca.pem'),'fixture_name':fixture.name,'key_sha256':resource['key_sha256'],'manifest_sha256':MAN,'mirror_path':obj(A/'resource-state.private.json')['prepared']['private_handoff_path'],'mirror_sha256':resource['handoff_sha256'],'namespace':b['project'],'output_dir':str(B/'r29-pressure-export-01'),'phase_dir':str(phase),'public_key_file':str(A/'public.pem'),'python_image_id':b['image_ids']['python'],'root_grant':str(grant_path),'root_grant_sha256':grant_sha,'scope_bridge_dir':str(B/'scope-bridge-v3-01'),'split_name':split,'tools_dir':str(T),'transfer_sha256':transfer}
    app_path = A/'APP-configuration.PUBLIC.json';app_sha = write(app_path,app)
    nonce = secrets.token_hex(16);unit = 't44-r29-producer-01'
    relay = {'kind':'T44_OPAQUE_RELAY_APP_V1','source_sha':SOURCE,'binding_sha256':s['binding_sha256'],'root_grant_sha256':grant_sha,'key_sha256':resource['key_sha256'],'nonce':nonce,'app_ip':resource['app_ip'],'load_ip':resource['load_ip'],'port':18447,'expires_at':resource['cost_stop_utc'],'cost_stop_utc':resource['cost_stop_utc'],'output_dir':str(A/'relay-app-state'),'producer_unit':unit,'export_dir':app['output_dir'],'tls_certificate':str(phase/'tls/server/server.pem'),'tls_certificate_sha256':sha(phase/'tls/server/server.pem'),'tls_key':str(phase/'tls/server/server.key')}
    relay_path = A/'relay-APP.PUBLIC.json';relay_sha = write(relay_path,relay)
    relay_module().configure(str(relay_path),relay_sha,'APP')
    start_unit(A,'07-relay-app','t44-r29-relay-app-01',['python3','-I','-B',R,'app','--configuration',relay_path,'--configuration-sha256',relay_sha],int(cost(resource)))
    ready_path = Path(relay['output_dir'])/'APP-ready.PUBLIC.json'
    for _ in range(40):
        if ready_path.exists():break
        time.sleep(.1)
    ready = obj(ready_path)
    pid = subprocess.check_output(['systemctl','show','t44-r29-relay-app-01','--property=MainPID','--value'],text=True,timeout=3).strip()
    need(str(ready['pid']) == pid and ready['nonce'] == nonce and ready['binding_sha256'] == s['binding_sha256'],'ACTUAL_BOUND_APP_RELAY_PID')
    result = {'kind':'R29_S1_AND_APP_RELAY_READY_NO_S2','source_sha':SOURCE,'binding_sha256':s['binding_sha256'],'root_grant_sha256':grant_sha,'key_sha256':resource['key_sha256'],'control_sha256':stage['control_sha256'],'ca_sha256':app['ca_sha256'],'namespace':b['project'],'python_image':b['images']['python']['alias'],'python_image_id':b['image_ids']['python'],'manifest_sha256':MAN,'transfer_sha256':transfer,'nonce':nonce,'app_ip':resource['app_ip'],'load_ip':resource['load_ip'],'cost_stop_utc':resource['cost_stop_utc'],'mirror_binding_sha256':mirror['mirror_binding_sha256'],'APP_configuration_sha256':app_sha,'APP_relay_ready':ready,'producer_unit':unit,'S2_or_matrix_started':False}
    write(A/'stage1-bridge.PUBLIC.json',result)
    return result
if __name__ == '__main__':
 os.umask(0o077)
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--public-input-zlib-b64',required=True);p.add_argument('--root-admit-06b',required=True,action='store_true');a=p.parse_args()
 try:
  d=zlib.decompressobj();raw=d.decompress(base64.b64decode(a.public_input_zlib_b64,validate=True),25001);need(d.eof and not d.unused_data and len(raw)<=25000,'BOUNDED_PUBLIC_INPUT');o.emit(app_after_grant(json.loads(raw)))
 except Exception as error:
  o.emit({'kind':'R29_EXISTING_GRANT_S1_CONTINUATION_FAILED_NO_RETRY','error_type':type(error).__name__,'reason':str(error),'partial_state_preserved':True});raise SystemExit(1) from None
