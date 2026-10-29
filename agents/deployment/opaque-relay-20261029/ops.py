"""Single-use coordinator operations; preserve original P790 runtimes and admission."""
import argparse
import base64
import datetime as dt
import hashlib
import importlib.util
import ipaddress
import json
import os
import platform
import secrets
import signal
import socket
import subprocess
import sys
import time
import zlib
from pathlib import Path

B = Path('/root/t44-r9')
T = B / 'p790-r29-01'
P = B / 'r29-code-01/profile'
R = B / 'opaque-relay-r29-01/relay.py'
A = B / 'r29-ops-app-01'
L = B / 'r29-ops-load-01'
K = B / 'r29-load-key-01'
MAN = 'a5510d962deee65ace91a3fa7cf93d0c720e1cb08e4b841220b75e9cc082e590'
PRO = '5b0eef799680cbc30c5096d37b4fbffb32087add52410045e33842c972d4237a'
REL = '0faba87792014ec0b16e18ef08286da234d8744f2d1792f409dccd01e939ea59'
SOURCE = 'f7cdb5fa3b19f84d8ab0d0b042bf51a5b8484e8f'
MARKER = {'kind':'RESOURCE_ONLY_NONCREDENTIAL_NEVER_TESTER_INPUT'}


def need(ok, code):
    if not ok:
        raise ValueError(code)


def raw(path, cap=300000):
    path = Path(path)
    need(path.is_absolute() and path.resolve() == path, 'CANONICAL_FILE')
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(fd, 'rb') as f:
        info = os.fstat(f.fileno())
        need(info.st_nlink == 1 and info.st_size <= cap, 'BOUNDED_SINGLE_FILE')
        value = f.read(cap+1)
    need(len(value) <= cap, 'FILE_CAP')
    return value


def sha(path):
    return hashlib.sha256(raw(path)).hexdigest()


def obj(path):
    return json.loads(raw(path))


def write(path, value):
    data = value if isinstance(value, bytes) else (json.dumps(value,sort_keys=True)+'\n').encode()
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as f:
        f.write(data);f.flush();os.fsync(f.fileno())
    return hashlib.sha256(data).hexdigest()


def emit(value):
    print(json.dumps(value,sort_keys=True),flush=True)


def now():
    return dt.datetime.now(dt.timezone.utc)


def utc(value):
    stamp = dt.datetime.fromisoformat(value.replace('Z','+00:00'))
    need(stamp.utcoffset().total_seconds() == 0, 'UTC_REQUIRED')
    return stamp


def cost(c, minimum=0):
    left = (utc(c['cost_stop_utc'])-now()).total_seconds()
    need(minimum < left <= 3600, 'INDEPENDENT_ONE_HOUR_COST_WINDOW')
    return left


def check_tree(directory, name, expected, key):
    need(sha(directory/name) == expected, 'CURRENT_MANIFEST_PIN')
    m = obj(directory/name)
    for name,row in m[key].items():
        need(not Path(name).is_absolute() and '..' not in Path(name).parts, 'MANIFEST_RELATIVE')
        value = raw(directory/name)
        need(hashlib.sha256(value).hexdigest() == row['sha256'], 'CURRENT_TOOL_SHA')
        if 'bytes' in row:
            need(len(value) == row['bytes'], 'CURRENT_TOOL_BYTES')
    return m


def checked():
    need(os.geteuid() == 0 and platform.system() == 'Linux', 'ROOT_LINUX_REQUIRED')
    need(B.resolve() == B and B.is_dir(), 'EXISTING_OWNED_BASE')
    m = check_tree(T,'manifest.json',MAN,'files')
    check_tree(P,'profile.json',PRO,'derived_files')
    need(sha(R) == REL, 'FIXED_RELAY_REQUIRED')
    return m


def step(directory,label,argv,cap=30):
    write(directory/(label+'.command.private.json'),{'utc':now().isoformat(),'argv':list(map(str,argv)),'retry':False})
    stdout = directory/(label+'.stdout.private')
    stderr = directory/(label+'.stderr.private')
    code = None
    with stdout.open('xb') as out, stderr.open('xb') as err:
        child = subprocess.Popen(list(map(str,argv)),stdout=out,stderr=err,start_new_session=True)
        try:
            code = child.wait(timeout=cap)
        except BaseException:
            if child.poll() is None:
                os.killpg(child.pid,signal.SIGKILL);child.wait()
            write(directory/(label+'.exit.PUBLIC.json'),{'returncode':None,'incomplete':True,'partial_state_preserved':True})
            raise
    write(directory/(label+'.exit.PUBLIC.json'),{'returncode':code,'stdout_sha256':sha(stdout),'stderr_sha256':sha(stderr),'partial_state_preserved':True})
    need(code == 0, 'STEP_FAILED_PRESERVE_NO_RETRY_'+label)
    return raw(stdout)


