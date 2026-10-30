import base64,datetime,hashlib,json,os,platform,subprocess,zlib,uuid
from pathlib import Path
R=Path('/root/t44-final-20261029');T=R/'ops01/deployment/cloud-reuse'

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def run(cmd):return subprocess.run(cmd,check=True,capture_output=True,timeout=30).stdout.decode().strip()
assert os.geteuid()==0 and platform.system()=='Linux' and platform.machine() in {'x86_64','amd64'}
boot=int(next(x.split()[1] for x in Path('/proc/stat').read_text().splitlines() if x.startswith('btime ')))
ntp=run(['timedatectl','show','--property=NTPSynchronized','--value'])
old=T/'P07-CONTINUOUS-copyfix.PUBLIC.py';oldsha='e880acfae7cc1145edcccecbb496d611dd7cd636962ae9022522923332c0c25a'
profile=R/'source-profile90b.load-projection.root-approved.PUBLIC.json'
assert sha(profile)=='346d19344281b9e02046a27cf9d24f07ebceb9c8f920105a981d7bfdc056ac1f'
pv=json.loads(profile.read_bytes());package=R/'source90b/official';bundle=json.loads((package/'backend-bundle-manifest.json').read_bytes())
assert sha(package/'backend-bundle-manifest.json')==pv['backend_bundle_manifest_sha256'] and sha(package/'source-manifest.json')==pv['source_manifest_sha256']
for n,row in bundle['files'].items():assert (package/n).stat().st_size==row['bytes'] and sha(package/n)==row['sha256']
proof={n:sha(package/n) for n in ['backend-bundle-manifest.json','source-manifest.json','actual-runtime-files.json','source-profile.PUBLIC.json']}
active=run(['systemctl','list-units','--type=service','--state=active','--plain','--no-legend','t44-final-p08*'])
nets=run(['docker','--context','default','network','ls','--filter','label=com.docker.compose.project','--format','{{json .}}'])
networks=[json.loads(x) for x in nets.splitlines() if x.strip() and json.loads(x).get('Name','').startswith('t44')]
derived=json.loads(run(['python3','-B',str(T/'P09-DERIVE-TOOLS.PUBLIC.py')]))
record={'kind':'USER_EXECUTED_APP_P09_TOOL_PREPARATION_ONLY','observed_utc':datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),'actual_APP_resume_boot_utc':datetime.datetime.fromtimestamp(boot,datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),'private_ip':json.loads(run(['ip','-4','-j','route','get','1.1.1.1']))[0]['prefsrc'],'NTP_synchronized':ntp,'profile_sha256':sha(profile),'actual90b_public_file_shas':proof,'backend_alias':bundle['images']['backend']['alias'],'backend_image_actual_id':run(['docker','--context','default','image','inspect','--format','{{.Id}}',bundle['images']['backend']['alias']]),'T44_compose_network_metadata':networks,'active_P08_units':active,'tool_derivation':derived,'new_campaign_internal_cap_CNY':50,'fee_approval_created':False,'fee_root_approved':False,'cost_origin_requirement':'Use earliest current actual boot and newly reviewed platform cutoff; no old campaign fee','new_absolute_cutoff_utc':None,'fresh_window_frozen':False,'QA_or_SUT_requests':0,'cloud_lifecycle_changed':False}
out=R/('P09-APP-user-preparation-'+uuid.uuid4().hex+'.PUBLIC.json')
with out.open('x') as f:json.dump(record,f,sort_keys=True,indent=2);f.write('\n')
out.chmod(0o600)
print(json.dumps({'receipt':str(out),'sha256':sha(out),'public_facts':record},sort_keys=True))