"""Continue only after failed start observation with the same original service actually running."""
import argparse,base64,hashlib,importlib.util,json,os,subprocess,sys,zlib
from pathlib import Path
OP=Path('/root/t44-r9/ops-r29-01.py')
need=lambda condition,message: None if condition else (_ for _ in ()).throw(ValueError(message))
need(hashlib.sha256(OP.read_bytes()).hexdigest()=='ca9a2953a847c03f4e644c3204412b0234703469722c67392006c111cff3571f','FIXED_EXISTING_OPS')
spec=importlib.util.spec_from_file_location('ops29',OP);o=importlib.util.module_from_spec(spec);spec.loader.exec_module(o)
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--public-input-zlib-b64',required=True);a=p.parse_args()
d=zlib.decompressobj();v=d.decompress(base64.b64decode(a.public_input_zlib_b64,validate=True),25001);need(d.eof and not d.unused_data and len(v)<=25000,'BOUNDED_PUBLIC_INPUT');c=json.loads(v)
os.umask(0o077);o.checked();o.cost(c,1200);s,phase,b=o.prepare()
need(o.local_ip(c['app_ip'])==b['app_private_ip'] and o.local_ip(c['load_ip'])!=c['app_ip'],'ACTUAL_TWO_NODE_IP')
key=c['load_key'];public=base64.b64decode(key['public_key_b64'],validate=True)
need(key['kind']=='PUBLIC-790-KEY' and hashlib.sha256(public).hexdigest()==key['public_key_sha256'] and o.raw(o.A/'public.pem')==public,'SAME_ORIGINAL_PUBLIC_KEY')
prep=o.one(o.raw(o.A/'01-resource-prepare.stdout.private'))
resource=Path(prep['directory']);need(resource==o.B/'r29-resource-app-01' and o.sha(resource/'binding.json')==prep['binding_sha256'],'SAME_ORIGINAL_RESOURCE_BINDING')
rb=o.obj(resource/'binding.json');plan=o.obj(resource/'start-plan.json')
need(plan['binding_sha256']==prep['binding_sha256'] and plan['unit']==rb['unit'] and o.sha(Path(plan['unit_path']))==plan['unit_sha256'],'ORIGINAL_UNIT_PLAN_AND_BYTES')
need(o.sha(Path(prep['private_handoff_path']))==prep['handoff_sha256'],'ORIGINAL_PRIVATE_HANDOFF')
for name,pin in rb['file_hashes'].items():need(o.sha(resource/name)==pin,'ORIGINAL_RESOURCE_FILES')
status=subprocess.check_output(['systemctl','show',rb['unit'],'--property=ActiveState,SubState,MainPID,Result'],timeout=5,text=True)
status=dict(row.split('=',1) for row in status.splitlines() if '=' in row)
need(status['ActiveState']=='active' and status['SubState']=='running' and status['Result']=='success','OBSERVED_SAME_UNIT_RUNNING')
pid=int(status['MainPID']);proc=Path('/proc')/str(pid)
need(pid>0 and proc.stat().st_uid==0 and (proc/'cmdline').read_bytes().rstrip(b'\0').split(b'\0')==[x.encode() for x in plan['argv']],'OBSERVED_ORIGINAL_ROOT_PROCESS_ARGV')
cmdline=(proc/'cmdline').read_bytes()
start_ticks=int((proc/'stat').read_text().rsplit(')',1)[1].split()[19])
receipt={'utc':o.now().isoformat(),'pid':pid,'start_ticks':start_ticks,'cmdline_sha256':hashlib.sha256(cmdline).hexdigest(),'recovered_by_fresh_actual_observation':True,'original_start_failure_preserved':True}
if (resource/'start-result.json').exists():
 old=o.obj(resource/'start-result.json')
 need(all(old[k]==receipt[k] for k in ('pid','start_ticks','cmdline_sha256')),'UNCHANGED_EXISTING_START_RESULT')
else:
 need(int(subprocess.check_output(['systemctl','show',rb['unit'],'--property=MainPID','--value'],timeout=3,text=True))==pid,'PID_STILL_CURRENT')
 need(int((proc/'stat').read_text().rsplit(')',1)[1].split()[19])==start_ticks,'PROCESS_START_STILL_CURRENT')
 o.write(resource/'start-result.json',receipt)
need((resource/'raw.jsonl').exists(),'RESOURCE_RAW_PREFIX_EXISTS')
first=o.raw(resource/'raw.jsonl',268435456).splitlines()[0];header=json.loads(first)
need(header['kind']=='resource_header' and header['binding_sha256']==prep['binding_sha256'] and header['source_sha']==o.SOURCE,'ACTUAL_RESOURCE_HEADER_SCOPE')
o.write(o.A/'02b-observed-original-running.PUBLIC.json',{'kind':'ORIGINAL_RESOURCE_START_OBSERVATION_RECOVERED','original_02_failure_preserved':True,'unit':rb['unit'],'pid':pid,'binding_sha256':prep['binding_sha256'],'service_restarted':False,'original_start_plan_sha256':o.sha(resource/'start-plan.json')})
o.write(o.A/'marker.json',o.MARKER);fixture=Path(s['bootstrap_output_dir']);control=fixture/'control.private.json'
o.step(o.A,'03-resource-only-seal',['python3','-I','-B',o.T/'transport/790_transfer.py','seal','--public-key-file',o.A/'public.pem','--public-key-sha256',key['public_key_sha256'],'--binding-sha256',s['binding_sha256'],'--control',control,'--control-sha256',o.sha(control),'--session',o.A/'marker.json','--packet-sha256',o.sha(o.A/'marker.json'),'--ca',phase/'tls/ca.pem','--ca-sha256',o.sha(phase/'tls/ca.pem'),'--mirror',prep['private_handoff_path'],'--mirror-sha256',prep['handoff_sha256'],'--output-dir',o.A/'resource-sealed'],60)
envelope=o.raw(o.A/'resource-sealed/transfer.public.jsonl',14000);blob=base64.b64encode(zlib.compress(envelope,9)).decode();need(len(blob)<=14500,'RESOURCE_ONLY_UI_CIPHERTEXT_CAP')
state={'kind':'R29_RESOURCE_ONLY_OPAQUE_HANDOFF','source_sha':o.SOURCE,'binding_sha256':s['binding_sha256'],'cost_stop_utc':c['cost_stop_utc'],'app_ip':c['app_ip'],'load_ip':c['load_ip'],'key_sha256':key['public_key_sha256'],'handoff_sha256':prep['handoff_sha256'],'opaque_bytes':len(envelope),'opaque_sha256':hashlib.sha256(envelope).hexdigest(),'opaque_zlib_b64':blob,'resource_binding_sha256':prep['binding_sha256'],'resource_only_never_matrix_input':True}
o.write(o.A/'resource-bridge.PUBLIC.json',state);o.write(o.A/'resource-state.private.json',{'prepared':prep,'started':{'observed_original_running':True,'unit':rb['unit'],'pid':pid,'original_02_failure_preserved':True},'fixture':str(fixture)})
o.emit(state)