def one(value, predicate=lambda v:v.get('success') is True):
    rows = [json.loads(x) for x in value.splitlines() if x.strip()]
    rows = [x for x in rows if isinstance(x,dict) and predicate(x)]
    need(len(rows) == 1, 'ONE_ACTUAL_RESULT')
    return rows[0]


def prepare():
    summary = obj(B/'r29-app-prep-01/complete.PUBLIC.json')
    need(summary['kind'] == 'R29_APP_PREP_COMPLETE_NOT_PRESSURE' and summary['source_sha'] == SOURCE, 'APP_PREP_ACTUAL_COMPLETE')
    phase = Path(summary['phase_dir'])
    need(phase == B/'campaign-r29-01/p' and sha(phase/'binding.json') == summary['binding_sha256'], 'ACTUAL_NEW_PHASE')
    return summary,phase,obj(phase/'binding.json')


def local_ip(value):
    address = ipaddress.IPv4Address(value)
    need(address.is_private and not address.is_loopback and not address.is_link_local,'PRIVATE_IP')
    return str(address)


def load_key(c):
    checked()
    need(not K.exists(), 'NEW_LOAD_KEY_ONLY')
    # Original keygen creates its own exclusive directory; private key never emitted.
    result = subprocess.run(['python3','-I','-B',str(T/'transport/790_transfer.py'),'keygen','--output-dir',str(K)],capture_output=True,timeout=30)
    need(result.returncode == 0,'ORIGINAL_KEYGEN_FAILED_NO_RETRY')
    value = json.loads(result.stdout)
    need(value['kind'] == 'PUBLIC-790-KEY' and sha(K/'public.pem') == value['public_key_sha256'], 'ACTUAL_PUBLIC_KEY')
    return value


def app_resource(c):
    checked();cost(c,1200)
    s,phase,b = prepare()
    need(local_ip(c['app_ip']) == b['app_private_ip'] and local_ip(c['load_ip']) != c['app_ip'],'ACTUAL_TWO_NODE_IP')
    key = c['load_key'];need(key['kind'] == 'PUBLIC-790-KEY','ORIGINAL_LOAD_PUBLIC_KEY')
    public = base64.b64decode(key['public_key_b64'],validate=True)
    need(hashlib.sha256(public).hexdigest() == key['public_key_sha256'] and public.startswith(b'-----BEGIN PUBLIC KEY-----'),'PUBLIC_KEY_BYTES')
    A.mkdir(mode=0o700);write(A/'public.pem',public)
    stop = utc(c['cost_stop_utc']);sample = stop-dt.timedelta(seconds=120)
    resource = B/'r29-resource-app-01'
    prep = one(step(A,'01-resource-prepare',['python3','-I','-B',P/'resource-stream.py','prepare-app','--phase-dir',phase,'--phase-binding-sha256',s['binding_sha256'],'--app-ip',c['app_ip'],'--load-ip',c['load_ip'],'--port','18449','--run-id','r29p64res01','--output',resource,'--sample-until',sample.isoformat(),'--serve-until',stop.isoformat(),'--interval','1','--byte-cap','268435456']))
    started = one(step(A,'02-resource-start',['python3','-I','-B',resource/'controller.py','start','--directory',resource,'--binding-sha256',prep['binding_sha256']]))
    write(A/'marker.json',MARKER)
    fixture = Path(s['bootstrap_output_dir'])
    control = fixture/'control.private.json'
    step(A,'03-resource-only-seal',['python3','-I','-B',T/'transport/790_transfer.py','seal','--public-key-file',A/'public.pem','--public-key-sha256',key['public_key_sha256'],'--binding-sha256',s['binding_sha256'],'--control',control,'--control-sha256',sha(control),'--session',A/'marker.json','--packet-sha256',sha(A/'marker.json'),'--ca',phase/'tls/ca.pem','--ca-sha256',sha(phase/'tls/ca.pem'),'--mirror',prep['private_handoff_path'],'--mirror-sha256',prep['handoff_sha256'],'--output-dir',A/'resource-sealed'],60)
    envelope = raw(A/'resource-sealed/transfer.public.jsonl',14000)
    blob = base64.b64encode(zlib.compress(envelope,9)).decode()
    need(len(blob) <= 14500,'RESOURCE_ONLY_UI_CIPHERTEXT_CAP')
    state = {'kind':'R29_RESOURCE_ONLY_OPAQUE_HANDOFF','source_sha':SOURCE,'binding_sha256':s['binding_sha256'],'cost_stop_utc':c['cost_stop_utc'],'app_ip':c['app_ip'],'load_ip':c['load_ip'],'key_sha256':key['public_key_sha256'],'handoff_sha256':prep['handoff_sha256'],'opaque_bytes':len(envelope),'opaque_sha256':hashlib.sha256(envelope).hexdigest(),'opaque_zlib_b64':blob,'resource_binding_sha256':prep['binding_sha256'],'resource_only_never_matrix_input':True}
    write(A/'resource-bridge.PUBLIC.json',state);write(A/'resource-state.private.json',{'prepared':prep,'started':started,'fixture':str(fixture)})
    return state


