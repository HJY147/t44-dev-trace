"""Continue pre-grant APP S1 after preserving real status without host_https; no runtime edits."""
import argparse,base64,datetime as dt,hashlib,http.client,importlib.util,json,os,secrets,ssl,subprocess,time,zlib
from pathlib import Path
OP=Path('/root/t44-r9/ops-r29-01.py')
assert hashlib.sha256(OP.read_bytes()).hexdigest()=='ca9a2953a847c03f4e644c3204412b0234703469722c67392006c111cff3571f'
spec=importlib.util.spec_from_file_location('ops29',OP);o=importlib.util.module_from_spec(spec);spec.loader.exec_module(o)
B,T,P,R,A,L,K,MAN,PRO,REL,SOURCE = (getattr(o,name) for name in ('B','T','P','R','A','L','K','MAN','PRO','REL','SOURCE'))
need,checked,cost,obj,step,one,write,relay_module,start_unit,prepare,sha,now = (getattr(o,name) for name in ('need','checked','cost','obj','step','one','write','relay_module','start_unit','prepare','sha','now'))
def strict_https(phase,b):
 ca=phase/'tls/ca.pem';need(sha(ca)==b['tls']['ca_sha256'],'EXACT_PHASE_CA')
 ctx=ssl.create_default_context(cafile=str(ca))
 need(ctx.check_hostname and ctx.verify_mode==ssl.CERT_REQUIRED,'STRICT_TLS_CA_IP')
 c=http.client.HTTPSConnection(b['app_private_ip'],b['tls_port'],timeout=5,context=ctx)
 row={'utc':now().isoformat(),'credentials_sent':False,'url_path':'/api/v1/projects','host':b['app_private_ip'],'port':b['tls_port'],'CA_sha256':sha(ca)}
 try:
  c.request('GET','/api/v1/projects',headers={'Accept':'application/json','Connection':'close'})
  r=c.getresponse();data=r.read(1048577)
  row.update(status=r.status,strict_CA_and_IP_verified=True,body_bytes=len(data),body_sha256=hashlib.sha256(data).hexdigest())
 except Exception as error:
  row.update(error_type=type(error).__name__,strict_CA_and_IP_verified=False);write(A/'04c-strict-TLS401-observation.PUBLIC.json',row);raise
 finally:
  c.close()
 write(A/'04c-strict-TLS401-observation.PUBLIC.json',row)
 need(row['status']==401 and row['body_bytes']<=1048576,'ACTUAL_STRICT_TLS401_REQUIRED')
def app_stage1(c):
    checked();need(c.get('root_admit_pressure') is True,'EXPLICIT_ROOT_PRESSURE_ADMIT_REQUIRED')
    resource = obj(A/'resource-bridge.PUBLIC.json');mirror = c['load_resource']
    cost(resource,1200)
    need(mirror['kind'] == 'R29_RESOURCE_MIRROR_PRESTARTED','LOAD_RESOURCE_ACTUAL_READY')
    for name in ('source_sha','binding_sha256','key_sha256','cost_stop_utc','app_ip','load_ip','resource_binding_sha256','handoff_sha256'):
        need(mirror[name] == resource[name],'TWO_NODE_RESOURCE_CORRELATION')
    s,phase,b = prepare();common = ['--phase-dir',phase,'--binding-sha256',s['binding_sha256']]
    state = one(step(A,'04b-fresh-actual-role-status',['python3','-I','-B',P/'generation.py','status']+common,40))
    strict_https(phase,b)
    roles = {}
    for row in state['resources']:
        if row['role'] == 'scheduler':
            need(row.get('absent') is True,'SCHEDULER_ABSENT');roles['scheduler']={'absent':True}
        else:
            need(row['state']['Running'] is True and row['restart_count'] == 0,'ACTUAL_RUNNING_ZERO_RESTART_ROLES')
            roles[row['role']]={'container_id':row['container_id'],'image_id':row['image_id'],'running':True,'restart_count':0}
    need(set(roles) == {'mysql','rabbitmq','api','consumer','scheduler','web','tls-gateway'},'EXACT_ROLE_SET')
    image = step(A,'05-backend-image',['docker','--context','default','image','inspect','--format','{{.Id}}',b['images']['backend']['alias']]).decode().strip()
    need(image in {b['image_ids']['backend'],b['config_ids']['backend']},'ACTUAL_BACKEND_IMAGE')
    grant = {'kind':'ROOT_P_PRESSURE_GRANT_V4','admitted':True,'HTTP_authorized':True,'formal_performance_authorized':False,'no_automatic_retry':True,'issued_at':now().isoformat(),'expires_at':b['stop_utc'],'source_sha':SOURCE,'run_id':obj(Path(s['bootstrap_output_dir'])/'control.private.json')['run_id'],'binding_sha256':s['binding_sha256'],'namespace':b['project'],'database':b['database'],'api_workers':b['api_workers'],'backend_image_id':image,'source_proof_sha256':b['source_actual_proof_sha256'],'source_file_count':53,'seed':44,'anchor_at':'2026-10-28T04:00:00Z','stop_utc':b['stop_utc'],'roles':roles,'session_nonce':secrets.token_hex(32),'session_ttl_seconds':600,'cohorts':[['baseline1',1,20,0],['warmup40',40,5,1],['measure400',400,5,41]],'root_admission_boundary':'One original short diagnostic only. No automatic retry/successor/formal acceptance.'}
    grant_path = A/'root-pressure-grant.private.json';grant_sha = write(grant_path,grant)
    fixture = Path(obj(A/'resource-state.private.json')['fixture'])
    split = 'split790-r29-01'
    args = ['python3','-I','-B',T/'790_host.py','stage1']+common+['--fixture-name',fixture.name,'--split-name',split,'--manifest-sha256',MAN,'--budget-receipt',s['budget_receipt'],'--budget-receipt-sha256',s['budget_receipt_sha256'],'--root-grant',grant_path,'--root-grant-sha256',grant_sha,'--scope-bridge-dir',B/'scope-bridge-v3-01']
    stage = one(step(A,'06-stage1-once',args,360),lambda v:v.get('kind') == 'contrast790-s1-host-complete')
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
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--public-input-zlib-b64',required=True);a=p.parse_args()
 try:
  d=zlib.decompressobj();raw=d.decompress(base64.b64decode(a.public_input_zlib_b64,validate=True),25001);need(d.eof and not d.unused_data and len(raw)<=25000,'BOUNDED_PUBLIC_INPUT');o.emit(app_stage1(json.loads(raw)))
 except Exception as error:
  o.emit({'kind':'R29_APP_S1_CONTINUATION_FAILED_NO_RETRY','error_type':type(error).__name__,'reason':str(error),'partial_state_preserved':True});raise SystemExit(1) from None
