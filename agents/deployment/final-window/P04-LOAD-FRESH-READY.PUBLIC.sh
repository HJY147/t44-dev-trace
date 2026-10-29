umask 077
mkdir -p /root/t44-final-20261029
python3 - <<'PY'
import json,subprocess,hashlib,datetime
active=subprocess.run(['docker','--context','default','ps','--format','{{.Names}}'],check=True,capture_output=True,timeout=20).stdout.decode().splitlines()
assert not any(x.startswith('qa753-') for x in active),'QA_CONTAINER_STILL_RUNNING_NO_READY'
from pathlib import Path
actual='sha256:4f3baf081863a4580b5608699d9a7a8af2d89c3e87abbb60089b630b9102b2a1'
config='sha256:3c4d812a6efe003770aafbdba65f9c1960ba8234ab23a133934205a70bdcda77'
image=json.loads(subprocess.run(['docker','--context','default','image','inspect',actual],check=True,capture_output=True,timeout=20).stdout)[0]
assert image['Id']==actual and image['Descriptor']['digest']==actual
assert image['Os']=='linux' and image['Architecture']=='amd64'
assert image['RootFS']['Type']=='layers' and image['RootFS']['Layers']==[
'sha256:9b35de7893378218e365c34c2c735fb0032a859112fb7345ca8ea73f9aa1db70',
'sha256:535ecd2088497f5955e24fd33c534fc9ba37fb717a33a841315a358dd4ff8b35',
'sha256:536ebec0f9d8119e620ed0e261faa2cfdeab88621f35924fb0ec74f646b5c53b',
'sha256:b8a5c0b25a3657c3b43a3a4cf1815f27fd7ca6c8bc3ffd36164f90731ca83db4']
probe="""import importlib.util,json,os,resource,sys
from pathlib import Path
print(json.dumps({'uid':os.getuid(),'python':sys.version,'sys_executable':sys.executable,'cpu_max':Path('/sys/fs/cgroup/cpu.max').read_text().strip(),'memory_max':Path('/sys/fs/cgroup/memory.max').read_text().strip(),'pids_max':Path('/sys/fs/cgroup/pids.max').read_text().strip(),'nofile':resource.getrlimit(resource.RLIMIT_NOFILE),'affinity_cpus':len(os.sched_getaffinity(0)),'t44_absent':importlib.util.find_spec('t44') is None,'business_env_absent':not any(k.startswith(('T44_','MYSQL_','DATABASE_','AMQP_','RABBITMQ_')) for k in os.environ)}))"""
argv=['docker','--context','default','run','--rm','--pull','never','--network','none','--read-only','--user','10001:10001','--cap-drop','ALL','--security-opt','no-new-privileges:true','--cpus','8','--memory','8g','--pids-limit','2048','--ulimit','nofile=4096:4096','--entrypoint','python',actual,'-B','-c',probe]
result=subprocess.run(argv,check=True,capture_output=True,timeout=40)
observed=json.loads(result.stdout)
assert observed['uid']==10001 and observed['python'].startswith('3.12.') and observed['t44_absent'] and observed['business_env_absent']
assert observed['cpu_max']=='800000 100000' and observed['memory_max']=='8589934592' and observed['pids_max']=='2048' and observed['nofile']==[4096,4096] and observed['affinity_cpus']>=8
row={'kind':'LIVE_LOAD_PYTHON_IDENTITY_LIMITS_ONLY_NOT_QA_EXECUTOR_OR_SUT','actual_image_id':actual,'proven_config_id':config,'original_identity_projection_sha256':'ce562c117428face0b421e06b33c361b291cab26d8d3a51d24484dbd0841da2a','descriptor':image['Descriptor'],'ordered_rootfs':image['RootFS'],'observation':observed,'SUT_requests':0}
path=Path('/root/t44-final-20261029/P04-load-python-limits.original.PUBLIC.json')
with path.open('x') as output:json.dump(row,output,sort_keys=True,indent=2);output.write('\n')
proofsha=hashlib.sha256(path.read_bytes()).hexdigest()
ready={'root_approved':True,'actual_LOAD_ready':True,'observed_utc':datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),'actual_image_id':actual,'QA_or_other_writer_started':False,'original_live_python_proof_sha256':proofsha,'SUT_requests':0,'scope_note':'Root invokes only after completed F04 seal; no active qa753 container observed'}
rp=Path('/root/t44-final-20261029/P04-LOAD-READY.PUBLIC.json')
with rp.open('x') as output:json.dump(ready,output,sort_keys=True,indent=2);output.write('\n')
print(json.dumps({'status':'P04_LOAD_FRESH_READY_NO_SUT_REQUESTS','proof':str(path),'proof_sha256':proofsha,'ready':str(rp),'ready_sha256':hashlib.sha256(rp.read_bytes()).hexdigest(),'ready_original':ready}))
PY