def load_resource(c):
    checked();cost(c,1000)
    need(c['kind'] == 'R29_RESOURCE_ONLY_OPAQUE_HANDOFF' and c['source_sha'] == SOURCE and c['resource_only_never_matrix_input'] is True,'EXACT_RESOURCE_MARKER_HANDOFF')
    need(sha(K/'public.pem') == c['key_sha256'],'NEW_OWN_LOAD_KEY')
    packed = base64.b64decode(c['opaque_zlib_b64'],validate=True)
    dec = zlib.decompressobj();envelope = dec.decompress(packed,14001)
    need(dec.eof and not dec.unused_data and len(envelope) == c['opaque_bytes'] <= 14000 and hashlib.sha256(envelope).hexdigest() == c['opaque_sha256'],'BOUNDED_OPAQUE_ENVELOPE')
    L.mkdir(mode=0o700);write(L/'resource.OPAQUE.jsonl',envelope)
    metadata = json.loads(envelope.splitlines()[0])
    need(metadata['binding_sha256'] == c['binding_sha256'] and metadata['key_sha256'] == c['key_sha256'],'RESOURCE_ENVELOPE_SCOPE')
    opened = L/'opened-resource-only'
    step(L,'01-resource-only-open',['python3','-I','-B',T/'transport/790_transfer.py','open','--private-key',K/'load-only-private.pem','--transfer-file',L/'resource.OPAQUE.jsonl','--public-record-sha256',metadata['public_record_sha256'],'--output-dir',opened],60)
    need(obj(opened/'inputs/session.private.json') == MARKER,'NONCREDENTIAL_MARKER_NEVER_MATRIX')
    handoff = opened/'mirror/private-mirror-handoff.json'
    need(sha(handoff) == c['handoff_sha256'],'ORIGINAL_MIRROR_SUBDIRECTORY_SHA')
    h = obj(handoff)
    need(h['app_ip'] == local_ip(c['app_ip']) and h['load_ip'] == local_ip(c['load_ip']) and h['ca_sha256'] == sha(opened/'inputs/ca.pem'),'ACTUAL_RESOURCE_IP_AND_CA')
    mirror = B/'r29-resource-mirror-01'
    prep = one(step(L,'02-mirror-prepare',['python3','-I','-B',P/'resource-stream.py','prepare-mirror','--handoff',handoff,'--handoff-sha256',c['handoff_sha256'],'--run-id','r29p64mirror01','--output',mirror]))
    one(step(L,'03-mirror-start',['python3','-I','-B',mirror/'controller.py','start','--directory',mirror,'--binding-sha256',prep['binding_sha256']]))
    result = {'kind':'R29_RESOURCE_MIRROR_PRESTARTED','source_sha':SOURCE,'binding_sha256':c['binding_sha256'],'key_sha256':c['key_sha256'],'cost_stop_utc':c['cost_stop_utc'],'app_ip':c['app_ip'],'load_ip':c['load_ip'],'mirror_dir':str(mirror),'mirror_binding_sha256':prep['binding_sha256'],'resource_binding_sha256':c['resource_binding_sha256'],'handoff_sha256':c['handoff_sha256'],'CA_sha256':h['ca_sha256'],'session_or_matrix_started':False}
    write(L/'resource-ready.PUBLIC.json',result)
    return result


