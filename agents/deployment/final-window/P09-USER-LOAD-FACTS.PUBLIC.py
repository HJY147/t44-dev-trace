"""User-run LOAD public facts only; network-none runtime probe, no QA cases/keys/SUT requests."""
import argparse,datetime,hashlib,json,os,platform,subprocess,uuid
from pathlib import Path
R=Path('/root/t44-final-20261029');T=R/'ops01/deployment/cloud-reuse'
IMAGE='sha256:4f3baf081863a4580b5608699d9a7a8af2d89c3e87abbb60089b630b9102b2a1'
LAYERS=['sha256:9b35de7893378218e365c34c2c735fb0032a859112fb7345ca8ea73f9aa1db70','sha256:535ecd2088497f5955e24fd33c534fc9ba37fb717a33a841315a358dd4ff8b35','sha256:536ebec0f9d8119e620ed0e261faa2cfdeab88621f35924fb0ec74f646b5c53b','sha256:b8a5c0b25a3657c3b43a3a4cf1815f27fd7ca6c8bc3ffd36164f90731ca83db4']
def sha(p):
 if p.is_symlink() or p.stat().st_size>2000000:raise ValueError('BOUNDED_PUBLIC_REGULAR_FILE_REQUIRED')
 return hashlib.sha256(p.read_bytes()).hexdigest()
def run(argv,timeout=30):return subprocess.run(argv,check=True,capture_output=True,timeout=timeout).stdout.decode()
def main():
 os.umask(0o077)
 if os.geteuid()!=0 or platform.system()!='Linux' or platform.machine() not in {'x86_64','amd64'}:raise ValueError('ROOT_LINUX_AMD64_LOAD_REQUIRED')
 boot=int(next(x.split()[1] for x in Path('/proc/stat').read_text().splitlines() if x.startswith('btime ')))
 rows=[json.loads(x) for x in run(['docker','--context','default','ps','--format','{{json .}}']).splitlines() if x.strip()]
 active=[{'name':x.get('Names'),'id':x.get('ID')} for x in rows if x.get('Names','').startswith('qa753-')]
 image=json.loads(run(['docker','--context','default','image','inspect',IMAGE]))[0]
 image_ok=image['Id']==IMAGE and image.get('Descriptor',{}).get('digest')==IMAGE and image.get('Os')=='linux' and image.get('Architecture')=='amd64' and image.get('RootFS',{}).get('Type')=='layers' and image['RootFS']['Layers']==LAYERS
 probe=None
 if image_ok and not active:
  code="""import importlib.util,json,os,resource,sys
from pathlib import Path
print(json.dumps({'uid':os.getuid(),'python':sys.version,'cpu_max':Path('/sys/fs/cgroup/cpu.max').read_text().strip(),'memory_max':Path('/sys/fs/cgroup/memory.max').read_text().strip(),'pids_max':Path('/sys/fs/cgroup/pids.max').read_text().strip(),'nofile':resource.getrlimit(resource.RLIMIT_NOFILE),'affinity_cpus':len(os.sched_getaffinity(0)),'t44_absent':importlib.util.find_spec('t44') is None,'business_env_absent':not any(k.startswith(('T44_','MYSQL_','DATABASE_','AMQP_','RABBITMQ_'))for k in os.environ)}))"""
  probe=json.loads(run(['docker','--context','default','run','--rm','--restart=no','--pull','never','--network','none','--read-only','--user','10001:10001','--cap-drop','ALL','--security-opt','no-new-privileges:true','--cpus','8','--memory','8g','--memory-swap','8g','--pids-limit','2048','--ulimit','nofile=4096:4096','--entrypoint','python3',IMAGE,'-B','-c',code],45))
 files={}
 public_names=['ENTRY_PERF_753.sh','ADAPTER_753.py','TARGET_PROFILE_753.template.json','INSTALL_753.sh','capsule_tool.py','tool-manifest.json','tools.753capsule','transport-key.rsa-oaep-sha256','DELIVERY_MANIFEST.PUBLIC.json','ENTRY_FUNCTIONAL_753.sh']
 for base in [R/'ops01/qa-public',R/'QA753P07/public',R/'QA753FRESH90B/public']:
  for n in public_names:
   p=base/n
   if p.is_file():files[str(p)]={'sha256':sha(p),'bytes':p.stat().st_size}
 for n in ['final-transport-profile05.py','P05-TRANSPORT-LOAD.PUBLIC.py','P09-USER-TRANSPORT-LOAD.PUBLIC.py','P09-SPLUS1-EXEC.PUBLIC.py']:
  p=T/n
  if p.is_file():files[str(p)]={'sha256':sha(p),'bytes':p.stat().st_size}
 ip=json.loads(run(['ip','-4','-j','route','get','1.1.1.1']))[0]['prefsrc']
 facts={'kind':'USER_LOAD_P09_FACTS_ONLY','observed_utc':datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),'actual_LOAD_resume_boot_utc':datetime.datetime.fromtimestamp(boot,datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),'NTP_synchronized':run(['timedatectl','show','--property=NTPSynchronized','--value']).strip(),'private_ip':ip,'actual_image_id':image['Id'],'image_descriptor_layers_match':image_ok,'expected_config_from_original_public_projection':'sha256:3c4d812a6efe003770aafbdba65f9c1960ba8234ab23a133934205a70bdcda77','original_public_projection_sha256':'ce562c117428face0b421e06b33c361b291cab26d8d3a51d24484dbd0841da2a','runtime_probe':probe,'active_QA_containers':active,'active_T44_units':run(['systemctl','list-units','--type=service','--state=active','--plain','--no-legend','t44-final-*']).strip(),'public_files':files,'PRIVATE_or_plaintext_key_contents_read':False,'public_transport_ciphertext_hashed_only':True,'QA_or_SUT_requests':0,'root_approved':False,'window_frozen':False}
 dest=R/('P09-LOAD-user-facts-'+uuid.uuid4().hex+'.PUBLIC.json')
 with dest.open('x') as out:json.dump(facts,out,sort_keys=True,indent=2);out.write('\n')
 dest.chmod(0o600);print(json.dumps({'receipt':str(dest),'sha256':sha(dest),'public_facts':facts},sort_keys=True))
if __name__=='__main__':main()