def start_unit(directory,label,unit,argv,limit,retain=False):
    out = directory/(label+'.unit.stdout.private');err = directory/(label+'.unit.stderr.private')
    write(out,b'');write(err,b'')
    command = ['systemd-run','--unit='+unit,'--property=Type=exec','--property=Restart=no','--property=RuntimeMaxSec='+str(limit),'--property=TimeoutStopSec=15','--property=KillMode=control-group','--property=UMask=0077','--property=StandardOutput=append:'+str(out),'--property=StandardError=append:'+str(err)]
    if retain:
        command += ['--property=RemainAfterExit=yes']
    step(directory,label+'-dispatch',command+list(map(str,argv)),20)


def relay_module():
    need(sha(R) == REL,'FIXED_RELAY')
    spec = importlib.util.spec_from_file_location('opaque_relay29',R)
    module = importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def app_stage1(c):
    checked();need(c.get('root_admit_pressure') is True,'EXPLICIT_ROOT_PRESSURE_ADMIT_REQUIRED')
    resource = obj(A/'resource-bridge.PUBLIC.json');mirror = c['load_resource']
    cost(resource,1200)
    need(mirror['kind'] == 'R29_RESOURCE_MIRROR_PRESTARTED','LOAD_RESOURCE_ACTUAL_READY')
    for name in ('source_sha','binding_sha256','key_sha256','cost_stop_utc','app_ip','load_ip','resource_binding_sha256','handoff_sha256'):
        need(mirror[name] == resource[name],'TWO_NODE_RESOURCE_CORRELATION')
    s,phase,b = prepare();common = ['--phase-dir',phase,'--binding-sha256',s['binding_sha256']]
    state = one(step(A,'04-actual-idle-status',['python3','-I','-B',P/'generation.py','status']+common,40))
    need(state['host_https']['status'] == 401 and state['host_https']['strict_CA_and_IP_verified'] is True,'FRESH_STRICT_TLS401')
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


def load_start(c):
    manifest = checked();cost(c,960)
    need(c['kind'] == 'R29_S1_AND_APP_RELAY_READY_NO_S2' and c['source_sha'] == SOURCE,'EXACT_S1_PUBLIC_BRIDGE')
    own = obj(L/'resource-ready.PUBLIC.json')
    for name in ('binding_sha256','key_sha256','cost_stop_utc','app_ip','load_ip','mirror_binding_sha256'):
        need(c[name] == own[name],'OWN_LOAD_RESOURCE_CORRELATION')
    mirror = Path(own['mirror_dir'])
    status = one(step(L,'04-mirror-status',['python3','-I','-B',mirror/'controller.py','status','--directory',mirror,'--binding-sha256',own['mirror_binding_sha256']]))
    need(status['observed_before_pid'] and status['observed_before_pid'] == status['observed_after_pid'] and status.get('progress',{}).get('raw_bytes_observed'),'LIVE_RESOURCE_BYTES_BEFORE_SESSION')
    image = step(L,'05-python-image',['docker','--context','default','image','inspect','--format','{{.Id}}',c['python_image']]).decode().strip()
    need(image == c['python_image_id'],'ACTUAL_LOAD_PYTHON_IMAGE')
    load = {'kind':'P790_F7_LOAD_CONFIGURATION_V4','source_sha':SOURCE,'binding_sha256':c['binding_sha256'],'ca_sha256':c['ca_sha256'],'control_sha256':c['control_sha256'],'expected_host':socket.gethostname().split('.')[0],'key_sha256':c['key_sha256'],'manifest_sha256':MAN,'mirror_binding_sha256':own['mirror_binding_sha256'],'mirror_dir':own['mirror_dir'],'namespace':c['namespace'],'private_key':str(K/'load-only-private.pem'),'python_image':c['python_image'],'python_image_id':c['python_image_id'],'root_grant_sha256':c['root_grant_sha256'],'tools_dir':str(T),'transfer_sha256':c['transfer_sha256'],'work_dir':str(L/'pressure-input')}
    load_path = L/'LOAD-configuration.PUBLIC.json';load_sha = write(load_path,load)
    relay = {name:c[name] for name in ('source_sha','binding_sha256','root_grant_sha256','key_sha256','nonce','app_ip','load_ip','cost_stop_utc')}
    relay.update({'kind':'T44_OPAQUE_RELAY_LOAD_V1','port':18447,'expires_at':c['cost_stop_utc'],'output_dir':str(L/'relay-load-state'),'ca_file':str(L/'opened-resource-only/inputs/ca.pem'),'ca_sha256':c['ca_sha256'],'load_configuration':str(load_path),'load_configuration_sha256':load_sha,'receiver_sha256':manifest['files']['790_receive.py']['sha256'],'consumer_sha256':manifest['files']['790_consumer.py']['sha256'],'max_wait_seconds':420})
    relay_path = L/'relay-LOAD.PUBLIC.json';relay_sha = write(relay_path,relay)
    relay_module().configure(str(relay_path),relay_sha,'LOAD')
    start_unit(L,'06-relay-load','t44-r29-relay-load-01',['python3','-I','-B',Path(__file__).resolve(),'load-wait','--configuration',relay_path,'--configuration-sha256',relay_sha],min(1000,int(cost(c))))
    for _ in range(60):
        if (L/'LOAD-ready.PUBLIC.json').exists():break
        time.sleep(.1)
    ready = obj(L/'LOAD-ready.PUBLIC.json')
    pid = subprocess.check_output(['systemctl','show','t44-r29-relay-load-01','--property=MainPID','--value'],text=True,timeout=3).strip()
    need(str(ready['pid']) == pid and ready['nonce'] == c['nonce'],'ACTUAL_LOAD_POLL_PID')
    return ready


def load_wait(args):
    module = relay_module();c = module.configure(args.configuration,args.configuration_sha256,'LOAD')
    need(module.fetch(c,'metadata',32768) is None,'ORIGINAL_PRODUCER_NOT_YET_STARTED_EXPECT_425')
    write(L/'LOAD-ready.PUBLIC.json',{'kind':'R29_LOAD_TLS425_POLL_READY','pid':os.getpid(),'nonce':c['nonce'],'source_sha':c['source_sha'],'binding_sha256':c['binding_sha256'],'root_grant_sha256':c['root_grant_sha256'],'cost_stop_utc':c['cost_stop_utc'],'strict_TLS_CA_IP_verified':True,'producer_not_ready_425':True,'consumer_started':False})
    return module.load(c)


def app_producer(c):
    checked();need(c.get('root_start_producer') is True,'EXPLICIT_ROOT_START_PRODUCER')
    bridge = obj(A/'stage1-bridge.PUBLIC.json');cost(bridge,960)
    ready = c['load_ready']
    need(ready['kind'] == 'R29_LOAD_TLS425_POLL_READY' and ready['strict_TLS_CA_IP_verified'] is True and ready['producer_not_ready_425'] is True,'ACTUAL_LOAD_PREPOLL_REQUIRED')
    for name in ('nonce','source_sha','binding_sha256','root_grant_sha256','cost_stop_utc'):
        need(ready[name] == bridge[name],'EXACT_PREPOLL_CORRELATION')
    write(A/'root-producer-admission.PUBLIC.json',{'root_start_producer':True,'load_ready':ready,'utc':now().isoformat(),'no_retry':True})
    app_path = A/'APP-configuration.PUBLIC.json'
    need(sha(app_path) == bridge['APP_configuration_sha256'],'PINNED_ORIGINAL_APP_CONFIG')
    start_unit(A,'08-producer',bridge['producer_unit'],['python3','-I','-B',T/'790_producer.py','--configuration',app_path,'--configuration-sha256',bridge['APP_configuration_sha256']],450,True)
    return {'kind':'R29_ORIGINAL_S2_DISPATCHED_ONCE','producer_unit':bridge['producer_unit'],'nonce':bridge['nonce'],'consumer_auto_after_valid_ciphertext':True,'next_iteration_authorized':False}


def main():
    os.umask(0o077)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation',choices=['load-key','app-resource','load-resource','app-stage1','load-start','load-wait','app-producer'])
    parser.add_argument('--public-input-b64');parser.add_argument('--public-input-zlib-b64')
    parser.add_argument('--configuration');parser.add_argument('--configuration-sha256')
    args = parser.parse_args()
    if args.operation == 'load-wait':
        return emit(load_wait(args))
    payload = base64.b64decode(args.public_input_b64,validate=True) if args.public_input_b64 else b'{}'
    if args.public_input_zlib_b64:
        dec = zlib.decompressobj()
        payload = dec.decompress(base64.b64decode(args.public_input_zlib_b64,validate=True),25001)
        need(dec.eof and not dec.unused_data,'BOUNDED_PUBLIC_INPUT_COMPRESSION')
    need(len(payload) <= 25000,'PUBLIC_INPUT_CAP')
    value = globals()[args.operation.replace('-','_')](json.loads(payload))
    emit(value)


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        emit({'kind':'R29_OPS_FAILED_NO_RETRY','error_type':type(error).__name__,'reason':str(error),'partial_state_preserved':True,'no_automatic_retry_or_new_session':True})
        raise SystemExit(1) from None
